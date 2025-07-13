import sys
from PyQt5.QtCore import Qt, QCoreApplication
QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget, QAction, QMenuBar
from settings import SettingsWidget
from timer import TimerWidget
from project_tree import ProjectTreeWidget
from review import ReviewWidget
from stats import StatsWidget
import db

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VisProject")
        self.resize(1000, 700)
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        
        # 记录跳转到timer之前的页面索引
        self.previous_page_index = 2  # 默认为Projects页面

        db.init_db()  # 初始化数据库

        self.settings = SettingsWidget()
        self.project = ProjectTreeWidget(self)
        self.review = ReviewWidget(self)
        self.stats = StatsWidget(self)
        self.timer = TimerWidget(self)
        from timeline_plotly import TimelinePlotlyWidget
        self.timeline_plotly = TimelinePlotlyWidget(self)

        self.stack.addWidget(self.settings)   # 0
        self.stack.addWidget(self.timer)      # 1
        self.stack.addWidget(self.project)    # 2
        self.stack.addWidget(self.review)     # 3
        self.stack.addWidget(self.stats)      # 4
        self.stack.addWidget(self.timeline_plotly)   # 5

        menubar = QMenuBar(self)
        self.setMenuBar(menubar)
        # 修改：隐藏Timer选项，只保留其他页面
        pages = ["Settings", "Projects", "Review", "Stats", "Timeline"]
        page_indices = [0, 2, 3, 4, 5]
        for i, name in enumerate(pages):
            act = QAction(name, self)
            act.triggered.connect(lambda _, idx=page_indices[i]: self.stack.setCurrentIndex(idx))
            menubar.addAction(act)

    def show_timer(self, node, mode):
        # 记录当前页面索引
        self.previous_page_index = self.stack.currentIndex()
        self.stack.setCurrentIndex(1)
        self.timer.set_node(node, mode)

    def return_from_timer(self):
        """从timer返回到之前的页面"""
        self.stack.setCurrentIndex(self.previous_page_index)

    def closeEvent(self, event):
        """重写关闭事件，检查timer状态"""
        if self.timer.is_timing():
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(
                self, 
                "计时器正在运行", 
                "计时器正在运行中，请先结束计时再关闭程序。",
                QMessageBox.Ok
            )
            event.ignore()  # 忽略关闭事件，阻止关闭
        else:
            event.accept()  # 接受关闭事件，允许关闭

    def refresh_all(self):
        self.project.refresh()
        self.review.refresh()
        self.stats.refresh()
        if hasattr(self, 'timeline_plotly'):
            self.timeline_plotly.refresh_timeline()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    from PyQt5.QtGui import QFont
    
    # 设置全局字体为霞鹜文楷
    font = QFont("霞鹜文楷", 12)
    font.setHintingPreference(QFont.PreferDefaultHinting)
    app.setFont(font)
    
    # 设置全局样式表，确保所有组件都使用霞鹜文楷字体
    app.setStyleSheet("""
        * {
            font-family: '霞鹜文楷';
        }
        QMenuBar {
            font-family: '霞鹜文楷';
            font-size: 12px;
        }
        QMenu {
            font-family: '霞鹜文楷';
            font-size: 12px;
        }
        QMessageBox {
            font-family: '霞鹜文楷';
        }
        QInputDialog {
            font-family: '霞鹜文楷';
        }
    """)
    
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())