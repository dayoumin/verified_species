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
    from species_verifier.gui.main_gui_backup import (
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
    def original_perform_verification(verification_list_input, update_progress=None, update_status=None, result_callback=None, check_cancelled=None):
        print(f"[Warning] Using original_perform_verification function with {len(verification_list_input)} items")
        
        # 결과 저장 리스트
        results = []
        
        # 진행 상태 업데이트 함수가 제공된 경우 사용
        if update_status:
            update_status(f"해양생물 검증 시작 (총 {len(verification_list_input)}개)")
        
        # 각 항목에 대해 처리
        for idx, item in enumerate(verification_list_input):
            # 취소 여부 확인
            if check_cancelled and check_cancelled():
                print("[Info Bridge] Original 함수에서 검증 취소 요청 받음 - 반복 중단")
                break
                
            # 진행률 업데이트
            if update_progress:
                progress = (idx + 1) / len(verification_list_input)
                print(f"[Debug Original] 해양생물 진행률 계산: {progress:.2f}, 현재 항목: {idx+1}, 전체 항목 수: {len(verification_list_input)}")
                # 현재 항목과 전체 항목 수도 함께 전달
                update_progress(progress, idx+1, len(verification_list_input))
            
            # 상태 메시지 업데이트
            item_name = item[0] if isinstance(item, tuple) else item
            if update_status:
                update_status(f"해양생물 검증 중: {item_name} ({idx+1}/{len(verification_list_input)}) - 전체 {len(verification_list_input)}개 중 {idx+1}번째")
            
            # 간단한 결과 생성 (실제 검증 없이)
            result = {
                "scientific_name": item_name,
                "status": "unknown",
                "matched_name": item_name,
                "authority": "",
                "rank": "Species",
                "source": "WoRMS",
                "wiki_summary": "",
                "confidence": 0.0
            }
            
            # 결과 리스트에 추가
            results.append(result)
            
            # 콜백 함수가 제공된 경우 호출
            if result_callback:
                result_callback(result, "marine")
        
        return results
    
    def original_perform_microbe_verification(microbe_names_list, update_progress=None, update_status=None, result_callback=None, context=None, check_cancelled=None):
        print(f"[Warning] Using original_perform_microbe_verification function with {len(microbe_names_list)} items")
        
        # 결과 저장 리스트
        results = []
        
        # 진행 상태 업데이트 함수가 제공된 경우 사용
        if update_status:
            update_status(f"미생물 검증 시작 (총 {len(microbe_names_list)}개)")
        
        # 각 항목에 대해 처리
        for idx, name in enumerate(microbe_names_list):
            # 취소 여부 확인
            if check_cancelled and check_cancelled():
                print("[Info Bridge] Original 함수에서 검증 취소 요청 받음 - 반복 중단")
                break
                
            # 진행률 업데이트
            if update_progress:
                progress = (idx + 1) / len(microbe_names_list)
                print(f"[Debug Original] 미생물 진행률 계산: {progress:.2f}, 현재 항목: {idx+1}, 전체 항목 수: {len(microbe_names_list)}")
                # 현재 항목과 전체 항목 수도 함께 전달
                update_progress(progress, idx+1, len(microbe_names_list))
            
            # 상태 메시지 업데이트
            if update_status:
                update_status(f"미생물 검증 중: {name} ({idx+1}/{len(microbe_names_list)}) - 전체 {len(microbe_names_list)}개 중 {idx+1}번째")
            
            # 간단한 결과 생성 (실제 검증 없이)
            result = {
                "scientific_name": name,
                "status": "unknown",
                "matched_name": name,
                "authority": "",
                "rank": "Species",
                "source": "LPSN",
                "wiki_summary": "",
                "confidence": 0.0
            }
            
            # 결과 리스트에 추가
            results.append(result)
            
            # 콜백 함수가 제공된 경우 호출
            if result_callback:
                result_callback(result, "microbe")
        
        return results
    
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
    result_callback: Callable[[Dict[str, Any]], None] = None,
    check_cancelled: Callable[[], bool] = None
) -> List[Dict[str, Any]]:
    """
    검증 수행을 위한 브릿지 함수 (수정: 클래스 사용 복원)
    
    Args:
        verification_list_input: 검증할 이름 목록
        update_progress: 진행 상태 업데이트 콜백
        update_status: 상태 메시지 업데이트 콜백
        result_callback: 개별 결과 업데이트 콜백
        check_cancelled: 취소 여부 확인 함수
        
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
            print(f"[Bridge] Calling MarineSpeciesVerifier.perform_verification for {len(verification_list_input)} items...")
            
            # 검증 전 입력 학명 수 출력
            print(f"[Debug Bridge] 검증할 해양생물 학명 수: {len(verification_list_input)}")
            if verification_list_input and len(verification_list_input) > 0:
                print(f"[Debug Bridge] 검증할 해양생물 학명 샘플: {verification_list_input[:min(5, len(verification_list_input))]}")
            
            # 각 항목을 개별적으로 처리하여 모든 항목이 처리되도록 함
            results = []
            for i, item in enumerate(verification_list_input):
                # 취소 여부 확인
                if check_cancelled and check_cancelled():
                    print("[Info Bridge] 해양생물 검증 취소 요청 받음 - 반복 중단")
                    break
                
                # 진행률 업데이트
                if update_progress:
                    progress = (i + 1) / len(verification_list_input)
                    print(f"[Debug Bridge Progress] 해양생물 진행률 계산: {progress:.2f}, 현재 항목: {i+1}, 전체 항목 수: {len(verification_list_input)}")
                    # 현재 항목과 전체 항목 수도 함께 전달
                    update_progress(progress, i+1, len(verification_list_input))
                
                # 상태 메시지 업데이트
                if update_status:
                    item_name = item[0] if isinstance(item, tuple) else item
                    update_status(f"해양생물 검증 중: {item_name} ({i+1}/{len(verification_list_input)}) - 전체 {len(verification_list_input)}개 중 {i+1}번째")
                
                # 단일 항목 검증 실행
                try:
                    # 하나의 항목만 전달하여 검증
                    single_item = [item]
                    single_result = verifier.perform_verification(single_item)
                    if single_result and len(single_result) > 0:
                        # 결과가 있는 경우 추가
                        results.extend(single_result)
                except Exception as item_e:
                    print(f"[Error Bridge] 항목 '{item}' 검증 중 오류: {item_e}")
            
            # 결과 확인
            print(f"[Debug Bridge] 검증 결과 수: {len(results) if results else 0}")
            return results
        except Exception as e:
            print(f"[Error] Core module verification failed, falling back to original: {e}")
            return original_perform_verification(verification_list_input, update_progress, update_status, check_cancelled)
    else:
        print("[Bridge] Falling back to original_perform_verification")
        return original_perform_verification(verification_list_input, update_progress, update_status, check_cancelled)


def perform_microbe_verification(
    microbe_names_list: List[str],
    update_progress: Callable[[float], None] = None,
    update_status: Callable[[str], None] = None,
    result_callback: Callable[[Dict[str, Any]], None] = None,
    context: Union[List[str], str, None] = None,
    check_cancelled: Callable[[], bool] = None
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
            print(f"[Bridge] Calling MicrobeVerifier.perform_microbe_verification for {len(microbe_names_list)} items...")
            
            # 검증 전 입력 학명 수 출력
            print(f"[Debug Bridge] 검증할 미생물 학명 수: {len(microbe_names_list)}")
            if microbe_names_list and len(microbe_names_list) > 0:
                print(f"[Debug Bridge] 검증할 미생물 학명 샘플: {microbe_names_list[:min(5, len(microbe_names_list))]}")
            
            # 취소 확인 함수가 있는 경우 전달
            if check_cancelled:
                # 취소 확인 함수를 전달하는 경우
                print("[Debug Bridge] 취소 확인 함수 전달 준비 완료")
                # 취소 여부 확인 래퍼 함수 정의
                original_perform = verifier.perform_microbe_verification
                
                def perform_with_cancel_check(*args, **kwargs):
                    # 각 학명에 대한 검증 전 취소 여부 확인
                    if check_cancelled and check_cancelled():
                        print("[Info Bridge] 검증 취소 요청 받음")
                        return []
                    return original_perform(*args, **kwargs)
                
                # 원래 함수 대체
                verifier.perform_microbe_verification = perform_with_cancel_check
            
            # MicrobeVerifier의 메서드 호출 시 context 전달
            results = []
            # 각 항목을 개별적으로 처리하여 취소 가능하게 함
            for i, name in enumerate(microbe_names_list):
                # 취소 여부 확인
                if check_cancelled and check_cancelled():
                    print("[Info Bridge] 검증 취소 요청 받음 - 반복 중단")
                    break
                
                # 진행률 업데이트
                if update_progress:
                    progress = (i + 1) / len(microbe_names_list)
                    print(f"[Debug Bridge Progress] 미생물 진행률 계산: {progress:.2f}, 현재 항목: {i+1}, 전체 항목 수: {len(microbe_names_list)}")
                    # 현재 항목과 전체 항목 수도 함께 전달
                    update_progress(progress, i+1, len(microbe_names_list))
                
                # 상태 메시지 업데이트
                if update_status:
                    update_status(f"미생물 검증 중: {name} ({i+1}/{len(microbe_names_list)}) - 전체 {len(microbe_names_list)}개 중 {i+1}번째")
                
                # 단일 항목 검증 실행
                try:
                    single_result = verifier.perform_microbe_verification([name], context=context)
                    if single_result and len(single_result) > 0:
                        # 결과가 있는 경우 추가
                        results.extend(single_result)
                        # 콜백 함수 호출
                        if result_callback and single_result[0]:
                            result_callback(single_result[0], "microbe")
                except Exception as item_e:
                    print(f"[Error Bridge] 항목 '{name}' 검증 중 오류: {item_e}")
            
            # 결과 확인
            print(f"[Debug Bridge] 검증 결과 수: {len(results) if results else 0}")
            return results
        except Exception as e:
            print(f"[Error] Core module microbe verification failed, falling back to original: {e}")
            # 오류 발생 시 원래 함수로 폴백
            print(f"[Debug Bridge] 원래 함수로 폴백 시도, 학명 수: {len(microbe_names_list)}")
            return original_perform_microbe_verification(microbe_names_list, update_progress, update_status, result_callback, check_cancelled)
    else:
        print("[Bridge] Falling back to original_perform_microbe_verification")
        print(f"[Debug Bridge] 원래 함수로 폴백, 학명 수: {len(microbe_names_list)}")
        return original_perform_microbe_verification(microbe_names_list, update_progress, update_status, result_callback, check_cancelled)


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
    
    print(f"[Info Bridge] 미생물 파일 '{file_path}' 처리 시작.")
    
    def extract_names_from_dataframe(df, has_header=False):
        """데이터프레임에서 이름 추출"""
        names = []
        header_keywords = ['scientific_name', 'scientificname', 'scientific name', 'name', '학명', 'species', 'microbe', 'bacteria']
        
        if has_header:
            # 헤더가 있는 경우
            for col in df.columns:
                if any(keyword in str(col).lower() for keyword in header_keywords):
                    print(f"[Info Bridge] 대상 컬럼 발견: {col}")
                    names.extend(df[col].dropna().astype(str).tolist())
                    break
            else:
                # 헤더는 있지만 키워드가 없는 경우 첫 번째 컬럼 사용
                if len(df.columns) > 0:
                    names.extend(df.iloc[:, 0].dropna().astype(str).tolist())
        else:
            # 헤더가 없는 경우
            if len(df.columns) > 0:
                names.extend(df.iloc[:, 0].dropna().astype(str).tolist())
        
        return names
    
    # 파일 확장자에 따라 다른 처리
    if file_ext == '.csv':
        # UTF-8 인코딩으로 시도
        for encoding in ['utf-8', 'cp949', 'euc-kr']:
            try:
                # 파일 전체를 읽어서 처리
                df = pd.read_csv(file_path, encoding=encoding, dtype=str, keep_default_na=False, low_memory=False)
                
                # 헤더 확인
                header_keywords = ['scientific_name', 'scientificname', 'scientific name', 'name', '학명', 'species', 'microbe', 'bacteria']
                has_header = any(any(keyword in str(col).lower() for keyword in header_keywords) for col in df.columns)
                
                if has_header:
                    print(f"[Info Bridge] CSV 파일에 헤더가 있습니다. ({encoding} 인코딩)")
                    microbe_names = extract_names_from_dataframe(df, has_header=True)
                else:
                    print(f"[Info Bridge] CSV 파일에 헤더가 없습니다. ({encoding} 인코딩)")
                    microbe_names = extract_names_from_dataframe(df, has_header=False)
                
                # 데이터가 제대로 읽혔으면 루프 종료
                if len(microbe_names) > 0:
                    break
                    
            except UnicodeDecodeError:
                print(f"[Info Bridge] {encoding} 인코딩 실패, 다음 인코딩 시도...")
                continue
            except Exception as e:
                print(f"[Error Bridge] CSV 파일 처리 중 오류 ({encoding}): {e}")
                continue
                
        if not microbe_names:
            print("[Warning Bridge] 모든 인코딩 시도 실패. 첫 번째 컬럼으로 시도합니다.")
            try:
                df = pd.read_csv(file_path, header=None, dtype=str, keep_default_na=False, low_memory=False)
                microbe_names = df[0].dropna().astype(str).tolist()
            except Exception as e:
                print(f"[Error Bridge] CSV 파일 처리 최종 실패: {e}")
                return []
    
    # Excel 파일 처리
    elif file_ext in ['.xlsx', '.xls']:
        try:
            # 첫 번째 시트 읽기
            xls = pd.ExcelFile(file_path)
            sheet_name = xls.sheet_names[0]  # 첫 번째 시트 사용
            df = pd.read_excel(file_path, sheet_name=sheet_name, dtype=str, keep_default_na=False)
            print(f"[Debug Bridge] DataFrame 로드 성공. 컬럼: {list(df.columns)}")
            print(f"[Debug Bridge] DataFrame 행 수: {len(df)}")
            
            # 헤더 확인
            header_keywords = ['scientific_name', 'scientificname', 'scientific name', 'name', '학명', 'species', 'microbe', 'bacteria']
            has_header = any(any(keyword in str(col).lower() for keyword in header_keywords) for col in df.columns)
            
            if has_header:
                print("[Info Bridge] Excel 파일에 헤더가 있습니다.")
                microbe_names = extract_names_from_dataframe(df, has_header=True)
            else:
                print("[Info Bridge] Excel 파일에 헤더가 없습니다.")
                microbe_names = extract_names_from_dataframe(df, has_header=False)
                
            # 첫 번째 열만 사용해보기 (데이터가 없을 경우)
            if not microbe_names and len(df.columns) > 0:
                print("[Info Bridge] 첫 번째 열만 사용하여 시도합니다.")
                # 첫 번째 열의 모든 행을 가져옴
                microbe_names = df.iloc[:, 0].dropna().astype(str).tolist()
                
        except Exception as e:
            print(f"[Error Bridge] Excel 파일 처리 중 오류: {e}")
            return []
    
    # 텍스트 파일 처리
    elif file_ext in ['.txt', '.tsv']:
        try:
            # 인코딩 시도 (UTF-8, CP949, EUC-KR 순서로 시도)
            encodings = ['utf-8', 'cp949', 'euc-kr']
            lines = []
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        lines = [line.strip() for line in f.readlines() if line.strip()]
                    print(f"[Info Bridge] {encoding} 인코딩으로 파일을 성공적으로 읽었습니다.")
                    break
                except UnicodeDecodeError:
                    print(f"[Info Bridge] {encoding} 인코딩 실패, 다음 인코딩 시도...")
                    continue
            
            if not lines:
                print("[Warning Bridge] 파일을 읽을 수 없거나 비어 있습니다.")
                return []
            
            # 헤더 확인 (첫 줄이 헤더 키워드를 포함하는지 확인)
            header_keywords = ['scientific_name', 'scientificname', 'scientific name', 'name', '학명', 'species', 'microbe', 'bacteria']
            has_header = any(keyword in lines[0].lower() for keyword in header_keywords)
            
            if has_header:
                print("[Info Bridge] 텍스트 파일에 헤더가 있습니다. 첫 줄을 제외합니다.")
                microbe_names = lines[1:]
            else:
                print("[Info Bridge] 텍스트 파일에 헤더가 없습니다. 모든 줄을 처리합니다.")
                microbe_names = lines
                
        except Exception as e:
            print(f"[Error Bridge] 텍스트 파일 처리 중 오류: {e}")
            return []
    
    # 결과 후처리
    try:
        # 빈 문자열 제거 및 중복 제거
        microbe_names = [name for name in microbe_names if name and str(name).strip()]
        microbe_names = list(dict.fromkeys(microbe_names))  # 순서 유지하며 중복 제거
        
        print(f"[Info Bridge] 최종 추출된 미생물 학명 수: {len(microbe_names)}")
        if microbe_names:
            print(f"[Info Bridge] 미생물 학명 샘플: {microbe_names[:min(5, len(microbe_names))]}")
        
        return microbe_names
        
    except Exception as e:
        print(f"[Error Bridge] 결과 처리 중 오류: {e}")
        return []
    
    # 처리할 수 없는 파일 형식인 경우
    else:
        print(f"[Error Bridge] 지원하지 않는 파일 형식: {file_ext}")
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