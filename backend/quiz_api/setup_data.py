#!/usr/bin/env python3
"""
Script để copy dữ liệu từ collection_export.json vào thư mục backend
"""
import shutil
import os
import sys

def setup_data():
    """Copy file collection_export.json vào thư mục backend"""
    try:
        # Đường dẫn file gốc
        source_file = "../collection_export.json"
        
        # Đường dẫn file đích
        dest_file = "collection_export.json"
        
        # Kiểm tra file gốc có tồn tại không
        if not os.path.exists(source_file):
            print(f"❌ Không tìm thấy file: {source_file}")
            print("Vui lòng chạy data_collection.py trước để tạo file dữ liệu")
            return False
        
        # Copy file
        shutil.copy2(source_file, dest_file)
        print(f"✅ Đã copy {source_file} → {dest_file}")
        
        # Kiểm tra file đích
        if os.path.exists(dest_file):
            file_size = os.path.getsize(dest_file)
            print(f"📊 Kích thước file: {file_size:,} bytes")
            return True
        else:
            print("❌ Lỗi khi copy file")
            return False
            
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Thiết lập dữ liệu cho Quiz API...")
    success = setup_data()
    
    if success:
        print("🎉 Thiết lập thành công!")
        print("Bây giờ bạn có thể chạy: python main.py")
    else:
        print("💥 Thiết lập thất bại!")
        sys.exit(1)
