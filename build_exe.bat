@echo off
chcp 65001 >nul
title HT DownloadVID - Build to EXE

echo ========================================
echo   HT DownloadVID - Build to EXE
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

REM Kích hoạt môi trường ảo nếu có
if exist "venv\Scripts\activate.bat" (
    echo 🚀 Kích hoạt môi trường ảo...
    call venv\Scripts\activate.bat
    echo.
)

REM Chạy script build
echo 🔨 Bắt đầu quá trình đóng gói...
echo.
python build_exe.py

echo.
echo ========================================
echo 🏁 Quá trình build hoàn tất
echo.
pause 