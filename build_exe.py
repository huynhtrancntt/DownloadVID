import PyInstaller.__main__

PyInstaller.__main__.run([
    '--onefile',
    '--noconsole',  # Ẩn cửa sổ console
    '--name=DownloadVID',
    '--icon=ico.ico',  # Thêm icon cho executable
    '--clean',      # Xóa cache trước khi build
    '--noconfirm',  # Không hỏi xác nhận khi ghi đè
    
    # Thêm các file cần thiết
    '--add-binary=ffmpeg/ffmpeg.exe;ffmpeg',
    '--add-binary=yt-dlp.exe;.',
    '--add-data=ico.ico;.',  # Thêm file icon vào bundle
    
    # Hidden imports
    '--hidden-import=subprocess',
    '--hidden-import=PySide6.QtCore',
    '--hidden-import=PySide6.QtWidgets',
    '--hidden-import=PySide6.QtGui',
    
    # Tối ưu hóa
    '--optimize=2',  # Tối ưu hóa bytecode
    
    'App.py'
])