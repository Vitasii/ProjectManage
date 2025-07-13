def get_base_dir():
    import sys, os
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(__file__)

#!/usr/bin/env python3
"""
VisProject - 项目管理工具启动脚本
"""

if __name__ == "__main__":
    import sys
    import os
    import traceback
    try:
        # 将src目录添加到Python路径（如果存在）
        src_path = os.path.join(get_base_dir(), 'src')
        if os.path.isdir(src_path) and src_path not in sys.path:
            sys.path.insert(0, src_path)
        # 导入并运行主程序
        try:
            from src.main import MainWindow
        except ModuleNotFoundError:
            # 如果 src 目录不存在，尝试直接导入 main
            sys.path.insert(0, get_base_dir())
            from src.main import MainWindow
        from PyQt5.QtWidgets import QApplication
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        # 捕获所有异常并写入 error.log
        error_log = os.path.join(get_base_dir(), 'error.log')
        with open(error_log, 'w', encoding='utf-8') as f:
            f.write(traceback.format_exc())
        raise
