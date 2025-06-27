"""
기업 네트워크 환경 API 클라이언트 템플릿

이 모듈은 향후 프로젝트에서 복사해서 사용할 수 있는
기업 네트워크 친화적 API 클라이언트 템플릿입니다.

사용법:
1. 이 파일을 새 프로젝트로 복사
2. 필요에 따라 커스터마이징
3. requirements.txt에 필수 패키지 추가

필수 패키지:
- requests
- urllib3
- certifi
"""

import requests
import urllib3
import random
import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

class EnterpriseAPIClient:
    """
    기업 네트워크 환경에 최적화된 API 클라이언트
    
    특징:
    - 브라우저 수준 SSL 처리 (SSL검증 → SSL우회 순차 시도)
    - 시스템 프록시 설정 자동 준수
    - 자연스러운 User-Agent 및 헤더 사용
    - 보안 친화적 로깅
    """
    
    def __init__(self, log_file: Optional[str] = None):
        """
        Args:
            log_file: 로그 파일 경로 (None이면 자동 생성)
        """
        self.session = self._create_session()
        self.logger = self._setup_logging(log_file)
        
        # 실제 브라우저 User-Agent 목록
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        
        self.logger.info("Enterprise API Client 초기화 완료")
    
    def _setup_logging(self, log_file: Optional[str] = None) -> logging.Logger:
        """보안 친화적 로깅 설정"""
        if log_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = f"api_client_{timestamp}.log"
        
        logger = logging.getLogger('enterprise_api_client')
        logger.setLevel(logging.DEBUG)
        
        # 기존 핸들러 제거
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # 파일 핸들러
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        logger.info(f"로그 파일: {log_file}")
        return logger
    
    def _create_session(self) -> requests.Session:
        """브라우저와 유사한 세션 생성"""
        session = requests.Session()
        
        # 시스템 프록시 설정 자동 감지 (브라우저와 동일)
        session.trust_env = True
        
        # 연결 풀 최적화 (브라우저 수준)
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=5,
            pool_maxsize=10,
            pool_block=True
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _get_browser_headers(self, user_agent: str) -> Dict[str, str]:
        """브라우저와 유사한 헤더 생성"""
        return {
            'User-Agent': user_agent,
            'Accept': 'application/json, text/html, */*',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    def api_request(self, 
                   url: str, 
                   method: str = 'GET',
                   params: Optional[Dict] = None, 
                   data: Optional[Dict] = None,
                   json_data: Optional[Dict] = None,
                   timeout: int = 30) -> requests.Response:
        """
        기업 환경에 최적화된 API 요청
        
        Args:
            url: 요청 URL
            method: HTTP 메서드 ('GET', 'POST', 'PUT', 'DELETE' 등)
            params: URL 파라미터
            data: 폼 데이터
            json_data: JSON 데이터
            timeout: 타임아웃 (초)
            
        Returns:
            requests.Response 객체
            
        Raises:
            Exception: 모든 연결 시도 실패시
        """
        self.logger.debug(f"API 요청: {method} {url}")
        
        # SSL 설정 옵션 (브라우저 수준)
        ssl_configs = [
            {'verify': True},   # 표준 SSL 검증
            {'verify': False}   # 기업 환경 대응
        ]
        
        # 각 SSL 설정과 User-Agent 조합으로 시도
        for ssl_idx, ssl_config in enumerate(ssl_configs):
            for ua_idx, user_agent in enumerate(self.user_agents):
                try:
                    config_desc = "SSL검증" if ssl_config['verify'] else "SSL우회"
                    self.logger.debug(f"시도: {config_desc} + UA{ua_idx+1}")
                    
                    # 자연스러운 요청 간격
                    if ssl_idx > 0 or ua_idx > 0:
                        delay = random.uniform(0.3, 0.8)
                        time.sleep(delay)
                    
                    # SSL 경고 숨기기 (기업 환경에서 일반적)
                    if not ssl_config['verify']:
                        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                    
                    headers = self._get_browser_headers(user_agent)
                    
                    # 요청 실행
                    response = self.session.request(
                        method=method,
                        url=url,
                        params=params,
                        data=data,
                        json=json_data,
                        headers=headers,
                        timeout=timeout,
                        **ssl_config
                    )
                    response.raise_for_status()
                    
                    self.logger.debug(f"API 요청 성공: {config_desc}")
                    return response
                    
                except requests.exceptions.SSLError:
                    self.logger.debug(f"SSL 오류: {config_desc}")
                    if ssl_config['verify']:
                        continue  # 다음 설정으로 시도
                    else:
                        raise
                except requests.exceptions.HTTPError as e:
                    self.logger.debug(f"HTTP 오류 {e.response.status_code}: {config_desc}")
                    if e.response.status_code in [403, 429]:
                        continue  # 다른 User-Agent로 시도
                    else:
                        raise
                except Exception as e:
                    self.logger.debug(f"연결 오류: {config_desc} - {type(e).__name__}")
                    continue
        
        # 모든 시도 실패
        error_msg = "모든 연결 시도 실패"
        self.logger.error(error_msg)
        raise Exception(error_msg)
    
    def get_json(self, url: str, params: Optional[Dict] = None, timeout: int = 30) -> Dict[str, Any]:
        """JSON 응답을 반환하는 GET 요청"""
        response = self.api_request(url, 'GET', params=params, timeout=timeout)
        return response.json()
    
    def post_json(self, url: str, data: Dict[str, Any], timeout: int = 30) -> Dict[str, Any]:
        """JSON 데이터를 전송하고 JSON 응답을 반환하는 POST 요청"""
        response = self.api_request(url, 'POST', json_data=data, timeout=timeout)
        return response.json()
    
    def close(self):
        """리소스 정리"""
        self.session.close()
        self.logger.info("API 클라이언트 종료")


# 사용 예시
def example_usage():
    """사용 예시"""
    
    # 1. 클라이언트 생성
    client = EnterpriseAPIClient()
    
    try:
        # 2. GET 요청 (JSON 응답)
        result = client.get_json(
            "https://api.catalogueoflife.org/nameusage/search",
            params={"q": "Homo sapiens", "limit": 1}
        )
        print("검색 결과:", result)
        
        # 3. POST 요청 (JSON 데이터 전송)
        # post_result = client.post_json(
        #     "https://api.example.com/submit",
        #     data={"name": "test", "value": 123}
        # )
        
        # 4. 커스텀 요청
        response = client.api_request(
            "https://httpbin.org/get",
            method='GET',
            params={"test": "value"}
        )
        print("응답 상태:", response.status_code)
        
    except Exception as e:
        print(f"오류 발생: {e}")
    
    finally:
        # 5. 리소스 정리
        client.close()


if __name__ == "__main__":
    example_usage() 