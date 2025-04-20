"""
기본 검증 서비스 인터페이스

이 모듈은 모든 검증 서비스가 구현해야 하는 기본 인터페이스를 정의합니다.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class BaseVerificationService(ABC):
    """
    검증 서비스의 기본 인터페이스
    
    모든 검증 서비스(WoRMS, LPSN 등)는 이 클래스를 상속하여 구현해야 합니다.
    """
    
    @abstractmethod
    async def verify(self, name: str) -> Dict[str, Any]:
        """
        단일 이름(학명) 검증
        
        Args:
            name: 검증할 이름 (학명)
            
        Returns:
            검증 결과 정보가 포함된 딕셔너리
        """
        pass
    
    @abstractmethod
    async def verify_batch(self, names: List[str]) -> List[Dict[str, Any]]:
        """
        여러 이름(학명) 일괄 검증
        
        Args:
            names: 검증할 이름 목록
            
        Returns:
            각 이름에 대한 검증 결과 목록
        """
        pass
    
    @abstractmethod
    def get_service_name(self) -> str:
        """
        서비스 이름 반환
        
        Returns:
            서비스 이름 문자열
        """
        pass
    
    @abstractmethod
    def get_service_info(self) -> Dict[str, Any]:
        """
        서비스 정보 반환
        
        Returns:
            서비스 정보가 포함된 딕셔너리 (버전, 상태 등)
        """
        pass 