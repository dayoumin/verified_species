import google.generativeai as genai
import os
import json
import re
from dotenv import load_dotenv

# 설정 로드 - 이 부분을 주석 처리하거나 삭제합니다.
# load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash") # 모델 이름도 .env 또는 기본값 사용

# Gemini 클라이언트 초기화 (스크립트 시작 시 한 번만)
try:
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        # print("Gemini 클라이언트 초기화 성공.")  # 디버그 로그 제거
except Exception as e:
    pass  # 예외 처리 블록 유지를 위한 빈 코드 블록
    # 필요시 여기서 exit() 대신 None 반환 또는 예외 발생 처리

def format_worms_result_with_gemini(input_name, worms_result):
    """WoRMS 결과를 바탕으로 Gemini를 사용하여 학명 정보를 요약하고 구조화된 데이터를 반환합니다."""
    # 기본 반환 구조 (오류 발생 시 사용)
    error_return = lambda status, conclusion, raw: {
        "gemini_status": status,
        "gemini_valid_name_info": "",
        "gemini_rank": worms_result.get('rank', '정보 없음') if worms_result else "",
        "gemini_conclusion": conclusion, # 최종 요약 또는 오류 메시지
        "raw_gemini_response": raw
    }

    if not GEMINI_API_KEY:
        return error_return("API 키 없음", "Gemini API 키가 설정되지 않았습니다.", "Gemini API 키 없음")

    if not worms_result or not isinstance(worms_result, dict):
        # WoRMS 결과가 없거나 형식이 잘못된 경우
        status = worms_result.get('status', '정보 없음') if isinstance(worms_result, dict) else "WoRMS 결과 없음"
        return error_return(
            "WoRMS 정보 없음",
            f"'{input_name}'에 대한 WoRMS 정보를 조회하지 못했거나 형식이 올바르지 않습니다.",
            f"입력된 WoRMS 결과: {worms_result}"
        )

    # WoRMS 결과에서 정보 추출 (실패 대비 기본값 설정)
    status = worms_result.get('status', '정보 없음')
    valid_name = worms_result.get('valid_name', '정보 없음')
    rank = worms_result.get('rank', '정보 없음')
    aphia_id = worms_result.get('AphiaID', '정보 없음')
    worms_url = worms_result.get('url', '정보 없음')

    # 프롬프트 생성 (이전과 동일)
    prompt = f"""
다음은 WoRMS 데이터베이스에서 '{input_name}'(으)로 조회한 학명 정보입니다:
- AphiaID: {aphia_id}
- 상태(Status): {status}
- 유효 학명(Valid Name): {valid_name}
- 분류 계급(Rank): {rank}
- WoRMS 상세 정보 링크: {worms_url}

이 정보를 바탕으로, '{input_name}'의 학명 유효성 검사 결과를 사용자가 이해하기 쉽게 한국어로 설명해주세요.
결과는 다음 키(key)를 포함하는 JSON 형식으로 반환해주세요. 각 값은 한국어 문자열이어야 합니다:
- "status_description": [상태 정보를 자연스러운 한국어로 설명. 예: '현재 유효한 학명입니다.', '유효하지 않은 학명(동의어)입니다.', '분류학적 상태가 불확실합니다.' 등]
- "valid_name_info": [만약 상태가 'unaccepted'이고 유효 학명이 다르다면, 유효 학명을 명시. 예: '현재 인정되는 학명은 '{valid_name}'입니다.' 상태가 'accepted'이면 빈 문자열("") 반환]
- "rank": "{rank}" [분류 계급 그대로 반환]
- "conclusion": [결론적으로 이 학명이 현재 사용해도 되는 이름인지, 아니면 다른 이름을 사용해야 하는지를 명확히 언급하는 문장]

JSON 형식 예시:
{{
  "status_description": "현재 유효한 학명입니다.",
  "valid_name_info": "",
  "rank": "Species",
  "conclusion": "현재 사용 가능한 유효한 학명입니다."
}}
"""

    try:
        model = genai.GenerativeModel(GEMINI_MODEL_NAME)
        response = model.generate_content(prompt)
        raw_response_text = response.text
        # print(f"[Debug Gemini Raw Response '{input_name}']: {raw_response_text[:200]}...") # 필요시 주석 해제

        # 응답에서 JSON 추출 시도
        json_string = None
        gemini_conclusion = "Gemini 응답 처리 실패 (결론 추출 불가)" # 기본 실패 메시지
        gemini_status_desc = "Gemini 응답 처리 실패"
        gemini_valid_name = ""
        gemini_rank = rank # 기본값은 WoRMS rank

        # 1. 마크다운 코드 블록 찾기
        match = re.search(r"```json\s*(\{.*?\})\s*```", raw_response_text, re.DOTALL | re.IGNORECASE)
        if match:
            json_string = match.group(1)
        else:
            # 2. 코드 블록 없으면 전체 텍스트에서 중괄호로 둘러싸인 패턴 찾기
            match = re.search(r"(\{.*?\})", raw_response_text, re.DOTALL)
            if match:
                json_string = match.group(1)

        # JSON 파싱 및 값 추출 시도
        if json_string:
            try:
                gemini_data = json.loads(json_string)
                gemini_status_desc = gemini_data.get("status_description", gemini_status_desc) # 파싱 성공 시 값 업데이트
                gemini_valid_name = gemini_data.get("valid_name_info", "")
                gemini_rank = gemini_data.get("rank", rank)
                gemini_conclusion = gemini_data.get("conclusion", gemini_conclusion) # conclusion 추출 시도

                # conclusion이 여전히 기본 실패 메시지면 다른 필드 조합 시도 (예시)
                if gemini_conclusion == "Gemini 응답 처리 실패 (결론 추출 불가)":
                    gemini_conclusion = f"{gemini_status_desc}. {gemini_valid_name}" if gemini_valid_name else gemini_status_desc

            except json.JSONDecodeError as e:
                # JSON 파싱 실패 시
                gemini_conclusion = "Gemini 응답 JSON 파싱 실패"
                gemini_status_desc = "Gemini 응답 JSON 파싱 실패"
                # print(f"[Warning Gemini] JSON parsing failed for '{input_name}': {e}") # 필요시 주석 해제
        else:
            # JSON 형식 못 찾음
            gemini_conclusion = "Gemini 응답 형식 오류 (JSON 없음)"
            gemini_status_desc = "Gemini 응답 형식 오류 (JSON 없음)"
            # print(f"[Warning Gemini] JSON format not found in response for '{input_name}'") # 필요시 주석 해제

        # 최종 결과 반환 (항상 모든 키 포함)
        return {
            "gemini_status": gemini_status_desc,
            "gemini_valid_name_info": gemini_valid_name,
            "gemini_rank": gemini_rank,
            "gemini_conclusion": gemini_conclusion.strip(), # 최종 요약/오류 (앞뒤 공백 제거)
            "raw_gemini_response": raw_response_text
        }

    except Exception as e:
        # print(f"Gemini API 호출 중 오류 발생 ({input_name}): {e}") # 로그 제거
        # API 호출 자체 실패 시
        return error_return("Gemini API 호출 실패", f"Gemini API 연동 실패: {e}", f"Gemini API 호출 실패: {e}")

# Wikipedia 정보 요약 함수 (나중에 external_data.py로 이동 고려)
# def summarize_wikipedia_info_with_gemini(species_name):
#     # TODO: Wikipedia API 또는 라이브러리 사용하여 정보 검색
#     # TODO: 검색된 정보를 바탕으로 Gemini에게 요약 요청 prompt 생성
#     # TODO: Gemini API 호출 및 결과 반환
#     pass