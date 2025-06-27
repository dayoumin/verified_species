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
    MAX_DIRECT_INPUT_LIMIT = 10  # 직접 입력으로 처리할 수 있는 최대 항목 수 (20 -> 10으로 감소)
    REALTIME_PROCESSING_THRESHOLD = 10  # 실시간 처리 임계값 (이하는 실시간, 초과는 배치)
    MAX_FILE_PROCESSING_LIMIT = 3000  # 한 번에 처리할 수 있는 최대 항목 수
    BATCH_SIZE = 100  # 배치 처리 크기 - 서버 과부하 방지를 위해 적정 수준 유지
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
    
    # API 요청 지연 시간 및 재시도 설정
    REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", "1.2"))  # 배치 처리용 지연 시간 (1.5 -> 1.2초로 감소, API 방식 최적화)
    REALTIME_REQUEST_DELAY = float(os.getenv("REALTIME_REQUEST_DELAY", "0.6"))  # 실시간 처리 전용 지연 시간 (0.8 -> 0.6초로 감소, API 방식 최적화)
    BATCH_DELAY = float(os.getenv("BATCH_DELAY", "3.0"))  # 배치간 지연 시간 (초) - 파일 처리용 유지
    
    # LPSN 웹 스크래핑 전용 지연 시간 (더 안전하게)
    LPSN_REQUEST_DELAY = float(os.getenv("LPSN_REQUEST_DELAY", "1.8"))  # 웹 스크래핑용 지연 시간 (더 안전하게)
    
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
    "truststore_enabled": True,  # 기업/공공기관 네트워크 지원
    "description": "truststore를 사용하여 OS 신뢰 저장소 기반 SSL 검증 수행"
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