"""
Supabase 클라이언트 설정 및 연결 관리

이 모듈은 Supabase 데이터베이스 연결을 관리하고 기본 설정을 제공합니다.
"""
import os
from typing import Optional
from supabase import create_client, Client
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

class SupabaseClient:
    """Supabase 클라이언트 관리 클래스"""
    
    def __init__(self):
        self._client: Optional[Client] = None
        self._url = os.getenv("SUPABASE_URL")
        self._key = os.getenv("SUPABASE_ANON_KEY")
        
    @property
    def client(self) -> Client:
        """Supabase 클라이언트 인스턴스 반환 (싱글톤 패턴)"""
        if self._client is None:
            if not self._url or not self._key:
                raise ValueError(
                    "Supabase 연결 정보가 설정되지 않았습니다. "
                    ".env 파일에 SUPABASE_URL과 SUPABASE_ANON_KEY를 설정해주세요."
                )
            
            self._client = create_client(self._url, self._key)
            print(f"[Info] Supabase 클라이언트 연결 성공: {self._url}")
            
        return self._client
    
    def test_connection(self) -> bool:
        """데이터베이스 연결 테스트"""
        try:
            # 간단한 쿼리로 연결 테스트
            result = self.client.table("verification_sessions").select("count", count="exact").execute()
            print(f"[Info] Supabase 연결 테스트 성공")
            return True
        except Exception as e:
            print(f"[Error] Supabase 연결 테스트 실패: {e}")
            return False

# 전역 클라이언트 인스턴스
supabase_client = SupabaseClient()

def get_supabase_client() -> Client:
    """Supabase 클라이언트 인스턴스 반환"""
    return supabase_client.client 