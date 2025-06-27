"""
Species Verifier 로깅 시스템

콘솔 출력만 제공하는 간단한 로깅 시스템입니다.
"""
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

def setup_logger():
    """간단한 콘솔 로거 설정"""
    # 로거 설정
    logger = logging.getLogger('species_verifier')
    logger.setLevel(logging.INFO)
    
    # 기존 핸들러 제거 (중복 방지)
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 콘솔 핸들러만 설정 (파일 핸들러 제거)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 간단한 로그 포맷 설정
    formatter = logging.Formatter('%(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    
    # 핸들러 추가
    logger.addHandler(console_handler)
    
    return logger

def log_system_info(logger):
    """시스템 정보 로그 - 비활성화"""
    pass

def log_dns_resolution(logger, domain):
    """DNS 해상도 테스트 로그 - 비활성화"""
    import socket
    try:
        ip = socket.gethostbyname(domain)
        return ip
    except Exception as e:
        return None

# 전역 로거 인스턴스
_logger = None

def get_logger():
    """전역 로거 인스턴스 반환"""
    global _logger
    if _logger is None:
        _logger = setup_logger()
    return _logger 