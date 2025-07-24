#!/bin/bash

# 启动后端API服务器
echo "Starting backend API server..."
cd backend
python -m pip install -r requirements.txt
python main.py &
BACKEND_PID=$!

# 等待后端启动
echo "Waiting for backend to start..."
sleep 3

# 启动Flutter应用 (仅限开发环境)
echo "Starting Flutter app..."
cd ../frontend
flutter pub get
flutter run

# 清理：当Flutter应用退出时，停止后端服务
kill $BACKEND_PID
