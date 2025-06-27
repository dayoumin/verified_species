"""
네트워크 연결 디버깅 스크립트

기관 네트워크에서 API 접속이 차단되는 원인을 파악하기 위한 테스트 도구
"""
import requests
import sys
import os
import socket
import ssl
import urllib.parse
from datetime import datetime

def test_basic_connectivity():
    """기본 인터넷 연결 테스트"""
    print("=" * 60)
    print("1. 기본 인터넷 연결 테스트")
    print("=" * 60)
    
    test_sites = [
        "https://www.google.com",
        "https://www.naver.com",
        "https://httpbin.org/get"
    ]
    
    for site in test_sites:
        try:
            response = requests.get(site, timeout=10)
            print(f"✅ {site}: {response.status_code}")
        except Exception as e:
            print(f"❌ {site}: {str(e)}")

def test_api_endpoints():
    """API 엔드포인트 연결 테스트"""
    print("\n" + "=" * 60)
    print("2. API 엔드포인트 연결 테스트")
    print("=" * 60)
    
    endpoints = [
        "https://api.catalogueoflife.org",
        "https://www.marinespecies.org/rest",
        "https://ko.wikipedia.org/w/api.php"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(endpoint, timeout=15)
            print(f"✅ {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint}: {str(e)}")

def test_with_different_headers():
    """다양한 헤더로 COL API 테스트"""
    print("\n" + "=" * 60)
    print("3. 다양한 헤더로 COL API 테스트")
    print("=" * 60)
    
    url = "https://api.catalogueoflife.org/nameusage/search"
    params = {"q": "Homo sapiens", "limit": 1, "type": "EXACT"}
    
    # 다양한 User-Agent 테스트
    user_agents = [
        # 현재 설정
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        # 간단한 User-Agent
        "SpeciesVerifier/1.0",
        # Python requests 기본값
        f"python-requests/{requests.__version__}",
        # 없음
        None
    ]
    
    for i, ua in enumerate(user_agents):
        print(f"\n3-{i+1}. User-Agent: {ua or '없음'}")
        headers = {}
        if ua:
            headers['User-Agent'] = ua
            
        try:
            response = requests.get(url, params=params, headers=headers, timeout=15)
            print(f"✅ 성공: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                result_count = len(data.get('result', []))
                print(f"   결과 개수: {result_count}")
        except Exception as e:
            print(f"❌ 실패: {str(e)}")

def test_proxy_settings():
    """프록시 설정 테스트"""
    print("\n" + "=" * 60)
    print("4. 프록시 설정 테스트")
    print("=" * 60)
    
    # 시스템 프록시 설정 확인
    print("4-1. 시스템 프록시 설정:")
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
    for var in proxy_vars:
        value = os.environ.get(var)
        print(f"   {var}: {value or '설정되지 않음'}")
    
    # requests 세션의 프록시 설정 확인
    session = requests.Session()
    print(f"\n4-2. requests 세션 프록시: {session.proxies}")
    
    # 프록시 없이 테스트
    print("\n4-3. 프록시 비활성화하고 COL API 테스트:")
    url = "https://api.catalogueoflife.org/nameusage/search"
    params = {"q": "Homo sapiens", "limit": 1}
    
    try:
        # 프록시 완전 비활성화
        response = requests.get(
            url, 
            params=params, 
            proxies={'http': None, 'https': None},
            timeout=15
        )
        print(f"✅ 프록시 없이 성공: {response.status_code}")
    except Exception as e:
        print(f"❌ 프록시 없이 실패: {str(e)}")

def test_ssl_verification():
    """SSL 인증서 검증 테스트"""
    print("\n" + "=" * 60)
    print("5. SSL 인증서 검증 테스트")
    print("=" * 60)
    
    url = "https://api.catalogueoflife.org/nameusage/search"
    params = {"q": "Homo sapiens", "limit": 1}
    
    # SSL 검증 활성화
    print("5-1. SSL 검증 활성화:")
    try:
        response = requests.get(url, params=params, verify=True, timeout=15)
        print(f"✅ SSL 검증 활성화 성공: {response.status_code}")
    except Exception as e:
        print(f"❌ SSL 검증 활성화 실패: {str(e)}")
    
    # SSL 검증 비활성화 (보안상 권장하지 않음)
    print("\n5-2. SSL 검증 비활성화:")
    try:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        response = requests.get(url, params=params, verify=False, timeout=15)
        print(f"✅ SSL 검증 비활성화 성공: {response.status_code}")
    except Exception as e:
        print(f"❌ SSL 검증 비활성화 실패: {str(e)}")

def test_dns_resolution():
    """DNS 해상도 테스트"""
    print("\n" + "=" * 60)
    print("6. DNS 해상도 테스트")
    print("=" * 60)
    
    domains = [
        "api.catalogueoflife.org",
        "www.marinespecies.org",
        "ko.wikipedia.org"
    ]
    
    for domain in domains:
        try:
            ip = socket.gethostbyname(domain)
            print(f"✅ {domain}: {ip}")
        except Exception as e:
            print(f"❌ {domain}: {str(e)}")

def test_port_connectivity():
    """포트 연결 테스트"""
    print("\n" + "=" * 60)
    print("7. 포트 연결 테스트")
    print("=" * 60)
    
    hosts = [
        ("api.catalogueoflife.org", 443),
        ("www.marinespecies.org", 443),
        ("ko.wikipedia.org", 443)
    ]
    
    for host, port in hosts:
        try:
            sock = socket.create_connection((host, port), timeout=10)
            sock.close()
            print(f"✅ {host}:{port} - 연결 성공")
        except Exception as e:
            print(f"❌ {host}:{port} - 연결 실패: {str(e)}")

def test_full_api_call():
    """실제 API 호출 테스트 (species_verifier 설정 사용)"""
    print("\n" + "=" * 60)
    print("8. 실제 API 호출 테스트 (현재 설정)")
    print("=" * 60)
    
    try:
        # species_verifier 설정 가져오기
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from species_verifier.config import api_config
        from species_verifier.core.col_api import verify_col_species
        
        print("8-1. 설정값 확인:")
        print(f"   REQUEST_TIMEOUT: {api_config.REQUEST_TIMEOUT}")
        print(f"   MAX_RETRIES: {api_config.MAX_RETRIES}")
        print(f"   REQUEST_DELAY: {api_config.REQUEST_DELAY}")
        print(f"   USER_AGENT: {api_config.USER_AGENT[:50]}...")
        
        print("\n8-2. COL API 호출 테스트:")
        result = verify_col_species("Homo sapiens")
        
        if result.get('matched'):
            print(f"✅ API 호출 성공!")
            print(f"   학명: {result.get('학명')}")
            print(f"   상태: {result.get('COL 상태')}")
            print(f"   ID: {result.get('COL ID')}")
        else:
            print(f"❌ API 호출 실패: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ 설정 로드 또는 API 호출 중 오류: {str(e)}")

def main():
    """메인 실행 함수"""
    print(f"Species Verifier 네트워크 디버깅 도구")
    print(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python 버전: {sys.version}")
    print(f"requests 버전: {requests.__version__}")
    
    # 모든 테스트 실행
    test_basic_connectivity()
    test_api_endpoints()
    test_with_different_headers()
    test_proxy_settings()
    test_ssl_verification()
    test_dns_resolution()
    test_port_connectivity()
    test_full_api_call()
    
    print("\n" + "=" * 60)
    print("테스트 완료!")
    print("=" * 60)
    print("\n문제 해결 방법:")
    print("1. 프록시 설정이 있다면 IT 부서에 화이트리스트 요청")
    print("2. User-Agent 차단이 의심된다면 다른 User-Agent 시도")
    print("3. SSL 인증서 문제가 있다면 기관 인증서 설치 필요")
    print("4. 특정 도메인 차단이라면 IT 부서에 접근 권한 요청")
    print("5. 모든 HTTPS 연결이 실패한다면 방화벽 설정 확인 필요")

if __name__ == "__main__":
    main() 