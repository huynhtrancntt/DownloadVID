python -m PyInstaller --onefile --name=HT_DownloadVID "--add-binary=ffmpeg\ffmpeg.exe:ffmpeg" "--add-binary=venv\Scripts\yt-dlp.exe:." --hidden-import=subprocess App.py

copy venv\Scripts\yt-dlp.exe dist\