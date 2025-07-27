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

## Cài đặt

### Yêu cầu hệ thống
- Python 3.8+
- Windows 10/11 (đã test)
- ffmpeg (tự động tích hợp)

### Cách cài đặt

1. Clone repository này:
```bash
git clone <repository-url>
cd DownloadVID
```

2. Cài đặt dependencies:
```bash
pip install -r requirements.txt
```

3. Chạy ứng dụng:
```bash
python App.py
```

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

## Cấu trúc thư mục

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

## Đóng góp

Mọi đóng góp đều được hoan nghênh! Hãy tạo issue hoặc pull request.

## Giấy phép

MIT License - Xem file LICENSE để biết thêm chi tiết.

## Liên hệ

- Email: support@example.com
- GitHub: https://github.com/username/DownloadVID

---

**Lưu ý**: Vui lòng tuân thủ các điều khoản sử dụng của các nền tảng video khi sử dụng ứng dụng này. 