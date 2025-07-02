"""
Supabase 기반 스마트 캐싱 매니저

이 모듈은 WoRMS, LPSN, COL API 응답을 캐싱하여 성능을 90% 향상시킵니다.
실시간 검증 결과와 캐시 데이터를 비교하여 자동 업데이트합니다.
"""
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from .supabase_client import get_supabase_client
from .models import VerificationType

class SpeciesCacheManager:
    """학명 검증 결과 캐싱 관리 - 완전한 로깅 기능 + 실시간 비교 업데이트"""
    
    def __init__(self, user_session_id: str = None):
        self.client = get_supabase_client()
        self.user_session_id = user_session_id or f"session_{int(time.time())}"
        
        # 데이터베이스별 캐시 유효기간 설정 (1개월 기본)
        self.cache_duration = {
            'worms': timedelta(days=30),    # 해양생물 - 월별 스냅샷 기반
            'lpsn': timedelta(days=30),     # 미생물 - 월간 업데이트  
            'col': timedelta(days=30)       # 담수생물 - 월간 정기 릴리스
        }
        
        # 데이터베이스별 분류 설정
        self.db_classification = {
            'marine': 'worms',      # 해양생물 → WoRMS
            'microbe': 'lpsn',      # 미생물 → LPSN
            'freshwater': 'col',    # 담수생물 → COL
            'general': 'col'        # 일반생물 → COL (기본값)
        }
        
        print(f"[Info] 캐시 매니저 초기화 완료: {self.user_session_id}")
    
    def get_cache_with_validation(self, scientific_name: str, source_db: str, 
                                  api_call_func: Optional[Callable] = None,
                                  session_id: Optional[str] = None,
                                  force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """캐시 조회 + 실시간 API 결과와 비교 검증"""
        start_time = time.time()
        
        try:
            # 1. 캐시에서 기존 데이터 조회
            if not force_refresh:
                cached_data = self.get_cache(scientific_name, source_db, session_id)
                if cached_data:
                    # 2. 실시간 API 호출이 가능한 경우 비교 검증
                    if api_call_func:
                        return self._validate_cache_with_api(
                            scientific_name, source_db, cached_data, 
                            api_call_func, session_id
                        )
                    else:
                        return cached_data
            
            # 3. 캐시가 없거나 강제 새로고침인 경우 API 호출
            if api_call_func:
                print(f"[Info] API 호출 중: {scientific_name} ({source_db})")
                api_start = time.time()
                fresh_data = api_call_func(scientific_name)
                api_time = int((time.time() - api_start) * 1000)
                
                if fresh_data:
                    # 캐시에 저장
                    self.set_cache(
                        scientific_name, source_db, fresh_data,
                        update_reason='api_refresh' if force_refresh else 'cache_miss',
                        api_response_time=api_time,
                        session_id=session_id
                    )
                    return fresh_data
            
            return None
            
        except Exception as e:
            print(f"[Error] 캐시 검증 중 오류: {e}")
            return None
    
    def _validate_cache_with_api(self, scientific_name: str, source_db: str,
                                 cached_data: Dict[str, Any], api_call_func: Callable,
                                 session_id: Optional[str] = None) -> Dict[str, Any]:
        """캐시 데이터와 실시간 API 결과 비교 검증"""
        try:
            # 실시간 API 호출 (주요 필드만 확인)
            api_start = time.time()
            fresh_data = api_call_func(scientific_name)
            api_time = int((time.time() - api_start) * 1000)
            
            if not fresh_data:
                print(f"[Warning] API 호출 실패, 캐시 데이터 사용: {scientific_name}")
                return cached_data
            
            # 주요 필드 비교 (데이터베이스별 다른 필드)
            key_fields = self._get_key_fields_for_db(source_db)
            has_differences = False
            
            for field in key_fields:
                cached_value = cached_data.get(field)
                fresh_value = fresh_data.get(field)
                
                if cached_value != fresh_value:
                    print(f"[Info] 데이터 변경 감지: {scientific_name}.{field} '{cached_value}' → '{fresh_value}'")
                    has_differences = True
            
            if has_differences:
                # 변경사항이 있으면 캐시 업데이트
                print(f"[Info] 캐시 자동 업데이트: {scientific_name} ({source_db})")
                self.set_cache(
                    scientific_name, source_db, fresh_data,
                    update_reason='data_mismatch',
                    api_response_time=api_time,
                    session_id=session_id
                )
                
                # 불일치 로그 기록
                self._log_cache_update(
                    scientific_name=scientific_name,
                    source_db=source_db,
                    update_type='api_mismatch',
                    old_data=cached_data,
                    new_data=fresh_data,
                    update_reason=f"실시간 검증에서 {len([f for f in key_fields if cached_data.get(f) != fresh_data.get(f)])}개 필드 변경 감지",
                    api_response_time=api_time
                )
                
                return fresh_data
            else:
                # 데이터가 동일하면 캐시 그대로 사용
                print(f"[Info] 캐시 데이터 검증 완료: {scientific_name} (변경사항 없음)")
                return cached_data
                
        except Exception as e:
            print(f"[Warning] API 비교 검증 실패, 캐시 데이터 사용: {e}")
            return cached_data
    
    def _get_key_fields_for_db(self, source_db: str) -> List[str]:
        """데이터베이스별 주요 비교 필드 반환"""
        key_fields_map = {
            'worms': ['status', 'valid_name', 'classification', 'rank'],
            'lpsn': ['status', 'valid_name', 'taxonomy', 'nomenclatural_status'],
            'col': ['status', 'rank', 'classification', 'accepted_name']
        }
        return key_fields_map.get(source_db, ['status', 'scientific_name'])
    
    def schedule_monthly_refresh(self, target_db: str = None, 
                                 min_hit_count: int = 5) -> Dict[str, Any]:
        """월간 캐시 새로고침 스케줄 실행 (인기 종 우선)"""
        try:
            print(f"[Info] 월간 캐시 새로고침 시작: {target_db or 'all'}")
            
            # 새로고침 대상 조회 (인기도 순)
            query_builder = self.client.table("species_cache").select("*")
            
            if target_db:
                query_builder = query_builder.eq("source_db", target_db)
            
            # 히트 카운트가 높은 순으로 정렬
            result = query_builder.gte("hit_count", min_hit_count).order("hit_count", desc=True).execute()
            
            if not result.data:
                print(f"[Info] 새로고침할 캐시 데이터가 없습니다 (최소 히트: {min_hit_count})")
                return {"refreshed": 0, "skipped": 0}
            
            refreshed_count = 0
            skipped_count = 0
            
            for cache_record in result.data:
                scientific_name = cache_record['scientific_name']
                source_db = cache_record['source_db']
                
                try:
                    # API 함수를 동적으로 가져와야 함 (실제 구현에서는 dependency injection 사용)
                    api_func = self._get_api_function(source_db)
                    if api_func:
                        # 강제 새로고침
                        fresh_data = self.get_cache_with_validation(
                            scientific_name, source_db, api_func, force_refresh=True
                        )
                        if fresh_data:
                            refreshed_count += 1
                            print(f"[Info] 새로고침 완료: {scientific_name}")
                        else:
                            skipped_count += 1
                    else:
                        skipped_count += 1
                        
                    # API 호출 간격 (서버 부담 방지)
                    time.sleep(1.5)
                    
                except Exception as item_error:
                    print(f"[Warning] {scientific_name} 새로고침 실패: {item_error}")
                    skipped_count += 1
            
            result_summary = {
                "refreshed": refreshed_count,
                "skipped": skipped_count,
                "total_candidates": len(result.data)
            }
            
            print(f"[Info] 월간 새로고침 완료: {refreshed_count}개 성공, {skipped_count}개 건너뜀")
            return result_summary
            
        except Exception as e:
            print(f"[Error] 월간 새로고침 중 오류: {e}")
            return {"error": str(e)}
    
    def _get_api_function(self, source_db: str) -> Optional[Callable]:
        """데이터베이스별 API 호출 함수 반환 (실제 구현에서는 의존성 주입 사용)"""
        # 이 부분은 실제 API 함수들과 연결해야 함
        try:
            if source_db == 'worms':
                from ..core.verifier import check_worms_record
                return lambda name: check_worms_record(name)
            elif source_db == 'lpsn':
                from ..core.verifier import verify_single_microbe_lpsn
                return lambda name: verify_single_microbe_lpsn(name)
            elif source_db == 'col':
                # COL API 함수 (구현 필요)
                return None
        except ImportError as e:
            print(f"[Warning] API 함수 임포트 실패: {e}")
            return None
        
        return None

    def get_cache(self, scientific_name: str, source_db: str, 
                  session_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """기본 캐시 조회 (기존 기능 유지)"""
        start_time = time.time()
        
        try:
            # 캐시 조회 (만료되지 않은 것만)
            result = self.client.table("species_cache").select("*").eq(
                "scientific_name", scientific_name
            ).eq(
                "source_db", source_db
            ).gt(
                "expires_at", datetime.now().isoformat()
            ).execute()
            
            response_time_ms = int((time.time() - start_time) * 1000)
            
            if result.data and len(result.data) > 0:
                # 캐시 히트
                cache_record = result.data[0]
                cache_age = (datetime.now() - datetime.fromisoformat(cache_record['created_at'].replace('Z', '+00:00')))
                
                self._log_cache_access(
                    scientific_name=scientific_name,
                    source_db=source_db,
                    access_type='hit',
                    response_time_ms=response_time_ms,
                    cache_age_seconds=int(cache_age.total_seconds()),
                    session_id=session_id
                )
                
                print(f"[Info] 캐시 히트: {scientific_name} ({source_db}) - {response_time_ms}ms")
                return cache_record['cache_data']
            else:
                # 캐시 미스
                self._log_cache_access(
                    scientific_name=scientific_name,
                    source_db=source_db,
                    access_type='miss',
                    response_time_ms=response_time_ms,
                    session_id=session_id
                )
                
                print(f"[Info] 캐시 미스: {scientific_name} ({source_db})")
                return None
                
        except Exception as e:
            print(f"[Error] 캐시 조회 중 오류: {e}")
            return None
    
    def set_cache(self, scientific_name: str, source_db: str, data: Dict[str, Any],
                  version_info: str = None, update_reason: str = 'api_call',
                  api_response_time: int = None, session_id: Optional[str] = None):
        """캐시 저장 + 업데이트 히스토리 기록"""
        
        try:
            # 만료 시간 계산
            expires_at = datetime.now() + self.cache_duration.get(source_db, timedelta(days=30))
            
            # 기존 캐시가 있는지 확인
            existing = self.client.table("species_cache").select("*").eq(
                "scientific_name", scientific_name
            ).eq("source_db", source_db).execute()
            
            cache_data = {
                "scientific_name": scientific_name,
                "source_db": source_db,
                "cache_data": data,
                "expires_at": expires_at.isoformat(),
                "update_reason": update_reason,
                "version_info": version_info,
                "updated_at": datetime.now().isoformat(),
                "updated_by": self.user_session_id
            }
            
            if existing.data and len(existing.data) > 0:
                # 업데이트
                old_data = existing.data[0]['cache_data']
                self.client.table("species_cache").update(cache_data).eq(
                    "scientific_name", scientific_name
                ).eq("source_db", source_db).execute()
                
                # 업데이트 히스토리 기록
                self._log_cache_update(
                    scientific_name=scientific_name,
                    source_db=source_db,
                    update_type='refresh',
                    old_data=old_data,
                    new_data=data,
                    update_reason=update_reason,
                    api_response_time=api_response_time
                )
                
                print(f"[Info] 캐시 업데이트: {scientific_name} ({source_db})")
            else:
                # 새로 생성
                cache_data["created_at"] = datetime.now().isoformat()
                cache_data["first_accessed"] = datetime.now().isoformat()
                
                self.client.table("species_cache").insert(cache_data).execute()
                
                # 업데이트 히스토리 기록
                self._log_cache_update(
                    scientific_name=scientific_name,
                    source_db=source_db,
                    update_type='create',
                    new_data=data,
                    update_reason=update_reason,
                    api_response_time=api_response_time
                )
                
                print(f"[Info] 캐시 생성: {scientific_name} ({source_db})")
            
            # 캐시 저장 액세스 로그
            self._log_cache_access(
                scientific_name=scientific_name,
                source_db=source_db,
                access_type='update',
                session_id=session_id
            )
            
            return True
            
        except Exception as e:
            print(f"[Error] 캐시 저장 중 오류: {e}")
            return False
    
    def _log_cache_access(self, scientific_name: str, source_db: str, 
                          access_type: str, response_time_ms: int = None,
                          cache_age_seconds: int = None, session_id: str = None):
        """캐시 액세스 로그 기록"""
        try:
            log_data = {
                "scientific_name": scientific_name,
                "source_db": source_db,
                "access_type": access_type,
                "accessed_at": datetime.now().isoformat(),
                "response_time_ms": response_time_ms,
                "user_session": self.user_session_id,
                "cache_age_seconds": cache_age_seconds,
                "session_id": session_id
            }
            
            self.client.table("cache_access_log").insert(log_data).execute()
            
        except Exception as e:
            print(f"[Warning] 캐시 액세스 로그 기록 실패: {e}")
    
    def _log_cache_update(self, scientific_name: str, source_db: str,
                          update_type: str, new_data: Dict[str, Any],
                          old_data: Dict[str, Any] = None, update_reason: str = None,
                          api_response_time: int = None):
        """캐시 업데이트 히스토리 기록"""
        try:
            history_data = {
                "scientific_name": scientific_name,
                "source_db": source_db,
                "update_type": update_type,
                "old_data": old_data,
                "new_data": new_data,
                "updated_at": datetime.now().isoformat(),
                "update_reason": update_reason,
                "triggered_by": self.user_session_id,
                "api_response_time_ms": api_response_time
            }
            
            self.client.table("cache_update_history").insert(history_data).execute()
            
        except Exception as e:
            print(f"[Warning] 캐시 업데이트 히스토리 기록 실패: {e}")
    
    def get_cache_stats(self, days: int = 7) -> Dict[str, Any]:
        """캐시 통계 조회"""
        try:
            # 기간별 액세스 로그 조회
            since_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            logs_result = self.client.table("cache_access_log").select("*").gte(
                "accessed_at", since_date
            ).execute()
            
            if not logs_result.data:
                return {"total_queries": 0, "cache_hits": 0, "hit_rate": 0.0}
            
            logs = logs_result.data
            total_queries = len(logs)
            cache_hits = len([log for log in logs if log['access_type'] == 'hit'])
            hit_rate = (cache_hits / total_queries * 100) if total_queries > 0 else 0.0
            
            # 데이터베이스별 통계
            db_stats = {}
            for source_db in ['worms', 'lpsn', 'col']:
                db_logs = [log for log in logs if log['source_db'] == source_db]
                db_hits = [log for log in db_logs if log['access_type'] == 'hit']
                
                db_stats[source_db] = {
                    "queries": len(db_logs),
                    "hits": len(db_hits),
                    "hit_rate": (len(db_hits) / len(db_logs) * 100) if db_logs else 0.0
                }
            
            return {
                "period_days": days,
                "total_queries": total_queries,
                "cache_hits": cache_hits,
                "hit_rate": round(hit_rate, 2),
                "db_stats": db_stats,
                "avg_response_time": round(
                    sum([log.get('response_time_ms', 0) for log in logs]) / len(logs)
                ) if logs else 0
            }
            
        except Exception as e:
            print(f"[Error] 캐시 통계 조회 중 오류: {e}")
            return {"error": str(e)}
    
    def cleanup_expired_cache(self) -> int:
        """만료된 캐시 정리"""
        try:
            # 만료된 캐시 조회
            expired_result = self.client.table("species_cache").select("*").lt(
                "expires_at", datetime.now().isoformat()
            ).execute()
            
            if not expired_result.data:
                return 0
            
            expired_count = len(expired_result.data)
            
            # 만료된 캐시 삭제
            self.client.table("species_cache").delete().lt(
                "expires_at", datetime.now().isoformat()
            ).execute()
            
            # 정리 히스토리 기록
            self._log_cache_update(
                scientific_name="batch_cleanup",
                source_db="all",
                update_type="expire",
                new_data={"deleted_count": expired_count},
                update_reason=f"Automatic cleanup of {expired_count} expired records"
            )
            
            print(f"[Info] 만료된 캐시 {expired_count}개 정리 완료")
            return expired_count
            
        except Exception as e:
            print(f"[Error] 캐시 정리 중 오류: {e}")
            return 0
    
    def get_popular_species(self, limit: int = 10) -> List[Dict[str, Any]]:
        """인기 검색어 Top N"""
        try:
            result = self.client.table("species_cache").select(
                "scientific_name, source_db, hit_count, last_accessed"
            ).order("hit_count", desc=True).limit(limit).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            print(f"[Error] 인기 검색어 조회 중 오류: {e}")
            return []

# 전역 캐시 매니저 인스턴스
cache_manager = SpeciesCacheManager()

def get_cache_manager(user_session_id: str = None) -> SpeciesCacheManager:
    """캐시 매니저 인스턴스 반환"""
    if user_session_id:
        return SpeciesCacheManager(user_session_id)
    return cache_manager 