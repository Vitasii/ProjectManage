@echo off
REM Windows启动脚本

echo Starting backend API server...
cd backend
python -m pip install -r requirements.txt
start /B python main.py

echo Waiting for backend to start...
timeout /t 3 /nobreak

echo Checking Flutter installation...
flutter --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo Flutter not found! Please install Flutter or use one of these alternatives:
    echo.
    echo 1. Install Flutter: https://docs.flutter.dev/get-started/install/windows
    echo 2. Use backend only: start_backend_only.bat
    echo 3. Use web interface: Open web_interface.html in your browser
    echo.
    echo Backend API is running at: http://localhost:8000
    echo API Documentation: http://localhost:8000/docs
    echo.
    pause
    exit /b 1
)

echo Starting Flutter app...
cd ..\frontend
flutter pub get
flutter run

pause
