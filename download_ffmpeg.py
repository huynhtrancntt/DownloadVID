#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Download ffmpeg for build
"""

import os
import urllib.request
import zipfile
import shutil
from pathlib import Path

def download_ffmpeg():
    """Tải ffmpeg"""
    ffmpeg_dir = Path("ffmpeg_temp")
    
    # Tạo thư mục
    if ffmpeg_dir.exists():
        shutil.rmtree(ffmpeg_dir)
    ffmpeg_dir.mkdir()
    
    # URL ffmpeg
    ffmpeg_url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
    temp_zip = ffmpeg_dir / "ffmpeg.zip"
    
    print("📥 Đang tải ffmpeg...")
    
    # Tải file
    with urllib.request.urlopen(ffmpeg_url) as response:
        total_size = int(response.headers.get('Content-Length', 0))
        downloaded = 0
        
        with open(temp_zip, 'wb') as f:
            while True:
                chunk = response.read(8192)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    print(f"\r📥 Đã tải: {percent:.1f}%", end="", flush=True)
    
    print("\n✅ Đã tải xong ffmpeg")
    
    # Giải nén
    print("📂 Đang giải nén...")
    with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
        zip_ref.extractall(ffmpeg_dir)
    
    # Tìm và copy ffmpeg.exe
    for root, dirs, files in os.walk(ffmpeg_dir):
        if 'ffmpeg.exe' in files:
            source_exe = Path(root) / 'ffmpeg.exe'
            shutil.copy2(source_exe, ffmpeg_dir / 'ffmpeg.exe')
            break
    
    # Dọn dẹp
    temp_zip.unlink()
    for item in ffmpeg_dir.iterdir():
        if item.is_dir() and item.name.startswith('ffmpeg-'):
            shutil.rmtree(item)
    
    if (ffmpeg_dir / 'ffmpeg.exe').exists():
        size_mb = (ffmpeg_dir / 'ffmpeg.exe').stat().st_size / (1024 * 1024)
        print(f"✅ Đã cài đặt ffmpeg.exe ({size_mb:.1f} MB)")
        return True
    else:
        print("❌ Không tìm thấy ffmpeg.exe")
        return False

if __name__ == "__main__":
    download_ffmpeg() 