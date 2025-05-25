import requests
from typing import Dict, Any

def verify_col_species(scientific_name: str) -> Dict[str, Any]:
    """
    COL 글로벌 API를 이용해 학명 검증 결과를 반환합니다.
    
    Args:
        scientific_name (str): 검증할 학명
        
    Returns:
        Dict[str, Any]: 검증 결과를 담은 딕셔너리
    """
    url = "https://api.catalogueoflife.org/nameusage/search"
    params = {"q": scientific_name, "limit": 1}
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        # 결과가 있는지 확인
        if data.get("result") and len(data["result"]) > 0:
            match = data["result"][0]
            
            # 검색어와 결과가 너무 다른 경우 매칭 실패로 처리
            # 입력된 학명을 소문자로 변환하여 비교
            input_name_lower = scientific_name.lower()
            
            # 결과에서 학명 추출
            usage = match.get("usage", {})
            name_info = usage.get("name", {})
            result_name = name_info.get("scientificName", "")
            if not result_name:
                result_name = match.get("scientificName", "")
                
            # 결과 학명도 소문자로 변환
            result_name_lower = result_name.lower() if result_name else ""
            
            # 입력 학명의 단어들이 결과 학명에 포함되어 있는지 확인
            # 입력 학명을 단어로 분리
            input_words = [word.strip() for word in input_name_lower.split() if len(word.strip()) > 2]
            
            # 매칭 여부 확인 (입력 단어 중 하나라도 결과에 포함되어 있어야 함)
            is_valid_match = False
            if input_words:
                for word in input_words:
                    if word in result_name_lower:
                        is_valid_match = True
                        break
            else:
                # 입력 단어가 없는 경우 (짧은 단어만 있는 경우) 직접 비교
                is_valid_match = input_name_lower in result_name_lower
                
            # 매칭이 유효하지 않은 경우 결과가 없는 것으로 처리
            if not is_valid_match:
                return {
                    "query": scientific_name,
                    "matched": False,
                    "학명": scientific_name,
                    "검증": "Unknown",
                    "COL 상태": "유효하지 않은 학명",
                    "COL ID": "-",
                    "COL URL": "-",
                    "심층분석 결과": "-"
                }
            
            # usage -> name -> scientificName 경로 시도
            usage = match.get("usage", {})
            name_info = usage.get("name", {})
            extracted_name = name_info.get("scientificName")
            
            # 추출 실패 시 최상위 scientificName 시도 (기존 방식)
            if not extracted_name:
                extracted_name = match.get("scientificName")

            # 그래도 없으면 입력명 사용 또는 '-'
            final_name = extracted_name if extracted_name else scientific_name 

            # 기본 결과 생성 (참고용, 키 이름은 API 응답 기준)
            original_result = {
                "query": scientific_name,
                "matched": True,
                "extracted_scientificName": final_name, # 추출된 이름 기록
                "status": usage.get("status"), # usage에서 상태 가져오기
                "rank": name_info.get("rank"), # name에서 rank 가져오기
                "col_id": usage.get("id"), # usage에서 ID 가져오기
                # 필요한 다른 정보들도 usage 또는 name_info 에서 가져올 수 있음
            }

            # ResultTreeview 형식으로 변환
            col_id = usage.get("id", "-") # ID를 여기서도 사용
            col_url = f"https://www.catalogueoflife.org/data/taxon/{col_id}" if col_id != '-' else '-'
            status = usage.get("status", "-")

            display_result = {
                "학명": final_name, # 추출된 학명 사용
                "검증": "Accepted" if status == "accepted" else status.capitalize() if isinstance(status, str) else "Unknown", # 상태에 기반한 검증
                "COL 상태": status,
                "COL ID": col_id,
                "COL URL": col_url,
                "심층분석 결과": "-",
                "original_data": original_result # 수정된 원본 데이터
            }
            return display_result
        else:
            # 매칭 결과가 없을 경우
            return {
                "query": scientific_name,
                "matched": False,
                "학명": scientific_name,
                "검증": "Unknown",
                "COL 상태": "-",
                "COL ID": "-",
                "COL URL": "-",
                "심층분석 결과": "-"
            }
    except requests.exceptions.HTTPError as http_err:
        # HTTP 에러 처리
        error_message = f"{http_err.response.status_code} {http_err.response.reason}"
        print(f"[Error COL API] HTTP error occurred: {error_message} for query: {scientific_name}")
        return {
            "query": scientific_name, "matched": False, "error": error_message,
            "학명": scientific_name, "검증": "Error", "COL 상태": f"오류: {error_message}",
            "COL ID": "-", "COL URL": "-", "심층분석 결과": "-"
        }
    except Exception as e:
        # 기타 에러 처리
        print(f"[Error COL API] General error occurred: {e} for query: {scientific_name}")
        return {
            "query": scientific_name, "matched": False, "error": str(e),
            "학명": scientific_name, "검증": "Error", "COL 상태": f"오류: {str(e)}",
            "COL ID": "-", "COL URL": "-", "심층분석 결과": "-"
        } 