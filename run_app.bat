@echo off
chcp 65001 >nul
title HT DownloadVID v1.0 - Launcher

echo ========================================
echo    HT DownloadVID v1.0 - Launcher
echo ========================================
echo.

REM Kiểm tra Python có được cài đặt không
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Lỗi: Python chưa được cài đặt hoặc không có trong PATH
    echo 📥 Vui lòng tải và cài đặt Python từ: https://python.org
    echo.
    pause
    exit /b 1
)

echo ✅ Python đã được cài đặt
python --version

REM Kiểm tra thư mục môi trường ảo có tồn tại không
if not exist "venv" (
    echo.
    echo 🔧 Đang tạo môi trường ảo...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ Lỗi: Không thể tạo môi trường ảo
        pause
        exit /b 1
    )
    echo ✅ Môi trường ảo đã được tạo thành công
) else (
    echo ✅ Môi trường ảo đã tồn tại
)

echo.
echo 🚀 Đang kích hoạt môi trường ảo...
call venv\Scripts\activate.bat

REM Kiểm tra file requirements.txt có tồn tại không
if not exist "requirements.txt" (
    echo ❌ Lỗi: Không tìm thấy file requirements.txt
    pause
    exit /b 1
)

echo.
echo 📦 Đang kiểm tra và cài đặt dependencies...
pip install -r requirements.txt --quiet --disable-pip-version-check

if errorlevel 1 (
    echo ❌ Lỗi: Không thể cài đặt dependencies
    pause
    exit /b 1
)

echo ✅ Dependencies đã được cài đặt thành công

REM Kiểm tra file App.py có tồn tại không
if not exist "App.py" (
    echo ❌ Lỗi: Không tìm thấy file App.py
    pause
    exit /b 1
)

echo.
echo 🎬 Đang khởi động ứng dụng...
echo ========================================
echo.

REM Chạy ứng dụng
python App.py

echo.
echo ========================================
echo 🔚 Ứng dụng đã đóng
echo.
pause 