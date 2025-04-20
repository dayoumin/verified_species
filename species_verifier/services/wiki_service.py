"""
위키백과 서비스 구현

이 모듈은 위키백과 API와의 통신을 처리하여 학명에 대한 정보를 검색합니다.
"""
import re
import asyncio
import aiohttp
import json
import traceback
from typing import Any, Dict, List, Optional, Union

from species_verifier.config import api_config
from species_verifier.services.base_service import BaseVerificationService

class WikipediaService(BaseVerificationService):
    """
    위키백과 API 서비스 구현 클래스
    
    위키백과 API를 사용하여 학명 또는 한글명에 대한 정보를 검색합니다.
    """
    
    def __init__(self, api_url: Optional[str] = None, request_timeout: int = 5):
        """
        초기화 함수
        
        Args:
            api_url: 위키백과 API URL (기본값은 설정에서 로드)
            request_timeout: API 요청 제한 시간 (초)
        """
        self.api_url = api_url or api_config.WIKIPEDIA_API_URL
        self.timeout = request_timeout or api_config.WIKIPEDIA_REQUEST_TIMEOUT
        self.client_timeout = aiohttp.ClientTimeout(total=self.timeout)
    
    def get_service_name(self) -> str:
        """서비스 이름 반환"""
        return "Wikipedia API Service"
    
    def get_service_info(self) -> Dict[str, Any]:
        """서비스 정보 반환"""
        return {
            "name": self.get_service_name(),
            "base_url": self.api_url,
            "timeout": self.timeout,
            "supported_languages": ["ko", "en"]
        }
    
    async def _search_wikipedia(self, session: aiohttp.ClientSession, search_term: str, language: str = "ko") -> List[str]:
        """
        위키백과에서 검색어 관련 페이지 목록 조회
        
        Args:
            session: aiohttp 세션 객체
            search_term: 검색할 용어
            language: 검색할 언어 ("ko" 또는 "en")
            
        Returns:
            검색 결과 제목 목록
        """
        params = {
            "action": "opensearch",
            "search": search_term,
            "limit": 5,
            "namespace": 0,
            "format": "json"
        }
        
        api_url = f"https://{language}.wikipedia.org/w/api.php"
        
        try:
            async with session.get(api_url, params=params, timeout=self.client_timeout) as response:
                if response.status != 200:
                    print(f"[Error Wiki API] Search request failed: HTTP {response.status}")
                    return []
                
                data = await response.json()
                if len(data) >= 2:
                    return data[1]  # 검색 결과 제목 목록
                return []
                
        except aiohttp.ClientError as e:
            print(f"[Error Wiki API] Network error during search: {e}")
            return []
        except asyncio.TimeoutError:
            print(f"[Error Wiki API] Timeout during search")
            return []
        except Exception as e:
            print(f"[Error Wiki API] Unexpected error during search: {e}")
            traceback.print_exc()
            return []
    
    async def _get_page_content(self, session: aiohttp.ClientSession, page_title: str, language: str = "ko") -> Optional[Dict[str, Any]]:
        """
        위키백과 페이지 내용 조회
        
        Args:
            session: aiohttp 세션 객체
            page_title: 페이지 제목
            language: 검색할 언어 ("ko" 또는 "en")
            
        Returns:
            페이지 내용 정보 딕셔너리 또는 None
        """
        params = {
            "action": "query",
            "prop": "extracts|categories",
            "exintro": 1,  # 도입부만 가져오기
            "explaintext": 1,  # 텍스트 형식으로 가져오기
            "titles": page_title,
            "format": "json",
            "redirects": 1  # 리다이렉트 따라가기
        }
        
        api_url = f"https://{language}.wikipedia.org/w/api.php"
        
        try:
            async with session.get(api_url, params=params, timeout=self.client_timeout) as response:
                if response.status != 200:
                    print(f"[Error Wiki API] Page content request failed: HTTP {response.status}")
                    return None
                
                data = await response.json()
                pages = data.get("query", {}).get("pages", {})
                
                if not pages:
                    return None
                
                # 첫 번째 페이지 (유일한 페이지) 정보 반환
                page_id = next(iter(pages))
                
                # 페이지가 없거나 내용이 없는 경우 (-1은 페이지 없음을 의미)
                if page_id == "-1" or "extract" not in pages[page_id]:
                    return None
                
                return pages[page_id]
                
        except aiohttp.ClientError as e:
            print(f"[Error Wiki API] Network error during page content request: {e}")
            return None
        except asyncio.TimeoutError:
            print(f"[Error Wiki API] Timeout during page content request")
            return None
        except Exception as e:
            print(f"[Error Wiki API] Unexpected error during page content request: {e}")
            traceback.print_exc()
            return None
    
    async def _extract_scientific_name_from_korean_page(self, session: aiohttp.ClientSession, page_content: Dict[str, Any]) -> Optional[str]:
        """
        한글 페이지에서 학명 추출
        
        Args:
            session: aiohttp 세션 객체
            page_content: 페이지 내용 정보
            
        Returns:
            추출된 학명 또는 None
        """
        if not page_content or "extract" not in page_content:
            return None
        
        content = page_content.get("extract", "")
        
        # 학명 추출 패턴
        patterns = [
            r'[학|學]명[은|:\s]*.{0,10}?([A-Z][a-z]+ [a-z]+)',  # '학명: Genus species' 형식
            r'(?<![a-zA-Z])([A-Z][a-z]+ [a-z]+)(?![a-zA-Z])',  # 일반적인 'Genus species' 형식
            r'\(([A-Z][a-z]+ [a-z]+)\)'  # '(Genus species)' 형식
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            if matches:
                scientific_name = matches[0].strip('()')  # 괄호 제거
                # 기본 검증: 최소 2단어 확인
                if len(scientific_name.split()) >= 2:
                    print(f"[Success Wiki Service] 학명 추출 성공: {scientific_name}")
                    return scientific_name
        
        return None
    
    async def _clean_wiki_content(self, content: str, max_length: int = 500) -> str:
        """
        위키 내용 정제
        
        Args:
            content: 원본 위키 내용
            max_length: 최대 길이
            
        Returns:
            정제된 위키 내용
        """
        if not content:
            return "정보 없음"
        
        # 불필요한 마크업 제거
        cleaned_content = re.sub(r'\[[0-9]+\]', '', content)  # 각주 번호 [1], [2] 등 제거
        cleaned_content = re.sub(r'{{\.*?}}', '', cleaned_content)  # {{...}} 템플릿 제거
        cleaned_content = cleaned_content.strip()
        
        # 길이 제한 적용
        if len(cleaned_content) > max_length:
            cleaned_content = cleaned_content[:max_length] + "... (더 많은 내용 있음)"
        
        return cleaned_content
    
    async def verify(self, name: str) -> Dict[str, Any]:
        """
        단일 이름에 대한 위키백과 정보 검색
        
        Args:
            name: 검색할 이름 (학명 또는 한글명)
            
        Returns:
            검색 결과 정보가 담긴 딕셔너리
        """
        if not name or name == '-':
            return {"wiki_summary": "정보 없음", "scientific_name": None}
        
        result = {
            "wiki_summary": "정보 없음",
            "scientific_name": None,
            "source_language": None
        }
        
        async with aiohttp.ClientSession() as session:
            # 1. 한국어로 먼저 검색
            search_results_ko = await self._search_wikipedia(session, name, "ko")
            
            if search_results_ko:
                # 첫 번째 검색 결과 사용
                page_title = search_results_ko[0]
                page_content = await self._get_page_content(session, page_title, "ko")
                
                if page_content and "extract" in page_content:
                    result["wiki_summary"] = await self._clean_wiki_content(page_content["extract"])
                    result["source_language"] = "ko"
                    
                    # 한글 페이지에서 학명 추출 시도
                    scientific_name = await self._extract_scientific_name_from_korean_page(session, page_content)
                    if scientific_name:
                        result["scientific_name"] = scientific_name
                    
                    return result
            
            # 2. 한국어로 검색 실패시 영어로 검색
            search_results_en = await self._search_wikipedia(session, name, "en")
            
            if search_results_en:
                page_title = search_results_en[0]
                page_content = await self._get_page_content(session, page_title, "en")
                
                if page_content and "extract" in page_content:
                    result["wiki_summary"] = await self._clean_wiki_content(page_content["extract"])
                    result["source_language"] = "en"
                    return result
        
        return result
    
    async def verify_batch(self, names: List[str]) -> List[Dict[str, Any]]:
        """
        여러 이름에 대한 위키백과 정보 일괄 검색
        
        Args:
            names: 검색할 이름 목록
            
        Returns:
            각 이름에 대한 검색 결과 목록
        """
        results = []
        
        for name in names:
            result = await self.verify(name)
            results.append(result)
        
        return results 