"""
기관 네트워크 환경용 검증 시스템

기존 verifier 모듈을 기관 네트워크 보안 정책에 맞게 래핑합니다:
- SSL 인증서 인터셉션 대응
- 프록시 서버 자동 설정
- 패킷 검사 및 DPI 우회
- 기관 친화적 API 호출 패턴
- LPSN 웹 스크래핑 지원 (API 아님)
"""

import time
import json
from typing import Dict, Any, Optional, List
from ..database.enterprise_network import get_enterprise_adapter
from .lpsn_scraper import verify_microbe_lpsn_scraping
from . import verifier

class EnterpriseWoRMSVerifier:
    """기관 네트워크용 WoRMS 검증기"""
    
    def __init__(self):
        self.adapter = get_enterprise_adapter()
        self.base_url = "https://www.marinespecies.org/rest"
        
    def check_worms_record_safe(self, scientific_name: str) -> Optional[Dict[str, Any]]:
        """기관 네트워크 안전 WoRMS 검증"""
        try:
            print(f"[Info] WoRMS 검증 시작 (기관 네트워크): {scientific_name}")
            
            # AphiaID 조회
            search_url = f"{self.base_url}/AphiaIDByName/{scientific_name}"
            
            response = self.adapter.safe_api_call(
                url=search_url,
                method='GET',
                params={'marine_only': 'false'}
            )
            
            if not response or response.status_code != 200:
                print(f"[Warning] WoRMS AphiaID 조회 실패: {scientific_name}")
                return None
            
            try:
                aphia_id = response.json()
            except json.JSONDecodeError:
                print(f"[Error] WoRMS 응답 JSON 파싱 실패")
                return None
            
            if not aphia_id:
                print(f"[Info] WoRMS에서 종을 찾을 수 없음: {scientific_name}")
                return {
                    'scientific_name': scientific_name,
                    'status': 'not_found',
                    'source': 'worms',
                    'worms_id': None
                }
            
            # 상세 정보 조회
            time.sleep(1.5)  # 기관 네트워크에서는 더 보수적인 간격
            
            detail_url = f"{self.base_url}/AphiaRecordByAphiaID/{aphia_id}"
            detail_response = self.adapter.safe_api_call(
                url=detail_url,
                method='GET'
            )
            
            if not detail_response or detail_response.status_code != 200:
                print(f"[Warning] WoRMS 상세 정보 조회 실패")
                return {
                    'scientific_name': scientific_name,
                    'status': 'partial',
                    'source': 'worms',
                    'worms_id': aphia_id
                }
            
            try:
                detail_data = detail_response.json()
            except json.JSONDecodeError:
                print(f"[Error] WoRMS 상세 정보 JSON 파싱 실패")
                return None
            
            # 결과 데이터 구성
            result = {
                'scientific_name': detail_data.get('scientificname', scientific_name),
                'status': 'valid' if detail_data.get('status') == 'accepted' else 'invalid',
                'source': 'worms',
                'worms_id': aphia_id,
                'valid_name': detail_data.get('valid_name'),
                'classification': {
                    'kingdom': detail_data.get('kingdom'),
                    'phylum': detail_data.get('phylum'),
                    'class': detail_data.get('class'),
                    'order': detail_data.get('order'),
                    'family': detail_data.get('family'),
                    'genus': detail_data.get('genus')
                },
                'rank': detail_data.get('rank'),
                'authority': detail_data.get('authority'),
                'last_updated': detail_data.get('modified'),
                'enterprise_network': True  # 기관 네트워크에서 조회됨을 표시
            }
            
            print(f"[Info] WoRMS 검증 완료 (기관 네트워크): {result['status']}")
            return result
            
        except Exception as e:
            print(f"[Error] WoRMS 검증 중 오류 (기관 네트워크): {e}")
            return None

class EnterpriseLPSNAPIClient:
    """
    기관 네트워크용 LPSN API 클라이언트 클래스
    
    ✅ LPSN API 장점:
    - 공식 RESTful API 지원 (https://api.lpsn.dsmz.de)
    - JSON 형식의 구조화된 데이터
    - 안정적이고 효율적인 접근
    - 기관 네트워크에서 허용될 가능성 높음
    - 웹 스크래핑보다 훨씬 안정적
    """
    
    def __init__(self):
        self.adapter = get_enterprise_adapter()
        self.api_base_url = "https://api.lpsn.dsmz.de"
        
        # API 인증 정보 (환경변수에서 로드)
        import os
        self.username = os.getenv('LPSN_USERNAME')
        self.password = os.getenv('LPSN_PASSWORD')
        
        if not self.username or not self.password:
            print("[Warning] LPSN API 인증 정보 없음 (LPSN_USERNAME, LPSN_PASSWORD 환경변수 설정 필요)")
        else:
            print("[Info] LPSN API 클라이언트 초기화 완료")
        
        # 세션 관리
        self.session_cookies = None
        self.session_expires = 0
        
    def _ensure_api_session(self) -> bool:
        """LPSN API 세션 확보"""
        try:
            import time
            current_time = time.time()
            
            # 기존 세션이 유효한 경우
            if self.session_cookies and current_time < self.session_expires:
                return True
            
            # 인증 정보 확인
            if not self.username or not self.password:
                return False
            
            # API 로그인
            login_url = f"{self.api_base_url}/login"
            login_data = {
                'username': self.username,
                'password': self.password
            }
            
            response = self.adapter.safe_api_call(
                url=login_url,
                method='POST',
                data=login_data,
                timeout=30
            )
            
            if response and response.status_code == 200:
                self.session_cookies = response.cookies
                self.session_expires = current_time + 3600  # 1시간 유효
                print("[Info] LPSN API 세션 생성 성공")
                return True
            else:
                print(f"[Error] LPSN API 로그인 실패: {response.status_code if response else 'No response'}")
                return False
                
        except Exception as e:
            print(f"[Error] LPSN API 세션 생성 오류: {e}")
            return False
        
    def verify_microbe_lpsn_safe(self, scientific_name: str) -> Optional[Dict[str, Any]]:
        """
        기관 네트워크 안전 LPSN API 조회
        
        ✅ API 방식 장점:
        - 공식 지원으로 안정적
        - JSON 응답으로 파싱 간단
        - 기관 네트워크에서 허용 가능성 높음
        """
        try:
            print(f"[Info] LPSN API 조회 시작 (기관 네트워크): {scientific_name}")
            
            # 학명을 속명과 종명으로 분리
            parts = scientific_name.strip().split()
            if len(parts) < 2:
                print(f"[Warning] 잘못된 학명 형식: {scientific_name}")
                return None
            
            genus = parts[0]
            species = parts[1]
            
            # API 세션 확보
            if not self._ensure_api_session():
                print("[Error] LPSN API 세션 생성 실패")
                return {
                    'scientific_name': scientific_name,
                    'status': 'api_auth_failed',
                    'source': 'lpsn_api',
                    'error': 'API 인증 실패 - 환경변수 확인 필요',
                    'enterprise_network': True
                }
            
            # Advanced Search API 호출
            search_url = f"{self.api_base_url}/advanced_search"
            params = {
                'genus': genus,
                'species_epithet': species,
                'page': 1
            }
            
            import time
            time.sleep(0.5)  # API 호출 간격
            
            response = self.adapter.safe_api_call(
                url=search_url,
                method='GET',
                params=params,
                cookies=self.session_cookies,
                timeout=30
            )
            
            if not response or response.status_code != 200:
                print(f"[Warning] LPSN API 검색 실패: {response.status_code if response else 'No response'}")
                return {
                    'scientific_name': scientific_name,
                    'status': 'api_failed',
                    'source': 'lpsn_api',
                    'error': f'API 호출 실패: {response.status_code if response else "네트워크 오류"}',
                    'enterprise_network': True
                }
            
            try:
                search_data = response.json()
            except json.JSONDecodeError:
                print("[Error] LPSN API 응답 JSON 파싱 실패")
                return None
            
            # 검색 결과 확인
            results = search_data.get('results', [])
            if not results:
                print(f"[Info] LPSN API 검색 결과 없음: {scientific_name}")
                return {
                    'scientific_name': scientific_name,
                    'status': 'not_found',
                    'source': 'lpsn_api',
                    'enterprise_network': True
                }
            
            # 첫 번째 결과의 상세 정보 조회
            first_result = results[0]
            lpsn_id = first_result.get('id')
            
            if not lpsn_id:
                print("[Warning] LPSN ID가 없음")
                return None
            
            # Detail API 호출
            time.sleep(0.5)  # API 호출 간격
            detail_url = f"{self.api_base_url}/fetch/{lpsn_id}"
            
            detail_response = self.adapter.safe_api_call(
                url=detail_url,
                method='GET',
                cookies=self.session_cookies,
                timeout=30
            )
            
            if not detail_response or detail_response.status_code != 200:
                print(f"[Warning] LPSN API 상세 조회 실패")
                return None
            
            try:
                detail_data = detail_response.json()
            except json.JSONDecodeError:
                print("[Error] LPSN API 상세 응답 JSON 파싱 실패")
                return None
            
            # API 응답 데이터 처리
            if isinstance(detail_data, list) and len(detail_data) > 0:
                api_record = detail_data[0]
            else:
                api_record = detail_data
            
            # 결과 데이터 구성
            result = {
                'scientific_name': api_record.get('full_name', scientific_name),
                'status': 'valid' if api_record.get('validly_published') else 'invalid',
                'source': 'lpsn_api',
                'lpsn_id': api_record.get('id'),
                'authors': api_record.get('authority', ''),
                'nomenclatural_status': api_record.get('nomenclatural_status', ''),
                'category': api_record.get('category', ''),
                'url': api_record.get('lpsn_address', ''),
                'type_strain': ', '.join(api_record.get('type_strain_names', [])) if api_record.get('type_strain_names') else None,
                'is_legitimate': api_record.get('is_legitimate', True),
                'enterprise_network': True,
                'api_method': True
            }
            
            print(f"[Info] LPSN API 조회 성공 (기관 네트워크): {result['status']}")
            return result
            
        except Exception as e:
            print(f"[Error] LPSN API 조회 중 오류 (기관 네트워크): {e}")
            return {
                'scientific_name': scientific_name,
                'status': 'error',
                'source': 'lpsn_api',
                'error': str(e),
                'enterprise_network': True,
                'api_method': True
            }

class EnterpriseSupabaseConnector:
    """기관 네트워크용 Supabase 연결기"""
    
    def __init__(self, supabase_url: str, supabase_key: str):
        self.adapter = get_enterprise_adapter()
        self.base_url = supabase_url.rstrip('/')
        self.headers = {
            'apikey': supabase_key,
            'Authorization': f'Bearer {supabase_key}',
            'Content-Type': 'application/json',
            'Prefer': 'return=minimal'  # 응답 크기 최소화
        }
        
    def safe_query(self, table: str, method: str = 'GET', 
                   params: Dict = None, data: Dict = None) -> Optional[Dict[str, Any]]:
        """기관 네트워크 안전 Supabase 쿼리"""
        try:
            url = f"{self.base_url}/rest/v1/{table}"
            
            # 헤더에 기관 네트워크 식별 정보 추가
            headers = self.headers.copy()
            headers['X-Client-Info'] = 'SpeciesVerifier-Enterprise/1.5'
            
            kwargs = {
                'headers': headers,
                'timeout': (30, 90)  # Supabase는 더 긴 타임아웃
            }
            
            if params:
                kwargs['params'] = params
            if data:
                kwargs['json'] = data
            
            response = self.adapter.safe_api_call(url, method, **kwargs)
            
            if response and response.status_code in [200, 201]:
                try:
                    return response.json()
                except json.JSONDecodeError:
                    print("[Error] Supabase 응답 JSON 파싱 실패")
                    return None
            else:
                status_code = response.status_code if response else "No Response"
                print(f"[Warning] Supabase 쿼리 실패: {status_code}")
                return None
                
        except Exception as e:
            print(f"[Error] Supabase 연결 오류 (기관 네트워크): {e}")
            return None

def get_enterprise_worms_verifier() -> EnterpriseWoRMSVerifier:
    """기관 네트워크용 WoRMS 검증기 인스턴스"""
    return EnterpriseWoRMSVerifier()

def get_enterprise_lpsn_client() -> EnterpriseLPSNAPIClient:
    """기관 네트워크용 LPSN API 클라이언트 인스턴스"""
    return EnterpriseLPSNAPIClient()

def create_enterprise_supabase_connector(url: str, key: str) -> EnterpriseSupabaseConnector:
    """기관 네트워크용 Supabase 연결기 생성"""
    return EnterpriseSupabaseConnector(url, key)

# 기존 모듈 함수들을 기관 네트워크용으로 래핑
def check_worms_record_enterprise(scientific_name: str) -> Optional[Dict[str, Any]]:
    """기관 네트워크 안전 WoRMS 검증 (기존 함수 호환)"""
    verifier_instance = get_enterprise_worms_verifier()
    return verifier_instance.check_worms_record_safe(scientific_name)

def verify_single_microbe_lpsn_enterprise(scientific_name: str) -> Optional[Dict[str, Any]]:
    """
    기관 네트워크 안전 LPSN 검증 (기존 함수 호환)
    
    ✅ LPSN API 방식으로 업데이트됨!
    - 안정적이고 효율적인 공식 API 사용
    - 기관 네트워크에서 허용될 가능성 높음
    - 구조화된 JSON 데이터 제공
    """
    client_instance = get_enterprise_lpsn_client()
    return client_instance.verify_microbe_lpsn_safe(scientific_name)

# 하위 호환성을 위한 별칭
get_enterprise_lpsn_scraper = get_enterprise_lpsn_client
EnterpriseLPSNScraper = EnterpriseLPSNAPIClient 