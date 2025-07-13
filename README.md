# VisProject

项目管理工具

## 项目结构

```
ProjectManage/
├── src/                    # 源代码目录
│   ├── __init__.py        # 包初始化文件
│   ├── main.py            # 主程序入口
│   ├── settings.py        # 设置模块
│   ├── timer.py           # 计时器模块
│   ├── project_tree.py    # 项目树模块
│   ├── review.py          # 复习模块
│   ├── stats.py           # 统计模块
│   ├── tree_base.py       # 树形基础组件
│   └── db.py              # 数据库模块
├── data/                  # 数据文件目录
├── run.py                 # 启动脚本
├── main.spec              # PyInstaller配置文件
└── README.md              # 本文件
```

## 运行方法

### 开发环境运行

```bash
python run.py
```

### 直接运行主程序（从 src 目录）

```bash
cd src
python main.py
```

### 打包为可执行文件

```bash
pyinstaller main.spec
```

## 修改说明

为了更好的代码组织，所有 Python 源文件都移动到了 `src` 目录中：

### 修改的文件：

1. **main.py** - 更新了导入路径
2. **timer.py** - 更新了导入路径
3. **stats.py** - 更新了导入路径
4. **project_tree.py** - 更新了导入路径
5. **review.py** - 更新了导入路径
6. **main.spec** - 更新了 PyInstaller 配置
7. **run.py** - 新增的启动脚本

### 新增的文件：

- `src/__init__.py` - Python 包初始化文件
- `run.py` - 应用程序启动脚本
- `README.md` - 项目说明文档

所有模块间的导入关系都已经正确更新，保持了原有的功能不变。
