import os
import shutil
from datetime import datetime

def test_simple_structure():
    """Test cấu trúc thư mục đơn giản"""
    
    # Xóa thư mục test cũ nếu có
    if os.path.exists("Video"):
        shutil.rmtree("Video")
    
    class MockWorker:
        def __init__(self, custom_name=""):
            self.custom_folder_name = custom_name
        
        def _create_download_folder(self):
            base_folder = "Video"
            os.makedirs(base_folder, exist_ok=True)
            
            if self.custom_folder_name:
                if os.path.isabs(self.custom_folder_name):
                    date_folder = self.custom_folder_name
                else:
                    date_folder = os.path.join(base_folder, self.custom_folder_name)
            else:
                date_str = datetime.now().strftime("%Y-%m-%d")
                date_folder = os.path.join(base_folder, date_str)
            
            download_folder = self._create_numbered_subfolder(date_folder)
            
            os.makedirs(download_folder, exist_ok=True)
            return download_folder
        
        def _create_numbered_subfolder(self, date_folder):
            if not os.path.exists(date_folder):
                os.makedirs(date_folder, exist_ok=True)
            
            max_number = 0
            for item in os.listdir(date_folder):
                item_path = os.path.join(date_folder, item)
                if os.path.isdir(item_path) and item.isdigit():
                    max_number = max(max_number, int(item))
            
            next_number = max_number + 1
            subfolder_name = f"{next_number:02d}"
            download_folder = os.path.join(date_folder, subfolder_name)
            
            return download_folder
    
    print("=== TEST CẤU TRÚC ĐƠN GIẢN ===")
    
    # Test 1: Lần đầu tiên
    print("\n1. Test lần đầu tiên:")
    worker1 = MockWorker()
    folder1 = worker1._create_download_folder()
    print(f"   Thư mục tạo: {folder1}")
    
    # Test 2: Lần thứ 2 (cùng ngày)
    print("\n2. Test lần thứ 2 (cùng ngày):")
    worker2 = MockWorker()
    folder2 = worker2._create_download_folder()
    print(f"   Thư mục tạo: {folder2}")
    
    # Test 3: Lần thứ 3 (cùng ngày)
    print("\n3. Test lần thứ 3 (cùng ngày):")
    worker3 = MockWorker()
    folder3 = worker3._create_download_folder()
    print(f"   Thư mục tạo: {folder3}")
    
    # Test 4: Với custom folder
    print("\n4. Test với custom folder:")
    worker4 = MockWorker("MyVideos")
    folder4 = worker4._create_download_folder()
    print(f"   Thư mục tạo: {folder4}")
    
    # Test 5: Thêm vào custom folder
    print("\n5. Test thêm vào custom folder:")
    worker5 = MockWorker("MyVideos")
    folder5 = worker5._create_download_folder()
    print(f"   Thư mục tạo: {folder5}")
    
    print("\n=== CẤU TRÚC THỦ MỤC ===")
    for root, dirs, files in os.walk("Video"):
        level = root.replace("Video", "").count(os.sep)
        indent = " " * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = " " * 2 * (level + 1)
        for d in sorted(dirs):
            print(f"{subindent}{d}/")
    
    print("\n✅ Cấu trúc mong muốn:")
    print("Video/")
    print("  2025-08-02/")
    print("    01/")
    print("    02/")
    print("    03/")
    print("  MyVideos/")
    print("    01/")
    print("    02/")

if __name__ == "__main__":
    test_simple_structure() 