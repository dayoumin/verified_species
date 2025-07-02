# 🧪 Species Verifier 종합 테스트 가이드

## 🎯 테스트 개요

Species Verifier v1.5의 모든 기능을 체계적으로 테스트하기 위한 가이드입니다.
특히 **기관 네트워크 환경**에서의 안정성과 보안 대응을 중점적으로 검증합니다.

## 📁 테스트 파일 구조

### 1. `test_enterprise_network.py` - 🌐 기관 네트워크 종합 진단
- **목적**: 기관 네트워크 환경에서의 모든 외부 API 연결성 테스트
- **진단 항목**: 네트워크 어댑터, SSL, 프록시, API 접근성, 검증기, 보고서
- **실행**: `python tests/test_enterprise_network.py`

### 2. `lpsn_api_guide.md` - 🔬 LPSN API 테스트 가이드  
- **목적**: LPSN API 연결 및 검증 테스트 (⚠️ **API 방식으로 업데이트됨!**)
- **변경사항**: 웹 스크래핑 → 공식 RESTful API
- **장점**: 안정성 ⬆️, 기관 허용도 ⬆️, 데이터 품질 ⬆️

### 3. `test_supabase_integration.py` - 🗄️ Supabase 통합 테스트
- **목적**: Supabase 데이터베이스 연결 및 캐싱 시스템 테스트
- **실행**: `python test_supabase_integration.py`

### 4. `test_new_features.py` - ✨ 신규 기능 테스트
- **목적**: v1.4에서 추가된 4가지 새로운 기능 테스트
- **실행**: `python test_new_features.py`

## 🚀 기관 환경 4단계 테스트 절차

### 📋 사전 준비 체크리스트
- [ ] Python 환경 설정 완료
- [ ] 필요한 패키지 설치 (`pip install -r requirements.txt`)
- [ ] 환경변수 설정 (API 키, 데이터베이스 URL 등)
- [ ] 네트워크 관리자와 사전 협의 완료

### 🔧 1단계: 환경변수 설정
```powershell
# LPSN API 인증 (✅ 새로 추가됨!)
$env:LPSN_USERNAME="your_lpsn_username"
$env:LPSN_PASSWORD="your_lpsn_password"

# Supabase 설정
$env:SUPABASE_URL="your_supabase_url"  
$env:SUPABASE_ANON_KEY="your_supabase_key"

# 기관 네트워크 설정 (필요시)
$env:SPECIES_VERIFIER_SSL_BYPASS="true"
$env:ENTERPRISE_USER_AGENT="YourCompany-Research-Tool/1.5"
```

### 🌐 2단계: 네트워크 연결성 진단
```powershell
cd D:\Projects\verified_species\tests
python test_enterprise_network.py
```

**예상 결과**:
- ✅ **모든 단계 통과**: 기관 환경에서 완벽 작동
- ⚠️ **일부 제한**: 특정 API만 차단 (WoRMS, LPSN 중 하나)
- ❌ **차단 상태**: 대부분의 외부 API 차단 (네트워크 관리자 문의 필요)

### 🔬 3단계: LPSN API 특별 테스트 (중요!)
```powershell
# 1. LPSN 계정 생성 (https://api.lpsn.dsmz.de/)
# 2. 환경변수 설정 후 테스트
python -c "
from species_verifier.core.verifier import verify_single_microbe_lpsn
result = verify_single_microbe_lpsn('Escherichia coli')
if result['is_verified']:
    print('✅ LPSN API 연결 성공!')
    print(f'학명: {result[\"scientific_name\"]}')
    print(f'상태: {result[\"status\"]}')
else:
    print('❌ LPSN API 연결 실패')
    print(f'오류: {result[\"status\"]}')
"
```

### 🗄️ 4단계: 전체 시스템 통합 테스트
```powershell
# Supabase 연결 테스트
python test_supabase_integration.py

# 신규 기능 테스트  
python test_new_features.py
```

## ⚠️ 중요 변경사항: LPSN API 전환

### 🎉 LPSN이 API를 제공한다는 사실을 발견!
**이전**: 웹 스크래핑 방식 (불안정, 기관에서 차단 위험)
**현재**: 공식 RESTful API (안정적, 기관 친화적)

### 📊 성능 비교
| 항목 | 웹 스크래핑 | **LPSN API** |
|------|-------------|--------------|
| 안정성 | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| 속도 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 기관 허용도 | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| 데이터 품질 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 유지보수 | ⭐⭐ | ⭐⭐⭐⭐⭐ |

### 🔧 API 설정 방법
1. **LPSN 계정 생성**: https://api.lpsn.dsmz.de/
2. **환경변수 설정**: `LPSN_USERNAME`, `LPSN_PASSWORD`
3. **방화벽 허용**: `api.lpsn.dsmz.de` (HTTPS/443)

## 🔍 문제 해결 FAQ

### Q1: LPSN API 인증 실패
```
A: 환경변수 확인
   $env:LPSN_USERNAME
   $env:LPSN_PASSWORD
   
   계정이 없다면 https://api.lpsn.dsmz.de/에서 무료 생성
```

### Q2: SSL 인증서 오류
```
A: 기관의 SSL 인터셉션 문제
   $env:SPECIES_VERIFIER_SSL_BYPASS="true"
   (보안팀 승인 후 사용)
```

### Q3: 프록시 연결 실패
```
A: Windows 레지스트리에서 프록시 설정 자동 감지
   수동 설정이 필요한 경우 network_debug.py 실행
```

### Q4: Supabase 연결 실패
```
A: 환경변수 및 네트워크 정책 확인
   *.supabase.co 도메인 허용 필요
```

## 📅 정기 점검 일정

### 🗓️ 주간 점검 (매주 금요일)
- [ ] 기본 연결성 테스트 (`test_enterprise_network.py`)
- [ ] LPSN API 응답 속도 확인
- [ ] Supabase 캐시 성능 모니터링

### 🗓️ 월간 점검 (매월 첫째 주)
- [ ] 모든 테스트 파일 실행
- [ ] API 키 및 인증 정보 갱신
- [ ] 네트워크 정책 변경사항 확인
- [ ] 성능 지표 분석 및 보고서 작성

### 🗓️ 분기 점검 (3개월마다)
- [ ] 전체 시스템 아키텍처 검토
- [ ] 새로운 API 및 데이터소스 평가
- [ ] 보안 정책 업데이트 검토
- [ ] 기관 네트워크 환경 변경사항 적용

## 🆘 긴급 상황 대응

### 🚨 모든 외부 API 차단 시
1. **오프라인 모드 활성화**
2. **로컬 데이터베이스 사용**
3. **수동 검증 프로세스 개시**
4. **네트워크 관리자 긴급 연락**

### 🚨 LPSN API만 차단 시
1. **WoRMS API로 부분 대체** (해양 미생물)
2. **캐시된 데이터 최대 활용**
3. **수동 미생물 검증 병행**

### 🚨 Supabase 연결 실패 시
1. **로컬 SQLite 백업 사용**
2. **캐싱 기능 비활성화**
3. **직접 API 호출 모드 전환**

## 📞 기술 지원 연락처

### 내부 문의
- **네트워크 관리자**: 도메인 허용 정책 문의
- **보안 담당자**: SSL 우회 및 프록시 설정
- **IT 지원팀**: 환경변수 및 시스템 설정

### 외부 리소스
- **LPSN API 문서**: https://api.lpsn.dsmz.de/
- **WoRMS API 문서**: https://www.marinespecies.org/rest/
- **Supabase 문서**: https://supabase.com/docs

---

## 🎯 최종 체크리스트

기관 환경에서 Species Verifier를 완전히 테스트하려면:

- [ ] 모든 환경변수 설정 완료
- [ ] 네트워크 관리자와 협의 완료  
- [ ] **LPSN API 계정 생성 및 테스트 성공** ⭐
- [ ] 6단계 네트워크 진단 모두 통과
- [ ] Supabase 연결 및 캐싱 정상 작동
- [ ] 신규 기능 4개 모두 정상 작동
- [ ] 문제 발생 시 대응 방안 숙지
- [ ] 정기 점검 일정 수립

**🎉 모든 항목 완료 시, 기관 환경에서 Species Verifier를 안전하고 효율적으로 사용할 수 있습니다!** 