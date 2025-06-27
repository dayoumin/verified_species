# 🚀 Supabase 기반 스마트 캐싱 시스템 구현 계획

## 📋 **프로젝트 개요**

### **목적**
- WoRMS, LPSN, COL API 호출 최적화를 통한 성능 향상
- 응답 시간 6-8초 → 0.1-0.3초 (90% 개선)
- 외부 API 호출 90% 감소로 서버 부담 최소화

### **핵심 기능**
- **지능형 캐싱**: 데이터베이스별 차별화된 캐시 전략
- **완전한 로깅**: 모든 조회/업데이트 활동 추적
- **실시간 모니터링**: 성능 통계 및 분석 대시보드
- **자동 최적화**: 백그라운드 캐시 관리 및 갱신

---

## 🗄️ **데이터베이스 설계**

### **1. species_cache (메인 캐시 테이블)**
```sql
CREATE TABLE species_cache (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    scientific_name TEXT NOT NULL,
    source_db TEXT NOT NULL CHECK (source_db IN ('worms', 'lpsn', 'col')),
    cache_data JSONB NOT NULL,
    
    -- 생성/업데이트 추적
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    update_reason TEXT DEFAULT 'initial_creation',
    
    -- 조회 추적
    hit_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP WITH TIME ZONE,
    first_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 버전 및 우선순위
    version_info TEXT,
    priority_level INTEGER DEFAULT 1,
    updated_by TEXT DEFAULT 'system',
    
    UNIQUE(scientific_name, source_db)
);
```

### **2. cache_access_log (상세 조회 기록)**
```sql
CREATE TABLE cache_access_log (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    scientific_name TEXT NOT NULL,
    source_db TEXT NOT NULL,
    access_type TEXT NOT NULL CHECK (access_type IN ('hit', 'miss', 'update', 'delete')),
    accessed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    response_time_ms INTEGER,
    user_session TEXT,
    cache_age_seconds INTEGER,
    
    INDEX idx_access_log_time (accessed_at),
    INDEX idx_access_log_species (scientific_name),
    INDEX idx_access_log_type (access_type)
);
```

### **3. cache_update_history (업데이트 이력)**
```sql
CREATE TABLE cache_update_history (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    scientific_name TEXT NOT NULL,
    source_db TEXT NOT NULL,
    update_type TEXT NOT NULL CHECK (update_type IN ('create', 'refresh', 'expire', 'manual', 'api_mismatch')),
    old_data JSONB,
    new_data JSONB,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    update_reason TEXT,
    triggered_by TEXT DEFAULT 'system',
    api_response_time_ms INTEGER,
    
    INDEX idx_update_history_time (updated_at),
    INDEX idx_update_history_species (scientific_name),
    INDEX idx_update_history_type (update_type)
);
```

---

## 🔧 **핵심 구현 클래스**

### **SpeciesCacheManager 클래스**
```python
class SpeciesCacheManager:
    """학명 검증 결과 캐싱 관리 - 완전한 로깅 기능"""
    
    def __init__(self, user_session_id: str = None):
        self.supabase: Client = create_client(
            api_config.SUPABASE_URL,
            api_config.SUPABASE_KEY
        )
        self.user_session_id = user_session_id or f"session_{int(time.time())}"
        
        # DB별 캐시 유효기간 설정
        self.cache_duration = {
            'worms': timedelta(days=30),    # 월별 스냅샷 기반
            'lpsn': timedelta(days=21),     # 월간 + 수시 업데이트
            'col': timedelta(days=30)       # 월간 정기 릴리스
        }
    
    def get_cache(self, scientific_name: str, source_db: str) -> Optional[Dict[str, Any]]:
        """캐시 조회 + 완전한 액세스 로깅"""
        
    def set_cache(self, scientific_name: str, source_db: str, data: Dict[str, Any], 
                  version_info: str = None, update_reason: str = 'api_call',
                  api_response_time: int = None) -> bool:
        """캐시 저장 + 업데이트 히스토리 기록"""
        
    def get_detailed_stats(self, days: int = 7) -> Dict[str, Any]:
        """상세 캐시 통계 분석"""
```

---

## 📊 **데이터베이스별 캐싱 전략**

### **🌊 WoRMS (상시 업데이트)**
- **캐시 유효기간**: 기존 학명 1개월, 최근 학명 1주
- **갱신 시점**: 월별 스냅샷 릴리스 시
- **특징**: 새 종 추가 중심, 기존 학명 변경 드뭄

### **🦠 LPSN (월간 + 수시)**
- **캐시 유효기간**: 공식 학명 1개월, 미공식 학명 2주
- **갱신 시점**: IJSEM 발행 주기 (월간)
- **특징**: 공식/미공식 학명 구분 관리

### **🌍 COL (월간 정기)**
- **캐시 유효기간**: 모든 학명 1개월
- **갱신 시점**: 월간 릴리스 발표 시
- **특징**: 체계적 버전 관리, 예측 가능한 업데이트

---

## 🚀 **구현 단계별 계획**

### **Phase 1: 기본 캐싱 (1-2주)**
1. ✅ Supabase 프로젝트 생성 및 테이블 설정
2. ✅ SpeciesCacheManager 클래스 구현
3. ✅ WoRMS API 캐시 통합
4. ✅ 기본 테스트 및 디버깅

### **Phase 2: 전체 API 통합 (1주)**
1. ✅ LPSN, COL API 캐시 통합
2. ✅ 설정 파일 업데이트
3. ✅ 오류 처리 및 로깅 강화

### **Phase 3: 고급 기능 (1주)**
1. ✅ 백그라운드 작업 구현
2. ✅ 실시간 모니터링 대시보드
3. ✅ 상세 통계 수집 및 분석

### **Phase 4: 최적화 및 테스트 (1주)**
1. ✅ 성능 테스트 및 튜닝
2. ✅ 대용량 데이터 처리 테스트
3. ✅ 사용자 테스트 및 피드백 반영

---

## 📈 **예상 성능 개선**

### **응답 시간**
- **현재**: 학명당 6-8초 (API 호출 필수)
- **캐시 적용 후**: 
  - 캐시 히트: 0.1-0.3초 (90% 케이스)
  - 캐시 미스: 6-8초 (10% 케이스)
  - **평균**: 0.6-1.1초 (**85% 개선**)

### **서버 부담**
- **API 호출**: 90% 감소
- **네트워크 트래픽**: 대폭 감소
- **Rate Limiting 위험**: 최소화

### **사용자 경험**
- **즉각적 응답**: 대부분의 검색에서 즉시 결과
- **오프라인 대응**: 네트워크 문제 시에도 캐시로 서비스
- **안정성 향상**: 외부 API 의존도 감소

---

## 🔍 **모니터링 및 분석**

### **실시간 대시보드**
- **히트율 차트**: 시각적 성능 모니터링
- **인기 학명 순위**: 사용 패턴 분석
- **응답 시간 추이**: 성능 트렌드 추적
- **업데이트 패턴**: 데이터 갱신 주기 분석

### **자동 보고서**
- **주간/월간 성능 리포트**: 자동 생성
- **최적화 제안**: AI 기반 개선 권장사항
- **사용량 통계**: 상세 이용 패턴 분석

---

## ⚙️ **설정 및 환경**

### **환경 변수**
```env
# Supabase 설정
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-anon-key

# 캐시 설정
CACHE_ENABLED=true
CACHE_CLEANUP_INTERVAL_HOURS=24
CACHE_STATS_ENABLED=true
```

### **의존성**
- **supabase-py**: Supabase 클라이언트
- **psycopg2**: PostgreSQL 연결
- **matplotlib**: 차트 생성
- **pandas**: 데이터 분석

---

## 🎯 **성공 지표**

### **성능 지표**
- **캐시 히트율**: > 85%
- **평균 응답시간**: < 1초
- **API 호출 감소율**: > 90%

### **안정성 지표**
- **시스템 가용성**: > 99.9%
- **데이터 일관성**: 100%
- **오류율**: < 0.1%

### **사용성 지표**
- **사용자 만족도**: 향상
- **검색 완료율**: 증가
- **시스템 응답성**: 대폭 개선

---

## 📋 **마이그레이션 계획**

### **기존 시스템 호환성**
- **점진적 적용**: 기존 API 호출 로직 유지
- **롤백 계획**: 문제 발생 시 즉시 복구
- **데이터 무결성**: 캐시와 원본 데이터 일치성 보장

### **테스트 전략**
- **단위 테스트**: 각 캐시 기능별 검증
- **통합 테스트**: 전체 워크플로우 검증
- **성능 테스트**: 대용량 처리 성능 확인
- **사용자 테스트**: 실제 사용 시나리오 검증

---

## 🔮 **향후 확장 계획**

### **추가 기능**
- **분산 캐싱**: Redis 클러스터 통합
- **ML 기반 예측**: 사용 패턴 예측으로 사전 캐싱
- **실시간 동기화**: 외부 DB 변경 감지 및 즉시 반영

### **플랫폼 확장**
- **모바일 지원**: 오프라인 캐싱 기능
- **웹 서비스**: RESTful API 제공
- **클라우드 배포**: 확장 가능한 인프라

---

*문서 생성일: 2024-12-26*
*버전: v1.0*
*작성자: AI Assistant* 