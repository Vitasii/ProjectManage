@echo off
REM 仅启动后端API服务器的脚本

echo Starting Project Management API Server...
echo.
echo Backend API will be available at: http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo.

cd backend
python -m pip install -r requirements.txt
python main.py

echo.
echo Backend server stopped.
pause
