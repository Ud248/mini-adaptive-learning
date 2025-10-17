import os
import sys
from pathlib import Path

# Thêm project root vào sys.path để import được các module
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Thêm thư mục backend/saint_analysis để import được package 'app'
SAINT_ANALYSIS_DIR = Path(__file__).parent
sys.path.insert(0, str(SAINT_ANALYSIS_DIR))

from app.api.saint_api import app