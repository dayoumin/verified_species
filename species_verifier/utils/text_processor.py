"""
텍스트 전처리 유틸리티 모듈

이 모듈은 학명, 국명 등의 텍스트 처리와 정제를 위한 유틸리티 함수들을 제공합니다.
"""
import re
from typing import Optional

def clean_scientific_name(input_name: str) -> str:
    """학명 문자열을 정리하고 표준 형식으로 변환
    
    Args:
        input_name: 정리할 학명 문자열
        
    Returns:
        정리된 학명 문자열
    """
    if not input_name:
        return ""
        
    # 앞뒤 공백 제거
    cleaned = input_name.strip()
    
    # 학명 형식 정리
    # 1. 불필요한 공백 제거 (두 개 이상의 공백을 하나로)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    # 2. 괄호 안의 저자 정보 제거 (예: Gadus morhua Linnaeus, 1758 -> Gadus morhua)
    cleaned = re.sub(r'\s+\([^)]+\)', '', cleaned)
    
    # 3. 저자 및 연도 정보 제거 (예: Gadus morhua Linnaeus, 1758 -> Gadus morhua)
    cleaned = re.sub(r'\s+[A-Z][a-zA-Z]+,?\s+\d{4}', '', cleaned)
    cleaned = re.sub(r'\s+[A-Z][a-zA-Z]+,?\s+\&\s+[A-Z][a-zA-Z]+,?\s+\d{4}', '', cleaned)
    
    # 4. 학명 철자 규칙 적용 (속명은 대문자로 시작, 종명은 소문자)
    parts = cleaned.split()
    if len(parts) >= 2:
        # 속명 첫 글자 대문자화
        parts[0] = parts[0].capitalize()
        # 종명 모두 소문자화 (실제 학명 규칙 준수)
        parts[1] = parts[1].lower()
        cleaned = ' '.join(parts)
    
    return cleaned

def is_korean(char: str) -> bool:
    """주어진 문자가 한글인지 확인
    
    Args:
        char: 확인할 문자
        
    Returns:
        한글 여부 (True/False)
    """
    return '\uAC00' <= char <= '\uD7A3' or '\u1100' <= char <= '\u11FF' or '\u3130' <= char <= '\u318F'

def has_korean(text: str) -> bool:
    """문자열에 한글이 포함되어 있는지 확인
    
    Args:
        text: 확인할 문자열
        
    Returns:
        한글 포함 여부 (True/False)
    """
    if not text:
        return False
    return any(is_korean(char) for char in text)

def extract_first_two_words(scientific_name: str) -> Optional[str]:
    """학명에서 속명과 종명만 추출 (이명법)
    
    Args:
        scientific_name: 학명 문자열
        
    Returns:
        속명과 종명만 포함된 학명 또는 None
    """
    if not scientific_name:
        return None
        
    words = scientific_name.strip().split()
    if len(words) >= 2:
        return f"{words[0]} {words[1]}"
    elif len(words) == 1:
        return words[0]  # 속명만 있는 경우
    else:
        return None

def get_display_name(input_name: str, scientific_name: str, korean_name: Optional[str] = None) -> str:
    """표시용 이름 생성 (UI 표시 목적)
    
    Args:
        input_name: 원본 입력 이름
        scientific_name: 학명
        korean_name: 한글명 (선택적)
        
    Returns:
        표시용 이름
    """
    # 한글명이 제공된 경우
    if korean_name:
        return f"{korean_name} ({scientific_name})"
    
    # 입력명이 학명과 동일한 경우
    if input_name == scientific_name:
        return scientific_name
    
    # 입력명이 한글이고 학명이 있는 경우
    if has_korean(input_name) and scientific_name:
        return f"{input_name} ({scientific_name})"
    
    # 그 외 케이스
    return input_name or scientific_name or "Unknown" 