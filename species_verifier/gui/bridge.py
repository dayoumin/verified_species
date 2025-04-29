"""
리팩토링 브릿지 모듈

이 모듈은 기존 main_gui.py 코드와 새로운 구조 간의 브릿지 역할을 합니다.
리팩토링이 완료될 때까지 일시적으로 사용되는 모듈입니다.
"""
import threading
from typing import Callable, List, Dict, Any, Union, Tuple, Optional
import sys  # 추가
import os   # 추가
import pandas as pd # 추가 (process_file 내부 import 제거 가능)
from pathlib import Path # 추가
import asyncio

# 기존 main_gui.py의 함수를 직접 임포트하기 위한 try-except
try:
    from species_verifier.gui.main_gui import (
        _perform_verification as original_perform_verification,
        _perform_microbe_verification as original_perform_microbe_verification,
        _process_file as original_process_file,
        _process_microbe_file as original_process_microbe_file,
        _get_wiki_summary as original_get_wiki_summary,
        # KOREAN_NAME_MAPPINGS # 기존 JSON 매핑 임포트 제거
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

# --- 국명-학명 매핑 로딩 로직 (Excel 파일 기반) ---

def get_base_path():
    """ 실행 파일의 기본 경로를 반환합니다 (개발 환경과 .exe 환경 모두 지원). """
    if getattr(sys, 'frozen', False):
        # .exe로 실행될 때
        return Path(sys.executable).parent
    else:
        # 스크립트로 실행될 때 (.py)
        # bridge.py는 gui 폴더 안에 있으므로, 프로젝트 루트는 두 단계 위입니다.
        return Path(__file__).resolve().parent.parent.parent

def load_korean_mappings_from_excel() -> Dict[str, str]:
    """ 실행 파일 옆의 data 폴더에 있는 Excel 파일에서 매핑을 로드합니다. """
    base_path = get_base_path()
    # 'data' 하위 폴더에 있다고 가정
    excel_path = base_path / "data" / "korean_mappings.xlsx"
    print(f"[Info Bridge] Attempting to load Korean mappings from: {excel_path}")

    mappings = {}
    if excel_path.exists():
        try:
            df = pd.read_excel(excel_path, header=0) # 첫 번째 행을 헤더로 사용
            # '국명', '학명' 컬럼이 있는지 확인 (대소문자, 공백 무시)
            df.columns = [str(col).strip().lower() for col in df.columns] # 컬럼명을 문자열로 변환 후 처리
            required_cols = ['국명', '학명']
            if all(col in df.columns for col in required_cols):
                # NaN 값 제거 후 딕셔너리 생성 (국명과 학명 모두 문자열로 변환)
                df_cleaned = df[required_cols].dropna()
                df_cleaned['국명'] = df_cleaned['국명'].astype(str)
                df_cleaned['학명'] = df_cleaned['학명'].astype(str)
                # 중복된 국명이 있을 경우 마지막 값 사용 (기본 동작)
                mappings = pd.Series(df_cleaned.학명.values, index=df_cleaned.국명).to_dict()
                print(f"[Info Bridge] Loaded {len(mappings)} Korean mappings from {excel_path}")
            else:
                print(f"[Error Bridge] Excel file {excel_path} missing required columns '국명' or '학명'. Found columns: {df.columns.tolist()}")

        except Exception as e:
            print(f"[Error Bridge] Failed to load or parse Excel mappings from {excel_path}: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"[Warning Bridge] Mapping file not found at {excel_path}. Korean name lookup will not work.")
    return mappings

# KOREAN_NAME_MAPPINGS 딕셔너리를 Excel 로딩 함수 호출 결과로 초기화
KOREAN_NAME_MAPPINGS: Dict[str, str] = load_korean_mappings_from_excel()

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
    
    file_ext = os.path.splitext(file_path)[1].lower()
    scientific_names = []
    df = None
    
    try:
        print(f"[Info Bridge] 파일 '{file_path}' 처리 시작.")
        
        # 1. 파일 형식에 따른 초기 로드
        if file_ext == '.csv':
            try:
                try:
                    # 첫 줄이 헤더인지 판단하기 위해 미리 몇 줄 읽어봄
                    sample_df = pd.read_csv(file_path, nrows=5)
                    print(f"[Debug Bridge] 파일 첫 5줄 샘플: {sample_df.head().to_dict()}")
                    
                    # 첫 번째 행이 헤더인지 확인 (학명, scientificname 등의 키워드 포함)
                    header_keywords = ['scientific_name', 'scientificname', 'scientific name', 'name', '학명', 'species']
                    has_header = False
                    
                    if len(sample_df.columns) > 0:
                        for col in sample_df.columns:
                            if isinstance(col, str) and any(keyword in col.lower() for keyword in header_keywords):
                                has_header = True
                                print(f"[Info Bridge] 헤더 식별됨: '{col}'")
                                break
                    
                    # 헤더 여부에 따라 다르게 로드
                    if has_header:
                        print("[Info Bridge] 파일에 헤더가 있습니다. header=0으로 로드합니다.")
                        df = pd.read_csv(file_path, header=0)
                    else:
                        print("[Info Bridge] 파일에 헤더가 없습니다. header=None으로 로드합니다.")
                        df = pd.read_csv(file_path, header=None)
                except UnicodeDecodeError:
                    print("[Warning Bridge] UTF-8 디코딩 실패, cp949 시도...")
                    # 첫 줄이 헤더인지 확인 (cp949 인코딩으로)
                    sample_df = pd.read_csv(file_path, nrows=5, encoding='cp949')
                    
                    # 헤더 확인 로직과 동일
                    header_keywords = ['scientific_name', 'scientificname', 'scientific name', 'name', '학명', 'species']
                    has_header = False
                    
                    if len(sample_df.columns) > 0:
                        for col in sample_df.columns:
                            if isinstance(col, str) and any(keyword in col.lower() for keyword in header_keywords):
                                has_header = True
                                break
                    
                    if has_header:
                        df = pd.read_csv(file_path, header=0, encoding='cp949')
                    else:
                        df = pd.read_csv(file_path, header=None, encoding='cp949')
            except Exception as read_err:
                print(f"[Error Bridge] CSV 파일 읽기 오류: {read_err}")
        
        elif file_ext in ['.xlsx', '.xls']:
            try:
                # 첫 줄이 헤더인지 판단하기 위해 미리 몇 줄 읽어봄
                sample_df = pd.read_excel(file_path, nrows=5)
                
                # 첫 번째 행이 헤더인지 확인
                header_keywords = ['scientific_name', 'scientificname', 'scientific name', 'name', '학명', 'species']
                has_header = False
                
                if len(sample_df.columns) > 0:
                    for col in sample_df.columns:
                        if isinstance(col, str) and any(keyword in col.lower() for keyword in header_keywords):
                            has_header = True
                            print(f"[Info Bridge] 헤더 식별됨: '{col}'")
                            break
                
                # 헤더 여부에 따라 다르게 로드
                if has_header:
                    print("[Info Bridge] 파일에 헤더가 있습니다. header=0으로 로드합니다.")
                    df = pd.read_excel(file_path, header=0)
                else:
                    print("[Info Bridge] 파일에 헤더가 없습니다. header=None으로 로드합니다.")
                    df = pd.read_excel(file_path, header=None)
            
            except Exception as read_err:
                print(f"[Error Bridge] Excel 파일 읽기 오류: {read_err}")
        
        elif file_ext == '.txt':
            # 텍스트 파일은 pandas 대신 직접 처리
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
                # 첫 줄이 헤더인지 확인
                has_header = False
                if lines and any(keyword in lines[0].lower() for keyword in ['scientific_name', 'scientificname', 'scientific name', 'name', '학명', 'species']):
                    has_header = True
                    print("[Info Bridge] 텍스트 파일에 헤더가 있습니다. 첫 줄을 제외합니다.")
                    scientific_names = [line.strip() for line in lines[1:] if line.strip()]
                else:
                    print("[Info Bridge] 텍스트 파일에 헤더가 없습니다. 모든 줄을 처리합니다.")
                    scientific_names = [line.strip() for line in lines if line.strip()]
                
                print(f"[Info Bridge] TXT 파일 직접 처리 완료. 추출된 학명 수: {len(scientific_names)}")
                
                # 결과 정제 (공통)
                scientific_names = [name for name in scientific_names if name and isinstance(name, str)]
                scientific_names = list(dict.fromkeys(scientific_names))  # 중복 제거
                
                print(f"[Info Bridge] 최종 추출된 학명 수: {len(scientific_names)}")
                return scientific_names
        else:
            print(f"[Error Bridge] 지원하지 않는 파일 형식: {file_ext}")
            return []

        # 2. DataFrame 처리 (TXT 파일 제외)
        if df is not None:
            print(f"[Debug Bridge] DataFrame 로드 성공. 컬럼: {df.columns.tolist()}")
            
            # DataFrame에서 데이터 추출
            if df.columns.name is None and not any(isinstance(col, str) and col.lower() in ['scientific_name', 'scientificname', 'scientific name', 'name', '학명', 'species'] for col in df.columns):
                # 헤더 없는 경우 (이미 header=None으로 로드됨)
                print("[Info Bridge] 헤더 없는 파일로 처리. 첫 번째 컬럼 사용.")
                if not df.empty and len(df.columns) > 0:
                    scientific_names = df.iloc[:, 0].dropna().astype(str).tolist()
            else:
                # 헤더 있는 경우
                found_target_col = False
                for col in df.columns:
                    if isinstance(col, str) and col.lower() in ['scientific_name', 'scientificname', 'scientific name', 'name', '학명', 'species']:
                        print(f"[Info Bridge] 대상 컬럼 찾음: '{col}'")
                        scientific_names = df[col].dropna().astype(str).tolist()
                        found_target_col = True
                        break
                
                # 적합한 컬럼 못 찾으면 첫 번째 컬럼 사용
                if not found_target_col and not df.empty and len(df.columns) > 0:
                    print("[Info Bridge] 적합한 헤더 컬럼 없음. 첫 번째 컬럼 사용.")
                    scientific_names = df.iloc[:, 0].dropna().astype(str).tolist()
        
        # 3. 결과 정제 (공통)
        scientific_names = [name.strip() for name in scientific_names if name and isinstance(name, str)]
        scientific_names = [name for name in scientific_names if name]  # 빈 문자열 제거
        scientific_names = list(dict.fromkeys(scientific_names))  # 중복 제거
        
        total_rows = len(scientific_names)
        print(f"[Info Bridge] 최종 추출된 학명 수: {total_rows}")
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
        print(f"[Info Bridge] 미생물 파일 '{file_path}' 처리 시작.")
        
        # 파일 확장자에 따라 다른 처리
        if file_ext == '.csv':
            try:
                # 첫 줄이 헤더인지 확인하기 위해 미리 읽어봄
                sample_df = pd.read_csv(file_path, nrows=5, encoding='utf-8')
                
                # 첫 번째 행이 헤더인지 확인
                header_keywords = ['scientific_name', 'scientificname', 'scientific name', 'name', '학명', 'species', 'microbe', 'bacteria']
                has_header = False
                
                if len(sample_df.columns) > 0:
                    for col in sample_df.columns:
                        if isinstance(col, str) and any(keyword in col.lower() for keyword in header_keywords):
                            has_header = True
                            print(f"[Info Bridge] 헤더 식별됨: '{col}'")
                            break
                
                # 헤더 여부에 따라 다르게 로드
                if has_header:
                    print("[Info Bridge] 파일에 헤더가 있습니다. header=0으로 로드합니다.")
                    df = pd.read_csv(file_path, header=0, encoding='utf-8')
                    # 대상 컬럼 찾기
                    target_col = None
                    for col in df.columns:
                        if col.lower() in header_keywords:
                            target_col = col
                            break
                    
                    if target_col:
                        microbe_names = df[target_col].dropna().astype(str).tolist()
                    elif len(df.columns) > 0:
                        microbe_names = df.iloc[:, 0].dropna().astype(str).tolist()
                else:
                    print("[Info Bridge] 파일에 헤더가 없습니다. header=None으로 로드합니다.")
                    df = pd.read_csv(file_path, header=None, encoding='utf-8')
                    if not df.empty and len(df.columns) > 0:
                        microbe_names = df.iloc[:, 0].dropna().astype(str).tolist()
                
            except UnicodeDecodeError:
                print("[Warning Bridge] UTF-8 디코딩 실패, cp949 시도...")
                try:
                    # 첫 줄이 헤더인지 확인 (cp949 인코딩으로)
                    sample_df = pd.read_csv(file_path, nrows=5, encoding='cp949')
                    
                    # 헤더 확인 로직
                    header_keywords = ['scientific_name', 'scientificname', 'scientific name', 'name', '학명', 'species', 'microbe', 'bacteria']
                    has_header = False
                    
                    if len(sample_df.columns) > 0:
                        for col in sample_df.columns:
                            if isinstance(col, str) and any(keyword in col.lower() for keyword in header_keywords):
                                has_header = True
                                break
                    
                    if has_header:
                        df = pd.read_csv(file_path, header=0, encoding='cp949')
                        # 대상 컬럼 찾기
                        target_col = None
                        for col in df.columns:
                            if col.lower() in header_keywords:
                                target_col = col
                                break
                        
                        if target_col:
                            microbe_names = df[target_col].dropna().astype(str).tolist()
                        elif len(df.columns) > 0:
                            microbe_names = df.iloc[:, 0].dropna().astype(str).tolist()
                    else:
                        df = pd.read_csv(file_path, header=None, encoding='cp949')
                        if not df.empty and len(df.columns) > 0:
                            microbe_names = df.iloc[:, 0].dropna().astype(str).tolist()
                except Exception as e:
                    print(f"[Error Bridge] CP949 로드 실패: {e}")
            except Exception as read_err:
                print(f"[Warning Bridge] Pandas CSV 로드 실패: {read_err}")
        
        elif file_ext in ['.xlsx', '.xls']:
            try:
                # 첫 줄이 헤더인지 확인하기 위해 미리 읽어봄
                sample_df = pd.read_excel(file_path, nrows=5)
                
                # 첫 번째 행이 헤더인지 확인
                header_keywords = ['scientific_name', 'scientificname', 'scientific name', 'name', '학명', 'species', 'microbe', 'bacteria']
                has_header = False
                
                if len(sample_df.columns) > 0:
                    for col in sample_df.columns:
                        if isinstance(col, str) and any(keyword in col.lower() for keyword in header_keywords):
                            has_header = True
                            print(f"[Info Bridge] 헤더 식별됨: '{col}'")
                            break
                
                # 헤더 여부에 따라 다르게 로드
                if has_header:
                    print("[Info Bridge] 파일에 헤더가 있습니다. header=0으로 로드합니다.")
                    df = pd.read_excel(file_path, header=0)
                    # 대상 컬럼 찾기
                    target_col = None
                    for col in df.columns:
                        if col.lower() in header_keywords:
                            target_col = col
                            break
                    
                    if target_col:
                        microbe_names = df[target_col].dropna().astype(str).tolist()
                    elif len(df.columns) > 0:
                        microbe_names = df.iloc[:, 0].dropna().astype(str).tolist()
                else:
                    print("[Info Bridge] 파일에 헤더가 없습니다. header=None으로 로드합니다.")
                    df = pd.read_excel(file_path, header=None)
                    if not df.empty and len(df.columns) > 0:
                        microbe_names = df.iloc[:, 0].dropna().astype(str).tolist()
            except Exception as read_err:
                print(f"[Error Bridge] Excel 파일 읽기 오류: {read_err}")
        
        elif file_ext == '.txt':
            # 텍스트 파일 직접 처리
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                    # 첫 줄이 헤더인지 확인
                    header_keywords = ['scientific_name', 'scientificname', 'scientific name', 'name', '학명', 'species', 'microbe', 'bacteria']
                    has_header = False
                    if lines and any(keyword in lines[0].lower() for keyword in header_keywords):
                        has_header = True
                        print("[Info Bridge] 텍스트 파일에 헤더가 있습니다. 첫 줄을 제외합니다.")
                        microbe_names = [line.strip() for line in lines[1:] if line.strip()]
                    else:
                        print("[Info Bridge] 텍스트 파일에 헤더가 없습니다. 모든 줄을 처리합니다.")
                        microbe_names = [line.strip() for line in lines if line.strip()]
            except UnicodeDecodeError:
                print("[Warning Bridge] UTF-8 디코딩 실패, cp949 시도...")
                with open(file_path, 'r', encoding='cp949') as f:
                    lines = f.readlines()
                    
                    # 첫 줄이 헤더인지 확인
                    header_keywords = ['scientific_name', 'scientificname', 'scientific name', 'name', '학명', 'species', 'microbe', 'bacteria']
                    has_header = False
                    if lines and any(keyword in lines[0].lower() for keyword in header_keywords):
                        has_header = True
                        print("[Info Bridge] 텍스트 파일에 헤더가 있습니다. 첫 줄을 제외합니다.")
                        microbe_names = [line.strip() for line in lines[1:] if line.strip()]
                    else:
                        print("[Info Bridge] 텍스트 파일에 헤더가 없습니다. 모든 줄을 처리합니다.")
                        microbe_names = [line.strip() for line in lines if line.strip()]
            except Exception as e:
                print(f"[Error Bridge] 텍스트 파일 처리 중 오류: {e}")
        
        else:
            print(f"[Error Bridge] 지원하지 않는 파일 형식: {file_ext}")
            return []
        
        # 결과 정제
        microbe_names = [name for name in microbe_names if name and isinstance(name, str)]
        microbe_names = [name.strip() for name in microbe_names]
        # 중복 제거
        microbe_names = list(dict.fromkeys(microbe_names))
        
        total_rows = len(microbe_names)
        print(f"[Info Bridge] 최종 추출된 미생물 학명 수: {total_rows}")
        if microbe_names:
            print(f"[Info Bridge] 미생물 학명 샘플: {microbe_names[:5]}")
        
        return microbe_names
        
    except Exception as e:
        import traceback
        print(f"[Error Bridge] 미생물 파일 처리 중 오류 발생: {e}")
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


async def process_batch(names: List[str], callback: Callable[[Dict[str, Any]], None]) -> List[Dict[str, Any]]:
    """
    학명 목록을 배치로 처리합니다.
    
    Args:
        names: 처리할 학명 목록
        callback: 결과를 처리할 콜백 함수
        
    Returns:
        처리된 결과 목록
    """
    results = []
    for name in names:
        try:
            # 여기에 API 호출 로직이 들어감 (verify_species는 예시)
            result = await verify_species(name)  # 비동기 검증 함수 호출
            if callback:
                callback(result)
            results.append(result)
            # API 호출 후 지연 시간 추가
            await asyncio.sleep(api_config.REQUEST_DELAY)
        except Exception as e:
            print(f"[Error] 처리 중 오류 발생: {e}")
            results.append({"name": name, "error": str(e)})
            # 오류 발생 시에도 잠시 대기하여 연속 오류 방지
            await asyncio.sleep(api_config.REQUEST_DELAY)
    return results 