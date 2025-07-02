"""
Supabase 데이터베이스 모델 정의

이 모듈은 Supabase 테이블과 연동하기 위한 Pydantic 모델을 정의합니다.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum

class VerificationType(str, Enum):
    """검증 타입 열거형"""
    MARINE = "marine"
    MICROBE = "microbe"
    COL = "col"
    MIXED = "mixed"

class SessionStatus(str, Enum):
    """세션 상태 열거형"""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class VerificationSession(BaseModel):
    """검증 세션 모델"""
    id: Optional[str] = None
    user_id: Optional[str] = None
    session_name: Optional[str] = None
    verification_type: VerificationType
    total_items: int = 0
    verified_count: int = 0
    skipped_count: int = 0
    error_count: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    status: SessionStatus = SessionStatus.RUNNING
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class VerificationResult(BaseModel):
    """검증 결과 모델"""
    id: Optional[str] = None
    session_id: str
    input_name: str
    scientific_name: Optional[str] = None
    korean_name: Optional[str] = None
    verification_type: VerificationType
    is_verified: bool = False
    verification_status: Optional[str] = None
    
    # 해양생물 전용 필드
    worms_id: Optional[str] = None
    worms_status: Optional[str] = None
    worms_link: Optional[str] = None
    mapped_name: Optional[str] = None
    
    # 미생물 전용 필드
    valid_name: Optional[str] = None
    taxonomy: Optional[str] = None
    lpsn_link: Optional[str] = None
    is_microbe: bool = False
    
    # COL 전용 필드
    col_id: Optional[str] = None
    col_status: Optional[str] = None
    col_rank: Optional[str] = None
    col_classification: Optional[Dict[str, Any]] = None
    
    # 공통 필드
    wiki_summary: str = "준비 중 (DeepSearch 기능 개발 예정)"
    external_links: Optional[Dict[str, Any]] = None
    raw_api_response: Optional[Dict[str, Any]] = None
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class UserFavorite(BaseModel):
    """사용자 즐겨찾기 모델"""
    id: Optional[str] = None
    user_id: str
    scientific_name: str
    korean_name: Optional[str] = None
    verification_type: VerificationType
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

class VerificationStats(BaseModel):
    """검증 통계 모델"""
    id: Optional[str] = None
    user_id: str
    date: datetime
    verification_type: VerificationType
    total_verifications: int = 0
    successful_verifications: int = 0
    success_rate: float = 0.0
    avg_processing_time: float = 0.0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class ApiUsageLog(BaseModel):
    """API 사용 로그 모델"""
    id: Optional[str] = None
    session_id: str
    api_name: str  # 'worms', 'lpsn', 'col', 'wikipedia'
    endpoint: Optional[str] = None
    request_data: Optional[Dict[str, Any]] = None
    response_status: Optional[int] = None
    response_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None 