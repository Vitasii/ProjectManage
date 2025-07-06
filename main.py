import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget, QAction, QMenuBar
from settings import SettingsWidget
from timer import TimerWidget
from project_tree import ProjectTreeWidget
from review import ReviewWidget
from stats import StatsWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VisProject")
        self.resize(1000, 700)
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # 页面
        self.settings = SettingsWidget()
        self.project = ProjectTreeWidget(self)
        self.review = ReviewWidget(self)
        self.stats = StatsWidget(self)
        self.timer = TimerWidget(self)  # 传递主窗口引用

        self.stack.addWidget(self.settings)   # 0
        self.stack.addWidget(self.timer)      # 1
        self.stack.addWidget(self.project)    # 2
        self.stack.addWidget(self.review)     # 3
        self.stack.addWidget(self.stats)     # 4

        menubar = QMenuBar(self)
        self.setMenuBar(menubar)
        pages = ["Settings", "Timer", "Projects", "Review", "Stats"]
        page_indices = [0, 1, 2, 3, 4]
        for i, name in enumerate(pages):
            act = QAction(name, self)
            act.triggered.connect(lambda _, idx=page_indices[i]: self.stack.setCurrentIndex(idx))
            menubar.addAction(act)

    def show_timer(self, node, mode):
        """切换到计时器页面，设置当前节点和结束回调
        mode: "learn" or "review"
        """
        self.stack.setCurrentIndex(1)
        self.timer.set_node(node, mode)

    def refresh_all(self):
        self.project.refresh()
        self.review.refresh()
        self.stats.refresh()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())