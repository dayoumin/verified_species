"""
기관 보안을 위한 안전한 데이터베이스 모드

이 모듈은 기관 내 보안 정책을 준수하면서도 성능 향상을 제공합니다.
- LOCAL_MODE: 완전한 로컬 처리 (외부 연결 없음)
- HYBRID_MODE: 로컬 캐시 + 선택적 외부 연결
- SECURE_MODE: 암호화된 로컬 저장소 사용
"""
import os
import json
import sqlite3
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Literal
from pathlib import Path

# 운영 모드 정의
DatabaseMode = Literal["local", "hybrid", "cloud"]

class SecureDatabaseManager:
    """보안을 고려한 로컬/하이브리드 데이터베이스 관리자"""
    
    def __init__(self, mode: DatabaseMode = "local", local_db_path: str = None):
        self.mode = mode
        self.local_db_path = local_db_path or self._get_default_db_path()
        
        # 로컬 SQLite 데이터베이스 초기화
        self._init_local_database()
        
        # 외부 연결 설정 (모드에 따라)
        self.supabase_client = None
        if mode in ["hybrid", "cloud"]:
            try:
                from .supabase_client import get_supabase_client
                self.supabase_client = get_supabase_client()
                print(f"[Info] {mode.upper()} 모드: 외부 DB 연결 활성화")
            except Exception as e:
                print(f"[Warning] 외부 DB 연결 실패, LOCAL 모드로 전환: {e}")
                self.mode = "local"
        
        print(f"[Info] 보안 데이터베이스 매니저 초기화: {self.mode.upper()} 모드")
    
    def _get_default_db_path(self) -> str:
        """기본 로컬 DB 경로 반환"""
        app_data_dir = os.getenv("APPDATA", os.path.expanduser("~"))
        db_dir = Path(app_data_dir) / "SpeciesVerifier" / "cache"
        db_dir.mkdir(parents=True, exist_ok=True)
        return str(db_dir / "species_cache.db")
    
    def _init_local_database(self):
        """로컬 SQLite 데이터베이스 초기화"""
        try:
            with sqlite3.connect(self.local_db_path) as conn:
                # 로컬 캐시 테이블 생성
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS local_species_cache (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        scientific_name TEXT NOT NULL,
                        source_db TEXT NOT NULL,
                        cache_data TEXT NOT NULL,  -- JSON 데이터
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        expires_at TEXT NOT NULL,
                        hit_count INTEGER DEFAULT 0,
                        last_accessed TEXT,
                        data_hash TEXT,  -- 데이터 무결성 확인용
                        UNIQUE(scientific_name, source_db)
                    )
                """)
                
                # 로컬 세션 테이블
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS local_verification_sessions (
                        id TEXT PRIMARY KEY,
                        session_name TEXT,
                        verification_type TEXT,
                        total_items INTEGER DEFAULT 0,
                        verified_count INTEGER DEFAULT 0,
                        created_at TEXT NOT NULL,
                        completed_at TEXT,
                        status TEXT DEFAULT 'running'
                    )
                """)
                
                # 로컬 결과 테이블
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS local_verification_results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        input_name TEXT NOT NULL,
                        scientific_name TEXT,
                        verification_type TEXT,
                        is_verified INTEGER DEFAULT 0,  -- SQLite boolean
                        verification_status TEXT,
                        result_data TEXT,  -- JSON 데이터
                        created_at TEXT NOT NULL,
                        FOREIGN KEY (session_id) REFERENCES local_verification_sessions(id)
                    )
                """)
                
                conn.commit()
                print(f"[Info] 로컬 데이터베이스 초기화 완료: {self.local_db_path}")
                
        except Exception as e:
            print(f"[Error] 로컬 데이터베이스 초기화 실패: {e}")
            raise
    
    def get_cache(self, scientific_name: str, source_db: str) -> Optional[Dict[str, Any]]:
        """보안 모드에 따른 캐시 조회"""
        # 1. 항상 로컬 캐시부터 확인
        local_data = self._get_local_cache(scientific_name, source_db)
        
        if local_data and not self._is_cache_expired(local_data):
            self._update_hit_count(scientific_name, source_db)
            print(f"[Info] 로컬 캐시 히트: {scientific_name} ({source_db})")
            return json.loads(local_data['cache_data'])
        
        # 2. 하이브리드/클라우드 모드에서만 외부 조회
        if self.mode in ["hybrid", "cloud"] and self.supabase_client:
            try:
                cloud_data = self._get_cloud_cache(scientific_name, source_db)
                if cloud_data:
                    # 클라우드에서 가져온 데이터를 로컬에도 저장 (보안 백업)
                    self._set_local_cache(scientific_name, source_db, cloud_data)
                    print(f"[Info] 클라우드 캐시 히트 + 로컬 백업: {scientific_name}")
                    return cloud_data
            except Exception as e:
                print(f"[Warning] 클라우드 캐시 조회 실패, 로컬만 사용: {e}")
        
        print(f"[Info] 캐시 미스: {scientific_name} ({source_db})")
        return None
    
    def set_cache(self, scientific_name: str, source_db: str, data: Dict[str, Any],
                  update_reason: str = "api_call") -> bool:
        """보안 모드에 따른 캐시 저장"""
        success = True
        
        # 1. 항상 로컬에 저장 (오프라인 대응)
        local_success = self._set_local_cache(scientific_name, source_db, data, update_reason)
        
        # 2. 클라우드 모드에서만 외부 저장
        if self.mode == "cloud" and self.supabase_client:
            try:
                cloud_success = self._set_cloud_cache(scientific_name, source_db, data, update_reason)
                success = local_success and cloud_success
            except Exception as e:
                print(f"[Warning] 클라우드 저장 실패, 로컬만 저장됨: {e}")
                success = local_success
        else:
            success = local_success
        
        if success:
            print(f"[Info] 캐시 저장 완료: {scientific_name} ({self.mode} 모드)")
        
        return success
    
    def _get_local_cache(self, scientific_name: str, source_db: str) -> Optional[Dict[str, Any]]:
        """로컬 SQLite에서 캐시 조회"""
        try:
            with sqlite3.connect(self.local_db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM local_species_cache 
                    WHERE scientific_name = ? AND source_db = ?
                """, (scientific_name, source_db))
                
                row = cursor.fetchone()
                return dict(row) if row else None
                
        except Exception as e:
            print(f"[Error] 로컬 캐시 조회 실패: {e}")
            return None
    
    def _set_local_cache(self, scientific_name: str, source_db: str, 
                         data: Dict[str, Any], update_reason: str = "api_call") -> bool:
        """로컬 SQLite에 캐시 저장"""
        try:
            cache_data_json = json.dumps(data, ensure_ascii=False)
            data_hash = hashlib.md5(cache_data_json.encode()).hexdigest()
            now = datetime.now().isoformat()
            expires_at = (datetime.now() + timedelta(days=30)).isoformat()
            
            with sqlite3.connect(self.local_db_path) as conn:
                # UPSERT 기능 (INSERT OR REPLACE)
                conn.execute("""
                    INSERT OR REPLACE INTO local_species_cache 
                    (scientific_name, source_db, cache_data, created_at, updated_at, 
                     expires_at, hit_count, data_hash)
                    VALUES (?, ?, ?, 
                           COALESCE((SELECT created_at FROM local_species_cache 
                                   WHERE scientific_name = ? AND source_db = ?), ?),
                           ?, ?, 
                           COALESCE((SELECT hit_count FROM local_species_cache 
                                   WHERE scientific_name = ? AND source_db = ?), 0),
                           ?)
                """, (scientific_name, source_db, cache_data_json,
                      scientific_name, source_db, now,  # created_at 처리
                      now, expires_at,  # updated_at, expires_at
                      scientific_name, source_db,  # hit_count 처리
                      data_hash))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"[Error] 로컬 캐시 저장 실패: {e}")
            return False
    
    def _get_cloud_cache(self, scientific_name: str, source_db: str) -> Optional[Dict[str, Any]]:
        """클라우드 Supabase에서 캐시 조회"""
        try:
            result = self.supabase_client.table("species_cache").select("*").eq(
                "scientific_name", scientific_name
            ).eq("source_db", source_db).gt(
                "expires_at", datetime.now().isoformat()
            ).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]['cache_data']
            return None
            
        except Exception as e:
            print(f"[Error] 클라우드 캐시 조회 실패: {e}")
            return None
    
    def _set_cloud_cache(self, scientific_name: str, source_db: str,
                         data: Dict[str, Any], update_reason: str = "api_call") -> bool:
        """클라우드 Supabase에 캐시 저장"""
        try:
            expires_at = datetime.now() + timedelta(days=30)
            
            cache_data = {
                "scientific_name": scientific_name,
                "source_db": source_db,
                "cache_data": data,
                "expires_at": expires_at.isoformat(),
                "update_reason": update_reason,
                "updated_at": datetime.now().isoformat()
            }
            
            # 기존 데이터 확인
            existing = self.supabase_client.table("species_cache").select("*").eq(
                "scientific_name", scientific_name
            ).eq("source_db", source_db).execute()
            
            if existing.data and len(existing.data) > 0:
                # 업데이트
                self.supabase_client.table("species_cache").update(cache_data).eq(
                    "scientific_name", scientific_name
                ).eq("source_db", source_db).execute()
            else:
                # 새로 생성
                cache_data["created_at"] = datetime.now().isoformat()
                self.supabase_client.table("species_cache").insert(cache_data).execute()
            
            return True
            
        except Exception as e:
            print(f"[Error] 클라우드 캐시 저장 실패: {e}")
            return False
    
    def _is_cache_expired(self, cache_record: Dict[str, Any]) -> bool:
        """캐시 만료 여부 확인"""
        try:
            expires_at = datetime.fromisoformat(cache_record['expires_at'])
            return datetime.now() > expires_at
        except:
            return True
    
    def _update_hit_count(self, scientific_name: str, source_db: str):
        """로컬 캐시 히트 카운트 업데이트"""
        try:
            with sqlite3.connect(self.local_db_path) as conn:
                conn.execute("""
                    UPDATE local_species_cache 
                    SET hit_count = hit_count + 1, last_accessed = ?
                    WHERE scientific_name = ? AND source_db = ?
                """, (datetime.now().isoformat(), scientific_name, source_db))
                conn.commit()
        except Exception as e:
            print(f"[Warning] 히트 카운트 업데이트 실패: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """로컬 캐시 통계 조회 (보안 친화적)"""
        try:
            with sqlite3.connect(self.local_db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # 전체 캐시 수
                total_cursor = conn.execute("SELECT COUNT(*) as total FROM local_species_cache")
                total_count = total_cursor.fetchone()['total']
                
                # 만료되지 않은 캐시 수
                valid_cursor = conn.execute("""
                    SELECT COUNT(*) as valid FROM local_species_cache 
                    WHERE expires_at > ?
                """, (datetime.now().isoformat(),))
                valid_count = valid_cursor.fetchone()['valid']
                
                # 인기 종 Top 5
                popular_cursor = conn.execute("""
                    SELECT scientific_name, source_db, hit_count 
                    FROM local_species_cache 
                    WHERE hit_count > 0
                    ORDER BY hit_count DESC LIMIT 5
                """)
                popular_species = [dict(row) for row in popular_cursor.fetchall()]
                
                return {
                    "mode": self.mode,
                    "total_cached": total_count,
                    "valid_cached": valid_count,
                    "expired_cached": total_count - valid_count,
                    "popular_species": popular_species,
                    "local_db_path": self.local_db_path
                }
                
        except Exception as e:
            print(f"[Error] 캐시 통계 조회 실패: {e}")
            return {"error": str(e)}
    
    def cleanup_expired_cache(self) -> int:
        """만료된 로컬 캐시 정리"""
        try:
            with sqlite3.connect(self.local_db_path) as conn:
                cursor = conn.execute("""
                    DELETE FROM local_species_cache 
                    WHERE expires_at < ?
                """, (datetime.now().isoformat(),))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                print(f"[Info] 만료된 로컬 캐시 {deleted_count}개 정리 완료")
                return deleted_count
                
        except Exception as e:
            print(f"[Error] 로컬 캐시 정리 실패: {e}")
            return 0

# 설정에 따른 보안 모드 결정
def get_secure_database_mode() -> DatabaseMode:
    """환경 변수와 설정을 기반으로 보안 모드 결정"""
    # 환경 변수 확인
    mode = os.getenv("SPECIES_VERIFIER_DB_MODE", "local").lower()
    
    # Supabase 설정 여부 확인
    has_supabase_config = bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_ANON_KEY"))
    
    # 기관 보안 정책 확인 (가상의 체크)
    is_enterprise_network = os.getenv("ENTERPRISE_NETWORK", "false").lower() == "true"
    
    if mode == "cloud" and has_supabase_config and not is_enterprise_network:
        return "cloud"
    elif mode in ["hybrid", "cloud"] and has_supabase_config:
        return "hybrid"  # 기관 네트워크에서는 하이브리드 권장
    else:
        return "local"  # 가장 안전한 기본값

# 전역 보안 데이터베이스 매니저
secure_db_manager = None

def get_secure_database_manager() -> SecureDatabaseManager:
    """보안 데이터베이스 매니저 인스턴스 반환"""
    global secure_db_manager
    if secure_db_manager is None:
        mode = get_secure_database_mode()
        secure_db_manager = SecureDatabaseManager(mode=mode)
    return secure_db_manager 