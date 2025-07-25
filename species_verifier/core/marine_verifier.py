"""
해양생물 검증 핵심 로직 모듈

이 모듈은 해양생물 학명 검증을 위한 핵심 로직을 담당합니다.
WoRMS API와 연동하여 학명 검증을 수행하고 위키백과에서 정보를 보강합니다.
"""
import time
import traceback
from typing import List, Dict, Tuple, Union, Optional, Any

from species_verifier.config import app_config, api_config
from species_verifier.core.wiki import get_wiki_summary
from species_verifier.core.worms_api import verify_species_list

class MarineSpeciesVerifier:
    """해양생물 학명 검증을 위한 클래스"""
    
    def __init__(self, progress_callback=None, status_update_callback=None, result_callback=None, check_cancelled=None):
        """
        초기화 함수
        
        Args:
            progress_callback: 진행률 업데이트 콜백 함수 (0.0~1.0 값 전달)
            status_update_callback: 상태 메시지 업데이트 콜백 함수 (문자열 메시지 전달)
            result_callback: 개별 결과 업데이트 콜백 함수 (결과 딕셔너리 전달)
            check_cancelled: 취소 여부 확인 콜백 함수 (불리언 값 반환)
        """
        """
        초기화 함수
        
        Args:
            progress_callback: 진행률 업데이트 콜백 함수 (0.0~1.0 값 전달)
            status_update_callback: 상태 메시지 업데이트 콜백 함수 (문자열 메시지 전달)
            result_callback: 개별 결과 업데이트 콜백 함수 (결과 딕셔너리 전달)
        """
        self.progress_callback = progress_callback
        self.status_update_callback = status_update_callback
        self.result_callback = result_callback
        self.check_cancelled = check_cancelled
    
    def update_progress(self, progress: float, current_item=None, total_items=None):
        """진행률 업데이트
        
        Args:
            progress: 진행률 (0.0~1.0 값)
            current_item: 현재 처리 중인 항목 번호
            total_items: 전체 항목 수
        """
        if self.progress_callback:
            # 모든 매개변수를 콜백에 전달
            if current_item is not None and total_items is not None:
                self.progress_callback(progress, current_item, total_items)
            else:
                self.progress_callback(progress)
    
    def update_status(self, message: str):
        """상태 메시지 업데이트"""
        if self.status_update_callback:
            self.status_update_callback(message)
            
    def create_basic_result(self, input_name: str, scientific_name: str, 
                          is_verified: bool, worms_status: str) -> Dict[str, Any]:
        """기본 결과 사전 생성
        
        Args:
            input_name: 입력된 이름 (한글명 또는 학명)
            scientific_name: 학명
            is_verified: 검증 성공 여부
            worms_status: WoRMS 검증 상태 메시지
            
        Returns:
            결과 정보가 담긴 사전
        """
        return {
            'input_name': input_name,
            'scientific_name': scientific_name if scientific_name else '-',
            'is_verified': is_verified,
            'worms_status': worms_status,
            'worms_id': '-',
            'worms_link': '-',
            'wiki_summary': '-',
            'mapped_name': scientific_name if scientific_name and scientific_name != '-' else '-'
        }
    
    def perform_verification(self, verification_list_input: List[Union[str, Tuple[str, str]]]) -> List[Dict[str, Any]]:
        """
        주어진 목록(학명 문자열 리스트 또는 (국명, 학명) 튜플 리스트)를 검증
        
        Args:
            verification_list_input: 검증할 목록 (문자열 리스트 또는 튜플 리스트)
            
        Returns:
            검증 결과 목록 (주의: 실시간 콜백으로 전달되므로 이 반환값은 덤 중요해짐)
        """
        error_occurred = False
        error_message_details = ""
        num_skipped_worms = 0
        results_list = []
        is_cancelled = False

        try:
            if verify_species_list is None:
                raise ImportError("Core verifier module not loaded.")

            # 진행 상태 초기화
            total_items = len(verification_list_input)
            if total_items == 0:
                return []
                
            self.update_status(f"총 {total_items}개 항목 처리 중...")
            self.update_progress(0, 0, total_items)
            print(f"[Debug] 검증 시작 - 전체 항목 수: {total_items}")

            # 학명 입력 처리
            for i, scientific_name in enumerate(verification_list_input):
                # 취소 여부 확인 (여러 번 확인)
                if self.check_cancelled and self.check_cancelled():
                    print(f"[Info] Marine verification cancelled by user after {i}/{total_items} items")
                    self.update_status(f"사용자 요청으로 취소됨: {i}/{total_items} 학명 처리 완료")
                    is_cancelled = True
                    break
                    
                # 현재 처리 중인 학명 표시
                if isinstance(scientific_name, tuple):
                    display_name = scientific_name[1] if scientific_name[1] else scientific_name[0]
                else:
                    display_name = scientific_name
                    
                self.update_status(f"'{display_name}' 처리 중 ({i+1}/{total_items})")
                
                # 진행률, 현재 항목, 전체 항목 수 함께 전달
                self.update_progress((i + 1) / total_items, i+1, total_items)
                
                print(f"[Info] Performing WoRMS verification for scientific name: '{display_name}'")
                
                result_entry = None  # 결과 초기화
                # 취소 여부 재확인 (중요한 작업 전에 다시 확인)
                if self.check_cancelled and self.check_cancelled():
                    print(f"[Info] Verification cancelled before processing item {i+1}/{total_items}")
                    self.update_status(f"사용자 요청으로 취소됨: {i}/{total_items} 학명 처리 완료")
                    is_cancelled = True
                    break
                    
                # 단일 학명에 대한 WoRMS 검증 수행
                try:
                    # WoRMS 검증 전 취소 확인
                    if self.check_cancelled and self.check_cancelled():
                        print(f"[Info] Verification cancelled before WoRMS API call for item {i+1}/{total_items}")
                        is_cancelled = True
                        break
                        
                    # WoRMS 검증 실행 (check_cancelled 콜백 전달)
                    result_list = verify_species_list([scientific_name], check_cancelled=self.check_cancelled)
                    
                    # WoRMS 검증 후 취소 확인
                    if self.check_cancelled and self.check_cancelled():
                        print(f"[Info] Verification cancelled after WoRMS API call for item {i+1}/{total_items}")
                        is_cancelled = True
                        break
                    
                    if result_list and len(result_list) > 0:
                        result_entry = result_list[0].copy()
                        input_scientific_name = result_entry.get('scientific_name', display_name)  # 입력된 학명
                        
                        # mapped_name 설정 (WoRMS 추천 이름이 있으면 반영)
                        if result_entry.get("similar_name") and result_entry["similar_name"] != "-":
                            result_entry["mapped_name"] = f"{result_entry['similar_name']} (WoRMS 추천)"
                        else:
                            result_entry["mapped_name"] = input_scientific_name
                        
                        # 위키 요약 검색 여부 결정
                        wiki_summary = '-'  # 기본값
                        current_worms_status = str(result_entry.get('worms_status', '')).lower()
                        error_statuses = ['-', 'n/a', 'error', 'no match', 'ambiguous', '형식 오류', 
                                        'worms 결과 없음', 'worms 처리 오류', '오류:', 'worms 오류:']
                        should_search_wiki = result_entry.get('is_verified') or \
                                            not any(status in current_worms_status for status in error_statuses)
                        
                        # 위키백과 검색 (필요한 경우에만)
                        if should_search_wiki:
                            # 위키 검색 전 취소 확인
                            if self.check_cancelled and self.check_cancelled():
                                print(f"[Info] Verification cancelled before Wikipedia search for item {i+1}/{total_items}")
                                is_cancelled = True
                                break
                                
                            self.update_status(f"'{display_name}' 위키백과 검색 중...")
                            self.update_progress((i + 0.75) / total_items, i+1, total_items)
                            
                            name_for_wiki = result_entry.get('scientific_name', display_name)
                            if not name_for_wiki or name_for_wiki == '-':
                                name_for_wiki = display_name
                                
                            try:
                                # 심층분석 결과는 현재 준비 중으로 설정 (향후 DeepSearch 기능 구현 예정)
                                print(f"[Info Wiki] '{name_for_wiki}' 심층분석 결과: 준비 중")
                                result_entry['wiki_summary'] = '준비 중 (DeepSearch 기능 개발 예정)'
                                
                                # 위키 검색 후 취소 확인
                                if self.check_cancelled and self.check_cancelled():
                                    print(f"[Info] Verification cancelled after Wikipedia search for item {i+1}/{total_items}")
                                    is_cancelled = True
                                    break
                                    
                            except Exception as e:
                                print(f"[Error Wiki] 심층분석 결과 가져오기 오류 ({name_for_wiki}): {e}")
                                traceback.print_exc()
                                result_entry['wiki_summary'] = '준비 중 (DeepSearch 기능 개발 예정)'
                        else:
                            result_entry['wiki_summary'] = '준비 중 (DeepSearch 기능 개발 예정)'
                    else:
                        print(f"[Warning] 검증 결과 없음: {display_name}")
                        result_entry = self.create_basic_result(
                            display_name, display_name, False, "WoRMS 결과 없음"
                        )
                        
                        # 심층분석 결과는 현재 준비 중으로 설정
                        result_entry['wiki_summary'] = '준비 중 (DeepSearch 기능 개발 예정)'
                except Exception as e:
                    print(f"[Error] Species verification failed for '{scientific_name}': {e}")
                    traceback.print_exc()
                    
                    # 오류 발생 시 기본 결과 생성
                    result_entry = self.create_basic_result(
                        scientific_name, scientific_name, False, f"오류: {str(e)}"
                    )
                    error_occurred = True
                    error_message_details = str(e)
                    
                    # 오류 발생 시에도 결과는 처리하도록 함
                    results_list.append(result_entry)
                    if self.result_callback:
                        self.result_callback(result_entry.copy(), 'marine')
                    continue
                
                # 결과 처리 (취소되지 않은 경우에만)
                if not is_cancelled:
                    # 결과 목록에 추가
                    results_list.append(result_entry)
                        
                    # 결과 콜백 호출
                    if self.result_callback:
                        self.result_callback(result_entry.copy(), 'marine')
                    
                    # 진행률 업데이트 (다음 항목으로 넘어가기 전에)
                    self.update_progress((i + 1) / total_items, i+1, total_items)
                    
                    # 일부 항목 처리 후 잠시 대기 (UI 반응성 확보)
                    if (i + 1) % 10 == 0:
                        time.sleep(0.1)
                        
            # 최종 진행률 업데이트 (취소 여부에 따라 다른 메시지 표시)
            if is_cancelled:
                processed_count = len(results_list)
                self.update_status(f"검증이 취소되었습니다. ({processed_count}/{total_items} 처리 완료)")
                self.update_progress(processed_count / total_items if total_items > 0 else 1.0, 
                                   processed_count, total_items)
            else:
                # 결과 요약 메시지
                if hasattr(self, 'is_korean_search') and self.is_korean_search and num_skipped_worms > 0:
                    self.update_status(f"검증 완료. {total_items}개 중 {num_skipped_worms}개 항목이 학명 없음으로 WoRMS 검증이 건너뛰어졌습니다.")
                else:
                    self.update_status(f"검증 완료. 총 {total_items}개 항목 처리됨")
                self.update_progress(1.0, total_items, total_items)
                
            return results_list
                
        except Exception as e:
            print(f"[Error] Verification process error: {e}")
            traceback.print_exc()
            error_occurred = True
            error_message_details = str(e)
            
            # 오류 메시지 전달
            self.update_status(f"오류 발생: {str(e)}")
            
            return results_list  # 여기까지 처리된 결과만 반환 