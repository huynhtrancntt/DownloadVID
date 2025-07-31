import sys
import os
import subprocess
import glob
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QPushButton,
    QTextEdit, QCheckBox, QComboBox, QRadioButton,
    QHBoxLayout, QButtonGroup, QMessageBox, QProgressBar, QListWidget, QListWidgetItem,
    QFileDialog
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QScreen


def resource_path(relative_path):
    """Trả về đường dẫn tương đối đến file resource"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


# Thiết lập đường dẫn ffmpeg và kiểm tra
ffmpeg_path = resource_path(os.path.join("ffmpeg", "ffmpeg.exe"))

# Gọi thử ffmpeg
try:
    result = subprocess.run([ffmpeg_path, "-version"], capture_output=True, text=True)
    print("✅ FFmpeg đã sẵn sàng:")
    print(result.stdout.split('\n')[0])  # Chỉ hiển thị dòng đầu tiên
except Exception as e:
    print("⚠️ Lỗi khi chạy ffmpeg:", e)
    print("📁 Đang tìm ffmpeg trong thư mục ffmpeg/")


class DownloadWorker(QThread):
    """Worker thread để xử lý download video"""
    message = Signal(str)
    progress_signal = Signal(int)
    finished = Signal(str)

    def __init__(self, urls, video_mode, audio_only, sub_mode, sub_lang, 
                 convert_srt, include_thumb, subtitle_only, custom_folder_name=""):
        super().__init__()
        self.urls = urls
        self.video_mode = video_mode
        self.audio_only = audio_only
        self.sub_mode = sub_mode
        self.sub_lang = sub_lang
        self.convert_srt = convert_srt
        self.include_thumb = include_thumb
        self.subtitle_only = subtitle_only
        self.custom_folder_name = custom_folder_name.strip()
        self.stop_flag = False
        self.process = None

    def stop(self):
        """Dừng quá trình download"""
        self.stop_flag = True
        if self.process:
            self.process.terminate()
            self.message.emit("⏹ Dừng tải...")

    def run(self):
        """Chạy quá trình download"""
        try:
            download_folder = self._create_download_folder()
            download_folder = download_folder.replace('\\', '/')
            for i, url in enumerate(self.urls, 1):
                if self.stop_flag:
                    self.message.emit("⏹ Đã dừng tải.")
                    break

                self.message.emit(f"🔗 [{i}] Đang tải: {url}")
                
                if self._download_single_url(url, download_folder, i):
                    self.message.emit(f"✅ Hoàn thành link URL: {url}")
                else:
                    self.message.emit(f"❌ Lỗi khi tải link: {url}")

                self.progress_signal.emit(int(i / len(self.urls) * 100))

            self.finished.emit(f"📂 Video được lưu tại: {download_folder}")

        except Exception as e:
            self.message.emit(f"❌ Lỗi: {e}")

    def _create_download_folder(self):
        """Tạo thư mục download"""
        if self.custom_folder_name:
            # Kiểm tra xem có phải là đường dẫn đầy đủ không
            if os.path.isabs(self.custom_folder_name):
                # Đường dẫn đầy đủ - sử dụng trực tiếp
                download_folder = self.custom_folder_name
                date_str = datetime.now().strftime("%Y-%m-%d")
                download_folder = os.path.join(download_folder, date_str)

            else:
                # Chỉ là tên thư mục - tạo trong thư mục Video
                base_folder = "Video"
                os.makedirs(base_folder, exist_ok=True)
                date_str = datetime.now().strftime("%Y-%m-%d")
                download_folder = os.path.join(base_folder, self.custom_folder_name)
        else:
            # Không có tên tùy chọn - tạo theo ngày
            base_folder = "Video"
            os.makedirs(base_folder, exist_ok=True)
            date_str = datetime.now().strftime("%Y-%m-%d")
            download_folder = os.path.join(base_folder, date_str)

        # Xử lý trường hợp thư mục đã tồn tại
        original_folder = download_folder
        count = 1
        while os.path.exists(download_folder):
            if os.path.isabs(self.custom_folder_name):
                # Với đường dẫn đầy đủ, thêm số vào cuối tên thư mục
                parent_dir = os.path.dirname(original_folder)
                folder_name = os.path.basename(original_folder)
                download_folder = os.path.join(parent_dir, f"{folder_name}-{count}")
            else:
                download_folder = f"{original_folder}-{count}"
            count += 1
        
        os.makedirs(download_folder, exist_ok=True)
        return download_folder

    def _download_single_url(self, url, download_folder, index):
        """Download một URL đơn"""
        cmd = self._build_command(url, download_folder, index)
        
        self.process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
            text=True, bufsize=1
        )

        for line in self.process.stdout:
            if self.stop_flag:
                self.process.terminate()
                self.message.emit("⏹ Đang dừng...")
                break

            line = line.strip()
            if line:
                self.message.emit(line)
                self._update_progress_from_line(line)
        
        self.process.wait()
        
        if self.process.returncode == 0:
            self._post_process_files(download_folder)
            return True
        return False

    def _build_command(self, url, download_folder, index):
        """Xây dựng lệnh yt-dlp"""
        # Tìm yt-dlp executable
        ytdlp_path = None
        possible_paths = [
            "yt-dlp.exe",  # Trong PATH
            "venv/Scripts/yt-dlp.exe",  # Trong venv
            os.path.join(sys.prefix, "Scripts", "yt-dlp.exe"),  # Trong Python Scripts
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                ytdlp_path = path
                break
        
        if not ytdlp_path:
            # Fallback to system yt-dlp
            ytdlp_path = "yt-dlp"
        
        cmd = [ytdlp_path, url, "--progress"]
        
        # Thêm đường dẫn ffmpeg nếu tồn tại
        if os.path.exists(ffmpeg_path):
            cmd += ["--ffmpeg-location", ffmpeg_path]
        
        if self.subtitle_only:
            cmd.append("--skip-download")
            self.message.emit("📝 Chế độ: Chỉ tải phụ đề")
        else:
            cmd += ["-f", "bv*+ba/b", "--merge-output-format", "mp4"]

        # Template output
        if self.video_mode:
            output_template = "%(title)s.%(ext)s"
        else:
            output_template = f"playlist_{index}_%(autonumber)03d_%(title)s.%(ext)s"
            cmd.append("--yes-playlist")
        
        cmd += ["-o", os.path.join(download_folder, output_template)]

        if self.audio_only and not self.subtitle_only:
            cmd += ["--extract-audio", "--audio-format", "mp3"]

        # Xử lý phụ đề
        if self.sub_mode != "❌ Không tải":
            self._add_subtitle_options(cmd)

        if self.convert_srt:
            cmd += ["--convert-subs", "srt"]
        if self.include_thumb:
            cmd.append("--write-thumbnail")

        return cmd

    def _add_subtitle_options(self, cmd):
        """Thêm tùy chọn phụ đề vào lệnh"""
        lang_string = ",".join(self.sub_lang) if isinstance(self.sub_lang, list) else self.sub_lang
        
        if self.sub_mode == "📄 Phụ đề chính thức":
            cmd += ["--write-subs", "--sub-langs", lang_string]
            self.message.emit(f"🔤 Tải phụ đề chính thức ngôn ngữ: {lang_string}")
        elif self.sub_mode == "🤖 Phụ đề tự động":
            cmd += ["--write-auto-subs", "--sub-langs", lang_string]
            self.message.emit(f"🤖 Tải phụ đề tự động ngôn ngữ: {lang_string}")
        
        cmd += ["--ignore-errors", "--no-warnings"]

    def _update_progress_from_line(self, line):
        """Cập nhật progress từ output line"""
        if "%" in line:
            try:
                percent_str = line.split("%", 1)[0].split()[-1].replace(".", "").strip()
                percent = int(percent_str)
                if 0 <= percent <= 100:
                    self.progress_signal.emit(percent)
            except:
                pass

    def _post_process_files(self, download_folder):
        """Xử lý files sau khi download"""
        if self.sub_mode != "❌ Không tải":
            lang_list = self.sub_lang if isinstance(self.sub_lang, list) else [self.sub_lang]
            for lang in lang_list:
                self._rename_subtitle_files(download_folder, lang)
        
        self._rename_video_files(download_folder)

    def _rename_subtitle_files(self, folder_path, sub_lang):
        """Đổi tên file phụ đề theo định dạng mong muốn"""
        try:
            if sub_lang == "en":
                # Xử lý tiếng Anh
                for subtitle_file in glob.glob(os.path.join(folder_path, "*.en.srt")):
                    new_name = subtitle_file.replace(".en.srt", ".srt")
                    if not os.path.exists(new_name):
                        os.rename(subtitle_file, new_name)
                        self.message.emit(f"📝 Đổi tên: {os.path.basename(subtitle_file)} → {os.path.basename(new_name)}")
                
                # Sửa lỗi ..srt
                for subtitle_file in glob.glob(os.path.join(folder_path, "*.srt")):
                    if "..srt" in subtitle_file:
                        new_name = subtitle_file.replace("..srt", ".srt")
                        if not os.path.exists(new_name) and new_name != subtitle_file:
                            os.rename(subtitle_file, new_name)
                            self.message.emit(f"📝 Sửa tên: {os.path.basename(subtitle_file)} → {os.path.basename(new_name)}")
            else:
                # Các ngôn ngữ khác
                for subtitle_file in glob.glob(os.path.join(folder_path, f"*.{sub_lang}.srt")):
                    if f"..{sub_lang}.srt" in subtitle_file:
                        new_name = subtitle_file.replace(f"..{sub_lang}.srt", f".{sub_lang}.srt")
                        if not os.path.exists(new_name):
                            os.rename(subtitle_file, new_name)
                            self.message.emit(f"📝 Sửa tên: {os.path.basename(subtitle_file)} → {os.path.basename(new_name)}")
                            
        except Exception as e:
            self.message.emit(f"⚠️ Lỗi đổi tên phụ đề: {e}")

    def _rename_video_files(self, folder_path):
        """Đổi tên file video (sửa ..mp4, ..mp3, etc. thành .mp4, .mp3)"""
        try:
            video_formats = ["*.mp4", "*.mp3", "*.mkv", "*.avi", "*.mov", "*.webm"]
            
            for format_pattern in video_formats:
                for media_file in glob.glob(os.path.join(folder_path, format_pattern)):
                    filename = os.path.basename(media_file)
                    
                    if ".." in filename:
                        file_ext = os.path.splitext(filename)[1]
                        new_filename = filename.replace(f"..{file_ext[1:]}", file_ext)
                        new_path = os.path.join(folder_path, new_filename)
                        
                        if not os.path.exists(new_path):
                            os.rename(media_file, new_path)
                            self.message.emit(f"📝 Sửa tên: {filename} → {new_filename}")
                            
        except Exception as e:
            self.message.emit(f"⚠️ Lỗi đổi tên file media: {e}")


class DownloaderApp(QWidget):
    """Ứng dụng chính để download video"""
    
    def __init__(self):
        super().__init__()
        self.worker = None
        self.init_ui()
        self.apply_styles()

    def init_ui(self):
        """Khởi tạo giao diện người dùng"""
        self.setWindowTitle("HT DownloadVID v1.0")
        self.setMinimumWidth(520)
        self.center_window()

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self._create_url_section()
        self._create_mode_section()
        self._create_subtitle_section()
        self._create_options_section()
        self._create_control_buttons()
        self._create_progress_section()
        self._create_log_section()

    def _create_url_section(self):
        """Tạo phần nhập URL"""
        self.layout.addWidget(QLabel("📋 Nhập URL video:"))
        
        self.url_input = QTextEdit()
        self.url_input.setPlaceholderText("Mỗi dòng 1 link video hoặc playlist...")
        self.url_input.setFixedHeight(75)
        self.layout.addWidget(self.url_input)

        self.layout.addWidget(QLabel("📁 Tên thư mục tải (tuỳ chọn):"))
        
        # Tạo layout ngang cho ô nhập tên thư mục và nút chọn thư mục
        folder_layout = QHBoxLayout()
        
        self.folder_name_input = QTextEdit()
        self.folder_name_input.setPlaceholderText("Nhập tên thư mục hoặc chọn thư mục...")
        self.folder_name_input.setFixedHeight(45)
        folder_layout.addWidget(self.folder_name_input)
        
        # Nút chọn thư mục
        self.browse_folder_button = QPushButton("📂 Open")
        self.browse_folder_button.clicked.connect(self.browse_folder)
        self.browse_folder_button.setFixedWidth(130)
        folder_layout.addWidget(self.browse_folder_button)
        
        self.layout.addLayout(folder_layout)

    def _create_mode_section(self):
        """Tạo phần chọn chế độ tải"""
        self.mode_group = QButtonGroup(self)
        self.video_radio = QRadioButton("🎬 Video đơn")
        self.playlist_radio = QRadioButton("📃 Playlist")
        self.video_radio.setChecked(True)
        
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(self.video_radio)
        mode_layout.addWidget(self.playlist_radio)
        
        self.mode_group.addButton(self.video_radio)
        self.mode_group.addButton(self.playlist_radio)
        self.layout.addLayout(mode_layout)

    def _create_subtitle_section(self):
        """Tạo phần tùy chọn phụ đề"""
        self.layout.addWidget(QLabel("📝 Chế độ phụ đề:"))
        
        self.sub_mode = QComboBox()
        self.sub_mode.addItems([
            "❌ Không tải",
            "📄 Phụ đề chính thức",
            "🤖 Phụ đề tự động"
        ])
        self.sub_mode.setCurrentText("🤖 Phụ đề tự động")
        self.layout.addWidget(self.sub_mode)

        self.layout.addWidget(QLabel("🌍 Ngôn ngữ phụ đề:"))
        self._create_language_checkboxes()

    def _create_language_checkboxes(self):
        """Tạo các checkbox chọn ngôn ngữ"""
        lang_widget = QWidget()
        lang_layout = QVBoxLayout(lang_widget)
        lang_layout.setContentsMargins(0, 0, 0, 0)
        lang_layout.setSpacing(3)

        self.lang_checkboxes = {}
        languages = [
            ("vi", "🇻🇳 Tiếng Việt"),
            ("en", "🇺🇸 Tiếng Anh"), 
            ("zh-Hans", "🇨🇳 Tiếng Trung (Giản thể)"),
            ("zh-Hant", "🇹🇼 Tiếng Trung (Phồn thể)"),
            ("ko", "🇰🇷 Tiếng Hàn"),
            ("ja", "🇯🇵 Tiếng Nhật"),
            ("fr", "🇫🇷 Tiếng Pháp"),
            ("es", "🇪🇸 Tiếng Tây Ban Nha")
        ]

        # Tạo layout dạng lưới 2 cột
        for i in range(0, len(languages), 4):
            row_layout = QHBoxLayout()
            row_layout.setSpacing(5)
            
            for j in range(4):
                if i + j < len(languages):
                    code, name = languages[i + j]
                    checkbox = QCheckBox(name)
                    checkbox.setObjectName("lang-checkbox")
                    if code in ["vi", "en"]:
                        checkbox.setChecked(True)
                    self.lang_checkboxes[code] = checkbox
                    row_layout.addWidget(checkbox)
            
            row_layout.addStretch()
            lang_layout.addLayout(row_layout)

        self.layout.addWidget(lang_widget)

    def _create_options_section(self):
        """Tạo phần tùy chọn bổ sung"""
        # Dòng 1: Chuyển phụ đề sang .srt và Tải âm thanh MP3
        row1_layout = QHBoxLayout()
        
        self.convert_srt = QCheckBox("🔁 Chuyển phụ đề sang .srt")
        self.convert_srt.setChecked(True)
        row1_layout.addWidget(self.convert_srt)
        
        self.audio_only = QCheckBox("🎵 Tải âm thanh MP3")
        row1_layout.addWidget(self.audio_only)
        
        row1_layout.addStretch()  # Thêm khoảng trống để căn trái
        self.layout.addLayout(row1_layout)
        
        # Dòng 2: Tải ảnh thumbnail và Chỉ tải phụ đề
        row2_layout = QHBoxLayout()
        
        self.include_thumb = QCheckBox("🖼️ Tải ảnh thumbnail")
        row2_layout.addWidget(self.include_thumb)
        
        self.subtitle_only = QCheckBox("📝 Chỉ tải phụ đề")
        row2_layout.addWidget(self.subtitle_only)
        
        row2_layout.addStretch()  # Thêm khoảng trống để căn trái
        self.layout.addLayout(row2_layout)

    def _create_control_buttons(self):
        """Tạo các nút điều khiển"""
        self.download_button = QPushButton("🚀 Bắt đầu tải")
        self.download_button.clicked.connect(self.start_download)
        
        self.stop_button = QPushButton("⏹ Dừng tải")
        self.stop_button.clicked.connect(self.stop_download)
        self.stop_button.setVisible(False)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.download_button)
        button_layout.addWidget(self.stop_button)
        self.layout.addLayout(button_layout)

    def _create_progress_section(self):
        """Tạo thanh tiến trình"""
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.layout.addWidget(self.progress)

    def _create_log_section(self):
        """Tạo phần log"""
        self.output_list = QListWidget()
        self.output_list.setWordWrap(True)
        self.output_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.output_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.output_list.setMinimumHeight(120)
        self.layout.addWidget(self.output_list)

    def center_window(self):
        """Căn giữa cửa sổ trên màn hình"""
        self.resize(520, 700)
        
        screen = QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            window_geometry = self.frameGeometry()
            center_point = screen_geometry.center()
            window_geometry.moveCenter(center_point)
            self.move(window_geometry.topLeft())

    def start_download(self):
        """Bắt đầu quá trình download"""
        urls = [u.strip() for u in self.url_input.toPlainText().splitlines() if u.strip()]
        if not urls:
            QMessageBox.warning(self, "Cảnh báo", "Bạn chưa nhập URL nào.")
            return

        self._prepare_ui_for_download()
        
        # Lấy danh sách ngôn ngữ đã chọn
        selected_lang_codes = [
            code for code, checkbox in self.lang_checkboxes.items() 
            if checkbox.isChecked()
        ]
        
        if not selected_lang_codes:
            selected_lang_codes = ["vi", "en"]

        self.worker = DownloadWorker(
            urls=urls,
            video_mode=self.video_radio.isChecked(),
            audio_only=self.audio_only.isChecked(),
            sub_mode=self.sub_mode.currentText(),
            sub_lang=selected_lang_codes,
            convert_srt=self.convert_srt.isChecked(),
            include_thumb=self.include_thumb.isChecked(),
            subtitle_only=self.subtitle_only.isChecked(),
            custom_folder_name=self.folder_name_input.toPlainText()
        )

        self._connect_worker_signals()
        self.worker.start()

    def _prepare_ui_for_download(self):
        """Chuẩn bị UI cho quá trình download"""
        self.output_list.clear()
        self.progress.setValue(0)
        self.stop_button.setVisible(True)
        self.progress.setVisible(True)
        self.download_button.setEnabled(False)
        # self.output_list.setMinimumHeight(120)

    def _connect_worker_signals(self):
        """Kết nối các signal của worker"""
        self.worker.message.connect(self.output_list.addItem)
        self.worker.message.connect(self.scroll_to_bottom)
        self.worker.progress_signal.connect(self.progress.setValue)
        self.worker.finished.connect(self.output_list.addItem)
        self.worker.finished.connect(self.scroll_to_bottom)
        self.worker.finished.connect(self.on_download_finished)

    def stop_download(self):
        """Dừng quá trình download"""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.output_list.addItem("⏹ Đang dừng tiến trình...")
            self.scroll_to_bottom()
            self._reset_ui_after_download()
        else:
            QMessageBox.information(self, "Thông báo", "Hiện không có tác vụ nào đang chạy.")

    def on_download_finished(self):
        """Xử lý khi download hoàn thành"""
        self._reset_ui_after_download()

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
                word-wrap: break-word;
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

    def browse_folder(self):
        """Mở hộp thoại để chọn thư mục download"""
        current_text = self.folder_name_input.toPlainText().strip()
        start_dir = current_text if os.path.isdir(current_text) else os.getcwd()
        
        folder_path = QFileDialog.getExistingDirectory(
            self, 
            "Chọn thư mục download", 
            start_dir
        )
        
        if folder_path:
            # Lưu đường dẫn đầy đủ vào input field
            self.folder_name_input.setText(folder_path)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = DownloaderApp()
    win.show()
    sys.exit(app.exec())
