"""Application configuration for LingPy."""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent  # dev/
PROJECT_ROOT = BASE_DIR.parent  # lingo_to_pyomo/
SRC_DIR = PROJECT_ROOT / "src"

DATA_FOLDER = PROJECT_ROOT / "data"
OUTPUT_FOLDER = PROJECT_ROOT / "notebooks"
UPLOAD_FOLDER = BASE_DIR / "uploads"

MAX_UPLOAD_SIZE = 16 * 1024 * 1024  # 16 MB
ALLOWED_LNG_EXTENSIONS = {".lng"}
ALLOWED_EXCEL_EXTENSIONS = {".xlsx", ".xls"}

# Ensure source directory is importable
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Ensure directories exist
for _d in [OUTPUT_FOLDER, UPLOAD_FOLDER]:
    os.makedirs(_d, exist_ok=True)
