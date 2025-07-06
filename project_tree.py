import json, os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene, QMenu, QInputDialog, QMessageBox
from PyQt5.QtCore import Qt
from tree_base import NodeItem, EdgeLine
from settings import load_settings
from PyQt5.QtGui import QPainter

DATA_FILE = "data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"name": "Root", "children": [], "pos": [0, 0], "done": False, "history": {"learn": {}, "review": {}}}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def total_learn_time(node):
    # Recursively sum up learning time for this node and all children
    self_time = sum(
        e["end"] - e["start"]
        for day in node.get("history", {}).get("learn", {}).values()
        for e in day
    )
    return self_time + sum(total_learn_time(ch) for ch in node.get("children", []))

class ProjectTreeWidget(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.settings = load_settings()
        self.data = load_data()
        layout = QVBoxLayout(self)
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
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
        def all_overlap(node):
            if node.get("pos", [0,0]) != [0,0]:
                return False
            return all(all_overlap(ch) for ch in node.get("children", []))
        if all_overlap(self.data):
            layout_tree(self.data)
        def draw_tree(node, parent_item=None):
            color = self.settings["project_finished"] if node.get("done") else self.settings["project_unfinished"]
            total_learn = total_learn_time(node)
            item = NodeItem(node, color)
            item.node_text = lambda: f'{node["name"]}\nLearn:{int(total_learn)}s'
            item.text.setPlainText(item.node_text())
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
        for item in self.node_items:
            item.update_lines = self.update_all_edges

    def update_all_edges(self):
        for edge in self.edges:
            edge.update_position()

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

    def add_node(self):
        node, _ = self.get_selected()
        if node is None:
            node = self.data
        name, ok = QInputDialog.getText(self, "Add Child Node", "Node Name:")
        if ok and name:
            if "children" not in node:
                node["children"] = []
            px, py = node.get("pos", [0, 0])
            node["children"].append({
                "name": name, "children": [], "pos": [px, py+120], "done": False, "history": {"learn": {}, "review": {}}
            })
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
        menu.exec_(self.view.mapToGlobal(pos))