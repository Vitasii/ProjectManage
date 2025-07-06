from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QMessageBox, QSizePolicy, QSpacerItem
from PyQt5.QtCore import QTimer, Qt
import time
import datetime
import json
import project_tree
import db

DATA_FILE = "data.json"

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def find_and_update_lastreview_by_id(node, target_id, ts):
    if node.get("id") == target_id:
        node["lastreview"] = ts
        return True
    for ch in node.get("children", []):
        if find_and_update_lastreview_by_id(ch, target_id, ts):
            return True
    return False

class TimerWidget(QWidget):
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.setMinimumSize(400, 300)

        outer_layout = QVBoxLayout(self)
        outer_layout.setAlignment(Qt.AlignCenter)
        outer_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        inner_layout = QVBoxLayout()
        inner_layout.setAlignment(Qt.AlignCenter)

        self.label = QLabel("00:00:00")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-size: 48px; font-weight: bold;")
        inner_layout.addWidget(self.label)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(30)
        btn_layout.setAlignment(Qt.AlignCenter)

        self.btn_start = QPushButton("Start")
        self.btn_start.setFixedSize(100, 50)
        self.btn_start.setStyleSheet("font-size: 20px;")
        btn_layout.addWidget(self.btn_start)

        self.btn_pause = QPushButton("Pause")
        self.btn_pause.setFixedSize(100, 50)
        self.btn_pause.setStyleSheet("font-size: 20px;")
        btn_layout.addWidget(self.btn_pause)

        self.btn_end = QPushButton("End")
        self.btn_end.setFixedSize(100, 50)
        self.btn_end.setStyleSheet("font-size: 20px;")
        btn_layout.addWidget(self.btn_end)

        inner_layout.addLayout(btn_layout)
        outer_layout.addLayout(inner_layout)
        outer_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.start_time = None
        self.paused = False
        self.intervals = []
        self.current_node = None
        self.mode = None  # "learn" or "review"

        self.btn_start.clicked.connect(self.start)
        self.btn_pause.clicked.connect(self.pause)
        self.btn_end.clicked.connect(self.end)

    def set_node(self, node, mode):
        self.current_node = node
        self.mode = mode
        self.label.setText("00:00:00")
        self.start_time = None
        self.paused = False
        self.intervals = []

    def start(self):
        if not self.start_time:
            self.start_time = time.time()
            self.intervals = [(self.start_time, None)]
        elif self.paused:
            self.paused = False
            resume_time = time.time()
            self.intervals.append((resume_time, None))
        self.timer.start(1000)

    def pause(self):
        if not self.paused and self.start_time:
            self.paused = True
            self.intervals[-1] = (self.intervals[-1][0], time.time())
            self.timer.stop()

    def end(self):
        if not self.start_time:
            return
        if not self.paused:
            self.intervals[-1] = (self.intervals[-1][0], time.time())
        self.timer.stop()
        total = sum(e-s for s, e in self.intervals if e)
        msg = f"Total {'Learning' if self.mode=='learn' else 'Review'} Time: {int(total)} seconds\nIntervals:\n"
        for s, e in self.intervals:
            if e:
                msg += f"{time.strftime('%H:%M:%S', time.localtime(s))} - {time.strftime('%H:%M:%S', time.localtime(e))}\n"
        QMessageBox.information(self, "Finished", msg)
        if self.current_node is not None and self.mode in ("learn", "review"):
            node_id = self.current_node.get("id")
            date = datetime.datetime.now().strftime("%Y-%m-%d")
            dbfile = db.DB_LEARN if self.mode == "learn" else db.DB_REVIEW
            for s, e in self.intervals:
                if e:
                    db.add_record(dbfile, node_id, date, int(s), int(e))
            # 复习后自动更新 lastreview
            if self.mode == "review":
                data = project_tree.load_data()
                ts = int(time.time())
                find_and_update_lastreview_by_id(data, node_id, ts)
                save_data(data)
        if self.main_window:
            self.main_window.refresh_all()
        self.label.setText("00:00:00")
        self.start_time = None
        self.paused = False
        self.intervals = []
        self.current_node = None
        self.mode = None

    def update_time(self):
        if not self.start_time:
            return
        now = time.time()
        total = sum((e-s) for s, e in self.intervals if e) + (now - self.intervals[-1][0] if not self.paused else 0)
        h, rem = divmod(int(total), 3600)
        m, s = divmod(rem, 60)
        self.label.setText(f"{h:02d}:{m:02d}:{s:02d}")