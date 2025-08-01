import requests
import sys
import time

CURRENT_VERSION = "1.0.0"
UPDATE_INFO_URL = "https://raw.githubusercontent.com/huynhtrancntt/DownloadVID/main/update_info.json"


def check_for_update():
    try:
        response = requests.get(UPDATE_INFO_URL, timeout=10)
        data = response.json()

        latest_version = data.get("latest_version")
        download_url = data.get("download_url")

        if latest_version > CURRENT_VERSION:
            print(f"🔔 Có phiên bản mới: {latest_version}")
            return latest_version, download_url
        else:
            print("✅ Bạn đang dùng phiên bản mới nhất.")
            return None, None

    except Exception as e:
        print(f"❌ Lỗi khi kiểm tra phiên bản: {e}")
        return None, None


def download_with_progress(url, output_file):
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    total_mb = total_size / (1024 * 1024)

    downloaded = 0
    chunk_size = 1024 * 1024  # 1MB

    with open(output_file, 'wb') as f:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                downloaded_mb = downloaded / (1024 * 1024)
                percent = int((downloaded_mb / total_mb) * 100)
                sys.stdout.write(f"\r⬇️ Tải xuống: {downloaded_mb:.1f}/{total_mb:.1f} MB ({percent}%)")
                sys.stdout.flush()

    print("\n✅ Tải hoàn tất.")


def main():
    latest_version, download_url = check_for_update()
    if latest_version and download_url:
        output_file = f"update_v{latest_version}.zip"
        download_with_progress(download_url, output_file)
        print(f"➡️ File cập nhật được lưu tại: {output_file}")
        # (Tuỳ chọn) Giải nén hoặc chạy file sau khi cập nhật


if __name__ == "__main__":
    main()