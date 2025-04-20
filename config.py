# config.py

"""
애플리케이션의 비민감 설정 값들을 저장하는 파일입니다.
API 엔드포인트, 기본 경로, UI 관련 설정 등을 관리합니다.
"""
import os

# --- API Endpoints ---
WORMS_API_BASE_URL = "https://www.marinespecies.org/rest" # From main_gui.py
# LPSN_API_ENDPOINT = "https://lpsn.dsmz.de/" # Keep commented or verify actual endpoint if used
WIKIPEDIA_API_ENDPOINT = "https://en.wikipedia.org/w/api.php" # Keep or verify if used directly

# --- File Paths ---
# Assuming config.py is at the root or a known location relative to data
# If config.py is in the root:
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# DATA_DIR = os.path.join(BASE_DIR, 'species_verifier', 'data')
# If config.py is elsewhere, adjust accordingly. Let's assume it's in the root for now.
# A simpler approach if the structure is consistent:
DATA_DIR = os.path.join(os.path.dirname(__file__), 'species_verifier', 'data') # Relative path might be fragile, consider absolute
MAPPINGS_FILENAME = "korean_scientific_mappings.json"
MAPPINGS_FILE_PATH = os.path.join(DATA_DIR, MAPPINGS_FILENAME)

# --- UI & Processing Limits ---
MAX_RESULTS_DISPLAY = 100 # From main_gui.py
MAX_FILE_PROCESSING_LIMIT = 3000 # From main_gui.py
DIRECT_EXPORT_THRESHOLD = 500 # From main_gui.py

# --- Other Configurations ---
# Consider moving license/expiry related constants here if appropriate
# EXPIRY_DAYS = 547
# CONTACT_EMAIL = "ecomarin@naver.com"
# DATE_FILE_NAME = ".verifier_expiry_date"

# Default directories (keep or adjust as needed)
DEFAULT_INPUT_DIR = "./input"
DEFAULT_OUTPUT_DIR = "./output"

# 여기에 더 많은 설정을 추가할 수 있습니다. 