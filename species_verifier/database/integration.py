"""
기존 Species Verifier와 Supabase 데이터베이스 통합

이 모듈은 기존의 검증 시스템과 새로운 데이터베이스 기능을 연결합니다.
- 보안 모드 지원 (LOCAL/HYBRID/CLOUD)
- 실시간 검증 결과와 캐시 비교
- 월간 자동 업데이트 스케줄링
"""
import time
from typing import List, Dict, Any, Optional
from ..models.verification_results import (
    MarineVerificationResult, MicrobeVerificationResult, VerificationSummary
)
from .services import DatabaseService
from .cache_manager import get_cache_manager
from .secure_mode import get_secure_database_manager
from .scheduler import get_cache_scheduler

class VerificationDatabaseIntegrator:
    """검증 시스템과 데이터베이스 통합 관리자 (보안 모드 지원)"""
    
    def __init__(self, user_session_id: str = None):
        self.db_service = DatabaseService()
        self.cache_manager = get_cache_manager(user_session_id)
        self.secure_db = get_secure_database_manager()
        self.scheduler = get_cache_scheduler()
        self.user_session_id = user_session_id or f"session_{int(time.time())}"
        
        print(f"[Info] 데이터베이스 통합 시스템 초기화 완료 ({self.secure_db.mode.upper()} 모드)")
    
    def verify_marine_species_with_cache(self, scientific_names: List[str], 
                                         session_name: str = None,
                                         use_real_time_validation: bool = True) -> VerificationSummary:
        """해양생물 검증 + 실시간 캐시 비교 업데이트"""
        
        print(f"[Info] 해양생물 검증 시작: {len(scientific_names)}개 종 (실시간 검증: {use_real_time_validation})")
        
        # 검증 세션 생성
        session_id = self.db_service.create_verification_session(
            session_name=session_name or f"Marine Species Verification",
            verification_type="marine",
            total_items=len(scientific_names),
            user_session=self.user_session_id
        )
        
        results = []
        verified_count = 0
        
        try:
            for i, scientific_name in enumerate(scientific_names, 1):
                print(f"[Info] 진행: {i}/{len(scientific_names)} - {scientific_name}")
                
                try:
                    if use_real_time_validation:
                        # 실시간 검증 + 캐시 비교 업데이트
                        from ..core.verifier import check_worms_record
                        verification_result = self.scheduler.verify_and_update_cache(
                            scientific_name, 'worms', check_worms_record
                        )
                        
                        marine_data = verification_result.get('data')
                        update_status = verification_result.get('status')
                        
                        if marine_data:
                            # 검증 결과 생성
                            result = MarineVerificationResult(
                                input_name=scientific_name,
                                scientific_name=marine_data.get('scientific_name', scientific_name),
                                is_verified=marine_data.get('status') == 'valid',
                                worms_data=marine_data,
                                verification_status=f"verified_with_cache_{update_status}"
                            )
                            verified_count += 1
                        else:
                            result = MarineVerificationResult(
                                input_name=scientific_name,
                                scientific_name=scientific_name,
                                is_verified=False,
                                verification_status="api_failed"
                            )
                    else:
                        # 기본 캐시 우선 검증
                        cached_data = self.secure_db.get_cache(scientific_name, 'worms')
                        
                        if cached_data:
                            result = MarineVerificationResult(
                                input_name=scientific_name,
                                scientific_name=cached_data.get('scientific_name', scientific_name),
                                is_verified=cached_data.get('status') == 'valid',
                                worms_data=cached_data,
                                verification_status="cache_hit"
                            )
                            if result.is_verified:
                                verified_count += 1
                        else:
                            # 캐시 미스 시 API 호출
                            from ..core.verifier import check_worms_record
                            fresh_data = check_worms_record(scientific_name)
                            
                            if fresh_data:
                                # 새 데이터 캐시에 저장
                                self.secure_db.set_cache(scientific_name, 'worms', fresh_data)
                                
                                result = MarineVerificationResult(
                                    input_name=scientific_name,
                                    scientific_name=fresh_data.get('scientific_name', scientific_name),
                                    is_verified=fresh_data.get('status') == 'valid',
                                    worms_data=fresh_data,
                                    verification_status="api_fresh"
                                )
                                if result.is_verified:
                                    verified_count += 1
                            else:
                                result = MarineVerificationResult(
                                    input_name=scientific_name,
                                    scientific_name=scientific_name,
                                    is_verified=False,
                                    verification_status="not_found"
                                )
                    
                    results.append(result)
                    
                    # 결과를 데이터베이스에 저장
                    self.db_service.save_verification_result(
                        session_id=session_id,
                        result=result,
                        verification_type="marine"
                    )
                    
                    # API 호출 간격 (서버 부담 방지)
                    time.sleep(0.5)
                    
                except Exception as item_error:
                    print(f"[Warning] {scientific_name} 검증 실패: {item_error}")
                    # 실패한 항목도 기록
                    error_result = MarineVerificationResult(
                        input_name=scientific_name,
                        scientific_name=scientific_name,
                        is_verified=False,
                        verification_status=f"error: {str(item_error)}"
                    )
                    results.append(error_result)
            
            # 세션 완료 처리
            self.db_service.complete_verification_session(session_id, verified_count)
            
            # 검증 결과 요약
            summary = VerificationSummary(
                session_id=session_id,
                total_items=len(scientific_names),
                verified_count=verified_count,
                unverified_count=len(scientific_names) - verified_count,
                marine_results=results,
                verification_method=f"{self.secure_db.mode}_mode_with_real_time_validation" if use_real_time_validation else f"{self.secure_db.mode}_mode_cache_first",
                database_stats=self.secure_db.get_cache_stats()
            )
            
            print(f"[Info] 해양생물 검증 완료: {verified_count}/{len(scientific_names)}개 성공")
            return summary
            
        except Exception as e:
            print(f"[Error] 해양생물 검증 중 오류: {e}")
            # 세션 실패 처리
            self.db_service.fail_verification_session(session_id, str(e))
            raise
    
    def verify_microbe_species_with_cache(self, scientific_names: List[str],
                                          session_name: str = None,
                                          use_real_time_validation: bool = True) -> VerificationSummary:
        """미생물 검증 + 실시간 캐시 비교 업데이트"""
        
        print(f"[Info] 미생물 검증 시작: {len(scientific_names)}개 종 (실시간 검증: {use_real_time_validation})")
        
        # 검증 세션 생성
        session_id = self.db_service.create_verification_session(
            session_name=session_name or f"Microbe Species Verification",
            verification_type="microbe",
            total_items=len(scientific_names),
            user_session=self.user_session_id
        )
        
        results = []
        verified_count = 0
        
        try:
            for i, scientific_name in enumerate(scientific_names, 1):
                print(f"[Info] 진행: {i}/{len(scientific_names)} - {scientific_name}")
                
                try:
                    if use_real_time_validation:
                        # 실시간 검증 + 캐시 비교 업데이트
                        from ..core.verifier import verify_single_microbe_lpsn
                        verification_result = self.scheduler.verify_and_update_cache(
                            scientific_name, 'lpsn', verify_single_microbe_lpsn
                        )
                        
                        microbe_data = verification_result.get('data')
                        update_status = verification_result.get('status')
                        
                        if microbe_data:
                            result = MicrobeVerificationResult(
                                input_name=scientific_name,
                                scientific_name=microbe_data.get('scientific_name', scientific_name),
                                is_verified=microbe_data.get('status') == 'valid',
                                lpsn_data=microbe_data,
                                verification_status=f"verified_with_cache_{update_status}"
                            )
                            verified_count += 1
                        else:
                            result = MicrobeVerificationResult(
                                input_name=scientific_name,
                                scientific_name=scientific_name,
                                is_verified=False,
                                verification_status="api_failed"
                            )
                    else:
                        # 기본 캐시 우선 검증
                        cached_data = self.secure_db.get_cache(scientific_name, 'lpsn')
                        
                        if cached_data:
                            result = MicrobeVerificationResult(
                                input_name=scientific_name,
                                scientific_name=cached_data.get('scientific_name', scientific_name),
                                is_verified=cached_data.get('status') == 'valid',
                                lpsn_data=cached_data,
                                verification_status="cache_hit"
                            )
                            if result.is_verified:
                                verified_count += 1
                        else:
                            # 캐시 미스 시 API 호출
                            from ..core.verifier import verify_single_microbe_lpsn
                            fresh_data = verify_single_microbe_lpsn(scientific_name)
                            
                            if fresh_data:
                                # 새 데이터 캐시에 저장
                                self.secure_db.set_cache(scientific_name, 'lpsn', fresh_data)
                                
                                result = MicrobeVerificationResult(
                                    input_name=scientific_name,
                                    scientific_name=fresh_data.get('scientific_name', scientific_name),
                                    is_verified=fresh_data.get('status') == 'valid',
                                    lpsn_data=fresh_data,
                                    verification_status="api_fresh"
                                )
                                if result.is_verified:
                                    verified_count += 1
                            else:
                                result = MicrobeVerificationResult(
                                    input_name=scientific_name,
                                    scientific_name=scientific_name,
                                    is_verified=False,
                                    verification_status="not_found"
                                )
                    
                    results.append(result)
                    
                    # 결과를 데이터베이스에 저장
                    self.db_service.save_verification_result(
                        session_id=session_id,
                        result=result,
                        verification_type="microbe"
                    )
                    
                    # API 호출 간격 (LPSN은 더 안전하게)
                    time.sleep(1.0)
                    
                except Exception as item_error:
                    print(f"[Warning] {scientific_name} 검증 실패: {item_error}")
                    error_result = MicrobeVerificationResult(
                        input_name=scientific_name,
                        scientific_name=scientific_name,
                        is_verified=False,
                        verification_status=f"error: {str(item_error)}"
                    )
                    results.append(error_result)
            
            # 세션 완료 처리  
            self.db_service.complete_verification_session(session_id, verified_count)
            
            # 검증 결과 요약
            summary = VerificationSummary(
                session_id=session_id,
                total_items=len(scientific_names),
                verified_count=verified_count,
                unverified_count=len(scientific_names) - verified_count,
                microbe_results=results,
                verification_method=f"{self.secure_db.mode}_mode_with_real_time_validation" if use_real_time_validation else f"{self.secure_db.mode}_mode_cache_first",
                database_stats=self.secure_db.get_cache_stats()
            )
            
            print(f"[Info] 미생물 검증 완료: {verified_count}/{len(scientific_names)}개 성공")
            return summary
            
        except Exception as e:
            print(f"[Error] 미생물 검증 중 오류: {e}")
            self.db_service.fail_verification_session(session_id, str(e))
            raise
    
    def get_user_favorites_with_cache_info(self, limit: int = 10) -> List[Dict[str, Any]]:
        """사용자 즐겨찾기 + 캐시 정보 조회"""
        try:
            favorites = self.db_service.get_user_favorites(
                user_session=self.user_session_id, limit=limit
            )
            
            # 각 즐겨찾기 항목에 캐시 정보 추가
            enhanced_favorites = []
            for fav in favorites:
                scientific_name = fav['scientific_name']
                verification_type = fav['verification_type']
                
                # 데이터베이스 분류에 따른 소스 DB 결정
                source_db = self._get_source_db_by_type(verification_type)
                
                # 캐시 상태 확인
                cached_data = self.secure_db.get_cache(scientific_name, source_db)
                
                enhanced_fav = fav.copy()
                enhanced_fav.update({
                    'cache_status': 'cached' if cached_data else 'not_cached',
                    'source_database': source_db,
                    'last_cache_update': cached_data.get('updated_at') if cached_data else None,
                    'cache_expires_at': cached_data.get('expires_at') if cached_data else None
                })
                
                enhanced_favorites.append(enhanced_fav)
            
            return enhanced_favorites
            
        except Exception as e:
            print(f"[Error] 즐겨찾기 조회 중 오류: {e}")
            return []
    
    def _get_source_db_by_type(self, verification_type: str) -> str:
        """검증 타입에 따른 소스 데이터베이스 반환"""
        type_mapping = {
            'marine': 'worms',      # 해양생물 → WoRMS
            'microbe': 'lpsn',      # 미생물 → LPSN  
            'freshwater': 'col',    # 담수생물 → COL (향후)
            'general': 'col'        # 일반생물 → COL (향후)
        }
        return type_mapping.get(verification_type, 'col')
    
    def run_monthly_cache_update(self, target_database: str = None) -> Dict[str, Any]:
        """월간 캐시 업데이트 실행 (보안 모드 고려)"""
        print(f"[Info] 월간 캐시 업데이트 시작 (보안 모드: {self.secure_db.mode.upper()})")
        
        if self.secure_db.mode == "local":
            print("[Info] LOCAL 모드: 로컬 캐시만 정리합니다")
            # 로컬 모드에서는 만료된 캐시만 정리
            cleanup_count = self.secure_db.cleanup_expired_cache()
            return {
                "mode": "local",
                "cleanup_count": cleanup_count,
                "message": "로컬 모드에서는 외부 API 업데이트를 수행하지 않습니다"
            }
        
        # HYBRID/CLOUD 모드에서는 실제 업데이트 수행
        result = self.scheduler.schedule_monthly_update(
            target_db=target_database,
            min_usage_count=3,  # 최소 3회 이상 사용된 종만 업데이트
            max_items_per_run=50  # 한 번에 최대 50개 (기관 네트워크 고려)
        )
        
        result["mode"] = self.secure_db.mode
        return result
    
    def get_integrated_system_status(self) -> Dict[str, Any]:
        """통합 시스템 상태 조회"""
        try:
            # 캐시 통계
            cache_stats = self.secure_db.get_cache_stats()
            
            # 스케줄 정보
            schedule_info = self.scheduler.get_update_schedule_info()
            
            # 데이터베이스 서비스 통계 (최근 7일)
            db_stats = self.db_service.get_verification_statistics(days=7)
            
            return {
                "system_mode": self.secure_db.mode.upper(),
                "cache_statistics": cache_stats,
                "update_schedule": schedule_info,
                "verification_statistics": db_stats,
                "database_classifications": {
                    "해양생물": "WoRMS API + 캐시",
                    "미생물": "LPSN API + 캐시", 
                    "담수생물": "COL API + 캐시 (계획중)",
                    "일반생물": "COL API + 캐시 (계획중)"
                },
                "performance_improvements": {
                    "cache_hit_rate": cache_stats.get('hit_rate', 0),
                    "avg_response_time_ms": cache_stats.get('avg_response_time', 0),
                    "estimated_api_calls_saved": cache_stats.get('cache_hits', 0)
                }
            }
            
        except Exception as e:
            print(f"[Error] 시스템 상태 조회 중 오류: {e}")
            return {"error": str(e)}

# 전역 통합 시스템 인스턴스
integrator = None

def get_verification_integrator(user_session_id: str = None) -> VerificationDatabaseIntegrator:
    """검증 데이터베이스 통합 시스템 인스턴스 반환"""
    global integrator
    if integrator is None or user_session_id:
        integrator = VerificationDatabaseIntegrator(user_session_id)
    return integrator 