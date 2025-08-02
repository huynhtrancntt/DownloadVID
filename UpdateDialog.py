import sys
import os
import subprocess
import glob
import logging
import requests
import json
import webbrowser
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QPushButton,
    QTextEdit, QCheckBox, QComboBox, QRadioButton,
    QHBoxLayout, QButtonGroup, QMessageBox, QProgressBar, QListWidget, QListWidgetItem,
    QFileDialog, QMenuBar, QMenu, QDialog
)
from PySide6.QtCore import Qt, QThread, Signal, QSettings, QTimer
from PySide6.QtGui import QScreen, QAction, QIcon
import shutil
import zipfile

os.system("taskkill /f /im DownloadVID.exe")
# Thiết lập logging


def setup_logging():
    """Thiết lập hệ thống logging"""
    log_file = os.path.join(os.getcwd(), "DownloadVID.log")

    # Tạo logger
    logger = logging.getLogger('DownloadVID')
    logger.setLevel(logging.DEBUG)

    # Xóa các handler cũ nếu có
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # File handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)

    # Console handler (chỉ khi có console)
    if hasattr(sys, '_MEIPASS'):
        # Đang chạy từ exe, không có console
        console_handler = None
    else:
        # Đang chạy từ Python, có console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    if console_handler:
        console_handler.setFormatter(formatter)

    # Thêm handlers
    logger.addHandler(file_handler)
    if console_handler:
        logger.addHandler(console_handler)

    return logger


# Khởi tạo logger
logger = setup_logging()

# Phiên bản ứng dụng
APP_VERSION = "1.1.0"
# URL để kiểm tra phiên bản mới
UPDATE_CHECK_URL = "https://raw.githubusercontent.com/huynhtrancntt/auto_update/main/update.json"


def debug_print(message):
    """In debug message - sẽ ghi vào file log khi không có console"""
    logger.info(message)
    # Vẫn giữ print cho compatibility
    try:
        print(message)
    except:
        pass  # Bỏ qua nếu không có console

def resource_path(relative_path):
    """Trả về đường dẫn tương đối đến file resource"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)



class UpdateChecker(QThread):
    """Worker thread để kiểm tra update"""
    update_available = Signal(dict)
    no_update = Signal()
    error_occurred = Signal(str)
    progress_update = Signal(int, str)  # progress, message
   
    def __init__(self):
        super().__init__()

    def run(self):
        """Kiểm tra phiên bản mới"""
        try:
            debug_print("🔍 Đang kiểm tra phiên bản mới...")
            self.progress_update.emit(30, "🔄 Đang kiểm tra...")

            # Gửi request để lấy thông tin release mới nhất
            response = requests.get(UPDATE_CHECK_URL, timeout=10)
            self.progress_update.emit(60, "📥 Đang xử lý response...")

            if response.status_code == 200:
                release_data = response.json()
                latest_version = release_data.get(
                    'tag_name', '').replace('v', '')
                release_name = release_data.get('name', '')
                release_notes = release_data.get('body', '')
                # Lấy download URL từ JSON response
                download_url = release_data.get('download_url', '')
                if not download_url:
                    # Fallback nếu không có download_url, có thể thử các key khác
                    download_url = release_data.get('html_url', '')
                    if not download_url:
                        download_url = release_data.get('zipball_url', '')
                
                # Kiểm tra tính hợp lệ của download URL
                if not download_url or not download_url.startswith(('http://', 'https://')):
                    self.error_occurred.emit("Không tìm thấy URL download hợp lệ trong response")
                    return
                
                published_at = release_data.get('published_at', '')
                debug_print(f"📥 Download URL từ JSON: {download_url}")
                self.progress_update.emit(80, "🔍 Đang so sánh phiên bản...")
                
                # So sánh phiên bản
                if self._is_newer_version(latest_version, APP_VERSION):
                    update_info = {
                        'version': latest_version,
                        'name': release_name,
                        'notes': release_notes,
                        'download_url': download_url,
                        'published_at': published_at
                    }
                    self.progress_update.emit(100, "🎉 Tìm thấy phiên bản mới!")
                    self.update_available.emit(update_info)
                else:
                    self.progress_update.emit(100, "✅ Phiên bản hiện tại là mới nhất")
                    self.no_update.emit()
            else:
                self.error_occurred.emit(
                    f"HTTP {response.status_code}: Không thể kết nối đến server")

        except requests.exceptions.Timeout:
            self.error_occurred.emit(
                "Timeout: Không thể kết nối đến server trong thời gian quy định")
        except requests.exceptions.ConnectionError:
            self.error_occurred.emit("Lỗi kết nối: Kiểm tra kết nối internet")
        except Exception as e:
            self.error_occurred.emit(f"Lỗi không xác định: {str(e)}")

    def _is_newer_version(self, latest, current):
        """So sánh 2 phiên bản"""
        try:
            # Chuyển đổi version string thành list số
            latest_parts = [int(x) for x in latest.split('.')]
            current_parts = [int(x) for x in current.split('.')]

            # Đảm bảo cả 2 list có cùng độ dài
            max_len = max(len(latest_parts), len(current_parts))
            latest_parts.extend([0] * (max_len - len(latest_parts)))
            current_parts.extend([0] * (max_len - len(current_parts)))

            # So sánh từng phần
            for i in range(max_len):
                if latest_parts[i] > current_parts[i]:
                    return True
                elif latest_parts[i] < current_parts[i]:
                    return False

            return False  # Bằng nhau
        except:
            return False

class DownloadUpdateWorker(QThread):
    """Worker thread để tải về và giải nén update"""
    progress_signal = Signal(int)
    message_signal = Signal(str)
    finished_signal = Signal(bool, str)  # success, message

    def __init__(self, download_url, version):
        super().__init__()
        self.download_url = download_url
        self.version = version
        self.stop_flag = False

    def run(self):
        """Thực hiện download và extract"""
        try:
            # Tạo tên file
            output_file = f"update_v{self.version}.zip"
            extract_to = "temp_update"

            # Bước 1: Download file
            self.message_signal.emit("⬇️ Đang tải file cập nhật...")
            if not self._download_with_progress(self.download_url, output_file):
                return

            if self.stop_flag:
                self._cleanup(output_file, extract_to)
                return

            # Bước 2: Giải nén file
            self.message_signal.emit("📦 Đang giải nén file...")
            if not self._extract_and_install(output_file, extract_to):
                return

            if self.stop_flag:
                self._cleanup(output_file, extract_to)
                return

            # Bước 3: Hoàn thành
            self.message_signal.emit("✅ Cập nhật hoàn tất!")
            self.progress_signal.emit(100)
            self.finished_signal.emit(
                True, f"Cập nhật thành công! Ứng dụng sẽ khởi động lại.")

        except Exception as e:
            self.finished_signal.emit(False, f"Lỗi cập nhật: {str(e)}")

    def _download_with_progress(self, url, output_file):
        """Tải file với thanh tiến trình"""
        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            total_mb = total_size / (1024 * 1024)

            downloaded = 0
            chunk_size = 1024 * 1024  # 1MB

            with open(output_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if self.stop_flag:
                        f.close()
                        self.message_signal.emit("⏹ Đã dừng tải")
                        return False

                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        downloaded_mb = downloaded / (1024 * 1024)

                        if total_mb > 0:
                            percent = int((downloaded_mb / total_mb) * 50)  # 50% cho download
                            self.progress_signal.emit(percent)
                            self.message_signal.emit(
                                f"⬇️ Đang tải: {downloaded_mb:.1f}/{total_mb:.1f} MB ({percent}%)")
                        else:
                            self.message_signal.emit(
                                f"⬇️ Đã tải: {downloaded_mb:.1f} MB")

            self.message_signal.emit("✅ Tải xuống hoàn tất!")
            return True

        except Exception as e:
            self.message_signal.emit(f"❌ Lỗi tải xuống: {str(e)}")
            return False

    def _extract_and_install(self, zip_file, extract_to):
        """Giải nén và cài đặt cập nhật"""
        try:
            # Xóa thư mục tạm cũ nếu có
            if os.path.exists(extract_to):
                shutil.rmtree(extract_to)
            os.makedirs(extract_to)

            # Giải nén
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                total_files = len(file_list)

                for i, file_name in enumerate(file_list):
                    if self.stop_flag:
                        # Xóa thư mục extract và file zip
                        self._cleanup(zip_file, extract_to)
                        return False

                    zip_ref.extract(file_name, extract_to)
                    # 50% cho extract (từ 50% đến 100%)
                    percent = 50 + int((i + 1) / total_files * 50)
                    self.progress_signal.emit(percent)
                    self.message_signal.emit(f"📦 Giải nén: {file_name}")

            # Copy files
            self.message_signal.emit("📋 Đang cập nhật files...")
            current_dir = os.getcwd()

            copied_files = []
            for root, dirs, files in os.walk(extract_to):
                for file in files:
                    if self.stop_flag:
                        # Xóa thư mục extract và file zip
                        self._cleanup(zip_file, extract_to)
                        return False

                    src_file = os.path.join(root, file)
                    rel_path = os.path.relpath(src_file, extract_to)
                    dst_file = os.path.join(current_dir, rel_path)

                    # Tạo thư mục đích nếu chưa có
                    dst_dir = os.path.dirname(dst_file)
                    if dst_dir and not os.path.exists(dst_dir):
                        os.makedirs(dst_dir)

                    # Copy file
                    shutil.copy2(src_file, dst_file)
                    copied_files.append(rel_path)
                    self.message_signal.emit(f"📋 Cập nhật: {rel_path}")

            # Lưu phiên bản mới vào file
            # try:
            #     version_file = os.path.join(current_dir, "version.txt")
            #     with open(version_file, 'w', encoding='utf-8') as f:
            #         f.write(self.version)
            #     self.message_signal.emit(
            #         f"💾 Đã lưu phiên bản mới: {self.version}")
            # except Exception as e:
            #     self.message_signal.emit(f"⚠️ Không thể lưu phiên bản: {e}")

            # Dọn dẹp - xóa file zip và thư mục extract
            self.message_signal.emit("🧹 Đang dọn dẹp...")
            self._cleanup(zip_file, extract_to)

            self.progress_signal.emit(100)
            self.message_signal.emit(
                f"✅ Đã cập nhật {len(copied_files)} files")
            self.message_signal.emit("🎉 Cập nhật hoàn tất! Ứng dụng sẽ khởi động lại...")
            return True

        except Exception as e:
            self.message_signal.emit(f"❌ Lỗi giải nén: {str(e)}")
            # Xóa file zip và thư mục extract khi có lỗi
            self._cleanup(zip_file, extract_to)
            return False

    def _cleanup(self, zip_file, extract_to):
        """Dọn dẹp files tạm"""
        try:
            # Xóa file zip
            if os.path.exists(zip_file):
                os.remove(zip_file)
                self.message_signal.emit(f"🗑️ Đã xóa file: {os.path.basename(zip_file)}")
            
            # Xóa thư mục extract
            if os.path.exists(extract_to):
                shutil.rmtree(extract_to)
                self.message_signal.emit("🗑️ Đã xóa thư mục tạm")
        except Exception as e:
            self.message_signal.emit(f"⚠️ Lỗi khi dọn dẹp: {e}")

    def stop(self):
        """Dừng quá trình download"""
        self.stop_flag = True



class DownloaderApp(QWidget):
    """Ứng dụng chính để download video"""

    def __init__(self):
        super().__init__()
        self.worker = None
        self.update_checker = None  # Update checker thread
        self.download_worker = None  # Download worker thread
        self.settings = QSettings("HT Software", "DownloadVID")
        self.loading_settings = False  # Flag để tránh auto-save khi đang load
        self.is_manual_check = False  # Đổi tên biến để tránh xung đột với tên hàm
        self.init_ui()
        self.apply_styles()
        
        # Hiển thị progress bar ngay khi khởi động
        self.update_progress_bar.setVisible(True)
        self.update_status_label.setVisible(True)
        self.update_progress_bar.setValue(20)
        self.update_status_label.setText("Đang kiểm tra...")
        self.output_list.addItem("🔄 Đang kiểm tra phiên bản mới...")
        # Kiểm tra update tự động khi khởi động (sau 3 giây)
        QTimer.singleShot(2000, self.auto_check_update)

        # Kiểm tra phiên bản mới nếu vừa cập nhật
        self._check_recent_update()

        # Cuộn xuống cuối
        self.scroll_to_bottom()

    def closeEvent(self, event):
        """Xử lý khi đóng ứng dụng - dọn dẹp threads"""
        # Dừng và dọn dẹp threads
        if self.update_checker and self.update_checker.isRunning():
            self.update_checker.quit()
            self.update_checker.wait(1000)  # Đợi tối đa 1 giây
            
        if self.download_worker and self.download_worker.isRunning():
            self.download_worker.stop()
            self.download_worker.quit()
            self.download_worker.wait(1000)  # Đợi tối đa 1 giây
            
        event.accept()

    def _check_recent_update(self):
        """Kiểm tra xem có vừa cập nhật không"""
        global APP_VERSION

        try:
            version_file = os.path.join(os.getcwd(), "version.txt")
            if os.path.exists(version_file):
                with open(version_file, 'r', encoding='utf-8') as f:
                    updated_version = f.read().strip()

                # Nếu phiên bản trong file khác với APP_VERSION hiện tại
                if updated_version and updated_version != APP_VERSION:
                    # Hiển thị thông báo cập nhật thành công
                    QTimer.singleShot(
                        1000, lambda: self._show_update_success_message(updated_version))

                    # Cập nhật APP_VERSION trong runtime
                    old_version = APP_VERSION
                    APP_VERSION = updated_version

                    debug_print(
                        f"🎉 Cập nhật thành công từ v{old_version} lên v{APP_VERSION}")

                    # Xóa file version.txt sau khi đã xử lý
                    os.remove(version_file)

        except Exception as e:
            debug_print(f"⚠️ Lỗi kiểm tra phiên bản mới: {e}")

    def _show_update_success_message(self, new_version):
        """Hiển thị thông báo cập nhật thành công"""
        QMessageBox.information(
            self,
            "🎉 Cập nhật thành công!",
            f"✅ Ứng dụng đã được cập nhật thành công!\n\n"
            f"🔄 Phiên bản mới: v{new_version}\n"
            f"🚀 Ứng dụng đã sẵn sàng sử dụng với các tính năng mới!\n\n"
            f"Cảm ơn bạn đã sử dụng HT DownloadVID! 💖"
        )

    def init_ui(self):
        """Khởi tạo giao diện người dùng"""
        self.setWindowTitle(f"Update Auto v{APP_VERSION}")

        #Thiết lập icon cho cửa sổ
        icon_path = resource_path("ico.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.setMinimumWidth(800)
        # self.center_window()

        # Tạo layout chính
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Thêm menubar
        # self._create_menubar()
        # main_layout.addWidget(self.menubar)

        # Tạo layout cho nội dung chính
        self.layout = QVBoxLayout()
        main_layout.addLayout(self.layout)

        self._create_url_section()
        # self._create_mode_section()
        # self._create_subtitle_section()
        # self._create_options_section()
        # self._create_control_buttons(
        self._create_progress_section()
        self._create_log_section()

        # Auto-save sẽ được kết nối sau khi load_settings() hoàn thành


    def _create_url_section(self):
        """Tạo phần nhập URL"""
        # self.layout.addWidget(QLabel("📋 Nhập URL video:"))
        
        # Ẩn nút kiểm tra update - chỉ sử dụng auto check
        # Tạo layout cho progress bar (ẩn ban đầu)
        self.update_progress_layout = QHBoxLayout()
        
        # Progress bar cho update (ẩn ban đầu)
        self.update_progress_bar = QProgressBar()
        self.update_progress_bar.setVisible(False)
        self.update_progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #dee2e6;
                border-radius: 6px;
                text-align: center;
                height: 20px;
                background-color: #f8f9fa;
                color: #495057;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #17a2b8;
                border-radius: 4px;
            }
        """)
        self.update_progress_layout.addWidget(self.update_progress_bar)
        
        # Label cho update status (ẩn ban đầu)
        self.update_status_label = QLabel("")
        self.update_status_label.setVisible(False)
        self.update_status_label.setStyleSheet("""
            QLabel {
                color: #17a2b8;
                font-weight: bold;
                font-size: 12px;
                margin-left: 10px;
            }
        """)
        self.update_progress_layout.addWidget(self.update_status_label)
        
        self.layout.addLayout(self.update_progress_layout)

    def _create_progress_section(self):
        """Tạo thanh tiến trình"""
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.layout.addWidget(self.progress)

    def _create_log_section(self):
        """Tạo phần log"""
        self.output_list = QListWidget()
        # self.output_list.setWordWrap(True)  # Ẩn để tránh warning
        self.output_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.output_list.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.output_list.setMinimumHeight(0)  # Làm nhỏ lại
        self.output_list.setMaximumHeight(50)  # Ẩn hoàn toàn
        self.output_list.setVisible(True)  # Ẩn log section
        self.layout.addWidget(self.output_list)
    def center_window(self):
        """Căn giữa cửa sổ trên màn hình"""
        # self.resize(520, 700)

        screen = QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            window_geometry = self.frameGeometry()
            center_point = screen_geometry.center()
            window_geometry.moveCenter(center_point)
            self.move(window_geometry.topLeft())

    def _reset_ui_after_download(self):
        """Reset UI sau khi download xong hoặc dừng"""
        self.stop_button.setVisible(False)
        self.progress.setVisible(False)
        self.download_button.setEnabled(True)
        # self.output_list.setMinimumHeight(120)

    def scroll_to_bottom(self):
        """Cuộn xuống cuối danh sách"""
        self.output_list.scrollToBottom()

    def apply_styles(self):
        """Áp dụng stylesheet"""
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                font-size: 13px;
                font-family: "Segoe UI", Arial, sans-serif;
                color: #212529;
            }
            QPushButton {
                background-color: #28a745;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #ffffff;
            }
            QProgressBar {
                border: 2px solid #dee2e6;
                border-radius: 6px;
                text-align: center;
                height: 20px;
                background-color: #e9ecef;
                color: #495057;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #28a745;
                border-radius: 4px;
            }
            QListWidget {
                background-color: #2d3748;
                color: #e2e8f0;
                border: 2px solid #4a5568;
                border-radius: 6px;
                font-family: "Consolas", "Monaco", monospace;
                font-size: 12px;
                padding: 8px;
                selection-background-color: #4299e1;
                outline: none;
            }
            QListWidget::item {
                padding: 6px 8px;
                border-bottom: 1px solid #4a5568;
                min-height: 20px;
                word-break: break-word;
            }
            QListWidget::item:hover {
                background-color: #4a5568;
            }
            QListWidget::item:selected {
                background-color: #4299e1;
                color: #ffffff;
            }
            QTextEdit {
                background-color: #ffffff;
                border: 2px solid #ced4da;
                border-radius: 6px;
                padding: 8px;
                color: #495057;
                font-size: 13px;
            }
            QTextEdit:focus {
                border-color: #80bdff;
                outline: none;
            }
            QComboBox {
                background-color: #ffffff;
                border: 2px solid #ced4da;
                border-radius: 8px;
                padding: 10px 15px;
                color: #495057;
                font-size: 13px;
                font-weight: 500;
                min-height: 20px;
            }
            QComboBox:hover {
                border-color: #80bdff;
                background-color: #f8f9fa;
            }
            QComboBox:focus {
                border-color: #007bff;
                outline: none;
            }
            QLabel {
                color: #343a40;
                font-weight: 500;
                font-size: 13px;
                margin: 5px 0px;
            }
            QCheckBox {
                color: #495057;
                font-size: 13px;
                spacing: 8px;
                padding: 5px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #ced4da;
                border-radius: 3px;
                background-color: #ffffff;
            }
            QCheckBox::indicator:hover {
                border-color: #007bff;
                background-color: #f8f9fa;
            }
            QCheckBox::indicator:checked {
                background-color: #28a745;
                border-color: #28a745;
            }
            QRadioButton {
                color: #495057;
                font-size: 13px;
                spacing: 8px;
                padding: 5px;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #ced4da;
                border-radius: 9px;
                background-color: #ffffff;
            }
            QRadioButton::indicator:hover {
                border-color: #007bff;
                background-color: #f8f9fa;
            }
            QRadioButton::indicator:checked {
                background-color: #28a745;
                border-color: #28a745;
            }
            #lang-checkbox {
                color: #495057;
                font-size: 11px;
                font-weight: 500;
                spacing: 6px;
                padding: 3px 6px;
                margin: 1px;
                border: 1px solid #e9ecef;
                border-radius: 4px;
                background-color: #f8f9fa;
                max-width: 180px;
            }
            #lang-checkbox:hover {
                background-color: #e9ecef;
                border-color: #007bff;
            }
            #lang-checkbox::indicator {
                width: 14px;
                height: 14px;
                border: 2px solid #ced4da;
                border-radius: 2px;
                background-color: #ffffff;
            }
            #lang-checkbox::indicator:hover {
                border-color: #007bff;
                background-color: #f8f9fa;
            }
            #lang-checkbox::indicator:checked {
                background-color: #007bff;
                border-color: #007bff;
            }
        """)

 
    def show_log_file(self):
        """Hiển thị nội dung file log"""
        try:
            log_file = os.path.join(os.getcwd(), "DownloadVID.log")

            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    log_content = f.read()

                # Lấy 50 dòng cuối
                lines = log_content.splitlines()
                if len(lines) > 50:
                    display_content = '\n'.join(lines[-50:])
                    header = f"📝 Log File (50 dòng cuối / tổng {len(lines)} dòng)\n{'='*60}\n"
                else:
                    display_content = log_content
                    header = f"📝 Log File (tổng {len(lines)} dòng)\n{'='*60}\n"

                # Tạo dialog để hiển thị log
                log_dialog = QMessageBox(self)
                log_dialog.setWindowTitle("Log File")
                log_dialog.setText(header + display_content)
                # Full log trong detailed text
                log_dialog.setDetailedText(log_content)
                log_dialog.exec()

            else:
                QMessageBox.information(
                    self, "Log File", "📝 Chưa có file log nào được tạo.")

        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"❌ Không thể đọc file log: {e}")


    def auto_check_update(self):
        """Tự động kiểm tra update khi khởi động (hiển thị progress bar)"""
        # Progress bar đã được hiển thị từ __init__, chỉ cập nhật text
        self.update_progress_bar.setValue(50)
        self.update_status_label.setText("🔄 Đang kiểm tra phiên bản mới...")
        
        # Ẩn log output - không thêm log vào output list nữa
        self.output_list.addItem("=" * 50)
        self.output_list.addItem("🔄 Đang kiểm tra phiên bản mới...")
        self.scroll_to_bottom()
        
        self._start_update_check()

    def manual_check_update(self):
        """Kiểm tra update thủ công (không hiển thị nút)"""
        # Gọi auto_check_update thay vì hiển thị nút
        self.auto_check_update()

    def _start_update_check(self):
        """Bắt đầu kiểm tra update"""
        # Cập nhật progress bar
        self.update_progress_bar.setValue(20)
        self.update_status_label.setText("🔄 Đang kết nối server...")
        
        # Tạo và chạy update checker
        self.update_checker = UpdateChecker()
        self.update_checker.update_available.connect(self.on_update_available)
        self.update_checker.no_update.connect(self.on_no_update)
        self.update_checker.error_occurred.connect(self.on_update_error)
        self.update_checker.progress_update.connect(self.update_progress_and_status)
        self.update_checker.start()

    def on_update_available(self, update_info):
        """Xử lý khi có cập nhật"""
        # Cập nhật progress bar và status
        self.update_progress_bar.setValue(20)
        self.update_status_label.setText("🎉 Phiên bản mới có sẵn!")
        
        # Ẩn log output - không thêm log vào output list nữa
        self.output_list.addItem(f"🎉 Phiên bản mới có sẵn: v{update_info['version']}")
        self.output_list.addItem(f"📋 Tên phiên bản: {update_info.get('name', 'N/A')}")
        if update_info.get('notes'):
            self.output_list.addItem(f"📝 Ghi chú: {update_info['notes']}")
        
        #Tự động bắt đầu tải về
        self.output_list.addItem("🚀 Bắt đầu tải về cập nhật...")
        self.scroll_to_bottom()
        
        # Tạo và chạy download worker
        self.download_worker = DownloadUpdateWorker(
            update_info['download_url'], update_info['version'])
        self.download_worker.progress_signal.connect(self.update_download_progress)
        self.download_worker.message_signal.connect(self.add_download_log)
        self.download_worker.finished_signal.connect(self.on_download_finished)
        self.download_worker.start()

    def update_download_progress(self, value):
        """Cập nhật progress bar cho download"""
        self.update_progress_bar.setValue(value)
        if value < 50:
            self.update_status_label.setText(f"⬇️ Đang tải về... {value}%")
        else:
            self.update_status_label.setText(f"📦 Đang cài đặt... {value}%")

    def add_download_log(self, message):
        """Thêm log cho quá trình download - ẩn log"""
        # Ẩn log output
        self.output_list.addItem(message)
        self.scroll_to_bottom()
        pass

    def on_download_finished(self, success, message):
        """Xử lý khi tải về hoàn thành"""
        if success:
            # Ẩn log output
            self.output_list.addItem("✅ Cập nhật thành công!")
            self.output_list.addItem("🔄 Ứng dụng sẽ khởi động lại...")
            self.scroll_to_bottom()
            
            # Hiển thị thông báo thành công
            QMessageBox.information(self, "Cập nhật thành công", 
                                   f"✅ Cập nhật lên phiên bản v{self.download_worker.version} thành công!\n\n"
                                   f"🔄 Ứng dụng sẽ khởi động lại để áp dụng thay đổi.")
            
            # Tự động khởi động lại ứng dụng
            QApplication.instance().quit()
            os.system("taskkill /f /im DownloadVID.exe")
            os.system("taskkill /f /im Update.exe")
            subprocess.run([r"DownloadVID.exe"])
        else:
            # Ẩn log output
            self.output_list.addItem(f"❌ Lỗi cập nhật")
            self.scroll_to_bottom()
            
            # Hiển thị thông báo lỗi
            QMessageBox.warning(self, "Lỗi cập nhật", 
                               f"❌ Không thể cập nhật: {message}")
            
            # Ẩn progress bar sau 3 giây
            QTimer.singleShot(3000, self._hide_update_progress)

    def on_no_update(self):
        """Xử lý khi không có cập nhật"""
        # Cập nhật progress bar và status
        self.update_progress_bar.setValue(20)
        self.update_status_label.setText("✅ Phiên bản mới nhất")
        
        # Ẩn progress bar sau 3 giây
        QTimer.singleShot(3000, self._hide_update_progress)
        
        # Ẩn log output
        self.output_list.addItem("✅ Bạn đang sử dụng phiên bản mới nhất")
        self.output_list.addItem("Không có cập nhật mới.")
        self.scroll_to_bottom()

    def on_update_error(self, error_message):
        """Xử lý lỗi khi kiểm tra cập nhật"""
        # Cập nhật progress bar và status
        self.update_progress_bar.setValue(20)
        self.update_status_label.setText("❌ Lỗi kiểm tra")
        
        # Ẩn progress bar sau 3 giây
        QTimer.singleShot(3000, self._hide_update_progress)
        
        # Ẩn log output
        self.output_list.addItem(f"❌ Lỗi kiểm tra cập nhật")
        self.scroll_to_bottom()

    def _hide_update_progress(self):
        """Ẩn progress bar và status label"""
        self.update_progress_bar.setVisible(False)
        self.update_status_label.setVisible(False)

    def update_progress_and_status(self, progress, message):
        """Cập nhật progress bar và status label"""
        # Giữ progress ở 20% thay vì 100%
        self.update_progress_bar.setValue(20)
        self.update_status_label.setText(message)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = DownloaderApp()
    win.show()
    sys.exit(app.exec())
