#!/usr/bin/env python3
"""
VisProject - 项目管理工具启动脚本
"""

if __name__ == "__main__":
    import sys
    import os
    
    # 将src目录添加到Python路径
    src_path = os.path.join(os.path.dirname(__file__), 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    
    # 导入并运行主程序
    from main import MainWindow
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
