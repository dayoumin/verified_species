"""Core verification logic for marine and microbe species."""

import time
import requests
import re
import json
import os
from bs4 import BeautifulSoup # LPSN 스크래핑에 필요
import traceback
from typing import Dict, Any, List, Callable, Optional
from species_verifier.config import api_config # api_config 임포트 추가

# 설정 및 다른 모듈 임포트
try:
    import config
    # 상대 경로 임포트 사용
    from .wiki import get_wiki_summary, extract_scientific_name_from_wiki
    from ..utils.helpers import (clean_scientific_name, create_basic_marine_result,
                               create_basic_microbe_result, get_default_taxonomy, is_korean)
    from species_verifier.config import app_config, api_config
    from species_verifier.core.worms_api import verify_species_list
except ImportError as e:
    # 임포트 오류 처리 (로그 제거)
    config = None
    get_wiki_summary = lambda x, check_cancelled=None: "정보 없음 (Import 오류)"
    extract_scientific_name_from_wiki = lambda x: None
    clean_scientific_name = lambda x: x
    create_basic_marine_result = lambda *args: {}
    create_basic_microbe_result = lambda *args: {}
    get_default_taxonomy = lambda x: "정보 없음"
    is_korean = lambda x: False # Fallback
    verify_species_list = None
    app_config = None
    api_config = None

# SSL 경고 관리 (보안 강화)
try:
    from species_verifier.config import SSL_CONFIG
    if SSL_CONFIG.get("allow_insecure_fallback", False):
        # 기업 환경 지원이 활성화된 경우에만 경고 비활성화
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except ImportError:
    # 설정 파일이 없는 경우 기본 동작
    pass

# 사용되지 않는 함수 제거됨

# clean_scientific_name 함수에 check_scientific_name 별칭 추가
check_scientific_name = clean_scientific_name

# 중복 래퍼 함수 제거 - worms_api.py의 verify_species_list를 직접 사용하도록 변경
# def verify_species_list(verification_list_input):
#     """
#     해양생물 목록을 검증하기 위한 래퍼 함수.
#     main_gui.py와의 호환성을 위해 verify_marine_species를 호출합니다.
#     """
#     print(f"[Info Verifier Core] verify_species_list 호출됨 - verify_marine_species로 전달")
#     return verify_marine_species(verification_list_input)

# --- 한글 국명 -> 학명 변환 관련 ---

# --- 해양생물 검증 로직 (WoRMS) ---

# check_worms_record 함수 제거됨 - worms_api.py의 verify_species_list 사용으로 대체

def check_worms_record(scientific_name):
    """
    호환성을 위한 래퍼 함수: worms_api.verify_single_species를 호출하고 
    기존 check_worms_record와 호환되는 형식으로 결과를 변환합니다.
    """
    from .worms_api import verify_single_species
    
    result = verify_single_species(scientific_name)
    
    if 'error' in result:
        return {'error': result['error']}
    
    # 기존 check_worms_record 형식으로 변환
        return {
        'worms_id': result.get('worms_id', '-'),
        'scientific_name': result.get('scientific_name', scientific_name),
        'status': 'valid' if result.get('is_verified', False) else 'not_found',
        'url': result.get('worms_link', '-'),
        'worms_status': result.get('worms_status', '-')
    }

def verify_marine_species(verification_list_input):
    """주어진 목록(학명 문자열 리스트 또는 (국명, 학명 or None) 튜플 리스트)을 처리합니다. (해양생물 WoRMS 검증)"""
    results = []
    is_korean_search = False
    if verification_list_input and isinstance(verification_list_input[0], tuple):
        is_korean_search = True

    total_items = len(verification_list_input)
    print(f"[Info Verifier Core] 해양생물 검증 시작: {total_items}개 항목, 국명 입력: {is_korean_search}")

    # worms_api 임포트 및 확인
    from .worms_api import verify_species_list as worms_verify_species_list
    
    # 학명 리스트 준비
    scientific_names_for_worms = []
    name_mapping = {}  # 원본 입력 -> 정리된 학명 매핑

    for i, item in enumerate(verification_list_input):
        korean_name = None
        scientific_name_input = None
        input_name_for_result = None

        # 입력 처리
        if is_korean_search:
            korean_name, scientific_name_mapped = item
            input_name_for_result = korean_name
            scientific_name_input = scientific_name_mapped
            print(f"[Info Verifier Core] {i+1}/{total_items} 준비 중 (국명): '{korean_name}' -> '{scientific_name_input or 'N/A'}'")
        else:
            scientific_name_input = item
            input_name_for_result = scientific_name_input
            print(f"[Info Verifier Core] {i+1}/{total_items} 준비 중 (학명): '{scientific_name_input}'")

        # 입력값 정리
        cleaned_scientific_name = clean_scientific_name(scientific_name_input) if scientific_name_input else None

        # 매핑 정보 저장
        name_mapping[i] = {
            'input_name_for_result': input_name_for_result,
            'scientific_name_input': scientific_name_input,
            'cleaned_scientific_name': cleaned_scientific_name,
            'korean_name': korean_name
        }
        
        # WoRMS 검증할 학명 리스트에 추가
        if cleaned_scientific_name and cleaned_scientific_name != '-':
            scientific_names_for_worms.append(cleaned_scientific_name)
        else:
            scientific_names_for_worms.append(None)  # 빈 자리 유지

    # WoRMS 일괄 검증 (중복 제거)
    print(f"[Info Verifier Core] WoRMS 일괄 검증 시작: {len([n for n in scientific_names_for_worms if n])}개 유효 학명")
    valid_names = [n for n in scientific_names_for_worms if n]
    if valid_names:
        worms_results = worms_verify_species_list(valid_names)
        # 결과를 학명별로 매핑
        worms_dict = {result.get('input_name', ''): result for result in worms_results}
    else:
        worms_dict = {}

    # 개별 결과 생성
    for i, item in enumerate(verification_list_input):
        mapping_info = name_mapping[i]
        input_name_for_result = mapping_info['input_name_for_result']
        cleaned_scientific_name = mapping_info['cleaned_scientific_name']
        korean_name = mapping_info['korean_name']

        # 기본 결과 생성
        result_entry = create_basic_marine_result(
            input_name_for_result,
            cleaned_scientific_name or '-',
            False,
            '시작 전'
        )

        # WoRMS 결과 적용
        worms_record = None
        if cleaned_scientific_name and cleaned_scientific_name in worms_dict:
            worms_record = worms_dict[cleaned_scientific_name]

        if worms_record:
            # worms_api.py의 결과 구조에 맞게 수정
            if 'error' in worms_record:
                result_entry['is_verified'] = False
                result_entry['worms_status'] = f"WoRMS 오류: {worms_record.get('error')}"
            else:
                # worms_api.py 결과 구조에 맞게 필드 매핑
                result_entry['worms_id'] = worms_record.get('worms_id', '-')
                result_entry['worms_url'] = worms_record.get('worms_link', '-')
                worms_status = worms_record.get('worms_status', '-')
                result_entry['worms_status'] = worms_status
                
                # worms_api.py는 is_verified로 검증 상태를 제공
                if worms_record.get('is_verified', False):
                    result_entry['is_verified'] = True
                    result_entry['scientific_name'] = worms_record.get('scientific_name', cleaned_scientific_name)
                    result_entry['mapped_name'] = worms_record.get('scientific_name', cleaned_scientific_name)
                else:
                    result_entry['is_verified'] = False
                    result_entry['scientific_name'] = worms_record.get('scientific_name', cleaned_scientific_name)
                    if worms_record.get('similar_name') and worms_record['similar_name'] != '-':
                        result_entry['mapped_name'] = f"{worms_record['similar_name']} (WoRMS 추천)"
                    else:
                        result_entry['mapped_name'] = worms_record.get('scientific_name', cleaned_scientific_name)

                # 위키피디아 요약 검색
                wiki_search_term = None
                if is_korean_search and korean_name:
                    wiki_search_term = korean_name
                elif result_entry.get('scientific_name') and result_entry['scientific_name'] != '-':
                    wiki_search_term = result_entry['scientific_name']
                elif cleaned_scientific_name and cleaned_scientific_name != '-':
                     wiki_search_term = cleaned_scientific_name

                # 심층분석 결과는 현재 준비 중으로 설정
                if wiki_search_term:
                    print(f"[Info Verifier Core] '{wiki_search_term}' 심층분석 결과: 준비 중")
                    result_entry['wiki_summary'] = '준비 중 (DeepSearch 기능 개발 예정)'
                else:
                    result_entry['wiki_summary'] = '준비 중 (DeepSearch 기능 개발 예정)'

        else: # WoRMS 레코드를 찾지 못한 경우
            result_entry['is_verified'] = False
            if not cleaned_scientific_name or cleaned_scientific_name == '-':
                if is_korean_search:
                     result_entry['worms_status'] = 'N/A (학명 없음)'
                     if korean_name:
                           print(f"[Info Verifier Core] '{korean_name}'(학명 없음) 심층분석 결과: 준비 중")
                           result_entry['wiki_summary'] = '준비 중 (DeepSearch 기능 개발 예정)'
                     else:
                           result_entry['wiki_summary'] = '준비 중 (DeepSearch 기능 개발 예정)'
                else:
                     result_entry['worms_status'] = '입력 오류'
                     result_entry['wiki_summary'] = '준비 중 (DeepSearch 기능 개발 예정)'
            else:
                result_entry['worms_status'] = 'WoRMS 결과 없음'
                print(f"[Info Verifier Core] WoRMS 실패, '{cleaned_scientific_name}' 심층분석 결과: 준비 중")
                result_entry['wiki_summary'] = '준비 중 (DeepSearch 기능 개발 예정)'

        results.append(result_entry)

    print(f"[Info Verifier Core] 해양생물 검증 완료: {len(results)}개 결과 생성")
    return results

def verify_single_microbe_lpsn(microbe_name):
    """
    LPSN API를 사용한 미생물 학명 검증 (fallback으로 웹 스크래핑 사용)
    """
    cleaned_name = clean_scientific_name(microbe_name)
    
    # 기본 결과 구조
    base_result = {
        'input_name': microbe_name,
        'scientific_name': cleaned_name,
        'is_verified': False,
        'valid_name': cleaned_name,
        'status': 'LPSN 접근 실패',
        'taxonomy': 'Domain: Bacteria (추정)',
        'lpsn_link': f"https://lpsn.dsmz.de/search?word={cleaned_name.replace(' ', '+')}",
        'wiki_summary': '준비 중 (DeepSearch 기능 개발 예정)',
        'korean_name': '-',
        'is_microbe': True
    }
    
    # 1단계: LPSN API 시도 (인증 정보가 있는 경우)
    try:
        import lpsn
        import os
        
        # 환경변수에서 인증 정보 확인
        lpsn_email = os.getenv("LPSN_EMAIL")
        lpsn_password = os.getenv("LPSN_PASSWORD")
        
        print(f"[Debug LPSN] 환경변수 확인: email={lpsn_email}, password={'설정됨' if lpsn_password else '없음'}")
        
        if lpsn_email and lpsn_password:
            print(f"[Info LPSN] API 인증으로 검증 시도: '{cleaned_name}'")
            
            client = lpsn.LpsnClient(lpsn_email, lpsn_password)
            count = client.search(taxon_name=cleaned_name, correct_name='yes')
            
            if count > 0:
                # 모든 검색 결과를 수집하여 species 우선 선택
                all_results = []
                for entry in client.retrieve():
                    if isinstance(entry, dict):
                        all_results.append(entry)
                
                # species 카테고리 우선 선택
                best_entry = None
                for entry in all_results:
                    category = entry.get('category', '').lower()
                    if category == 'species':
                        best_entry = entry
                        break
                
                # species가 없으면 첫 번째 결과 사용
                if not best_entry and all_results:
                    best_entry = all_results[0]
                
                if best_entry:
                    # LPSN API 결과 파싱
                    full_name = best_entry.get('full_name', cleaned_name)
                    taxonomic_status = best_entry.get('lpsn_taxonomic_status', 'unknown')
                    lpsn_url = best_entry.get('lpsn_address', f"https://lpsn.dsmz.de/search?word={cleaned_name.replace(' ', '+')}")
                    is_legitimate = best_entry.get('is_legitimate', False)
                    category = best_entry.get('category', 'species')
                    
                    # 검증 상태 결정
                    is_verified = is_legitimate and 'correct name' in taxonomic_status.lower()
                    
                    print(f"[Info LPSN] '{cleaned_name}' → '{full_name}' (카테고리: {category}, 검증: {is_verified})")
                    
                    return {
                        'input_name': microbe_name,
                        'scientific_name': full_name,
                        'is_verified': is_verified,
                        'valid_name': full_name,
                        'status': taxonomic_status,
                        'taxonomy': f"Domain: Bacteria; {category}",
                        'lpsn_link': lpsn_url,
                        'wiki_summary': '준비 중 (DeepSearch 기능 개발 예정)',
                        'korean_name': '-',
                        'is_microbe': True
                    }
            else:
                print(f"[Info LPSN] API 검색 결과 없음: '{cleaned_name}'")
        else:
            print(f"[Info LPSN] API 인증 정보 없음, 스크래핑으로 전환")
            
    except Exception as e:
        print(f"[Error LPSN] API 검증 실패: {e}")
    
    # 2단계: 웹 스크래핑 fallback
    try:
        from .lpsn_scraper import verify_microbe_lpsn_scraping
        scraping_result = verify_microbe_lpsn_scraping(microbe_name)
        if scraping_result:
            return scraping_result
    except Exception as e:
        print(f"[Error LPSN] 스크래핑도 실패: {e}")
    
    # 3단계: 기본 결과 반환
    return base_result


# --- COL(통합생물) 검증 로직 ---
def verify_col_species(col_names_list, result_callback=None):
    """
    COL(통합생물목록) API를 사용하여 학명을 검증합니다.
    향상된 col_api.py의 단일 처리 함수를 활용하여 리스트를 일괄 처리합니다.
    
    Args:
        col_names_list: 검증할 학명 문자열 리스트
        result_callback: 개별 결과 처리를 위한 콜백 함수 (Optional)
        
    Returns:
        각 학명에 대한 검증 결과 딕셔너리의 리스트
    """
    from .col_api import verify_col_species as col_api_verify_single
    
    results = []
    total_items = len(col_names_list)
    print(f"[Info Verifier Core] COL 검증 시작: {total_items}개 항목")
    
    for i, name in enumerate(col_names_list):
        print(f"[Info Verifier Core] {i+1}/{total_items} 처리 중 (COL): '{name}'")
        
        try:
            # col_api.py의 향상된 단일 처리 함수 사용
            single_result = col_api_verify_single(name)
            
            # 백엔드 형식으로 통일 (기존 인터페이스 호환성 유지)
            normalized_result = {
                "input_name": single_result.get("input_name", name),
                "scientific_name": single_result.get("scientific_name", name), 
                "is_verified": single_result.get("is_verified", False),
                "status": single_result.get("status", "unknown"),
                "valid_name": single_result.get("scientific_name", name),  # COL에서는 scientific_name이 valid_name 역할
                "taxonomy": single_result.get("심층분석 결과", "-"),  # 분류 정보가 있다면 매핑
                "col_id": single_result.get("col_id", "-"),
                "col_url": single_result.get("col_url", "-"),
                "is_microbe": False
            }
            
            results.append(normalized_result)
            
            # 결과 콜백 호출
            if result_callback:
                result_callback(normalized_result)
                
        except Exception as e:
            print(f"[Error Verifier Core] COL 검증 중 오류: '{name}' - {e}")
            # 오류 발생 시 기본 결과
            error_result = {
                "input_name": name,
                "scientific_name": name,
                "is_verified": False,
                "status": f"Error: {str(e)[:100]}",
                "valid_name": name,
                "taxonomy": "-",
                "col_id": "-",
                "col_url": "-",
                "is_microbe": False
            }
            results.append(error_result)
        
        if result_callback:
                result_callback(error_result)
    
    print(f"[Info Verifier Core] COL 검증 완료: {len(results)}개 결과 생성")
    return results

# _get_col_taxonomy 함수 제거됨 - col_api.py에서 더 정교한 처리로 대체됨

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
                'wiki_summary': '준비 중 (DeepSearch 기능 개발 예정)',
                'korean_name': '-',
                'is_microbe': True
            }
            
            # 실제 LPSN 검증 로직 구현 - verify_single_microbe_lpsn 함수 호출
            verification_result = verify_single_microbe_lpsn(microbe_name)
            
            # 검증 결과로 single_result 업데이트
            if verification_result:
                single_result.update(verification_result)
            else:
                # 검증 실패 시 기본값 유지
                print(f"[Warning Verifier Core] LPSN 검증 실패: '{microbe_name}'")
            
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