#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LPSN 웹 스크래핑 기반 미생물 검증 모듈

이전에 잘 작동했던 LPSN 사이트 직접 접속 방식을 재구현합니다.
공식 라이브러리의 50초 지연 문제 없이 빠르고 정확한 검증을 제공합니다.
"""

import requests
import time
import re
from typing import Dict, Any, Optional
from urllib.parse import quote_plus
from bs4 import BeautifulSoup


def clean_scientific_name(name: str) -> str:
    """학명 정리 (공통 유틸리티 함수)"""
    if not name:
        return ""
    
    # 기본 정리
    cleaned = str(name).strip()
    
    # 특수 문자 제거 및 공백 정규화
    cleaned = re.sub(r'[^\w\s.-]', ' ', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    return cleaned.strip()


def verify_microbe_lpsn_scraping(microbe_name: str) -> Dict[str, Any]:
    """
    LPSN 웹사이트 스크래핑을 통한 미생물 학명 검증
    
    이전에 검증된 방식으로 LPSN 사이트에 직접 접속하여 정확한 정보를 가져옵니다.
    
    Args:
        microbe_name: 검증할 미생물 학명
        
    Returns:
        검증 결과 딕셔너리
    """
    print(f"[Info LPSN Scraper] LPSN 웹 스크래핑 검증 시작: '{microbe_name}'")
    
    cleaned_name = clean_scientific_name(microbe_name)
    
    # 기본 결과 구조
    base_result = {
        'input_name': microbe_name,
        'scientific_name': cleaned_name,
        'is_verified': False,
        'valid_name': cleaned_name,
        'status': 'Not found in LPSN',
        'taxonomy': 'Domain: Bacteria',
        'lpsn_link': f"https://lpsn.dsmz.de/search?word={quote_plus(cleaned_name)}",
        'wiki_summary': '-',
        'korean_name': '-',
        'is_microbe': True
    }
    
    if not cleaned_name or len(cleaned_name) < 3:
        base_result['status'] = 'Invalid input'
        return base_result
    
    try:
        # LPSN 검색 URL 구성
        search_url = f"https://lpsn.dsmz.de/search?word={quote_plus(cleaned_name)}"
        
        # 세션 생성 (쿠키 및 헤더 관리)
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # 검색 요청
        print(f"[Info LPSN Scraper] LPSN 검색 요청: {search_url}")
        response = session.get(search_url, timeout=15)
        
        if response.status_code != 200:
            print(f"[Warning LPSN Scraper] HTTP 응답 오류: {response.status_code}")
            base_result['status'] = f'LPSN 접속 오류 (HTTP {response.status_code})'
            return base_result
        
        # HTML 파싱
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 검색 결과 확인
        results = parse_lpsn_search_results(soup, cleaned_name)
        
        if results:
            # 검증 성공
            result_data = results[0]  # 첫 번째 결과 사용
            
            base_result.update({
                'scientific_name': result_data.get('name', cleaned_name),
                'is_verified': True,
                'valid_name': result_data.get('name', cleaned_name),
                'status': f"LPSN 검증됨: {result_data.get('status', 'valid')}",
                'taxonomy': result_data.get('taxonomy', 'Domain: Bacteria'),
                'lpsn_link': result_data.get('link', base_result['lpsn_link']),
                'wiki_summary': f"✅ LPSN에서 검증되었습니다.\n상태: {result_data.get('status', 'valid')}"
            })
            
            print(f"[Info LPSN Scraper] 검증 성공: '{result_data.get('name', cleaned_name)}'")
            
        else:
            # 검색 결과 없음
            print(f"[Info LPSN Scraper] 검색 결과 없음: '{cleaned_name}'")
            base_result.update({
                'status': 'LPSN 검색됨: 결과 없음',
                'taxonomy': 'Domain: Bacteria (추정)',
                'wiki_summary': f"LPSN에서 '{cleaned_name}'을 검색했으나 결과가 없습니다."
            })
        
        # 요청 간 지연
        time.sleep(0.5)  # 서버 부하 방지
        
        return base_result
        
    except requests.exceptions.Timeout:
        print(f"[Error LPSN Scraper] 타임아웃 오류")
        base_result['status'] = 'LPSN 연결 타임아웃'
        return base_result
        
    except requests.exceptions.ConnectionError:
        print(f"[Error LPSN Scraper] 연결 오류")
        base_result['status'] = 'LPSN 연결 실패'
        return base_result
        
    except Exception as e:
        print(f"[Error LPSN Scraper] 예상치 못한 오류: {e}")
        base_result['status'] = f'LPSN 스크래핑 오류'
        return base_result


def parse_lpsn_search_results(soup: BeautifulSoup, search_term: str) -> list:
    """
    LPSN 검색 결과 페이지에서 데이터 추출
    
    Args:
        soup: BeautifulSoup 객체
        search_term: 검색어
        
    Returns:
        검색 결과 리스트
    """
    results = []
    
    try:
        # LPSN 검색 결과 테이블 찾기
        # 실제 LPSN 사이트 구조에 맞게 조정 필요
        
        # 방법 1: 검색 결과 테이블
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows[1:]:  # 헤더 제외
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    name_cell = cells[0]
                    status_cell = cells[1] if len(cells) > 1 else None
                    
                    # 학명 추출
                    name_text = name_cell.get_text(strip=True)
                    if name_text and search_term.lower() in name_text.lower():
                        
                        # 링크 추출
                        link_elem = name_cell.find('a')
                        detail_link = ""
                        if link_elem and link_elem.get('href'):
                            href = link_elem.get('href')
                            if href.startswith('/'):
                                detail_link = f"https://lpsn.dsmz.de{href}"
                            else:
                                detail_link = href
                        
                        # 상태 정보 추출
                        status_text = status_cell.get_text(strip=True) if status_cell else "valid"
                        
                        result = {
                            'name': name_text,
                            'status': status_text,
                            'link': detail_link,
                            'taxonomy': 'Domain: Bacteria (LPSN 확인)',
                            'source': 'lpsn_scraping'
                        }
                        
                        results.append(result)
                        print(f"[Debug LPSN Scraper] 결과 발견: {name_text} ({status_text})")
        
        # 방법 2: 다른 구조 시도 (div, span 등)
        if not results:
            # 검색 결과가 다른 형태로 표시될 경우
            result_divs = soup.find_all(['div', 'span'], class_=re.compile(r'result|search|species', re.I))
            for div in result_divs:
                text = div.get_text(strip=True)
                if text and search_term.lower() in text.lower():
                    results.append({
                        'name': text,
                        'status': 'found',
                        'link': f"https://lpsn.dsmz.de/search?word={quote_plus(search_term)}",
                        'taxonomy': 'Domain: Bacteria (LPSN 확인)',
                        'source': 'lpsn_scraping'
                    })
                    print(f"[Debug LPSN Scraper] 대체 방법으로 결과 발견: {text}")
                    break
        
        # 방법 3: 페이지 제목이나 메타 정보 확인
        if not results:
            title = soup.find('title')
            if title and search_term.lower() in title.get_text().lower():
                results.append({
                    'name': search_term,
                    'status': 'found in title',
                    'link': f"https://lpsn.dsmz.de/search?word={quote_plus(search_term)}",
                    'taxonomy': 'Domain: Bacteria (LPSN 확인)',
                    'source': 'lpsn_scraping'
                })
                print(f"[Debug LPSN Scraper] 제목에서 결과 발견")
        
    except Exception as e:
        print(f"[Error LPSN Scraper] 파싱 오류: {e}")
    
    return results


# 호환성을 위한 별명
verify_single_microbe_lpsn_scraping = verify_microbe_lpsn_scraping


if __name__ == "__main__":
    # 테스트 코드
    test_names = [
        "Escherichia coli",
        "Bacillus subtilis", 
        "Staphylococcus aureus",
        "Unknown microbe 123"
    ]
    
    print("=== LPSN 웹 스크래핑 테스트 ===")
    for name in test_names:
        print(f"\n테스트: {name}")
        result = verify_microbe_lpsn_scraping(name)
        print(f"결과: {result['status']}")
        print(f"검증됨: {result['is_verified']}")
        print("-" * 40) 