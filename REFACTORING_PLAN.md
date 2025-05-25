@

# Species Verifier 리팩토링 계획

**목표:**

1.  **모듈화:** `main_gui.py`를 기능별로 더 작고 관리하기 쉬운 여러 파일(모듈)로 분리합니다.
2.  **관심사 분리 (Separation of Concerns):** UI 로직, 핵심 검증 로직(WoRMS, LPSN, Wiki 등), 데이터 처리, 상태 관리, 설정 관리 등을 명확히 분리합니다.
3.  **코드 재사용성 증대:** 중복되는 코드(예: 결과 표시, UI 업데이트 로직)를 식별하고 공통 함수나 클래스로 통합합니다.
4.  **가독성 및 유지보수성 향상:** 코드를 더 이해하기 쉽고 수정하기 용이하게 만들며, PEP 8 가이드라인 및 명확한 Docstring 작성을 준수합니다.
5.  **미래 확장성 확보:** UI(Flutter), 백엔드/DB(FastAPI, Supabase) 기술 스택 변경 및 비동기 처리 도입에 유연하게 대응할 수 있는 구조를 만듭니다.
6.  **테스트 용이성 증대:** 모듈화 및 관심사 분리를 통해 단위 테스트 작성을 용이하게 합니다.

**단계:**

1.  **코드 분석:**
    *   `main_gui.py` 내 주요 기능 블록 식별 (UI 구성, 탭별 로직, 파일 처리, API 연동, 헬퍼 함수 등)
    *   중복 코드 패턴 탐색 (예: Treeview 업데이트, 상태 업데이트, 에러 처리 방식)
    *   현재 코드의 의존성 관계 분석

2.  **Configuration 관리:**
    *   API URL, 파일 경로, 처리 제한 개수 등 설정 값들을 `config.py` 또는 `.env` 파일을 이용한 설정 관리 모듈로 분리합니다.

3.  **핵심 로직 분리 (`species_verifier/core`):**
    *   해양생물(`_perform_verification`), 미생물(`_perform_microbe_verification`) 검증 로직을 `core` 모듈 또는 하위 모듈로 분리합니다.
    *   심층분석 결과(`_get_wiki_summary`) 로직을 분리합니다.
    *   데이터 정리 로직(`_clean_scientific_name`) 등을 유틸리티 함수로 분리 (`species_verifier/utils` 활용 고려).

4.  **외부 서비스 연동 분리 (`species_verifier/services`):**
    *   WoRMS, LPSN, Wikipedia API 호출 및 스크래핑 로직을 서비스별 모듈(`worms_service.py`, `lpsn_service.py`, `wiki_service.py`)로 분리합니다.
    *   (고려사항) 향후 비동기(asyncio) 전환을 염두에 두고 인터페이스를 설계합니다.

5.  **UI 로직 분리 (`species_verifier/gui/components`):**
    *   메인 `SpeciesVerifierApp` 클래스를 더 작은 UI 컴포넌트 클래스로 분리합니다.
        *   탭별 프레임 관리 클래스 (`MarineTabFrame`, `MicrobeTabFrame`)
        *   결과 Treeview 관리 클래스 (`ResultTreeview`)
        *   상태 표시줄 관리 클래스 (`StatusBar`)
        *   팝업 윈도우 (매핑 관리, 위키 요약 등) 관리 클래스
    *   UI 관련 헬퍼 함수(툴팁, 컨텍스트 메뉴 등)는 해당 UI 컴포넌트 클래스로 이동합니다.

6.  **데이터 및 상태 관리 개선:**
    *   파일 읽기/파싱 로직(`_process_file`, `_process_microbe_file`)을 `species_verifier/utils/file_processor.py` 와 같은 유틸리티 모듈로 분리합니다.
    *   **Pydantic 모델 도입:** 검증 결과, API 응답 등 주요 데이터 구조를 Pydantic 모델로 정의하여 데이터 유효성 검사 및 명확성을 높입니다.
    *   **상태 관리 명확화:** 애플리케이션 상태(현재 결과, 활성 탭 등)를 관리하는 중앙화된 방식 도입 고려 (예: `AppState` 클래스).

7.  **로깅 및 에러 처리 표준화:**
    *   Python의 `logging` 모듈을 사용하여 체계적인 로깅 시스템을 구축합니다. (로그 레벨, 포맷, 파일 출력 등 정책 정의)
    *   API 호출, 파일 처리 등 다양한 부분의 에러 처리 방식을 표준화하고, 사용자에게 명확한 피드백을 제공합니다.

8.  **문서화 강화:**
    *   리팩토링 과정에서 생성/수정되는 모든 모듈, 클래스, 함수에 대해 명확하고 상세한 Docstring을 작성합니다.

9.  **단위 테스트 작성 (`tests` 디렉토리):**
    *   분리된 핵심 로직, 서비스 모듈, 유틸리티 함수에 대한 단위 테스트를 작성하여 코드의 신뢰성을 확보합니다.

**진행 방식:**

*   각 단계별로 브랜치(Branch)를 생성하여 작업을 진행하고, 완료 후 메인 브랜치에 병합(Merge)합니다.
*   코드 리뷰를 통해 리팩토링 결과의 품질을 검증합니다.
*   이 `REFACTORING_PLAN.md` 파일에 진행 상황을 기록합니다.
