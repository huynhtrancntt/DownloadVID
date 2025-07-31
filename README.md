# HT DownloadVID v1.0

Ứng dụng tải video và phụ đề từ YouTube, TikTok và nhiều nền tảng khác với giao diện đồ họa thân thiện.

## Tính năng chính

- ✅ Tải video từ YouTube, TikTok, Facebook, Instagram và 1000+ trang web khác
- 📝 Tải phụ đề tự động và phụ đề chính thức với nhiều ngôn ngữ
- 🎵 Chuyển đổi video sang MP3
- 🖼️ Tải thumbnail của video
- 📂 Tự động tạo thư mục theo ngày hoặc tên tùy chỉnh
- 🔄 Đổi tên file tự động để tránh lỗi
- ⏹️ Có thể dừng quá trình tải bất cứ lúc nào

## Cài đặt và chạy (Windows)

### Cách 1: Sử dụng file Batch (Khuyến nghị)

1. **Lần đầu chạy** - Double-click vào `run_app.bat`:
   - Tự động kiểm tra Python
   - Tạo môi trường ảo (virtual environment)
   - Cài đặt dependencies
   - Chạy ứng dụng

2. **Các lần sau** - Double-click vào `start.bat` để chạy nhanh

3. **Chỉ cài đặt** - Chạy `install.bat` nếu chỉ muốn cài đặt dependencies

### Cách 2: Thủ công

#### Yêu cầu hệ thống
- Python 3.8+
- Windows 10/11 (đã test)
- ffmpeg (tự động tích hợp từ thư mục `ffmpeg/`)

#### Các bước cài đặt

1. Clone repository này:
```bash
git clone <repository-url>
cd DownloadVID
```

2. Tạo môi trường ảo:
```bash
python -m venv venv
```

3. Kích hoạt môi trường ảo:
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

4. Cài đặt dependencies:
```bash
pip install -r requirements.txt
```

5. Chạy ứng dụng:
```bash
python App.py
```

## Đóng gói thành file .exe

### ⚡ Cách nhanh nhất (Khuyến nghị)

**Double-click vào `build_complete.bat`** - File này sẽ:
- ✅ Tự động tạo môi trường ảo
- 📦 Cài đặt tất cả thư viện cần thiết
- 🔧 Kiểm tra và báo lỗi nếu thiếu gì
- 🚀 Đóng gói thành file .exe hoàn chỉnh
- 🧪 Tự động test file exe sau khi build

### Cách 1: Sử dụng file Batch thông thường

1. **Chuẩn bị**:
   - Đảm bảo đã cài đặt dependencies (`run_app.bat` hoặc `install.bat`)
   - Đặt file `ffmpeg.exe` vào thư mục `ffmpeg/`

2. **Đóng gói**: Double-click vào `build.bat`

3. **Kết quả**: File `HT_DownloadVID.exe` sẽ được tạo trong thư mục `release/`

### Cách 2: Thủ công

```bash
# Kích hoạt môi trường ảo
venv\Scripts\activate

# Cài đặt đầy đủ dependencies
pip install -r requirements.txt

# Chạy script build cải tiến
python build_exe.py
```

### 🔧 Khắc phục lỗi "thiếu thư viện"

Nếu file exe báo lỗi thiếu thư viện, hãy:

1. **Sử dụng `build_complete.bat`** thay vì `build.bat`
2. **Hoặc cài đặt thêm thư viện**:
   ```bash
   pip install websockets mutagen pycryptodomex brotli
   ```
3. **Build lại**: `python build_exe.py`

### Tính năng của file .exe

- 🚀 **Chạy độc lập**: Không cần cài đặt Python hay thư viện
- 📦 **Tích hợp đầy đủ**: Bao gồm tất cả dependencies và ffmpeg
- 💻 **Portable**: Có thể copy và chạy trên máy khác
- 🎯 **Kích thước tối ưu**: Nén UPX để giảm dung lượng
- 🧪 **Đã test**: Tự động kiểm tra sau khi build

## Cấu trúc files

```
DownloadVID/
├── App.py              # File chính của ứng dụng
├── requirements.txt    # Dependencies
├── README.md          # Hướng dẫn sử dụng
├── run_app.bat        # Batch file chạy đầy đủ (lần đầu)
├── start.bat          # Batch file chạy nhanh
├── install.bat        # Batch file chỉ cài đặt
├── build.bat          # Batch file đóng gói exe
├── build_exe.py       # Script đóng gói chi tiết
├── ffmpeg/            # Thư mục chứa ffmpeg
│   └── ffmpeg.exe     # File thực thi ffmpeg
├── venv/              # Môi trường ảo (tự động tạo)
└── release/           # Thư mục chứa file exe (sau khi build)
    └── HT_DownloadVID.exe
```

## Cấu hình FFmpeg

Ứng dụng sẽ tự động tìm và sử dụng `ffmpeg.exe` từ thư mục `ffmpeg/`. Nếu bạn chưa có:

1. Tải FFmpeg từ: https://ffmpeg.org/download.html
2. Tạo thư mục `ffmpeg` trong thư mục gốc của project
3. Copy file `ffmpeg.exe` vào thư mục `ffmpeg/`

**Lưu ý**: FFmpeg cần thiết để:
- Chuyển đổi video sang MP3
- Merge video và audio
- Xử lý các định dạng video phức tạp

## Hướng dẫn sử dụng

### Tải video cơ bản
1. Nhập URL video vào ô "Nhập URL video"
2. Chọn chế độ "Video đơn" hoặc "Playlist"
3. Nhấn "Bắt đầu tải"

### Tùy chọn phụ đề
- **Không tải**: Bỏ qua phụ đề
- **Phụ đề chính thức**: Tải phụ đề có sẵn từ video
- **Phụ đề tự động**: Tải phụ đề được tạo tự động

### Ngôn ngữ hỗ trợ
- 🇻🇳 Tiếng Việt
- 🇺🇸 Tiếng Anh
- 🇨🇳 Tiếng Trung (Giản thể)
- 🇹🇼 Tiếng Trung (Phồn thể)
- 🇰🇷 Tiếng Hàn
- 🇯🇵 Tiếng Nhật
- 🇫🇷 Tiếng Pháp
- 🇪🇸 Tiếng Tây Ban Nha

### Tùy chọn bổ sung
- **Chuyển phụ đề sang .srt**: Tự động chuyển đổi định dạng phụ đề
- **Tải âm thanh MP3**: Chỉ tải âm thanh, không tải video
- **Tải ảnh thumbnail**: Tải ảnh đại diện của video
- **Chỉ tải phụ đề**: Chỉ tải phụ đề, bỏ qua video/âm thanh

## Cấu trúc thư mục output

```
Video/
├── 2024-01-15/          # Thư mục theo ngày
│   ├── video1.mp4
│   ├── video1.srt
│   └── video1.jpg
└── Custom-Folder/       # Thư mục tùy chỉnh
    ├── playlist_001_video.mp4
    └── playlist_001_video.vi.srt
```

## Xử lý lỗi

Ứng dụng tự động xử lý các lỗi phổ biến:
- Tên file không hợp lệ
- Kết nối mạng không ổn định
- Video bị hạn chế địa lý
- Phụ đề không tồn tại

## Gỡ lỗi

Nếu gặp lỗi, hãy kiểm tra:
1. Kết nối internet
2. URL có hợp lệ không
3. Video có bị hạn chế không
4. Đủ dung lượng ổ cứng không
5. Python đã được cài đặt đúng cách
6. FFmpeg có trong thư mục `ffmpeg/` không

### Lỗi thường gặp

- **"Python chưa được cài đặt"**: Tải Python từ https://python.org
- **"Môi trường ảo chưa được tạo"**: Chạy `run_app.bat` hoặc `install.bat`
- **"Không tìm thấy yt-dlp"**: Dependencies chưa được cài đặt
- **"Lỗi khi chạy ffmpeg"**: Kiểm tra file `ffmpeg.exe` trong thư mục `ffmpeg/`
- **"Lỗi khi build exe"**: Đảm bảo tất cả dependencies đã được cài đặt

## Phân phối ứng dụng

### File .exe (Khuyến nghị cho người dùng cuối)
- 📁 Chỉ cần file `HT_DownloadVID.exe` từ thư mục `release/`
- 🚀 Chạy trực tiếp mà không cần cài đặt gì thêm
- 💾 Kích thước: ~80-120MB (bao gồm tất cả thư viện)

### Source code (Cho developers)
- 📂 Toàn bộ thư mục project
- 🐍 Cần Python và dependencies
- 🔧 Có thể chỉnh sửa và tùy biến

## Đóng góp

Mọi đóng góp đều được hoan nghênh! Hãy tạo issue hoặc pull request.

## Giấy phép

MIT License - Xem file LICENSE để biết thêm chi tiết.

## Liên hệ

- Email: support@example.com
- GitHub: https://github.com/username/DownloadVID

---

**Lưu ý**: Vui lòng tuân thủ các điều khoản sử dụng của các nền tảng video khi sử dụng ứng dụng này. 