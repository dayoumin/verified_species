# 🔬 LPSN API 테스트 가이드

## ✅ LPSN API 방식 변경 완료!

**중요 발견**: LPSN은 웹 스크래핑이 아니라 **공식 RESTful API**를 제공합니다!

### 🎯 LPSN API 장점
- ✅ **공식 지원**: 안정적이고 신뢰할 수 있는 데이터
- ✅ **구조화된 데이터**: JSON 형식으로 파싱 불필요
- ✅ **기관 친화적**: 웹 스크래핑보다 허용될 가능성 높음
- ✅ **효율적**: 빠르고 정확한 데이터 접근

## 🔧 API 설정 방법

### 1. LPSN 계정 등록
```
1. https://api.lpsn.dsmz.de/ 방문
2. "Login / Register" 클릭
3. 무료 계정 생성
4. 이메일 인증 완료
```

### 2. 환경변수 설정
```bash
# Windows PowerShell
$env:LPSN_USERNAME="your_username"
$env:LPSN_PASSWORD="your_password"

# 또는 .env 파일에 추가
LPSN_USERNAME=your_username
LPSN_PASSWORD=your_password
```

### 3. 연결 테스트
```python
from species_verifier.core.verifier import verify_single_microbe_lpsn

# API 연결 테스트
result = verify_single_microbe_lpsn("Escherichia coli")

if result['is_verified']:
    print("✅ LPSN API 연결 성공!")
    print(f"학명: {result['scientific_name']}")
    print(f"상태: {result['status']}")
else:
    print("❌ LPSN API 연결 실패")
    print(f"오류: {result['status']}")
```

## 🏢 기관 네트워크 환경에서의 장점

### ✅ 웹 스크래핑 대비 API의 우수성
| 항목 | 웹 스크래핑 | LPSN API |
|------|-------------|----------|
| **안정성** | ❌ HTML 구조 변경 시 오류 | ✅ API 스펙 안정적 |
| **속도** | ❌ HTML 파싱 부하 | ✅ JSON 직접 파싱 |
| **기관 정책** | ❌ 스크래핑 차단 가능 | ✅ 정상 API 호출 |
| **SSL 인증서** | ❌ 브라우저 위장 필요 | ✅ 표준 HTTP 요청 |
| **프록시 통과** | ❌ 복잡한 우회 로직 | ✅ 일반 API 트래픽 |

### 🔒 보안 고려사항
- **인증 정보 보호**: 환경변수로 안전 관리
- **HTTPS 통신**: 암호화된 API 통신
- **표준 헤더**: 의심스러운 User-Agent 불필요

## 🧪 테스트 시나리오

### 기본 테스트
```python
# 1. 일반적인 미생물 학명
test_names = [
    "Escherichia coli",
    "Bacillus subtilis", 
    "Staphylococcus aureus"
]

for name in test_names:
    result = verify_single_microbe_lpsn(name)
    print(f"{name}: {result['status']}")
```

### 오류 처리 테스트
```python
# 2. 잘못된 학명 또는 네트워크 오류
test_cases = [
    "Invalid species name",
    "Nonexistent bacterium",
    ""  # 빈 문자열
]

for name in test_cases:
    result = verify_single_microbe_lpsn(name)
    print(f"'{name}': {result['status']}")
```

## ⚠️ 주의사항

### 🔑 인증 정보 필수
```bash
# 환경변수가 설정되지 않으면 오류 발생
# 반드시 LPSN 계정 생성 후 설정 필요
```

### 🌐 네트워크 요구사항
- `*.lpsn.dsmz.de` 도메인 접근 필요
- 기관 방화벽에서 `api.lpsn.dsmz.de` 허용 필요
- HTTPS(443 포트) 접근 가능해야 함

### 📊 사용량 제한
- LPSN API는 무료이지만 과도한 요청 시 제한 가능
- 적절한 지연 시간(1초) 자동 적용
- 대량 처리 시 배치 단위로 분할 권장

## 🎯 최종 권장사항

1. **✅ 우선순위**: LPSN API 사용 (웹 스크래핑 완전 대체)
2. **⚙️ 설정**: 환경변수 정확히 설정
3. **🔧 테스트**: 기관 환경에서 연결성 확인
4. **📞 협의**: 네트워크 관리자에게 도메인 화이트리스트 요청

**결론**: LPSN API는 웹 스크래핑의 모든 문제점을 해결하는 완벽한 솔루션입니다! 🚀 