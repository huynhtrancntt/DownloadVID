import PyInstaller.__main__

PyInstaller.__main__.run([
    '--onefile',
    '--name=HT_DownloadVID',
    '--add-binary=ffmpeg/ffmpeg.exe;ffmpeg',
    '--add-binary=venv/Scripts/yt-dlp.exe;.',
    '--hidden-import=subprocess',
    'App.py'
])