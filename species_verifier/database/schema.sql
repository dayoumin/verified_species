-- Species Verifier 하이브리드 검색 시스템 스키마
-- 실시간 검색 결과를 캐싱하고 업데이트 날짜를 관리합니다.

-- 1. 해양생물 검증 결과 (WoRMS)
CREATE TABLE marine_species_cache (
    id SERIAL PRIMARY KEY,
    input_name VARCHAR(255) NOT NULL,           -- 사용자가 입력한 학명
    scientific_name VARCHAR(255),               -- 정규화된 학명
    worms_id INTEGER,                          -- WoRMS AphiaID
    worms_status VARCHAR(100),                 -- WoRMS 상태 (accepted, unaccepted 등)
    is_verified BOOLEAN DEFAULT FALSE,          -- 검증 성공 여부
    classification JSONB,                       -- 분류학적 정보 (JSON)
    worms_url TEXT,                            -- WoRMS 상세 페이지 URL
    wiki_summary TEXT,                         -- 위키 요약 정보
    
    -- 캐시 관리 필드
    last_verified_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),  -- 마지막 검증 일시
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),        -- 최초 생성 일시
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),        -- 마지막 업데이트 일시
    verification_count INTEGER DEFAULT 1,                     -- 검증 횟수
    
    -- 검색 최적화
    UNIQUE(input_name)  -- 동일한 입력명 중복 방지
);

-- 2. 미생물 검증 결과 (LPSN)
CREATE TABLE microbe_species_cache (
    id SERIAL PRIMARY KEY,
    input_name VARCHAR(255) NOT NULL,           -- 사용자가 입력한 학명
    valid_name VARCHAR(255),                   -- LPSN 유효 학명
    lpsn_status VARCHAR(100),                  -- LPSN 상태 (correct name 등)
    is_verified BOOLEAN DEFAULT FALSE,          -- 검증 성공 여부
    taxonomy JSONB,                            -- 분류학적 정보 (JSON)
    lpsn_url TEXT,                             -- LPSN 상세 페이지 URL
    
    -- 캐시 관리 필드
    last_verified_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),  -- 마지막 검증 일시
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),        -- 최초 생성 일시
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),        -- 마지막 업데이트 일시
    verification_count INTEGER DEFAULT 1,                     -- 검증 횟수
    
    -- 검색 최적화
    UNIQUE(input_name)  -- 동일한 입력명 중복 방지
);

-- 3. 통합생물 검증 결과 (COL)
CREATE TABLE col_species_cache (
    id SERIAL PRIMARY KEY,
    input_name VARCHAR(255) NOT NULL,           -- 사용자가 입력한 학명
    scientific_name VARCHAR(255),               -- COL 학명
    col_id VARCHAR(100),                       -- COL 고유 ID
    col_status VARCHAR(100),                   -- COL 상태 (accepted, synonym 등)
    is_verified BOOLEAN DEFAULT FALSE,          -- 검증 성공 여부
    classification JSONB,                       -- 분류학적 정보 (JSON)
    col_url TEXT,                              -- COL 상세 페이지 URL
    
    -- 캐시 관리 필드
    last_verified_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),  -- 마지막 검증 일시
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),        -- 최초 생성 일시
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),        -- 마지막 업데이트 일시
    verification_count INTEGER DEFAULT 1,                     -- 검증 횟수
    
    -- 검색 최적화
    UNIQUE(input_name)  -- 동일한 입력명 중복 방지
);

-- 4. 검색 통계 테이블 (선택사항)
CREATE TABLE verification_stats (
    id SERIAL PRIMARY KEY,
    date DATE DEFAULT CURRENT_DATE,
    api_type VARCHAR(20) NOT NULL,              -- 'marine', 'microbe', 'col'
    total_searches INTEGER DEFAULT 0,
    cache_hits INTEGER DEFAULT 0,
    cache_misses INTEGER DEFAULT 0,
    real_time_searches INTEGER DEFAULT 0,
    
    UNIQUE(date, api_type)
);

-- 인덱스 생성 (검색 성능 최적화)
CREATE INDEX idx_marine_input_name ON marine_species_cache(input_name);
CREATE INDEX idx_marine_last_verified ON marine_species_cache(last_verified_at);
CREATE INDEX idx_marine_is_verified ON marine_species_cache(is_verified);

CREATE INDEX idx_microbe_input_name ON microbe_species_cache(input_name);
CREATE INDEX idx_microbe_last_verified ON microbe_species_cache(last_verified_at);
CREATE INDEX idx_microbe_is_verified ON microbe_species_cache(is_verified);

CREATE INDEX idx_col_input_name ON col_species_cache(input_name);
CREATE INDEX idx_col_last_verified ON col_species_cache(last_verified_at);
CREATE INDEX idx_col_is_verified ON col_species_cache(is_verified);

-- 트리거: 업데이트 시 updated_at 자동 갱신
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_marine_updated_at BEFORE UPDATE ON marine_species_cache 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_microbe_updated_at BEFORE UPDATE ON microbe_species_cache 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_col_updated_at BEFORE UPDATE ON col_species_cache 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 뷰: 오래된 데이터 조회용 (30일 이상 된 데이터)
CREATE VIEW outdated_cache_30days AS
SELECT 
    'marine' as source_type, input_name, last_verified_at,
    EXTRACT(DAY FROM (NOW() - last_verified_at)) as days_old
FROM marine_species_cache 
WHERE last_verified_at < NOW() - INTERVAL '30 days'
UNION ALL
SELECT 
    'microbe' as source_type, input_name, last_verified_at,
    EXTRACT(DAY FROM (NOW() - last_verified_at)) as days_old
FROM microbe_species_cache 
WHERE last_verified_at < NOW() - INTERVAL '30 days'
UNION ALL
SELECT 
    'col' as source_type, input_name, last_verified_at,
    EXTRACT(DAY FROM (NOW() - last_verified_at)) as days_old
FROM col_species_cache 
WHERE last_verified_at < NOW() - INTERVAL '30 days';

-- RLS (Row Level Security) 설정 (선택사항)
ALTER TABLE marine_species_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE microbe_species_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE col_species_cache ENABLE ROW LEVEL SECURITY;

-- 모든 사용자가 읽고 쓸 수 있도록 설정 (간단한 예시)
CREATE POLICY "Public Access" ON marine_species_cache FOR ALL USING (true);
CREATE POLICY "Public Access" ON microbe_species_cache FOR ALL USING (true);
CREATE POLICY "Public Access" ON col_species_cache FOR ALL USING (true); 