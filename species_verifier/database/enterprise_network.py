"""
기관 네트워크 환경 대응 모듈

기관 인터넷망에서 발생할 수 있는 보안 정책 이슈를 해결합니다:
1. SSL 인증서 임시 발급 및 인터셉션 대응
2. 프록시 서버 자동 감지 및 설정
3. 패킷 검사 및 DPI 우회
4. 화이트리스트 기반 접근 제어 대응
5. 기관 친화적 API 호출 패턴
"""

import os
import ssl
import socket
import urllib3
import certifi
import requests
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse
import logging

# 기관 네트워크에서는 과도한 로깅 방지
logging.getLogger("urllib3").setLevel(logging.WARNING)

class EnterpriseNetworkAdapter:
    """기관 네트워크 환경 대응 어댑터"""
    
    def __init__(self):
        self.proxy_config = self._detect_proxy_settings()
        self.ssl_config = self._setup_ssl_configuration()
        self.user_agent = self._get_enterprise_user_agent()
        
        # 기관 네트워크 설정
        self.timeout_config = {
            'connect_timeout': 30,  # 기관 네트워크는 연결이 느릴 수 있음
            'read_timeout': 60,     # 패킷 검사로 인한 지연 고려
            'retry_attempts': 3,    # 네트워크 불안정성 대응
            'retry_delay': 2.0      # 재시도 간격
        }
        
        print(f"[Info] 기관 네트워크 어댑터 초기화 완료")
        print(f"  프록시 감지: {'설정됨' if self.proxy_config else '없음'}")
        print(f"  SSL 검증: {'기관 정책 적용' if self.ssl_config.get('verify') else '우회 모드'}")
    
    def _detect_proxy_settings(self) -> Optional[Dict[str, str]]:
        """프록시 설정 자동 감지"""
        proxy_config = {}
        
        # 환경 변수에서 프록시 설정 확인
        proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
        for var in proxy_vars:
            proxy_url = os.getenv(var)
            if proxy_url:
                if var.lower().startswith('http'):
                    proxy_config['http'] = proxy_url
                else:
                    proxy_config['https'] = proxy_url
        
        # Windows 시스템 프록시 설정 확인 (레지스트리)
        if not proxy_config and os.name == 'nt':
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                   r"Software\Microsoft\Windows\CurrentVersion\Internet Settings") as key:
                    proxy_enable = winreg.QueryValueEx(key, "ProxyEnable")[0]
                    if proxy_enable:
                        proxy_server = winreg.QueryValueEx(key, "ProxyServer")[0]
                        if proxy_server:
                            proxy_config['http'] = f"http://{proxy_server}"
                            proxy_config['https'] = f"http://{proxy_server}"
            except Exception as e:
                print(f"[Warning] Windows 프록시 설정 감지 실패: {e}")
        
        return proxy_config if proxy_config else None
    
    def _setup_ssl_configuration(self) -> Dict[str, Any]:
        """기관 SSL 정책에 맞는 SSL 설정"""
        ssl_config = {
            'verify': True,  # 기본적으로는 검증 활성화
            'cert_bundle': certifi.where(),  # 표준 인증서 번들
            'ssl_context': None
        }
        
        # 기관 네트워크 SSL 우회 모드 (환경 변수로 제어)
        if os.getenv('SPECIES_VERIFIER_SSL_BYPASS', 'false').lower() == 'true':
            print("[Warning] SSL 검증 우회 모드 활성화 (기관 정책에 따라)")
            ssl_config['verify'] = False
            # SSL 경고 억제 (기관 환경에서는 의도된 설정)
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # 기관 인증서 경로 설정 (있는 경우)
        enterprise_ca_path = os.getenv('ENTERPRISE_CA_BUNDLE')
        if enterprise_ca_path and os.path.exists(enterprise_ca_path):
            ssl_config['cert_bundle'] = enterprise_ca_path
            print(f"[Info] 기관 인증서 번들 사용: {enterprise_ca_path}")
        
        # SSL 컨텍스트 생성 (고급 설정)
        try:
            context = ssl.create_default_context()
            
            # 기관 네트워크에서 흔히 사용하는 설정
            context.check_hostname = ssl_config['verify']
            context.verify_mode = ssl.CERT_REQUIRED if ssl_config['verify'] else ssl.CERT_NONE
            
            # TLS 버전 설정 (기관 정책에 따라)
            min_tls_version = os.getenv('MIN_TLS_VERSION', '1.2')
            if min_tls_version == '1.3':
                context.minimum_version = ssl.TLSVersion.TLSv1_3
            elif min_tls_version == '1.2':
                context.minimum_version = ssl.TLSVersion.TLSv1_2
            
            ssl_config['ssl_context'] = context
            
        except Exception as e:
            print(f"[Warning] SSL 컨텍스트 생성 실패: {e}")
        
        return ssl_config
    
    def _get_enterprise_user_agent(self) -> str:
        """기관 친화적 User-Agent 생성"""
        # 일반적인 브라우저처럼 보이도록 설정 (DPI 우회)
        base_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        
        # 기관에서 허용하는 애플리케이션처럼 보이도록
        enterprise_ua = os.getenv('ENTERPRISE_USER_AGENT', 
                                 f"{base_ua} SpeciesVerifier/1.4 (Enterprise)")
        
        return enterprise_ua
    
    def create_session(self) -> requests.Session:
        """기관 네트워크 최적화된 requests 세션 생성"""
        session = requests.Session()
        
        # 프록시 설정
        if self.proxy_config:
            session.proxies.update(self.proxy_config)
            print(f"[Info] 프록시 설정 적용: {list(self.proxy_config.keys())}")
        
        # SSL 설정
        session.verify = self.ssl_config['verify']
        if not self.ssl_config['verify']:
            session.verify = False
        elif self.ssl_config['cert_bundle']:
            session.verify = self.ssl_config['cert_bundle']
        
        # 헤더 설정 (기관 친화적)
        session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',  # Do Not Track (프라이버시 고려)
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # 타임아웃 설정 (어댑터 레벨에서)
        adapter = requests.adapters.HTTPAdapter(
            max_retries=urllib3.util.Retry(
                total=self.timeout_config['retry_attempts'],
                backoff_factor=self.timeout_config['retry_delay'],
                status_forcelist=[500, 502, 503, 504, 429]  # 재시도할 HTTP 상태 코드
            )
        )
        
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        
        return session
    
    def safe_api_call(self, url: str, method: str = 'GET', 
                      **kwargs) -> Optional[requests.Response]:
        """기관 네트워크 안전 API 호출"""
        session = self.create_session()
        
        # 기본 타임아웃 적용
        if 'timeout' not in kwargs:
            kwargs['timeout'] = (
                self.timeout_config['connect_timeout'],
                self.timeout_config['read_timeout']
            )
        
        # 민감한 로깅 방지 (기관 보안 정책)
        sanitized_url = self._sanitize_url_for_logging(url)
        
        try:
            print(f"[Info] API 호출: {method} {sanitized_url}")
            
            response = session.request(method, url, **kwargs)
            
            # 응답 상태 확인
            if response.status_code == 200:
                print(f"[Info] API 호출 성공: {response.status_code}")
                return response
            elif response.status_code in [403, 407]:
                print(f"[Warning] 접근 권한 문제: {response.status_code} - 기관 정책 확인 필요")
            elif response.status_code in [502, 503]:
                print(f"[Warning] 프록시/게이트웨이 오류: {response.status_code}")
            else:
                print(f"[Warning] API 호출 실패: {response.status_code}")
            
            return response
            
        except requests.exceptions.SSLError as e:
            print(f"[Error] SSL 인증서 오류: {e}")
            print("  기관 인증서 설정을 확인하거나 SSL_BYPASS 모드를 고려하세요")
            return None
            
        except requests.exceptions.ProxyError as e:
            print(f"[Error] 프록시 연결 오류: {e}")
            print("  프록시 설정을 확인하거나 네트워크 관리자에게 문의하세요")
            return None
            
        except requests.exceptions.Timeout as e:
            print(f"[Error] 연결 타임아웃: {e}")
            print("  기관 네트워크 지연 또는 방화벽 정책을 확인하세요")
            return None
            
        except requests.exceptions.ConnectionError as e:
            print(f"[Error] 연결 오류: {e}")
            return None
            
        except Exception as e:
            print(f"[Error] 예기치 못한 오류: {e}")
            return None
        
        finally:
            session.close()
    
    def _sanitize_url_for_logging(self, url: str) -> str:
        """로깅용 URL 정리 (API 키 등 민감정보 제거)"""
        try:
            parsed = urlparse(url)
            # API 키나 토큰이 포함된 쿼리 파라미터 마스킹
            if parsed.query:
                # 간단한 마스킹 (실제로는 더 정교한 방법 사용 가능)
                return f"{parsed.scheme}://{parsed.netloc}{parsed.path}?[PARAMS_MASKED]"
            else:
                return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        except:
            return "[URL_MASKED]"
    
    def check_network_connectivity(self) -> Dict[str, Any]:
        """기관 네트워크 연결성 테스트"""
        test_results = {
            'proxy_detected': bool(self.proxy_config),
            'ssl_bypass_mode': not self.ssl_config['verify'],
            'internet_access': False,
            'api_endpoints': {}
        }
        
        # 기본 인터넷 연결 테스트
        try:
            response = self.safe_api_call('https://httpbin.org/get', timeout=10)
            test_results['internet_access'] = response is not None and response.status_code == 200
        except:
            test_results['internet_access'] = False
        
        # API 엔드포인트별 테스트
        api_endpoints = {
            'supabase': 'https://supabase.com',
            'worms': 'https://www.marinespecies.org',
            'lpsn': 'https://lpsn.dsmz.de'
        }
        
        for name, url in api_endpoints.items():
            try:
                response = self.safe_api_call(url, timeout=15)
                test_results['api_endpoints'][name] = {
                    'accessible': response is not None,
                    'status_code': response.status_code if response else None
                }
            except Exception as e:
                test_results['api_endpoints'][name] = {
                    'accessible': False,
                    'error': str(e)
                }
        
        return test_results
    
    def get_enterprise_recommendations(self) -> List[str]:
        """기관 네트워크 관리자를 위한 권장사항"""
        recommendations = []
        
        if not self.proxy_config:
            recommendations.append(
                "✅ 프록시 설정이 감지되지 않았습니다. 직접 연결이 가능한 환경입니다."
            )
        else:
            recommendations.append(
                "📋 프록시 서버를 통한 연결이 감지되었습니다. 프록시 정책을 확인하세요."
            )
        
        if not self.ssl_config['verify']:
            recommendations.append(
                "⚠️ SSL 검증 우회 모드입니다. 보안 정책에 따라 활성화되었는지 확인하세요."
            )
        
        recommendations.extend([
            "📋 허용할 도메인: *.supabase.co, *.marinespecies.org, *.dsmz.de",
            "📋 필요한 포트: 443 (HTTPS), 80 (HTTP - 리다이렉트용)",
            "📋 User-Agent 허용: SpeciesVerifier/1.4 (Enterprise)",
            "📋 API 호출 패턴: 1-3초 간격의 정상적인 REST API 호출",
            "⚠️ 대용량 데이터 전송은 없으며, JSON 응답만 처리합니다",
            "🔒 민감한 정보: API 키는 헤더로만 전송, 로그에 기록하지 않음"
        ])
        
        return recommendations

# 전역 기관 네트워크 어댑터
enterprise_adapter = None

def get_enterprise_adapter() -> EnterpriseNetworkAdapter:
    """기관 네트워크 어댑터 인스턴스 반환"""
    global enterprise_adapter
    if enterprise_adapter is None:
        enterprise_adapter = EnterpriseNetworkAdapter()
    return enterprise_adapter

def patch_requests_for_enterprise():
    """기존 requests 호출을 기관 네트워크용으로 패치"""
    adapter = get_enterprise_adapter()
    
    # 기존 requests.get, requests.post 등을 래핑
    original_request = requests.request
    
    def enterprise_request(method, url, **kwargs):
        """기관 네트워크 최적화된 requests 래퍼"""
        session = adapter.create_session()
        
        # 기본 타임아웃 적용
        if 'timeout' not in kwargs:
            kwargs['timeout'] = (30, 60)
        
        try:
            return session.request(method, url, **kwargs)
        finally:
            session.close()
    
    # 원본 함수 대체 (옵션)
    if os.getenv('ENTERPRISE_REQUESTS_PATCH', 'false').lower() == 'true':
        requests.request = enterprise_request
        print("[Info] requests 라이브러리를 기관 네트워크용으로 패치했습니다")

# 초기화 시 자동 패치 (환경 변수로 제어)
if os.getenv('AUTO_ENTERPRISE_PATCH', 'false').lower() == 'true':
    patch_requests_for_enterprise() 