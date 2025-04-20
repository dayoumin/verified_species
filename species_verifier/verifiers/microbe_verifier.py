import logging
from typing import Dict, Any, Optional, Tuple, Callable, Union

from .base_verifier import BaseVerifier


class MicrobeVerifier(BaseVerifier):
    """
    미생물 종 이름을 검증하는 검증기 클래스
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        미생물 검증기 초기화
        
        Args:
            logger: 로깅을 위한 로거 객체
        """
        super().__init__(logger)
    
    def _verify_single_name(self, name_item: Union[str, Tuple[str, str]], get_wiki_summary: Callable[[str], str]) -> Optional[Dict[str, Any]]:
        """
        단일 미생물 종 이름을 검증
        
        Args:
            name_item: 검증할 이름(한글명, 학명) 튜플 또는 학명 문자열
            get_wiki_summary: 위키피디아 요약을 가져오는 함수
            
        Returns:
            검증 결과 딕셔너리 또는 None(검증 실패 시)
        """
        try:
            is_korean = isinstance(name_item, tuple)
            
            if is_korean:
                korean_name, scientific_name = name_item
                if not korean_name or not scientific_name:
                    self.logger.warning(f"빈 이름 발견: {name_item}")
                    return None
            else:
                korean_name = ""
                scientific_name = name_item
                if not scientific_name:
                    self.logger.warning(f"빈 학명 발견")
                    return None
            
            self.logger.info(f"미생물 검증 중: {scientific_name} ({'한글명: ' + korean_name if korean_name else '한글명 없음'})")
            
            # 위키피디아에서 정보 가져오기
            try:
                summary = get_wiki_summary(scientific_name)
            except Exception as e:
                self.logger.error(f"미생물 {scientific_name} 위키피디아 정보 가져오기 실패: {str(e)}")
                summary = "정보 가져오기 실패"
            
            # 미생물 특화 검증 로직 (추가 특성 확인 등)
            is_microbe = self._check_if_microbe(scientific_name, summary)
            
            # 결과 생성
            result = {
                "korean_name": korean_name if korean_name else "-",
                "scientific_name": scientific_name,
                "summary": summary if summary else "정보 없음",
                "is_verified": summary is not None and summary != "정보 가져오기 실패",
                "is_microbe": is_microbe
            }
            
            return result
        
        except Exception as e:
            self.logger.error(f"미생물 종 검증 중 오류 발생: {str(e)}")
            return None
    
    def _check_if_microbe(self, scientific_name: str, summary: str) -> bool:
        """
        주어진 학명과 요약 정보를 기반으로 실제 미생물인지 확인
        
        Args:
            scientific_name: 검증할 학명
            summary: 위키피디아 요약 정보
            
        Returns:
            미생물 여부 (True/False)
        """
        # 미생물 관련 키워드
        microbe_keywords = [
            "bacteria", "bacterium", "archaea", "archaeon", "virus", "fungi", "fungus",
            "protozoa", "algae", "microorganism", "미생물", "박테리아", "세균", "바이러스",
            "고균", "원생생물", "조류", "미생물"
        ]
        
        # 학명에서 확인
        if any(keyword.lower() in scientific_name.lower() for keyword in microbe_keywords):
            return True
            
        # 요약에서 확인
        if summary and any(keyword.lower() in summary.lower() for keyword in microbe_keywords):
            return True
            
        return False 