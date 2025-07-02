"""
Supabase 데이터베이스 서비스 함수

이 모듈은 Species Verifier 앱의 데이터베이스 CRUD 작업을 담당합니다.
"""
import time
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import uuid4

from .supabase_client import get_supabase_client
from .models import (
    VerificationSession, VerificationResult, UserFavorite, 
    VerificationStats, ApiUsageLog, VerificationType, SessionStatus
)
from ..models.verification_results import (
    MarineVerificationResult, MicrobeVerificationResult, VerificationSummary
)

class DatabaseService:
    """데이터베이스 서비스 클래스"""
    
    def __init__(self):
        self.client = get_supabase_client()
    
    # === 검증 세션 관리 ===
    
    async def create_session(
        self, 
        session_name: str, 
        verification_type: VerificationType,
        user_id: Optional[str] = None
    ) -> str:
        """새 검증 세션 생성"""
        session_data = {
            "session_name": session_name,
            "verification_type": verification_type.value,
            "user_id": user_id,
            "start_time": datetime.now().isoformat(),
            "status": SessionStatus.RUNNING.value
        }
        
        result = self.client.table("verification_sessions").insert(session_data).execute()
        session_id = result.data[0]["id"]
        print(f"[Info] 새 검증 세션 생성: {session_id}")
        return session_id
    
    def create_session_sync(
        self, 
        session_name: str, 
        verification_type: VerificationType,
        user_id: Optional[str] = None
    ) -> str:
        """새 검증 세션 생성 (동기 버전)"""
        session_data = {
            "session_name": session_name,
            "verification_type": verification_type.value,
            "user_id": user_id,
            "start_time": datetime.now().isoformat(),
            "status": SessionStatus.RUNNING.value
        }
        
        result = self.client.table("verification_sessions").insert(session_data).execute()
        session_id = result.data[0]["id"]
        print(f"[Info] 새 검증 세션 생성: {session_id}")
        return session_id
    
    def update_session_status(
        self, 
        session_id: str, 
        status: SessionStatus,
        error_message: Optional[str] = None
    ):
        """세션 상태 업데이트"""
        update_data = {
            "status": status.value,
            "updated_at": datetime.now().isoformat()
        }
        
        if status == SessionStatus.COMPLETED:
            update_data["end_time"] = datetime.now().isoformat()
            
        if error_message:
            update_data["error_message"] = error_message
            
        self.client.table("verification_sessions").update(update_data).eq("id", session_id).execute()
        print(f"[Info] 세션 상태 업데이트: {session_id} -> {status.value}")
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """세션 정보 조회"""
        result = self.client.table("verification_sessions").select("*").eq("id", session_id).execute()
        return result.data[0] if result.data else None
    
    # === 검증 결과 관리 ===
    
    def save_verification_results(
        self, 
        session_id: str, 
        results: List[Dict[str, Any]], 
        verification_type: VerificationType
    ):
        """검증 결과 배치 저장"""
        db_results = []
        
        for result in results:
            db_result = {
                "session_id": session_id,
                "input_name": result.get("input_name", ""),
                "scientific_name": result.get("scientific_name", ""),
                "korean_name": result.get("korean_name", ""),
                "verification_type": verification_type.value,
                "is_verified": result.get("is_verified", False),
                "verification_status": result.get("worms_status") or result.get("status", ""),
                "wiki_summary": result.get("wiki_summary", "준비 중 (DeepSearch 기능 개발 예정)"),
                "created_at": datetime.now().isoformat()
            }
            
            # 검증 타입별 특수 필드 처리
            if verification_type == VerificationType.MARINE:
                db_result.update({
                    "worms_id": result.get("worms_id"),
                    "worms_status": result.get("worms_status"),
                    "worms_link": result.get("worms_link") or result.get("worms_url"),
                    "mapped_name": result.get("mapped_name")
                })
            elif verification_type == VerificationType.MICROBE:
                db_result.update({
                    "valid_name": result.get("valid_name"),
                    "taxonomy": result.get("taxonomy"),
                    "lpsn_link": result.get("lpsn_link"),
                    "is_microbe": result.get("is_microbe", False)
                })
            elif verification_type == VerificationType.COL:
                db_result.update({
                    "col_id": result.get("col_id"),
                    "col_status": result.get("col_status"),
                    "col_rank": result.get("col_rank")
                })
            
            db_results.append(db_result)
        
        # 배치 삽입
        if db_results:
            self.client.table("verification_results").insert(db_results).execute()
            print(f"[Info] {len(db_results)}개 검증 결과 저장 완료")
    
    def get_verification_results(
        self, 
        session_id: str, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """세션의 검증 결과 조회"""
        result = self.client.table("verification_results").select("*").eq("session_id", session_id).limit(limit).execute()
        return result.data
    
    # === 사용자 즐겨찾기 관리 ===
    
    def add_to_favorites(
        self, 
        user_id: str, 
        scientific_name: str, 
        korean_name: Optional[str] = None,
        verification_type: VerificationType = VerificationType.MARINE,
        notes: Optional[str] = None
    ):
        """즐겨찾기에 추가"""
        favorite_data = {
            "user_id": user_id,
            "scientific_name": scientific_name,
            "korean_name": korean_name,
            "verification_type": verification_type.value,
            "notes": notes
        }
        
        self.client.table("user_favorites").insert(favorite_data).execute()
        print(f"[Info] 즐겨찾기 추가: {scientific_name}")
    
    def get_user_favorites(self, user_id: str) -> List[Dict[str, Any]]:
        """사용자 즐겨찾기 목록 조회"""
        result = self.client.table("user_favorites").select("*").eq("user_id", user_id).execute()
        return result.data
    
    def remove_from_favorites(self, user_id: str, scientific_name: str):
        """즐겨찾기에서 제거"""
        self.client.table("user_favorites").delete().eq("user_id", user_id).eq("scientific_name", scientific_name).execute()
        print(f"[Info] 즐겨찾기 제거: {scientific_name}")
    
    # === 통계 관리 ===
    
    def update_daily_stats(
        self, 
        user_id: str, 
        verification_type: VerificationType,
        total_verifications: int,
        successful_verifications: int,
        avg_processing_time: float
    ):
        """일일 통계 업데이트"""
        today = datetime.now().date()
        success_rate = (successful_verifications / total_verifications * 100) if total_verifications > 0 else 0.0
        
        # 기존 통계 확인
        existing = self.client.table("verification_stats").select("*").eq("user_id", user_id).eq("date", today.isoformat()).eq("verification_type", verification_type.value).execute()
        
        stats_data = {
            "user_id": user_id,
            "date": today.isoformat(),
            "verification_type": verification_type.value,
            "total_verifications": total_verifications,
            "successful_verifications": successful_verifications,
            "success_rate": success_rate,
            "avg_processing_time": avg_processing_time,
            "updated_at": datetime.now().isoformat()
        }
        
        if existing.data:
            # 기존 통계 업데이트
            self.client.table("verification_stats").update(stats_data).eq("id", existing.data[0]["id"]).execute()
        else:
            # 새 통계 생성
            self.client.table("verification_stats").insert(stats_data).execute()
        
        print(f"[Info] 일일 통계 업데이트: {verification_type.value} - {success_rate:.1f}% 성공률")
    
    def get_user_stats(
        self, 
        user_id: str, 
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """사용자 통계 조회"""
        result = self.client.table("verification_stats").select("*").eq("user_id", user_id).order("date", desc=True).limit(days).execute()
        return result.data
    
    # === API 사용 로그 ===
    
    def log_api_usage(
        self,
        session_id: str,
        api_name: str,
        endpoint: Optional[str] = None,
        request_data: Optional[Dict[str, Any]] = None,
        response_status: Optional[int] = None,
        response_time_ms: Optional[int] = None,
        error_message: Optional[str] = None
    ):
        """API 사용 로그 기록"""
        log_data = {
            "session_id": session_id,
            "api_name": api_name,
            "endpoint": endpoint,
            "request_data": request_data,
            "response_status": response_status,
            "response_time_ms": response_time_ms,
            "error_message": error_message,
            "created_at": datetime.now().isoformat()
        }
        
        self.client.table("api_usage_logs").insert(log_data).execute()
    
    # === 검색 및 필터링 ===
    
    def search_species(
        self, 
        query: str, 
        verification_type: Optional[VerificationType] = None,
        user_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """종 검索 (학명 또는 국명)"""
        query_builder = self.client.table("verification_results").select("*")
        
        # 텍스트 검색 (학명 또는 국명)
        query_builder = query_builder.or_(f"scientific_name.ilike.%{query}%,korean_name.ilike.%{query}%,input_name.ilike.%{query}%")
        
        if verification_type:
            query_builder = query_builder.eq("verification_type", verification_type.value)
        
        if user_id:
            # 사용자의 세션으로 제한
            user_sessions = self.client.table("verification_sessions").select("id").eq("user_id", user_id).execute()
            session_ids = [s["id"] for s in user_sessions.data]
            if session_ids:
                query_builder = query_builder.in_("session_id", session_ids)
        
        result = query_builder.limit(limit).execute()
        return result.data

# 전역 서비스 인스턴스
db_service = DatabaseService()

def get_database_service() -> DatabaseService:
    """데이터베이스 서비스 인스턴스 반환"""
    return db_service 