"""
애플리케이션 설정 관리 모듈

이 모듈은 Species Verifier 애플리케이션의 모든 설정 값을 중앙 집중식으로 관리합니다.
환경 변수, 상수, 기본 설정 등을 포함합니다.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 환경 변수 로드
dotenv_path = Path(__file__).parent.parent / '.env'
if dotenv_path.exists():
    load_dotenv(dotenv_path)

class AppConfig:
    """애플리케이션 전반 설정"""
    # 앱 정보
    APP_NAME = "Species Verifier"
    APP_VERSION = "1.0.0"
    
    # 파일 처리 관련
    MAX_DIRECT_INPUT_LIMIT = 20  # 직접 입력으로 처리할 수 있는 최대 항목 수
    MAX_FILE_PROCESSING_LIMIT = 1000  # 한 번에 처리할 수 있는 최대 항목 수 (500에서 1000으로 수정)
    MAX_RESULTS_DISPLAY = 100  # 한 번에 표시할 수 있는 최대 결과 수
    DIRECT_EXPORT_THRESHOLD = 100  # 이 수치보다 많은 결과는 바로 파일로 내보내기
    
    # 로깅 설정
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "species_verifier.log")
    
    # 데이터 경로
    DATA_DIR = Path(__file__).parent / "data"
    KOREAN_MAPPINGS_FILE = DATA_DIR / "korean_mappings.json"

class APIConfig:
    """외부 API 연결 설정"""
    # WoRMS API 설정
    WORMS_API_URL = os.getenv("WORMS_API_URL", "https://www.marinespecies.org/rest")
    WORMS_REQUEST_DELAY = 1.0  # 연속 요청 시 딜레이 (초)
    
    # LPSN 관련 설정 
    LPSN_BASE_URL = "https://lpsn.dsmz.de/species"
    
    # 위키백과 API 설정
    WIKIPEDIA_API_URL = "https://ko.wikipedia.org/w/api.php"
    WIKIPEDIA_REQUEST_TIMEOUT = 5  # 초
    
    # Gemini API 설정 (있는 경우)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_ENABLED = bool(GEMINI_API_KEY)

class UIConfig:
    """사용자 인터페이스 관련 설정"""
    # 창 크기
    WINDOW_WIDTH = 1200
    WINDOW_HEIGHT = 800
    
    # 테마 설정
    THEME = "dark"  # "dark" 또는 "light"
    PRIMARY_COLOR = "#1E88E5"  # 파란색 계열
    
    # 결과 표시 설정
    MAX_WIKI_SUMMARY_LENGTH = 500  # 위키 요약 최대 표시 길이

# 기본 설정 인스턴스 생성
app_config = AppConfig()
api_config = APIConfig()
ui_config = UIConfig() 