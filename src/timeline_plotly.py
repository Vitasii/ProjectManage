import sys
import os

def get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

import datetime
from PyQt5.QtWidgets import QWidget, QVBoxLayout
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from PyQt5.QtWebEngineWidgets import QWebEngineView
import db
import os

def get_last_n_days(n):
    today = datetime.date.today()
    return [(today - datetime.timedelta(days=i)).strftime("%Y-%m-%d") for i in reversed(range(n))]

def get_project_tasks():
    # 从数据库收集所有学习/复习记录，按项目分组
    from project_tree import load_data
    data = load_data()
    node_id_name = {}
    def collect(node):
        node_id_name[node.get("id")] = node.get("name", "")
        for ch in node.get("children", []):
            collect(ch)
    collect(data)
    # 收集所有学习/复习记录
    tasks = []
    for node_id, name in node_id_name.items():
        for _, date, start, end in db.get_records(db.DB_LEARN, node_id):
            tasks.append({
                "Task": name,
                "Type": "Learn",
                "Start": datetime.datetime.fromtimestamp(start),
                "Finish": datetime.datetime.fromtimestamp(end),
                "Date": date
            })
        for _, date, start, end in db.get_records(db.DB_REVIEW, node_id):
            tasks.append({
                "Task": name,
                "Type": "Review",
                "Start": datetime.datetime.fromtimestamp(start),
                "Finish": datetime.datetime.fromtimestamp(end),
                "Date": date
            })
    return tasks

class TimelinePlotlyWidget(QWidget):
    def __init__(self, main_window, num_segments=None):
        super().__init__()
        self.main_window = main_window
        # 读取设置
        try:
            import json
            settings_path = os.path.join(get_base_dir(), 'data', 'settings.json')
            with open(settings_path, "r", encoding="utf-8") as f:
                settings = json.load(f)
            self.num_segments = int(settings.get("timeline_num_segments", 9)) if num_segments is None else num_segments
        except Exception:
            self.num_segments = num_segments if num_segments is not None else 9
        
        # 主布局
        main_layout = QVBoxLayout(self)
        
        # 添加更新按钮
        from PyQt5.QtWidgets import QPushButton, QHBoxLayout
        button_layout = QHBoxLayout()
        self.update_button = QPushButton("更新时间线")
        self.update_button.setStyleSheet("font-family: '霞鹜文楷'; font-size: 16px; padding: 5px 15px;")
        self.update_button.clicked.connect(self.refresh_timeline)
        button_layout.addWidget(self.update_button)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)
        
        # 滚动区域
        from PyQt5.QtWidgets import QScrollArea, QWidget
        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        self.container.setLayout(self.layout)
        self.scroll.setWidget(self.container)
        main_layout.addWidget(self.scroll)
        
        self.setLayout(main_layout)
        self.show_timeline(self.layout)
        # 页面加载后滚动到底部
        from PyQt5.QtCore import QTimer
        def scroll_to_bottom():
            self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum())
        QTimer.singleShot(300, scroll_to_bottom)

    def refresh_timeline(self):
        """刷新时间线数据"""
        # 清空现有内容
        for i in reversed(range(self.layout.count())):
            child = self.layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # 重新生成时间线
        self.show_timeline(self.layout)
        
        # 滚动到底部
        from PyQt5.QtCore import QTimer
        def scroll_to_bottom():
            self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum())
        QTimer.singleShot(300, scroll_to_bottom)

    def show_timeline(self, layout):
        tasks = get_project_tasks()
        if not tasks:
            from PyQt5.QtWidgets import QLabel
            layout.addWidget(QLabel("No data to show."))
            return
        import pandas as pd
        df = pd.DataFrame(tasks)
        df = df[df["Task"] != "Root"]
        if df.empty:
            from PyQt5.QtWidgets import QLabel
            layout.addWidget(QLabel("No data to show."))
            return
        import plotly.graph_objects as go
        type_color = {"Learn": "#4F81BD", "Review": "#C0504D"}
        # 计算当前时间属于哪个8小时段
        now = datetime.datetime.now()
        hour = now.hour
        seg_idx = hour // 8
        # 生成可设置数量的时间段（每段8小时），最靠近当前时间的段在最下方
        segments = []
        # 计算当前段的结束时间，始终为有效datetime
        end_time = now.replace(minute=0, second=0, microsecond=0)
        end_hour = (seg_idx+1)*8 if (seg_idx+1)*8 < 24 else 24
        if end_hour >= 24:
            end_time = end_time.replace(hour=0) + datetime.timedelta(days=1)
        else:
            end_time = end_time.replace(hour=end_hour)
        for i in range(self.num_segments):
            seg_end = end_time - datetime.timedelta(hours=8*i)
            seg_start = seg_end - datetime.timedelta(hours=8)
            # 保证 seg_start/seg_end 都是 datetime 类型且 seg_start < seg_end
            if not (isinstance(seg_start, datetime.datetime) and isinstance(seg_end, datetime.datetime)):
                continue
            seg_start = seg_start.replace(microsecond=0)
            seg_end = seg_end.replace(microsecond=0)
            if seg_start >= seg_end:
                continue
            segments.append((seg_start, seg_end))
        segments = segments[::-1]
        from PyQt5.QtCore import QUrl
        webviews = []
        # 新建 timeline_html 文件夹
        html_dir = os.path.join(get_base_dir(), "timeline_html")
        if not os.path.exists(html_dir):
            os.makedirs(html_dir)
        for idx, (seg_start, seg_end) in enumerate(segments):
            if seg_start >= seg_end:
                continue
            mask = (df["Start"] >= seg_start) & (df["Start"] < seg_end)
            df_seg = df[mask]
            fig = go.Figure()
            # 主轴线用go.Scatter绘制，横坐标用datetime，彻底消除NaN
            fig.add_trace(go.Scatter(
                x=[seg_start, seg_end],
                y=[0, 0],
                mode="lines",
                line=dict(color="#888", width=3),
                hoverinfo="skip",
                showlegend=False
            ))
            intervals = []
            for _, row in df_seg.iterrows():
                intervals.append({
                    "start": row["Start"],
                    "end": row["Finish"],
                    "task": row["Task"],
                    "type": row["Type"]
                })
            intervals.sort(key=lambda x: x["start"])
            if intervals:
                for iv in intervals:
                    duration = iv["end"] - iv["start"]
                    duration_str = str(duration)
                    # 区间宽线 hover 显示名字、时长、开始时间、结束时间（用 hovertemplate 保证显示）
                    fig.add_trace(go.Scatter(
                        x=[iv["start"], iv["end"]],
                        y=[0, 0],
                        mode="lines",
                        line=dict(color=type_color.get(iv["type"], "#888"), width=12),
                        hovertemplate=(
                            f"<b>{iv['task']}</b><br>"
                            f"类型: {iv['type']}<br>"
                            f"时长: {duration_str}<br>"
                            f"开始: {iv['start'].strftime('%Y-%m-%d %H:%M:%S')}<br>"
                            f"结束: {iv['end'].strftime('%Y-%m-%d %H:%M:%S')}<extra></extra>"
                        ),
                        showlegend=False,
                        name=iv['task']
                    ))
                    # markers 不显示 hover 信息
                    fig.add_trace(go.Scatter(
                        x=[iv["start"]],
                        y=[0],
                        mode="markers",
                        marker=dict(size=14, color=type_color.get(iv["type"], "#888"), symbol="circle"),
                        showlegend=False,
                        hoverinfo="skip"
                    ))
                    fig.add_trace(go.Scatter(
                        x=[iv["end"]],
                        y=[0],
                        mode="markers",
                        marker=dict(size=14, color=type_color.get(iv["type"], "#888"), symbol="circle-open"),
                        showlegend=False,
                        hoverinfo="skip"
                    ))
            # 横坐标刻度全部转为时间字符串
            tickvals = []
            ticktext = []
            t = seg_start
            t_end = seg_end
            while t <= t_end:
                tickvals.append(t)
                ticktext.append(t.strftime('%H:%M'))
                t += datetime.timedelta(hours=1)
            fig.update_layout(
                title=f"时间段 {seg_start.strftime('%Y-%m-%d %H:%M')} ~ {seg_end.strftime('%Y-%m-%d %H:%M')}",
                xaxis_title="时间",
                yaxis=dict(visible=False, range=[-1, 1], fixedrange=True),
                height=220,
                margin=dict(l=80, r=40, t=60, b=40),
                font=dict(family="LXGW WenKai, 霞鹜文楷, SimHei, Microsoft YaHei, Arial", size=14),
                hoverlabel=dict(font=dict(family="LXGW WenKai, 霞鹜文楷, SimHei, Microsoft YaHei, Arial", size=14)),
                plot_bgcolor="#F7F9FB",
                paper_bgcolor="#F7F9FB",
                showlegend=False,
                xaxis=dict(
                    rangeslider=dict(visible=False),
                    showgrid=True,
                    zeroline=False,
                    showline=True,
                    tickvals=tickvals,
                    ticktext=ticktext,
                ),
                dragmode=False,
            )
            html_path = os.path.abspath(os.path.join(html_dir, f"timeline_plotly_{idx}.html"))
            fig.write_html(
                html_path,
                include_plotlyjs='cdn',
                config={
                    "scrollZoom": False,
                    "displayModeBar": False
                }
            )
            webview = QWebEngineView()
            webview.load(QUrl.fromLocalFile(html_path))
            webview.setMinimumHeight(220)
            webview.setMaximumHeight(220)
            layout.addWidget(webview)
            webviews.append(webview)
        # 用最后一个webview的loadFinished信号触发滚动
        if webviews:
            def scroll_to_bottom():
                self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum())
            webviews[-1].loadFinished.connect(lambda _: scroll_to_bottom())
