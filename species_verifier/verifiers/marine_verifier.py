import logging
from typing import Dict, Any, Optional, Tuple, Callable, Union

from .base_verifier import BaseVerifier


class MarineVerifier(BaseVerifier):
    """
    해양생물 종 이름을 검증하는 검증기 클래스
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        해양생물 검증기 초기화
        
        Args:
            logger: 로깅을 위한 로거 객체
        """
        super().__init__(logger)
    
    def _verify_single_name(self, name_item: Union[str, Tuple[str, str]], get_wiki_summary: Callable[[str], str]) -> Optional[Dict[str, Any]]:
        """
        단일 해양생물 종 이름을 검증
        
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
            
            self.logger.info(f"검증 중: {scientific_name} ({'한글명: ' + korean_name if korean_name else '한글명 없음'})")
            
            # 위키피디아에서 정보 가져오기
            try:
                summary = get_wiki_summary(scientific_name)
            except Exception as e:
                self.logger.error(f"{scientific_name} 위키피디아 정보 가져오기 실패: {str(e)}")
                summary = "정보 가져오기 실패"
            
            # 결과 생성
            result = {
                "korean_name": korean_name if korean_name else "-",
                "scientific_name": scientific_name,
                "summary": summary if summary else "정보 없음",
                "is_verified": summary is not None and summary != "정보 가져오기 실패",
            }
            
            return result
        
        except Exception as e:
            self.logger.error(f"종 검증 중 오류 발생: {str(e)}")
            return None 