import sys
import os
import subprocess
import glob                                                      # Thêm import cho xử lý file pattern
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QPushButton,
    QTextEdit, QCheckBox, QComboBox, QRadioButton,
    QHBoxLayout, QButtonGroup, QMessageBox, QProgressBar, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QScreen # Thêm import cho việc căn giữa cửa sổ

# ------------------- Worker -------------------
class DownloadWorker(QThread):
    message = Signal(str)
    progress_signal = Signal(int)
    finished = Signal(str)

    def __init__(self, urls, video_mode, audio_only, sub_mode, sub_lang, convert_srt, include_thumb, subtitle_only, custom_folder_name=""):
        super().__init__()
        self.urls = urls
        self.video_mode = video_mode
        self.audio_only = audio_only
        self.sub_mode = sub_mode
        self.sub_lang = sub_lang
        self.convert_srt = convert_srt
        self.include_thumb = include_thumb
        self.subtitle_only = subtitle_only                            # Chỉ tải phụ đề
        self.custom_folder_name = custom_folder_name.strip()
        self.stop_flag = False
        self.process = None

    def stop(self):
        self.stop_flag = True
        if self.process:
            self.process.terminate()
            self.message.emit("⏹ Dừng tải...")

    def run(self):
        try:
            # --------- Tạo thư mục ---------
            base_folder = "Video"
            os.makedirs(base_folder, exist_ok=True)

            if self.custom_folder_name:
                download_folder = os.path.join(base_folder, self.custom_folder_name)
            else:
                date_str = datetime.now().strftime("%Y-%m-%d")
                download_folder = os.path.join(base_folder, date_str)

            original_folder = download_folder
            count = 1
            while os.path.exists(download_folder):
                download_folder = f"{original_folder}-{count}"
                count += 1
            os.makedirs(download_folder, exist_ok=True)
            # -------------------------------

            for i, url in enumerate(self.urls, 1):
                if self.stop_flag:
                    self.message.emit("⏹ Đã dừng tải.")
                    break

                self.message.emit(f"🔗 [{i}] Đang tải: {url}")

                # Khởi tạo lệnh yt-dlp cơ bản
                cmd = ["yt-dlp", url, "--progress"]
                
                # Nếu chỉ tải phụ đề, bỏ qua tải video/audio
                if self.subtitle_only:
                    cmd.append("--skip-download")                     # Bỏ qua tải video/audio
                    self.message.emit("📝 Chế độ: Chỉ tải phụ đề")
                else:
                    # Ép định dạng MP4 cho video bình thường
                    cmd += ["-f", "bv*+ba/b", "--merge-output-format", "mp4"]

                # Template output
                output_template = f"%(title)s.%(ext)s" if self.video_mode else f"playlist_{i}_%(autonumber)03d_%(title)s.%(ext)s"
                cmd += ["-o", os.path.join(download_folder, output_template)]

                if not self.video_mode:
                    cmd.append("--yes-playlist")
                if self.audio_only and not self.subtitle_only:          # Chỉ extract audio nếu không phải subtitle-only
                    cmd += ["--extract-audio", "--audio-format", "mp3"]

                # ===== XỬ LÝ PHỤ ĐỀ =====
                if self.sub_mode != "❌ Không tải":
                    self.message.emit(f"📄 Đang xử lý phụ đề cho video {i}...")
                    
                    # Tạo chuỗi ngôn ngữ cho yt-dlp (vi,en,ko,...)
                    lang_string = ",".join(self.sub_lang) if isinstance(self.sub_lang, list) else self.sub_lang
                    
                    # Xử lý phụ đề chính thức (có sẵn từ video)
                    if self.sub_mode == "📄 Phụ đề chính thức":
                        cmd += ["--write-subs"]                    # Tải phụ đề có sẵn
                        cmd += ["--sub-langs", lang_string]        # Chọn ngôn ngữ phụ đề
                        self.message.emit(f"🔤 Tải phụ đề chính thức ngôn ngữ: {lang_string}")
                    
                    # Xử lý phụ đề tự động (auto-generated) - hỗ trợ nhiều ngôn ngữ
                    elif self.sub_mode == "🤖 Phụ đề tự động":
                        cmd += ["--write-auto-subs"]              # Tải phụ đề tự động
                        cmd += ["--sub-langs", lang_string]        # Chọn ngôn ngữ phụ đề
                        self.message.emit(f"🤖 Tải phụ đề tự động ngôn ngữ: {lang_string}")
                    
                    # Kiểm soát định dạng tên file phụ đề
                    self.message.emit(f"📝 Định dạng phụ đề: Tự động theo ngôn ngữ")
                    
                    # Bỏ qua lỗi nếu không có phụ đề và tiếp tục tải video
                    cmd += ["--ignore-errors"]                    # Bỏ qua lỗi phụ đề
                    cmd += ["--no-warnings"]                      # Giảm cảnh báo không cần thiết

                if self.convert_srt:
                    cmd += ["--convert-subs", "srt"]
                if self.include_thumb:
                    cmd.append("--write-thumbnail")

                # Chạy process
                self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

                for line in self.process.stdout:
                    if self.stop_flag:
                        self.process.terminate()
                        self.message.emit("⏹ Đang dừng...")
                        break

                    line = line.strip()
                    if line:
                        self.message.emit(line)
                        if "%" in line:
                            try:
                                percent_str = line.split("%", 1)[0].split()[-1].replace(".", "").strip()
                                percent = int(percent_str)
                                if 0 <= percent <= 100:
                                    self.progress_signal.emit(percent)
                            except:
                                pass
                self.process.wait()

                # Xử lý đổi tên file phụ đề sau khi tải xong
                if self.process.returncode == 0 and self.sub_mode != "❌ Không tải":
                    # Xử lý từng ngôn ngữ trong danh sách
                    lang_list = self.sub_lang if isinstance(self.sub_lang, list) else [self.sub_lang]
                    for lang in lang_list:
                        self.rename_subtitle_files(download_folder, lang)
                
                # Xử lý đổi tên file video (sửa ..mp4 thành .mp4)
                if self.process.returncode == 0:
                    self.rename_video_files(download_folder)

                if self.process.returncode == 0:
                    self.message.emit(f"✅ Hoàn thành link URL: {url}")
                else:
                    self.message.emit(f"❌ Lỗi khi tải link: {url}")

                self.progress_signal.emit(int(i / len(self.urls) * 100))

            self.finished.emit(f"📂 Video được lưu tại: {download_folder}")

        except Exception as e:
            self.message.emit(f"❌ Lỗi: {e}")

    def rename_subtitle_files(self, folder_path, sub_lang):
        """Đổi tên file phụ đề theo định dạng mong muốn"""
        try:
            if sub_lang == "en":
                # Tiếng Anh: xử lý cả .en.srt và ..srt
                # Trước tiên xử lý .en.srt thành .srt
                for subtitle_file in glob.glob(os.path.join(folder_path, "*.en.srt")):
                    new_name = subtitle_file.replace(".en.srt", ".srt")
                    if not os.path.exists(new_name):
                        os.rename(subtitle_file, new_name)
                        self.message.emit(f"📝 Đổi tên: {os.path.basename(subtitle_file)} → {os.path.basename(new_name)}")
                
                # Sau đó xử lý tất cả file có ..srt (bao gồm cả những file vừa đổi tên)
                for subtitle_file in glob.glob(os.path.join(folder_path, "*.srt")):
                    if "..srt" in subtitle_file:
                        new_name = subtitle_file.replace("..srt", ".srt")
                        if not os.path.exists(new_name) and new_name != subtitle_file:
                            os.rename(subtitle_file, new_name)
                            self.message.emit(f"📝 Sửa tên: {os.path.basename(subtitle_file)} → {os.path.basename(new_name)}")
            else:
                # Các ngôn ngữ khác: đổi từ ..vi.srt thành .vi.srt
                for subtitle_file in glob.glob(os.path.join(folder_path, f"*.{sub_lang}.srt")):
                    if f"..{sub_lang}.srt" in subtitle_file:
                        new_name = subtitle_file.replace(f"..{sub_lang}.srt", f".{sub_lang}.srt")
                        if not os.path.exists(new_name):
                            os.rename(subtitle_file, new_name)
                            self.message.emit(f"📝 Sửa tên: {os.path.basename(subtitle_file)} → {os.path.basename(new_name)}")
                            
        except Exception as e:
            self.message.emit(f"⚠️ Lỗi đổi tên phụ đề: {e}")

    def rename_video_files(self, folder_path):
        """Đổi tên file video (sửa ..mp4, ..mp3, etc. thành .mp4, .mp3)"""
        try:
            # Danh sách các định dạng file cần xử lý
            video_formats = ["*.mp4", "*.mp3", "*.mkv", "*.avi", "*.mov", "*.webm"]
            
            for format_pattern in video_formats:
                for media_file in glob.glob(os.path.join(folder_path, format_pattern)):
                    filename = os.path.basename(media_file)
                    
                    # Kiểm tra và sửa các trường hợp dấu chấm kép
                    if ".." in filename:
                        # Lấy phần mở rộng file
                        file_ext = os.path.splitext(filename)[1]  # .mp4, .mp3, etc.
                        
                        # Tạo tên file mới bằng cách thay thế dấu chấm kép
                        new_filename = filename.replace(f"..{file_ext[1:]}", file_ext)
                        new_path = os.path.join(folder_path, new_filename)
                        
                        # Đổi tên nếu file đích chưa tồn tại
                        if not os.path.exists(new_path):
                            os.rename(media_file, new_path)
                            self.message.emit(f"📝 Sửa tên: {filename} → {new_filename}")
                            
        except Exception as e:
            self.message.emit(f"⚠️ Lỗi đổi tên file media: {e}")


# ------------------- App -------------------
class DownloaderApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HT DownloadVID v1.0")
        self.setMinimumWidth(520)

        # Căn giữa cửa sổ trên màn hình
        self.center_window()

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # URL input
        self.url_input = QTextEdit()
        self.url_input.setPlaceholderText("📋 Mỗi dòng 1 link video hoặc playlist...")
        self.url_input.setFixedHeight(100)
        self.layout.addWidget(QLabel("Nhập URL video:"))
        self.layout.addWidget(self.url_input)

        # Folder name input
        self.folder_name_input = QTextEdit()
        self.folder_name_input.setPlaceholderText("Nhập tên thư mục (tuỳ chọn)")
        self.folder_name_input.setFixedHeight(30)
        self.layout.addWidget(QLabel("Tên thư mục tải (tuỳ chọn):"))
        self.layout.addWidget(self.folder_name_input)

        # Chế độ tải
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

        # Subtitle options
        # Tạo dropdown chọn chế độ phụ đề
        self.sub_mode = QComboBox()
        self.sub_mode.addItems([
            "❌ Không tải",                              # Không tải phụ đề
            "📄 Phụ đề chính thức",                     # Phụ đề có sẵn từ video
            "🤖 Phụ đề tự động"                         # Phụ đề tự động tạo
        ])
        self.sub_mode.setCurrentText("🤖 Phụ đề tự động")  # Mặc định chọn phụ đề tự động

        # Tạo phần chọn ngôn ngữ phụ đề với layout đẹp hơn
        lang_widget = QWidget()
        lang_layout = QVBoxLayout(lang_widget)
        lang_layout.setContentsMargins(0, 0, 0, 0)
        lang_layout.setSpacing(3)                                    # Giảm spacing để gọn hơn

        # Danh sách ngôn ngữ với checkbox - hiển thị theo dạng grid
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

        # Tạo layout dạng lưới 2 cột cho các ngôn ngữ
        grid_layout = QVBoxLayout()
        grid_layout.setSpacing(2)                                    # Giảm spacing giữa các hàng
        
        # Hàng 1: Tiếng Việt và Tiếng Anh
        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(5)                                    # Giảm spacing giữa các checkbox
        for code, name in languages[:2]:
            checkbox = QCheckBox(name)
            checkbox.setObjectName("lang-checkbox")
            if code in ["vi", "en"]:  # Mặc định chọn Việt và Anh
                checkbox.setChecked(True)
            self.lang_checkboxes[code] = checkbox
            row1_layout.addWidget(checkbox)
        row1_layout.addStretch()  # Đẩy về bên trái
        grid_layout.addLayout(row1_layout)

        # Hàng 2: Tiếng Trung
        row2_layout = QHBoxLayout()
        row2_layout.setSpacing(5)
        for code, name in languages[2:4]:
            checkbox = QCheckBox(name)
            checkbox.setObjectName("lang-checkbox")
            self.lang_checkboxes[code] = checkbox
            row2_layout.addWidget(checkbox)
        row2_layout.addStretch()
        grid_layout.addLayout(row2_layout)

        # Hàng 3: Hàn, Nhật
        row3_layout = QHBoxLayout()
        row3_layout.setSpacing(5)
        for code, name in languages[4:6]:
            checkbox = QCheckBox(name)
            checkbox.setObjectName("lang-checkbox")
            self.lang_checkboxes[code] = checkbox
            row3_layout.addWidget(checkbox)
        row3_layout.addStretch()
        grid_layout.addLayout(row3_layout)

        # Hàng 4: Pháp, Tây Ban Nha
        row4_layout = QHBoxLayout()
        row4_layout.setSpacing(5)
        for code, name in languages[6:8]:
            checkbox = QCheckBox(name)
            checkbox.setObjectName("lang-checkbox")
            self.lang_checkboxes[code] = checkbox
            row4_layout.addWidget(checkbox)
        row4_layout.addStretch()
        grid_layout.addLayout(row4_layout)

        lang_layout.addLayout(grid_layout)

        # Tạo các checkbox cho tùy chọn bổ sung
        self.convert_srt = QCheckBox("🔁 Chuyển phụ đề sang .srt")    # Chuyển đổi định dạng phụ đề
        self.convert_srt.setChecked(True)                            # Mặc định check vào ô này
        self.audio_only = QCheckBox("🎵 Tải âm thanh MP3")            # Chỉ tải âm thanh, không tải video
        self.include_thumb = QCheckBox("🖼️ Tải ảnh thumbnail")        # Tải ảnh đại diện của video
        self.subtitle_only = QCheckBox("📝 Chỉ tải phụ đề")          # Chỉ tải phụ đề, không tải video

        # Thêm các widget vào layout với nhãn mô tả
        self.layout.addWidget(QLabel("Chế độ phụ đề:"))              # Nhãn cho dropdown chế độ phụ đề
        self.layout.addWidget(self.sub_mode)                         # Dropdown chế độ phụ đề
        self.layout.addWidget(QLabel("Ngôn ngữ phụ đề:"))            # Nhãn cho phần chọn ngôn ngữ
        self.layout.addWidget(lang_widget)                           # Widget chứa các checkbox ngôn ngữ
        self.layout.addWidget(self.convert_srt)                      # Checkbox chuyển đổi SRT
        self.layout.addWidget(self.audio_only)                       # Checkbox tải âm thanh
        self.layout.addWidget(self.include_thumb)                    # Checkbox tải thumbnail
        self.layout.addWidget(self.subtitle_only)                    # Checkbox chỉ tải phụ đề

        # Buttons
        self.download_button = QPushButton("🚀 Bắt đầu tải")
        self.download_button.clicked.connect(self.start_download)
        self.stop_button = QPushButton("⏹ Dừng tải")
        self.stop_button.clicked.connect(self.stop_download)
        self.stop_button.setVisible(False)                           # Ẩn nút dừng ban đầu

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.download_button)
        button_layout.addWidget(self.stop_button)
        self.layout.addLayout(button_layout)

        # Progress and log
        self.progress = QProgressBar()
        self.progress.setVisible(False)                              # Ẩn thanh tiến trình ban đầu
        self.layout.addWidget(self.progress)

        self.output_list = QListWidget()
        self.output_list.setWordWrap(True)                           # Cho phép text xuống hàng
        self.output_list.setResizeMode(QListWidget.ResizeMode.Adjust) # Tự động điều chỉnh kích thước
        self.output_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff) # Tắt thanh cuộn ngang
        self.output_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)   # Chỉ hiện thanh cuộn dọc khi cần
        self.output_list.setMinimumHeight(120)                       # Chiều cao tối thiểu ban đầu
        self.layout.addWidget(self.output_list)

        # Style - Original styling
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
                background-color: #2d3748;                  /* Nền tối cho log */
                color: #e2e8f0;                             /* Chữ sáng */
                border: 2px solid #4a5568;                  /* Viền xám */
                border-radius: 6px;                         /* Bo góc */
                font-family: "Consolas", "Monaco", monospace; /* Font monospace */
                font-size: 12px;                            /* Cỡ chữ */
                padding: 8px;                               /* Khoảng cách trong */
                selection-background-color: #4299e1;        /* Nền khi chọn */
                alternate-background-color: #374151;        /* Nền xen kẽ */
                outline: none;                              /* Bỏ viền focus */
            }
            
            /* Styling cho từng item trong log */
            QListWidget::item {
                padding: 6px 8px;                           /* Khoảng cách trong item */
                border-bottom: 1px solid #4a5568;          /* Viền dưới phân cách */
                min-height: 20px;                           /* Chiều cao tối thiểu */
                max-width: 100%;                            /* Giới hạn chiều rộng */
                word-wrap: break-word;                      /* Cho phép ngắt từ */
                word-break: break-all;                      /* Ngắt từ mạnh */
                white-space: pre-wrap;                      /* Giữ nguyên xuống hàng */
                overflow-wrap: break-word;                  /* Ngắt từ khi cần */
                text-overflow: clip;                        /* Cắt text thay vì hiện ... */
            }
            
            /* Hiệu ứng hover cho item */
            QListWidget::item:hover {
                background-color: #4a5568;                  /* Nền khi hover */
            }
            
            /* Item được chọn */
            QListWidget::item:selected {
                background-color: #4299e1;                  /* Nền xanh khi chọn */
                color: #ffffff;                             /* Chữ trắng khi chọn */
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
            /* ===== STYLING CHO COMBOBOX ===== */
            QComboBox {
                background-color: #ffffff;              /* Nền trắng cho dropdown */
                border: 2px solid #ced4da;              /* Viền xám nhạt */
                border-radius: 8px;                     /* Bo góc mềm mại */
                padding: 10px 15px;                     /* Khoảng cách trong */
                color: #495057;                         /* Màu chữ xám đậm */
                font-size: 13px;                        /* Cỡ chữ */
                font-weight: 500;                       /* Độ đậm chữ vừa phải */
                min-height: 20px;                       /* Chiều cao tối thiểu */
                selection-background-color: #007bff;     /* Màu nền khi chọn */
            }
            
            /* Hiệu ứng khi hover (di chuột qua) */
            QComboBox:hover {
                border-color: #80bdff;                  /* Viền xanh khi hover */
                background-color: #f8f9fa;              /* Nền sáng nhẹ khi hover */
                box-shadow: 0 2px 4px rgba(0,0,0,0.1); /* Đổ bóng nhẹ */
            }
            
            /* Hiệu ứng khi focus (được chọn) */
            QComboBox:focus {
                border-color: #007bff;                  /* Viền xanh đậm khi focus */
                outline: none;                          /* Bỏ viền mặc định */
                box-shadow: 0 0 0 3px rgba(0,123,255,0.25); /* Halo xanh */
            }
            
            /* Hiệu ứng khi bị disabled */
            QComboBox:disabled {
                background-color: #e9ecef;              /* Nền xám khi disabled */
                color: #6c757d;                         /* Chữ xám nhạt */
                border-color: #dee2e6;                  /* Viền xám nhạt */
            }
            
            /* Styling cho nút dropdown (mũi tên) */
            QComboBox::drop-down {
                subcontrol-origin: padding;             /* Vị trí gốc */
                subcontrol-position: top right;         /* Vị trí góc phải trên */
                width: 30px;                            /* Độ rộng vùng nút */
                border-left: 1px solid #ced4da;        /* Viền trái phân cách */
                border-top-right-radius: 8px;          /* Bo góc phải trên */
                border-bottom-right-radius: 8px;       /* Bo góc phải dưới */
                background-color: #f8f9fa;              /* Nền sáng cho nút */
            }
            
            /* Hiệu ứng hover cho nút dropdown */
            QComboBox::drop-down:hover {
                background-color: #e9ecef;              /* Nền đậm hơn khi hover */
            }
            
            /* Styling cho mũi tên dropdown */
            QComboBox::down-arrow {
                image: none;                            /* Bỏ hình ảnh mặc định */
                border-left: 6px solid transparent;    /* Tạo mũi tên bằng CSS */
                border-right: 6px solid transparent;   /* Cạnh phải trong suốt */
                border-top: 6px solid #495057;         /* Cạnh trên tạo mũi tên */
                margin: 0px;                            /* Bỏ margin */
            }
            
            /* Mũi tên khi hover */
            QComboBox::down-arrow:hover {
                border-top-color: #007bff;              /* Đổi màu mũi tên khi hover */
            }
            
            /* Styling cho danh sách dropdown */
            QComboBox QAbstractItemView {
                background-color: #ffffff;              /* Nền trắng cho danh sách */
                border: 2px solid #007bff;              /* Viền xanh cho danh sách */
                border-radius: 8px;                     /* Bo góc danh sách */
                selection-background-color: #007bff;     /* Nền xanh khi chọn item */
                selection-color: #ffffff;               /* Chữ trắng khi chọn */
                color: #495057;                         /* Màu chữ mặc định */
                padding: 5px;                           /* Khoảng cách trong */
                outline: none;                          /* Bỏ viền focus */
            }
            
            /* Styling cho từng item trong danh sách */
            QComboBox QAbstractItemView::item {
                height: 35px;                           /* Chiều cao mỗi item */
                padding: 8px 12px;                      /* Khoảng cách trong item */
                border-radius: 4px;                     /* Bo góc nhẹ cho item */
                margin: 2px;                            /* Khoảng cách giữa các item */
            }
            
            /* Hiệu ứng hover cho item */
            QComboBox QAbstractItemView::item:hover {
                background-color: #e3f2fd;              /* Nền xanh nhạt khi hover */
                color: #1976d2;                         /* Chữ xanh đậm khi hover */
            }
            
            /* Item được chọn */
            QComboBox QAbstractItemView::item:selected {
                background-color: #007bff;              /* Nền xanh khi được chọn */
                color: #ffffff;                         /* Chữ trắng khi được chọn */
                font-weight: 600;                       /* Chữ đậm khi được chọn */
            }
            /* ===== STYLING CHO LABEL (NHÃN) ===== */
            QLabel {
                color: #343a40;                         /* Màu chữ xám đậm cho nhãn */
                font-weight: 500;                       /* Độ đậm chữ vừa phải */
                font-size: 13px;                        /* Cỡ chữ tiêu chuẩn */
                margin: 5px 0px;                        /* Khoảng cách trên dưới */
            }
            
            /* ===== STYLING CHO CHECKBOX ===== */
            QCheckBox {
                color: #495057;                         /* Màu chữ cho text checkbox */
                font-size: 13px;                        /* Cỡ chữ */
                spacing: 8px;                           /* Khoảng cách giữa hộp tick và text */
                padding: 5px;                           /* Khoảng cách trong */
            }
            
            /* Hộp tick của checkbox */
            QCheckBox::indicator {
                width: 18px;                            /* Chiều rộng hộp tick */
                height: 18px;                           /* Chiều cao hộp tick */
                border: 2px solid #ced4da;              /* Viền xám cho hộp tick */
                border-radius: 3px;                     /* Bo góc nhẹ */
                background-color: #ffffff;              /* Nền trắng */
            }
            
            /* Hiệu ứng hover cho hộp tick */
            QCheckBox::indicator:hover {
                border-color: #007bff;                  /* Viền xanh khi hover */
                background-color: #f8f9fa;              /* Nền sáng nhẹ khi hover */
            }
            
            /* Hộp tick khi được check */
            QCheckBox::indicator:checked {
                background-color: #28a745;              /* Nền xanh lá khi checked */
                border-color: #28a745;                  /* Viền xanh lá */
                image: none;                            /* Bỏ hình ảnh mặc định */
            }
            
            /* Tạo dấu tick bằng CSS */
            QCheckBox::indicator:checked::after {
                content: '✓';                           /* Ký tự tick */
                color: #ffffff;                         /* Màu trắng cho tick */
                font-size: 12px;                        /* Cỡ chữ tick */
                font-weight: bold;                      /* Tick đậm */
                position: absolute;                     /* Vị trí tuyệt đối */
                left: 3px;                              /* Vị trí từ trái */
                top: 1px;                               /* Vị trí từ trên */
            }
            
            /* ===== STYLING CHO RADIO BUTTON ===== */
            QRadioButton {
                color: #495057;                         /* Màu chữ cho text radio */
                font-size: 13px;                        /* Cỡ chữ */
                spacing: 8px;                           /* Khoảng cách giữa nút tròn và text */
                padding: 5px;                           /* Khoảng cách trong */
            }
            
            /* Nút tròn của radio button */
            QRadioButton::indicator {
                width: 18px;                            /* Chiều rộng nút tròn */
                height: 18px;                           /* Chiều cao nút tròn */
                border: 2px solid #ced4da;              /* Viền xám cho nút tròn */
                border-radius: 9px;                     /* Bo tròn hoàn toàn */
                background-color: #ffffff;              /* Nền trắng */
            }
            
            /* Hiệu ứng hover cho nút tròn */
            QRadioButton::indicator:hover {
                border-color: #007bff;                  /* Viền xanh khi hover */
                background-color: #f8f9fa;              /* Nền sáng nhẹ khi hover */
            }
            
            /* Nút tròn khi được chọn */
            QRadioButton::indicator:checked {
                background-color: #28a745;              /* Nền xanh lá khi checked */
                border-color: #28a745;                  /* Viền xanh lá */
            }
            
            /* Tạo chấm tròn bên trong khi được chọn */
            QRadioButton::indicator:checked::after {
                content: '';                            /* Nội dung rỗng */
                width: 8px;                             /* Chiều rộng chấm tròn */
                height: 8px;                            /* Chiều cao chấm tròn */
                border-radius: 4px;                     /* Bo tròn chấm */
                background-color: #ffffff;              /* Màu trắng cho chấm */
                margin: 3px;                            /* Căn giữa chấm */
                position: absolute;                     /* Vị trí tuyệt đối */
                left: 3px;                              /* Vị trí từ trái */
                top: 3px;                               /* Vị trí từ trên */
            }
            
            /* ===== STYLING CHO LANGUAGE CHECKBOXES ===== */
            #lang-checkbox {
                color: #495057;                         /* Màu chữ cho text checkbox */
                font-size: 11px;                        /* Cỡ chữ nhỏ hơn */
                font-weight: 500;                       /* Độ đậm chữ */
                spacing: 6px;                           /* Khoảng cách giữa hộp tick và text nhỏ hơn */
                padding: 3px 6px;                       /* Khoảng cách trong nhỏ hơn */
                margin: 1px;                            /* Margin nhỏ hơn giữa các checkbox */
                border: 1px solid #e9ecef;              /* Viền nhẹ */
                border-radius: 4px;                     /* Bo góc nhỏ hơn */
                background-color: #f8f9fa;              /* Nền sáng nhẹ */
                max-width: 180px;                       /* Giới hạn chiều rộng */
            }
            
            /* Hiệu ứng hover cho language checkbox */
            #lang-checkbox:hover {
                background-color: #e9ecef;              /* Nền đậm hơn khi hover */
                border-color: #007bff;                  /* Viền xanh khi hover */
            }
            
            /* Hộp tick của language checkbox */
            #lang-checkbox::indicator {
                width: 14px;                            /* Chiều rộng hộp tick nhỏ hơn */
                height: 14px;                           /* Chiều cao hộp tick nhỏ hơn */
                border: 2px solid #ced4da;              /* Viền xám cho hộp tick */
                border-radius: 2px;                     /* Bo góc nhỏ hơn */
                background-color: #ffffff;              /* Nền trắng */
            }
            
            /* Hiệu ứng hover cho hộp tick language */
            #lang-checkbox::indicator:hover {
                border-color: #007bff;                  /* Viền xanh khi hover */
                background-color: #f8f9fa;              /* Nền sáng nhẹ khi hover */
            }
            
            /* Hộp tick language khi được check */
            #lang-checkbox::indicator:checked {
                background-color: #007bff;              /* Nền xanh khi checked */
                border-color: #007bff;                  /* Viền xanh */
                image: none;                            /* Bỏ hình ảnh mặc định */
            }
            
            /* Tạo dấu tick bằng CSS cho language checkbox */
            #lang-checkbox::indicator:checked::after {
                content: '✓';                           /* Ký tự tick */
                color: #ffffff;                         /* Màu trắng cho tick */
                font-size: 9px;                         /* Cỡ chữ tick nhỏ hơn */
                font-weight: bold;                      /* Tick đậm */
                position: absolute;                     /* Vị trí tuyệt đối */
                left: 2px;                              /* Vị trí từ trái */
                top: -1px;                              /* Vị trí từ trên */
            }
        """)

        self.worker = None

    def create_header(self):
        """Tạo phần header với logo và thông tin"""
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setSpacing(5)
        
        # Title
        title_label = QLabel("🎬 HT DownloadVID")
        title_label.setObjectName("title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Subtitle
        subtitle_label = QLabel("Tải video & phụ đề từ YouTube, TikTok và nhiều nền tảng khác")
        subtitle_label.setObjectName("subtitle")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        self.layout.addWidget(header_widget)

    def create_url_section(self):
        """Tạo phần nhập URL"""
        url_group = QWidget()
        url_group.setObjectName("section")
        url_layout = QVBoxLayout(url_group)
        url_layout.setSpacing(8)
        
        # URL input label
        url_label = QLabel("📋 Nhập URL video:")
        url_label.setObjectName("section-title")
        
        # URL input field
        self.url_input = QTextEdit()
        self.url_input.setPlaceholderText("Nhập URL video hoặc playlist...\nVí dụ: https://www.youtube.com/watch?v=...")
        self.url_input.setFixedHeight(80)
        self.url_input.setObjectName("url-input")
        
        # Folder name
        folder_label = QLabel("📁 Tên thư mục tải (tuỳ chọn):")
        folder_label.setObjectName("section-title")
        
        self.folder_name_input = QTextEdit()
        self.folder_name_input.setPlaceholderText("Để trống sẽ tự động tạo thư mục theo ngày")
        self.folder_name_input.setFixedHeight(35)
        self.folder_name_input.setObjectName("folder-input")
        
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        url_layout.addWidget(folder_label)
        url_layout.addWidget(self.folder_name_input)
        
        self.layout.addWidget(url_group)

    def create_options_section(self):
        """Tạo phần tùy chọn download"""
        options_group = QWidget()
        options_group.setObjectName("section")
        options_layout = QVBoxLayout(options_group)
        options_layout.setSpacing(12)
        
        # Download mode
        mode_label = QLabel("🎯 Chế độ tải:")
        mode_label.setObjectName("section-title")
        
        self.mode_group = QButtonGroup(self)
        self.video_radio = QRadioButton("🎬 Video đơn")
        self.playlist_radio = QRadioButton("📃 Playlist")
        self.video_radio.setChecked(True)
        self.video_radio.setObjectName("radio-button")
        self.playlist_radio.setObjectName("radio-button")
        
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(self.video_radio)
        mode_layout.addWidget(self.playlist_radio)
        mode_layout.addStretch()
        
        self.mode_group.addButton(self.video_radio)
        self.mode_group.addButton(self.playlist_radio)
        
        # Subtitle options
        subtitle_label = QLabel("📝 Tùy chọn phụ đề:")
        subtitle_label.setObjectName("section-title")
        
        self.sub_mode = QComboBox()
        self.sub_mode.addItems([
            "❌ Không tải",
            "📄 Phụ đề chính thức", 
            "🤖 Phụ đề tự động"
        ])
        self.sub_mode.setCurrentText("🤖 Phụ đề tự động")
        self.sub_mode.setObjectName("combo-box")
        
        # Language selection - FIX: Ensure proper setup
        lang_label = QLabel("🌍 Ngôn ngữ phụ đề:")
        lang_label.setObjectName("section-title")
        
        self.langs_list = QListWidget()
        self.langs_list.setMaximumHeight(120)
        self.langs_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)  # Enable multi-selection
        self.langs_list.setObjectName("language-list")
        
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
        
        # Add language items with checkboxes
        for code, name in languages:
            item = QListWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, code)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.langs_list.addItem(item)
            
            # Default check Vietnamese and English
            if code in ["vi", "en"]:
                item.setCheckState(Qt.CheckState.Checked)
        
        # Additional options
        additional_label = QLabel("⚙️ Tùy chọn bổ sung:")
        additional_label.setObjectName("section-title")
        
        self.convert_srt = QCheckBox("🔁 Chuyển phụ đề sang .srt")
        self.convert_srt.setChecked(True)
        self.convert_srt.setObjectName("checkbox")
        
        self.audio_only = QCheckBox("🎵 Chỉ tải âm thanh MP3")
        self.audio_only.setObjectName("checkbox")
        
        self.include_thumb = QCheckBox("🖼️ Tải ảnh thumbnail")
        self.include_thumb.setObjectName("checkbox")
        
        self.subtitle_only = QCheckBox("📝 Chỉ tải phụ đề")
        self.subtitle_only.setObjectName("checkbox")
        
        # Add all to layout
        options_layout.addWidget(mode_label)
        options_layout.addLayout(mode_layout)
        options_layout.addWidget(subtitle_label)
        options_layout.addWidget(self.sub_mode)
        options_layout.addWidget(lang_label)
        options_layout.addWidget(self.langs_list)
        options_layout.addWidget(additional_label)
        options_layout.addWidget(self.convert_srt)
        options_layout.addWidget(self.audio_only)
        options_layout.addWidget(self.include_thumb)
        options_layout.addWidget(self.subtitle_only)
        
        self.layout.addWidget(options_group)

    def create_control_buttons(self):
        """Tạo các nút điều khiển"""
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setSpacing(10)
        
        self.download_button = QPushButton("🚀 Bắt đầu tải")
        self.download_button.clicked.connect(self.start_download)
        self.download_button.setObjectName("primary-button")
        self.download_button.setMinimumHeight(45)
        
        self.stop_button = QPushButton("⏹ Dừng tải")
        self.stop_button.clicked.connect(self.stop_download)
        self.stop_button.setVisible(False)
        self.stop_button.setObjectName("danger-button")
        self.stop_button.setMinimumHeight(45)
        
        button_layout.addWidget(self.download_button)
        button_layout.addWidget(self.stop_button)
        
        self.layout.addWidget(button_widget)

    def create_progress_log_section(self):
        """Tạo phần progress và log"""
        progress_group = QWidget()
        progress_group.setObjectName("section")
        progress_layout = QVBoxLayout(progress_group)
        progress_layout.setSpacing(10)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setObjectName("progress-bar")
        self.progress.setMinimumHeight(25)
        
        # Log area
        log_label = QLabel("📊 Nhật ký tải:")
        log_label.setObjectName("section-title")
        
        self.output_list = QListWidget()
        self.output_list.setWordWrap(True)
        self.output_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.output_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.output_list.setMinimumHeight(120)
        self.output_list.setObjectName("log-area")
        
        progress_layout.addWidget(self.progress)
        progress_layout.addWidget(log_label)
        progress_layout.addWidget(self.output_list)
        
        self.layout.addWidget(progress_group)

    def apply_modern_styling(self):
        """Áp dụng styling hiện đại và đẹp mắt"""
        self.setStyleSheet("""
            /* ===== MAIN WINDOW ===== */
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f0f4f8, stop:1 #e2e8f0);
                font-family: "Segoe UI", "SF Pro Display", -apple-system, BlinkMacSystemFont, Arial, sans-serif;
                font-size: 13px;
                color: #2d3748;
            }
            
            /* ===== HEADER ===== */
            #title {
                font-size: 32px;
                font-weight: 700;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                -webkit-background-clip: text;
                color: transparent;
                margin: 15px 0px 5px 0px;
                letter-spacing: -0.5px;
            }
            
            #subtitle {
                font-size: 15px;
                color: #718096;
                margin-bottom: 25px;
                font-weight: 400;
            }
            
            /* ===== SECTIONS ===== */
            QWidget#section {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f7fafc);
                border: 2px solid #e2e8f0;
                border-radius: 16px;
                padding: 24px;
                margin: 8px 0px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
            }
            
            #section-title {
                font-size: 15px;
                font-weight: 700;
                color: #2d3748;
                margin-bottom: 12px;
                padding-bottom: 4px;
                border-bottom: 2px solid #e2e8f0;
            }
            
            /* ===== INPUT FIELDS ===== */
            #url-input, #folder-input {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f7fafc);
                border: 2px solid #cbd5e0;
                border-radius: 12px;
                padding: 16px;
                font-size: 14px;
                color: #2d3748;
                selection-background-color: #667eea;
            }
            
            #url-input:focus, #folder-input:focus {
                border: 2px solid #667eea;
                background: #ffffff;
                outline: none;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }
            
            /* ===== COMBO BOX ===== */
            #combo-box {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f7fafc);
                border: 2px solid #cbd5e0;
                border-radius: 12px;
                padding: 12px 16px;
                font-size: 14px;
                font-weight: 500;
                min-height: 24px;
                color: #2d3748;
            }
            
            #combo-box:hover {
                border-color: #667eea;
                background: #ffffff;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            }
            
            #combo-box:focus {
                border-color: #667eea;
                outline: none;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }
            
            #combo-box::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 32px;
                border-left: 1px solid #cbd5e0;
                border-top-right-radius: 12px;
                border-bottom-right-radius: 12px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f7fafc, stop:1 #edf2f7);
            }
            
            #combo-box::down-arrow {
                image: none;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 6px solid #718096;
                margin: 0px;
            }
            
            #combo-box QAbstractItemView {
                background-color: #ffffff;
                border: 2px solid #667eea;
                border-radius: 12px;
                selection-background-color: #667eea;
                selection-color: #ffffff;
                color: #2d3748;
                padding: 8px;
                outline: none;
            }
            
            #combo-box QAbstractItemView::item {
                height: 40px;
                padding: 8px 16px;
                border-radius: 8px;
                margin: 2px;
            }
            
            #combo-box QAbstractItemView::item:hover {
                background-color: #edf2f7;
                color: #2d3748;
            }
            
            #combo-box QAbstractItemView::item:selected {
                background-color: #667eea;
                color: #ffffff;
                font-weight: 600;
            }
            
            /* ===== LANGUAGE LIST ===== */
            #language-list {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f7fafc);
                border: 2px solid #cbd5e0;
                border-radius: 12px;
                padding: 12px;
                outline: none;
                font-size: 14px;
            }
            
            #language-list::item {
                padding: 12px 16px;
                border-radius: 8px;
                margin: 2px 0px;
                background-color: transparent;
                color: #2d3748;
                font-weight: 500;
                min-height: 20px;
            }
            
            #language-list::item:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #e6fffa, stop:1 #f0fff4);
                color: #2d3748;
            }
            
            #language-list::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: #ffffff;
                font-weight: 600;
            }
            
            /* ===== RADIO BUTTONS ===== */
            #radio-button {
                font-size: 14px;
                font-weight: 600;
                color: #2d3748;
                spacing: 12px;
                padding: 8px;
            }
            
            #radio-button::indicator {
                width: 20px;
                height: 20px;
                border: 3px solid #cbd5e0;
                border-radius: 10px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f7fafc);
            }
            
            #radio-button::indicator:hover {
                border-color: #667eea;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #edf2f7, stop:1 #e2e8f0);
            }
            
            #radio-button::indicator:checked {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border-color: #667eea;
            }
            
            /* ===== CHECKBOXES ===== */
            #checkbox {
                font-size: 14px;
                font-weight: 500;
                color: #2d3748;
                spacing: 12px;
                padding: 8px;
            }
            
            #checkbox::indicator {
                width: 20px;
                height: 20px;
                border: 3px solid #cbd5e0;
                border-radius: 6px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f7fafc);
            }
            
            #checkbox::indicator:hover {
                border-color: #667eea;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #edf2f7, stop:1 #e2e8f0);
            }
            
            #checkbox::indicator:checked {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #48bb78, stop:1 #38a169);
                border-color: #48bb78;
                image: none;
            }
            
            /* ===== BUTTONS ===== */
            #primary-button {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: #ffffff;
                border: none;
                border-radius: 12px;
                padding: 16px 32px;
                font-size: 16px;
                font-weight: 700;
                letter-spacing: 0.5px;
            }
            
            #primary-button:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5a67d8, stop:1 #6b46c1);
                transform: translateY(-1px);
                box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
            }
            
            #primary-button:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4c51bf, stop:1 #553c9a);
                transform: translateY(0px);
            }
            
            #primary-button:disabled {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #a0aec0, stop:1 #cbd5e0);
                color: #ffffff;
            }
            
            #danger-button {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #fc8181, stop:1 #f56565);
                color: #ffffff;
                border: none;
                border-radius: 12px;
                padding: 16px 32px;
                font-size: 16px;
                font-weight: 700;
                letter-spacing: 0.5px;
            }
            
            #danger-button:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #f56565, stop:1 #e53e3e);
                box-shadow: 0 8px 25px rgba(245, 101, 101, 0.3);
            }
            
            /* ===== PROGRESS BAR ===== */
            #progress-bar {
                border: 2px solid #cbd5e0;
                border-radius: 16px;
                text-align: center;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #edf2f7, stop:1 #e2e8f0);
                color: #2d3748;
                font-weight: 700;
                font-size: 14px;
            }
            
            #progress-bar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 14px;
            }
            
            /* ===== LOG AREA ===== */
            #log-area {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a202c, stop:1 #2d3748);
                color: #e2e8f0;
                border: 2px solid #4a5568;
                border-radius: 12px;
                font-family: "JetBrains Mono", "SF Mono", "Monaco", "Consolas", monospace;
                font-size: 13px;
                padding: 16px;
                selection-background-color: #667eea;
                outline: none;
            }
            
            #log-area::item {
                padding: 8px 12px;
                border-bottom: 1px solid rgba(74, 85, 104, 0.3);
                border-radius: 6px;
                margin: 2px 0px;
                background-color: transparent;
            }
            
            #log-area::item:hover {
                background-color: rgba(74, 85, 104, 0.2);
            }
            
            #log-area::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: #ffffff;
                font-weight: 500;
            }
        """)

    def center_window(self):
        """Căn giữa cửa sổ trên màn hình"""
        # Đặt kích thước mặc định cho cửa sổ
        self.resize(520, 700)
        
        # Lấy thông tin màn hình
        screen = QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            window_geometry = self.frameGeometry()
            
            # Tính toán vị trí giữa màn hình
            center_point = screen_geometry.center()
            window_geometry.moveCenter(center_point)
            
            # Di chuyển cửa sổ đến vị trí đã tính
            self.move(window_geometry.topLeft())

    def start_download(self):
        urls = [u.strip() for u in self.url_input.toPlainText().splitlines() if u.strip()]
        if not urls:
            QMessageBox.warning(self, "Cảnh báo", "Bạn chưa nhập URL nào.")
            return

        self.output_list.clear()
        self.progress.setValue(0)
        
        # Hiện nút dừng và thanh tiến trình khi bắt đầu tải
        self.stop_button.setVisible(True)                            # Hiện nút dừng
        self.progress.setVisible(True)                               # Hiện thanh tiến trình
        self.download_button.setEnabled(False)                       # Vô hiệu hóa nút tải
        self.output_list.setMinimumHeight(200)                       # Tăng chiều cao ô log khi tải

        # Lấy danh sách ngôn ngữ đã chọn từ QListWidget (theo checkbox)
        selected_lang_codes = []
        for code, checkbox in self.lang_checkboxes.items():
            if checkbox.isChecked():
                selected_lang_codes.append(code)
        
        # Nếu không chọn ngôn ngữ nào, mặc định là tiếng Việt và tiếng Anh
        if not selected_lang_codes:
            selected_lang_codes = ["vi", "en"]

        self.worker = DownloadWorker(
            urls,
            video_mode=self.video_radio.isChecked(),
            audio_only=self.audio_only.isChecked(),
            sub_mode=self.sub_mode.currentText(),
            sub_lang=selected_lang_codes, # Pass a list of selected language codes
            convert_srt=self.convert_srt.isChecked(),
            include_thumb=self.include_thumb.isChecked(),
            subtitle_only=self.subtitle_only.isChecked(),
            custom_folder_name=self.folder_name_input.toPlainText()
        )

        self.worker.message.connect(self.output_list.addItem)
        self.worker.message.connect(self.scroll_to_bottom)           # Tự động cuộn xuống cuối
        self.worker.progress_signal.connect(self.progress.setValue)
        self.worker.finished.connect(self.output_list.addItem)
        self.worker.finished.connect(self.scroll_to_bottom)          # Cuộn xuống cuối khi hoàn thành
        self.worker.finished.connect(self.on_download_finished)      # Kết nối signal hoàn thành

        self.worker.start()

    def stop_download(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.output_list.addItem("⏹ Đang dừng tiến trình...")
            self.scroll_to_bottom()                                  # Cuộn xuống cuối khi dừng
            
            # Ẩn nút dừng, thanh tiến trình và kích hoạt lại nút tải khi dừng thủ công
            self.stop_button.setVisible(False)                       # Ẩn nút dừng
            self.progress.setVisible(False)                          # Ẩn thanh tiến trình
            self.download_button.setEnabled(True)                    # Kích hoạt lại nút tải
            self.output_list.setMinimumHeight(120)                   # Đặt lại chiều cao ô log khi dừng
        else:
            QMessageBox.information(self, "Thông báo", "Hiện không có tác vụ nào đang chạy.")

    def on_download_finished(self):
        """Xử lý khi tải hoàn thành - ẩn nút dừng, thanh tiến trình và kích hoạt lại nút tải"""
        self.stop_button.setVisible(False)                           # Ẩn nút dừng
        self.progress.setVisible(False)                              # Ẩn thanh tiến trình
        self.download_button.setEnabled(True)                        # Kích hoạt lại nút tải
        self.output_list.setMinimumHeight(120)                       # Đặt lại chiều cao ô log khi kết thúc

    def scroll_to_bottom(self):
        """Cuộn xuống cuối danh sách khi có thêm mục mới"""
        self.output_list.scrollToBottom()


# ------------------- MAIN -------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = DownloaderApp()
    win.show()
    sys.exit(app.exec())
