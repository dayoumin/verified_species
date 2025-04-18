import requests
import json # Import json for JSONDecodeError if not using requests' specific one
from requests.exceptions import RequestException, JSONDecodeError
import time
import os
from dotenv import load_dotenv

# 설정 로드 (core 모듈 내에서도 필요할 수 있음)
# load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '..', '.env')) # 프로젝트 루트의 .env 로드

WORMS_BASE_URL = os.getenv("WORMS_BASE_URL", "https://www.marinespecies.org/rest") # 기본값 설정
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 30))
API_DELAY = float(os.getenv("API_DELAY", 0.5))

def get_aphia_id(scientific_name):
    """주어진 학명으로 WoRMS에서 AphiaID를 조회합니다."""
    aphia_id = None # 변수 초기화
    try:
        time.sleep(API_DELAY)
        encoded_name = requests.utils.quote(scientific_name)
        url = f"{WORMS_BASE_URL}/AphiaIDByName/{encoded_name}?marine_only=false"
        print(f"[Debug WoRMS API] Requesting AphiaID: {url}") # 요청 URL 로그 추가
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        print(f"[Debug WoRMS API] Response Status (AphiaID for '{scientific_name}'): {response.status_code}") # 상태 코드 로그 추가
        # print(f"[Debug WoRMS API] Response Content (AphiaID for '{scientific_name}'): {response.text[:100]}...") # 내용 로그 (필요시 주석 해제)

        response.raise_for_status() # HTTP 오류 발생 시 예외 발생

        if not response.content or response.status_code == 204: # No content
             print(f"[Debug WoRMS API] No content received for AphiaID '{scientific_name}'.") # 로그 추가
             aphia_id = {"error": "WoRMS 응답 없음 (AphiaID)"}
        else:
            aphia_id_data = response.json()
            print(f"[Debug WoRMS API] Parsed JSON (AphiaID for '{scientific_name}'): {aphia_id_data}") # 파싱된 JSON 로그 추가
            if isinstance(aphia_id_data, int) and aphia_id_data == -999:
                aphia_id = {"error": "유효하지 않은 학명 (WoRMS)"}
            elif isinstance(aphia_id_data, list) and len(aphia_id_data) > 0 and isinstance(aphia_id_data[0], int):
                aphia_id = aphia_id_data[0]
            elif isinstance(aphia_id_data, int):
                aphia_id = aphia_id_data
            else:
                print(f"[Warning WoRMS API] Unexpected response format (AphiaID for {scientific_name}): {aphia_id_data}") # 경고 로그
                aphia_id = {"error": "WoRMS 예상치 못한 응답 형식 (AphiaID)"}

    except RequestException as e:
        print(f"[Error WoRMS API] Network error during AphiaID request for '{scientific_name}': {e}") # 상세 오류 로그
        aphia_id = {"error": f"WoRMS 네트워크 오류 (AphiaID): {e}"}
    except JSONDecodeError as e:
        print(f"[Error WoRMS API] JSON parsing error during AphiaID request for '{scientific_name}': {e}") # 상세 오류 로그
        print(f"[Error WoRMS API] Raw response text: {response.text[:200]}...") # 원본 텍스트 로그 추가
        aphia_id = {"error": f"WoRMS 응답 파싱 오류 (AphiaID): {e}"}
    except Exception as e:
        import traceback
        print(f"[Error WoRMS API] Unexpected error during AphiaID request for '{scientific_name}': {e}") # 상세 오류 로그
        print(traceback.format_exc()) # 스택 트레이스 출력
        aphia_id = {"error": f"WoRMS 예상치 못한 오류 (AphiaID): {e}"}

    print(f"[Debug WoRMS API] Returning for AphiaID '{scientific_name}': {aphia_id}") # 최종 반환 값 로그 추가
    return aphia_id

def get_aphia_record(aphia_id):
    """주어진 AphiaID로 WoRMS에서 상세 레코드를 조회합니다."""
    record = None # 변수 초기화
    if not isinstance(aphia_id, int) or aphia_id <= 0: # 유효한 ID인지 먼저 확인 (-999 등 제외)
        print(f"[Debug WoRMS API] Invalid AphiaID provided for record lookup: {aphia_id}") # 로그 추가
        # 유효하지 않은 ID에 대해서는 None 대신 오류 딕셔너리 반환 고려 가능
        # return {"error": "유효하지 않은 AphiaID 제공됨"}
        return None # 일단 None 반환 유지
    try:
        time.sleep(API_DELAY)
        url = f"{WORMS_BASE_URL}/AphiaRecordByAphiaID/{aphia_id}"
        print(f"[Debug WoRMS API] Requesting AphiaRecord: {url}") # 요청 URL 로그 추가
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        print(f"[Debug WoRMS API] Response Status (AphiaRecord for {aphia_id}): {response.status_code}") # 상태 코드 로그 추가
        # print(f"[Debug WoRMS API] Response Content (AphiaRecord for {aphia_id}): {response.text[:100]}...") # 내용 로그 (필요시 주석 해제)

        response.raise_for_status()

        if not response.content or response.status_code == 204:
            print(f"[Debug WoRMS API] No content received for AphiaRecord {aphia_id}. B") # 로그 추가
            record = {"error": f"WoRMS 응답 없음 (AphiaRecord: {aphia_id})"}
        else:
            record_data = response.json()
            print(f"[Debug WoRMS API] Parsed JSON (AphiaRecord for {aphia_id}): {record_data}") # 파싱된 JSON 로그 추가
            record = record_data # 파싱 성공 시 데이터 할당

    except RequestException as e:
        print(f"[Error WoRMS API] Network error during AphiaRecord request for AphiaID {aphia_id}: {e}") # 상세 오류 로그
        record = {"error": f"WoRMS 네트워크 오류 (AphiaRecord): {e}"}
    except JSONDecodeError as e:
        print(f"[Error WoRMS API] JSON parsing error during AphiaRecord request for AphiaID {aphia_id}: {e}") # 상세 오류 로그
        print(f"[Error WoRMS API] Raw response text: {response.text[:200]}...") # 원본 텍스트 로그 추가
        record = {"error": f"WoRMS 응답 파싱 오류 (AphiaRecord): {e}"}
    except Exception as e:
        import traceback
        print(f"[Error WoRMS API] Unexpected error during AphiaRecord request for AphiaID {aphia_id}: {e}") # 상세 오류 로그
        print(traceback.format_exc()) # 스택 트레이스 출력
        record = {"error": f"WoRMS 예상치 못한 오류 (AphiaRecord): {e}"}

    print(f"[Debug WoRMS API] Returning for AphiaRecord {aphia_id}: {record}") # 최종 반환 값 로그 추가
    return record