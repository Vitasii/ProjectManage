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
        self.view.setRenderHint(QPainter.Antialiasing)
        layout.addWidget(self.view)
        self.info_label = QLabel()
        layout.addWidget(self.info_label)
        self.node_items = []
        self.selected_node = None
        self.edges = []
        self.refresh()
        self.view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.view.customContextMenuRequested.connect(self.show_context_menu)

    def refresh(self):
        self.data = load_data()
        self.scene.clear()
        self.node_items = []
        self.edges = []
        def layout_tree(node, depth=0, x=0, siblings=1, idx=0, x_offset=180, y_offset=120):
            y = depth * y_offset
            width = x_offset * (siblings - 1)
            node_x = x - width/2 + idx * x_offset if siblings > 1 else x
            node["pos"] = [node_x, y]
            for i, ch in enumerate(node.get("children", [])):
                layout_tree(ch, depth+1, node_x, len(node["children"]), i, x_offset, y_offset)
        layout_tree(self.data)
        def draw_tree(node, parent_item=None):
            color = self.settings["project_finished"] if node.get("done") else self.settings["project_unfinished"]
            learn, review = node_learn_review_time(node)
            text = f'{node["name"]}\nLearn:{format_seconds(learn)}\nReview:{format_seconds(review)}'
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

        fig, axs = plt.subplots(3, 1, figsize=(10, 12))
        axs[0].plot(week_dates, week_learn, marker='o', label="Learn", color="#4F81BD")
        axs[0].plot(week_dates, week_review, marker='s', label="Review", color="#C0504D")
        axs[0].set_title("Last 7 Days Time Trend")
        axs[0].set_ylabel("Seconds")
        axs[0].legend()
        axs[0].set_xticks(week_dates)
        axs[0].set_xticklabels(week_dates, rotation=45, ha='right')

        axs[1].plot(month_dates, month_learn, marker='o', label="Learn", color="#4F81BD")
        axs[1].plot(month_dates, month_review, marker='s', label="Review", color="#C0504D")
        axs[1].set_title("Last 30 Days Time Trend")
        axs[1].set_ylabel("Seconds")
        axs[1].legend()
        axs[1].set_xticks(month_dates[::max(1, len(month_dates)//10)])
        axs[1].set_xticklabels(month_dates[::max(1, len(month_dates)//10)], rotation=45, ha='right')

        axs[2].plot(year_months, year_learn, marker='o', label="Learn", color="#4F81BD")
        axs[2].plot(year_months, year_review, marker='s', label="Review", color="#C0504D")
        axs[2].set_title("Last 12 Months Time Trend")
        axs[2].set_ylabel("Seconds")
        axs[2].legend()
        axs[2].set_xticks(year_months)
        axs[2].set_xticklabels(year_months, rotation=45, ha='right')

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
        menu.addAction("Show Chart", self.show_chart)
        menu.exec_(self.view.mapToGlobal(pos))