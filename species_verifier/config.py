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
    
    # 파일 처리 관련 - API 차단 위험 방지를 위해 대폭 감소
    MAX_DIRECT_INPUT_LIMIT = 10  # 직접 입력으로 처리할 수 있는 최대 항목 수 (20 -> 10으로 감소)
    REALTIME_PROCESSING_THRESHOLD = 10  # 실시간 처리 임계값 (이하는 실시간, 초과는 배치)
    MAX_FILE_PROCESSING_LIMIT = 500  # 한 번에 처리할 수 있는 최대 항목 수 (3000 -> 500으로 대폭 감소, API 차단 위험 방지)
    BATCH_SIZE = 50  # 배치 처리 크기 - API 부하 방지를 위해 감소 (100 -> 50)
    MAX_RESULTS_DISPLAY = 100  # 한 번에 표시할 수 있는 최대 결과 수
    
    # 대량 처리 경고 임계값 추가 (API 차단 위험 방지)
    LARGE_FILE_WARNING_THRESHOLD = 100  # 100개 이상 시 경고 표시
    CRITICAL_FILE_WARNING_THRESHOLD = 300  # 300개 이상 시 강력 경고 표시
    
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
    
    # API 요청 지연 시간 및 재시도 설정 - API 차단 위험 방지를 위해 대폭 증가
    REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", "2.0"))  # 배치 처리용 지연 시간 (1.2 -> 2.0초로 증가, API 차단 위험 방지)
    REALTIME_REQUEST_DELAY = float(os.getenv("REALTIME_REQUEST_DELAY", "1.0"))  # 실시간 처리 전용 지연 시간 (0.6 -> 1.0초로 증가)
    BATCH_DELAY = float(os.getenv("BATCH_DELAY", "5.0"))  # 배치간 지연 시간 (3.0 -> 5.0초로 증가, API 부하 방지)
    
    # LPSN API 전용 지연 시간 (계정 차단 위험이 가장 높음)
    LPSN_REQUEST_DELAY = float(os.getenv("LPSN_REQUEST_DELAY", "3.0"))  # LPSN API 지연 시간 (1.8 -> 3.0초로 대폭 증가, 계정 차단 위험 방지)
    
    # 대량 처리 시 추가 보호 지연 시간
    LARGE_BATCH_EXTRA_DELAY = float(os.getenv("LARGE_BATCH_EXTRA_DELAY", "2.0"))  # 100개 이상 시 추가 지연
    
    # 네트워크 안정성 설정 (외부망 환경을 위해 강화)
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "20"))  # HTTP 요청 타임아웃 (초) - 30 -> 20으로 감소 (빠른 실패)
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))  # 최대 재시도 횟수 - 5 -> 3으로 감소
    RETRY_DELAY = float(os.getenv("RETRY_DELAY", "1.5"))  # 재시도 간격 (초) - 3.0 -> 1.5으로 감소
    
    # COL API 설정
    COL_API_URL = "https://api.catalogueoflife.org"
    COL_REQUEST_TIMEOUT = int(os.getenv("COL_REQUEST_TIMEOUT", "20"))  # COL API 타임아웃 (초) - 30 -> 20으로 감소
    
    # User-Agent 설정 (일반적인 브라우저로 위장)
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

# SSL/TLS 설정 정보
SSL_CONFIG = {
    "allow_insecure_fallback": True,  # 기업 환경 지원 (False로 설정하면 SSL 우회 비활성화)
    "log_ssl_bypass": True,  # SSL 우회 사용 시 로깅
    "prefer_secure": True,   # 항상 SSL 검증을 먼저 시도
    "bypass_warning": True   # SSL 우회 시 사용자 알림 표시
}

# 기본 설정 인스턴스 생성
app_config = AppConfig()
api_config = APIConfig()
ui_config = UIConfig()

# 기관 네트워크 환경을 위한 추가 설정 (정상적인 학술 연구용 설정)
ENTERPRISE_CONFIG = {
    # 네트워크 연결 최적화 설정
    "bypass_proxy": False,  # 시스템 프록시 설정 사용 (보안 정책 준수)
    
    # 표준 브라우저 User-Agent (학술 연구용 정상 접속)
    "standard_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    
    # 다중 User-Agent 백업 (네트워크 접근성 향상)
    "fallback_user_agents": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ],
    
    # 연결 안정성 설정 (학술 API 접속 최적화)
    "connection_pool_settings": {
        "pool_connections": 3,  # 적정 수준의 연결 풀 크기
        "pool_maxsize": 5,      # 최대 연결 수 (과도하지 않게)
        "pool_block": True      # 연결 풀이 가득 찰 때 대기 (안정성 우선)
    },
    
    # 재시도 전략 (네트워크 불안정 대응)
    "enhanced_retry": {
        "backoff_factor": 2.0,  # 표준 지수 백오프
        "status_forcelist": [429, 500, 502, 503, 504],  # 일반적인 재시도 상태 코드
        "allowed_methods": ["GET", "POST"]  # 표준 HTTP 메서드만
    }
} 