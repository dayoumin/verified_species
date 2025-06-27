"""
Species Verifier 로깅 시스템

실행파일에서 네트워크 문제 진단을 위한 상세 로그를 생성합니다.
"""
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

def setup_logger():
    """실행파일용 로거 설정"""
    # 실행파일의 경우 임시 디렉토리 또는 실행파일과 같은 위치에 로그 저장
    if getattr(sys, 'frozen', False):
        # PyInstaller로 패키징된 실행파일인 경우
        log_dir = Path(sys.executable).parent
    else:
        # 개발 환경인 경우
        log_dir = Path(__file__).parent.parent.parent
    
    # 로그 파일명에 타임스탬프 포함
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"species_verifier_{timestamp}.log"
    
    # 로거 설정
    logger = logging.getLogger('species_verifier')
    logger.setLevel(logging.DEBUG)
    
    # 기존 핸들러 제거 (중복 방지)
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 파일 핸들러 설정
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    
    # 콘솔 핸들러 설정 (실행파일에서는 보이지 않지만 개발시 유용)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 로그 포맷 설정
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 핸들러 추가
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # 로그 파일 위치 출력
    print(f"로그 파일: {log_file}")
    logger.info(f"Species Verifier 시작 - v0.5")
    logger.debug(f"로그 파일: {log_file}")
    logger.debug(f"Python: {sys.version.split()[0]}")
    logger.debug(f"환경: {'실행파일' if getattr(sys, 'frozen', False) else '개발환경'}")
    
    return logger



def log_system_info(logger):
    """시스템 정보 로그"""
    import platform
    import socket
    
    logger.debug("=== 시스템 정보 ===")
    logger.debug(f"OS: {platform.system()} {platform.release()}")
    logger.debug(f"아키텍처: {platform.architecture()[0]}")
    logger.debug(f"머신: {platform.machine()}")
    
    # 네트워크 정보
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        logger.debug(f"호스트: {hostname}")
        logger.debug(f"IP: {local_ip}")
    except Exception as e:
        logger.debug(f"네트워크 정보 조회 실패: {e}")
    
    # 환경 변수 (프록시 관련)
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
    logger.debug("=== 네트워크 설정 ===")
    for var in proxy_vars:
        value = os.environ.get(var)
        if value:
            logger.debug(f"{var}: {value}")
        else:
            logger.debug(f"{var}: 없음")

def log_dns_resolution(logger, domain):
    """DNS 해상도 테스트 로그"""
    import socket
    try:
        ip = socket.gethostbyname(domain)
        logger.info(f"DNS 해상도 성공: {domain} -> {ip}")
        return ip
    except Exception as e:
        logger.error(f"DNS 해상도 실패: {domain} -> {str(e)}")
        return None

# 전역 로거 인스턴스
_logger = None

def get_logger():
    """전역 로거 인스턴스 반환"""
    global _logger
    if _logger is None:
        _logger = setup_logger()
        log_system_info(_logger)
    return _logger 