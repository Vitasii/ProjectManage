import json, os, uuid
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene, QMenu, QInputDialog, QMessageBox
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
    if "id" not in node:
        node["id"] = str(uuid.uuid4())
    for ch in node.get("children", []):
        ensure_ids(ch)

def total_learn_time(node):
    ids = []
    def collect_ids(n):
        ids.append(n.get("id"))
        for ch in n.get("children", []):
            collect_ids(ch)
    collect_ids(node)
    total = 0
    for node_id in ids:
        for _, _, start, end in db.get_records(db.DB_LEARN, node_id):
            total += end - start
    return total

def format_seconds(seconds):
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h}h {m}m {s}s"

class ProjectTreeWidget(QWidget):
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

        # 递归计算每棵子树的宽度
        def calc_width(node):
            if not node.get("children"):
                node["_subtree_width"] = 1
                return 1
            width = 0
            for ch in node["children"]:
                width += calc_width(ch)
            node["_subtree_width"] = width
            return width

        # 递归布局，避免重叠
        def layout_tree(node, depth=0, x=0):
            y = depth * y_offset
            width = node.get("_subtree_width", 1)
            left = x - (width / 2.0) * x_offset + x_offset / 2.0
            cur_x = left
            node["pos"] = [x, y]
            for ch in node.get("children", []):
                w = ch.get("_subtree_width", 1)
                child_center = cur_x + (w / 2.0) * x_offset - x_offset / 2.0
                layout_tree(ch, depth + 1, child_center)
                cur_x += w * x_offset

        calc_width(self.data)
        layout_tree(self.data)

        # draw_tree部分保持不变
        def draw_tree(node, parent_item=None):
            color = "#ffd54f" if node.get("is_root_task") else ("#90EE90" if node.get("done") else "#A0A0A0")
            learn_sec = total_learn_time(node)
            text = f'{node["name"]}\n{format_seconds(learn_sec)}'
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

    def add_node(self):
        node, _ = self.get_selected()
        if node is None:
            node = self.data
        name, ok = QInputDialog.getText(self, "Add Child Node", "Node Name:")
        if not (ok and name):
            return
        new_node = {
            "name": name,
            "id": str(uuid.uuid4()),
            "children": [],
            "pos": [0, 0],
            "done": False,
            "lastreview": 0,
            "review_state": False
        }
        node["children"].append(new_node)
        save_data(self.data)
        self.main_window.refresh_all()

    def del_node(self):
        node, parent = self.get_selected()
        if node is None or parent is None:
            QMessageBox.warning(self, "Warning", "Cannot delete root node")
            return
        if node.get("children"):
            QMessageBox.warning(self, "Warning", "Only leaf nodes can be deleted")
            return
        parent["children"] = [ch for ch in parent["children"] if ch is not node]
        save_data(self.data)
        self.main_window.refresh_all()

    def toggle_done(self):
        node, _ = self.get_selected()
        if node is None:
            return
        node["done"] = not node.get("done", False)
        save_data(self.data)
        self.main_window.refresh_all()

    def start_study(self):
        node, _ = self.get_selected()
        if node is None:
            QMessageBox.warning(self, "Warning", "Please select a node")
            return
        self.main_window.show_timer(node, "learn")

    def rename_node(self):
        node, _ = self.get_selected()
        if node is None:
            QMessageBox.warning(self, "Warning", "Please select a node")
            return
        new_name, ok = QInputDialog.getText(self, "Rename Node", "New Name:", text=node.get("name", ""))
        if ok and new_name and new_name != node.get("name"):
            node["name"] = new_name
            save_data(self.data)
            self.main_window.refresh_all()

    def move_node(self, direction):
        node, parent = self.get_selected()
        if node is None or parent is None:
            QMessageBox.warning(self, "Warning", "请选择非根节点")
            return
        siblings = parent["children"]
        idx = siblings.index(node)
        new_idx = idx + direction
        if 0 <= new_idx < len(siblings):
            siblings[idx], siblings[new_idx] = siblings[new_idx], siblings[idx]
            save_data(self.data)
            self.main_window.refresh_all()

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
        menu.addAction("Add Child Node", self.add_node)
        menu.addAction("Delete Node", self.del_node)
        menu.addAction("Rename Node", self.rename_node)
        menu.addAction("Toggle Done/Undone", self.toggle_done)
        menu.addAction("Start Learning", self.start_study)
        # 新增左右移动
        menu.addAction("Move Left", lambda: self.move_node(-1))
        menu.addAction("Move Right", lambda: self.move_node(1))
        menu.exec_(self.view.mapToGlobal(pos))