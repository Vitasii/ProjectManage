# Flutter 安装指南

## Windows 安装步骤

### 1. 下载 Flutter SDK

- 访问: https://docs.flutter.dev/get-started/install/windows
- 下载 Flutter SDK ZIP 文件
- 解压到 `C:\src\flutter` (或您选择的目录)

### 2. 添加环境变量

- 打开 "系统属性" > "环境变量"
- 在用户变量中找到 "Path"，点击编辑
- 添加 `C:\src\flutter\bin` (根据您的安装路径调整)

### 3. 验证安装

打开新的命令提示符窗口，运行：

```cmd
flutter doctor
```

### 4. 安装 Android 工具链 (如果要构建 Android 应用)

- 安装 Android Studio
- 安装 Android SDK
- 运行 `flutter doctor --android-licenses` 接受许可证

## 快速测试

```cmd
flutter --version
flutter doctor
```

## 如果无法安装 Flutter

可以使用下面的纯后端方案运行项目。
