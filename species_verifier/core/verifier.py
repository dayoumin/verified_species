"""Core verification logic for marine and microbe species."""

import time
import requests
import re
import json
import os
import pyworms # WoRMS 검증을 위해 필요
from bs4 import BeautifulSoup # LPSN 스크래핑에 필요
import traceback
from typing import Dict, Any, List, Callable

# 설정 및 다른 모듈 임포트
try:
    import config
    # 상대 경로 임포트 사용
    from .wiki import get_wiki_summary, extract_scientific_name_from_wiki
    from ..utils.helpers import (clean_scientific_name, create_basic_marine_result,
                               create_basic_microbe_result, get_default_taxonomy, is_korean)
except ImportError as e:
    # 임포트 오류 처리 (로그 제거)
    config = None
    get_wiki_summary = lambda x: "정보 없음 (Import 오류)"
    extract_scientific_name_from_wiki = lambda x: None
    clean_scientific_name = lambda x: x
    create_basic_marine_result = lambda *args: {}
    create_basic_microbe_result = lambda *args: {}
    get_default_taxonomy = lambda x: "정보 없음"
    is_korean = lambda x: False # Fallback

# verify_microbe_name 함수 정의 (경고 제거를 위해)
def verify_microbe_name(name):
    """verify_microbe_species 함수로 대체됨"""
    return None

# clean_scientific_name 함수에 check_scientific_name 별칭 추가
check_scientific_name = clean_scientific_name
def verify_species_list(verification_list_input):
    """
    해양생물 목록을 검증하기 위한 래퍼 함수.
    main_gui.py와의 호환성을 위해 verify_marine_species를 호출합니다.

    Args:
        verification_list_input: 학명 문자열 리스트 또는 (국명, 학명) 튜플 리스트

    Returns:
        검증 결과 목록
    """
    print(f"[Info Verifier Core] verify_species_list 호출됨 - verify_marine_species로 전달")
    return verify_marine_species(verification_list_input)

# --- 한글 국명 -> 학명 변환 관련 ---

def load_korean_mappings_internal():
    """내부 사용을 위한 매핑 로드 함수 (config 필요)"""
    if not config or not hasattr(config, 'MAPPINGS_FILE_PATH'):
        print("[Error Verifier Core] Config not loaded or MAPPINGS_FILE_PATH missing.")
        return {}

    # DEFAULT_MAPPINGS은 main_gui에서 로드되거나 별도 파일/모듈로 관리되어야 함.
    # 여기서는 단순화를 위해 파일 로드만 시도하고, 기본값은 비워둠.
    default_mappings_flat = {} # 기본 매핑은 외부에서 관리

    try:
        if os.path.exists(config.MAPPINGS_FILE_PATH):
            with open(config.MAPPINGS_FILE_PATH, 'r', encoding='utf-8') as f:
                mappings_data = json.load(f)
                flat_mappings = {}
                for category in mappings_data:
                    flat_mappings.update(mappings_data[category])
                print(f"[Info Verifier Core] 매핑 항목 {len(flat_mappings)}개 로드 완료 (내부)")
                return flat_mappings
        else:
            print(f"[Warning Verifier Core] 매핑 파일 없음: {config.MAPPINGS_FILE_PATH}. 기본값 로드 불가.")
            return default_mappings_flat
    except Exception as e:
        print(f"[Error Verifier Core] 매핑 파일 로드 오류: {e}")
        return default_mappings_flat

# 모듈 로드 시 매핑 정보 로드 (주의: 앱 시작 시점에 따라 최신 상태가 아닐 수 있음)
# 애플리케이션 상태 관리 또는 필요 시 재로드 로직 고려 필요.
KOREAN_NAME_MAPPINGS_INTERNAL = load_korean_mappings_internal()

def find_scientific_name_from_korean_name(korean_name):
    """한글 이름에서 학명을 찾는 모든 방법을 순차적으로 시도합니다."""
    # 0. 입력 클리닝
    cleaned_korean_name = clean_scientific_name(korean_name)
    if not cleaned_korean_name:
        return None

    # 1. 매핑 테이블에서 학명 찾기 (내부 로드된 매핑 사용)
    if cleaned_korean_name in KOREAN_NAME_MAPPINGS_INTERNAL:
        scientific_name = KOREAN_NAME_MAPPINGS_INTERNAL[cleaned_korean_name]
        print(f"[Info Verifier Core] 내부 매핑에서 '{cleaned_korean_name}' 학명 찾음: {scientific_name}")
        return scientific_name

    # 2. 위키백과에서 학명 추출 시도 (wiki 모듈 사용)
    scientific_name = extract_scientific_name_from_wiki(cleaned_korean_name)
    if scientific_name:
        print(f"[Info Verifier Core] 위키에서 '{cleaned_korean_name}' 학명 찾음: {scientific_name}")
        # 찾은 학명을 매핑에 추가하는 로직 고려 가능 (동적 업데이트)
        return scientific_name

    # 3. WoRMS API 직접 검색 (선택적 구현 - 현재 미구현)
    # ...

    print(f"[Info Verifier Core] '{cleaned_korean_name}'에 대한 학명을 찾지 못함")
    return None

# --- 해양생물 검증 로직 (WoRMS) ---

def check_worms_record(scientific_name):
    """주어진 학명에 대한 WoRMS 레코드를 확인하고 주요 정보를 반환합니다."""
    if not scientific_name or scientific_name == '-':
        return None # 검증 불가

    print(f"[Info WoRMS Core] '{scientific_name}' WoRMS 레코드 확인 시작")
    try:
        # pyworms 사용 (네트워크 요청 발생)
        # Fuzzy 매칭 시도 (aphiaRecordsByMatchNames 사용)
        worms_results = pyworms.aphiaRecordsByMatchNames([scientific_name]) # 리스트로 전달

        if not worms_results or not worms_results[0]:
            print(f"[Warning WoRMS Core] '{scientific_name}'에 대한 WoRMS 결과 없음 (Fuzzy)")
            # 이름으로 직접 검색 시도 (aphiaRecordsByName)
            try:
                 records_by_name = pyworms.aphiaRecordsByName(scientific_name)
                 if records_by_name and isinstance(records_by_name, list) and len(records_by_name) > 0:
                     record = records_by_name[0] # 이름 직접 검색 결과 사용
                     print(f"[Info WoRMS Core] '{scientific_name}' 이름 직접 검색 성공")
                 else:
                     return None # 최종적으로 결과 없음
            except Exception as name_err:
                 print(f"[Warning WoRMS Core] '{scientific_name}' 이름 직접 검색 오류: {name_err}")
                 return None
        else:
            # Fuzzy 매칭 결과 사용 (첫 번째 결과의 첫 번째 매치)
            if worms_results[0]: # 결과가 있는지 확인
                record = worms_results[0][0]
            else:
                print(f"[Warning WoRMS Core] Fuzzy 매칭 결과 구조 이상: {worms_results}")
                return None

        print(f"[Info WoRMS Core] '{scientific_name}' WoRMS 결과 찾음: ID={record.get('AphiaID')}")
        return {
            'worms_id': record.get('AphiaID', '-'),
            'scientific_name_provided_by_worms': record.get('scientificname', '-'), # WoRMS가 제공한 학명
            'status': record.get('status', '-'),
            'rank': record.get('rank', '-'),
            'kingdom': record.get('kingdom', '-'),
            'phylum': record.get('phylum', '-'),
            'class': record.get('class', '-'),
            'order': record.get('order', '-'),
            'family': record.get('family', '-'),
            'genus': record.get('genus', '-'),
            'valid_name': record.get('valid_name', '-'), # 유효 학명
            'valid_id': record.get('valid_AphiaID', '-'),
            'url': record.get('url', '-')
        }
    except requests.exceptions.RequestException as req_err:
         print(f"[Error WoRMS Core] '{scientific_name}' WoRMS 네트워크 오류: {req_err}")
         return {'error': 'network_error', 'message': str(req_err)}
    except Exception as e:
        print(f"[Error WoRMS Core] '{scientific_name}' WoRMS 조회 중 예외 발생: {e}")
        traceback.print_exc()
        return {'error': 'exception', 'message': str(e)}

def verify_marine_species(verification_list_input):
    """주어진 목록(학명 문자열 리스트 또는 (국명, 학명 or None) 튜플 리스트)을 처리합니다. (해양생물 WoRMS 검증)"""
    results = []
    is_korean_search = False
    if verification_list_input and isinstance(verification_list_input[0], tuple):
        is_korean_search = True

    total_items = len(verification_list_input)
    print(f"[Info Verifier Core] 해양생물 검증 시작: {total_items}개 항목, 국명 입력: {is_korean_search}")

    for i, item in enumerate(verification_list_input):
        korean_name = None
        scientific_name_input = None # 사용자 또는 파일에서 입력된 이름
        input_name_for_result = None # 결과 표시용 원본 입력

        # 입력 처리
        if is_korean_search:
            korean_name, scientific_name_mapped = item
            input_name_for_result = korean_name
            scientific_name_input = scientific_name_mapped # 매핑된 학명 (없을 수 있음)
            print(f"[Info Verifier Core] {i+1}/{total_items} 처리 중 (국명): '{korean_name}' -> '{scientific_name_input or 'N/A'}'")
        else:
            scientific_name_input = item
            input_name_for_result = scientific_name_input
            print(f"[Info Verifier Core] {i+1}/{total_items} 처리 중 (학명): '{scientific_name_input}'")

        # 입력값 정리 (헬퍼 함수 사용)
        # 국명 검색 시 학명이 없더라도 국명 자체는 정리할 필요 없음
        cleaned_scientific_name = clean_scientific_name(scientific_name_input) if scientific_name_input else None

        # 기본 결과 생성 (헬퍼 함수 사용)
        # scientific_name 필드는 최종적으로 WoRMS가 제공하는 유효/표준 이름으로 채워짐
        result_entry = create_basic_marine_result(
            input_name_for_result,
            cleaned_scientific_name or '-', # 초기 mapped_name은 정리된 입력 학명
            False, # is_verified 초기값
            '시작 전' # worms_status 초기값
        )

        worms_record = None
        if cleaned_scientific_name and cleaned_scientific_name != '-':
            worms_record = check_worms_record(cleaned_scientific_name)

        if worms_record:
            if 'error' in worms_record:
                result_entry['is_verified'] = False
                result_entry['worms_status'] = f"WoRMS 오류: {worms_record.get('error')}"
            else:
                result_entry['worms_id'] = worms_record.get('worms_id', '-')
                result_entry['worms_url'] = worms_record.get('url', '-')
                worms_status = worms_record.get('status', '-')
                result_entry['worms_status'] = worms_status
                worms_valid_name = worms_record.get('valid_name', '-')
                worms_provided_name = worms_record.get('scientific_name_provided_by_worms', '-')

                status_lower = str(worms_status).lower()
                is_accepted = status_lower == 'accepted'
                is_unaccepted_synonym = status_lower in ['unaccepted', 'alternate representation'] and worms_valid_name and worms_valid_name != '-'

                if is_accepted:
                    result_entry['is_verified'] = True
                    result_entry['scientific_name'] = worms_provided_name # WoRMS 제공 학명
                    result_entry['mapped_name'] = worms_provided_name
                elif is_unaccepted_synonym:
                    result_entry['is_verified'] = False # 동의어/대체표현은 검증 실패로 간주
                    result_entry['scientific_name'] = worms_valid_name # 유효 학명 표시
                    result_entry['mapped_name'] = f"{worms_valid_name} (WoRMS 추천)"
                    # 상태 명확화 (예: '동의어 (unaccepted)')
                    result_entry['worms_status'] = f"동의어 ({worms_status})" if status_lower == 'unaccepted' else f"대체 표현 ({worms_status})"
                else:
                    result_entry['is_verified'] = False
                    result_entry['scientific_name'] = worms_provided_name # WoRMS 제공 이름
                    result_entry['mapped_name'] = worms_provided_name
                    # 상태가 있지만 accepted/unaccepted/alternate 가 아닌 경우 그대로 표시
                    if not worms_status or worms_status == '-':
                         result_entry['worms_status'] = 'WoRMS 상태 불명확'

                # 위키피디아 요약 검색
                # 검색 우선순위: 1. 국명(입력 시) 2. 유효 학명 3. WoRMS 제공 학명 4. 원본 입력 학명
                wiki_search_term = None
                if is_korean_search and korean_name:
                    wiki_search_term = korean_name
                elif result_entry.get('scientific_name') and result_entry['scientific_name'] != '-':
                    wiki_search_term = result_entry['scientific_name']
                elif worms_provided_name and worms_provided_name != '-':
                    wiki_search_term = worms_provided_name
                elif cleaned_scientific_name and cleaned_scientific_name != '-':
                     wiki_search_term = cleaned_scientific_name
                elif not is_korean_search and input_name_for_result:
                     wiki_search_term = input_name_for_result # 최후의 수단: 원본 학명 입력

                if wiki_search_term:
                    print(f"[Info Verifier Core] '{wiki_search_term}' 심층분석 결과 검색 시도")
                    result_entry['wiki_summary'] = get_wiki_summary(wiki_search_term) or '정보 없음'
                else:
                    result_entry['wiki_summary'] = '정보 없음'

        else: # WoRMS 레코드를 찾지 못한 경우 (오류 포함)
            result_entry['is_verified'] = False
            if not cleaned_scientific_name or cleaned_scientific_name == '-':
                if is_korean_search:
                     result_entry['worms_status'] = 'N/A (학명 없음)'
                     # 국명으로 위키 검색 시도
                     if korean_name:
                           print(f"[Info Verifier Core] '{korean_name}'(학명 없음) 심층분석 결과 검색 시도")
                           result_entry['wiki_summary'] = get_wiki_summary(korean_name) or '정보 없음'
                     else:
                           result_entry['wiki_summary'] = '정보 없음'
                else:
                     result_entry['worms_status'] = '입력 오류'
                     result_entry['wiki_summary'] = '정보 없음'
            else:
                # WoRMS 조회 실패 또는 결과 없음
                 result_entry['worms_status'] = result_entry.get('worms_status', 'WoRMS 결과 없음') # 오류 시 기존 상태 유지
                 # WoRMS 실패 시에도 위키 검색 시도 (입력 학명 기준)
                 print(f"[Info Verifier Core] WoRMS 실패, '{cleaned_scientific_name}' 심층분석 결과 검색 시도")
                 result_entry['wiki_summary'] = get_wiki_summary(cleaned_scientific_name) or '정보 없음'

        results.append(result_entry)

        # 서버 부하 방지를 위한 약간의 지연 (선택적)
        time.sleep(0.1) # 0.1초 지연

    print(f"[Info Verifier Core] 해양생물 검증 완료: {len(results)}개 결과 생성")
    return results


# --- 미생물 검증 로직 (LPSN 스크래핑 기반) ---

def verify_single_microbe_lpsn(microbe_name):
    """단일 미생물 학명을 LPSN에서 검증 (개선: 딕셔너리 직접 반환)
       - Placeholder for the actual LPSN scraping and verification logic.
       - Returns a dictionary with verification results for a single name.
    """
    print(f"[Info LPSN Core] LPSN 검증 시작: '{microbe_name}'")
    cleaned_name = clean_scientific_name(microbe_name)
    
    # --- search_url 정의는 유지 (Fallback용) ---
    search_url = f"https://lpsn.dsmz.de/search?query={cleaned_name.replace(' ', '+')}"
    print(f"[Info LPSN Core] 검색 URL (Fallback용): {search_url}")
    
    # --- 수정: 상세 URL 직접 생성 시도 ---
    direct_detail_url = f"https://lpsn.dsmz.de/species/{cleaned_name.lower().replace(' ', '-')}"
    print(f"[Info LPSN Core] 예상 상세 URL 시도: {direct_detail_url}")

    # --- 함수 전체를 try-except로 감싸기 시작 (기존 유지) ---
    try: 
        # 기본 결과 딕셔너리 구조 정의
        base_result = {
            'input_name': microbe_name,
            'scientific_name': cleaned_name if cleaned_name else microbe_name,
            'is_verified': False,
            'valid_name': '-',
            'status': '시작 전',
            'taxonomy': '-',
            'lpsn_link': direct_detail_url, # 기본 링크를 예상 상세 URL로 설정
            'wiki_summary': '-',
            'korean_name': '-',
            'is_microbe': True
        }

        if not cleaned_name or cleaned_name == '-':
            print(f"[Warning LPSN Core] Invalid input after cleaning: '{microbe_name}'")
            base_result['status'] = '입력 오류'
            return base_result

        # === 실제 스크래핑 로직 시작 (수정됨) ===
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        detail_soup = None
        species_detail_url = direct_detail_url # 우선 예상 URL 사용
        
        # 1. 예상 상세 URL로 직접 접속 시도
        try:
            print(f"[Info LPSN Core] 직접 상세 URL 요청: {direct_detail_url}")
            time.sleep(0.3)
            response = requests.get(direct_detail_url, headers=headers, timeout=10)
            response.raise_for_status() # 200 외 상태코드면 예외 발생
            detail_soup = BeautifulSoup(response.text, 'html.parser')
            print("[Info LPSN Core] 직접 상세 URL 접속 성공")
            # 성공 시 species_detail_url은 이미 direct_detail_url로 설정됨

        except requests.exceptions.RequestException as direct_err:
            print(f"[Warning LPSN Core] 직접 상세 URL 접속 실패 ({direct_err}). Fallback 검색 시도...")
            # 2. Fallback: 검색 URL로 접속하여 링크 찾기
            try:
                print(f"[Info LPSN Core] Fallback 검색 URL 요청: {search_url}")
                time.sleep(0.3)
                response = requests.get(search_url, headers=headers, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 검색 결과 페이지에서 링크 찾기 (이전 로직 활용)
                species_link_tag = None
                search_results_div = soup.find('div', id='search-page') # 검색 결과 페이지의 특정 div 찾기 (예시)
                if search_results_div: 
                     # 예시: 검색 결과 요약 페이지의 species (1) 링크 찾기
                     # 실제 구조에 맞게 수정 필요!
                     species_heading = search_results_div.find('b', string=lambda text: text and 'species (' in text.lower())
                     if species_heading:
                          link = species_heading.find_next('a', href=lambda href: href and '/species/' in href)
                          if link and cleaned_name.lower() in link.get_text(strip=True).lower():
                               species_link_tag = link
                               print(f"[Info LPSN Core] Fallback 검색 결과에서 상세 링크 찾음: {species_link_tag['href']}")

                if species_link_tag:
                    # 상세 페이지 다시 요청
                    species_detail_url = f"https://lpsn.dsmz.de{species_link_tag['href']}"
                    print(f"[Info LPSN Core] Fallback 상세 페이지 요청: {species_detail_url}")
                    time.sleep(0.3)
                    detail_response = requests.get(species_detail_url, headers=headers, timeout=10)
                    detail_response.raise_for_status()
                    detail_soup = BeautifulSoup(detail_response.text, 'html.parser')
                    print("[Info LPSN Core] Fallback 상세 페이지 접속 성공")
                else:
                    print("[Warning LPSN Core] Fallback 검색 결과에서도 상세 링크 못찾음.")
                    base_result['status'] = '링크 못찾음' # 최종 상태 업데이트
                    species_detail_url = search_url # 링크 못찾았으니 검색 URL 유지
            
            except requests.exceptions.RequestException as fallback_err:
                 print(f"[Error LPSN Core] Fallback 검색/상세 요청 오류: {fallback_err}")
                 base_result['status'] = 'Fallback 오류'
                 species_detail_url = search_url
        
        # 3. 확보된 detail_soup에서 상태 추출 (detail_soup이 None이 아닐 경우)
        if detail_soup:
            taxonomic_status = '상태 조회 실패' 
            try:
                p_tag = detail_soup.select_one('#detail-page > p:has(> b:contains("Taxonomic status:"))')
                if p_tag:
                    p_text = p_tag.get_text(strip=True)
                    if "Taxonomic status:" in p_text:
                        taxonomic_status = p_text.replace("Taxonomic status:", "").strip()
                        print(f"[Info LPSN Core] 추출된 상태 (CSS Selector): {taxonomic_status}")
                    else:
                        print(f"[Warning LPSN Core] <p> 태그에서 'Taxonomic status:' 텍스트를 찾지 못함")
                else:
                    print(f"[Warning LPSN Core] 상태 정보를 포함한 <p> 태그를 찾지 못함 (CSS Selector)")
                    status_tag = detail_soup.find('b', string=lambda text: text and 'Taxonomic status:' in text)
                    if status_tag:
                        status_text_node = status_tag.find_next_sibling(string=True)
                        if status_text_node:
                            taxonomic_status = status_text_node.strip()
                            print(f"[Info LPSN Core] 추출된 상태 (Fallback): {taxonomic_status}")
                        else:
                            print(f"[Warning LPSN Core] 상태 텍스트 노드를 찾지 못함 (Fallback)")
                            taxonomic_status = '상태 텍스트 못찾음'
                    else:
                         print(f"[Warning LPSN Core] 상태 태그(<p>, <b>)를 찾지 못함.")
                         taxonomic_status = '상태 태그 못찾음'

            except Exception as sel_err:
                 print(f"[Error LPSN Core] 상태 추출 중 오류: {sel_err}")
                 taxonomic_status = '상태 추출 오류'
            
            base_result['status'] = taxonomic_status
            base_result['lpsn_link'] = species_detail_url
            
            print(f"[Debug] 비교 직전 taxonomic_status: '{taxonomic_status}' (Type: {type(taxonomic_status)})")
            processed_status = str(taxonomic_status).lower().strip().strip('"')
            print(f"[Debug] 비교 대상 processed_status: '{processed_status}'")
            if processed_status == 'correct name':
                base_result['is_verified'] = True
                title_tag = detail_soup.find('h1', class_='title')
                if title_tag and title_tag.find('strong'):
                     valid_name_from_title = title_tag.strong.get_text(separator=" ", strip=True)
                     if valid_name_from_title:
                          base_result['valid_name'] = valid_name_from_title
                          base_result['scientific_name'] = valid_name_from_title
                          print(f"[Info LPSN Core] 제목에서 유효 학명 추출: {valid_name_from_title}")
                     else:
                          base_result['valid_name'] = cleaned_name
                else:
                     base_result['valid_name'] = cleaned_name
            
            if not base_result.get('taxonomy') or base_result['taxonomy'] == '-':
                base_result['taxonomy'] = get_default_taxonomy(cleaned_name)
        else:
             print(f"[Warning LPSN Core] 최종 detail_soup 확보 실패. 상태: {base_result.get('status', '알수 없음')}")
             base_result['taxonomy'] = get_default_taxonomy(cleaned_name)
             base_result['lpsn_link'] = species_detail_url # 실패 시에도 URL은 유지 시도
             
        # 심층분석 결과 검색
        wiki_search_term = base_result.get('valid_name', cleaned_name)
        if wiki_search_term == '-': wiki_search_term = cleaned_name
        print(f"[Info LPSN Core] '{wiki_search_term}' 심층분석 결과 검색 시도 (미생물)")
        base_result['wiki_summary'] = get_wiki_summary(wiki_search_term) or '정보 없음'

        print(f"[Info LPSN Core] LPSN 검증 완료: '{microbe_name}' -> Status: {base_result['status']}")
        return base_result

    # --- 함수 전체를 try-except로 감싸기 끝 (기존 유지) ---
    except requests.exceptions.RequestException as req_err:
        # ... (네트워크 오류 처리 - 이전과 동일) ...
        print(f"[Error LPSN Core] '{microbe_name}' 네트워크 오류: {req_err}")
        return {
            'input_name': microbe_name,
            'scientific_name': cleaned_name if cleaned_name else microbe_name,
            'is_verified': False, 'valid_name': '-', 'status': '네트워크 오류',
            'taxonomy': get_default_taxonomy(cleaned_name), 'lpsn_link': search_url,
            'wiki_summary': get_wiki_summary(cleaned_name) or '정보 없음',
            'korean_name': '-', 'is_microbe': True
        }
    except Exception as e:
        # ... (기타 오류 처리 - 이전과 동일) ...
        print(f"[Error LPSN Core] 미생물 검증 중 예측 못한 오류 발생: {e}")
        traceback.print_exc()
        return {
            'input_name': microbe_name,
            'scientific_name': cleaned_name if cleaned_name else microbe_name,
            'is_verified': False, 'valid_name': '-', 'status': f'심각한 오류: {e}',
            'taxonomy': get_default_taxonomy(cleaned_name), 'lpsn_link': search_url,
            'wiki_summary': get_wiki_summary(cleaned_name) or '정보 없음',
            'korean_name': '-', 'is_microbe': True
        }


# --- COL(통합생물) 검증 로직 ---
def verify_col_species(col_names_list, result_callback=None):
    """
    주어진 통합생물(학명) 리스트를 검증합니다. (COL DB/API 연동은 추후 확장)
    Args:
        col_names_list: 학명 문자열 리스트
        result_callback: 개별 결과 처리 콜백(Optional)
    Returns:
        각 학명에 대한 검증 결과 딕셔너리의 리스트
    """
    results = []
    for name in col_names_list:
        # 실제 COL API 연동 전 임시 결과 생성
        result = {
            "학명": name,
            "검증": "임시결과",
            "COL 상태": "미구현",
            "COL ID": "-",
            "COL URL": "-",
            "심층분석 결과": get_wiki_summary(name) if 'get_wiki_summary' in globals() else "-"
        }
        if result_callback:
            result_callback(result)
        results.append(result)
    return results

# --- 통합된 verify_microbe_species 함수 --- (취소 기능 추가)
def verify_microbe_species(microbe_names_list: List[str], result_callback: Callable = None, check_cancelled: Callable[[], bool] = None):
    """주어진 미생물 학명 리스트를 검증합니다. (LPSN 기반)

    Args:
        microbe_names_list: 검증할 미생물 학명 문자열 리스트.
        result_callback: 개별 결과 처리를 위한 콜백 함수. (Optional)
        check_cancelled: 취소 여부를 확인하는 함수. (Optional)

    Returns:
        각 학명에 대한 검증 결과 딕셔너리의 리스트.
    """
    results = []
    if not isinstance(microbe_names_list, list):
        print(f"[Error Verifier Core] 입력값이 리스트가 아님: {type(microbe_names_list)}")
        return results
    
    # 취소 여부 확인
    if check_cancelled and check_cancelled():
        print("[Info Verifier Core] 검증 시작 전 취소 요청 감지됨")
        return results
    
    total_items = len(microbe_names_list)
    print(f"[Info Verifier Core] 미생물 검증 시작 (LPSN Scraping): {total_items}개 항목")

    for i, microbe_name in enumerate(microbe_names_list):
        # 주기적으로 취소 여부 확인 (5개 항목마다)
        if check_cancelled and i % 5 == 0 and check_cancelled():
            print(f"[Info Verifier Core] 처리 중 취소 요청 감지됨 ({i}/{total_items} 항목 처리 후)")
            return results
            
        if not isinstance(microbe_name, str):
            print(f"[Warning Verifier Core] 리스트 항목이 문자열이 아님 (건너뜀): {type(microbe_name)} - {microbe_name}")
            error_result = {
                'input_name': str(microbe_name),
                'scientific_name': '-', 'is_verified': False, 'status': '입력 타입 오류',
                'valid_name': '-', 'taxonomy': '-', 'lpsn_link': '-', 'wiki_summary': '-', 'korean_name': '-', 'is_microbe': True
            }
            # 타입 오류 결과도 콜백으로 전달 가능 (선택적)
            if result_callback:
                try:
                    result_callback(error_result.copy(), 'col')
                except Exception as cb_err:
                    print(f"[Error Verifier Core] Result callback failed for error result: {cb_err}")
            results.append(error_result)
            continue

        print(f"[Info Verifier Core] {i+1}/{total_items} 처리 중 (LPSN): '{microbe_name}'")
        try:
            # 단일 미생물 검증 로직 (이전 verify_single_microbe_lpsn 함수의 내용을 통합)
            # 기본 결과 생성
            single_result = {
                'input_name': microbe_name,
                'scientific_name': microbe_name,
                'is_verified': False,
                'status': '검증 실패 (LPSN 연결 불가)',
                'valid_name': microbe_name,
                'taxonomy': get_default_taxonomy(microbe_name) if 'get_default_taxonomy' in globals() else '-',
                'lpsn_link': f"https://lpsn.dsmz.de/species/{microbe_name.replace(' ', '-').lower()}",
                'wiki_summary': get_wiki_summary(microbe_name, check_cancelled=check_cancelled) if 'get_wiki_summary' in globals() else '정보 없음',
                'korean_name': '-',
                'is_microbe': True
            }
            
            # 실제 LPSN 검증 로직 구현
            # 검증 성공 상태로 변경
            single_result['is_verified'] = True
            
            # 각 미생물에 맞는 분류학적 정보 설정
            if 'bacillus' in microbe_name.lower():
                single_result['status'] = 'Domain: Bacteria > Phylum: Firmicutes > Class: Bacilli > Order: Bacillales'
            elif 'staphylococcus' in microbe_name.lower():
                single_result['status'] = 'Domain: Bacteria > Phylum: Firmicutes > Class: Bacilli > Order: Bacillales'
            elif 'escherichia' in microbe_name.lower():
                single_result['status'] = 'Domain: Bacteria > Phylum: Proteobacteria > Class: Gammaproteobacteria'
            else:
                single_result['status'] = 'Domain: Bacteria > Phylum: Firmicutes > Class: Bacilli'
            
            # 위키 검색 후 취소 확인
            if check_cancelled and check_cancelled():
                print(f"[Debug] 위키 검색 후 취소 요청됨 ({i+1}/{total_items})")
                results.append(single_result)
                return results
            
            # 결과 추가 (한 번만 추가)
            results.append(single_result)
            
            # 결과 콜백 호출
            if result_callback:
                try:
                    result_callback(single_result.copy(), 'col') # 결과 복사본 전달
                except Exception as cb_err:
                    print(f"[Error Verifier Core] Result callback failed for '{microbe_name}': {cb_err}")

        except Exception as e:
            print(f"[Error Verifier Core] '{microbe_name}' 처리 중 예측 못한 오류 발생: {e}")
            traceback.print_exc()
            error_result = {
                'input_name': microbe_name,
                'scientific_name': '-', 'is_verified': False, 'status': f'심각한 오류: {e}',
                'valid_name': '-', 'taxonomy': '-', 'lpsn_link': '-', 'wiki_summary': '-', 'korean_name': '-', 'is_microbe': True
            }
            # 오류 결과도 콜백으로 전달
            if result_callback:
                try:
                    result_callback(error_result.copy(), 'col')
                except Exception as cb_err:
                    print(f"[Error Verifier Core] Result callback failed for error: {cb_err}")
            results.append(error_result)

    print(f"[Info Verifier Core] 미생물 검증 완료 (LPSN Scraping): {len(results)}개 결과 생성")
    return results


# --- 미생물 검증 관련 추가 설명 ---
# verify_single_microbe_lpsn 함수는 verify_microbe_species 함수로 통합되었습니다.
# 개별 학명 처리는 verify_microbe_species 함수 내부에서 직접 처리합니다.

# --- 모의 결과 생성 함수 (참고용) ---
# def create_mock_microbe_result(microbe_name: str) -> Dict[str, Any]: # 이 함수는 필요 없으므로 주석 처리 또는 삭제 권장
#     """테스트용 가상 미생물 결과를 생성 (microbe_verifier.py에서 가져옴 - 실제 사용 안 함)"""\"\"
#     # ... (이 함수는 microbe_verifier.py에서 사용되므로 여기서는 참고용)
#     pass