import requests
import sys
import time
import zipfile
import shutil
import os

VERSION_FILE = "version.bin"
UPDATE_INFO_URL = "https://raw.githubusercontent.com/huynhtrancntt/DownloadVID/main/update_info.json"


def get_current_version():
    """Đọc phiên bản hiện tại từ file version.bin"""
    try:
        if os.path.exists(VERSION_FILE):
            with open(VERSION_FILE, 'r', encoding='utf-8') as f:
                version = f.read().strip()
                return version if version else "1.0.0"
        else:
            # Tạo file version.bin với version mặc định nếu chưa tồn tại
            save_current_version("1.0.0")
            return "1.0.0"
    except Exception as e:
        print(f"❌ Lỗi khi đọc version: {e}")
        return "1.0.0"


def save_current_version(version):
    """Lưu phiên bản hiện tại vào file version.bin"""
    try:
        with open(VERSION_FILE, 'w', encoding='utf-8') as f:
            f.write(version)
    except Exception as e:
        print(f"❌ Lỗi khi lưu version: {e}")


def check_for_update():
    current_version = get_current_version()
    try:
        response = requests.get(UPDATE_INFO_URL, timeout=10)
        data = response.json()

        latest_version = data.get("latest_version")
        download_url = data.get("download_url")

        if latest_version > current_version:
            print(f"🔔 Có phiên bản mới: {latest_version} (hiện tại: {current_version})")
            return latest_version, download_url
        else:
            print(f"✅ Bạn đang dùng phiên bản mới nhất: {current_version}")
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


def extract_and_install(zip_file, new_version, extract_to="temp_update"):
    """Giải nén và cài đặt cập nhật vào thư mục gốc"""
    try:
        print(f"\n📦 Đang giải nén {zip_file}...")
        
        # Tạo thư mục tạm để giải nén
        if os.path.exists(extract_to):
            shutil.rmtree(extract_to)
        os.makedirs(extract_to)
        
        # Giải nén file zip
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        
        print("✅ Giải nén hoàn tất.")
        
        # Copy tất cả file từ thư mục giải nén vào thư mục gốc
        print("📋 Đang cập nhật file...")
        current_dir = os.getcwd()
        
        for root, dirs, files in os.walk(extract_to):
            for file in files:
                src_file = os.path.join(root, file)
                # Tính relative path từ thư mục giải nén
                rel_path = os.path.relpath(src_file, extract_to)
                dst_file = os.path.join(current_dir, rel_path)
                
                # Tạo thư mục đích nếu chưa tồn tại
                dst_dir = os.path.dirname(dst_file)
                if dst_dir and not os.path.exists(dst_dir):
                    os.makedirs(dst_dir)
                
                # Copy file
                shutil.copy2(src_file, dst_file)
                print(f"   → {rel_path}")
        
        # Cập nhật version mới vào file .data
        save_current_version(new_version)
        
        # Dọn dẹp file tạm
        print("🧹 Đang dọn dẹp...")
        os.remove(zip_file)
        shutil.rmtree(extract_to)
        
        print(f"✅ Cập nhật hoàn tất! Phiên bản mới: {new_version}")
        print("🔄 Khởi động lại ứng dụng để áp dụng thay đổi.")
        
    except Exception as e:
        print(f"❌ Lỗi khi cài đặt cập nhật: {e}")
        # Dọn dẹp trong trường hợp lỗi
        if os.path.exists(zip_file):
            os.remove(zip_file)
        if os.path.exists(extract_to):
            shutil.rmtree(extract_to)


def main():
    latest_version, download_url = check_for_update()
    if latest_version and download_url:
        output_file = f"update_v{latest_version}.zip"
        download_with_progress(download_url, output_file)
        print(f"➡️ File cập nhật được lưu tại: {output_file}")
        
        # Giải nén và cài đặt cập nhật
        extract_and_install(output_file, latest_version)


if __name__ == "__main__":
    main()