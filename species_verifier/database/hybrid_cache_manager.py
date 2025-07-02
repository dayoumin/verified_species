"""
Species Verifier 하이브리드 캐시 매니저
실시간 검색과 DB 캐시 검색을 통합 관리합니다.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import json
import logging
from dataclasses import dataclass

from .supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

@dataclass
class CacheResult:
    """캐시 검색 결과를 담는 데이터 클래스"""
    input_name: str
    scientific_name: str
    is_verified: bool
    status: str
    details: Dict[str, Any]
    last_verified_at: datetime
    days_old: int
    source: str  # 'cache' 또는 'realtime'
    
class HybridCacheManager:
    """하이브리드 검색 시스템의 핵심 캐시 매니저"""
    
    def __init__(self):
        """캐시 매니저 초기화"""
        self.supabase = get_supabase_client()
        self.default_cache_days = 365  # DB 검색 시 모든 데이터 조회 (1년으로 설정)
        
        # API 타입별 테이블 매핑
        self.table_mapping = {
            'marine': 'marine_species_cache',
            'microbe': 'microbe_species_cache', 
            'col': 'col_species_cache'
        }
        
        logger.info("HybridCacheManager 초기화 완료 - DB 검색 시 모든 캐시 데이터 조회")
        
    def get_cache_result(self, input_name: str, api_type: str, 
                        max_age_days: int = None) -> Optional[CacheResult]:
        """
        캐시에서 결과를 조회합니다.
        
        Args:
            input_name: 검색할 학명
            api_type: 'marine', 'microbe', 'col'
            max_age_days: 최대 허용 캐시 나이 (None이면 모든 데이터 조회)
            
        Returns:
            CacheResult 또는 None (캐시 미스)
        """
        try:
            table_name = self.table_mapping.get(api_type)
            if not table_name:
                logger.error(f"Unknown API type: {api_type}")
                return None
                
            # DB 검색 모드에서는 유효기간 무시하고 모든 데이터 조회
            if max_age_days is None:
                max_age_days = self.default_cache_days
                
            cutoff_date = datetime.now() - timedelta(days=max_age_days)
            
            # Supabase에서 캐시 조회
            result = self.supabase.table(table_name)\
                .select("*")\
                .eq("input_name", input_name)\
                .gte("last_verified_at", cutoff_date.isoformat())\
                .execute()
                
            if result.data and len(result.data) > 0:
                cache_data = result.data[0]
                last_verified = datetime.fromisoformat(
                    cache_data['last_verified_at'].replace('Z', '+00:00')
                )
                days_old = (datetime.now() - last_verified.replace(tzinfo=None)).days
                
                # API 타입별 결과 구성
                cache_result = self._build_cache_result(cache_data, api_type, days_old)
                
                logger.info(f"Cache HIT: {input_name} ({api_type}) - {days_old}일 전 데이터")
                return cache_result
                
            logger.info(f"Cache MISS: {input_name} ({api_type})")
            return None
            
        except Exception as e:
            logger.error(f"Cache 조회 중 오류: {str(e)}")
            return None
    
    def save_realtime_result(self, input_name: str, api_type: str, 
                           verification_result: Dict[str, Any]) -> bool:
        """
        실시간 검증 결과를 캐시에 저장합니다.
        
        Args:
            input_name: 학명
            api_type: 'marine', 'microbe', 'col'
            verification_result: 검증 결과 딕셔너리
            
        Returns:
            저장 성공 여부
        """
        try:
            table_name = self.table_mapping.get(api_type)
            if not table_name:
                logger.error(f"Unknown API type: {api_type}")
                return False
                
            # API 타입별 데이터 변환
            cache_data = self._convert_to_cache_format(verification_result, api_type)
            
            # Upsert (있으면 업데이트, 없으면 삽입)
            result = self.supabase.table(table_name)\
                .upsert(cache_data, on_conflict="input_name")\
                .execute()
                
            if result.data:
                logger.info(f"Cache SAVE: {input_name} ({api_type}) 저장 완료")
                return True
            else:
                logger.error(f"Cache SAVE 실패: {input_name} ({api_type})")
                return False
                
        except Exception as e:
            logger.error(f"Cache 저장 중 오류: {str(e)}")
            return False
    
    def get_outdated_species(self, api_type: str, max_age_days: int = 30) -> List[str]:
        """
        오래된 캐시 데이터 목록을 반환합니다.
        
        Args:
            api_type: 'marine', 'microbe', 'col'
            max_age_days: 기준 일수
            
        Returns:
            오래된 학명 리스트
        """
        try:
            table_name = self.table_mapping.get(api_type)
            if not table_name:
                return []
                
            cutoff_date = datetime.now() - timedelta(days=max_age_days)
            
            result = self.supabase.table(table_name)\
                .select("input_name, last_verified_at")\
                .lt("last_verified_at", cutoff_date.isoformat())\
                .execute()
                
            outdated_species = [item['input_name'] for item in result.data]
            logger.info(f"오래된 캐시 ({api_type}): {len(outdated_species)}개")
            
            return outdated_species
            
        except Exception as e:
            logger.error(f"오래된 캐시 조회 중 오류: {str(e)}")
            return []
    
    def get_cache_statistics(self, api_type: str = None) -> Dict[str, Any]:
        """
        캐시 통계 정보를 반환합니다.
        
        Args:
            api_type: None이면 전체, 특정 타입이면 해당 타입만
            
        Returns:
            통계 정보 딕셔너리
        """
        try:
            stats = {}
            api_types = [api_type] if api_type else ['marine', 'microbe', 'col']
            
            for api in api_types:
                table_name = self.table_mapping.get(api)
                if not table_name:
                    continue
                    
                # 전체 캐시 수
                total_result = self.supabase.table(table_name)\
                    .select("id", count="exact")\
                    .execute()
                total_count = total_result.count
                
                # 30일 이내 최신 캐시 수
                cutoff_date = datetime.now() - timedelta(days=30)
                recent_result = self.supabase.table(table_name)\
                    .select("id", count="exact")\
                    .gte("last_verified_at", cutoff_date.isoformat())\
                    .execute()
                recent_count = recent_result.count
                
                # 검증 성공 수
                verified_result = self.supabase.table(table_name)\
                    .select("id", count="exact")\
                    .eq("is_verified", True)\
                    .execute()
                verified_count = verified_result.count
                
                stats[api] = {
                    'total_cached': total_count,
                    'recent_30days': recent_count,
                    'outdated': total_count - recent_count,
                    'verified_count': verified_count,
                    'success_rate': round(verified_count / total_count * 100, 1) if total_count > 0 else 0
                }
                
            return stats
            
        except Exception as e:
            logger.error(f"캐시 통계 조회 중 오류: {str(e)}")
            return {}
    
    def _build_cache_result(self, cache_data: Dict, api_type: str, days_old: int) -> CacheResult:
        """캐시 데이터를 CacheResult 객체로 변환"""
        
        if api_type == 'marine':
            return CacheResult(
                input_name=cache_data['input_name'],
                scientific_name=cache_data['scientific_name'] or cache_data['input_name'],
                is_verified=cache_data['is_verified'],
                status=cache_data['worms_status'] or 'unknown',
                details={
                    'worms_id': cache_data.get('worms_id'),
                    'worms_url': cache_data.get('worms_url'),
                    'classification': cache_data.get('classification'),
                    'wiki_summary': cache_data.get('wiki_summary')
                },
                last_verified_at=datetime.fromisoformat(
                    cache_data['last_verified_at'].replace('Z', '+00:00')
                ),
                days_old=days_old,
                source='cache'
            )
            
        elif api_type == 'microbe':
            return CacheResult(
                input_name=cache_data['input_name'],
                scientific_name=cache_data['valid_name'] or cache_data['input_name'],
                is_verified=cache_data['is_verified'],
                status=cache_data['lpsn_status'] or 'unknown',
                details={
                    'lpsn_url': cache_data.get('lpsn_url'),
                    'taxonomy': cache_data.get('taxonomy')
                },
                last_verified_at=datetime.fromisoformat(
                    cache_data['last_verified_at'].replace('Z', '+00:00')
                ),
                days_old=days_old,
                source='cache'
            )
            
        elif api_type == 'col':
            return CacheResult(
                input_name=cache_data['input_name'],
                scientific_name=cache_data['scientific_name'] or cache_data['input_name'],
                is_verified=cache_data['is_verified'],
                status=cache_data['col_status'] or 'unknown',
                details={
                    'col_id': cache_data.get('col_id'),
                    'col_url': cache_data.get('col_url'),
                    'classification': cache_data.get('classification')
                },
                last_verified_at=datetime.fromisoformat(
                    cache_data['last_verified_at'].replace('Z', '+00:00')
                ),
                days_old=days_old,
                source='cache'
            )
    
    def _convert_to_cache_format(self, verification_result: Dict, api_type: str) -> Dict:
        """검증 결과를 캐시 저장 형식으로 변환"""
        
        base_data = {
            'input_name': verification_result.get('input_name', ''),
            'is_verified': verification_result.get('is_verified', False),
            'last_verified_at': datetime.now().isoformat(),
            'verification_count': 1
        }
        
        if api_type == 'marine':
            base_data.update({
                'scientific_name': verification_result.get('scientific_name'),
                'worms_id': verification_result.get('worms_id'),
                'worms_status': verification_result.get('status'),
                'classification': verification_result.get('taxonomy'),
                'worms_url': verification_result.get('worms_url'),
                'wiki_summary': verification_result.get('wiki_summary')
            })
            
        elif api_type == 'microbe':
            base_data.update({
                'valid_name': verification_result.get('valid_name') or verification_result.get('scientific_name'),
                'lpsn_status': verification_result.get('status'),
                'taxonomy': verification_result.get('taxonomy'),
                'lpsn_url': verification_result.get('lpsn_link')
            })
            
        elif api_type == 'col':
            base_data.update({
                'scientific_name': verification_result.get('scientific_name'),
                'col_id': verification_result.get('col_id'),
                'col_status': verification_result.get('status'),
                'classification': verification_result.get('taxonomy'),
                'col_url': verification_result.get('col_url')
            })
        
        return base_data

# 전역 캐시 매니저 인스턴스
_cache_manager = None

def get_cache_manager() -> HybridCacheManager:
    """캐시 매니저 싱글톤 인스턴스 반환"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = HybridCacheManager()
    return _cache_manager 