# 🚀 Species Verifier Flutter 전환 계획 v2.0 + Supabase 캐싱 통합

## 📋 **프로젝트 개요**

### **전환 목적**
- **크로스 플랫폼 지원**: 모바일(Android/iOS) + 웹 + 데스크톱 통합
- **현대적 UI/UX**: Material Design 3 기반 직관적 인터페이스
- **성능 최적화**: Supabase 캐싱 시스템 통합으로 극대화된 성능
- **확장성**: 미래 기능 확장을 위한 견고한 아키텍처

### **핵심 혁신사항**
- **🗄️ 스마트 캐싱**: Supabase 기반 지능형 캐시 시스템
- **📱 모바일 우선**: 터치 인터페이스 최적화
- **🌐 웹 호환**: PWA 지원으로 브라우저에서도 완벽 동작
- **⚡ 실시간 동기화**: 여러 기기 간 데이터 실시간 동기화

---

## 🏗️ **아키텍처 설계**

### **전체 시스템 구조**
```
┌─────────────────────────────────────────────────┐
│                Flutter Frontend                  │
├─────────────────┬───────────────────────────────┤
│  Mobile Apps    │  Web App    │  Desktop Apps   │
│  (iOS/Android)  │   (PWA)     │ (Win/Mac/Linux) │
└─────────────────┴─────────────┬─────────────────┘
                                │
┌───────────────────────────────┴─────────────────┐
│              Supabase Backend                    │
├─────────────────────────────────────────────────┤
│  • PostgreSQL Database (캐시 + 사용자 데이터)    │
│  • Real-time 구독 (실시간 업데이트)             │
│  • Auth (사용자 인증 및 권한 관리)               │
│  • Storage (파일 업로드/다운로드)               │
│  • Edge Functions (서버리스 백엔드 로직)        │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────┴───────────────────────────────┐
│           External APIs (기존 유지)              │
├─────────────────────────────────────────────────┤
│  • WoRMS API (해양생물)                        │
│  • LPSN API (미생물)                           │
│  • COL API (통합생물)                          │
└─────────────────────────────────────────────────┘
```

---

## 📊 **Supabase 데이터베이스 설계 (확장)**

### **기존 캐싱 테이블 + 사용자 관리**
```sql
-- 1. 캐싱 테이블 (이전에 설계한 것 그대로 유지)
-- species_cache, cache_access_log, cache_update_history

-- 2. 사용자 관리 테이블 (신규)
CREATE TABLE user_profiles (
    id UUID REFERENCES auth.users(id) PRIMARY KEY,
    username TEXT UNIQUE,
    full_name TEXT,
    organization TEXT,
    research_field TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    preferences JSONB DEFAULT '{}'::jsonb
);

-- 3. 검색 히스토리 테이블 (신규)
CREATE TABLE search_history (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id),
    scientific_name TEXT NOT NULL,
    search_type TEXT NOT NULL CHECK (search_type IN ('marine', 'microbe', 'col')),
    results_data JSONB,
    searched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    device_type TEXT, -- mobile, web, desktop
    session_id TEXT
);

-- 4. 즐겨찾기 테이블 (신규)
CREATE TABLE user_favorites (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id),
    scientific_name TEXT NOT NULL,
    common_name TEXT,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, scientific_name)
);

-- 5. 작업 큐 테이블 (신규 - 대용량 처리용)
CREATE TABLE processing_jobs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id),
    job_type TEXT NOT NULL CHECK (job_type IN ('file_upload', 'batch_verification', 'export')),
    status TEXT NOT NULL CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    input_data JSONB,
    output_data JSONB,
    progress INTEGER DEFAULT 0,
    total_items INTEGER,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);
```

---

## 📱 **Flutter 앱 구조**

### **폴더 구조**
```
lib/
├── main.dart
├── app/
│   ├── app.dart                    # 메인 앱 위젯
│   └── theme/                      # 테마 설정
├── core/
│   ├── constants/                  # 상수 정의
│   ├── services/                   # 핵심 서비스
│   │   ├── supabase_service.dart   # Supabase 연결
│   │   ├── cache_service.dart      # 캐시 관리
│   │   ├── api_service.dart        # 외부 API 호출
│   │   └── sync_service.dart       # 데이터 동기화
│   └── models/                     # 데이터 모델
├── features/
│   ├── auth/                       # 인증 기능
│   ├── search/                     # 검색 기능
│   │   ├── models/
│   │   ├── services/
│   │   ├── widgets/
│   │   └── screens/
│   ├── history/                    # 검색 기록
│   ├── favorites/                  # 즐겨찾기
│   ├── batch_processing/           # 대용량 처리
│   └── settings/                   # 설정
├── shared/
│   ├── widgets/                    # 공통 위젯
│   ├── utils/                      # 유틸리티
│   └── extensions/                 # 확장 메서드
└── l10n/                          # 다국어 지원
```

### **핵심 서비스 클래스**

#### **CacheService (Flutter용)**
```dart
class CacheService {
  final SupabaseClient _supabase;
  final Logger _logger = Logger('CacheService');
  
  CacheService(this._supabase);
  
  // 캐시에서 학명 검색
  Future<Map<String, dynamic>?> getCache(
    String scientificName, 
    String sourceDb
  ) async {
    try {
      final response = await _supabase
        .from('species_cache')
        .select()
        .eq('scientific_name', scientificName.trim())
        .eq('source_db', sourceDb)
        .maybeSingle();
      
      if (response != null) {
        final expiresAt = DateTime.parse(response['expires_at']);
        if (DateTime.now().isBefore(expiresAt)) {
          // 캐시 히트 로깅
          await _logCacheAccess(scientificName, sourceDb, 'hit');
          await _updateHitCount(response['id']);
          return response['cache_data'];
        } else {
          // 만료된 캐시 삭제
          await _deleteExpiredCache(response['id']);
        }
      }
      
      await _logCacheAccess(scientificName, sourceDb, 'miss');
      return null;
    } catch (e) {
      _logger.severe('캐시 조회 실패: $e');
      return null;
    }
  }
  
  // 캐시에 데이터 저장
  Future<bool> setCache(
    String scientificName,
    String sourceDb,
    Map<String, dynamic> data, {
    String? versionInfo,
    String updateReason = 'api_call',
  }) async {
    try {
      final expiresAt = DateTime.now().add(_getCacheDuration(sourceDb));
      
      final cacheEntry = {
        'scientific_name': scientificName.trim(),
        'source_db': sourceDb,
        'cache_data': data,
        'expires_at': expiresAt.toIso8601String(),
        'version_info': versionInfo,
        'update_reason': updateReason,
        'priority_level': _calculatePriority(scientificName),
      };
      
      await _supabase
        .from('species_cache')
        .upsert(cacheEntry);
      
      return true;
    } catch (e) {
      _logger.severe('캐시 저장 실패: $e');
      return false;
    }
  }
  
  Duration _getCacheDuration(String sourceDb) {
    switch (sourceDb) {
      case 'worms': return const Duration(days: 30);
      case 'lpsn': return const Duration(days: 21);
      case 'col': return const Duration(days: 30);
      default: return const Duration(days: 7);
    }
  }
}
```

#### **ApiService (통합 API 서비스)**
```dart
class ApiService {
  final CacheService _cacheService;
  final HttpService _httpService;
  final Logger _logger = Logger('ApiService');
  
  ApiService(this._cacheService, this._httpService);
  
  // 통합 종 검색 (캐시 우선)
  Future<SearchResult> searchSpecies(
    String scientificName,
    String searchType, {
    bool forceRefresh = false,
  }) async {
    // 1. 캐시 확인 (강제 새로고침이 아닌 경우)
    if (!forceRefresh) {
      final cached = await _cacheService.getCache(scientificName, searchType);
      if (cached != null) {
        return SearchResult.fromJson(cached);
      }
    }
    
    // 2. API 호출
    final stopwatch = Stopwatch()..start();
    final apiResult = await _callExternalApi(scientificName, searchType);
    stopwatch.stop();
    
    // 3. 결과를 캐시에 저장
    if (apiResult.isSuccess) {
      await _cacheService.setCache(
        scientificName,
        searchType,
        apiResult.toJson(),
        versionInfo: _generateVersionInfo(searchType),
      );
    }
    
    // 4. 사용자 검색 기록 저장
    await _saveSearchHistory(scientificName, searchType, apiResult);
    
    return apiResult;
  }
  
  // 배치 처리 (대용량 파일 처리)
  Future<String> processBatchFile(
    String userId,
    List<String> speciesNames,
    String searchType,
  ) async {
    // 작업 큐에 등록
    final jobId = await _createProcessingJob(userId, speciesNames, searchType);
    
    // 백그라운드에서 처리 (isolate 사용)
    _processBatchInBackground(jobId, speciesNames, searchType);
    
    return jobId;
  }
}
```

---

## 🔄 **마이그레이션 전략**

### **Phase 1: 백엔드 마이그레이션 (2-3주)**
1. **Supabase 프로젝트 설정**
   - PostgreSQL 데이터베이스 생성
   - 캐싱 테이블 생성 (기존 설계 적용)
   - 사용자 관리 테이블 추가
   - Auth 설정 및 RLS 정책 구성

2. **데이터 마이그레이션 도구 개발**
   - 기존 Python 로직을 Dart/Flutter로 포팅
   - API 호출 로직 재구현
   - 캐시 시스템 통합

### **Phase 2: 모바일 앱 개발 (3-4주)**
1. **핵심 기능 구현**
   - 사용자 인증 (이메일/Google/Apple)
   - 학명 검색 (음성 입력 지원)
   - 결과 표시 (터치 친화적 UI)
   - 오프라인 모드 (캐시 활용)

2. **모바일 특화 기능**
   - 카메라 통합 (OCR로 학명 인식)
   - GPS 위치 정보 (서식지 매칭)
   - 알림 (즐겨찾기 종 업데이트 시)

### **Phase 3: 웹 앱 개발 (2-3주)**
1. **PWA 구현**
   - 반응형 웹 디자인
   - 오프라인 지원
   - 파일 업로드/다운로드

2. **웹 특화 기능**
   - 드래그 앤 드롭 파일 업로드
   - 키보드 단축키
   - 대용량 데이터 처리

### **Phase 4: 데스크톱 앱 개발 (1-2주)**
1. **네이티브 데스크톱 기능**
   - 시스템 트레이 통합
   - 파일 시스템 접근
   - 자동 업데이트

---

## 📱 **모바일 앱 주요 화면**

### **1. 메인 검색 화면**
```dart
class SearchScreen extends StatefulWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Species Verifier'),
        actions: [
          IconButton(
            icon: Icon(Icons.history),
            onPressed: () => Navigator.push(
              context,
              MaterialPageRoute(builder: (_) => HistoryScreen()),
            ),
          ),
        ],
      ),
      body: Column(
        children: [
          // 검색 입력 영역
          SearchInputWidget(),
          
          // 검색 타입 선택
          SearchTypeSelector(),
          
          // 최근 검색 + 즐겨찾기 탭
          RecentAndFavoritesWidget(),
          
          // 빠른 액션 버튼들
          QuickActionButtons(),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _showBatchUploadSheet,
        child: Icon(Icons.upload_file),
        tooltip: '파일 업로드',
      ),
    );
  }
}
```

### **2. 결과 표시 화면**
```dart
class ResultScreen extends StatelessWidget {
  final SearchResult result;
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: CustomScrollView(
        slivers: [
          // 상단 이미지 + 기본 정보
          SliverAppBar(
            expandedHeight: 200,
            flexibleSpace: FlexibleSpaceBar(
              title: Text(result.scientificName),
              background: ResultHeaderWidget(result),
            ),
          ),
          
          // 상세 정보 카드들
          SliverList(
            delegate: SliverChildListDelegate([
              TaxonomyCard(result.taxonomy),
              ValidationCard(result.validation),
              DistributionCard(result.distribution),
              ReferencesCard(result.references),
            ]),
          ),
        ],
      ),
      floatingActionButton: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          FloatingActionButton(
            heroTag: "favorite",
            mini: true,
            onPressed: () => _toggleFavorite(),
            child: Icon(Icons.favorite),
          ),
          SizedBox(height: 8),
          FloatingActionButton(
            heroTag: "share",
            mini: true,
            onPressed: () => _shareResult(),
            child: Icon(Icons.share),
          ),
        ],
      ),
    );
  }
}
```

---

## ⚡ **성능 최적화 전략**

### **캐싱 최적화**
- **로컬 캐시**: SQLite + Drift ORM으로 오프라인 지원
- **이미지 캐싱**: cached_network_image로 효율적 이미지 관리
- **API 응답 캐싱**: Supabase + 로컬 캐시 2단계 구조

### **UI 성능**
- **지연 로딩**: 대용량 리스트는 ListView.builder 사용
- **이미지 최적화**: WebP 포맷 + 다중 해상도 지원
- **애니메이션**: 120fps 지원으로 부드러운 전환

### **네트워크 최적화**
- **배치 요청**: 여러 API 호출을 하나로 통합
- **압축**: gzip 압축으로 데이터 크기 최소화
- **연결 풀링**: HTTP 연결 재사용

---

## 🔒 **보안 및 프라이버시**

### **데이터 보안**
- **End-to-End 암호화**: 민감한 사용자 데이터 보호
- **RLS (Row Level Security)**: Supabase에서 사용자별 데이터 격리
- **API 키 보안**: 환경 변수 + 난독화

### **프라이버시 보호**
- **익명 사용 옵션**: 로그인 없이도 기본 기능 사용 가능
- **데이터 최소화**: 필요한 데이터만 수집
- **사용자 제어**: 언제든 데이터 삭제 가능

---

## 📊 **분석 및 모니터링**

### **성능 모니터링**
- **Firebase Analytics**: 사용자 행동 분석
- **Crashlytics**: 앱 크래시 모니터링
- **Supabase Analytics**: 백엔드 성능 추적

### **사용자 피드백**
- **인앱 피드백**: 쉬운 버그 리포트 및 제안
- **평가 요청**: 적절한 타이밍에 스토어 리뷰 요청
- **베타 테스트**: TestFlight/Play Console 베타 프로그램

---

## 🎯 **출시 계획**

### **베타 출시 (개발 완료 후 1개월)**
- **내부 테스트**: 개발팀 + 핵심 사용자 10명
- **클로즈드 베타**: 연구자 커뮤니티 50명
- **피드백 수집 및 개선**: 2주간 집중 개선

### **정식 출시**
- **Android**: Google Play Store
- **iOS**: Apple App Store  
- **Web**: PWA 배포
- **Desktop**: Windows/macOS/Linux 바이너리

### **마케팅 전략**
- **학술 커뮤니티**: 생물학/생태학 학회 발표
- **소셜 미디어**: 연구자 네트워크 활용
- **블로그/유튜브**: 사용법 가이드 및 케이스 스터디

---

## 💰 **예산 및 리소스**

### **개발 비용**
- **Supabase 구독**: 월 $25 (Pro 플랜)
- **외부 API 비용**: 기존과 동일 (캐싱으로 오히려 절약)
- **스토어 등록비**: Android $25 + iOS $99/년
- **도메인/호스팅**: 월 $10

### **예상 ROI**
- **사용자 증가**: 모바일 접근성으로 10배 증가 예상
- **사용 편의성**: 캐싱으로 85% 성능 개선
- **확장성**: 다중 플랫폼으로 사용자 기반 확대

---

## 🔮 **미래 로드맵**

### **Phase 5: AI 통합 (6개월 후)**
- **이미지 인식**: 생물 사진으로 종 식별
- **자연어 처리**: 일반명으로 학명 추천
- **예측 분석**: 사용 패턴 기반 추천

### **Phase 6: 협업 기능 (1년 후)**
- **팀 워크스페이스**: 연구팀 공동 작업 공간
- **데이터 공유**: 검증 결과 공유 및 협업
- **API 제공**: 다른 앱에서 활용 가능한 API

### **Phase 7: 고급 분석 (1.5년 후)**
- **생태학적 분석**: 서식지, 분포, 보전 상태 통합 분석
- **논문 연동**: 관련 연구 자동 추천
- **데이터 시각화**: 인터랙티브 차트 및 맵

---

*문서 업데이트: 2024-12-26*
*버전: v2.0 (Supabase 캐싱 통합)*
*작성자: AI Assistant* 