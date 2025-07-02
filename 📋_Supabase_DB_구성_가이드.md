# Supabase 데이터베이스 구성 가이드

## 📋 개요

이 가이드는 Species Verifier 앱을 위한 Supabase 데이터베이스 구성 방법을 설명합니다.

## 🎯 데이터베이스 구조

### 핵심 테이블 설계

#### A. 검증 세션 및 결과 관리

```sql
-- 1. 검증 세션 테이블
verification_sessions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id),
    session_name VARCHAR(255),
    verification_type VARCHAR(50),
    total_items INTEGER,
    verified_count INTEGER,
    skipped_count INTEGER,
    error_count INTEGER,
    start_time TIMESTAMPTZ,
    end_time TIMESTAMPTZ,
    duration_seconds FLOAT,
    status VARCHAR(50),
    error_message TEXT,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
);

-- 2. 검증 결과 테이블
verification_results (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES verification_sessions(id),
    input_name VARCHAR(500),
    scientific_name VARCHAR(500),
    korean_name VARCHAR(500),
    verification_type VARCHAR(50),
    is_verified BOOLEAN,
    verification_status VARCHAR(100),
    
    -- 해양생물 전용 필드
    worms_id VARCHAR(50),
    worms_status VARCHAR(100),
    worms_link TEXT,
    mapped_name VARCHAR(500),
    
    -- 미생물 전용 필드
    valid_name VARCHAR(500),
    taxonomy TEXT,
    lpsn_link TEXT,
    is_microbe BOOLEAN,
    
    -- COL 전용 필드
    col_id VARCHAR(50),
    col_status VARCHAR(100),
    col_rank VARCHAR(50),
    col_classification JSONB,
    
    -- 공통 필드
    wiki_summary TEXT,
    external_links JSONB,
    raw_api_response JSONB,
    
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
);

-- 3. 사용자 즐겨찾기 테이블
user_favorites (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id),
    scientific_name VARCHAR(500),
    korean_name VARCHAR(500),
    verification_type VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMPTZ
);

-- 4. 검증 통계 테이블
verification_stats (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id),
    date DATE,
    verification_type VARCHAR(50),
    total_verifications INTEGER,
    successful_verifications INTEGER,
    success_rate FLOAT,
    avg_processing_time FLOAT,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
);

-- 5. API 사용 로그 테이블
api_usage_logs (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES verification_sessions(id),
    api_name VARCHAR(50),
    endpoint VARCHAR(255),
    request_data JSONB,
    response_status INTEGER,
    response_time_ms INTEGER,
    error_message TEXT,
    created_at TIMESTAMPTZ
);
```

## 🚀 Supabase 프로젝트 설정

### 1. Supabase 프로젝트 생성

1. [Supabase 대시보드](https://app.supabase.com/)에 접속
2. "New Project" 클릭
3. 프로젝트 이름: `species-verifier`
4. 데이터베이스 비밀번호 설정
5. 지역 선택 (한국: ap-northeast-2)

### 2. 데이터베이스 스키마 생성

Supabase SQL Editor에서 다음 스크립트를 실행하세요:

```sql
-- 1. 검증 세션 테이블 생성
CREATE TABLE verification_sessions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id),
    session_name VARCHAR(255),
    verification_type VARCHAR(50) CHECK (verification_type IN ('marine', 'microbe', 'col', 'mixed')),
    total_items INTEGER DEFAULT 0,
    verified_count INTEGER DEFAULT 0,
    skipped_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    start_time TIMESTAMPTZ DEFAULT NOW(),
    end_time TIMESTAMPTZ,
    duration_seconds FLOAT DEFAULT 0.0,
    status VARCHAR(50) DEFAULT 'running',
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. 검증 결과 테이블 생성
CREATE TABLE verification_results (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id UUID REFERENCES verification_sessions(id) ON DELETE CASCADE,
    input_name VARCHAR(500) NOT NULL,
    scientific_name VARCHAR(500),
    korean_name VARCHAR(500),
    verification_type VARCHAR(50) NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE,
    verification_status VARCHAR(100),
    
    -- 해양생물 전용 필드
    worms_id VARCHAR(50),
    worms_status VARCHAR(100),
    worms_link TEXT,
    mapped_name VARCHAR(500),
    
    -- 미생물 전용 필드
    valid_name VARCHAR(500),
    taxonomy TEXT,
    lpsn_link TEXT,
    is_microbe BOOLEAN DEFAULT FALSE,
    
    -- COL 전용 필드
    col_id VARCHAR(50),
    col_status VARCHAR(100),
    col_rank VARCHAR(50),
    col_classification JSONB,
    
    -- 공통 필드
    wiki_summary TEXT DEFAULT '준비 중 (DeepSearch 기능 개발 예정)',
    external_links JSONB,
    raw_api_response JSONB,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. 사용자 즐겨찾기 테이블 생성
CREATE TABLE user_favorites (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id),
    scientific_name VARCHAR(500) NOT NULL,
    korean_name VARCHAR(500),
    verification_type VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. 검증 통계 테이블 생성
CREATE TABLE verification_stats (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id),
    date DATE DEFAULT CURRENT_DATE,
    verification_type VARCHAR(50),
    total_verifications INTEGER DEFAULT 0,
    successful_verifications INTEGER DEFAULT 0,
    success_rate FLOAT DEFAULT 0.0,
    avg_processing_time FLOAT DEFAULT 0.0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(user_id, date, verification_type)
);

-- 5. API 사용 로그 테이블 생성
CREATE TABLE api_usage_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id UUID REFERENCES verification_sessions(id),
    api_name VARCHAR(50) NOT NULL,
    endpoint VARCHAR(255),
    request_data JSONB,
    response_status INTEGER,
    response_time_ms INTEGER,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### B. 스마트 캐싱 시스템 (성능 최적화)

```sql
-- 6. 종 캐시 테이블 (API 응답 캐싱)
CREATE TABLE species_cache (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    scientific_name VARCHAR(500) NOT NULL,
    source_db VARCHAR(50) NOT NULL CHECK (source_db IN ('worms', 'lpsn', 'col')),
    cache_data JSONB NOT NULL,
    
    -- 생성/업데이트 추적
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    update_reason VARCHAR(100) DEFAULT 'initial_creation',
    
    -- 조회 추적
    hit_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMPTZ,
    first_accessed TIMESTAMPTZ DEFAULT NOW(),
    
    -- 버전 및 우선순위
    version_info VARCHAR(100),
    priority_level INTEGER DEFAULT 1,
    updated_by VARCHAR(100) DEFAULT 'system',
    
    UNIQUE(scientific_name, source_db)
);

-- 7. 캐시 액세스 로그 테이블
CREATE TABLE cache_access_log (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    scientific_name VARCHAR(500) NOT NULL,
    source_db VARCHAR(50) NOT NULL,
    access_type VARCHAR(50) NOT NULL CHECK (access_type IN ('hit', 'miss', 'update', 'delete')),
    accessed_at TIMESTAMPTZ DEFAULT NOW(),
    response_time_ms INTEGER,
    user_session VARCHAR(100),
    cache_age_seconds INTEGER,
    session_id UUID REFERENCES verification_sessions(id)
);

-- 8. 캐시 업데이트 이력 테이블
CREATE TABLE cache_update_history (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    scientific_name VARCHAR(500) NOT NULL,
    source_db VARCHAR(50) NOT NULL,
    update_type VARCHAR(50) NOT NULL CHECK (update_type IN ('create', 'refresh', 'expire', 'manual', 'api_mismatch')),
    old_data JSONB,
    new_data JSONB,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    update_reason TEXT,
    triggered_by VARCHAR(100) DEFAULT 'system',
    api_response_time_ms INTEGER
);
```

### 3. 인덱스 생성

```sql
-- 검색 성능을 위한 인덱스
CREATE INDEX idx_verification_results_session_id ON verification_results(session_id);
CREATE INDEX idx_verification_results_scientific_name ON verification_results(scientific_name);
CREATE INDEX idx_verification_results_verification_type ON verification_results(verification_type);
CREATE INDEX idx_verification_results_is_verified ON verification_results(is_verified);
CREATE INDEX idx_verification_results_created_at ON verification_results(created_at);

CREATE INDEX idx_verification_sessions_user_id ON verification_sessions(user_id);
CREATE INDEX idx_verification_sessions_created_at ON verification_sessions(created_at);

CREATE INDEX idx_user_favorites_user_id ON user_favorites(user_id);
CREATE INDEX idx_user_favorites_scientific_name ON user_favorites(scientific_name);

CREATE INDEX idx_verification_stats_user_date ON verification_stats(user_id, date);
CREATE INDEX idx_api_usage_logs_session_id ON api_usage_logs(session_id);

-- 캐싱 시스템을 위한 인덱스
CREATE INDEX idx_species_cache_name_source ON species_cache(scientific_name, source_db);
CREATE INDEX idx_species_cache_expires ON species_cache(expires_at);
CREATE INDEX idx_species_cache_hit_count ON species_cache(hit_count DESC);
CREATE INDEX idx_species_cache_last_accessed ON species_cache(last_accessed);

CREATE INDEX idx_cache_access_log_time ON cache_access_log(accessed_at);
CREATE INDEX idx_cache_access_log_species ON cache_access_log(scientific_name);
CREATE INDEX idx_cache_access_log_type ON cache_access_log(access_type);
CREATE INDEX idx_cache_access_log_session ON cache_access_log(session_id);

CREATE INDEX idx_cache_update_history_time ON cache_update_history(updated_at);
CREATE INDEX idx_cache_update_history_species ON cache_update_history(scientific_name);
CREATE INDEX idx_cache_update_history_type ON cache_update_history(update_type);
```

### 4. Row Level Security (RLS) 설정

```sql
-- RLS 활성화
ALTER TABLE verification_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE verification_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_favorites ENABLE ROW LEVEL SECURITY;
ALTER TABLE verification_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_usage_logs ENABLE ROW LEVEL SECURITY;

-- 사용자별 데이터 접근 정책
CREATE POLICY "Users can only access their own sessions" ON verification_sessions
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can only access their own results" ON verification_results
    FOR ALL USING (auth.uid() = (SELECT user_id FROM verification_sessions WHERE id = session_id));

CREATE POLICY "Users can only access their own favorites" ON user_favorites
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can only access their own stats" ON verification_stats
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can only access their own api logs" ON api_usage_logs
    FOR ALL USING (auth.uid() = (SELECT user_id FROM verification_sessions WHERE id = session_id));

-- 캐시 테이블 RLS 정책 (공용 캐시이므로 읽기는 모든 사용자 허용)
ALTER TABLE species_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE cache_access_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE cache_update_history ENABLE ROW LEVEL SECURITY;

-- 캐시 데이터는 모든 사용자가 읽을 수 있지만, 시스템만 쓰기 가능
CREATE POLICY "Everyone can read cache" ON species_cache FOR SELECT USING (true);
CREATE POLICY "Only system can write cache" ON species_cache FOR ALL USING (auth.uid() = 'system-admin-id'::uuid);

-- 캐시 로그는 사용자별 접근 제한
CREATE POLICY "Users can only see their cache logs" ON cache_access_log
    FOR ALL USING (auth.uid() = (SELECT user_id FROM verification_sessions WHERE id = session_id) OR user_session = auth.uid()::text);

-- 캐시 업데이트 이력은 관리자만 접근
CREATE POLICY "Only admin can access cache history" ON cache_update_history
    FOR ALL USING (auth.uid() = 'system-admin-id'::uuid);
```

### 5. 트리거 함수 생성

```sql
-- updated_at 자동 업데이트 함수
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 트리거 생성
CREATE TRIGGER update_verification_sessions_updated_at 
    BEFORE UPDATE ON verification_sessions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_verification_results_updated_at 
    BEFORE UPDATE ON verification_results 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_verification_stats_updated_at 
    BEFORE UPDATE ON verification_stats 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 세션 통계 자동 업데이트 함수
CREATE OR REPLACE FUNCTION update_session_stats()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
        UPDATE verification_sessions 
        SET 
            total_items = (SELECT COUNT(*) FROM verification_results WHERE session_id = NEW.session_id),
            verified_count = (SELECT COUNT(*) FROM verification_results WHERE session_id = NEW.session_id AND is_verified = TRUE),
            error_count = (SELECT COUNT(*) FROM verification_results WHERE session_id = NEW.session_id AND verification_status LIKE '%오류%'),
            updated_at = NOW()
        WHERE id = NEW.session_id;
        
        RETURN NEW;
    END IF;
    
    RETURN NULL;
END;
$$ language 'plpgsql';

-- 세션 통계 업데이트 트리거
CREATE TRIGGER update_session_stats_trigger 
    AFTER INSERT OR UPDATE ON verification_results 
    FOR EACH ROW EXECUTE FUNCTION update_session_stats();

-- 캐시 히트 카운트 자동 업데이트 함수
CREATE OR REPLACE FUNCTION update_cache_hit_count()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.access_type = 'hit' THEN
        UPDATE species_cache 
        SET 
            hit_count = hit_count + 1,
            last_accessed = NOW()
        WHERE scientific_name = NEW.scientific_name 
        AND source_db = NEW.source_db;
    END IF;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 캐시 히트 카운트 업데이트 트리거
CREATE TRIGGER update_cache_hit_count_trigger 
    AFTER INSERT ON cache_access_log 
    FOR EACH ROW EXECUTE FUNCTION update_cache_hit_count();

-- 만료된 캐시 자동 정리 함수
CREATE OR REPLACE FUNCTION cleanup_expired_cache()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM species_cache WHERE expires_at < NOW();
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    INSERT INTO cache_update_history (
        scientific_name, source_db, update_type, update_reason, triggered_by
    )
    SELECT 
        'batch_cleanup', 'all', 'expire', 
        'Automatic cleanup of ' || deleted_count || ' expired records',
        'system'
    WHERE deleted_count > 0;
    
    RETURN deleted_count;
END;
$$ language 'plpgsql';
```

## 🔧 앱 설정

### 1. 환경 변수 설정

`.env` 파일을 생성하고 다음 내용을 추가하세요:

```env
# Supabase 설정
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here

# 기존 API 설정들...
```

### 2. 의존성 설치

```powershell
pip install supabase pydantic python-dotenv
```

### 3. 데이터베이스 연결 테스트

```python
from species_verifier.database.supabase_client import supabase_client

# 연결 테스트
if supabase_client.test_connection():
    print("✅ Supabase 연결 성공!")
else:
    print("❌ Supabase 연결 실패")
```

## 📊 사용 예시

### 1. 검증 세션 생성 및 결과 저장

```python
from species_verifier.database.integration import get_verification_integrator

integrator = get_verification_integrator()

# 해양생물 검증
result = integrator.verify_and_save_marine_species(
    species_list=["Homo sapiens", "Canis lupus"],
    session_name="테스트 검증",
    user_id="user-uuid-here"
)

print(f"세션 ID: {result['session_id']}")
print(f"검증 결과: {len(result['results'])}개")
```

### 2. 검증 결과 조회

```python
# 세션 결과 조회
session_results = integrator.get_session_results(session_id)
print(f"세션 정보: {session_results['session']}")
print(f"결과 개수: {len(session_results['results'])}")

# 종 검색
search_results = integrator.search_previous_results(
    query="Homo",
    verification_type=VerificationType.MARINE
)
print(f"검색 결과: {len(search_results)}개")
```

### 3. 즐겨찾기 관리

```python
from species_verifier.database.services import get_database_service
from species_verifier.database.models import VerificationType

db_service = get_database_service()

# 즐겨찾기 추가
db_service.add_to_favorites(
    user_id="user-uuid",
    scientific_name="Homo sapiens",
    korean_name="사람",
    verification_type=VerificationType.MARINE,
    notes="테스트 즐겨찾기"
)

# 즐겨찾기 조회
favorites = db_service.get_user_favorites("user-uuid")
print(f"즐겨찾기: {len(favorites)}개")
```

## 🎛️ 관리 기능

### 데이터 백업

```sql
-- 전체 데이터 백업
SELECT * FROM verification_sessions;
SELECT * FROM verification_results;
SELECT * FROM user_favorites;
SELECT * FROM verification_stats;
SELECT * FROM api_usage_logs;
```

### 성능 모니터링

```sql
-- 세션별 성능 통계
SELECT 
    verification_type,
    COUNT(*) as session_count,
    AVG(duration_seconds) as avg_duration,
    AVG(verified_count::float / total_items * 100) as avg_success_rate
FROM verification_sessions
WHERE status = 'completed'
GROUP BY verification_type;

-- 일별 사용량 통계
SELECT 
    DATE(created_at) as date,
    COUNT(*) as daily_sessions,
    SUM(total_items) as total_items_processed
FROM verification_sessions
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

## 🚀 성능 최적화 및 캐싱 전략

### 캐싱 시스템 활용

```python
# 캐시 매니저 사용 예시
from species_verifier.database.cache_manager import SpeciesCacheManager

cache_manager = SpeciesCacheManager()

# 캐시된 데이터 조회
cached_result = cache_manager.get_cache("Homo sapiens", "worms")
if cached_result:
    print("캐시에서 즉시 반환!")
else:
    # API 호출 후 캐시에 저장
    api_result = call_worms_api("Homo sapiens")
    cache_manager.set_cache("Homo sapiens", "worms", api_result)
```

### 데이터베이스별 캐시 전략

1. **WoRMS (해양생물)**: 30일 캐시, 월별 업데이트
2. **LPSN (미생물)**: 21일 캐시, 격주 업데이트  
3. **COL (일반생물)**: 30일 캐시, 월간 업데이트

### 예상 성능 개선

- **응답 시간**: 6-8초 → 0.1-0.3초 (90% 개선)
- **API 호출**: 90% 감소
- **서버 부담**: 대폭 감소

## 🔧 고급 관리 기능

### 캐시 통계 및 모니터링

```sql
-- 캐시 히트율 통계
SELECT 
    source_db,
    COUNT(*) as total_queries,
    SUM(CASE WHEN access_type = 'hit' THEN 1 ELSE 0 END) as cache_hits,
    ROUND(
        SUM(CASE WHEN access_type = 'hit' THEN 1 ELSE 0 END)::float / COUNT(*) * 100, 2
    ) as hit_rate_percent
FROM cache_access_log
WHERE accessed_at >= NOW() - INTERVAL '7 days'
GROUP BY source_db;

-- 인기 검색어 Top 10
SELECT 
    scientific_name,
    SUM(hit_count) as total_hits,
    MAX(last_accessed) as last_accessed
FROM species_cache
GROUP BY scientific_name
ORDER BY total_hits DESC
LIMIT 10;
```

### 자동 캐시 정리

```sql
-- 매일 자동 실행할 캐시 정리 작업
SELECT cleanup_expired_cache(); -- 만료된 캐시 삭제

-- 한 달에 한 번 실행할 통계 정리
DELETE FROM cache_access_log 
WHERE accessed_at < NOW() - INTERVAL '3 months';
```

## 🚨 주의 사항

1. **RLS 정책**: 모든 테이블에 Row Level Security가 활성화되어 있어 사용자는 자신의 데이터만 접근 가능합니다.

2. **캐시 전략**: 각 데이터베이스별로 다른 캐시 유효기간을 적용하여 최적화합니다.

3. **대용량 데이터**: 검증 결과가 많은 경우 배치 처리를 통해 성능을 최적화합니다.

4. **API 제한**: 캐싱을 통해 외부 API 호출량을 90% 감소시켜 제한을 방지합니다.

5. **백업**: 정기적으로 데이터를 백업하여 데이터 손실을 방지합니다.

6. **모니터링**: 캐시 히트율과 API 사용 로그를 통해 시스템 성능을 실시간 모니터링합니다.

7. **캐시 정리**: 만료된 캐시는 자동으로 정리되며, 오래된 로그는 정기적으로 삭제합니다.

이 가이드를 따라 설정하면 Species Verifier 앱이 Supabase 데이터베이스와 완전히 통합되어 사용 가능합니다! 🎉 