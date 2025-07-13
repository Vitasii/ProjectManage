import json, os, uuid, sys
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene, QMenu, QInputDialog, QMessageBox
from PyQt5.QtCore import Qt
from tree_base import NodeItem, EdgeLine
from settings import load_settings
from PyQt5.QtGui import QPainter
import db

def get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_FILE = os.path.join(get_base_dir(), "data", "data.json")

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


        # 新的递归布局算法：x_offset为叶子节点最小间距
        leaf_positions = []
        def assign_leaf_positions(node, depth=0):
            if not node.get("children"):
                node["_leaf_index"] = len(leaf_positions)
                leaf_positions.append(node)
            else:
                for ch in node["children"]:
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

        # draw_tree支持颜色优先级
        def get_node_color(node):
            settings = self.settings
            # 优先级：toggle_done_color_project_tree > 节点color > default color
            if node.get("done") and settings.get("toggle_done_color_project_tree"):
                return settings["toggle_done_color_project_tree"]
            if node.get("color"):
                return node["color"]
            return settings.get("default_color", "#A0A0A0")

        def draw_tree(node, parent_item=None):
            color = get_node_color(node)
            learn_sec = total_learn_time(node)
            text = node["name"]
            # 如果已完成，显示完成时间
            if node.get("done"):
                finished_time = node.get("done_time")
                if finished_time:
                    import datetime
                    try:
                        dt = datetime.datetime.fromtimestamp(finished_time)
                        finished_str = dt.strftime("Finished at %Y-%m-%d")
                    except Exception:
                        finished_str = f"Finished at {finished_time}"
                    text += f"\n{finished_str}"
            text += f'\n{format_seconds(learn_sec)}'
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
            # 不含 done_time 字段
        }
        if "done_time" in new_node:
            del new_node["done_time"]
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
        import time
        node, _ = self.get_selected()
        if node is None:
            return
        if not node.get("done", False):
            node["done"] = True
            node["done_time"] = int(time.time())
        else:
            node["done"] = False
            if "done_time" in node:
                del node["done_time"]
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
        # Start Learning 作为主菜单第一个选项
        menu.addAction("Start Learning", self.start_study)
        # Toggle Done/Undone 作为主菜单
        menu.addAction("Toggle Done/Undone", self.toggle_done)
        # Color 子菜单
        color_menu = menu.addMenu("Color")
        color_menu.addAction("Change Color", self.change_node_color)
        color_menu.addAction("Set to Default Color", self.set_node_default_color)
        # Operation 子菜单
        op_menu = menu.addMenu("Operation")
        op_menu.addAction("Add Child Node", self.add_node)
        op_menu.addAction("Delete Node", self.del_node)
        op_menu.addAction("Rename Node", self.rename_node)
        op_menu.addAction("Move Left", lambda: self.move_node(-1))
        op_menu.addAction("Move Right", lambda: self.move_node(1))
        global_pos = self.view.mapToGlobal(pos)
        menu.exec_(global_pos)

    def set_node_default_color(self):
        node, _ = self.get_selected()
        if node is None:
            return
        if "color" in node:
            del node["color"]
            save_data(self.data)
            self.main_window.refresh_all()

    def change_node_color(self):
        node, _ = self.get_selected()
        if node is None:
            return
        from PyQt5.QtWidgets import QColorDialog
        color = QColorDialog.getColor()
        if color.isValid():
            node["color"] = color.name()
            save_data(self.data)
            self.main_window.refresh_all()