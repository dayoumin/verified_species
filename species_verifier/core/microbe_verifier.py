"""
미생물 학명 검증 핵심 로직 모듈

이 모듈은 미생물 학명 검증을 위한 핵심 로직을 담당합니다.
LPSN 사이트를 기반으로 미생물 학명 검증을 수행하고 위키백과에서 정보를 보강합니다.
"""
import time
import traceback
import os
from typing import List, Dict, Any, Callable, Optional, Union

from species_verifier.config import app_config, api_config
from species_verifier.core.wiki import get_wiki_summary
from species_verifier.core.verifier import verify_microbe_species

class MicrobeVerifier:
    """미생물 학명 검증을 위한 클래스"""
    
    def __init__(self, progress_callback=None, status_update_callback=None, result_callback=None):
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
    
    def create_basic_result(self, input_name: str, valid_name: str = '-', status: str = '정보 없음', 
                              taxonomy: str = '-', link: str = '-', wiki_summary: str = '정보 없음', 
                              is_microbe: bool = False) -> Dict[str, Any]:
        """기본 결과 딕셔너리 생성"""
        # 학명이 유효하지 않거나 검증 실패 상태인 경우 is_verified를 False로 설정
        is_verified = False
        if valid_name and valid_name != '-' and valid_name != '유효하지 않음' and 'correct' in status.lower():
            is_verified = True
            
        return {
            'input_name': input_name,
            'valid_name': valid_name,
            'is_verified': is_verified,
            'status': status,
            'taxonomy': taxonomy,
            'lpsn_link': link,
            'wiki_summary': wiki_summary,
            'is_microbe': is_microbe
        }
    
    def create_mock_microbe_result(self, microbe_name: str) -> Dict[str, Any]:
        """테스트용 가상 미생물 결과를 생성
        
        Args:
            microbe_name: 미생물 학명
            
        Returns:
            모의 결과 정보
        """
        # print(f"[Debug] 가상 미생물 결과 생성: {microbe_name}")
        
        # 학명별 상태 정보 (샘플)
        status_info = {
            "Vibrio parahaemolyticus": "correct name",
            "Listeria monocytogenes": "correct name",
            "Salmonella enterica": "correct name", 
            "Escherichia coli": "correct name",
            "Bacillus subtilis": "correct name",
            "Staphylococcus aureus": "correct name"
        }
        
        # 기본 결과 생성
        mock_status = "unverified"
        if microbe_name in status_info:
            mock_status = status_info[microbe_name]
        
        # 학명이 잘 알려진 종인지 확인
        valid_name = microbe_name
        taxonomy = self.get_default_taxonomy(microbe_name)
        
        # LPSN 링크 생성
        genus_species = microbe_name.replace(' ', '-').lower()
        lpsn_link = f"https://lpsn.dsmz.de/species/{genus_species}"
        
        return self.create_basic_result(
            microbe_name, valid_name, mock_status, taxonomy, lpsn_link, '-'
        )
    
    def get_default_taxonomy(self, microbe_name: str) -> str:
        """일반적인 미생물 학명의 분류 정보를 반환
        
        Args:
            microbe_name: 미생물 학명
            
        Returns:
            분류 정보 문자열
        """
        # 학명별 분류 정보 (샘플)
        taxonomy_info = {
            "Vibrio parahaemolyticus": "Domain: Bacteria > Phylum: Proteobacteria > Class: Gammaproteobacteria > Order: Vibrionales > Family: Vibrionaceae",
            "Listeria monocytogenes": "Domain: Bacteria > Phylum: Firmicutes > Class: Bacilli > Order: Bacillales > Family: Listeriaceae",
            "Salmonella enterica": "Domain: Bacteria > Phylum: Proteobacteria > Class: Gammaproteobacteria > Order: Enterobacterales > Family: Enterobacteriaceae",
            "Aeromonas hydrophila": "Domain: Bacteria > Phylum: Proteobacteria > Class: Gammaproteobacteria > Order: Aeromonadales > Family: Aeromonadaceae",
            "Clostridium botulinum": "Domain: Bacteria > Phylum: Firmicutes > Class: Clostridia > Order: Clostridiales > Family: Clostridiaceae",
            "Escherichia coli": "Domain: Bacteria > Phylum: Proteobacteria > Class: Gammaproteobacteria > Order: Enterobacterales > Family: Enterobacteriaceae"
        }
        
        # 속명 기반 분류 정보 (정확한 종명이 없을 때 사용)
        genus_taxonomy = {
            "Vibrio": "Domain: Bacteria > Phylum: Proteobacteria > Class: Gammaproteobacteria > Order: Vibrionales > Family: Vibrionaceae",
            "Listeria": "Domain: Bacteria > Phylum: Firmicutes > Class: Bacilli > Order: Bacillales > Family: Listeriaceae",
            "Salmonella": "Domain: Bacteria > Phylum: Proteobacteria > Class: Gammaproteobacteria > Order: Enterobacterales > Family: Enterobacteriaceae",
            "Aeromonas": "Domain: Bacteria > Phylum: Proteobacteria > Class: Gammaproteobacteria > Order: Aeromonadales > Family: Aeromonadaceae",
            "Clostridium": "Domain: Bacteria > Phylum: Firmicutes > Class: Clostridia > Order: Clostridiales > Family: Clostridiaceae",
            "Escherichia": "Domain: Bacteria > Phylum: Proteobacteria > Class: Gammaproteobacteria > Order: Enterobacterales > Family: Enterobacteriaceae",
            "Bacillus": "Domain: Bacteria > Phylum: Firmicutes > Class: Bacilli > Order: Bacillales > Family: Bacillaceae",
            "Pseudomonas": "Domain: Bacteria > Phylum: Proteobacteria > Class: Gammaproteobacteria > Order: Pseudomonadales > Family: Pseudomonadaceae",
            "Staphylococcus": "Domain: Bacteria > Phylum: Firmicutes > Class: Bacilli > Order: Bacillales > Family: Staphylococcaceae",
            "Streptococcus": "Domain: Bacteria > Phylum: Firmicutes > Class: Bacilli > Order: Lactobacillales > Family: Streptococcaceae",
            "Lactobacillus": "Domain: Bacteria > Phylum: Firmicutes > Class: Bacilli > Order: Lactobacillales > Family: Lactobacillaceae"
        }
        
        # 전체 학명이 매핑에 있는지 확인
        if microbe_name in taxonomy_info:
            return taxonomy_info[microbe_name]
            
        # 속명만 추출하여 매핑 확인
        parts = microbe_name.split()
        if len(parts) > 0 and parts[0] in genus_taxonomy:
            return genus_taxonomy[parts[0]]
            
        # 기본 분류 제공
        return "Domain: Bacteria"
    
    def perform_microbe_verification(self, microbe_names_list: List[str], context: Union[List[str], str, None] = None, check_cancelled: Callable[[], bool] = None) -> List[Dict[str, Any]]:
        """미생물 학명 목록을 검증하는 함수 (LPSN 사이트 이용) - 수정됨
        
        Args:
            microbe_names_list: 검증할 미생물 학명 목록
            context: 검증 컨텍스트 (파일 경로 또는 학명 리스트)
            check_cancelled: 취소 여부를 확인하는 함수
            
        Returns:
            검증 결과 목록
        """
        try:
            # 취소 여부 확인
            if check_cancelled and check_cancelled():
                print("[Info MicrobeVerifier] 검증 시작 전 취소 요청 감지됨")
                return []  # 빈 리스트 반환
                
            # 초기 설정
            if not isinstance(microbe_names_list, list):
                print(f"[Error MicrobeVerifier] 입력값이 리스트가 아님: {type(microbe_names_list)}")
                return [] # 빈 리스트 반환
            
            total_items = len(microbe_names_list)
            
            # 진행 상태 UI 업데이트 (초기 메시지)
            initial_status = f"미생물 학명 검증 시작 (총 {total_items}개)"
            if isinstance(context, str): # 파일 경로인 경우
                initial_status = f"파일 '{os.path.basename(context)}' 검증 시작 (총 {total_items}개)"
            elif isinstance(context, list): # 직접 입력인 경우
                initial_status = f"입력된 {total_items}개 학명 검증 시작"
                
            self.update_status(initial_status)
            self.update_progress(0, 0, total_items)
            
            # 취소 여부 한번 더 확인
            if check_cancelled and check_cancelled():
                print("[Info MicrobeVerifier] 검증 직전 취소 요청 감지됨")
                return []
                
            # 전체 리스트를 verify_microbe_species 함수에 한 번만 전달
            if verify_microbe_species is not None:
                try:
                    # verify_microbe_species는 내부적으로 진행률/상태 콜백을 호출하지 않음
                    # 필요하다면 verifier.py 내부에서 콜백 호출 로직 추가 필요
                    # 여기서는 전체 리스트를 전달하여 결과를 한 번에 받음
                    print(f"[Info MicrobeVerifier] Calling verify_microbe_species with {total_items} items...")
                    print(f"[Info MicrobeVerifier] verify_microbe_species 호출 시작 - 전체 {total_items}개 항목 처리 예정")
                    
                    # 통합된 verify_microbe_species 함수 호출
                    # 취소 기능을 포함하여 호출
                    print(f"[Info MicrobeVerifier] verify_microbe_species 호출 시작 - 전체 {total_items}개 항목 처리 예정")
                    
                    # 처리된 항목 수를 추적하기 위한 카운터 변수
                    processed_count = [0]  # 변경 가능한 리스트로 사용
                    
                    # 진행률 업데이트를 위한 콜백 함수 정의
                    def progress_callback(result, result_type):
                        if self.result_callback:
                            self.result_callback(result, result_type)
                        
                        # 현재 처리된 항목 수 증가 및 계산
                        processed_count[0] += 1
                        progress = float(processed_count[0]) / total_items if total_items > 0 else 0
                        
                        # 진행률 업데이트 시 현재 항목 수와 전체 항목 수를 정확히 전달
                        if self.progress_callback:
                            self.progress_callback(progress, processed_count[0], total_items)
                        
                        # 상태 메시지 업데이트
                        if self.status_update_callback:
                            self.status_update_callback(f"미생물 검증 중... ({processed_count[0]}/{total_items})")
                    
                    # verify_microbe_species 함수 호출 (취소 기능 포함)
                    results_list = verify_microbe_species(
                        microbe_names_list, 
                        result_callback=progress_callback, 
                        check_cancelled=check_cancelled
                    )
                    
                    print(f"[Info MicrobeVerifier] verify_microbe_species 처리 완료 - 반환된 결과 수: {len(results_list)}/{total_items}개")
                    
                    # 취소 여부 최종 확인
                    if check_cancelled and check_cancelled():
                        print("[Info MicrobeVerifier] 결과 처리 전 취소 요청 감지됨")
                        cancel_status = f"미생물 검증 취소됨 ({len(results_list)}/{total_items} 결과)"
                        if isinstance(context, str):
                            cancel_status = f"파일 '{os.path.basename(context)}' 검증 취소됨 ({len(results_list)}/{total_items} 결과)"
                        self.update_status(cancel_status)
                        return results_list
                    
                    # 최종 상태 업데이트 (진행률은 콜백에서 처리되므로 여기서는 1.0으로 설정)
                    completion_status = f"미생물 검증 완료 ({len(results_list)}/{total_items} 결과)"
                    if isinstance(context, str):
                        completion_status = f"파일 '{os.path.basename(context)}' 검증 완료 ({len(results_list)}/{total_items} 결과)"
                    self.update_status(completion_status)
                    self.update_progress(1.0, total_items, total_items) # 완료 시 100%

                    return results_list
                
                except Exception as ve:
                    print(f"[Error MicrobeVerifier] verify_microbe_species 함수 호출 중 오류: {ve}")
                    traceback.print_exc()
                    self.update_status(f"오류 발생: {ve}")
                    self.update_progress(1.0, total_items, total_items)
                    return []
            else:
                print("[Warning MicrobeVerifier] verify_microbe_species 함수를 찾을 수 없음. 모의 결과 생성.")
                # 모의 결과 생성 및 콜백 처리 (기존 로직 유지)
                results_list = [self.create_mock_microbe_result(name) for name in microbe_names_list]
                if self.result_callback:
                    for i, result_item in enumerate(results_list):
                        self.result_callback(result_item, "col")
                        self.update_progress((i + 1) / total_items, i + 1, total_items)
                self.update_status("모의 검증 완료")
                self.update_progress(1.0, total_items, total_items)
                return results_list

        except Exception as e:
            print(f"[Error MicrobeVerifier] perform_microbe_verification 중 예외 발생: {e}")
            traceback.print_exc()
            self.update_status(f"심각한 오류 발생: {e}")
            return [] 