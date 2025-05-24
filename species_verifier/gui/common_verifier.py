"""
공통 검증 모듈 - 모든 검증 시스템(WoRMS, LPSN, COL)에서 사용하는 통합 검증 로직
"""
from typing import List, Dict, Any, Callable, Union, Tuple, Optional
import time
import traceback

def perform_common_verification(
    items_list: List[Any],
    verification_function: Callable[[Any], Dict[str, Any]],
    update_progress: Optional[Callable[[float, int, int], None]] = None,
    update_status: Optional[Callable[[str], None]] = None,
    result_callback: Optional[Callable[[Dict[str, Any], str], None]] = None,
    check_cancelled: Optional[Callable[[], bool]] = None,
    verification_type: str = "species",
    preprocess_item: Optional[Callable[[Any], Any]] = None
) -> List[Dict[str, Any]]:
    """
    모든 검증 시스템에서 사용하는 공통 검증 루프 함수
    
    Args:
        items_list: 검증할 항목 목록
        verification_function: 개별 항목을 검증하는 함수
        update_progress: 진행 상태 업데이트 콜백
        update_status: 상태 메시지 업데이트 콜백
        result_callback: 개별 결과 업데이트 콜백
        check_cancelled: 취소 여부 확인 함수
        verification_type: 검증 유형 (marine, microbe, col)
        preprocess_item: 항목 전처리 함수 (선택 사항)
        
    Returns:
        검증 결과 목록
    """
    results = []
    total_items = len(items_list)
    current_item = 0
    
    # 진행 상황 추적을 위한 변수
    start_time_total = time.time()
    
    # 디버그 로그
    print(f"[Info Common] {verification_type} 검증 시작: 총 {total_items}개 항목")
    if items_list and len(items_list) > 0:
        sample_items = items_list[:min(5, len(items_list))]
        print(f"[Debug Common] {verification_type} 검증 샘플 항목: {sample_items}")
    
    # 진행 상태 초기화 - 중요: total_items 값을 명시적으로 전달
    if update_progress:
        update_progress(0.0, 0, total_items)
    if update_status:
        update_status(f"{verification_type} 검증 시작 (총 {total_items}개)")
    
    # 각 항목 처리
    for idx, item in enumerate(items_list):
        # 취소 여부 확인 - 각 항목 처리 전
        try:
            if check_cancelled and check_cancelled():
                print(f"[Info Common] 취소 요청 받음 - {verification_type} 항목 {idx}/{total_items} 처리 전 중단")
                break
        except Exception as e:
            print(f"[Error Common] 취소 확인 중 오류: {e}")
        
        # 현재 항목 번호 업데이트
        current_item = idx + 1
        
        # 진행률 업데이트 - 중요: current_item과 total_items 값을 명시적으로 전달
        if update_progress:
            update_progress(idx / total_items, current_item, total_items)
        
        # 항목 전처리 (필요한 경우)
        processed_item = item
        if preprocess_item:
            try:
                processed_item = preprocess_item(item)
            except Exception as e:
                print(f"[Error Common] 항목 전처리 중 오류: {e}")
        
        # 현재 처리 중인 항목 정보 표시
        item_display = str(processed_item)[:30]
        if update_status:
            update_status(f"'{item_display}...' 검증 중... ({current_item}/{total_items})")
        
        # 개별 검증 수행
        try:
            start_time = time.time()
            result = verification_function(processed_item)
            duration = time.time() - start_time
            
            # 결과 로깅
            print(f"[Debug Common] {verification_type} 항목 {current_item}/{total_items} '{item_display}' 완료: 소요시간 {duration:.2f}초")
            
            # 결과 저장
            results.append(result)
            
            # 결과 콜백 호출
            if result_callback:
                result_callback(result, verification_type)
        except Exception as e:
            print(f"[Error Common] '{item_display}' 검증 중 오류 발생: {e}")
            traceback.print_exc()
        
        # 취소 여부 다시 확인 - 각 항목 처리 후
        try:
            if check_cancelled and check_cancelled():
                print(f"[Info Common] 취소 요청 받음 - {verification_type} 항목 {current_item}/{total_items} 처리 후 중단")
                break
        except Exception as e:
            print(f"[Error Common] 취소 확인 중 오류: {e}")
    
    # 총 소요 시간 계산
    total_duration = time.time() - start_time_total
    
    # 최종 진행률 업데이트 - 중요: 완료된 current_item과 total_items 값을 명시적으로 전달
    if update_progress:
        update_progress(1.0, current_item, total_items)
    if update_status:
        update_status(f"검증 완료: {current_item}/{total_items} 항목 처리됨")
    
    print(f"[Info Common] {verification_type} 검증 완료: {current_item}/{total_items} 항목 처리됨 (총 소요시간: {total_duration:.2f}초)")
    return results
