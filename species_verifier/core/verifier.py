import pyworms
import time
import wikipedia

def check_scientific_name(name_to_check, korean_name=None):
    """
    단일 학명을 pyworms 및 wikipedia를 사용하여 검증하고 관련 정보를 딕셔너리로 반환합니다.
    korean_name: 선택적 매개변수로, 위키피디아 검색을 위한 한글 국명을 전달받을 수 있습니다.
    """
    # 기본 결과 구조 초기화 (wiki_summary 필드 추가)
    result = {
        "input_name": name_to_check,
        "is_verified": False,
        "scientific_name": "조회 실패",
        "worms_id": "조회 실패",
        "worms_status": "시작 전",
        "worms_url": "-",
        "wiki_summary": "-",
        "similar_name": "-"  # 유사한 이름 필드 추가
    }
    
    try:
        # pyworms를 사용하여 Aphia 레코드 조회 시도 (이름 기준)
        # match_fuzzy=True, marine_only=False 옵션 고려 가능
        records_result = pyworms.aphiaRecordsByName(name_to_check)

        # 결과가 리스트 형태이고, 비어있지 않은지 확인
        best_record = None # 최적의 레코드를 저장할 변수
        if records_result and isinstance(records_result, list) and len(records_result) > 0:
            # 'Accepted' 상태인 레코드를 우선적으로 찾음
            accepted_records = [r for r in records_result if r.get('status') == 'Accepted']
            if accepted_records:
                best_record = accepted_records[0] # 첫 번째 'Accepted' 레코드 사용
            else:
                # 'Accepted' 레코드가 없으면, 그냥 첫 번째 레코드 사용
                best_record = records_result[0]
        
        # WoRMS API 검색 결과가 없는 경우, 유사한 이름 검색 시도
        if not best_record:
            # 대안 1: 유사 검색 (첫 번째 방법이 실패한 경우)
            try:
                # 유사한 이름 검색을 위해 match_fuzzy=True 옵션 사용
                fuzzy_results = pyworms.aphiaRecordsByMatchNames([name_to_check], match_fuzzy=True)
                if fuzzy_results and isinstance(fuzzy_results, list) and len(fuzzy_results) > 0:
                    # 첫 번째 결과의 매치 레코드 가져오기
                    first_result = fuzzy_results[0]
                    if 'matches' in first_result and first_result['matches']:
                        best_record = first_result['matches'][0]  # 가장 일치하는 레코드 사용
                        # 유사한 이름 저장
                        result["similar_name"] = best_record.get('scientificname', '-')
                        print(f"[Info] 유사한 이름 찾음: '{name_to_check}' -> '{result['similar_name']}'")
            except Exception as fuzzy_err:
                print(f"[Warning] 유사 검색 오류: {fuzzy_err}")

        if best_record:
            # 선택된 최적의 레코드 사용
            record = best_record
            aphia_id = record.get('AphiaID') # 레코드에서 AphiaID 추출 시도

            if aphia_id:
                result["worms_id"] = aphia_id
                # 이미 레코드를 가져왔으므로, record 변수의 정보 활용
                result["worms_status"] = record.get('status', '-')
                # 오류 수정: 대소문자 무시 및 공백 제거 후 비교
                result["is_verified"] = result["worms_status"].strip().lower() == 'accepted'
                
                # 학명이 입력과 다른 경우 similar_name 필드에 저장
                record_scientific_name = record.get('scientificname', '-')
                if record_scientific_name and record_scientific_name.lower() != name_to_check.lower():
                    result["similar_name"] = record_scientific_name
                
                result["scientific_name"] = record.get('valid_name', '-')
                result["worms_url"] = record.get('url', '-')

                # --- Wikipedia 요약 조회 (WoRMS 검증 성공 시) ---
                if result["is_verified"] and result["scientific_name"] != '-':
                    try:
                        wikipedia.set_lang("ko") # 언어 설정: 한국어
                        # sentences=2 로 2문장 요약 가져오기
                        search_terms = []
                        
                        # 국명이 제공된 경우, 국명으로 먼저 검색
                        if korean_name:
                            search_terms.append(korean_name)  # 첫 번째로 국명 검색 시도
                        
                        # 그 다음으로 학명 검색
                        search_terms.append(result["scientific_name"])  # 완전한 학명 시도
                        search_terms.append(result["scientific_name"].split()[0])  # 속명만 시도
                        
                        summary = None
                        successful_term = None
                        
                        for term in search_terms:
                            try:
                                print(f"[Info Wiki] '{term}' 위키백과 검색 시도")
                                summary = wikipedia.summary(term, sentences=2)
                                if summary and summary.strip():
                                    successful_term = term
                                    break
                            except (wikipedia.exceptions.PageError, wikipedia.exceptions.DisambiguationError):
                                continue
                            except Exception as e:
                                print(f"[Error Wiki] '{term}' 위키백과 검색 실패: {e}")
                                continue
                        
                        if summary:
                            result["wiki_summary"] = summary
                            print(f"[Info Wiki] '{successful_term}' 위키백과 요약 찾음")
                        else:
                            result["wiki_summary"] = "위키백과 정보 없음"
                            
                    except wikipedia.exceptions.PageError:
                        result["wiki_summary"] = "위키백과 정보 없음"
                    except wikipedia.exceptions.DisambiguationError as e:
                        # 여러 후보가 있는 경우, 첫 번째 후보로 다시 시도
                        try:
                            print(f"[Info Wiki] Disambiguation error for {result['scientific_name']}: {e.options[:3]}")
                            # 첫 번째 후보로 다시 시도
                            if e.options:
                                summary = wikipedia.summary(e.options[0], sentences=2)
                                result["wiki_summary"] = summary
                            else:
                                result["wiki_summary"] = "위키백과 정보 없음 (다중 항목)"
                        except Exception:
                            result["wiki_summary"] = "위키백과 정보 없음 (다중 항목)"
                    except Exception as wiki_e:
                        print(f"[Error Wiki] '{result['scientific_name']}' 위키백과 조회 오류: {wiki_e}")
                        result["wiki_summary"] = "위키백과 조회 오류"
                # ---------------------------------------------

            else:
                # 레코드는 찾았으나 AphiaID가 없는 경우
                result["worms_status"] = "AphiaID 없음 (레코드 확인 필요)"
        else:
            # 이름을 찾지 못한 경우
            result["worms_status"] = "WoRMS 이름 조회 실패"

    except Exception as e:
        # 네트워크 오류 등 pyworms 라이브러리 자체 오류 처리
        print(f"[Error pyworms] '{name_to_check}' 처리 중 오류: {e}")
        result["worms_status"] = f"오류 발생: {e}"

    return result

def verify_species_list(species_list, progress_callback=None):
    """
    pyworms를 사용하여 주어진 학명 리스트(또는 (원래입력, 학명, 국명) 튜플 리스트)를 검증하고 결과를 리스트로 반환합니다.
    progress_callback: 진행률 업데이트를 위한 콜백 함수
    """
    results = []
    total = len(species_list)
    if total == 0:
        if progress_callback:
            progress_callback(1.0)
        return results

    for i, item in enumerate(species_list):
        original_input = None
        name_to_check = None
        korean_name = None

        # 입력 항목 타입 확인
        if isinstance(item, tuple):
            if len(item) == 3:  # (원래입력, 검증할이름, 국명)
                original_input, name_to_check, korean_name = item
            elif len(item) == 2:  # (원래입력, 검증할이름)
                original_input, name_to_check = item
                korean_name = None
        elif isinstance(item, str):
            original_input = item  # 원래입력과 검증할이름 동일
            name_to_check = item
            korean_name = None
        else:
            # 지원하지 않는 타입은 건너뛰기 또는 오류 처리
            print(f"[Warning] Skipping unsupported item type: {type(item)}")
            results.append({
                "input_name": str(item),  # 최대한 문자열로 표시
                "is_verified": False,
                "scientific_name": "처리 불가",
                "worms_id": "-",
                "worms_status": "입력 형식 오류",
                "worms_url": "-",
                "wiki_summary": "-",
                "similar_name": "-"
            })
            if progress_callback:
                progress = (i + 1) / total
                progress_callback(progress)
            continue  # 다음 항목으로

        # check_scientific_name 호출 (검증할 이름 및 국명 사용)
        result = check_scientific_name(name_to_check, korean_name)
        # 결과 딕셔너리의 input_name을 항상 원래 입력값으로 설정
        result["input_name"] = original_input
        results.append(result)

        # API 호출 제한 지연 (선택 사항)
        # time.sleep(0.1)

        if progress_callback:
            progress = (i + 1) / total
            progress_callback(progress)

    return results

# --- 이하 GUI 관련 코드 삭제 ---