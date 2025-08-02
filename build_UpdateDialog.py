import PyInstaller.__main__

PyInstaller.__main__.run([
    '--onefile',
    '--noconsole',  # Ẩn cửa sổ console
    '--name=Update',
    '--icon=ico.ico',  # Thêm icon cho executable
    '--clean',      # Xóa cache trước khi build
    '--noconfirm',  # Không hỏi xác nhận khi ghi đè
    
    # Thêm các file cần thiết
    '--add-data=ico.ico;.',  # Thêm file icon vào bundle
    
    # Hidden imports
    '--hidden-import=subprocess',
    '--hidden-import=PySide6.QtCore',
    '--hidden-import=PySide6.QtWidgets',
    '--hidden-import=PySide6.QtGui',
    
    'UpdateDialog.py'
])