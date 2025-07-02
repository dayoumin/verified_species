"""
자동 캐시 업데이트 스케줄러

이 모듈은 다음 기능을 제공합니다:
1. 월간 정기 캐시 새로고침 (WoRMS, LPSN, COL)
2. 실시간 검증 결과와 캐시 비교 업데이트
3. 데이터베이스별 맞춤 업데이트 전략
"""
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from .cache_manager import get_cache_manager
from .secure_mode import get_secure_database_manager

class CacheUpdateScheduler:
    """캐시 업데이트 스케줄링 및 실시간 검증 관리자"""
    
    def __init__(self):
        self.cache_manager = get_cache_manager()
        self.secure_db = get_secure_database_manager()
        
        # 데이터베이스별 업데이트 전략
        self.update_strategies = {
            'worms': {
                'schedule': 'monthly',  # 월간 업데이트
                'priority_fields': ['status', 'valid_name', 'classification'],
                'api_delay': 1.5,  # API 호출 간격 (초)
                'batch_size': 50   # 배치 크기
            },
            'lpsn': {
                'schedule': 'monthly',  # 월간 업데이트  
                'priority_fields': ['status', 'valid_name', 'taxonomy'],
                'api_delay': 2.0,  # LPSN은 더 안전하게
                'batch_size': 30
            },
            'col': {
                'schedule': 'monthly',  # 월간 업데이트
                'priority_fields': ['status', 'accepted_name', 'rank'],
                'api_delay': 1.0,
                'batch_size': 100
            }
        }
        
        print("[Info] 캐시 업데이트 스케줄러 초기화 완료")
    
    def verify_and_update_cache(self, scientific_name: str, source_db: str,
                                api_call_func: Callable,
                                force_update: bool = False) -> Dict[str, Any]:
        """실시간 검증 결과와 캐시 비교 후 필요시 업데이트"""
        
        try:
            # 1. 기존 캐시 데이터 조회
            cached_data = self.secure_db.get_cache(scientific_name, source_db)
            
            # 2. 실시간 API 호출
            print(f"[Info] 실시간 검증 시작: {scientific_name} ({source_db})")
            api_start = time.time()
            fresh_data = api_call_func(scientific_name)
            api_time = int((time.time() - api_start) * 1000)
            
            if not fresh_data:
                if cached_data:
                    print(f"[Warning] API 호출 실패, 캐시 데이터 사용: {scientific_name}")
                    return {"status": "cache_fallback", "data": cached_data}
                else:
                    print(f"[Error] API 호출 실패, 캐시도 없음: {scientific_name}")
                    return {"status": "failed", "data": None}
            
            # 3. 캐시와 실시간 데이터 비교
            if cached_data and not force_update:
                comparison_result = self._compare_data(
                    cached_data, fresh_data, source_db
                )
                
                if not comparison_result['has_changes']:
                    print(f"[Info] 데이터 일치, 캐시 유지: {scientific_name}")
                    return {"status": "cache_valid", "data": cached_data}
                else:
                    print(f"[Info] 데이터 변경 감지: {scientific_name}")
                    print(f"      변경된 필드: {comparison_result['changed_fields']}")
                    
                    # 변경 로그 기록
                    self._log_data_changes(
                        scientific_name, source_db, 
                        comparison_result['changed_fields'],
                        cached_data, fresh_data
                    )
            
            # 4. 캐시 업데이트
            update_reason = 'force_update' if force_update else 'data_mismatch'
            update_success = self.secure_db.set_cache(
                scientific_name, source_db, fresh_data, update_reason
            )
            
            if update_success:
                print(f"[Info] 캐시 업데이트 완료: {scientific_name}")
                return {
                    "status": "updated", 
                    "data": fresh_data,
                    "api_time_ms": api_time,
                    "changes": comparison_result.get('changed_fields', []) if cached_data else ['initial_creation']
                }
            else:
                print(f"[Warning] 캐시 업데이트 실패: {scientific_name}")
                return {"status": "update_failed", "data": fresh_data}
                
        except Exception as e:
            print(f"[Error] 검증 및 업데이트 중 오류: {e}")
            # 오류 시 캐시 데이터라도 반환
            if cached_data:
                return {"status": "error_cache_fallback", "data": cached_data}
            return {"status": "error", "data": None}
    
    def _compare_data(self, cached_data: Dict[str, Any], fresh_data: Dict[str, Any],
                      source_db: str) -> Dict[str, Any]:
        """캐시 데이터와 실시간 데이터 비교"""
        strategy = self.update_strategies.get(source_db, {})
        priority_fields = strategy.get('priority_fields', ['status', 'scientific_name'])
        
        changed_fields = []
        
        for field in priority_fields:
            cached_value = cached_data.get(field)
            fresh_value = fresh_data.get(field)
            
            # 값 정규화 (문자열 비교를 위해)
            cached_str = str(cached_value).strip().lower() if cached_value else ""
            fresh_str = str(fresh_value).strip().lower() if fresh_value else ""
            
            if cached_str != fresh_str:
                changed_fields.append({
                    'field': field,
                    'old_value': cached_value,
                    'new_value': fresh_value
                })
        
        return {
            'has_changes': len(changed_fields) > 0,
            'changed_fields': changed_fields,
            'total_fields_checked': len(priority_fields)
        }
    
    def _log_data_changes(self, scientific_name: str, source_db: str,
                          changed_fields: List[Dict], old_data: Dict, new_data: Dict):
        """데이터 변경 사항 로깅"""
        try:
            change_summary = f"종명: {scientific_name} ({source_db})"
            for change in changed_fields:
                change_summary += f"\n  - {change['field']}: '{change['old_value']}' → '{change['new_value']}'"
            
            print(f"[Data Change] {change_summary}")
            
            # 중요한 변경사항은 별도 로그 파일에 기록 (선택사항)
            important_fields = ['status', 'valid_name', 'accepted_name']
            has_important_changes = any(
                change['field'] in important_fields for change in changed_fields
            )
            
            if has_important_changes:
                self._write_change_log(scientific_name, source_db, changed_fields)
                
        except Exception as e:
            print(f"[Warning] 변경 로그 기록 실패: {e}")
    
    def _write_change_log(self, scientific_name: str, source_db: str,
                          changed_fields: List[Dict]):
        """중요한 변경사항을 파일에 기록"""
        try:
            import os
            from pathlib import Path
            
            log_dir = Path(os.getenv("APPDATA", os.path.expanduser("~"))) / "SpeciesVerifier" / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            
            log_file = log_dir / f"data_changes_{datetime.now().strftime('%Y-%m')}.log"
            
            with open(log_file, 'a', encoding='utf-8') as f:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"\n[{timestamp}] {scientific_name} ({source_db})\n")
                for change in changed_fields:
                    f.write(f"  {change['field']}: '{change['old_value']}' → '{change['new_value']}'\n")
                
        except Exception as e:
            print(f"[Warning] 변경 로그 파일 쓰기 실패: {e}")
    
    def schedule_monthly_update(self, target_db: str = None, 
                               min_usage_count: int = 3,
                               max_items_per_run: int = 100) -> Dict[str, Any]:
        """월간 정기 업데이트 실행 (인기 종 우선)"""
        
        print(f"[Info] 월간 정기 업데이트 시작: {target_db or 'all databases'}")
        
        try:
            # 업데이트 대상 조회 (로컬 통계 기반)
            stats = self.secure_db.get_cache_stats()
            
            if 'popular_species' not in stats:
                print("[Info] 업데이트할 인기 종이 없습니다")
                return {"updated": 0, "skipped": 0, "error": "no_popular_species"}
            
            # 업데이트 대상 필터링
            candidates = []
            for species in stats['popular_species']:
                if species['hit_count'] >= min_usage_count:
                    if not target_db or species['source_db'] == target_db:
                        candidates.append(species)
            
            if not candidates:
                print(f"[Info] 조건에 맞는 업데이트 대상이 없습니다 (최소 사용: {min_usage_count})")
                return {"updated": 0, "skipped": 0, "error": "no_candidates"}
            
            # 최대 항목 수 제한
            if len(candidates) > max_items_per_run:
                candidates = candidates[:max_items_per_run]
                print(f"[Info] 업데이트 대상을 {max_items_per_run}개로 제한")
            
            # 실제 업데이트 실행
            updated_count = 0
            skipped_count = 0
            
            for i, species in enumerate(candidates, 1):
                scientific_name = species['scientific_name']
                source_db = species['source_db']
                
                print(f"[Info] 업데이트 진행: {i}/{len(candidates)} - {scientific_name}")
                
                try:
                    # API 함수 가져오기
                    api_func = self._get_api_function(source_db)
                    
                    if api_func:
                        # 강제 업데이트 실행
                        result = self.verify_and_update_cache(
                            scientific_name, source_db, api_func, force_update=True
                        )
                        
                        if result['status'] in ['updated', 'cache_valid']:
                            updated_count += 1
                        else:
                            skipped_count += 1
                    else:
                        print(f"[Warning] {source_db} API 함수를 찾을 수 없음")
                        skipped_count += 1
                    
                    # API 호출 간격 (서버 부담 방지)
                    strategy = self.update_strategies.get(source_db, {})
                    delay = strategy.get('api_delay', 1.5)
                    time.sleep(delay)
                    
                except Exception as item_error:
                    print(f"[Warning] {scientific_name} 업데이트 실패: {item_error}")
                    skipped_count += 1
            
            result_summary = {
                "updated": updated_count,
                "skipped": skipped_count,
                "total_candidates": len(candidates),
                "target_db": target_db,
                "completed_at": datetime.now().isoformat()
            }
            
            print(f"[Info] 월간 업데이트 완료: {updated_count}개 성공, {skipped_count}개 실패")
            return result_summary
            
        except Exception as e:
            print(f"[Error] 월간 업데이트 중 오류: {e}")
            return {"error": str(e)}
    
    def _get_api_function(self, source_db: str) -> Optional[Callable]:
        """데이터베이스별 API 호출 함수 반환"""
        try:
            if source_db == 'worms':
                from ..core.verifier import check_worms_record
                return lambda name: check_worms_record(name)
            elif source_db == 'lpsn':
                from ..core.verifier import verify_single_microbe_lpsn  
                return lambda name: verify_single_microbe_lpsn(name)
            elif source_db == 'col':
                # COL API 함수 (향후 구현)
                print("[Warning] COL API 함수가 아직 구현되지 않았습니다")
                return None
        except ImportError as e:
            print(f"[Warning] API 함수 임포트 실패: {e}")
            return None
        
        return None
    
    def get_update_schedule_info(self) -> Dict[str, Any]:
        """업데이트 스케줄 정보 반환"""
        return {
            "update_strategies": self.update_strategies,
            "next_monthly_update": self._get_next_monthly_date(),
            "database_classifications": {
                "marine_species": "worms",     # 해양생물
                "microorganisms": "lpsn",      # 미생물  
                "freshwater_species": "col",   # 담수생물
                "general_species": "col"       # 일반생물
            },
            "security_mode": self.secure_db.mode
        }
    
    def _get_next_monthly_date(self) -> str:
        """다음 월간 업데이트 예정일 계산"""
        now = datetime.now()
        # 매월 1일로 설정
        if now.day == 1:
            next_update = now.replace(day=1) + timedelta(days=32)
        else:
            next_month = now.replace(day=1) + timedelta(days=32)
            next_update = next_month.replace(day=1)
        
        return next_update.strftime('%Y-%m-%d')

# 전역 스케줄러 인스턴스
cache_scheduler = CacheUpdateScheduler()

def get_cache_scheduler() -> CacheUpdateScheduler:
    """캐시 업데이트 스케줄러 인스턴스 반환"""
    return cache_scheduler 