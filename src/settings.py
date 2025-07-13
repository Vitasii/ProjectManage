import json, os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QColorDialog, QPushButton, QSpinBox, QHBoxLayout

SETTINGS_FILE = "data/settings.json"
DEFAULT_COLORS = {
    "project_unfinished": "#A0A0A0",
    "project_finished": "#90EE90",
    "review_active": "#ffd54f",
    "review_inactive": "#A0A0A0",
    "tree_x_offset": 300,
    "tree_y_offset": 120
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
        # 颜色设置
        for key, label in [
            ("project_unfinished", "Project_unfinished Color"),
            ("project_finished", "Project_finished Color"),
            ("review_active", "Review_active Color"),
            ("review_inactive", "Review_inactive Color")
        ]:
            l = QLabel(f"{label}: {self.colors[key]}")
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

        self.setLayout(layout)

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