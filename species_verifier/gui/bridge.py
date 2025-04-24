"""
리팩토링 브릿지 모듈

이 모듈은 기존 main_gui.py 코드와 새로운 구조 간의 브릿지 역할을 합니다.
리팩토링이 완료될 때까지 일시적으로 사용되는 모듈입니다.
"""
import threading
from typing import Callable, List, Dict, Any, Union, Tuple, Optional

# 기존 main_gui.py의 함수를 직접 임포트하기 위한 try-except
try:
    from species_verifier.gui.main_gui import (
        _perform_verification as original_perform_verification,
        _perform_microbe_verification as original_perform_microbe_verification,
        _process_file as original_process_file,
        _process_microbe_file as original_process_microbe_file,
        _get_wiki_summary as original_get_wiki_summary,
        KOREAN_NAME_MAPPINGS
    )
    
    # 임포트 성공 로그
    print("[Info] Successfully imported original functions from main_gui.py")
    
except ImportError as e:
    print(f"[Error] Failed to import original functions from main_gui.py: {e}")
    # 더미 함수 정의
    def original_perform_verification(*args, **kwargs):
        print("[Warning] Using dummy perform_verification function")
        return []
    
    def original_perform_microbe_verification(*args, **kwargs):
        print("[Warning] Using dummy perform_microbe_verification function")
        return []
    
    def original_process_file(*args, **kwargs):
        print("[Warning] Using dummy process_file function")
        return []
    
    def original_process_microbe_file(*args, **kwargs):
        print("[Warning] Using dummy process_microbe_file function")
        return []
    
    def original_get_wiki_summary(*args, **kwargs):
        print("[Warning] Using dummy get_wiki_summary function")
        return "정보 없음 (더미 함수)"
    
    KOREAN_NAME_MAPPINGS = {}


# 코어 모듈 임포트 시도 (수정: 클래스 임포트 복원)
try:
    from species_verifier.core.marine_verifier import MarineSpeciesVerifier
    from species_verifier.core.wiki import get_wiki_summary
    from species_verifier.core.microbe_verifier import MicrobeVerifier
    # 함수 직접 임포트 제거
    # from species_verifier.core.verifier import verify_marine_species, verify_microbe_species
    
    HAS_CORE_MODULES = True
    print("[Info] Successfully imported core Verifier classes") # 로그 메시지 변경
    
except ImportError as e:
    print(f"[Error] Failed to import core modules: {e}")
    HAS_CORE_MODULES = False
    # 클래스 임포트 실패 시 None 할당
    MarineSpeciesVerifier = None
    MicrobeVerifier = None


def perform_verification(
    verification_list_input: Union[List[str], List[Tuple[str, str]]],
    update_progress: Callable[[float], None] = None,
    update_status: Callable[[str], None] = None,
    result_callback: Callable[[Dict[str, Any]], None] = None
) -> List[Dict[str, Any]]:
    """
    검증 수행을 위한 브릿지 함수 (수정: 클래스 사용 복원)
    
    Args:
        verification_list_input: 검증할 이름 목록
        update_progress: 진행 상태 업데이트 콜백
        update_status: 상태 메시지 업데이트 콜백
        result_callback: 개별 결과 업데이트 콜백
        
    Returns:
        검증 결과 목록 (Fallback 시에만 의미 있음)
    """
    # 수정: 클래스 존재 여부 확인
    if HAS_CORE_MODULES and MarineSpeciesVerifier:
        try:
            # 수정: Verifier 인스턴스 생성 및 콜백 전달
            verifier = MarineSpeciesVerifier(
                progress_callback=update_progress, 
                status_update_callback=update_status,
                result_callback=result_callback
            )
            # Core 모듈은 콜백으로 결과를 전달하므로, 반환값은 덜 중요
            print("[Bridge] Calling MarineSpeciesVerifier.perform_verification...")
            return verifier.perform_verification(verification_list_input)
        except Exception as e:
            print(f"[Error] Core module verification failed, falling back to original: {e}")
            return original_perform_verification(verification_list_input, update_progress, update_status)
    else:
        print("[Bridge] Falling back to original_perform_verification")
        return original_perform_verification(verification_list_input, update_progress, update_status)


def perform_microbe_verification(
    microbe_names_list: List[str],
    update_progress: Callable[[float], None] = None,
    update_status: Callable[[str], None] = None,
    result_callback: Callable[[Dict[str, Any]], None] = None,
    context: Union[List[str], str, None] = None
) -> List[Dict[str, Any]]:
    """
    미생물 검증 수행을 위한 브릿지 함수 (수정: 클래스 사용 복원)
    
    Args:
        microbe_names_list: 검증할 미생물 이름 목록
        update_progress: 진행 상태 업데이트 콜백
        update_status: 상태 메시지 업데이트 콜백
        result_callback: 개별 결과 업데이트 콜백
        context: 검증 컨텍스트 (파일 경로 또는 학명 리스트)
        
    Returns:
        미생물 검증 결과 목록 (Fallback 시에만 의미 있음)
    """
    # 수정: 클래스 존재 여부 확인
    if HAS_CORE_MODULES and MicrobeVerifier:
        try:
             # 수정: Verifier 인스턴스 생성 및 콜백 전달
            verifier = MicrobeVerifier(
                progress_callback=update_progress,
                status_update_callback=update_status,
                result_callback=result_callback
            )
            print("[Bridge] Calling MicrobeVerifier.perform_microbe_verification...")
            # MicrobeVerifier의 메서드 호출 시 context 전달
            return verifier.perform_microbe_verification(microbe_names_list, context=context)
        except Exception as e:
            print(f"[Error] Core module microbe verification failed, falling back to original: {e}")
            return original_perform_microbe_verification(microbe_names_list)
    else:
        print("[Bridge] Falling back to original_perform_microbe_verification")
        return original_perform_microbe_verification(microbe_names_list)


def process_file(file_path: str) -> List[Any]:
    """
    파일에서 학명 추출을 위한 브릿지 함수 (수정: 헤더 없는 경우 처리 개선)
    
    Args:
        file_path: 파일 경로
        
    Returns:
        추출된 학명 목록
    """
    import os
    import pandas as pd
    import csv
    
    file_ext = os.path.splitext(file_path)[1].lower()
    scientific_names = []
    df = None # DataFrame 변수 초기화
    
    try:
        # 1. 파일 확장자에 따라 읽기 시도 (기본값: header=0)
        print(f"[Info Bridge] 파일 읽기 시도 (header=0 가정): {file_path}")
        if file_ext == '.csv':
            try:
                # UTF-8 시도, 실패 시 다른 인코딩(cp949) 시도
                try:
                    df = pd.read_csv(file_path, header=0)
                except UnicodeDecodeError:
                    print("[Warning Bridge] UTF-8 디코딩 실패, cp949 시도...")
                    df = pd.read_csv(file_path, header=0, encoding='cp949')
            except Exception as read_err:
                print(f"[Error Bridge] CSV 파일 읽기 오류 (header=0): {read_err}")
                # CSV 읽기 실패 시에도 대체 로직 시도 가능 (예: header=None)
        elif file_ext in ['.xlsx', '.xls']:
            try:
                df = pd.read_excel(file_path, header=0)
            except Exception as read_err:
                 print(f"[Error Bridge] Excel 파일 읽기 오류 (header=0): {read_err}")
        elif file_ext == '.txt':
            # 텍스트 파일은 pandas 대신 직접 처리 유지
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                scientific_names = [line.strip() for line in lines if line.strip()]
            print(f"[Info Bridge] TXT 파일 직접 처리 완료.")
        else:
            print(f"[Error Bridge] 지원하지 않는 파일 형식: {file_ext}")
            return []

        # 2. DataFrame 처리 (TXT 파일 제외)
        if df is not None:
            print(f"[Debug Bridge] DataFrame 로드 성공. 컬럼: {df.columns.tolist()}")
            found_target_col = False
            # 2-1. 적합한 컬럼 이름 찾기
            for col in df.columns:
                if isinstance(col, str) and col.lower() in ['scientific_name', 'scientificname', 'scientific name', 'name', '학명', 'species']:
                    print(f"[Info Bridge] 대상 컬럼 찾음: '{col}'")
                    scientific_names = df[col].dropna().astype(str).tolist()
                    found_target_col = True
                    break
            
            # 2-2. 적합한 컬럼 이름이 없을 경우 -> 헤더 없다고 가정하고 다시 읽기
            if not found_target_col:
                print("[Warning Bridge] 대상 컬럼 이름 없음. header=None으로 다시 시도...")
                df_no_header = None
                try:
                    if file_ext == '.csv':
                         try:
                             df_no_header = pd.read_csv(file_path, header=None)
                         except UnicodeDecodeError:
                             df_no_header = pd.read_csv(file_path, header=None, encoding='cp949')
                    elif file_ext in ['.xlsx', '.xls']:
                        df_no_header = pd.read_excel(file_path, header=None)
                    
                    if df_no_header is not None and not df_no_header.empty:
                        print("[Info Bridge] header=None 읽기 성공. 첫 번째 컬럼 사용.")
                        scientific_names = df_no_header.iloc[:, 0].dropna().astype(str).tolist()
                    else:
                         print("[Warning Bridge] header=None 읽기 실패 또는 빈 파일. 기존 첫 컬럼 사용 시도.")
                         # 최후의 수단: 처음에 읽은 df의 첫 컬럼 사용 (데이터 손실 가능성 인지)
                         if not df.empty:
                              scientific_names = df.iloc[:, 0].dropna().astype(str).tolist()
                         else:
                              print("[Error Bridge] 파일이 비어있거나 읽을 수 없음.")
                              return []
                except Exception as read_err_no_header:
                     print(f"[Error Bridge] 파일 읽기 오류 (header=None): {read_err_no_header}")
                     # 재시도 실패 시 빈 리스트 반환
                     return []
        
        # 3. 결과 정제 (공통)
        # astype(str)을 추가하여 숫자 등이 포함된 경우 문자열로 변환
        scientific_names = [name.strip() for name in scientific_names if name and isinstance(name, str)]
        scientific_names = [name for name in scientific_names if name] # 혹시 모를 빈 문자열 제거
        # 중복 제거
        scientific_names = list(dict.fromkeys(scientific_names))
        
        print(f"[Info Bridge] 최종 추출된 학명 수: {len(scientific_names)}")
        if scientific_names:
            print(f"[Info Bridge] 최종 학명 샘플: {scientific_names[:5]}")
        
        return scientific_names
        
    except Exception as e:
        import traceback
        print(f"[Error Bridge] 파일 처리 중 예측 못한 오류 발생: {e}")
        print(traceback.format_exc())
        return []


def process_microbe_file(file_path: str) -> List[str]:
    """
    파일에서 미생물 학명 추출을 위한 브릿지 함수
    
    Args:
        file_path: 파일 경로
        
    Returns:
        추출된 미생물 학명 목록
    """
    import os
    import pandas as pd
    import csv
    
    file_ext = os.path.splitext(file_path)[1].lower()
    microbe_names = []
    
    try:
        # 파일 확장자에 따라 다른 처리
        if file_ext == '.csv':
            # CSV 파일 처리
            try:
                # 먼저 pandas로 시도
                df = pd.read_csv(file_path, encoding='utf-8')
                # 가장 적합한 열 찾기
                for col in df.columns:
                    if col.lower() in ['scientific_name', 'scientificname', 'scientific name', 'name', '학명', 'species', 'microbe', 'bacteria']:
                        microbe_names = df[col].dropna().tolist()
                        break
                
                # 적합한 열이 없으면 첫 번째 열 사용
                if not microbe_names and len(df.columns) > 0:
                    microbe_names = df.iloc[:, 0].dropna().tolist()
                
            except Exception as e:
                print(f"[Warning] Pandas CSV 로드 실패, csv 모듈로 시도: {e}")
                # pandas 로드 실패 시 csv 모듈 사용
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    headers = next(reader, None)
                    
                    if headers:
                        # 적합한 열 인덱스 찾기
                        target_col = 0
                        for i, header in enumerate(headers):
                            if header.lower() in ['scientific_name', 'scientificname', 'scientific name', 'name', '학명', 'species', 'microbe', 'bacteria']:
                                target_col = i
                                break
                        
                        for row in reader:
                            if len(row) > target_col and row[target_col].strip():
                                microbe_names.append(row[target_col].strip())
        
        elif file_ext in ['.xlsx', '.xls']:
            # Excel 파일 처리
            df = pd.read_excel(file_path)
            # 가장 적합한 열 찾기
            for col in df.columns:
                if col.lower() in ['scientific_name', 'scientificname', 'scientific name', 'name', '학명', 'species', 'microbe', 'bacteria']:
                    microbe_names = df[col].dropna().tolist()
                    break
            
            # 적합한 열이 없으면 첫 번째 열 사용
            if not microbe_names and len(df.columns) > 0:
                microbe_names = df.iloc[:, 0].dropna().tolist()
        
        elif file_ext == '.txt':
            # 텍스트 파일 처리
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                microbe_names = [line.strip() for line in lines if line.strip()]
        
        else:
            print(f"[Error] 지원하지 않는 파일 형식: {file_ext}")
            return []
        
        # 결과 정제
        microbe_names = [name for name in microbe_names if name and isinstance(name, str)]
        microbe_names = [name.strip() for name in microbe_names]
        # 중복 제거
        microbe_names = list(dict.fromkeys(microbe_names))
        
        print(f"[Info] 파일에서 추출한 미생물 학명 수: {len(microbe_names)}")
        if microbe_names:
            print(f"[Info] 미생물 학명 샘플: {microbe_names[:5]}")
        
        return microbe_names
        
    except Exception as e:
        import traceback
        print(f"[Error] 미생물 파일 처리 중 오류 발생: {e}")
        print(traceback.format_exc())
        return []


def get_wiki_summary(search_term: str) -> str:
    """
    위키백과 요약 검색을 위한 브릿지 함수
    
    Args:
        search_term: 검색어
        
    Returns:
        위키백과 요약
    """
    if HAS_CORE_MODULES:
        try:
            # 코어 모듈 사용
            return get_wiki_summary(search_term)
        except Exception as e:
            print(f"[Error] Core wiki search failed, falling back to original: {e}")
            # 예외 발생 시 기존 함수로 폴백
            return original_get_wiki_summary(search_term)
    else:
        # 코어 모듈이 없는 경우 기존 함수 사용
        return original_get_wiki_summary(search_term) 