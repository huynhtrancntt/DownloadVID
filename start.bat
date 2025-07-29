@echo off
chcp 65001 >nul
title HT DownloadVID v1.0

REM Kích hoạt môi trường ảo và chạy ứng dụng
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    python App.py
) else (
    echo ❌ Môi trường ảo chưa được tạo
    echo 🔧 Vui lòng chạy run_app.bat trước
    pause
) 