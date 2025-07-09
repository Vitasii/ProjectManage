import json, os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QColorDialog, QPushButton

SETTINGS_FILE = "data/settings.json"
DEFAULT_COLORS = {
    "project_unfinished": "#A0A0A0",
    "project_finished": "#90EE90",
    "review_active": "#ffd54f",
    "review_inactive": "#A0A0A0"
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
        for key, label in [
            ("project_unfinished", "Project_unfinished Color"),
            ("project_finished", "Project_finished Color"),
            ("review_active", "Review_active Color"),
            ("review_inactive", "Review_inactive Color")
        ]:
            l = QLabel(f"{label}: {self.colors[key]}")
            btn = QPushButton("Modify")
            btn.clicked.connect(lambda _, k=key, lab=l: self.change_color(k, lab))
            layout.addWidget(l)
            layout.addWidget(btn)
            self.labels[key] = l
        self.setLayout(layout)

    def change_color(self, key, label):
        color = QColorDialog.getColor()
        if color.isValid():
            self.colors[key] = color.name()
            label.setText(f"{label.text().split(':')[0]}: {color.name()}")
            save_settings(self.colors)