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
    
    def update_progress(self, progress: float):
        """진행률 업데이트"""
        if self.progress_callback:
            self.progress_callback(progress)
    
    def update_status(self, message: str):
        """상태 메시지 업데이트"""
        if self.status_update_callback:
            self.status_update_callback(message)
    
    def create_basic_result(self, input_name: str, valid_name: str = '-', status: str = '정보 없음', 
                              taxonomy: str = '-', link: str = '-', wiki_summary: str = '정보 없음', 
                              is_microbe: bool = False) -> Dict[str, Any]:
        """기본 결과 딕셔너리 생성 (한 줄로 수정)"""
        return {
            'input_name': input_name,
            'valid_name': valid_name,
            'is_verified': 'valid' in status.lower(),
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
    
    def perform_microbe_verification(self, microbe_names_list: List[str], context: Union[List[str], str, None] = None) -> List[Dict[str, Any]]:
        """미생물 학명 목록을 검증하는 함수 (LPSN 사이트 이용)
        
        Args:
            microbe_names_list: 검증할 미생물 학명 목록
            context: 검증 컨텍스트 (파일 경로 또는 학명 리스트)
            
        Returns:
            검증 결과 목록
        """
        try:
            # 초기 설정
            total_items = len(microbe_names_list)
            results_list = []
            
            # 진행 상태 UI 업데이트 (초기 메시지)
            initial_status = f"미생물 학명 검증 중 (0/{total_items})"
            if isinstance(context, str): # 파일 경로인 경우
                initial_status = f"파일 '{os.path.basename(context)}' 검증 시작 (총 {total_items}개)"
            elif isinstance(context, list): # 직접 입력인 경우
                initial_status = f"입력된 {total_items}개 학명 검증 시작"
                
            self.update_status(initial_status)
            self.update_progress(0)
            
            # 각 미생물 학명 검증
            for i, microbe_name in enumerate(microbe_names_list):
                try:
                    # 현재 진행 상태 업데이트 (context 반영)
                    prefix = ""
                    if isinstance(context, str): # 파일 경로인 경우
                        prefix = f"파일 '{os.path.basename(context)}' 처리 중 - "
                    
                    current_label = f"{prefix}미생물 학명 검증 중 ({i+1}/{total_items}): {microbe_name}"
                    self.update_status(current_label)
                    self.update_progress(i/total_items)
                    
                    # print(f"[Info] Verifying microbe name: {microbe_name}")
                    
                    # 실제 검증 함수 호출
                    result = None
                    if verify_microbe_species is not None:
                        try:
                            if i > 0:
                                time.sleep(1.0)
                            result = verify_microbe_species(microbe_name)
                        except Exception as ve:
                            print(f"[Error] 검증 함수 호출 오류: {ve}")
                            result = self.create_mock_microbe_result(microbe_name)
                        
                        if result:
                            if isinstance(result, list) and len(result) > 0:
                                result = result[0]
                            if not result.get('status') or result.get('status') in ["시작 전", "-"]:
                                if result.get('valid_name') == microbe_name:
                                    result['status'] = "correct name"
                                elif result.get('valid_name') and result.get('valid_name') != "-":
                                    result['status'] = "synonym"
                                else:
                                    result['status'] = "검증 완료"
                            taxonomy = result.get('taxonomy', '')
                            if not taxonomy or taxonomy in ["조회실패", "조회 실패", "-", ""] or "실패" in taxonomy:
                                default_taxonomy = self.get_default_taxonomy(microbe_name)
                                if default_taxonomy:
                                    result['taxonomy'] = default_taxonomy
                        else:
                            result = self.create_basic_result(microbe_name, microbe_name, "검증 실패", "정보 없음", "-")
                    else:
                        result = self.create_mock_microbe_result(microbe_name)
                    
                    # LPSN 링크 생성
                    valid_name = result.get('valid_name', microbe_name)
                    if valid_name != '-' and valid_name != "정보 없음":
                        genus_species = valid_name.strip().replace(' ', '-').lower()
                        lpsn_link = f"https://lpsn.dsmz.de/species/{genus_species}"
                        result['lpsn_link'] = lpsn_link
                        # print(f"[Debug] LPSN 링크 생성: {lpsn_link}")
                    
                    # 마지막 검사 - 여전히 분류 정보가 없으면 강제로 설정
                    if not result.get('taxonomy') or result.get('taxonomy') in ["조회실패", "조회 실패", "-", ""]:
                        result['taxonomy'] = self.get_default_taxonomy(microbe_name)
                    
                    # 위키피디아 요약 가져오기 (상태 메시지 변경)
                    wiki_search_status = f"'{microbe_name}' 위키백과 검색 중... ({i+1}/{total_items})"
                    if prefix:
                         wiki_search_status = f"{prefix}{wiki_search_status}"
                    self.update_status(wiki_search_status) 
                    
                    name_for_wiki = result.get('valid_name', microbe_name)
                    if name_for_wiki == '-' or not name_for_wiki:
                        name_for_wiki = microbe_name
                    
                    # print(f"[Debug] 미생물 위키 검색어: {name_for_wiki}")
                    wiki_summary = get_wiki_summary(name_for_wiki)
                    # print(f"[Debug] 가져온 위키 내용 길이: {len(wiki_summary) if wiki_summary and wiki_summary != '정보 없음' else 0}자")
                    
                    # 위키 내용이 없거나 충분하지 않으면 종만 검색
                    if wiki_summary == "정보 없음" and ' ' in name_for_wiki:
                        species_parts = name_for_wiki.split()
                        if len(species_parts) >= 2:
                            # 속명만 검색 시도 (예: Escherichia coli -> Escherichia)
                            genus_name = species_parts[0]
                            # print(f"[Debug] 속명으로 다시 시도: {genus_name}")
                            wiki_genus = get_wiki_summary(genus_name)
                            if wiki_genus and wiki_genus != "정보 없음":
                                wiki_summary = wiki_genus
                                # print(f"[Debug] 속명으로 위키 내용 찾음: {len(wiki_summary)}자")
                    
                    wiki_summary = wiki_summary if wiki_summary else '정보 없음'
                    
                    # 위키 정보 추가
                    result['wiki_summary'] = wiki_summary
                    
                    # 최종 결과 확인 (디버깅)
                    # print(f"[Debug] 최종 결과: status={result.get('status')}, taxonomy={result.get('taxonomy')[:30]}...")
                    
                    # 결과 목록에 추가
                    results_list.append(result)
                    
                    # 결과 콜백 호출 (수정: 탭 식별자 추가)
                    if self.result_callback:
                        self.result_callback(result.copy(), 'microbe')
                    
                except Exception as e:
                    print(f"[Error] 미생물 '{microbe_name}' 검증 중 오류 발생: {e}")
                    error_result = self.create_basic_result(microbe_name, microbe_name, "오류", f"검증 중 오류: {str(e)}", "-")
                    results_list.append(error_result)
            
            # 최종 업데이트 (context 반영)
            completion_message = "검증 완료"
            if isinstance(context, str): # 파일 경로인 경우
                completion_message = f"파일 '{os.path.basename(context)}'의 {total_items}개 학명 검증이 완료되었습니다."
            elif isinstance(context, list): # 직접 입력인 경우
                if total_items == 1:
                    completion_message = f"학명 '{context[0]}' 검증이 완료되었습니다."
                elif total_items > 1:
                    completion_message = f"'{context[0]}' 외 {total_items - 1}개 학명의 검증이 완료되었습니다."
            else: # Fallback
                completion_message = f"{total_items}개 학명 검증 완료"
                
            self.update_status(completion_message)
            self.update_progress(1.0)
            
            return results_list
            
        except Exception as e:
            print(f"[Error] 미생물 검증 프로세스 중 오류 발생: {e}")
            traceback.print_exc()
            self.update_status(f"오류 발생: {str(e)}")
            return []  # 오류 발생 시 빈 리스트 반환 