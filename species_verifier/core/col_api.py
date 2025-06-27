import requests
import time
from typing import Dict, Any
from species_verifier.config import api_config, ENTERPRISE_CONFIG
import random
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from species_verifier.utils.logger import get_logger

def create_robust_session():
    """브라우저와 유사한 자연스러운 네트워크 세션 생성"""
    logger = get_logger()
    logger.debug("네트워크 세션 초기화 중...")
    
    session = requests.Session()
    
    # 안정적인 연결 설정
    pool_settings = ENTERPRISE_CONFIG["connection_pool_settings"]
    adapter = HTTPAdapter(
        pool_connections=pool_settings["pool_connections"],
        pool_maxsize=pool_settings["pool_maxsize"],
        pool_block=pool_settings["pool_block"]
    )
    
    # 적절한 재시도 전략 (서버 부담 고려)
    retry_config = ENTERPRISE_CONFIG["enhanced_retry"]
    retry_strategy = Retry(
        total=3,  # 적절한 재시도 횟수
        backoff_factor=1.5,  # 적절한 백오프 계수
        status_forcelist=retry_config["status_forcelist"],
        allowed_methods=retry_config["allowed_methods"]
    )
    
    adapter.max_retries = retry_strategy
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # 시스템 프록시 설정 자동 감지 (브라우저와 동일)
    session.trust_env = True
    
    # 기업 환경 SSL 처리 (브라우저와 동일한 방식)
    try:
        import ssl
        import certifi
        # 시스템 인증서 저장소 사용 (브라우저와 동일)
        session.verify = certifi.where()
        logger.debug("시스템 SSL 인증서 사용")
    except ImportError:
        # certifi가 없는 경우 시스템 기본값 사용
        logger.debug("기본 SSL 설정 사용")
    
    logger.debug("네트워크 세션 준비 완료")
    return session

def try_with_different_user_agents(url, params, session, timeout):
    """브라우저와 유사한 방식으로 API 요청 (SSL 오류 해결)"""
    logger = get_logger()
    user_agents = ENTERPRISE_CONFIG["fallback_user_agents"]
    
    # SSL 설정 옵션들 (브라우저 수준)
    ssl_configs = [
        {'verify': True},   # 기본 SSL 검증
        {'verify': False}   # SSL 검증 비활성화 (기업 환경 대응)
    ]
    
    # 각 SSL 설정과 User-Agent 조합으로 시도
    for ssl_idx, ssl_config in enumerate(ssl_configs):
        for ua_idx, user_agent in enumerate(user_agents):
            try:
                config_desc = "SSL검증" if ssl_config['verify'] else "SSL우회"
                logger.debug(f"네트워크 요청 시도: {config_desc} + UA{ua_idx+1}")
                
                headers = api_config.DEFAULT_HEADERS.copy()
                headers['User-Agent'] = user_agent
                
                # 일반적인 브라우저 요청 간격
                if ssl_idx > 0 or ua_idx > 0:
                    delay = random.uniform(0.3, 0.8)
                    time.sleep(delay)
                
                # SSL 경고 숨기기 (기업 환경에서 일반적)
                if not ssl_config['verify']:
                    import urllib3
                    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                
                response = session.get(
                    url, 
                    params=params, 
                    headers=headers, 
                    timeout=timeout,
                    **ssl_config
                )
                response.raise_for_status()
                
                logger.debug(f"API 요청 성공: {config_desc}")
                return response
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 403:
                    logger.debug(f"접근 제한: {config_desc}")
                    continue
                elif e.response.status_code == 429:
                    logger.debug(f"요청 빈도 제한: {config_desc}")
                    time.sleep(1.0)
                    continue
                else:
                    logger.debug(f"HTTP 오류 {e.response.status_code}: {config_desc}")
                    continue
            except Exception as e:
                logger.debug(f"연결 오류: {config_desc} - {type(e).__name__}")
                continue
    
    # 모든 시도 실패
    raise Exception("네트워크 연결 실패")

def verify_col_species(scientific_name: str) -> Dict[str, Any]:
    """
    COL 글로벌 API를 이용해 학명 검증 결과를 반환합니다.
    기관 네트워크 환경에 최적화된 강화된 버전입니다.
    
    Args:
        scientific_name (str): 검증할 학명
        
    Returns:
        Dict[str, Any]: 검증 결과를 담은 딕셔너리
    """
    url = "https://api.catalogueoflife.org/nameusage/search"
    params = {"q": scientific_name, "limit": 1, "type": "EXACT"}
    
    # config 값 안전하게 처리
    if api_config is not None:
        timeout = api_config.COL_REQUEST_TIMEOUT
    else:
        timeout = 30
        print("[Warning COL API] api_config가 None이므로 기본값 사용")

    # 강화된 세션 생성
    session = create_robust_session()
    
    try:
        logger = get_logger()
        logger.debug(f"학명 검증 요청: {scientific_name}")
        
        # 브라우저와 유사한 방식으로 API 호출
        resp = try_with_different_user_agents(url, params, session, timeout)
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
                    logger.debug(f"status를 usage에서 추출: {status}")
            
            logger.debug(f"검증 완료: {scientific_name} -> {status}")
            
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
                "심층분석 결과": "준비 중 (DeepSearch 기능 개발 예정)",
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
                "심층분석 결과": "준비 중 (DeepSearch 기능 개발 예정)"
            }
            
    except Exception as e:
        # 연결 실패시 오류 반환
        logger = get_logger()
        error_message = f"네트워크 오류: {str(e)}"
        logger.warning(f"학명 검증 실패: {scientific_name} - {type(e).__name__}")
        
        return {
            "query": scientific_name, 
            "input_name": scientific_name, 
            "matched": False, 
            "error": error_message,
            "학명": scientific_name, 
            "scientific_name": scientific_name, 
            "is_verified": False,
            "검증": "Network Error", 
            "status": "network_error", 
            "COL 상태": f"네트워크 오류: {str(e)}",
            "COL ID": "-", 
            "col_id": "-", 
            "COL URL": "-", 
            "col_url": "-", 
            "심층분석 결과": "준비 중 (DeepSearch 기능 개발 예정)"
        }
    finally:
        # 세션 정리
        session.close() 