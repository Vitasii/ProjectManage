import json, os, sys
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QColorDialog, QPushButton, QSpinBox, QHBoxLayout

def get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SETTINGS_FILE = os.path.join(get_base_dir(), "data", "settings.json")
DEFAULT_COLORS = {
    "default_color": "#A0A0A0",
    "toggle_done_color_project_tree": "#90EE90",
    "start_review_color": "#ffd54f",
    "toggle_done_color_stat": "#90caf9",
    "tree_x_offset": 300,
    "tree_y_offset": 120,
    "timeline_num_segments": 9
}

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_COLORS.copy()

def save_settings(data):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

class SettingsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.colors = load_settings()
        layout = QVBoxLayout(self)
        self.labels = {}
        # 新颜色设置
        color_settings = [
            ("default_color", "Default Node Color (所有图默认)"),
            ("toggle_done_color_project_tree", "Toggle Done Color in Project Tree (仅Project Tree)"),
            ("start_review_color", "Start Review Color (仅Review)") ,
            ("toggle_done_color_stat", "Toggle Done Color in Stat (仅Stat)")
        ]
        for key, label in color_settings:
            l = QLabel(f"{label}: {self.colors.get(key, '')}")
            l.setStyleSheet("font-family: '霞鹜文楷'; font-size: 20px;")
            btn = QPushButton("Modify")
            btn.setStyleSheet("font-family: '霞鹜文楷'; font-size: 20px;")
            btn.clicked.connect(lambda _, k=key, lab=l: self.change_color(k, lab))
            layout.addWidget(l)
            layout.addWidget(btn)
            self.labels[key] = l

        # tree_x_offset 设置
        x_layout = QHBoxLayout()
        x_label = QLabel("Tree X Offset:")
        x_label.setStyleSheet("font-family: '霞鹜文楷'; font-size: 20px;")
        self.x_spin = QSpinBox()
        self.x_spin.setStyleSheet("font-family: '霞鹜文楷'; font-size: 20px;")
        self.x_spin.setRange(50, 1000)
        self.x_spin.setValue(int(self.colors.get("tree_x_offset", 300)))
        self.x_spin.valueChanged.connect(self.save_offsets)
        x_layout.addWidget(x_label)
        x_layout.addWidget(self.x_spin)
        layout.addLayout(x_layout)

        # tree_y_offset 设置
        y_layout = QHBoxLayout()
        y_label = QLabel("Tree Y Offset:")
        y_label.setStyleSheet("font-family: '霞鹜文楷'; font-size: 20px;")
        self.y_spin = QSpinBox()
        self.y_spin.setStyleSheet("font-family: '霞鹜文楷'; font-size: 20px;")
        self.y_spin.setRange(50, 1000)
        self.y_spin.setValue(int(self.colors.get("tree_y_offset", 120)))
        self.y_spin.valueChanged.connect(self.save_offsets)
        y_layout.addWidget(y_label)
        y_layout.addWidget(self.y_spin)
        layout.addLayout(y_layout)

        # 时间线图数量设置
        timeline_layout = QHBoxLayout()
        timeline_label = QLabel("Timeline Segments (时间线图数量):")
        timeline_label.setStyleSheet("font-family: '霞鹜文楷'; font-size: 20px;")
        self.timeline_spin = QSpinBox()
        self.timeline_spin.setStyleSheet("font-family: '霞鹜文楷'; font-size: 20px;")
        self.timeline_spin.setRange(1, 24)
        self.timeline_spin.setValue(int(self.colors.get("timeline_num_segments", 9)))
        self.timeline_spin.valueChanged.connect(self.save_timeline_num_segments)
        timeline_layout.addWidget(timeline_label)
        timeline_layout.addWidget(self.timeline_spin)
        layout.addLayout(timeline_layout)
        self.setLayout(layout)
    def save_timeline_num_segments(self):
        self.colors["timeline_num_segments"] = self.timeline_spin.value()
        save_settings(self.colors)

    def change_color(self, key, label):
        color = QColorDialog.getColor()
        if color.isValid():
            self.colors[key] = color.name()
            label.setText(f"{label.text().split(':')[0]}: {color.name()}")
            save_settings(self.colors)

    def save_offsets(self):
        self.colors["tree_x_offset"] = self.x_spin.value()
        self.colors["tree_y_offset"] = self.y_spin.value()
        save_settings(self.colors)