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
            # 취소 여부 확인 - 디버그 로그 추가
            cancel_check_result = False
            try:
                if check_cancelled:
                    print(f"[Debug Cancel] 취소 확인 함수 호출: {type(check_cancelled).__name__}")
                    cancel_check_result = check_cancelled()
                    print(f"[Debug Cancel] 취소 확인 결과: {cancel_check_result}")
            except Exception as e:
                print(f"[Error Cancel] 취소 확인 중 오류: {e}")
            
            if cancel_check_result:
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

# --- 기본 경로 가져오기 함수 ---

def get_base_path():
    """ 실행 파일의 기본 경로를 반환합니다 (개발 환경과 .exe 환경 모두 지원). """
    if getattr(sys, 'frozen', False):
        # .exe로 실행될 때
        return Path(sys.executable).parent
    else:
        # 스크립트로 실행될 때 (.py)
        # bridge.py는 gui 폴더 안에 있으므로, 프로젝트 루트는 두 단계 위입니다.
        return Path(__file__).resolve().parent.parent.parent

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
    update_progress: Callable[[float, Optional[int], Optional[int]], None] = None,
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
    # 로그 출력 향상: 항목 수 및 첫 번째 항목 정보 출력
    print(f"[Debug Bridge perform_verification] 전체 항목 수: {len(verification_list_input)}")
    if verification_list_input and len(verification_list_input) > 0:
        sample_items = verification_list_input[:min(5, len(verification_list_input))]
        print(f"[Debug Bridge perform_verification] 샘플 항목: {sample_items}")
    
    # API 지연 시간 확인 및 조정
    from species_verifier.core.worms_api import API_DELAY
    print(f"[Debug Bridge] 현재 API 지연 시간: {API_DELAY}초")
    
    # 수정: 클래스 존재 여부 확인
    if HAS_CORE_MODULES and MarineSpeciesVerifier:
        adapted_msv_callback = None
        if result_callback:
            # MarineSpeciesVerifier의 콜백은 인자 두 개(결과 딕셔너리, 탭 타입)를 전달하므로,
            # 해당 탭 타입을 함께 전달하는 어댑터 생성
            adapted_msv_callback = lambda r_dict, t="marine": result_callback(r_dict, t)

        try:
            # 수정: Verifier 인스턴스 생성 및 어댑터 콜백 전달
            verifier = MarineSpeciesVerifier(
                progress_callback=update_progress, 
                status_update_callback=update_status,
                result_callback=adapted_msv_callback,
                check_cancelled=check_cancelled
            )
            print(f"[Bridge] Calling MarineSpeciesVerifier.perform_verification for {len(verification_list_input)} items...")
            
            # 검증 전 입력 학명 수 출력
            print(f"[Debug Bridge] 검증할 해양생물 학명 수: {len(verification_list_input)}")
            if verification_list_input and len(verification_list_input) > 0:
                print(f"[Debug Bridge] 검증할 해양생물 학명 샘플: {verification_list_input[:min(5, len(verification_list_input))]}")
            
            # 모든 항목을 일괄 처리하도록 수정
            print(f"[Info Bridge] 전체 {len(verification_list_input)}개 항목 검증을 일괄 처리합니다")
            
            # 10개 제한 문제 디버깅: 입력 목록의 전체 길이를 재확인
            print(f"[Debug Bridge] 검증 직전 확인 - 입력 목록 길이: {len(verification_list_input)}")
            
            # API 지연 시간 조정 시도 (필요한 경우)
            if len(verification_list_input) > 20:
                print(f"[Debug Bridge] 많은 항목({len(verification_list_input)}개)이 감지되어 API 지연 시간을 0.2초로 조정합니다")
                import species_verifier.core.worms_api as worms_api
                worms_api.API_DELAY = 0.2
            
            try:
                # 모든 항목을 한 번에 검증
                results = verifier.perform_verification(verification_list_input)
                print(f"[Info Bridge] 검증 완료: 총 {len(results)}개 결과 반환됨")
                
                # 진행률 100%로 설정
                if update_progress:
                    update_progress(1.0, len(verification_list_input), len(verification_list_input))
                
                # 상태 메시지 업데이트
                if update_status:
                    update_status(f"해양생물 검증 완료: 전체 {len(verification_list_input)}개 항목 처리됨")
                    
            except Exception as batch_e:
                print(f"[Error Bridge] 일괄 검증 중 오류 발생: {batch_e}")
                
                # 오류 발생 시 원래 방식(개별 처리)으로 폴백
                print("[Info Bridge] 개별 처리 방식으로 폴백합니다")
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
            
            # 원본 함수에 맞게 어댑터 함수 생성
            def check_cancelled_adapter(*args):
                # 이 함수가 호출되었는지 확인하는 로그 추가
                print(f"[Debug Cancel] try-except 내 check_cancelled_adapter 호출됨, 인자: {args}")
                
                # 원본 check_cancelled 함수 호출 결과 확인
                is_cancelled = check_cancelled() if check_cancelled else False
                print(f"[Debug Cancel] try-except 내 취소 여부 확인 결과: {is_cancelled}")
                
                return is_cancelled
                
            print("[Warning] Using original_perform_verification function with " + str(len(verification_list_input)) + " items")
            return original_perform_verification(verification_list_input, update_progress, update_status, result_callback, check_cancelled_adapter)
    else:
        print("[Bridge] Falling back to original_perform_verification")
        
        # 원본 함수에 맞게 어댑터 함수 생성
        def check_cancelled_adapter(*args):
            # 이 함수가 호출되었는지 확인하는 로그 추가
            print(f"[Debug Cancel] check_cancelled_adapter 호출됨, 인자: {args}")
            
            # 원본 check_cancelled 함수 호출 결과 확인
            is_cancelled = check_cancelled() if check_cancelled else False
            print(f"[Debug Cancel] 취소 여부 확인 결과: {is_cancelled}")
            
            return is_cancelled
            
        print("[Warning] Using original_perform_verification function with " + str(len(verification_list_input)) + " items")
        return original_perform_verification(verification_list_input, update_progress, update_status, result_callback, check_cancelled_adapter)


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
            # 결과 콜백 함수를 래핑하여 탭 타입 정보 추가
            def wrapped_result_callback(result, *args):
                # 로그 추가
                print(f"[Debug Bridge] wrapped_result_callback 호출됨: 결과 키={list(result.keys()) if isinstance(result, dict) else 'None'}, 추가 인자={args}")
                if result_callback:
                    # 결과와 함께 'microbe' 탭 타입 전달 (미생물 결과는 미생물 탭에 표시)
                    result_callback(result, 'microbe')
                    
            verifier = MicrobeVerifier(
                progress_callback=update_progress,
                status_update_callback=update_status,
                result_callback=wrapped_result_callback
            )
            print(f"[Bridge] Calling MicrobeVerifier.perform_microbe_verification for {len(microbe_names_list)} items...")
            
            # 검증 전 입력 학명 수 출력
            print(f"[Info] 검증할 미생물 학명 수: {len(microbe_names_list)} (전체 항목 처리 예정)")
            if microbe_names_list and len(microbe_names_list) > 0 and len(microbe_names_list) < 10:
                print(f"[Info] 검증할 미생물 학명 샘플: {microbe_names_list}")
            elif microbe_names_list and len(microbe_names_list) >= 10:
                print(f"[Info] 검증할 미생물 학명 샘플: {microbe_names_list[:5]} ... 외 {len(microbe_names_list)-5}개")
            
            # 취소 확인 함수가 있는 경우 전달
            if check_cancelled:
                # 취소 확인 함수를 전달하는 경우
                print("[Debug Bridge] 취소 확인 함수 전달 준비 완료")
                # 이제 perform_microbe_verification 메서드에 직접 check_cancelled 함수를 전달합니다.
                # 래퍼 함수를 사용하지 않고 직접 전달하는 방식으로 변경합니다.
            
            # MicrobeVerifier의 메서드 호출 시 context 전달
            results = []
            # 취소 여부 확인 - 여기서 한 번 확인하고 나머지는 MicrobeVerifier 클래스에서 처리
            if check_cancelled and check_cancelled():
                print("[Info Bridge] 검증 취소 요청 받음 - 처리 시작 전 중단")
                return []
                
            # 취소 시 빠르게 처리하기 위해 배치 처리 방식 도입
            # 취소되지 않은 경우 모든 항목을 한 번에 처리
            try:
                # 상태 메시지 업데이트
                if update_status:
                    update_status(f"미생물 검증 중: 전체 {len(microbe_names_list)}개 항목 처리 중...")
                
                # 진행률 초기 업데이트
                if update_progress:
                    update_progress(0.1, 1, len(microbe_names_list))
                
                # 취소 여부 한 번 더 확인
                if check_cancelled and check_cancelled():
                    print("[Info Bridge] 검증 취소 요청 받음 - 검증 함수 호출 전 중단")
                    return []
                
                # 모든 항목을 한 번에 처리 (취소 확인 함수도 전달)
                batch_results = verifier.perform_microbe_verification(microbe_names_list, context=context, check_cancelled=check_cancelled)
                
                # 취소 여부 확인
                if check_cancelled and check_cancelled():
                    print("[Info Bridge] 검증 취소 요청 받음 - 결과 처리 전 중단")
                    return []
                
                # 진행률 업데이트 (80% 완료)
                if update_progress:
                    update_progress(0.8, int(len(microbe_names_list) * 0.8), len(microbe_names_list))
                
                # 결과 처리
                if batch_results:
                    print(f"[Info Bridge] 배치 결과 개수: {len(batch_results)} / 전체 학명 수: {len(microbe_names_list)}")
                    results.extend(batch_results)
                    
                    # 참고: 결과 콜백은 microbe_verifier.py에서 이미 처리되었으므로 여기서는 처리하지 않음
                
                # 진행률 최종 업데이트 (취소되지 않은 경우에만)
                if update_progress and not (check_cancelled and check_cancelled()):
                    update_progress(1.0, len(microbe_names_list), len(microbe_names_list))
                    
            except Exception as batch_e:
                print(f"[Error Bridge] 미생물 일괄 검증 중 오류: {batch_e}")
            
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


def process_file(file_path, korean_mode=False):
    """파일에서 학명 또는 한글명-학명 쌍을 추출합니다.
    
    Args:
        file_path (str): 처리할 파일 경로
        korean_mode (bool): 한글명 모드 여부 (True=한글명 있음, False=학명만)

    Returns:
        List[str] 또는 List[Tuple[str, str]]: 추출된 학명 목록 또는 (한글명, 학명) 튜플 목록
    """
    print(f"[Info] 파일 '{file_path}' 처리 시작.")

    results = []
    file_extension = os.path.splitext(file_path)[1].lower()

    # 파일 확장자별 처리
    try:
        if file_extension in ['.xlsx', '.xls']:
            # 엑셀 파일 처리
            try:
                # 현재 처리 로직에서는 데이터 일관성을 위해 모든 파일을 헤더 없이 읽도록 수정
                # 기본적으로 header=None으로 설정하여 첫 번째 행부터 데이터로 처리
                print(f"[Info Bridge] 모든 파일을 헤더 없이 처리합니다.")
                
                # Excel 파일인 경우
                if file_extension in ['.xlsx', '.xls']:
                    try:
                        # 모든 파일을 header=None으로 읽어서 첫 번째 행도 데이터로 처리
                        df = pd.read_excel(file_path, header=None)
                        print(f"[Debug Bridge] 파일을 header=None으로 로드함. 콜럼: {list(df.columns)}")
                        print(f"[Debug Bridge] DataFrame 행 수: {len(df)}")
                        has_header = False  # 헤더가 없는 것으로 처리
                        print(f"[Info Bridge] Excel 파일은 헤더 없이 처리합니다.")
                    except Exception as e:
                        print(f"[Error Bridge] 엑셀 파일 처리 중 오류: {e}")
                        # 헤더 없이 다시 시도
                        try:
                            print(f"[Info Bridge] 헤더 없이 다시 시도합니다.")
                            df = pd.read_excel(file_path, header=None)
                            print(f"[Debug Bridge] 헤더 없이 DataFrame 행 수: {len(df)}")
                            has_header = False  # 헤더가 없는 것으로 처리
                            print(f"[Info Bridge] Excel 파일은 헤더 없이 처리합니다.")
                        except Exception as inner_e:
                            print(f"[Error Bridge] 헤더 없이 시도 중 오류: {inner_e}")
                            raise RuntimeError(f"엑셀 파일 '{file_path}' 처리 실패")
                
                # 한글명 모드 처리
                if korean_mode and len(df.columns) >= 2:
                    korean_col = df.columns[0]
                    sci_col = df.columns[1]
                    
                    # 한글명-학명 쌍으로 결과 생성
                    for idx, row in df.iterrows():
                        korean_name = str(row[korean_col]).strip()
                        scientific_name = str(row[sci_col]).strip()
                        
                        # 빈 값이 아닐 경우에만 추가
                        if korean_name and scientific_name and korean_name.lower() not in ['nan', 'none', ''] and scientific_name.lower() not in ['nan', 'none', '']:
                            results.append((korean_name, scientific_name))
                else:
                    # 학명만 추출
                    print(f"[Info Bridge] 학명 모드로 처리합니다. 전체 {len(df)} 행의 데이터를 처리합니다.")
                    
                    # 첫 번째 콜럼 정보 확인
                    first_col = df.columns[0]
                    if len(df) > 0:
                        sample_items = df[first_col].head(5).tolist()
                        print(f"[Debug Bridge] 첫 번째 콜럼의 처음 5개 항목: {sample_items}")
                    
                    # 미생물.xlsx 파일 특별 처리
                    file_basename = os.path.basename(file_path).lower()
                    is_microbe_file = '미생물' in file_basename
                    is_marine_file = ('gadus morhua' in str(first_col).lower() or '해양생물' in file_basename)
                    
                    # 미생물 파일인 경우 특별 처리
                    if is_microbe_file:
                        print(f"[Info Bridge] 미생물 파일 '{file_path}' 처리 시작.")
                        print(f"[Info Bridge] 미생물.xlsx 파일 형식 감지, 특별 처리 적용")
                        
                        # 콜럼 이름을 포함하여 모든 항목 추출
                        all_species = []
                        
                        # 첫 번째 콜럼 이름 처리
                        first_col = df.columns[0]  # 첫 번째 콜럼 이름 가져오기
                        first_col_name = str(first_col).strip()
                        
                        # 콜럼 이름이 미생물 학명인지 확인
                        if first_col_name and ' ' in first_col_name and len(first_col_name) > 3 and first_col_name.lower() not in ['nan', 'none', '']:
                            # 첫 번째 항목으로 콜럼 이름 추가 (예: Escherichia coli)
                            all_species.append(first_col_name)
                            print(f"[Debug Bridge] 콜럼 이름 추가: {first_col_name}")
                        
                        # 첫 번째 콜럼의 모든 행 처리
                        for idx, row in df.iterrows():
                            try:
                                value = str(row[first_col]).strip()
                                if value and value.lower() not in ['nan', 'none', ''] and ' ' in value and len(value) > 3:
                                    # 중복 방지
                                    if value not in all_species:
                                        all_species.append(value)
                                        print(f"[Debug Bridge] 항목 추가: {value}")
                            except Exception as e:
                                print(f"[Debug Bridge] 항목 추출 중 오류: {e}")
                                continue
                        
                        print(f"[Debug Bridge] 추출된 전체 미생물 수: {len(all_species)}")
                        
                        # 결과에 추가 - 모든 항목 유지
                        results = all_species
                        print(f"[Debug Bridge] 최종 추출된 미생물 학명 수: {len(results)}")
                        print(f"[Debug Bridge] 추출된 학명 목록: {results}")
                    
                    # 해양생물 파일인 경우 특별 처리
                    elif is_marine_file:
                        print(f"[Info Bridge] 해양생물.xlsx 파일 형식 감지, 특별 처리 적용")
                        
                        # 수정: 'Gadus morhua'를 헤더가 아닌 첫 번째 데이터로 처리
                        print(f"[Info Bridge] 헤더로 인식되던 'Gadus morhua'를 데이터로 처리합니다.")
                        
                        # 첫 번째 행을 포함하여 모든 항목 추출
                        all_species = []
                        
                        # 콜럼 이름이 존재하는 경우 먼저 추가
                        if 'gadus morhua' in str(first_col).lower():
                            # 헤더에 학명이 있는 경우 첫 번째 항목으로 추가
                            first_col_name = str(first_col).strip()
                            if first_col_name and ' ' in first_col_name and len(first_col_name) > 3:
                                all_species.append(first_col_name)
                                print(f"[Debug Bridge] 콜럼 이름을 첫 번째 항목으로 추가: {first_col_name}")
                        
                        # 나머지 데이터 처리
                        for idx, row in df.iterrows():
                            try:
                                value = str(row[first_col]).strip()
                                if value and value.lower() not in ['nan', 'none', ''] and ' ' in value and len(value) > 3:
                                    all_species.append(value)
                            except Exception as e:
                                print(f"[Debug Bridge] 항목 추출 중 오류: {e}")
                                continue
                        
                        print(f"[Debug Bridge] 추출된 전체 종 수: {len(all_species)}")
                        
                        # 결과에 추가 - 모든 항목 유지
                        results = []  # 기존 결과 초기화
                        for species in all_species:
                            results.append(species)
                        
                        print(f"[Debug Bridge] 최종 추출된 종 수: {len(results)}")
                    else:
                        # 일반적인 처리: 모든 컬럼에서 유효한 학명 찾기
                        for col in df.columns:
                            for idx, row in df.iterrows():
                                try:
                                    value = str(row[col]).strip()
                                    # 빈 값이 아니고 유효한 학명 형태인 경우만 추가
                                    if value and value.lower() not in ['nan', 'none', ''] and ' ' in value and len(value) > 3:
                                        # 중복 방지
                                        if value not in results:
                                            results.append(value)
                                except Exception as val_e:
                                    print(f"[Debug Bridge] 값 처리 중 무시된 오류: {val_e}")
                                    continue
            except Exception as e:
                print(f"[Error Bridge] 엑셀 파일 처리 중 오류: {e}")
                # 헤더 없이 다시 시도
                try:
                    print(f"[Info Bridge] 헤더 없이 다시 시도합니다.")
                    df = pd.read_excel(file_path, header=None)
                    print(f"[Debug Bridge] 헤더 없이 DataFrame 행 수: {len(df)}")
                    
                    if korean_mode and df.shape[1] >= 2:
                        for idx, row in df.iterrows():
                            korean_name = str(row[0]).strip()
                            scientific_name = str(row[1]).strip()
                            if korean_name and scientific_name and korean_name.lower() not in ['nan', 'none', ''] and scientific_name.lower() not in ['nan', 'none', '']:
                                results.append((korean_name, scientific_name))
                    else:
                        # 모든 컬럼에서 유효한 학명 찾기
                        for col in range(df.shape[1]):
                            for idx, row in df.iterrows():
                                try:
                                    value = str(row[col]).strip()
                                    # 빈 값이 아니고 유효한 학명 형태인 경우만 추가
                                    if value and value.lower() not in ['nan', 'none', ''] and ' ' in value and len(value) > 3:
                                        # 중복 방지
                                        if value not in results:
                                            results.append(value)
                                except Exception as val_e:
                                    continue
                except Exception as inner_e:
                    print(f"[Error Bridge] 헤더 없이 시도 중 오류: {inner_e}")
                    raise RuntimeError(f"엑셀 파일 '{file_path}' 처리 실패")
        
        elif file_extension == '.csv':
            # CSV 파일 처리
            try:
                # 헤더가 있는지 확인
                df_sample = pd.read_csv(file_path, nrows=5, encoding='utf-8')
                
                # CSV 파일인 경우: header=None으로 설정하여 첫 번째 행도 데이터로 처리
                df = pd.read_csv(file_path, header=None)
                print(f"[Debug Bridge] CSV 파일을 header=None으로 로드함. 열 목록: {list(df.columns)}")
                has_header = False  # 헤더가 없는 것으로 처리
                
                # 한글명 모드 처리
                if korean_mode and len(df.columns) >= 2:
                    korean_col = df.columns[0]
                    sci_col = df.columns[1]
                    
                    # 한글명-학명 쌍으로 결과 생성
                    for idx, row in df.iterrows():
                        korean_name = str(row[korean_col]).strip()
                        scientific_name = str(row[sci_col]).strip()
                        
                        # 빈 값이 아닐 경우에만 추가
                        if korean_name and scientific_name and korean_name.lower() not in ['nan', 'none', ''] and scientific_name.lower() not in ['nan', 'none', '']:
                            results.append((korean_name, scientific_name))
                else:
                    # 학명 모드 처리 - 모든 컬럼에서 유효한 학명 찾기
                    for col in df.columns:
                        for idx, row in df.iterrows():
                            try:
                                value = str(row[col]).strip()
                                # 빈 값이 아니고 유효한 학명 형태인 경우만 추가
                                if value and value.lower() not in ['nan', 'none', ''] and ' ' in value and len(value) > 3:
                                    # 중복 방지
                                    if value not in results:
                                        results.append(value)
                            except Exception as val_e:
                                continue
            except Exception as e:
                print(f"[Error Bridge] CSV 파일 처리 중 오류: {e}")
                # 헤더 없이 다시 시도
                try:
                    df = pd.read_csv(file_path, header=None, encoding='utf-8')
                    print(f"[Debug Bridge] 헤더 없이 CSV DataFrame 행 수: {len(df)}")
                    
                    if korean_mode and df.shape[1] >= 2:
                        for idx, row in df.iterrows():
                            korean_name = str(row[0]).strip()
                            scientific_name = str(row[1]).strip()
                            if korean_name and scientific_name and korean_name.lower() not in ['nan', 'none', ''] and scientific_name.lower() not in ['nan', 'none', '']:
                                results.append((korean_name, scientific_name))
                    else:
                        # 모든 컬럼에서 유효한 학명 찾기
                        for col in range(df.shape[1]):
                            for idx, row in df.iterrows():
                                try:
                                    value = str(row[col]).strip()
                                    # 빈 값이 아니고 유효한 학명 형태인 경우만 추가
                                    if value and value.lower() not in ['nan', 'none', ''] and ' ' in value and len(value) > 3:
                                        # 중복 방지
                                        if value not in results:
                                            results.append(value)
                                except Exception as val_e:
                                    continue
                except Exception as inner_e:
                    print(f"[Error Bridge] 헤더 없이 CSV 시도 중 오류: {inner_e}")
                    # UTF-8이 아닐 경우 CP949로 다시 시도
                    try:
                        df = pd.read_csv(file_path, header=None, encoding='cp949')
                        print(f"[Debug Bridge] CP949 인코딩 CSV DataFrame 행 수: {len(df)}")
                        
                        if korean_mode and df.shape[1] >= 2:
                            for idx, row in df.iterrows():
                                korean_name = str(row[0]).strip()
                                scientific_name = str(row[1]).strip()
                                if korean_name and scientific_name and korean_name.lower() not in ['nan', 'none', ''] and scientific_name.lower() not in ['nan', 'none', '']:
                                    results.append((korean_name, scientific_name))
                        else:
                            # 모든 컬럼에서 유효한 학명 찾기
                            for col in range(df.shape[1]):
                                for idx, row in df.iterrows():
                                    try:
                                        value = str(row[col]).strip()
                                        # 빈 값이 아니고 유효한 학명 형태인 경우만 추가
                                        if value and value.lower() not in ['nan', 'none', ''] and ' ' in value and len(value) > 3:
                                            # 중복 방지
                                            if value not in results:
                                                results.append(value)
                                    except Exception as val_e:
                                        continue
                    except Exception as cp_e:
                        print(f"[Error Bridge] CP949 인코딩으로 시도 중 오류: {cp_e}")
                        raise RuntimeError(f"CSV 파일 '{file_path}' 처리 실패")
        else:
            # 지원하지 않는 파일 형식
            raise ValueError(f"지원하지 않는 파일 형식: {file_extension}")
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
                    for item in df.iloc[:, 0].dropna().astype(str).tolist():
                        if item and item.lower() not in ['nan', 'none', ''] and ' ' in item and len(item) > 3:
                            if item not in results:
                                results.append(item)
                    
    except Exception as e:
        import traceback
        print(f"[Error Bridge] 파일 처리 중 예측 못한 오류 발생: {e}")
        print(traceback.format_exc())
        return []
    
    # 결과 요약 로그
    print(f"[Info Bridge] 최종 추출된 학명 수: {len(results)}")
    if results:
        print(f"[Info Bridge] 최종 학명 샘플: {results[:min(5, len(results))]}")
    
    return results


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
    file_basename = os.path.basename(file_path).lower()
    microbe_names = []
    
    print(f"[Info Bridge] 미생물 파일 '{file_path}' 처리 시작.")
    
    # 해양생물 파일 특별 처리 여부 확인
    is_marine_file = '해양생물' in file_basename
    
    def extract_names_from_dataframe(df, has_header=False):
        """데이터프레임에서 이름 추출"""
        names = []
        header_keywords = ['scientific_name', 'scientificname', 'scientific name', 'name', '학명', 'species', 'microbe', 'bacteria']
        
        # 해양생물 파일 특별 처리
        if is_marine_file:
            # 첫 번째 컬럼이 'Gadus morhua'인지 확인
            first_col = df.columns[0] if len(df.columns) > 0 else None
            if first_col and 'gadus morhua' in str(first_col).lower():
                # 헤더로 인식된 'Gadus morhua'를 첫 번째 항목으로 추가
                names.append(str(first_col))
                print(f"[Info Bridge] 헤더로 인식된 '{first_col}'를 첫 번째 항목으로 추가")
                
                # 첫 번째 컬럼의 모든 항목 추가
                for idx, row in df.iterrows():
                    try:
                        value = str(row[first_col]).strip()
                        if value and value.lower() not in ['nan', 'none', ''] and ' ' in value and len(value) > 3:
                            names.append(value)
                    except Exception as e:
                        print(f"[Debug Bridge] 항목 추출 중 오류: {e}")
                return names
        
        # 일반적인 처리
        if has_header:
            # 헤더가 있는 경우
            for col in df.columns:
                if any(keyword in str(col).lower() for keyword in header_keywords):
                    print(f"[Info Bridge] 대상 컬럼 발견: {col}")
                    names.extend([str(x).strip() for x in df[col].dropna().tolist() if str(x).strip() and ' ' in str(x)])
                    break
            else:
                # 헤더는 있지만 키워드가 없는 경우 첫 번째 컬럼 사용
                if len(df.columns) > 0:
                    names.extend([str(x).strip() for x in df.iloc[:, 0].dropna().tolist() if str(x).strip() and ' ' in str(x)])
        else:
            # 헤더가 없는 경우
            if len(df.columns) > 0:
                names.extend([str(x).strip() for x in df.iloc[:, 0].dropna().tolist() if str(x).strip() and ' ' in str(x)])
        
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
        # 빈 문자열 제거만 수행 (중복 제거 안함)
        microbe_names = [name for name in microbe_names if name and str(name).strip()]
        
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
    심층분석 결과 검색을 위한 브릿지 함수
    
    Args:
        search_term: 검색어
        
    Returns:
        심층분석 결과
    """
    if HAS_CORE_MODULES and get_wiki_summary:
        try:
            return get_wiki_summary(search_term)
        except Exception as e:
            print(f"[Error Bridge] Error in get_wiki_summary: {e}")
            # 오류 발생 시 원본 함수로 폴백
    
    # 코어 모듈이 없거나 오류 발생 시 원본 함수 사용
    return original_get_wiki_summary(search_term)


# process_col_file 함수는 더 이상 사용되지 않으므로 제거하였습니다.
# 통합된 process_file 함수로 대체되었습니다.

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