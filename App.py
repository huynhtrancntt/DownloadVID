import sys
import os
import subprocess
import glob
import logging
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QPushButton,
    QTextEdit, QCheckBox, QComboBox, QRadioButton,
    QHBoxLayout, QButtonGroup, QMessageBox, QProgressBar, QListWidget, QListWidgetItem,
    QFileDialog, QMenuBar, QMenu
)
from PySide6.QtCore import Qt, QThread, Signal, QSettings
from PySide6.QtGui import QScreen, QAction, QIcon

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


# Thiết lập đường dẫn ffmpeg và kiểm tra
ffmpeg_path = resource_path(os.path.join("ffmpeg", "ffmpeg.exe"))

# Gọi thử ffmpeg
try:
    result = subprocess.run([ffmpeg_path, "-version"], capture_output=True, text=True)
    debug_print("✅ FFmpeg đã sẵn sàng:")
    debug_print(result.stdout.split('\n')[0])  # Chỉ hiển thị dòng đầu tiên
except Exception as e:
    debug_print("⚠️ Lỗi khi chạy ffmpeg:", e)
    debug_print("📁 Đang tìm ffmpeg trong thư mục ffmpeg/")


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
        # Xử lý danh sách ngôn ngữ
        if isinstance(self.sub_lang, list):
            lang_string = ",".join(self.sub_lang)
            lang_display = ", ".join(self.sub_lang)
        else:
            lang_string = self.sub_lang
            lang_display = self.sub_lang
        
        if self.sub_mode == "📄 Phụ đề chính thức":
            cmd += ["--write-subs", "--sub-langs", lang_string]
            self.message.emit(f"🔤 Tải phụ đề chính thức cho {len(self.sub_lang) if isinstance(self.sub_lang, list) else 1} ngôn ngữ: {lang_display}")
        elif self.sub_mode == "🤖 Phụ đề tự động":
            cmd += ["--write-auto-subs", "--sub-langs", lang_string]
            self.message.emit(f"🤖 Tải phụ đề tự động cho {len(self.sub_lang) if isinstance(self.sub_lang, list) else 1} ngôn ngữ: {lang_display}")
        
        # Thêm các tùy chọn để đảm bảo tải được phụ đề
        cmd += [
            "--ignore-errors",           # Bỏ qua lỗi nếu một ngôn ngữ không có
            "--no-warnings",            # Không hiển thị cảnh báo
            "--sub-format", "srt/best" # Ưu tiên định dạng SRT
            # "--write-info-json"         # Ghi thông tin để debug
        ]
        
        # KHÔNG dùng --all-subs nữa, chỉ tải chính xác ngôn ngữ đã chọn
        self.message.emit(f"🎯 Chỉ tải chính xác {len(self.sub_lang) if isinstance(self.sub_lang, list) else 1} ngôn ngữ đã chọn")
        
        # Debug: In ra lệnh phụ đề
        self.message.emit(f"🔧 Debug: Lệnh phụ đề = --sub-langs {lang_string}")

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
            # Đảm bảo sub_lang luôn là list
            lang_list = self.sub_lang if isinstance(self.sub_lang, list) else [self.sub_lang]
            
            self.message.emit(f"🔄 Xử lý phụ đề cho {len(lang_list)} ngôn ngữ: {', '.join(lang_list)}")
            
            # Sau đó xử lý từng ngôn ngữ
            for i, lang in enumerate(lang_list, 1):
                self.message.emit(f"📝 [{i}/{len(lang_list)}] Xử lý phụ đề ngôn ngữ: {lang}")
                self._rename_subtitle_files(download_folder, lang)
        
        self._rename_video_files(download_folder)
        


    def _rename_subtitle_files(self, folder_path, sub_lang):
        """Đổi tên file phụ đề theo định dạng mong muốn"""
        try:
            self.message.emit(f"🔧 Đang xử lý phụ đề ngôn ngữ: {sub_lang}")
            
            # Tìm tất cả file phụ đề cho ngôn ngữ này
            patterns = [
                f"*.{sub_lang}.srt",
                f"*.{sub_lang}.vtt", 
                f"*.{sub_lang}.ass"
            ]
            
            found_files = []
            for pattern in patterns:
                found_files.extend(glob.glob(os.path.join(folder_path, pattern)))
            
            if not found_files:
                self.message.emit(f"⚠️ Không tìm thấy file phụ đề cho ngôn ngữ: {sub_lang}")
                return
                
            self.message.emit(f"📁 Tìm thấy {len(found_files)} file phụ đề cho {sub_lang}")
            
            for subtitle_file in found_files:
                filename = os.path.basename(subtitle_file)
                
                if sub_lang == "en":
                    # Xử lý đặc biệt cho tiếng Anh - đổi thành .srt chính
                    if subtitle_file.endswith(".en.srt"):
                        # print(f"🔍 Đang xử lý1 : {subtitle_file}")
                        new_name = subtitle_file.replace("..en.srt", ".srt").replace(".en.srt", ".srt")
                        # print(f"🔍 Đang xử lý: {new_name}")
                        if not os.path.exists(new_name):
                            os.rename(subtitle_file, new_name)
                            self.message.emit(f"📝 Đổi tên: {filename} → {os.path.basename(new_name)}")
                        else:
                            self.message.emit(f"⚠️ File đã tồn tại: {os.path.basename(new_name)}")
                
                # Sửa lỗi tên file có .. (double dots)
                if f"..{sub_lang}." in subtitle_file:
                    ext = os.path.splitext(subtitle_file)[1]
                    new_name = subtitle_file.replace(f"..{sub_lang}.", f".{sub_lang}.")
                    if not os.path.exists(new_name) and new_name != subtitle_file:
                        os.rename(subtitle_file, new_name)
                        self.message.emit(f"📝 Sửa tên: {filename} → {os.path.basename(new_name)}")
                        
        except Exception as e:
            self.message.emit(f"⚠️ Lỗi đổi tên phụ đề {sub_lang}: {e}")

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
        self.settings = QSettings("HT Software", "DownloadVID")
        self.loading_settings = False  # Flag để tránh auto-save khi đang load
        self.init_ui()
        self.apply_styles()
        self.load_settings()

    def init_ui(self):
        """Khởi tạo giao diện người dùng"""
        self.setWindowTitle("HT DownloadVID v1.0")
        
        # Thiết lập icon cho cửa sổ
        icon_path = resource_path("ico.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        self.setMinimumWidth(520)
        self.center_window()

        # Tạo layout chính
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # Thêm menubar
        self._create_menubar()
        main_layout.addWidget(self.menubar)
        
        # Tạo layout cho nội dung chính
        self.layout = QVBoxLayout()
        main_layout.addLayout(self.layout)

        self._create_url_section()
        self._create_mode_section()
        self._create_subtitle_section()
        self._create_options_section()
        self._create_control_buttons()
        self._create_progress_section()
        self._create_log_section()
        
        # Auto-save sẽ được kết nối sau khi load_settings() hoàn thành

    def _create_menubar(self):
        """Tạo menubar"""
        self.menubar = QMenuBar(self)
        
        # Menu File
        file_menu = self.menubar.addMenu("📁 File")
        
        # Action Reset Settings
        reset_action = QAction("🔄 Reset Settings", self)
        reset_action.triggered.connect(self.reset_settings)
        file_menu.addAction(reset_action)
        
        file_menu.addSeparator()
        
        # Action Exit
        exit_action = QAction("❌ Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Menu Settings
        settings_menu = self.menubar.addMenu("⚙️ Settings")
        
        # Action Save Current Settings
        save_settings_action = QAction("💾 Save Current Settings", self)
        save_settings_action.triggered.connect(self.save_settings)
        settings_menu.addAction(save_settings_action)
        
        # Action Load Default Settings
        load_default_action = QAction("📋 Load Default Settings", self)
        load_default_action.triggered.connect(self.load_default_settings)
        settings_menu.addAction(load_default_action)
        
        settings_menu.addSeparator()
        
        # Action View Settings Info
        info_action = QAction("📊 View Settings Info", self)
        info_action.triggered.connect(self.show_settings_info)
        settings_menu.addAction(info_action)
        
        # Menu Help
        help_menu = self.menubar.addMenu("❓ Help")
        
        # Action View Log File
        log_action = QAction("📝 View Log File", self)
        log_action.triggered.connect(self.show_log_file)
        help_menu.addAction(log_action)
        
        help_menu.addSeparator()
        
        # Action About
        about_action = QAction("ℹ️ About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

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

        # Tạo layout dạng lưới 4 cột
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
                    # Kết nối signal để hiển thị trạng thái khi thay đổi
                    checkbox.toggled.connect(lambda checked, lang_code=code: self.on_language_toggled(lang_code, checked))
                    self.lang_checkboxes[code] = checkbox
                    row_layout.addWidget(checkbox)
            
            row_layout.addStretch()
            lang_layout.addLayout(row_layout)

        # Thêm label hiển thị số ngôn ngữ đã chọn
        self.selected_lang_label = QLabel("✅ Đã chọn: 2 ngôn ngữ (Tiếng Việt, Tiếng Anh)")
        self.selected_lang_label.setStyleSheet("color: #28a745; font-weight: bold; margin: 5px 0px;")
        lang_layout.addWidget(self.selected_lang_label)

        self.layout.addWidget(lang_widget)

    def on_language_toggled(self, lang_code, checked):
        """Xử lý khi checkbox ngôn ngữ được thay đổi"""
        self.update_selected_languages_display()
        # Gọi auto-save nếu không đang load settings
        if not (hasattr(self, 'loading_settings') and self.loading_settings):
            self.auto_save_on_change()

    def update_selected_languages_display(self):
        """Cập nhật hiển thị ngôn ngữ đã chọn"""
        selected_langs = []
        lang_map = {
            "vi": "🇻🇳 Tiếng Việt",
            "en": "🇺🇸 Tiếng Anh", 
            "zh-Hans": "🇨🇳 Tiếng Trung (Giản thể)",
            "zh-Hant": "🇹🇼 Tiếng Trung (Phồn thể)",
            "ko": "🇰🇷 Tiếng Hàn",
            "ja": "🇯🇵 Tiếng Nhật",
            "fr": "🇫🇷 Tiếng Pháp",
            "es": "🇪🇸 Tiếng Tây Ban Nha"
        }
        
        for code, checkbox in self.lang_checkboxes.items():
            if checkbox.isChecked():
                selected_langs.append(lang_map.get(code, code))
        
        if selected_langs:
            if len(selected_langs) <= 3:
                lang_text = ", ".join(selected_langs)
            else:
                lang_text = f"{', '.join(selected_langs[:2])} và {len(selected_langs)-2} ngôn ngữ khác"
            
            self.selected_lang_label.setText(f"✅ Đã chọn: {len(selected_langs)} ngôn ngữ ({lang_text})")
            self.selected_lang_label.setStyleSheet("color: #28a745; font-weight: bold; margin: 5px 0px;")
        else:
            self.selected_lang_label.setText("⚠️ Chưa chọn ngôn ngữ nào - sẽ dùng mặc định")
            self.selected_lang_label.setStyleSheet("color: #dc3545; font-weight: bold; margin: 5px 0px;")

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

    def _connect_auto_save(self):
        """Kết nối auto-save với các control"""
        # Chỉ kết nối sau khi đã load settings xong
        if not hasattr(self, 'loading_settings') or self.loading_settings:
            return
            
        # URL input
        self.url_input.textChanged.connect(self.auto_save_on_change)
        
        # Folder input
        self.folder_name_input.textChanged.connect(self.auto_save_on_change)
        
        # Radio buttons
        self.video_radio.toggled.connect(self.auto_save_on_change)
        self.playlist_radio.toggled.connect(self.auto_save_on_change)
        
        # Combobox
        self.sub_mode.currentTextChanged.connect(self.auto_save_on_change)
        
        # Checkboxes
        self.convert_srt.toggled.connect(self.auto_save_on_change)
        self.audio_only.toggled.connect(self.auto_save_on_change)
        self.include_thumb.toggled.connect(self.auto_save_on_change)
        self.subtitle_only.toggled.connect(self.auto_save_on_change)
        
        # Language checkboxes đã được kết nối trong _create_language_checkboxes()
        # Không cần kết nối lại ở đây

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
            self.output_list.addItem("⚠️ Không có ngôn ngữ nào được chọn, sử dụng mặc định: vi, en")

        # Debug: Hiển thị thông tin cấu hình chi tiết
        self.output_list.addItem("🔧 === THÔNG TIN CẤU HÌNH ===")
        self.output_list.addItem(f"🔗 Số URL: {len(urls)}")
        self.output_list.addItem(f"🎬 Chế độ: {'Video đơn' if self.video_radio.isChecked() else 'Playlist'}")
        self.output_list.addItem(f"📝 Phụ đề: {self.sub_mode.currentText()}")
        self.output_list.addItem(f"🌍 Ngôn ngữ phụ đề ({len(selected_lang_codes)}): {', '.join(selected_lang_codes)}")
        
        # Hiển thị tên ngôn ngữ đầy đủ với trạng thái
        lang_names = []
        lang_map = {
            "vi": "🇻🇳 Tiếng Việt",
            "en": "🇺🇸 Tiếng Anh", 
            "zh-Hans": "🇨🇳 Tiếng Trung (Giản thể)",
            "zh-Hant": "🇹🇼 Tiếng Trung (Phồn thể)",
            "ko": "🇰🇷 Tiếng Hàn",
            "ja": "🇯🇵 Tiếng Nhật",
            "fr": "🇫🇷 Tiếng Pháp",
            "es": "🇪🇸 Tiếng Tây Ban Nha"
        }
        
        for code in selected_lang_codes:
            lang_names.append(lang_map.get(code, f"❓ {code}"))
        
        self.output_list.addItem(f"📋 Sẽ tải phụ đề: {', '.join(lang_names)}")
        
        # Hiển thị trạng thái tất cả ngôn ngữ trong UI
        self.output_list.addItem("🔍 Trạng thái chọn ngôn ngữ trong UI:")
        for code, checkbox in self.lang_checkboxes.items():
            status = "✅ ĐÃ CHỌN" if checkbox.isChecked() else "❌ Không chọn"
            lang_name = lang_map.get(code, f"❓ {code}")
            self.output_list.addItem(f"   {lang_name}: {status}")
        
        # Hiển thị các tùy chọn khác
        options = []
        if self.audio_only.isChecked():
            options.append("🎵 Audio MP3")
        if self.convert_srt.isChecked():
            options.append("🔁 Convert SRT")
        if self.include_thumb.isChecked():
            options.append("🖼️ Thumbnail")
        if self.subtitle_only.isChecked():
            options.append("📝 Chỉ phụ đề")
            
        if options:
            self.output_list.addItem(f"⚙️ Tùy chọn: {', '.join(options)}")
        
        custom_folder = self.folder_name_input.toPlainText().strip()
        if custom_folder:
            self.output_list.addItem(f"📁 Thư mục: {custom_folder}")
            
        self.output_list.addItem("🔧 ========================")
        self.scroll_to_bottom()

        self.worker = DownloadWorker(
            urls=urls,
            video_mode=self.video_radio.isChecked(),
            audio_only=self.audio_only.isChecked(),
            sub_mode=self.sub_mode.currentText(),
            sub_lang=selected_lang_codes,
            convert_srt=self.convert_srt.isChecked(),
            include_thumb=self.include_thumb.isChecked(),
            subtitle_only=self.subtitle_only.isChecked(),
            custom_folder_name=custom_folder
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
            # Tự động lưu ngay khi chọn thư mục
            self.auto_save_on_change()

    def save_settings(self):
        """Lưu settings vào registry (với thông báo)"""
        try:
            # Gọi auto_save_on_change để lưu tất cả
            self.auto_save_on_change()
            
            # Lưu thêm thông tin thống kê
            self.settings.setValue("last_saved", datetime.now().isoformat())
            
            usage_count = self.settings.value("usage_count", 0, int)
            self.settings.setValue("usage_count", usage_count + 1)
            
            # Lưu vị trí cửa sổ
            self.settings.setValue("geometry", self.saveGeometry())
            
            # Đồng bộ
            self.settings.sync()
            
            QMessageBox.information(self, "Thành công", "✅ Đã lưu settings thành công!")
            
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"❌ Không thể lưu settings: {e}")

    def load_settings(self):
        """Tải settings từ registry"""
        self.loading_settings = True  # Tắt auto-save trong khi load
        
        try:
            debug_print("🔄 Đang tải settings...")
            
            # Tải URL đã lưu
            saved_urls = self.settings.value("urls", "")
            if saved_urls:
                self.url_input.setText(saved_urls)
                debug_print(f"📋 Đã tải {len(saved_urls.splitlines())} ")
            
            # Tải tên thư mục tùy chọn
            custom_folder = self.settings.value("custom_folder", "")
            if custom_folder:
                self.folder_name_input.setText(custom_folder)
                debug_print(f"📁 Đã tải thư mục: {custom_folder}")
            
            # Tải chế độ video
            video_mode = self.settings.value("video_mode", True, bool)
            if video_mode:
                self.video_radio.setChecked(True)
            else:
                self.playlist_radio.setChecked(True)
            debug_print(f"🎬 Chế độ video: {'Video đơn' if video_mode else 'Playlist'}")
            
            # Tải chế độ phụ đề
            subtitle_mode = self.settings.value("subtitle_mode", "🤖 Phụ đề tự động")
            index = self.sub_mode.findText(subtitle_mode)
            if index >= 0:
                self.sub_mode.setCurrentIndex(index)
            debug_print(f"📝 Chế độ phụ đề: {subtitle_mode}")
            
            # Tải ngôn ngữ phụ đề
            selected_langs = self.settings.value("selected_languages", ["vi", "en"])
            if isinstance(selected_langs, str):
                selected_langs = [selected_langs]
            
            # Reset tất cả checkbox về False trước
            for checkbox in self.lang_checkboxes.values():
                checkbox.setChecked(False)
            
            # Chọn các ngôn ngữ đã lưu
            for lang in selected_langs:
                if lang in self.lang_checkboxes:
                    self.lang_checkboxes[lang].setChecked(True)
            debug_print(f"🌍 Đã tải {len(selected_langs)} ngôn ngữ: {selected_langs}")
            
            # Cập nhật hiển thị ngôn ngữ đã chọn
            self.update_selected_languages_display()
            
            # Tải các tùy chọn
            self.convert_srt.setChecked(self.settings.value("convert_srt", True, bool))
            self.audio_only.setChecked(self.settings.value("audio_only", False, bool))
            self.include_thumb.setChecked(self.settings.value("include_thumb", False, bool))
            self.subtitle_only.setChecked(self.settings.value("subtitle_only", False, bool))
            
            # Tải vị trí và kích thước cửa sổ
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
                debug_print("🪟 Đã khôi phục vị trí cửa sổ")
                
            # Hiển thị thông tin thống kê
            usage_count = self.settings.value("usage_count", 0, int)
            last_saved = self.settings.value("last_saved", "")
            
            if usage_count > 0:
                debug_print(f"📊 Lần sử dụng thứ: {usage_count}")
                if last_saved:
                    debug_print(f"🕒 Lần lưu cuối: {last_saved}")
                    
            debug_print("✅ Đã tải settings thành công!")
                
        except Exception as e:
            debug_print(f"⚠️ Không thể tải settings: {e}")
        finally:
            self.loading_settings = False  # Bật lại auto-save
            # Kết nối auto-save sau khi load xong
            self._connect_auto_save()

    def reset_settings(self):
        """Reset tất cả settings về mặc định"""
        reply = QMessageBox.question(
            self, "Xác nhận", 
            "🔄 Bạn có chắc muốn reset tất cả settings về mặc định?\n\n⚠️ Điều này sẽ xóa:\n• URL đã lưu\n• Tất cả tùy chọn\n• Thư mục tùy chọn\n• Vị trí cửa sổ",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.settings.clear()
            self.load_default_settings()
            QMessageBox.information(self, "Thành công", "✅ Đã reset settings về mặc định!")

    def load_default_settings(self):
        """Tải settings mặc định"""
        # Xóa URL
        self.url_input.clear()
        
        # Chế độ video mặc định
        self.video_radio.setChecked(True)
        
        # Chế độ phụ đề mặc định
        self.sub_mode.setCurrentText("🤖 Phụ đề tự động")
        
        # Ngôn ngữ mặc định
        for code, checkbox in self.lang_checkboxes.items():
            checkbox.setChecked(code in ["vi", "en"])
        
        # Tùy chọn mặc định
        self.convert_srt.setChecked(True)
        self.audio_only.setChecked(False)
        self.include_thumb.setChecked(False)
        self.subtitle_only.setChecked(False)
        
        # Xóa tên thư mục tùy chọn
        self.folder_name_input.clear()

    def auto_save_on_change(self):
        """Tự động lưu khi có thay đổi (không hiển thị thông báo)"""
        # Không lưu nếu đang trong quá trình load settings
        if hasattr(self, 'loading_settings') and self.loading_settings:
            return
            
        try:
            # Lưu URL đã nhập
            urls_text = self.url_input.toPlainText().strip()
            self.settings.setValue("urls", urls_text)
            
            # Lưu chế độ video
            self.settings.setValue("video_mode", self.video_radio.isChecked())
            
            # Lưu chế độ phụ đề
            self.settings.setValue("subtitle_mode", self.sub_mode.currentText())
            
            # Lưu ngôn ngữ phụ đề đã chọn
            selected_langs = []
            for code, checkbox in self.lang_checkboxes.items():
                if checkbox.isChecked():
                    selected_langs.append(code)
            self.settings.setValue("selected_languages", selected_langs)
            
            # Lưu các tùy chọn
            self.settings.setValue("convert_srt", self.convert_srt.isChecked())
            self.settings.setValue("audio_only", self.audio_only.isChecked())
            self.settings.setValue("include_thumb", self.include_thumb.isChecked())
            self.settings.setValue("subtitle_only", self.subtitle_only.isChecked())
            
            # Lưu tên thư mục tùy chọn
            custom_folder = self.folder_name_input.toPlainText().strip()
            self.settings.setValue("custom_folder", custom_folder)
            
            # Đồng bộ settings ngay lập tức
            self.settings.sync()
            
            # Debug log (chỉ khi có thay đổi quan trọng)
            if custom_folder:
                debug_print(f"💾 Auto-save: Thư mục = {custom_folder}")
            
        except Exception as e:
            debug_print(f"⚠️ Lỗi auto-save: {e}")

    def debug_settings(self):
        """Debug method để kiểm tra settings đã lưu"""
        debug_print("\n🔍 DEBUG SETTINGS:")
        debug_print(f"📁 Custom folder trong registry: '{self.settings.value('custom_folder', 'EMPTY')}'")
        debug_print(f"📁 Custom folder trong UI: '{self.folder_name_input.toPlainText()}'")
        debug_print(f"🔗 URLs trong registry: {len(self.settings.value('urls', '').splitlines())} dòng")
        debug_print(f"🔗 URLs trong UI: {len(self.url_input.toPlainText().splitlines())} dòng")
        debug_print(f"🎬 Video mode: {self.settings.value('video_mode', 'NONE')}")
        debug_print(f"📝 Subtitle mode: {self.settings.value('subtitle_mode', 'NONE')}")
        debug_print(f"🌍 Languages: {self.settings.value('selected_languages', 'NONE')}")
        debug_print("=" * 60)

    def show_about(self):
        """Hiển thị thông tin về ứng dụng"""
        about_text = """
        <h3>🎬 HT DownloadVID v1.0</h3>
        <p><b>Ứng dụng download video và phụ đề</b></p>
        <p>📅 Phiên bản: 1.0</p>
        <p>👨‍💻 Phát triển bởi: HT Software</p>
        <p>🔧 Sử dụng: yt-dlp + ffmpeg</p>
        <br>
        <p><b>Tính năng:</b></p>
        <ul>
        <li>✅ Download video từ nhiều nền tảng</li>
        <li>✅ Hỗ trợ playlist</li>
        <li>✅ Download phụ đề đa ngôn ngữ</li>
        <li>✅ Chuyển đổi audio sang MP3</li>
        <li>✅ Lưu settings tự động</li>
        </ul>
        """
        
        QMessageBox.about(self, "Về ứng dụng", about_text)

    def show_settings_info(self):
        """Hiển thị thông tin về settings đã lưu"""
        try:
            usage_count = self.settings.value("usage_count", 0, int)
            last_saved = self.settings.value("last_saved", "Chưa lưu")
            
            # Đếm số URL đã lưu
            saved_urls = self.settings.value("urls", "")
            url_count = len([url for url in saved_urls.splitlines() if url.strip()]) if saved_urls else 0
            
            # Đếm ngôn ngữ đã chọn
            selected_langs = self.settings.value("selected_languages", [])
            if isinstance(selected_langs, str):
                selected_langs = [selected_langs]
            lang_count = len(selected_langs) if selected_langs else 0
            
            # Kiểm tra thư mục tùy chọn - Hiển thị chi tiết hơn
            custom_folder = self.settings.value("custom_folder", "")
            folder_display = custom_folder if custom_folder else "Không có"
            
            info_text = f"""
            <h3>📊 Thông tin Settings</h3>
            <table border="1" cellpadding="5" cellspacing="0">
            <tr><td><b>🔢 Số lần sử dụng:</b></td><td>{usage_count}</td></tr>
            <tr><td><b>🕒 Lần lưu cuối:</b></td><td>{last_saved}</td></tr>
            <tr><td><b>🔗 Số URL đã lưu:</b></td><td>{url_count}</td></tr>
            <tr><td><b>🌍 Ngôn ngữ đã chọn:</b></td><td>{lang_count}</td></tr>
            <tr><td><b>📁 Thư mục tùy chọn:</b></td><td>{folder_display}</td></tr>
            <tr><td><b>🎬 Chế độ video:</b></td><td>{"Video đơn" if self.video_radio.isChecked() else "Playlist"}</td></tr>
            <tr><td><b>📝 Chế độ phụ đề:</b></td><td>{self.sub_mode.currentText()}</td></tr>
            </table>
            <br>
            <p><b>🔧 Tùy chọn hiện tại:</b></p>
            <ul>
            <li>🔁 Convert SRT: {"✅" if self.convert_srt.isChecked() else "❌"}</li>
            <li>🎵 Audio Only: {"✅" if self.audio_only.isChecked() else "❌"}</li>
            <li>🖼️ Include Thumbnail: {"✅" if self.include_thumb.isChecked() else "❌"}</li>
            <li>📝 Subtitle Only: {"✅" if self.subtitle_only.isChecked() else "❌"}</li>
            </ul>
            """
            
            QMessageBox.information(self, "Settings Info", info_text)
            
            # Debug trong console
            self.debug_settings()
            
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"❌ Không thể hiển thị thông tin settings: {e}")

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
                log_dialog.setDetailedText(log_content)  # Full log trong detailed text
                log_dialog.exec()
                
            else:
                QMessageBox.information(self, "Log File", "📝 Chưa có file log nào được tạo.")
                
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"❌ Không thể đọc file log: {e}")

    def closeEvent(self, event):
        """Xử lý khi đóng ứng dụng - tự động lưu settings"""
        try:
            # Lưu settings không hiển thị thông báo
            self.auto_save_on_change()
            
            # Lưu vị trí cửa sổ cuối cùng
            self.settings.setValue("geometry", self.saveGeometry())
            
            # Cập nhật thời gian đóng ứng dụng
            from datetime import datetime
            self.settings.setValue("last_closed", datetime.now().isoformat())
            
        except Exception as e:
            debug_print(f"⚠️ Lỗi khi lưu settings: {e}")
        
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = DownloaderApp()
    win.show()
    sys.exit(app.exec())
