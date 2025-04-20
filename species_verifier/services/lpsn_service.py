"""
LPSN 서비스 구현

이 모듈은 List of Prokaryotic names with Standing in Nomenclature (LPSN) 웹사이트의 데이터를 가져와
미생물 학명을 검증하는 서비스를 제공합니다.
"""
import re
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import time
import traceback
from typing import Any, Dict, List, Optional, Union

from species_verifier.config import api_config
from species_verifier.services.base_service import BaseVerificationService
from species_verifier.utils.text_processor import clean_scientific_name

class LPSNService(BaseVerificationService):
    """
    LPSN 서비스 구현 클래스
    
    LPSN 웹사이트를 크롤링하여 미생물 학명을 검증합니다.
    """
    
    def __init__(self, base_url: Optional[str] = None, request_delay: float = 1.0):
        """
        초기화 함수
        
        Args:
            base_url: LPSN 사이트 기본 URL (기본값은 설정에서 로드)
            request_delay: 연속적인 요청 사이의 지연 시간 (초)
        """
        self.base_url = base_url or api_config.LPSN_BASE_URL
        self.request_delay = request_delay
        self.timeout = aiohttp.ClientTimeout(total=30)
        self._last_request_time = 0
        
        # 헤더 설정 (봇 차단 방지)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
        }
    
    def get_service_name(self) -> str:
        """서비스 이름 반환"""
        return "LPSN Service"
    
    def get_service_info(self) -> Dict[str, Any]:
        """서비스 정보 반환"""
        return {
            "name": self.get_service_name(),
            "base_url": self.base_url,
            "request_delay": self.request_delay,
            "service_type": "Web Scraping"
        }
    
    async def _wait_for_rate_limit(self):
        """요청 간 속도 제한 적용"""
        now = time.time()
        elapsed = now - self._last_request_time
        
        if elapsed < self.request_delay:
            await asyncio.sleep(self.request_delay - elapsed)
        
        self._last_request_time = time.time()
    
    def get_default_taxonomy(self, microbe_name: str) -> str:
        """
        일반적인 미생물 학명의 분류 정보를 반환
        
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
    
    async def _search_lpsn(self, session: aiohttp.ClientSession, name: str) -> Optional[BeautifulSoup]:
        """
        LPSN 사이트에서 학명 검색
        
        Args:
            session: aiohttp 세션 객체
            name: 검색할 학명
            
        Returns:
            검색 결과 페이지의 BeautifulSoup 객체 또는 None
        """
        await self._wait_for_rate_limit()
        
        search_url = f"https://lpsn.dsmz.de/search?word={name}"
        print(f"[Info LPSN Service] Searching '{name}' at {search_url}")
        
        try:
            async with session.get(search_url, headers=self.headers, timeout=self.timeout) as response:
                if response.status != 200:
                    print(f"[Error LPSN Service] Search request failed: HTTP {response.status}")
                    return None
                
                html_content = await response.text()
                soup = BeautifulSoup(html_content, 'html.parser')
                return soup
                
        except aiohttp.ClientError as e:
            print(f"[Error LPSN Service] Network error during search: {e}")
            return None
        except asyncio.TimeoutError:
            print(f"[Error LPSN Service] Timeout during search")
            return None
        except Exception as e:
            print(f"[Error LPSN Service] Unexpected error during search: {e}")
            traceback.print_exc()
            return None
    
    async def _get_species_page(self, session: aiohttp.ClientSession, species_url: str) -> Optional[BeautifulSoup]:
        """
        LPSN 종 상세 페이지 조회
        
        Args:
            session: aiohttp 세션 객체
            species_url: 종 상세 페이지 URL
            
        Returns:
            상세 페이지의 BeautifulSoup 객체 또는 None
        """
        await self._wait_for_rate_limit()
        
        try:
            async with session.get(species_url, headers=self.headers, timeout=self.timeout) as response:
                if response.status != 200:
                    print(f"[Error LPSN Service] Species page request failed: HTTP {response.status}")
                    return None
                
                html_content = await response.text()
                soup = BeautifulSoup(html_content, 'html.parser')
                return soup
                
        except aiohttp.ClientError as e:
            print(f"[Error LPSN Service] Network error during species page request: {e}")
            return None
        except asyncio.TimeoutError:
            print(f"[Error LPSN Service] Timeout during species page request")
            return None
        except Exception as e:
            print(f"[Error LPSN Service] Unexpected error during species page request: {e}")
            traceback.print_exc()
            return None
    
    async def verify(self, name: str) -> Dict[str, Any]:
        """
        단일 미생물 학명 검증
        
        Args:
            name: 검증할 미생물 학명
            
        Returns:
            검증 결과 정보가 담긴 딕셔너리
        """
        cleaned_name = clean_scientific_name(name)
        result = {
            'input_name': name,
            'valid_name': cleaned_name,
            'status': "검증 전",
            'taxonomy': "-",
            'lpsn_link': "-",
            'wiki_summary': "-"
        }
        
        if not cleaned_name:
            result['status'] = "빈 학명"
            return result
        
        async with aiohttp.ClientSession() as session:
            # 1. LPSN 사이트 검색
            search_soup = await self._search_lpsn(session, cleaned_name)
            
            if not search_soup:
                result['status'] = "검색 실패"
                result['taxonomy'] = self.get_default_taxonomy(cleaned_name)
                return result
            
            # 2. 검색 결과 없음 체크
            no_results = search_soup.find('div', class_='alert-info')
            if no_results and "No results" in no_results.text:
                print(f"[Info LPSN Service] '{cleaned_name}' 검색 결과 없음")
                result['status'] = '검색 결과 없음'
                result['taxonomy'] = self.get_default_taxonomy(cleaned_name)
                return result
            
            # 3. 검색 결과 테이블 또는 직접 링크 확인
            species_link_tag = None
            
            # 우선순위: Species 테이블의 링크 > Genus 테이블의 링크
            species_table = search_soup.find('h4', string=re.compile(r'Species'))
            if species_table:
                table = species_table.find_next_sibling('table')
                if table:
                    # 입력 이름과 가장 유사한 링크 찾기 (대소문자 무시)
                    links = table.find_all('a', href=re.compile(r'/species/'))
                    best_match_link = None
                    min_diff = float('inf')
                    
                    for link in links:
                        link_text_cleaned = clean_scientific_name(link.text.strip())
                        if cleaned_name.lower() == link_text_cleaned.lower():  # 정확히 일치
                            best_match_link = link
                            break
                        # 유사도 계산 (간단히 길이 차이)
                        diff = abs(len(cleaned_name) - len(link_text_cleaned))
                        if diff < min_diff:
                            min_diff = diff
                            best_match_link = link
                    
                    species_link_tag = best_match_link
            
            # Species 테이블에서 못찾으면 Genus 테이블 시도
            if not species_link_tag:
                genus_table = search_soup.find('h4', string=re.compile(r'Genus'))
                if genus_table:
                    table = genus_table.find_next_sibling('table')
                    if table:
                        links = table.find_all('a', href=re.compile(r'/genus/'))
                        # 속명만 비교
                        genus_part = cleaned_name.split()[0].lower() if ' ' in cleaned_name else cleaned_name.lower()
                        for link in links:
                            if genus_part == link.text.strip().lower():
                                species_link_tag = link
                                break
            
            # 4. 상세 페이지 정보 추출
            if species_link_tag and species_link_tag.get('href'):
                species_url = f"https://lpsn.dsmz.de{species_link_tag.get('href')}"
                result['lpsn_link'] = species_url
                print(f"[Info LPSN Service] 상세 페이지 접근: {species_url}")
                
                species_soup = await self._get_species_page(session, species_url)
                
                if species_soup:
                    # 유효 학명 (페이지 제목 등에서 추출 시도)
                    title_tag = species_soup.find('h1')
                    if title_tag:
                        # 'Genus species' 또는 'Genus' 형태 추출
                        title_text = title_tag.get_text(strip=True)
                        if title_text.startswith("Species"):
                            result['valid_name'] = title_text.replace("Species", "").strip()
                        elif title_text.startswith("Genus"):
                            result['valid_name'] = title_text.replace("Genus", "").strip()
                        else:  # 예상치 못한 제목 형식
                            result['valid_name'] = species_link_tag.text.strip()  # 링크 텍스트 사용
                    else:  # 제목 태그 없으면 링크 텍스트 사용
                        result['valid_name'] = species_link_tag.text.strip()
                    
                    # 분류학적 상태 (Taxonomic status)
                    status_dt = species_soup.find('dt', string=re.compile(r'Taxonomic status:'))
                    if status_dt and status_dt.find_next_sibling('dd'):
                        result['status'] = status_dt.find_next_sibling('dd').get_text(strip=True)
                    else:  # 상태 정보 못찾으면 링크 텍스트로 추정
                        try:
                            row = species_link_tag.find_parent('tr')
                            if row and len(row.find_all('td')) > 1:
                                result['status'] = row.find_all('td')[1].get_text(strip=True)
                            else:
                                result['status'] = 'correct name'  # 기본값
                        except Exception:
                            result['status'] = 'correct name'  # 기본값
                    
                    # 분류 정보 (breadcrumb 또는 dl 사용)
                    breadcrumb = species_soup.find('ol', class_='breadcrumb')
                    taxonomy_parts = []
                    
                    if breadcrumb:
                        items = breadcrumb.find_all('li', class_='breadcrumb-item')
                        # Domain부터 시작 (LPSN Home 제외)
                        for item in items[1:]:  # LPSN Home 건너뛰기
                            link = item.find('a')
                            if link:
                                level_text = link.get_text(strip=True)
                                taxonomy_parts.append(level_text)
                    else:
                        # dl 리스트에서 추출 시도
                        dl = species_soup.find('dl', class_='dl-horizontal')
                        if dl:
                            levels = ['Domain', 'Phylum', 'Class', 'Order', 'Family', 'Genus']
                            for level in levels:
                                dt = dl.find('dt', string=re.compile(f'{level}:'))
                                if dt and dt.find_next_sibling('dd'):
                                    dd = dt.find_next_sibling('dd')
                                    link = dd.find('a')
                                    if link:
                                        taxonomy_parts.append(f"{level}: {link.get_text(strip=True)}")
                    
                    if taxonomy_parts:
                        result['taxonomy'] = ' > '.join(taxonomy_parts)
                    else:
                        result['taxonomy'] = self.get_default_taxonomy(result.get('valid_name', cleaned_name))
                
                else:
                    # 상세 페이지 로드 실패
                    result['status'] = '상세 페이지 로드 실패'
                    result['taxonomy'] = self.get_default_taxonomy(cleaned_name)
            
            else:
                # 검색 결과에서 링크를 찾지 못한 경우
                result['status'] = '상세 정보 링크 없음'
                result['taxonomy'] = self.get_default_taxonomy(cleaned_name)
        
        # 결과가 없거나 불완전한 경우 상태 보정
        if not result['valid_name'] or result['valid_name'] == '-':
            result['valid_name'] = cleaned_name
        
        if result['status'] in ["검증 전", "시작 전", "-"]:
            # 학명이 일치하면 correct name으로 설정
            if result['valid_name'] == cleaned_name:
                result['status'] = "correct name"
            else:
                # 유효한 학명이 반환되었으면 synonym으로 설정
                if result['valid_name'] and result['valid_name'] != "-":
                    result['status'] = "synonym"
                else:
                    result['status'] = "검증 완료"
        
        # 분류 정보가 없으면 기본값 사용
        if not result['taxonomy'] or result['taxonomy'] == "-":
            result['taxonomy'] = self.get_default_taxonomy(cleaned_name)
        
        # LPSN 링크 생성 (없는 경우)
        if result['lpsn_link'] == "-" and result['valid_name'] != "-":
            genus_species = result['valid_name'].strip().replace(' ', '-').lower()
            result['lpsn_link'] = f"https://lpsn.dsmz.de/species/{genus_species}"
        
        return result
    
    async def verify_batch(self, names: List[str]) -> List[Dict[str, Any]]:
        """
        여러 미생물 학명 일괄 검증
        
        Args:
            names: 검증할 미생물 학명 목록
            
        Returns:
            각 학명에 대한 검증 결과 목록
        """
        results = []
        
        for name in names:
            result = await self.verify(name)
            results.append(result)
        
        return results 