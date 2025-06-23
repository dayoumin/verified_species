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

# 사용되지 않는 함수 제거됨

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

def verify_single_microbe_lpsn(microbe_name):
    """
    LPSN(List of Prokaryotic names with Standing in Nomenclature) 웹사이트에서 미생물 학명을 검증합니다.
    학명을 바로 URL로 변환하여 직접 종 페이지에 접근합니다.
    
    Args:
        microbe_name: 검증할 미생물 학명 문자열
        
    Returns:
        검증 결과를 포함한 디셔너리
    """
    print(f"[Info LPSN Core] LPSN 검증 시작: '{microbe_name}'")
    cleaned_name = clean_scientific_name(microbe_name)
    
    # 기본 결과 디셔너리 구조 정의
    base_result = {
        'input_name': microbe_name,
        'scientific_name': cleaned_name if cleaned_name else microbe_name,
        'is_verified': False,  # 기본값은 검증 실패
        'valid_name': cleaned_name if cleaned_name else microbe_name,
        'status': 'Not found in LPSN',
        'taxonomy': 'Domain: Bacteria',
        'lpsn_link': f"https://lpsn.dsmz.de/search?word={cleaned_name.replace(' ', '+')}",
        'wiki_summary': '-',
        'is_microbe': True
    }

    if not cleaned_name or cleaned_name == '-':
        print(f"[Warning LPSN Core] Invalid input after cleaning: '{microbe_name}'")
        base_result['status'] = 'Invalid input'
        return base_result

    # 초기화
    detail_soup = None
    species_detail_url = None
    
    try:
        # LPSN 접근을 위한 헤더 설정
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # 학명에서 종명 추출하여 직접 URL 생성 (예: Streptococcus parauberis -> streptococcus-parauberis)
        genus_species = cleaned_name.lower().replace(' ', '-')
        direct_species_url = f"https://lpsn.dsmz.de/species/{genus_species}"
        print(f"[Info LPSN Core] 직접 접근 URL: {direct_species_url}")
        
        try:
            # LPSN 서버 부하 방지를 위한 지연 시간 추가
            time.sleep(1.0)
            # 직접 URL 접근 시도
            direct_response = requests.get(direct_species_url, headers=headers, timeout=10)
            direct_response.raise_for_status()  # 404 등의 오류 확인
            
            # 성공적으로 페이지에 접근했다면 상세 정보 파싱
            species_detail_url = direct_species_url
            detail_soup = BeautifulSoup(direct_response.text, 'html.parser')
            
            # 페이지 제목에서 학명 확인
            title_elem = detail_soup.find('h1')
            
            # 공백을 유지하도록 strip=False로 변경하고 추가 전처리 수행
            title_text_raw = title_elem.get_text(strip=False) if title_elem else ''
            # 추가 공백 제거 및 여러 공백을 하나로 변환하되 단어 간 공백은 유지
            title_text = ' '.join(title_text_raw.split())
            print(f"[Debug LPSN Core] 원본 페이지 제목: '{title_text_raw}'")
            print(f"[Debug LPSN Core] 처리된 페이지 제목: '{title_text}'")
            print(f"[Debug LPSN Core] 비교할 학명: '{cleaned_name}'")
            
            # HTML 구조 분석
            print(f"[Debug LPSN Core] HTML 구조: {title_elem}")
            
            # 강화된 비교 로직
            # 학명에서 이탤릭체 태그가 제거되었을 수 있으므로 직접 추출
            italicized_name = ''
            if title_elem:
                italic_elems = title_elem.find_all('i')
                if len(italic_elems) >= 2:  # 보통 속명과 종명이 각각 <i> 태그로 감싸짐
                    italicized_name = ' '.join([i.get_text(strip=True) for i in italic_elems])
                    print(f"[Debug LPSN Core] 추출된 이탤릭체 학명: '{italicized_name}'")
            
            # 다양한 비교 방법 시도
            contains_name = cleaned_name.lower() in title_text.lower()
            contains_with_species = f"species {cleaned_name}".lower() in title_text.lower()
            contains_genus_species = genus_species.replace('-', ' ') in title_text.lower()
            # 이탤릭체에서 추출한 학명과 직접 비교 추가
            contains_italicized = False
            if italicized_name:
                contains_italicized = cleaned_name.lower() == italicized_name.lower()
            
            print(f"[Debug LPSN Core] 학명 포함 여부: {contains_name}")
            print(f"[Debug LPSN Core] 'Species+학명' 포함 여부: {contains_with_species}")
            print(f"[Debug LPSN Core] 속명+종명 포함 여부: {contains_genus_species}")
            print(f"[Debug LPSN Core] 이탤릭체 학명 일치 여부: {contains_italicized}")
            
            # 다양한 조건을 포함하여 확인 (이탤릭체 추출 비교 추가)
            if title_elem and (contains_name or contains_with_species or contains_genus_species or 
                               title_text.lower().endswith(cleaned_name.lower()) or contains_italicized):
                print(f"[Info LPSN Core] 직접 URL에서 학명 발견: {title_elem.get_text(strip=True)}")
                
                # 분류학적 정보 추출
                taxonomy_parts = []
                taxonomy_section = detail_soup.find('div', class_='classification')
                print(f"[Info LPSN Core] 직접 URL 접근 성공: {direct_species_url}")
            else:
                print(f"[Warning LPSN Core] 직접 URL에서 학명을 찾을 수 없음")
                detail_soup = None
                taxonomy_parts = []
                taxonomy_section = None
        except requests.exceptions.HTTPError as e:
            # 404 등의 오류가 발생한 경우
            print(f"[Warning LPSN Core] 직접 URL 접근 실패: {e}")
            detail_soup = None
            taxonomy_parts = []
            taxonomy_section = None
        except Exception as e:
            print(f"[Error LPSN Core] 직접 URL 접근 중 오류 발생: {e}")
            detail_soup = None
            taxonomy_parts = []
            taxonomy_section = None
        # 분류학적 정보 추출
        if taxonomy_section:
            taxonomy_items = taxonomy_section.find_all('div', class_='classification-item')
            for item in taxonomy_items:
                rank_elem = item.find('div', class_='rank')
                name_elem = item.find('div', class_='name')
                if rank_elem and name_elem:
                    rank = rank_elem.get_text(strip=True)
                    name = name_elem.get_text(strip=True)
                    if rank and name:
                        taxonomy_parts.append(f"{rank}: {name}")
        
        # 학명 상태 추출 - 다양한 위치와 클래스를 시도하여 상태 정보 찾기
        taxonomic_status = 'unknown'
        
        # 방법 1: .status 클래스 찾기
        status_elem = detail_soup.find('div', class_='status') if detail_soup else None
        if status_elem:
            taxonomic_status = status_elem.get_text(strip=True)
            print(f"[Info LPSN Core] 방법1에서 상태 추출: {taxonomic_status}")
        
        # 방법 2: 'Status:' 텍스트를 포함하는 요소 찾기
        if taxonomic_status == 'unknown' and detail_soup:
            status_labels = detail_soup.find_all(string=lambda text: 'status' in text.lower() if text else False)
            for label in status_labels:
                parent = label.parent
                if parent and parent.next_sibling:
                    status_text = parent.next_sibling.strip()
                    if status_text:
                        taxonomic_status = status_text
                        print(f"[Info LPSN Core] 방법2에서 상태 추출: {taxonomic_status}")
                        break
        
        # 방법 3: 'Status' 또는 'Type' 등의 테이블에서 찾기
        if taxonomic_status == 'unknown' and detail_soup:
            table_rows = detail_soup.find_all('tr')
            for row in table_rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    header = cells[0].get_text(strip=True).lower()
                    if 'status' in header or 'type' in header:
                        status_text = cells[1].get_text(strip=True)
                        taxonomic_status = status_text
                        print(f"[Info LPSN Core] 방법3에서 상태 추출: {taxonomic_status}")
                        break
        
        # 검증 상태에 따라 기본값 설정 (학명 페이지를 찾았으면 'correct name')
        if taxonomic_status == 'unknown' and detail_soup:
            # 페이지를 찾았으나 상태를 추출하지 못한 경우 'correct name'으로 가정
            taxonomic_status = 'correct name'
            print(f"[Info LPSN Core] 상태를 찾을 수 없어 기본값 설정: {taxonomic_status}")
        
        print(f"[Info LPSN Core] 최종 추출된 상태: {taxonomic_status}")
        
        # 유효한 학명 추출 - 이탤릭체 태그에서 학명 추출 우선
        title_elem = detail_soup.find('h1') if detail_soup else None
        valid_name = cleaned_name
        
        if title_elem:
            # 이탤릭체 태그에서 학명 추출 시도 (이 방법이 가장 정확함)
            italic_elems = title_elem.find_all('i') if title_elem else []
            if len(italic_elems) >= 2:
                valid_name = ' '.join([i.get_text(strip=True) for i in italic_elems])
                print(f"[Debug LPSN Core] 이탤릭체에서 학명 추출: {valid_name}")
            else:
                # 이탤릭체 태그가 없으면 전체 텍스트에서 추출
                title_text = ' '.join(title_elem.get_text(strip=False).split())
                # 'Species ' 접두사 제거
                if title_text.lower().startswith('species '):
                    valid_name = title_text[len('Species '):]
                else:
                    valid_name = title_text
            print(f"[Info LPSN Core] 제목에서 학명 추출: {valid_name}")
        
        # 결과 업데이트
        if detail_soup and species_detail_url:
            # 링크가 UI에 표시될 때 잘리지 않도록 완전한 URL 저장
            print(f"[Debug LPSN Core] 저장할 링크 URL: {species_detail_url}")
            
            # 'Species ' 접두사 제거
            if valid_name.startswith('Species '):
                valid_name = valid_name[len('Species '):]
                
            base_result.update({
                'is_verified': True,  # 상세 페이지를 찾았으므로 검증 성공
                'scientific_name': valid_name,
                'valid_name': valid_name,
                'status': taxonomic_status,
                'taxonomy': ' | '.join(taxonomy_parts) if taxonomy_parts else 'Domain: Bacteria',
                'lpsn_link': species_detail_url  # 완전한 URL 저장
            })
            
            # 위키백과 정보 추가
            wiki_summary = get_wiki_summary(valid_name) or '-'
            base_result['wiki_summary'] = wiki_summary
        else:
            print(f"[Warning LPSN Core] 종 페이지를 찾을 수 없음: {cleaned_name}")
            base_result['is_verified'] = False
            base_result['status'] = 'Not found in LPSN'
            base_result['lpsn_link'] = f"https://lpsn.dsmz.de/search?word={cleaned_name.replace(' ', '+')}"
        
        # 결과 반환
        return base_result
    
    except requests.exceptions.RequestException as e:
        print(f"[Error LPSN Core] 요청 오류: {e}")
        base_result['status'] = f'요청 오류: {str(e)[:50]}...'
        base_result['lpsn_link'] = search_url
        base_result['is_verified'] = False
        base_result['valid_name'] = '유효하지 않음'
        
    except Exception as e:
        print(f"[Error LPSN Core] 미생물 검증 중 오류: {e}")
        traceback.print_exc()
        base_result['status'] = f'오류: {str(e)[:50]}...'
        base_result['lpsn_link'] = search_url
        base_result['is_verified'] = False
        base_result['valid_name'] = '유효하지 않음'
        
    # 최종 로그 출력
    print(f"[Info LPSN Core] LPSN 검증 완료: '{microbe_name}' -> Status: {base_result['status']}")
    return base_result


# --- COL(통합생물) 검증 로직 ---
def verify_col_species(col_names_list, result_callback=None):
    """
    COL(통합생물목록) API를 사용하여 학명을 검증합니다.
    
    Args:
        col_names_list: 검증할 학명 문자열 리스트
        result_callback: 개별 결과 처리를 위한 콜백 함수 (Optional)
        
    Returns:
        각 학명에 대한 검증 결과 딕셔너리의 리스트
    """
    import requests
    import json
    from urllib.parse import quote
    
    results = []
    
    for name in col_names_list:
        try:
            # COL API 엔드포인트
            base_url = "https://api.catalogueoflife.org/"
            search_url = f"{base_url}dataset/3LR/nameusage/search?q={quote(name)}&limit=1"
            
            # COL API 서버 부하 방지를 위한 지연 시간 추가
            time.sleep(0.5)
            # COL API 요청
            response = requests.get(search_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # 결과 파싱
            if data.get('result') and len(data['result']) > 0:
                result_data = data['result'][0]
                col_id = result_data.get('id', '-')
                status = result_data.get('status', 'unknown').capitalize()
                
                # COL 웹사이트 URL 생성
                col_url = f"https://www.catalogueoflife.org/data/taxon/{col_id}"
                
                result = {
                    "input_name": name,
                    "scientific_name": result_data.get('name', name),
                    "is_verified": status.lower() in ['accepted', 'provisionally accepted'],
                    "status": status,
                    "valid_name": result_data.get('acceptedName', {}).get('name', name),
                    "taxonomy": _get_col_taxonomy(result_data),
                    "col_id": col_id,
                    "col_url": col_url,
                    "is_microbe": False
                }
            else:
                # 검색 결과가 없는 경우
                result = {
                    "input_name": name,
                    "scientific_name": name,
                    "is_verified": False,
                    "status": "Not found in COL",
                    "valid_name": name,
                    "taxonomy": "-",
                    "col_id": "-",
                    "col_url": "-",
                    "is_microbe": False
                }
                
        except Exception as e:
            # 오류 발생 시
            result = {
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
        
        # 결과 추가
        if result_callback:
            result_callback(result)
        results.append(result)
    
    return results

def _get_col_taxonomy(result_data):
    """COL API 결과에서 분류학적 정보를 추출합니다."""
    try:
        classification = result_data.get('classification', [])
        if not classification:
            return "-"
            
        # 분류 정보를 계층별로 추출
        ranks = []
        for rank in ['kingdom', 'phylum', 'class', 'order', 'family', 'genus', 'species']:
            for taxon in classification:
                if taxon.get('rank', '').lower() == rank:
                    ranks.append(f"{rank.capitalize()}: {taxon.get('name', '')}")
                    break
                    
        return " | ".join(ranks) if ranks else "-"
    except Exception:
        return "-"

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