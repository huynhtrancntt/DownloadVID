import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import requests
import zipfile
import shutil
import os
import sys
from datetime import datetime

VERSION_FILE = "version.bin"
UPDATE_INFO_URL = "https://raw.githubusercontent.com/huynhtrancntt/DownloadVID/main/update_info.json"

class UpdaterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("DownloadVID - Trình Cập Nhật")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        
        # Thiết lập style
        self.setup_style()
        
        # Tạo giao diện
        self.create_widgets()
        
        # Tự động kiểm tra version khi khởi động
        self.check_version_on_startup()
    
    def setup_style(self):
        """Thiết lập style cho giao diện"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Cấu hình màu sắc
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'), foreground='#2c3e50')
        style.configure('Info.TLabel', font=('Arial', 10), foreground='#34495e')
        style.configure('Success.TLabel', font=('Arial', 10), foreground='#27ae60')
        style.configure('Error.TLabel', font=('Arial', 10), foreground='#e74c3c')
        style.configure('Update.TButton', font=('Arial', 11, 'bold'))
    
    def create_widgets(self):
        """Tạo các widget cho giao diện"""
        # Frame chính
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Tiêu đề
        title_label = ttk.Label(main_frame, text="🔄 TRÌNH CẬP NHẬT DOWNLOADVID", style='Title.TLabel')
        title_label.pack(pady=(0, 20))
        
        # Frame thông tin version
        version_frame = ttk.LabelFrame(main_frame, text="Thông Tin Phiên Bản", padding="15")
        version_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Version hiện tại
        current_frame = ttk.Frame(version_frame)
        current_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(current_frame, text="Phiên bản hiện tại:", style='Info.TLabel').pack(side=tk.LEFT)
        self.current_version_label = ttk.Label(current_frame, text="Đang kiểm tra...", style='Info.TLabel')
        self.current_version_label.pack(side=tk.RIGHT)
        
        # Version mới nhất
        latest_frame = ttk.Frame(version_frame)
        latest_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(latest_frame, text="Phiên bản mới nhất:", style='Info.TLabel').pack(side=tk.LEFT)
        self.latest_version_label = ttk.Label(latest_frame, text="Đang kiểm tra...", style='Info.TLabel')
        self.latest_version_label.pack(side=tk.RIGHT)
        
        # Trạng thái
        status_frame = ttk.Frame(version_frame)
        status_frame.pack(fill=tk.X)
        ttk.Label(status_frame, text="Trạng thái:", style='Info.TLabel').pack(side=tk.LEFT)
        self.status_label = ttk.Label(status_frame, text="Đang kiểm tra...", style='Info.TLabel')
        self.status_label.pack(side=tk.RIGHT)
        
        # Frame nút bấm
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.check_button = ttk.Button(button_frame, text="🔍 Kiểm Tra Cập Nhật", 
                                      command=self.check_for_update_thread)
        self.check_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.update_button = ttk.Button(button_frame, text="⬇️ Cập Nhật Ngay", 
                                       command=self.start_update_thread, style='Update.TButton',
                                       state=tk.DISABLED)
        self.update_button.pack(side=tk.LEFT)
        
        # Progress bar
        self.progress_frame = ttk.Frame(main_frame)
        self.progress_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(self.progress_frame, text="Tiến trình:", style='Info.TLabel').pack(anchor=tk.W)
        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))
        
        # Log area
        log_frame = ttk.LabelFrame(main_frame, text="Nhật Ký Hoạt Động", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=12, wrap=tk.WORD,
                                                 font=('Consolas', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Thêm log khởi tạo
        self.log(f"🚀 Trình cập nhật khởi động - {datetime.now().strftime('%H:%M:%S')}")
    
    def log(self, message):
        """Thêm message vào log"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def get_current_version(self):
        """Đọc phiên bản hiện tại từ file version.bin"""
        try:
            if os.path.exists(VERSION_FILE):
                with open(VERSION_FILE, 'r', encoding='utf-8') as f:
                    version = f.read().strip()
                    return version if version else "1.0.0"
            else:
                self.save_current_version("1.0.0")
                return "1.0.0"
        except Exception as e:
            self.log(f"❌ Lỗi khi đọc version: {e}")
            return "1.0.0"
    
    def save_current_version(self, version):
        """Lưu phiên bản hiện tại vào file version.bin"""
        try:
            with open(VERSION_FILE, 'w', encoding='utf-8') as f:
                f.write(version)
        except Exception as e:
            self.log(f"❌ Lỗi khi lưu version: {e}")
    
    def check_version_on_startup(self):
        """Kiểm tra version khi khởi động"""
        current_version = self.get_current_version()
        self.current_version_label.config(text=current_version)
        self.log(f"📱 Phiên bản hiện tại: {current_version}")
        
        # Tự động kiểm tra update
        threading.Thread(target=self.check_for_update, daemon=True).start()
    
    def check_for_update_thread(self):
        """Chạy kiểm tra update trong thread riêng"""
        threading.Thread(target=self.check_for_update, daemon=True).start()
    
    def check_for_update(self):
        """Kiểm tra có phiên bản mới không"""
        self.log("🔍 Đang kiểm tra phiên bản mới...")
        self.check_button.config(state=tk.DISABLED)
        
        try:
            current_version = self.get_current_version()
            response = requests.get(UPDATE_INFO_URL, timeout=10)
            data = response.json()
            
            latest_version = data.get("latest_version")
            self.download_url = data.get("download_url")
            
            self.latest_version_label.config(text=latest_version)
            
            if latest_version > current_version:
                self.log(f"🔔 Có phiên bản mới: {latest_version}")
                self.status_label.config(text="Có cập nhật mới!", style='Success.TLabel')
                self.update_button.config(state=tk.NORMAL)
                self.latest_version = latest_version
                
                # Hiển thị thông báo
                messagebox.showinfo("Cập Nhật Có Sẵn", 
                                  f"Có phiên bản mới: {latest_version}\n"
                                  f"Phiên bản hiện tại: {current_version}\n\n"
                                  f"Nhấn 'Cập Nhật Ngay' để cài đặt.")
            else:
                self.log("✅ Bạn đang dùng phiên bản mới nhất")
                self.status_label.config(text="Đã cập nhật", style='Success.TLabel')
                self.update_button.config(state=tk.DISABLED)
                
        except Exception as e:
            self.log(f"❌ Lỗi khi kiểm tra phiên bản: {e}")
            self.status_label.config(text="Lỗi kiểm tra", style='Error.TLabel')
            self.latest_version_label.config(text="Không xác định")
        
        finally:
            self.check_button.config(state=tk.NORMAL)
    
    def start_update_thread(self):
        """Bắt đầu quá trình cập nhật trong thread riêng"""
        threading.Thread(target=self.perform_update, daemon=True).start()
    
    def perform_update(self):
        """Thực hiện cập nhật"""
        try:
            self.update_button.config(state=tk.DISABLED)
            self.check_button.config(state=tk.DISABLED)
            
            output_file = f"update_v{self.latest_version}.zip"
            
            # Tải file
            self.log(f"⬇️ Đang tải {output_file}...")
            self.download_with_progress(self.download_url, output_file)
            
            # Giải nén và cài đặt
            self.extract_and_install(output_file, self.latest_version)
            
        except Exception as e:
            self.log(f"❌ Lỗi trong quá trình cập nhật: {e}")
            messagebox.showerror("Lỗi Cập Nhật", f"Có lỗi xảy ra: {e}")
        
        finally:
            self.update_button.config(state=tk.NORMAL)
            self.check_button.config(state=tk.NORMAL)
    
    def download_with_progress(self, url, output_file):
        """Tải file với thanh tiến trình"""
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        total_mb = total_size / (1024 * 1024)
        
        downloaded = 0
        chunk_size = 1024 * 1024  # 1MB
        
        self.progress_bar.config(maximum=100)
        
        with open(output_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    downloaded_mb = downloaded / (1024 * 1024)
                    percent = int((downloaded_mb / total_mb) * 100) if total_mb > 0 else 0
                    
                    self.progress_bar.config(value=percent)
                    self.log_text.delete("end-2l", "end-1l")  # Xóa dòng cuối
                    self.log(f"⬇️ Tải xuống: {downloaded_mb:.1f}/{total_mb:.1f} MB ({percent}%)")
        
        self.log("✅ Tải hoàn tất!")
    
    def extract_and_install(self, zip_file, new_version, extract_to="temp_update"):
        """Giải nén và cài đặt cập nhật"""
        try:
            self.log(f"📦 Đang giải nén {zip_file}...")
            self.progress_bar.config(value=0, maximum=0, mode='indeterminate')
            self.progress_bar.start()
            
            # Tạo thư mục tạm
            if os.path.exists(extract_to):
                shutil.rmtree(extract_to)
            os.makedirs(extract_to)
            
            # Giải nén
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
            
            self.log("✅ Giải nén hoàn tất")
            
            # Copy files
            self.log("📋 Đang cập nhật file...")
            current_dir = os.getcwd()
            
            for root, dirs, files in os.walk(extract_to):
                for file in files:
                    src_file = os.path.join(root, file)
                    rel_path = os.path.relpath(src_file, extract_to)
                    dst_file = os.path.join(current_dir, rel_path)
                    
                    dst_dir = os.path.dirname(dst_file)
                    if dst_dir and not os.path.exists(dst_dir):
                        os.makedirs(dst_dir)
                    
                    shutil.copy2(src_file, dst_file)
                    self.log(f"   → {rel_path}")
            
            # Cập nhật version
            self.save_current_version(new_version)
            self.current_version_label.config(text=new_version)
            
            # Dọn dẹp
            self.log("🧹 Đang dọn dẹp...")
            os.remove(zip_file)
            shutil.rmtree(extract_to)
            
            self.progress_bar.stop()
            self.progress_bar.config(value=100, mode='determinate')
            
            self.log(f"✅ Cập nhật hoàn tất! Phiên bản mới: {new_version}")
            self.status_label.config(text="Đã cập nhật", style='Success.TLabel')
            self.update_button.config(state=tk.DISABLED)
            
            # Thông báo thành công
            result = messagebox.showinfo("Cập Nhật Thành Công", 
                                       f"Cập nhật thành công lên phiên bản {new_version}!\n"
                                       f"Khởi động lại ứng dụng để áp dụng thay đổi.\n\n"
                                       f"Bạn có muốn đóng trình cập nhật không?")
            
        except Exception as e:
            self.progress_bar.stop()
            self.log(f"❌ Lỗi khi cài đặt: {e}")
            # Dọn dẹp khi lỗi
            if os.path.exists(zip_file):
                os.remove(zip_file)
            if os.path.exists(extract_to):
                shutil.rmtree(extract_to)
            raise

def main():
    root = tk.Tk()
    app = UpdaterGUI(root)
    
    # Căn giữa cửa sổ
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    root.mainloop()

if __name__ == "__main__":
    main() 