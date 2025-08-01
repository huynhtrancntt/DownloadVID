@echo off
chcp 65001 >nul
title HT DownloadVID v1.0 - Installation

echo ========================================
echo   HT DownloadVID v1.0 - Installation
echo ========================================
echo.

REM Kiểm tra Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Lỗi: Python chưa được cài đặt
    echo 📥 Tải Python tại: https://python.org
    pause
    exit /b 1
)

echo ✅ Python: 
python --version
echo.

REM Tạo môi trường ảo
if not exist "venv" (
    echo 🔧 Tạo môi trường ảo...
    python -m venv venv
    echo ✅ Môi trường ảo đã tạo
) else (
    echo ✅ Môi trường ảo đã tồn tại
)

echo.
echo 🚀 Kích hoạt môi trường ảo...
call venv\Scripts\activate.bat

echo.
echo 📦 Cài đặt dependencies...
@REM pip install --upgrade pip
pip install -r requirements.txt

echo.
echo ✅ Cài đặt hoàn tất!
echo 🎬 Bạn có thể chạy ứng dụng bằng start.bat
echo.
pause 