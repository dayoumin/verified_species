# DeepSearch 심층분석 시스템 설계 v1.0

## 📋 개요

현재 Species Verifier에서 심층분석 결과는 "준비 중 (DeepSearch 기능 개발 예정)"으로 표시됩니다.
향후 DeepSearch 시스템을 통해 종합적인 생물종 정보를 제공할 예정입니다.

## 🎯 DeepSearch 시스템 목표

### 핵심 기능
- **종합 정보 수집**: 위키백과, 학술 데이터베이스, 연구 논문 등 다양한 출처 통합
- **구조화된 데이터**: 생태학적, 형태학적, 경제적 정보를 체계적으로 분류
- **별도 팝업 화면**: 검증 결과와 분리된 상세 정보 화면 제공
- **데이터베이스 캐싱**: Supabase를 활용한 효율적인 정보 저장 및 관리

## 🏗️ 시스템 아키텍처

### 1. 데이터 수집 모듈 (Data Collection Module)
```python
# species_verifier/core/deep_search/
├── data_collectors/
│   ├── __init__.py
│   ├── wikipedia_collector.py      # 위키백과 정보 수집
│   ├── eol_collector.py           # Encyclopedia of Life 연동
│   ├── gbif_collector.py          # GBIF 데이터 수집
│   └── literature_collector.py    # 학술 논문 정보 수집
├── processors/
│   ├── __init__.py
│   ├── text_processor.py          # 텍스트 정제 및 구조화
│   ├── image_processor.py         # 이미지 URL 처리
│   └── taxonomy_processor.py      # 분류학적 정보 처리
└── aggregator.py                  # 데이터 통합 및 품질 관리
```

### 2. 데이터베이스 스키마 (Supabase)
```sql
-- DeepSearch 결과 저장 테이블
CREATE TABLE deep_search_cache (
    id SERIAL PRIMARY KEY,
    scientific_name VARCHAR(255) UNIQUE NOT NULL,
    korean_name VARCHAR(255),
    common_names JSONB,                    -- 다국어 일반명
    taxonomy JSONB,                        -- 분류학적 정보
    ecology JSONB,                         -- 생태학적 정보
    morphology TEXT,                       -- 형태학적 특징
    distribution TEXT,                     -- 분포 정보
    habitat TEXT,                          -- 서식지 정보
    conservation_status VARCHAR(100),      -- 보전 상태
    economic_importance TEXT,              -- 경제적 중요성
    ecological_role TEXT,                  -- 생태적 역할
    images JSONB,                         -- 이미지 URL 배열
    references JSONB,                     -- 참고문헌 정보
    data_sources JSONB,                   -- 데이터 출처
    data_quality_score INTEGER DEFAULT 0, -- 데이터 품질 점수
    last_updated TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX(scientific_name),
    INDEX(korean_name),
    INDEX(last_updated)
);

-- 데이터 수집 로그 테이블
CREATE TABLE deep_search_logs (
    id SERIAL PRIMARY KEY,
    scientific_name VARCHAR(255) NOT NULL,
    collection_date TIMESTAMP DEFAULT NOW(),
    data_source VARCHAR(100),              -- 'wikipedia', 'eol', 'gbif' 등
    collection_status VARCHAR(50),         -- 'success', 'failed', 'partial'
    error_message TEXT,
    data_size INTEGER,                     -- 수집된 데이터 크기
    processing_time_ms INTEGER,           -- 처리 시간 (밀리초)
    INDEX(scientific_name),
    INDEX(collection_date),
    INDEX(data_source)
);
```

### 3. GUI 팝업 화면 설계
```python
# species_verifier/gui/components/deep_search_popup.py
class DeepSearchPopup(ctk.CTkToplevel):
    """심층분석 결과를 표시하는 팝업 창"""
    
    def __init__(self, parent, scientific_name: str):
        super().__init__(parent)
        self.scientific_name = scientific_name
        self.setup_ui()
        self.load_deep_search_data()
    
    def setup_ui(self):
        """팝업 UI 구성"""
        # 탭 구성:
        # - 개요 (Overview)
        # - 분류학 (Taxonomy)  
        # - 생태학 (Ecology)
        # - 형태학 (Morphology)
        # - 분포/서식지 (Distribution)
        # - 보전/경제적 중요성 (Conservation)
        # - 이미지 갤러리 (Images)
        # - 참고문헌 (References)
```

## 📊 데이터 수집 전략

### 1차 데이터 소스 (1순위)
- **위키백과 (한국어/영어)**: 일반적인 정보, 이미지
- **WoRMS (해양생물)**: 분류학적 정보, 분포
- **LPSN (미생물)**: 명명법, 분류학 정보
- **COL (통합생물)**: 표준 분류 체계

### 2차 데이터 소스 (2순위)  
- **Encyclopedia of Life (EOL)**: 종합 생물 정보
- **GBIF**: 분포, 표본 정보
- **iNaturalist**: 생태 사진, 관찰 기록
- **Tree of Life (ToL)**: 계통 분류 정보

### 3차 데이터 소스 (3순위)
- **PubMed**: 관련 연구 논문
- **Google Scholar**: 학술 자료
- **ResearchGate**: 연구자 네트워크 정보

## 🔄 DeepSearch 워크플로우

### 1. 데이터 수집 단계
```python
async def collect_deep_search_data(scientific_name: str) -> dict:
    """심층분석 데이터 수집"""
    
    # 1. 기존 캐시 확인
    cached_data = await check_cache(scientific_name)
    if cached_data and not is_cache_expired(cached_data):
        return cached_data
    
    # 2. 다중 소스 데이터 수집 (병렬 처리)
    tasks = [
        collect_wikipedia_data(scientific_name),
        collect_eol_data(scientific_name), 
        collect_gbif_data(scientific_name),
        collect_literature_data(scientific_name)
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 3. 데이터 통합 및 품질 검증
    aggregated_data = aggregate_and_validate(results)
    
    # 4. 데이터베이스 저장
    await save_to_cache(scientific_name, aggregated_data)
    
    return aggregated_data
```

### 2. 데이터 품질 관리
- **정확성 검증**: 다중 소스 간 정보 교차 검증
- **완성도 평가**: 수집된 정보의 완전성 점수
- **최신성 관리**: 정기적인 데이터 업데이트 (월 1회)
- **신뢰도 평가**: 소스별 신뢰도 가중치 적용

### 3. 사용자 인터페이스
- **검증 결과 화면**: "심층분석 보기" 버튼 추가
- **팝업 창**: 탭 형태의 상세 정보 화면
- **로딩 상태**: 데이터 수집 중 진행률 표시
- **오프라인 모드**: 캐시된 데이터 활용

## 🚀 구현 단계별 계획

### Phase 1: 기본 인프라 구축 (4주)
- ✅ 현재 완료: 심층분석 결과 "준비 중" 메시지 표시
- 🔄 Supabase 스키마 설계 및 구축
- 🔄 기본 데이터 수집 모듈 개발
- 🔄 위키백과 수집기 구현

### Phase 2: 팝업 UI 개발 (3주)
- 🔄 DeepSearch 팝업 창 기본 구조 구현
- 🔄 탭 기반 정보 표시 시스템
- 🔄 이미지 갤러리 컴포넌트
- 🔄 참고문헌 링크 시스템

### Phase 3: 데이터 소스 확장 (4주)
- 🔄 Encyclopedia of Life API 연동
- 🔄 GBIF API 연동  
- 🔄 다중 소스 데이터 통합 로직
- 🔄 데이터 품질 관리 시스템

### Phase 4: 최적화 및 고도화 (2주)
- 🔄 캐싱 전략 최적화
- 🔄 성능 모니터링 대시보드
- 🔄 오류 처리 및 예외 상황 대응
- 🔄 사용자 피드백 수집 시스템

## 💡 기술적 고려사항

### 성능 최적화
- **비동기 처리**: 다중 API 호출 병렬 처리
- **캐싱 전략**: 계층적 캐싱 (메모리 → 로컬 DB → Supabase)
- **이미지 최적화**: 썸네일 생성 및 지연 로딩
- **데이터 압축**: JSONB 압축 저장

### 안정성 확보
- **API 제한 관리**: Rate limiting 및 백오프 전략
- **오류 복구**: 부분 실패 시 복구 메커니즘
- **데이터 검증**: 수집 데이터 무결성 검사
- **모니터링**: 실시간 시스템 상태 추적

### 확장성 고려
- **모듈형 설계**: 새로운 데이터 소스 쉽게 추가
- **다국어 지원**: 한국어/영어 외 언어 확장 가능
- **플러그인 아키텍처**: 커스텀 데이터 수집기 개발 지원
- **API 제공**: 외부 시스템 연동을 위한 REST API

## 📈 예상 효과

### 사용자 경험 향상
- **풍부한 정보**: 기본 검증을 넘어선 종합적 생물 정보
- **직관적 UI**: 탭 기반의 체계적인 정보 구성
- **빠른 접근**: 캐시된 데이터로 즉시 정보 제공
- **신뢰성**: 다중 소스 검증을 통한 정확한 정보

### 연구 지원 강화
- **참고문헌**: 관련 연구 논문 및 학술 자료 링크
- **이미지 자료**: 고품질 생물 이미지 갤러리  
- **분포 정보**: 지리적 분포 및 서식지 데이터
- **생태 정보**: 생활사, 생태적 역할 등 상세 정보

### 데이터 품질 관리
- **정확성**: 다중 소스 교차 검증
- **최신성**: 정기적 데이터 업데이트
- **완성도**: 체계적인 정보 분류 및 구조화
- **추적성**: 데이터 출처 및 수집 이력 관리

---

**개발 담당:** ecomarine@korea.kr  
**최종 업데이트:** 2024년 1월 (v1.0)  
**다음 리뷰:** 2024년 2월 