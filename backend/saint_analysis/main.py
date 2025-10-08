import os
import sys

# Đảm bảo có thể import module 'app' khi chạy từ project root
CURRENT_DIR = os.path.dirname(__file__)
if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)

from app.api.saint_api import app