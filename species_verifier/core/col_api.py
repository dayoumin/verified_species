import requests
import time
from typing import Dict, Any
from species_verifier.config import api_config, ENTERPRISE_CONFIG, SSL_CONFIG
import random
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from species_verifier.utils.logger import get_logger

def create_robust_session():
    """기관 네트워크 환경에 최적화된 강화된 세션 생성"""
    session = requests.Session()
    logger = get_logger()
    
    # 안전한 설정 접근
    try:
        pool_settings = ENTERPRISE_CONFIG.get("connection_pool_settings", {
            "pool_connections": 3,
            "pool_maxsize": 5,
            "pool_block": True
        })
    except Exception as e:
        logger.warning(f"connection_pool_settings 설정 오류: {e}")
        pool_settings = {"pool_connections": 3, "pool_maxsize": 5, "pool_block": True}
    
    try:
        retry_config = ENTERPRISE_CONFIG.get("enhanced_retry", {
            "backoff_factor": 2.0,
            "status_forcelist": [429, 500, 502, 503, 504],
            "allowed_methods": ["GET", "POST"]
        })
    except Exception as e:
        logger.warning(f"enhanced_retry 설정 오류: {e}")
        retry_config = {
            "backoff_factor": 2.0,
            "status_forcelist": [429, 500, 502, 503, 504],
            "allowed_methods": ["GET", "POST"]
        }
    
    # 연결 풀 설정 (안정성 우선)
    retry_strategy = Retry(
        total=api_config.MAX_RETRIES,
        backoff_factor=retry_config["backoff_factor"],
        status_forcelist=retry_config["status_forcelist"],
        allowed_methods=retry_config["allowed_methods"]
    )
    
    adapter = HTTPAdapter(
        max_retries=retry_strategy,
        pool_connections=pool_settings["pool_connections"],
        pool_maxsize=pool_settings["pool_maxsize"],
        pool_block=pool_settings["pool_block"]
    )
    
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # 시스템 프록시 설정 사용 (보안 정책 준수)
    session.trust_env = True
    
    # SSL 인증서 검증 강화 (브라우저 수준)
    try:
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
    """브라우저와 유사한 방식으로 API 요청 (보안 강화)"""
    logger = get_logger()
    
    # fallback_user_agents를 안전하게 접근
    try:
        user_agents = ENTERPRISE_CONFIG.get("fallback_user_agents", [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0"
        ])
    except Exception as e:
        logger.warning(f"fallback_user_agents 설정 오류: {e}")
        user_agents = [api_config.USER_AGENT]
    
    # SSL 설정 가져오기 (보안 우선)
    from species_verifier.config import SSL_CONFIG
    
    # SSL 설정 옵션들 (보안 우선 순서)
    ssl_configs = [
        {'verify': True, 'description': 'SSL 검증 활성화'}   # 항상 먼저 시도
    ]
    
    # 기업 환경 지원이 활성화된 경우에만 SSL 우회 옵션 추가
    if SSL_CONFIG.get("allow_insecure_fallback", False):
        ssl_configs.append({
            'verify': False, 
            'description': 'SSL 검증 우회 (기업 환경 지원)'
        })
    
    # 각 SSL 설정과 User-Agent 조합으로 시도
    for ssl_idx, ssl_config in enumerate(ssl_configs):
        for ua_idx, user_agent in enumerate(user_agents):
            try:
                config_desc = ssl_config['description']
                logger.debug(f"네트워크 요청 시도: {config_desc} + UA{ua_idx+1}")
                
                headers = api_config.DEFAULT_HEADERS.copy()
                headers['User-Agent'] = user_agent
                
                # 일반적인 브라우저 요청 간격
                if ssl_idx > 0 or ua_idx > 0:
                    delay = random.uniform(0.3, 0.8)
                    time.sleep(delay)
                
                # SSL 우회 사용 시 조용히 처리
                if not ssl_config['verify']:
                    # urllib3 경고 비활성화 (콘솔 정리용)
                    import urllib3
                    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                
                response = session.get(
                    url, 
                    params=params, 
                    headers=headers, 
                    timeout=timeout,
                    verify=ssl_config['verify']
                )
                response.raise_for_status()
                
                # 연결 성공 - 조용히 처리
                
                return response
                
            except requests.exceptions.SSLError as e:
                logger.debug(f"SSL 오류: {config_desc} - {str(e)[:100]}...")
                continue
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
    raise Exception("네트워크 연결 실패 - 모든 보안 연결 방법 시도 후 실패")

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
    try:
        timeout = api_config.COL_REQUEST_TIMEOUT if api_config is not None else 30
    except Exception:
        timeout = 30
        print("[Warning COL API] api_config 접근 오류, 기본값 사용")

    # 강화된 세션 생성
    session = None
    try:
        session = create_robust_session()
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
            
    except KeyError as e:
        # KeyError 구체적으로 처리
        logger = get_logger()
        error_message = f"설정 키 오류: {str(e)}"
        logger.warning(f"학명 검증 실패 (KeyError): {scientific_name} - {str(e)}")
        
        return {
            "query": scientific_name, 
            "input_name": scientific_name, 
            "matched": False, 
            "error": error_message,
            "학명": scientific_name, 
            "scientific_name": scientific_name, 
            "is_verified": False,
            "검증": "Configuration Error", 
            "status": "config_error", 
            "COL 상태": f"설정 오류: {str(e)}",
            "COL ID": "-", 
            "col_id": "-", 
            "COL URL": "-", 
            "col_url": "-", 
            "심층분석 결과": "준비 중 (DeepSearch 기능 개발 예정)"
        }
    except Exception as e:
        # 일반 예외 처리
        logger = get_logger()
        error_message = f"네트워크 오류: {str(e)}"
        logger.warning(f"학명 검증 실패: {scientific_name} - {type(e).__name__}: {str(e)}")
        
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
        if session:
            try:
                session.close()
            except Exception:
                pass  # 세션 정리 실패는 무시 