# Project Manager - Flutter + FastAPI

## 项目结构

```
ProjectManage/
├── backend/                 # FastAPI后端
│   ├── main.py             # API服务器
│   └── requirements.txt    # Python依赖
├── frontend/               # Flutter前端
│   ├── lib/
│   │   ├── main.dart      # 应用入口
│   │   ├── models/        # 数据模型
│   │   ├── providers/     # 状态管理
│   │   ├── screens/       # 界面
│   │   └── services/      # API服务
│   └── pubspec.yaml       # Flutter依赖
├── data/                  # 数据文件（保留现有数据）
├── web_interface.html     # 临时Web界面（开发测试用）
├── start_backend_only.bat # 仅启动后端
├── start_dev.bat         # Windows开发启动脚本
└── start_dev.sh          # Linux/Mac开发启动脚本
```

## ✅ 已删除的文件

以下 PyQt5 相关文件已安全删除：

- `src/` 目录（所有 PyQt5 源代码）
- `run.py`（PyQt5 应用入口）
- `*.spec`（PyInstaller 配置文件）
- `build/` 和 `dist/`（PyInstaller 构建目录）
- `timeline_html/`（现由后端动态生成）
- 其他 PyInstaller 相关文件

## 技术栈

### 后端 (FastAPI)

- **FastAPI**: 现代 Python Web 框架
- **SQLite**: 本地数据库
- **Pydantic**: 数据验证
- **CORS**: 跨域支持

### 前端 (Flutter)

- **Flutter**: 跨平台 UI 框架
- **Provider**: 状态管理
- **HTTP**: API 通信
- **Material Design**: UI 设计

## 开发环境设置

### 1. 安装依赖

**后端:**

```bash
cd backend
pip install -r requirements.txt
```

**前端:**

```bash
cd frontend
flutter pub get
```

### 2. 运行应用

**方法 1: 使用启动脚本**

```bash
# Windows
start_dev.bat

# Linux/Mac
chmod +x start_dev.sh
./start_dev.sh
```

**方法 2: 手动启动**

```bash
# 启动后端 (终端1)
cd backend
python main.py

# 启动前端 (终端2)
cd frontend
flutter run
```

## API 接口

### 项目管理

- `GET /api/projects` - 获取项目树
- `POST /api/projects` - 保存项目树
- `POST /api/projects/node` - 创建节点
- `DELETE /api/projects/node/{id}` - 删除节点

### 时间记录

- `GET /api/records/{mode}/{node_id}` - 获取时间记录
- `POST /api/timer/complete` - 完成计时会话

### 统计数据

- `GET /api/stats/timeline` - 获取时间线数据

### 设置

- `GET /api/settings` - 获取设置
- `POST /api/settings` - 保存设置

## 部署

### Android APK 打包

```bash
cd frontend
flutter build apk --release
```

### Windows 桌面应用

```bash
cd frontend
flutter build windows --release
```

### Web 应用

```bash
cd frontend
flutter build web --release
```

## 数据迁移

现有的 PyQt5 应用数据完全兼容，数据库和 JSON 文件可以直接使用。

## 功能特性

✅ **已实现:**

- 项目树管理
- 计时功能
- 前后端分离架构
- 跨平台支持

🚧 **待实现:**

- 复习管理界面
- 统计图表
- 时间线可视化
- 数据同步

## 开发说明

1. **状态管理**: 使用 Provider 进行状态管理
2. **数据持久化**: 后端负责所有数据操作
3. **API 设计**: RESTful API 设计，便于扩展
4. **跨平台**: 一套代码，多端运行

## 下一步计划

1. 完善所有界面功能
2. 添加数据可视化
3. 实现云同步功能
4. 优化移动端体验
5. 添加推送通知
