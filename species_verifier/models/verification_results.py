"""
검증 결과 데이터 모델

이 모듈은 종 검증 결과를 표현하는 데이터 모델을 정의합니다.
"""
from typing import Optional, Any, Dict, List
from datetime import datetime
from pydantic import BaseModel, Field


class BaseVerificationResult(BaseModel):
    """기본 검증 결과 모델"""
    input_name: str = Field(..., description="입력된 이름 (국명 또는 학명)")
    scientific_name: str = Field(..., description="학명")
    is_verified: bool = Field(default=False, description="검증 성공 여부")
    wiki_summary: str = Field(default="준비 중 (DeepSearch 기능 개발 예정)", description="심층분석 결과 정보")
    verification_date: datetime = Field(default_factory=datetime.now, description="검증 일시")


class MarineVerificationResult(BaseVerificationResult):
    """해양생물 검증 결과 모델"""
    korean_name: str = Field(default="-", description="한글 국명")
    worms_status: str = Field(default="-", description="WoRMS 검증 상태")
    worms_id: str = Field(default="-", description="WoRMS ID")
    worms_link: str = Field(default="-", description="WoRMS 링크")
    mapped_name: str = Field(default="-", description="매핑된 이름 (추천 이름)")


class MicrobeVerificationResult(BaseVerificationResult):
    """미생물 검증 결과 모델"""
    korean_name: str = Field(default="-", description="한글 국명")
    valid_name: str = Field(default="-", description="유효한 학명")
    status: str = Field(default="-", description="검증 상태")
    taxonomy: str = Field(default="-", description="분류학적 정보")
    lpsn_link: str = Field(default="-", description="LPSN 링크")
    is_microbe: bool = Field(default=False, description="미생물 여부")


class VerificationSummary(BaseModel):
    """검증 작업 요약 정보"""
    total_items: int = Field(default=0, description="총 항목 수")
    verified_count: int = Field(default=0, description="검증 성공 항목 수")
    skipped_count: int = Field(default=0, description="건너뛴 항목 수")
    error_count: int = Field(default=0, description="오류 발생 항목 수")
    had_errors: bool = Field(default=False, description="오류 발생 여부")
    error_message: str = Field(default="", description="오류 메시지")
    start_time: datetime = Field(default_factory=datetime.now, description="시작 시간")
    end_time: Optional[datetime] = Field(default=None, description="종료 시간")
    duration_seconds: float = Field(default=0.0, description="소요 시간 (초)")


def dict_to_marine_result(result_dict: Dict[str, Any]) -> MarineVerificationResult:
    """사전 형태의 결과를 MarineVerificationResult 모델로 변환

    Args:
        result_dict: 사전 형태의 결과 데이터
        
    Returns:
        변환된 MarineVerificationResult 객체
    """
    return MarineVerificationResult(
        input_name=result_dict.get('input_name', '-'),
        scientific_name=result_dict.get('scientific_name', '-'),
        is_verified=result_dict.get('is_verified', False),
        wiki_summary=result_dict.get('wiki_summary', '-'),
        korean_name=result_dict.get('korean_name', '-'),
        worms_status=result_dict.get('worms_status', '-'),
        worms_id=result_dict.get('worms_id', '-'),
        worms_link=result_dict.get('worms_link', '-'),
        mapped_name=result_dict.get('mapped_name', '-')
    )


def dict_to_microbe_result(result_dict: Dict[str, Any]) -> MicrobeVerificationResult:
    """사전 형태의 결과를 MicrobeVerificationResult 모델로 변환

    Args:
        result_dict: 사전 형태의 결과 데이터
        
    Returns:
        변환된 MicrobeVerificationResult 객체
    """
    return MicrobeVerificationResult(
        input_name=result_dict.get('input_name', '-'),
        scientific_name=result_dict.get('scientific_name', '-'),
        is_verified=result_dict.get('is_verified', False),
        wiki_summary=result_dict.get('wiki_summary', '-'),
        korean_name=result_dict.get('korean_name', '-'),
        valid_name=result_dict.get('valid_name', '-'),
        status=result_dict.get('status', '-'),
        taxonomy=result_dict.get('taxonomy', '-'),
        lpsn_link=result_dict.get('lpsn_link', '-'),
        is_microbe=result_dict.get('is_microbe', False)
    ) 