"""
WoRMS API 서비스 구현

이 모듈은 World Register of Marine Species (WoRMS) API와의 통신을 처리합니다.
해양생물 학명 검증을 위해 WoRMS REST API를 활용합니다.
"""
import asyncio
import aiohttp
import time
import json
import traceback
from typing import Any, Dict, List, Optional, Union, Tuple

from species_verifier.config import api_config
from species_verifier.services.base_service import BaseVerificationService
from species_verifier.utils.text_processor import clean_scientific_name

class WormsService(BaseVerificationService):
    """
    WoRMS API 서비스 구현 클래스
    
    World Register of Marine Species (WoRMS) API를 사용하여 해양생물 학명을 검증합니다.
    """
    
    def __init__(self, api_url: Optional[str] = None, request_delay: float = 1.0):
        """
        초기화 함수
        
        Args:
            api_url: WoRMS API 기본 URL (기본값은 설정에서 로드)
            request_delay: 연속적인 API 요청 사이의 지연 시간 (초)
        """
        self.api_url = api_url or api_config.WORMS_API_URL
        self.request_delay = request_delay or api_config.WORMS_REQUEST_DELAY
        self.timeout = aiohttp.ClientTimeout(total=30)
        self._last_request_time = 0
    
    def get_service_name(self) -> str:
        """서비스 이름 반환"""
        return "WoRMS API Service"
    
    def get_service_info(self) -> Dict[str, Any]:
        """서비스 정보 반환"""
        return {
            "name": self.get_service_name(),
            "base_url": self.api_url,
            "request_delay": self.request_delay,
            "api_type": "REST"
        }
    
    async def _wait_for_rate_limit(self):
        """API 요청 간 속도 제한 적용"""
        now = time.time()
        elapsed = now - self._last_request_time
        
        if elapsed < self.request_delay:
            await asyncio.sleep(self.request_delay - elapsed)
        
        self._last_request_time = time.time()
    
    async def _get_aphia_id(self, session: aiohttp.ClientSession, scientific_name: str) -> Union[int, Dict[str, str]]:
        """
        주어진 학명으로 WoRMS에서 AphiaID를 조회
        
        Args:
            session: aiohttp 세션 객체
            scientific_name: 조회할 학명
            
        Returns:
            AphiaID (정수) 또는 오류 정보가 담긴 딕셔너리
        """
        await self._wait_for_rate_limit()
        
        try:
            encoded_name = scientific_name.replace(" ", "%20")
            url = f"{self.api_url}/AphiaIDByName/{encoded_name}?marine_only=false"
            print(f"[Debug WoRMS API] Requesting AphiaID: {url}")
            
            async with session.get(url, timeout=self.timeout) as response:
                print(f"[Debug WoRMS API] Response Status (AphiaID for '{scientific_name}'): {response.status}")
                
                if response.status == 204 or response.status == 404:  # No content or not found
                    print(f"[Debug WoRMS API] No content received for AphiaID '{scientific_name}'.")
                    return {"error": "WoRMS 응답 없음 (AphiaID)"}
                
                if response.status != 200:
                    return {"error": f"WoRMS API 오류 (HTTP {response.status})"}
                
                try:
                    aphia_id_data = await response.json()
                    print(f"[Debug WoRMS API] Parsed JSON (AphiaID for '{scientific_name}'): {aphia_id_data}")
                    
                    if isinstance(aphia_id_data, int) and aphia_id_data == -999:
                        return {"error": "유효하지 않은 학명 (WoRMS)"}
                    elif isinstance(aphia_id_data, list) and len(aphia_id_data) > 0 and isinstance(aphia_id_data[0], int):
                        return aphia_id_data[0]
                    elif isinstance(aphia_id_data, int):
                        return aphia_id_data
                    else:
                        print(f"[Warning WoRMS API] Unexpected response format (AphiaID for {scientific_name}): {aphia_id_data}")
                        return {"error": "WoRMS 예상치 못한 응답 형식 (AphiaID)"}
                    
                except json.JSONDecodeError as e:
                    print(f"[Error WoRMS API] JSON parsing error during AphiaID request for '{scientific_name}': {e}")
                    return {"error": f"WoRMS 응답 파싱 오류 (AphiaID): {e}"}
                
        except aiohttp.ClientError as e:
            print(f"[Error WoRMS API] Network error during AphiaID request for '{scientific_name}': {e}")
            return {"error": f"WoRMS 네트워크 오류 (AphiaID): {e}"}
        except asyncio.TimeoutError:
            print(f"[Error WoRMS API] Timeout during AphiaID request for '{scientific_name}'")
            return {"error": "WoRMS 요청 시간 초과 (AphiaID)"}
        except Exception as e:
            print(f"[Error WoRMS API] Unexpected error during AphiaID request for '{scientific_name}': {e}")
            traceback.print_exc()
            return {"error": f"WoRMS 예상치 못한 오류 (AphiaID): {e}"}
    
    async def _get_aphia_record(self, session: aiohttp.ClientSession, aphia_id: int) -> Dict[str, Any]:
        """
        주어진 AphiaID로 WoRMS에서 상세 레코드를 조회
        
        Args:
            session: aiohttp 세션 객체
            aphia_id: 조회할 AphiaID
            
        Returns:
            AphiaRecord 정보가 담긴 딕셔너리 또는 오류 정보
        """
        if not isinstance(aphia_id, int) or aphia_id <= 0:
            print(f"[Debug WoRMS API] Invalid AphiaID provided for record lookup: {aphia_id}")
            return {"error": "유효하지 않은 AphiaID 제공됨"}
        
        await self._wait_for_rate_limit()
        
        try:
            url = f"{self.api_url}/AphiaRecordByAphiaID/{aphia_id}"
            print(f"[Debug WoRMS API] Requesting AphiaRecord: {url}")
            
            async with session.get(url, timeout=self.timeout) as response:
                print(f"[Debug WoRMS API] Response Status (AphiaRecord for {aphia_id}): {response.status}")
                
                if response.status == 204 or response.status == 404:  # No content or not found
                    print(f"[Debug WoRMS API] No content received for AphiaRecord {aphia_id}.")
                    return {"error": f"WoRMS 응답 없음 (AphiaRecord: {aphia_id})"}
                
                if response.status != 200:
                    return {"error": f"WoRMS API 오류 (HTTP {response.status})"}
                
                try:
                    record_data = await response.json()
                    print(f"[Debug WoRMS API] Parsed JSON (AphiaRecord for {aphia_id}): {record_data}")
                    return record_data
                    
                except json.JSONDecodeError as e:
                    print(f"[Error WoRMS API] JSON parsing error during AphiaRecord request for AphiaID {aphia_id}: {e}")
                    return {"error": f"WoRMS 응답 파싱 오류 (AphiaRecord): {e}"}
                
        except aiohttp.ClientError as e:
            print(f"[Error WoRMS API] Network error during AphiaRecord request for AphiaID {aphia_id}: {e}")
            return {"error": f"WoRMS 네트워크 오류 (AphiaRecord): {e}"}
        except asyncio.TimeoutError:
            print(f"[Error WoRMS API] Timeout during AphiaRecord request for AphiaID {aphia_id}")
            return {"error": "WoRMS 요청 시간 초과 (AphiaRecord)"}
        except Exception as e:
            print(f"[Error WoRMS API] Unexpected error during AphiaRecord request for AphiaID {aphia_id}: {e}")
            traceback.print_exc()
            return {"error": f"WoRMS 예상치 못한 오류 (AphiaRecord): {e}"}
    
    async def verify(self, name: str) -> Dict[str, Any]:
        """
        단일 해양생물 학명 검증
        
        Args:
            name: 검증할 학명
            
        Returns:
            검증 결과 정보가 담긴 딕셔너리
        """
        cleaned_name = clean_scientific_name(name)
        result = {
            'input_name': name,
            'scientific_name': cleaned_name,
            'is_verified': False,
            'worms_status': 'pending',
            'worms_id': '-',
            'worms_link': '-',
            'wiki_summary': '-',
            'similar_name': '-'
        }
        
        if not cleaned_name:
            result['worms_status'] = '빈 학명'
            return result
        
        async with aiohttp.ClientSession() as session:
            # 1. AphiaID 조회
            aphia_id = await self._get_aphia_id(session, cleaned_name)
            
            # AphiaID 조회 오류 처리
            if isinstance(aphia_id, dict) and 'error' in aphia_id:
                result['worms_status'] = aphia_id['error']
                return result
            
            # 2. AphiaRecord 조회
            record = await self._get_aphia_record(session, aphia_id)
            
            # 레코드 조회 오류 처리
            if isinstance(record, dict) and 'error' in record:
                result['worms_status'] = record['error']
                return result
            
            # 3. 결과 매핑
            result['is_verified'] = True
            result['worms_id'] = str(aphia_id)
            result['worms_link'] = f"https://www.marinespecies.org/aphia.php?p=taxdetails&id={aphia_id}"
            
            # 학명 정보
            if 'scientificname' in record:
                result['scientific_name'] = record['scientificname']
            
            # 유효 학명 (accepted_name)과 다른 경우
            if 'valid_name' in record and record['valid_name'] and record['valid_name'] != record.get('scientificname', ''):
                result['similar_name'] = record['valid_name']
                result['worms_status'] = 'synonym'
            elif 'status' in record:
                result['worms_status'] = record['status']
            else:
                result['worms_status'] = 'verified'
            
            # 분류 정보 추가
            taxonomy_parts = []
            for level in ['kingdom', 'phylum', 'class', 'order', 'family', 'genus', 'species']:
                if level in record and record[level]:
                    taxonomy_parts.append(f"{level.capitalize()}: {record[level]}")
            
            if taxonomy_parts:
                result['taxonomy'] = ' > '.join(taxonomy_parts)
        
        return result
    
    async def verify_batch(self, names: List[str]) -> List[Dict[str, Any]]:
        """
        여러 해양생물 학명 일괄 검증
        
        Args:
            names: 검증할 학명 목록
            
        Returns:
            각 학명에 대한 검증 결과 목록
        """
        results = []
        
        for name in names:
            result = await self.verify(name)
            results.append(result)
        
        return results 