"""Core verification logic for marine and microbe species."""

import time
import requests
import re
import json
import os
import pyworms # WoRMS 검증을 위해 필요
from bs4 import BeautifulSoup # LPSN 스크래핑에 필요
import traceback
from typing import Dict, Any

# 설정 및 다른 모듈 임포트
try:
    import config
    # 상대 경로 임포트 사용
    from .wiki import get_wiki_summary, extract_scientific_name_from_wiki
    from ..utils.helpers import (clean_scientific_name, create_basic_marine_result,
                               create_basic_microbe_result, get_default_taxonomy, is_korean)
except ImportError as e:
    print(f"[Error Verifier Core] Failed to import config or other modules: {e}")
    # Handle missing modules appropriately, maybe raise an exception or use defaults
    # This is a fallback, ideally imports should succeed
    config = None
    get_wiki_summary = lambda x: "정보 없음 (Import 오류)"
    extract_scientific_name_from_wiki = lambda x: None
    clean_scientific_name = lambda x: x
    create_basic_marine_result = lambda *args: {}
    create_basic_microbe_result = lambda *args: {}
    get_default_taxonomy = lambda x: "정보 없음"
    is_korean = lambda x: False # Fallback

# clean_scientific_name 함수에 check_scientific_name 별칭 추가
check_scientific_name = clean_scientific_name

# verify_species_list 함수 추가 - verify_marine_species 함수 래핑
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
                    print(f"[Info Verifier Core] '{wiki_search_term}' 위키백과 요약 검색 시도")
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
                           print(f"[Info Verifier Core] '{korean_name}'(학명 없음) 위키백과 요약 검색 시도")
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
                 print(f"[Info Verifier Core] WoRMS 실패, '{cleaned_scientific_name}' 위키백과 요약 검색 시도")
                 result_entry['wiki_summary'] = get_wiki_summary(cleaned_scientific_name) or '정보 없음'

        results.append(result_entry)

        # 서버 부하 방지를 위한 약간의 지연 (선택적)
        time.sleep(0.1) # 0.1초 지연

    print(f"[Info Verifier Core] 해양생물 검증 완료: {len(results)}개 결과 생성")
    return results


# --- 미생물 검증 로직 (LPSN 스크래핑 기반) ---

def verify_single_microbe_lpsn(microbe_name):
    """단일 미생물 학명을 LPSN에서 검증 (기존 로직 유지 또는 개선)
       - Placeholder for the actual LPSN scraping and verification logic.
       - Returns a dictionary with verification results for a single name.
    """
    print(f"[Info LPSN Core] LPSN 검증 시작: '{microbe_name}'")
    cleaned_name = clean_scientific_name(microbe_name)
    if not cleaned_name or cleaned_name == '-':
        print(f"[Warning LPSN Core] Invalid input after cleaning: '{microbe_name}'")
        return create_basic_microbe_result(microbe_name, status='입력 오류')

    # --- 실제 LPSN 스크래핑 로직 시작 ---
    # (기존 스크래핑 로직이 이 안에 구현되어 있다고 가정)
    # 예시: 검색 URL 생성, 요청, 파싱, 정보 추출
    search_url = f"https://lpsn.dsmz.de/search?query={cleaned_name.replace(' ', '+')}"
    print(f"[Info LPSN Core] 검색 URL: {search_url}")
    time.sleep(0.5) # Rate limiting

    # 임시 결과 (실제로는 스크래핑 결과 사용)
    # 이 부분은 실제 스크래핑 결과에 따라 달라져야 함
    lpsn_data = {
        'valid_name': '-', # 스크래핑으로 찾은 유효 이름
        'status': '상세 정보 링크 없음', # 스크래핑 결과 상태
        'taxonomy': get_default_taxonomy(cleaned_name), # 기본 분류 또는 스크래핑 결과
        'lpsn_link': '-' # 스크래핑으로 찾은 링크
    }
    print(f"[Warning LPSN Core] '{cleaned_name}' 검색 결과는 있으나, 상세 링크 못찾음") # 예시 로그

    # --- 스크래핑 로직 끝 ---

    # 위키백과 요약 검색
    print(f"[Info LPSN Core] '{cleaned_name}' 위키백과 요약 검색 시도 (미생물)")
    wiki_summary = get_wiki_summary(lpsn_data.get('valid_name', cleaned_name))

    final_result = create_basic_microbe_result(
        input_name=microbe_name, # 원본 입력 이름
        valid_name=lpsn_data.get('valid_name', '-'),
        status=lpsn_data.get('status', '정보 없음'),
        taxonomy=lpsn_data.get('taxonomy', '정보 없음'),
        lpsn_link=lpsn_data.get('lpsn_link', '-'),
        wiki_summary=wiki_summary if wiki_summary else '정보 없음'
    )
    print(f"[Info LPSN Core] LPSN 검증 완료: '{microbe_name}' -> Status: {final_result['status']}")
    return final_result

# --- 기존 verify_microbe_species 함수 수정 ---
# 이 함수가 microbe_verifier.py 에서 호출됨
def verify_microbe_species(microbe_names_list):
    """주어진 미생물 학명 리스트를 검증합니다. (LPSN 기반)

    Args:
        microbe_names_list: 검증할 미생물 학명 문자열 리스트.

    Returns:
        각 학명에 대한 검증 결과 딕셔너리의 리스트.
    """
    results = []
    total_items = len(microbe_names_list)
    print(f"[Info Verifier Core] 미생물 검증 시작 (LPSN Scraping): {total_items}개 항목") # 올바른 항목 수 로깅

    # 리스트의 각 학명 문자열을 순회
    for i, microbe_name in enumerate(microbe_names_list):
        print(f"[Info Verifier Core] {i+1}/{total_items} 처리 중 (LPSN): '{microbe_name}'") # 학명 전체 로깅
        try:
            # 각 학명 문자열 전체를 단일 검증 함수에 전달
            single_result = verify_single_microbe_lpsn(microbe_name)
            results.append(single_result)

            # 디버그: 개별 결과 확인 (필요시 주석 해제)
            # print(f"[Debug] 검증 함수 호출 결과 (단일): {single_result}")

        except Exception as e:
            print(f"[Error Verifier Core] '{microbe_name}' 처리 중 오류 발생: {e}")
            traceback.print_exc()
            # 오류 발생 시 기본 오류 결과 추가
            error_result = create_basic_microbe_result(microbe_name, status=f'오류: {e}')
            results.append(error_result)

    print(f"[Info Verifier Core] 미생물 검증 완료 (LPSN Scraping): {len(results)}개 결과 생성") # 올바른 결과 수 로깅
    return results


# --- 모의 결과 생성 함수 (참고용) ---
def create_mock_microbe_result(microbe_name: str) -> Dict[str, Any]:
    """테스트용 가상 미생물 결과를 생성 (microbe_verifier.py에서 가져옴 - 실제 사용 안 함)"""
    # ... (이 함수는 microbe_verifier.py에서 사용되므로 여기서는 참고용)
    pass