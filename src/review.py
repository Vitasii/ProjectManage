import json, os, time, datetime
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene, QMenu, QInputDialog, QMessageBox, QLabel
from PyQt5.QtCore import Qt
from tree_base import NodeItem, EdgeLine
from settings import load_settings
from PyQt5.QtGui import QPainter
import db

DATA_FILE = "data/data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"name": "Root", "id": "root", "children": [], "pos": [0, 0], "done": False, "lastreview": 0, "review_state": False}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def ensure_ids(node):
    import uuid
    if "id" not in node:
        node["id"] = str(uuid.uuid4())
    for ch in node.get("children", []):
        ensure_ids(ch)

def human_time(ts):
    if not ts:
        return "无"
    return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")

def total_review_time(node):
    ids = []
    def collect_ids(n):
        ids.append(n.get("id"))
        for ch in n.get("children", []):
            collect_ids(ch)
    collect_ids(node)
    total = 0
    for node_id in ids:
        for _, _, start, end in db.get_records(db.DB_REVIEW, node_id):
            total += end - start
    return total

def format_seconds(seconds):
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h}h {m}m {s}s"

class ReviewWidget(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.settings = load_settings()
        self.data = load_data()
        ensure_ids(self.data)
        save_data(self.data)
        layout = QVBoxLayout(self)
        self.scene = QGraphicsScene()
        from tree_base import ZoomableGraphicsView
        self.view = ZoomableGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        layout.addWidget(self.view)
        self.suggest_label = QLabel()
        self.suggest_label.setStyleSheet("font-family: '霞鹜文楷'; font-size: 14px;")
        layout.addWidget(self.suggest_label)
        self.node_items = []
        self.selected_node = None
        self.edges = []
        self.refresh()
        self.view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.view.customContextMenuRequested.connect(self.show_context_menu)

    def refresh(self):
        self.data = load_data()
        ensure_ids(self.data)
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
            # 优先级：start_review_color > 节点color > default color
            if node.get("review_state") and settings.get("start_review_color"):
                return settings["start_review_color"]
            if node.get("color"):
                return node["color"]
            return settings.get("default_color", "#A0A0A0")

        def draw_tree(node, parent_item=None):
            color = get_node_color(node)
            review_sec = total_review_time(node)
            if node.get("review_state"):
                period = node.get("period", None)
                period_str = f"\nPeriod:{period}DAY" if period else ""
                text = f'{node["name"]}{period_str}\nLast:{human_time(node.get("lastreview",0))}\nReview:{format_seconds(review_sec)}'
            else:
                text = f'{node["name"]}\nReview:{format_seconds(review_sec)}'
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
        self.show_suggest()

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

    def get_selected(self):
        if self.selected_node:
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
        return None, None

    def set_review(self):
        node, _ = self.get_selected()
        if node is None:
            return
        period, ok = QInputDialog.getInt(self, "Review_Period", "SuggestedDays(天):", value=node.get("period", 1), min=1)
        if not ok:
            return
        node["review_state"] = True
        node["period"] = period
        save_data(self.data)
        self.main_window.refresh_all()

    def unset_review(self):
        node, _ = self.get_selected()
        if node is None:
            return
        node["review_state"] = False
        if "period" in node:
            del node["period"]
        save_data(self.data)
        self.main_window.refresh_all()

    def start_review(self):
        node, _ = self.get_selected()
        if node is None or not node.get("review_state"):
            QMessageBox.warning(self, "Warning", "Please select a node in review state")
            return
        self.main_window.show_timer(node, "review")

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
        # Start Review 作为主菜单第一个选项
        menu.addAction("Start Review", self.start_review)
        # 只显示 Set Review 或 Unset Review
        if self.selected_node.get("review_state"):
            menu.addAction("Unset Review", self.unset_review)
        else:
            menu.addAction("Set Review", self.set_review)
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

    def show_suggest(self):
        now = int(time.time())
        nodes = []
        def collect(node):
            if node.get("review_state"):
                period = node.get("period", 1)
                lastreview = node.get("lastreview", 0)
                due = (now - lastreview) / (period * 86400) if period else 0
                nodes.append((due, node))
            for ch in node.get("children", []):
                collect(ch)
        collect(self.data)
        nodes.sort(reverse=True, key=lambda x: x[0])
        suggest = [f'{n["name"]} (Period{n.get("period",1)}DAY, Last:{human_time(n.get("lastreview",0))})' for _, n in nodes[:10]]
        self.suggest_label.setText("Suggest:\n" + "\n".join(suggest) if suggest else "All Perfect")