import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Optional, Callable


class BaseVerifier(ABC):
    """
    종 검증 기능을 위한 기본 추상 클래스
    모든 구체적인 검증기는 이 클래스를 상속해야 함
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        기본 검증기 초기화
        
        Args:
            logger: 로깅을 위한 로거 객체
        """
        self.logger = logger or logging.getLogger(__name__)
    
    @abstractmethod
    def _verify_single_name(self, name_item: Any, get_wiki_summary: Callable[[str], str]) -> Optional[Dict[str, Any]]:
        """
        단일 종 이름을 검증하는 추상 메서드
        하위 클래스에서 반드시 구현해야 함
        
        Args:
            name_item: 검증할 이름 항목(문자열 또는 튜플)
            get_wiki_summary: 위키피디아 요약을 가져오는 함수
            
        Returns:
            검증 결과 딕셔너리 또는 None(검증 실패 시)
        """
        pass
    
    def verify_names(
        self, 
        names: List[Any],
        update_progress: Callable[[int, str], None],
        get_wiki_summary: Callable[[str], str]
    ) -> Tuple[List[Dict[str, Any]], bool, int]:
        """
        종 이름 목록을 검증하는 공통 메서드
        
        Args:
            names: 검증할 종 이름 목록
            update_progress: 진행 상황을 업데이트하는 콜백 함수
            get_wiki_summary: 위키피디아 요약을 가져오는 함수
            
        Returns:
            검증 결과 목록, 오류 발생 여부, 건너뛴 항목 수
        """
        results = []
        had_errors = False
        skipped = 0
        
        total_names = len(names)
        
        for i, name_item in enumerate(names):
            progress_percent = int((i / total_names) * 100) if total_names > 0 else 0
            
            try:
                # 추상 메서드를 호출하여 실제 검증 로직 수행
                result = self._verify_single_name(name_item, get_wiki_summary)
                
                if result:
                    results.append(result)
                else:
                    skipped += 1
                
                # 진행 상황 업데이트
                status_msg = f"검증 진행 중... {i+1}/{total_names} 완료"
                update_progress(progress_percent, status_msg)
                
            except Exception as e:
                had_errors = True
                self.logger.error(f"검증 중 오류 발생: {str(e)}")
                status_msg = f"오류 발생: {str(e)}"
                update_progress(progress_percent, status_msg)
        
        # 최종 진행 상황 업데이트
        update_progress(100, "검증 완료")
        return results, had_errors, skipped 