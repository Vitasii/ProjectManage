import json, os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene, QMenu, QMessageBox, QLabel
from PyQt5.QtCore import Qt
from tree_base import NodeItem, EdgeLine
from settings import load_settings
from PyQt5.QtGui import QPainter

import matplotlib.pyplot as plt
import datetime
from collections import defaultdict
import db

DATA_FILE = "data/data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"name": "Root", "children": [], "pos": [0, 0], "done": False}

def collect_ids(node):
    ids = [node.get("id")]
    for ch in node.get("children", []):
        ids.extend(collect_ids(ch))
    return ids

def get_last_n_days(n):
    today = datetime.date.today()
    return [(today - datetime.timedelta(days=i)).strftime("%Y-%m-%d") for i in reversed(range(n))]

def get_last_n_months(n):
    today = datetime.date.today()
    months = []
    for i in reversed(range(n)):
        year = today.year
        month = today.month - i
        while month <= 0:
            year -= 1
            month += 12
        months.append(f"{year}-{month:02d}")
    return months

def format_seconds(seconds):
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h}h {m}m {s}s"

def node_learn_review_time(node):
    ids = collect_ids(node)
    learn = 0
    review = 0
    for node_id in ids:
        for _, _, start, end in db.get_records(db.DB_LEARN, node_id):
            learn += end - start
        for _, _, start, end in db.get_records(db.DB_REVIEW, node_id):
            review += end - start
    return learn, review

class StatsWidget(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.settings = load_settings()
        self.data = load_data()
        layout = QVBoxLayout(self)
        self.scene = QGraphicsScene()
        from tree_base import ZoomableGraphicsView
        self.view = ZoomableGraphicsView(self.scene)
        layout.addWidget(self.view)
        self.info_label = QLabel()
        self.info_label.setStyleSheet("font-family: '霞鹜文楷'; font-size: 14px;")
        layout.addWidget(self.info_label)
        self.node_items = []
        self.selected_node = None
        self.edges = []
        self.refresh()
        self.view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.view.customContextMenuRequested.connect(self.show_context_menu)

    def refresh(self):
        self.data = load_data()
    def refresh(self):
        self.data = load_data()
        self.scene.clear()
        self.node_items = []
        self.edges = []
        x_offset = int(self.settings.get("tree_x_offset", 300))
        y_offset = int(self.settings.get("tree_y_offset", 120))

        # 递归布局算法（与project_tree一致）
        leaf_positions = []
        def assign_leaf_positions(node, depth=0):
            if not node.get("children"):
                node["_leaf_index"] = len(leaf_positions)
                leaf_positions.append(node)
            else:
                for ch in node.get("children", []):
                    assign_leaf_positions(ch, depth+1)

        def set_positions(node, depth=0):
            y = depth * y_offset
            if not node.get("children"):
                x = node["_leaf_index"] * x_offset
                node["pos"] = [x, y]
                return x
            else:
                child_xs = [set_positions(ch, depth+1) for ch in node["children"]]
                x = sum(child_xs) / len(child_xs)
                node["pos"] = [x, y]
                return x

        assign_leaf_positions(self.data)
        set_positions(self.data)

        def get_node_color(node):
            settings = self.settings
            # 优先级：toggle_done_color_stat > 节点color > default color
            if node.get("done") and settings.get("toggle_done_color_stat"):
                return settings["toggle_done_color_stat"]
            if node.get("color"):
                return node["color"]
            return settings.get("default_color", "#A0A0A0")

        def draw_tree(node, parent_item=None):
            color = get_node_color(node)
            learn_sec, review_sec = node_learn_review_time(node)
            text = node["name"]
            # 如果已完成，显示完成时间
            if node.get("done"):
                finished_time = node.get("done_time")
                if finished_time:
                    try:
                        dt = datetime.datetime.fromtimestamp(finished_time)
                        finished_str = dt.strftime("Finished at %Y-%m-%d")
                    except Exception:
                        finished_str = f"Finished at {finished_time}"
                    text += f"\n{finished_str}"
            text += f'\n学:{format_seconds(learn_sec)}\n复:{format_seconds(review_sec)}'
            item = NodeItem(node, color, text)
            self.scene.addItem(item)
            self.node_items.append(item)
            if parent_item:
                edge = EdgeLine(parent_item, item)
                self.scene.addItem(edge)
                self.edges.append(edge)
            for ch in node.get("children", []):
                draw_tree(ch, item)
        draw_tree(self.data)
        self.view.setSceneRect(self.scene.itemsBoundingRect().adjusted(-100, -100, 100, 100))
        self.show_total_time()

    def show_total_time(self):
        ids = collect_ids(self.data)
        learn = 0
        review = 0
        for node_id in ids:
            for _, _, start, end in db.get_records(db.DB_LEARN, node_id):
                learn += end - start
            for _, _, start, end in db.get_records(db.DB_REVIEW, node_id):
                review += end - start
        self.info_label.setText(f"TOTALLEARN: {format_seconds(learn)}    TOTALREVIEW: {format_seconds(review)}")

    def get_selected(self):
        if not self.selected_node:
            return None, None
        def find_parent(data, target):
            for ch in data.get("children", []):
                if ch is target:
                    return data
                res = find_parent(ch, target)
                if res:
                    return res
            return None
        parent = find_parent(self.data, self.selected_node)
        return self.selected_node, parent

    def show_chart(self):
        node, _ = self.get_selected()
        if node is None:
            QMessageBox.warning(self, "Tip", "Please select a node")
            return

        ids = collect_ids(node)
        learn_by_date = defaultdict(int)
        review_by_date = defaultdict(int)
        for node_id in ids:
            for _, date, start, end in db.get_records(db.DB_LEARN, node_id):
                learn_by_date[date] += end - start
            for _, date, start, end in db.get_records(db.DB_REVIEW, node_id):
                review_by_date[date] += end - start

        week_dates = get_last_n_days(7)
        week_learn = [learn_by_date.get(d, 0) for d in week_dates]
        week_review = [review_by_date.get(d, 0) for d in week_dates]

        month_dates = get_last_n_days(30)
        month_learn = [learn_by_date.get(d, 0) for d in month_dates]
        month_review = [review_by_date.get(d, 0) for d in month_dates]

        year_months = get_last_n_months(12)
        learn_month_agg = defaultdict(int)
        review_month_agg = defaultdict(int)
        for d, v in learn_by_date.items():
            ym = d[:7]
            learn_month_agg[ym] += v
        for d, v in review_by_date.items():
            ym = d[:7]
            review_month_agg[ym] += v
        year_learn = [learn_month_agg.get(m, 0) for m in year_months]
        year_review = [review_month_agg.get(m, 0) for m in year_months]

        import numpy as np
        fig, axs = plt.subplots(2, 4, figsize=(24, 10))
        # 1. 折线图1：最近7天
        ax = axs[0, 0]
        ax.plot(week_dates, week_learn, marker='o', label="Learn", color="#4F81BD")
        ax.plot(week_dates, week_review, marker='s', label="Review", color="#C0504D")
        ax.set_title("Last 7 Days Time Trend")
        ax.set_ylabel("Seconds")
        ax.legend()
        ax.set_xticks(week_dates)
        ax.set_xticklabels(week_dates, rotation=45, ha='right')

        # 2. 折线图2：最近30天
        ax = axs[0, 1]
        ax.plot(month_dates, month_learn, marker='o', label="Learn", color="#4F81BD")
        ax.plot(month_dates, month_review, marker='s', label="Review", color="#C0504D")
        ax.set_title("Last 30 Days Time Trend")
        ax.set_ylabel("Seconds")
        ax.legend()
        ax.set_xticks(month_dates[::max(1, len(month_dates)//10)])
        ax.set_xticklabels(month_dates[::max(1, len(month_dates)//10)], rotation=45, ha='right')

        # 3. 折线图3：最近12个月
        ax = axs[0, 2]
        ax.plot(year_months, year_learn, marker='o', label="Learn", color="#4F81BD")
        ax.plot(year_months, year_review, marker='s', label="Review", color="#C0504D")
        ax.set_title("Last 12 Months Time Trend")
        ax.set_ylabel("Seconds")
        ax.legend()
        ax.set_xticks(year_months)
        ax.set_xticklabels(year_months, rotation=45, ha='right')

        # 4. 空白子图
        axs[0, 3].axis('off')

        # 饼图绘制函数
        def plot_percent_pie(ax, node, days, title):
            # 只统计直接子节点
            if not node.get("children"):
                ax.set_title(title + " (No Data)")
                ax.axis('off')
                return
            end_date = datetime.date.today()
            start_date = end_date - datetime.timedelta(days=days-1)
            child_names = []
            child_times = []
            for ch in node["children"]:
                ids = collect_ids(ch)
                total = 0
                for node_id in ids:
                    for _, date, start, end in db.get_records(db.DB_LEARN, node_id):
                        d = datetime.datetime.strptime(date, "%Y-%m-%d").date()
                        if start_date <= d <= end_date:
                            total += end - start
                if total > 0:  # 只添加时长大于0的
                    child_names.append(ch["name"])
                    child_times.append(total)
            total_time = sum(child_times)
            if total_time == 0:
                ax.set_title(title + " (No Data)")
                ax.axis('off')
                return
            percent = np.array(child_times) / total_time
            ax.pie(percent, labels=child_names, autopct='%1.1f%%', startangle=90)
            ax.set_title(title)

        # 5. 饼图1：Today
        plot_percent_pie(axs[1, 0], node, 1, "Today")
        # 6. 饼图2：Last 7 Days
        plot_percent_pie(axs[1, 1], node, 7, "Last 7 Days")
        # 7. 饼图3：Last 30 Days
        plot_percent_pie(axs[1, 2], node, 30, "Last 30 Days")
        # 8. 饼图4：Last 1 Year
        plot_percent_pie(axs[1, 3], node, 365, "Last 1 Year")

        plt.tight_layout()
        plt.show()

    def show_context_menu(self, pos):
        view_pos = self.view.mapToScene(pos)
        clicked_item = None
        for item in self.node_items:
            if item.contains(item.mapFromScene(view_pos)):
                clicked_item = item
                break
        if not clicked_item:
            return
        self.selected_node = clicked_item.node_data
        menu = QMenu(self)
        # Show Chart 作为主菜单第一个选项
        menu.addAction("Show Chart", self.show_chart)
        # Color 子菜单
        color_menu = menu.addMenu("Color")
        color_menu.addAction("Change Color", self.change_node_color)
        color_menu.addAction("Set to Default Color", self.set_node_default_color)
        global_pos = self.view.mapToGlobal(pos)
        menu.exec_(global_pos)

    def set_node_default_color(self):
        node = self.selected_node
        if node is None:
            return
        if "color" in node:
            del node["color"]
            from project_tree import save_data
            save_data(self.data)
            self.refresh()

    def change_node_color(self):
        node = self.selected_node
        if node is None:
            return
        from PyQt5.QtWidgets import QColorDialog
        color = QColorDialog.getColor()
        if color.isValid():
            node["color"] = color.name()
            from project_tree import save_data
            save_data(self.data)
            self.refresh()