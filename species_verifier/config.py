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
    MAX_FILE_PROCESSING_LIMIT = 3000  # 한 번에 처리할 수 있는 최대 항목 수
    BATCH_SIZE = 100  # 배치 처리 크기 (500 -> 100으로 수정)
    MAX_RESULTS_DISPLAY = 100  # 한 번에 표시할 수 있는 최대 결과 수
    DIRECT_EXPORT_THRESHOLD = 100  # 이 수치보다 많은 결과는 바로 파일로 내보내기
    
    # 로깅 설정
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "species_verifier.log")
    
    # 데이터 경로 (더 이상 사용하지 않음 - 국명 검색 중단)
    # DATA_DIR = Path(__file__).parent / "data"
    # KOREAN_MAPPINGS_FILE = DATA_DIR / "korean_mappings.json"

class APIConfig:
    """외부 API 연결 설정"""
    # WoRMS API 설정
    WORMS_API_URL = os.getenv("WORMS_API_URL", "https://www.marinespecies.org/rest")
    WORMS_REQUEST_DELAY = float(os.getenv("WORMS_REQUEST_DELAY", "1.0"))  # 연속 요청 시 딜레이 (초)
    
    # LPSN 관련 설정 
    LPSN_BASE_URL = "https://lpsn.dsmz.de/species"
    
    # 위키백과 API 설정
    WIKIPEDIA_API_URL = "https://ko.wikipedia.org/w/api.php"
    WIKIPEDIA_REQUEST_TIMEOUT = int(os.getenv("WIKIPEDIA_REQUEST_TIMEOUT", "15"))  # 초 (10 -> 15로 증가)
    
    # Gemini API 설정 (있는 경우)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_ENABLED = bool(GEMINI_API_KEY)
    
    # API 요청 지연 시간 및 재시도 설정 (외부망 환경 최적화)
    REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", "2.0"))  # 각 API 호출 사이의 지연 시간 (초) - 1.0 -> 2.0으로 증가
    BATCH_DELAY = float(os.getenv("BATCH_DELAY", "5.0"))  # 배치간 지연 시간 (초) - 3.0 -> 5.0으로 증가
    
    # 네트워크 안정성 설정 (외부망 환경을 위해 강화)
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))  # HTTP 요청 타임아웃 (초) - 15 -> 30으로 증가
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "5"))  # 최대 재시도 횟수 - 3 -> 5로 증가
    RETRY_DELAY = float(os.getenv("RETRY_DELAY", "3.0"))  # 재시도 간격 (초) - 2.0 -> 3.0으로 증가
    
    # COL API 설정
    COL_API_URL = "https://api.catalogueoflife.org"
    COL_REQUEST_TIMEOUT = int(os.getenv("COL_REQUEST_TIMEOUT", "30"))  # COL API 타임아웃 (초) - 20 -> 30으로 증가
    
    # User-Agent 설정 (외부망에서 차단 방지)
    USER_AGENT = os.getenv("USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # HTTP 헤더 설정
    DEFAULT_HEADERS = {
        'User-Agent': USER_AGENT,
        'Accept': 'application/json, text/html, */*',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    # 연결 안정성 설정 (보안 정책 준수)
    CONNECTION_POOL_SIZE = int(os.getenv("CONNECTION_POOL_SIZE", "10"))
    CONNECTION_POOL_MAXSIZE = int(os.getenv("CONNECTION_POOL_MAXSIZE", "20"))

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