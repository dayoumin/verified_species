import requests
import time
from typing import Dict, Any
from species_verifier.config import api_config

def verify_col_species(scientific_name: str) -> Dict[str, Any]:
    """
    COL 글로벌 API를 이용해 학명 검증 결과를 반환합니다.
    
    Args:
        scientific_name (str): 검증할 학명
        
    Returns:
        Dict[str, Any]: 검증 결과를 담은 딕셔너리
    """
    url = "https://api.catalogueoflife.org/nameusage/search"
    params = {"q": scientific_name, "limit": 1, "type": "EXACT"}
    
    # config 값 안전하게 처리
    if api_config is not None:
        max_retries = api_config.MAX_RETRIES
        request_delay = api_config.REQUEST_DELAY
        retry_delay = api_config.RETRY_DELAY
        headers = api_config.DEFAULT_HEADERS
        timeout = api_config.COL_REQUEST_TIMEOUT
    else:
        # api_config가 None인 경우 기본값 사용
        max_retries = 3
        request_delay = 1.0
        retry_delay = 2.0
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        timeout = 10
        print("[Warning COL API] api_config가 None이므로 기본값 사용")

    # 재시도 로직 구현
    for attempt in range(max_retries):
        try:
            # API 서버 부하 방지를 위한 지연 시간 추가 (config 값 사용)
            time.sleep(request_delay)
            
            # 헤더와 타임아웃 설정을 config에서 가져옴
            resp = requests.get(
                url, 
                params=params, 
                headers=headers,
                timeout=timeout
            )
            resp.raise_for_status()
            data = resp.json()
            
            # 결과가 있는지 확인
            if data.get("result") and len(data["result"]) > 0:
                original_result = data["result"][0]
                
                # 결과 데이터 추출
                col_id = original_result.get("id", "-")
                
                # 상태 정보는 usage 내부에 있을 수 있음
                status = original_result.get("status", "unknown")
                if status == "unknown" and "usage" in original_result:
                    usage_status = original_result["usage"].get("status", "unknown")
                    if usage_status != "unknown":
                        status = usage_status
                        print(f"[Debug COL API] status를 usage에서 추출: {status}")
                
                print(f"[Debug COL API] 최종 status: {status} for {scientific_name}")
                
                # 학명 정보 추출 (이름 구조는 dict일 수 있음)
                name_info = original_result.get("name", scientific_name)
                if isinstance(name_info, dict):
                    # "name" 필드가 딕셔너리인 경우, "scientificName" 또는 "name" 키를 찾음
                    final_name = name_info.get("scientificName", name_info.get("name", scientific_name))
                else:
                    # "name" 필드가 문자열인 경우
                    final_name = name_info
                
                # COL 웹사이트 URL 생성
                col_url = f"https://www.catalogueoflife.org/data/taxon/{col_id}" if col_id != "-" else "-"
                
                # 검증 상태 결정 (중요: is_verified 필드 추가)
                is_verified = status.lower() in ['accepted', 'provisionally accepted'] if status else False
                verification_status = "Accepted" if status == "accepted" else status.capitalize() if isinstance(status, str) else "Unknown"
                
                # 결과 구조 생성 (백엔드 형식에 맞춤)
                display_result = {
                    "query": scientific_name,
                    "input_name": scientific_name,  # 백엔드 형식
                    "matched": True,  # type: "EXACT"를 사용했으므로 매칭 성공으로 설정
                    "학명": final_name, # UI 표시용
                    "scientific_name": final_name,  # 백엔드 형식
                    "is_verified": is_verified,  # 중요: 검증 상태 추가
                    "검증": verification_status, # UI 표시용
                    "status": status,  # 백엔드 형식
                    "COL 상태": status,  # UI 표시용
                    "COL ID": col_id,
                    "col_id": col_id,  # 백엔드 형식
                    "COL URL": col_url,
                    "col_url": col_url,  # 백엔드 형식
                    "심층분석 결과": "-",
                    "original_data": original_result # 수정된 원본 데이터
                }
                return display_result
            else:
                # 매칭 결과가 없을 경우
                return {
                    "query": scientific_name,
                    "input_name": scientific_name,  # 백엔드 형식
                    "matched": False,
                    "학명": scientific_name,  # UI 표시용
                    "scientific_name": scientific_name,  # 백엔드 형식
                    "is_verified": False,  # 매칭 실패는 검증 실패
                    "검증": "Unknown",  # UI 표시용
                    "status": "not found",  # 백엔드 형식
                    "COL 상태": "-",  # UI 표시용
                    "COL ID": "-",
                    "col_id": "-",  # 백엔드 형식
                    "COL URL": "-",
                    "col_url": "-",  # 백엔드 형식
                    "심층분석 결과": "-"
                }
                
        except requests.exceptions.HTTPError as http_err:
            # HTTP 에러 처리
            error_message = f"{http_err.response.status_code} {http_err.response.reason}"
            print(f"[Error COL API] HTTP error occurred (attempt {attempt + 1}/{max_retries}): {error_message} for query: {scientific_name}")
            
            # 마지막 시도가 아니면 재시도
            if attempt < max_retries - 1:
                print(f"[Info COL API] Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                continue
            else:
                return {
                    "query": scientific_name, "input_name": scientific_name, "matched": False, "error": error_message,
                    "학명": scientific_name, "scientific_name": scientific_name, "is_verified": False,
                    "검증": "Error", "status": "error", "COL 상태": f"오류: {error_message}",
                    "COL ID": "-", "col_id": "-", "COL URL": "-", "col_url": "-", "심층분석 결과": "-"
                }
                
        except requests.exceptions.RequestException as req_err:
            # 네트워크 관련 에러 처리
            error_message = f"네트워크 오류: {str(req_err)}"
            print(f"[Error COL API] Network error occurred (attempt {attempt + 1}/{max_retries}): {error_message} for query: {scientific_name}")
            
            # 마지막 시도가 아니면 재시도
            if attempt < max_retries - 1:
                print(f"[Info COL API] Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                continue
            else:
                return {
                    "query": scientific_name, "input_name": scientific_name, "matched": False, "error": error_message,
                    "학명": scientific_name, "scientific_name": scientific_name, "is_verified": False,
                    "검증": "Network Error", "status": "network_error", "COL 상태": f"네트워크 오류: {str(req_err)}",
                    "COL ID": "-", "col_id": "-", "COL URL": "-", "col_url": "-", "심층분석 결과": "-"
                }
                
        except Exception as e:
            # 기타 에러 처리
            error_message = f"일반 오류: {str(e)}"
            print(f"[Error COL API] General error occurred (attempt {attempt + 1}/{max_retries}): {error_message} for query: {scientific_name}")
            
            # 마지막 시도가 아니면 재시도
            if attempt < max_retries - 1:
                print(f"[Info COL API] Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                continue
            else:
                return {
                    "query": scientific_name, "input_name": scientific_name, "matched": False, "error": error_message,
                    "학명": scientific_name, "scientific_name": scientific_name, "is_verified": False,
                    "검증": "Error", "status": "error", "COL 상태": f"오류: {str(e)}",
                    "COL ID": "-", "col_id": "-", "COL URL": "-", "col_url": "-", "심층분석 결과": "-"
                }
    
    # 모든 재시도가 실패한 경우 (여기까지 도달하지 않아야 함)
    return {
        "query": scientific_name, "input_name": scientific_name, "matched": False, "error": "모든 재시도 실패",
        "학명": scientific_name, "scientific_name": scientific_name, "is_verified": False,
        "검증": "Error", "status": "retry_failed", "COL 상태": "모든 재시도 실패",
        "COL ID": "-", "col_id": "-", "COL URL": "-", "col_url": "-", "심층분석 결과": "-"
    } 