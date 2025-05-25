# species_verifier/core/wiki.py

"""Handles interactions with the Wikipedia API."""

import wikipedia
import requests
import re
import traceback
import time

def get_wiki_summary(search_term, check_cancelled=None):
    """주어진 검색어로 위키백과 페이지의 내용을 가져옵니다.

    한국어 페이지를 먼저 시도하고, 없으면 영어 페이지를 검색합니다.
    다의어 페이지의 경우 첫 번째 옵션을 사용합니다.
    가져온 내용은 기본적인 정제 과정을 거칩니다.
    
    Args:
        search_term (str): 검색할 학명
        check_cancelled (callable, optional): 취소 여부를 확인하는 콜백 함수
    
    Returns:
        str: 심층분석 결과 또는 오류 메시지
    """
    if not search_term or search_term == '-':
        return "정보 없음"

    try:
        print(f"[Info Wiki Core] '{search_term}' 위키백과 페이지 검색 시도")
        
        # 취소 여부 확인
        if check_cancelled and check_cancelled():
            print(f"[Debug Wiki] '{search_term}' 위키백과 검색 취소 요청됨")
            return "작업 취소됨"
            
        wikipedia.set_lang("ko") # 한국어 먼저 시도
        is_english_page = False
        page = None

        try:
            # 취소 여부 확인
            if check_cancelled and check_cancelled():
                print(f"[Debug Wiki] '{search_term}' 한국어 위키백과 검색 전 취소 요청됨")
                return "작업 취소됨"
                
            page = wikipedia.page(search_term, auto_suggest=False)
            print(f"[Info Wiki Core] '{search_term}' 한국어 페이지 찾음")
        except wikipedia.exceptions.PageError:
            print(f"[Info Wiki Core] '{search_term}' 한국어 페이지 없음, 영어로 시도")
            wikipedia.set_lang("en")
            
            # 취소 여부 확인
            if check_cancelled and check_cancelled():
                print(f"[Debug Wiki] '{search_term}' 영어 위키백과 검색 전 취소 요청됨")
                return "작업 취소됨"
                
            try:
                page = wikipedia.page(search_term, auto_suggest=False) # 영어로 재시도
                print(f"[Info Wiki Core] '{search_term}' 영어 페이지 찾음")
                is_english_page = True
            except wikipedia.exceptions.PageError: # 영어로도 못 찾은 경우
                print(f"[Info Wiki Core] '{search_term}' 영어 페이지도 찾을 수 없음")
                return "정보 없음 (페이지 없음)"
            except wikipedia.exceptions.DisambiguationError as e_en:
                # 영어 다의어 처리
                if e_en.options:
                    # 취소 여부 확인
                    if check_cancelled and check_cancelled():
                        print(f"[Debug Wiki] '{search_term}' 영어 다의어 처리 전 취소 요청됨")
                        return "작업 취소됨"
                    
                    first_option_en = e_en.options[0]
                    print(f"[Warning Wiki Core] 영어 '{search_term}' 다의어, 첫 옵션 '{first_option_en}'으로 재시도")
                    return get_wiki_summary(first_option_en, check_cancelled) # 재귀 호출
                else:
                    print(f"[Warning Wiki Core] 영어 '{search_term}' 다의어 페이지지만 옵션 없음: {e_en}")
                    return "정보 없음 (다의어 처리 실패)"

        except wikipedia.exceptions.DisambiguationError as e_ko:
            # 한국어 다의어 처리
            if e_ko.options:
                # 취소 여부 확인
                if check_cancelled and check_cancelled():
                    print(f"[Debug Wiki] '{search_term}' 한국어 다의어 처리 전 취소 요청됨")
                    return "작업 취소됨"
                    
                first_option_ko = e_ko.options[0]
                print(f"[Warning Wiki Core] 한국어 '{search_term}' 다의어, 첫 옵션 '{first_option_ko}'으로 재시도")
                return get_wiki_summary(first_option_ko, check_cancelled) # 재귀 호출
            else:
                print(f"[Warning Wiki Core] 한국어 '{search_term}' 다의어 페이지지만 옵션 없음: {e_ko}")
                return "정보 없음 (다의어 처리 실패)"

        # page 객체가 성공적으로 생성되었는지 확인
        if page is None:
             print(f"[Info Wiki Core] '{search_term}'에 대한 페이지 객체를 생성하지 못했습니다.")
             return "정보 없음"

        # 취소 여부 확인
        if check_cancelled and check_cancelled():
            print(f"[Debug Wiki] '{search_term}' 페이지 내용 가져오기 전 취소 요청됨")
            return "작업 취소됨"
        
        try:
            # 전체 문서 내용 가져오기
            content = page.content
            print(f"[Info Wiki Core] '{search_term}' 전체 내용 ({len(content)} chars) 가져옴")
            
            # 취소 여부 확인
            if check_cancelled and check_cancelled():
                print(f"[Debug Wiki] '{search_term}' 내용 가져온 후 취소 요청됨")
                return "작업 취소됨"
            
            # 내용이 비어있는지 확인
            if not content or not content.strip():
                print(f"[Info Wiki Core] '{search_term}' 페이지 내용이 비어 있음")
                return "정보 없음"
                
            # 취소 여부 확인
            if check_cancelled and check_cancelled():
                print(f"[Debug Wiki] '{search_term}' 내용 처리 전 취소 요청됨")
                return "작업 취소됨"
                
            # 내용 정제: 위키 마크업 정리 및 불필요한 섹션 제거
            sections = content.split('\n== ')
            main_content = sections[0] # 기본적으로 첫 번째 섹션만 사용

            # 영어 페이지의 경우, 첫 섹션 내용이 짧으면 추가 섹션 포함 시도
            if is_english_page and len(main_content.strip()) < 100:
                included_sections = [main_content]
                section_count = min(len(sections), 3) # 최대 3개 섹션
                skip_sections = ['references', 'external links', 'see also', 'further reading']

                for i in range(1, section_count):
                    # 취소 여부 확인
                    if check_cancelled and check_cancelled():
                        print(f"[Debug Wiki] '{search_term}' 섹션 처리 중 취소 요청됨")
                        return "작업 취소됨"
                        
                    if sections[i]:
                        section_parts = sections[i].split('\n', 1) # 제목과 내용 분리
                        section_title = section_parts[0].strip().lower()
                        section_content = section_parts[1] if len(section_parts) > 1 else ""

                        if section_content.strip() and not any(skip_title in section_title for skip_title in skip_sections):
                            included_sections.append(f"== {sections[i]}")

                main_content = '\n'.join(included_sections)
                print(f"[Info Wiki Core] 영어 페이지: {len(included_sections)}개 섹션 내용 결합됨")

            # 취소 여부 확인
            if check_cancelled and check_cancelled():
                print(f"[Debug Wiki] '{search_term}' 콘텐츠 정리 전 취소 요청됨")
                return "작업 취소됨"

            # 불필요한 마크업 제거
            cleaned_content = re.sub(r'\[[0-9]+\]', '', main_content)  # 각주 번호 [1], [2] 등 제거
            cleaned_content = re.sub(r'{{\.*?}}', '', cleaned_content)  # {{...}} 템플릿 제거
            cleaned_content = cleaned_content.strip()

            # 길이 제한 적용
            max_length = 500 if is_english_page else 300  # 영어 페이지는 더 긴 내용 허용
            if len(cleaned_content) > max_length:
                cleaned_content = cleaned_content[:max_length] + "... (더 많은 내용 있음)"

            print(f"[Info Wiki Core] '{search_term}' 최종 위키 요약 길이: {len(cleaned_content)} chars")
            return cleaned_content
        except Exception as inner_e:
            print(f"[Error Wiki Core] '{search_term}' 페이지 내용 처리 중 오류: {inner_e}")
            traceback.print_exc()
            return "정보 없음 (내용 처리 오류)"

    except requests.exceptions.RequestException as req_e:
        print(f"[Error Wiki Core] '{search_term}' 위키 네트워크 오류: {req_e}")
        return "정보 없음 (네트워크 오류)"
    except Exception as wiki_e:
        print(f"[Error Wiki Core] '{search_term}' 위키 검색 중 예외 발생: {wiki_e}")
        traceback.print_exc() # 상세 오류 로그 출력
        return "정보 없음 (오류)"

def extract_scientific_name_from_wiki(korean_name):
    """위키백과에서 한글 이름에 대한 학명을 추출합니다.
    """
    try:
        print(f"[Info Wiki Core] 위키에서 '{korean_name}' 학명 추출 시도")
        wikipedia.set_lang("ko")
        page = None

        try:
            search_results = wikipedia.search(korean_name, results=3)
            if not search_results:
                print(f"[Info Wiki Core] '{korean_name}' 위키 검색 결과 없음 (학명 추출 실패)")
                return None

            page_title = search_results[0]
            print(f"[Info Wiki Core] '{korean_name}' 첫 검색 결과 사용: {page_title}")

            try:
                page = wikipedia.page(page_title, auto_suggest=False)
            except wikipedia.exceptions.DisambiguationError as e:
                if e.options:
                    page_title = e.options[0]
                    print(f"[Info Wiki Core] 다의어 처리, 첫 옵션 사용: {page_title}")
                    # 다의어 페이지를 다시 로드 시도
                    try:
                        page = wikipedia.page(page_title, auto_suggest=False)
                    except wikipedia.exceptions.PageError:
                         print(f"[Warning Wiki Core] 다의어 옵션 '{page_title}' 페이지 로드 실패")
                         return None
                    except wikipedia.exceptions.DisambiguationError:
                         print(f"[Warning Wiki Core] 다의어 옵션 '{page_title}'이 또 다의어 페이지임")
                         return None
                else:
                    print(f"[Warning Wiki Core] 다의어 페이지 옵션 없음 (학명 추출 실패): {e}")
                    return None
            except wikipedia.exceptions.PageError:
                print(f"[Warning Wiki Core] '{korean_name}'에 대한 위키 페이지 없음 (학명 추출 실패)")
                return None

            # page 객체가 생성되었는지 확인
            if page is None:
                print(f"[Warning Wiki Core] '{korean_name}'에 대한 페이지 객체를 생성하지 못함 (학명 추출 실패)")
                return None

            content = page.content
            scientific_name_patterns = [
                r'[학|學]명[은|:\s]*.{0,10}?([A-Z][a-z]+ [a-z]+)',  # '학명: Genus species' 형식
                r'(?<![a-zA-Z])([A-Z][a-z]+ [a-z]+)(?![a-zA-Z])',  # 일반적인 'Genus species' 형식 (단어 경계 추가)
                r'\(([A-Z][a-z]+ [a-z]+)\)'  # '(Genus species)' 형식
            ]

            for pattern in scientific_name_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    scientific_name = matches[0].strip('()') # 첫 번째 매치 사용 및 괄호 제거
                    # 추가 검증: 너무 짧거나 일반적인 단어 제외 (선택적)
                    if len(scientific_name.split()) == 2: # 최소 2단어 확인
                        print(f"[Success Wiki Core] '{korean_name}' 학명 추출 성공: {scientific_name}")
                        return scientific_name
                    else:
                        print(f"[Warning Wiki Core] 추출된 이름 '{scientific_name}' 형식 미달, 다음 패턴 시도")

            print(f"[Warning Wiki Core] '{korean_name}' 위키 페이지에서 학명 추출 실패")
            return None

        except wikipedia.exceptions.PageError: # search 단계에서 오류 발생 시
             print(f"[Warning Wiki Core] '{korean_name}' 위키 검색 중 PageError 발생 (학명 추출 실패)")
             return None

    except Exception as e:
        print(f"[Error Wiki Core] '{korean_name}' 위키 학명 추출 중 오류: {e}")
        traceback.print_exc()
        return None
