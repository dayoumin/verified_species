"""
GUI 컴포넌트 기본 클래스

이 모듈은 모든 GUI 컴포넌트가 상속할 기본 클래스를 정의합니다.
"""
import customtkinter as ctk
from typing import Optional, Callable, Any
from abc import ABC, abstractmethod


class BaseComponent:
    """모든 GUI 컴포넌트의 기본 클래스"""
    
    def __init__(self):
        """초기화"""
        self.parent = None
        self.widget = None
    
    def get_widget(self) -> Any:
        """컴포넌트의 메인 위젯 반환"""
        return self.widget


class BaseTkComponent(BaseComponent):
    """Tkinter/CustomTkinter 위젯 기반 컴포넌트의 기본 클래스"""
    
    def __init__(self, parent: Any, **kwargs):
        """
        초기화
        
        Args:
            parent: 부모 위젯
            **kwargs: 추가 인자
        """
        super().__init__()
        self.parent = parent
        self._create_widgets(**kwargs)
    
    def _create_widgets(self, **kwargs):
        """위젯 생성 (하위 클래스에서 오버라이드)"""
        pass
    
    def update(self, **kwargs):
        """컴포넌트 업데이트 (하위 클래스에서 오버라이드)"""
        pass
    
    def clear(self):
        """컴포넌트 초기화 (하위 클래스에서 오버라이드)"""
        pass


class BaseTabFrame(ctk.CTkFrame):  # 기존 클래스에서 ctk.CTkFrame을 상속받도록 수정
    """
    탭 프레임 컴포넌트의 기본 클래스
    
    각 탭 프레임은 이 클래스를 상속받아 구현해야 합니다.
    """
    
    def __init__(self, parent, *args, **kwargs):
        """
        초기화
        
        Args:
            parent: 부모 위젯
            *args: 추가 위치 인자
            **kwargs: 추가 키워드 인자
        """
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        
        # 콜백 등록을 위한 딕셔너리
        self._callbacks = {}
        
        # 위젯 생성
        self._create_widgets()

    def _create_widgets(self):
        """위젯 생성 메서드 (서브클래스에서 구현)"""
        pass
    
    def register_callback(self, event_name: str, callback: Callable):
        """
        콜백 함수 등록
        
        Args:
            event_name: 이벤트 이름
            callback: 콜백 함수
        """
        self._callbacks[event_name] = callback
    
    def unregister_callback(self, event_name: str):
        """
        콜백 함수 해제
        
        Args:
            event_name: 이벤트 이름
        """
        if event_name in self._callbacks:
            del self._callbacks[event_name]
    
    def trigger_callback(self, event_name: str, *args, **kwargs):
        """
        콜백 함수 호출
        
        Args:
            event_name: 이벤트 이름
            *args: 콜백 함수에 전달할 위치 인자
            **kwargs: 콜백 함수에 전달할 키워드 인자
        
        Returns:
            콜백 함수의 반환값 또는 None (콜백이 없는 경우)
        """
        if event_name in self._callbacks:
            return self._callbacks[event_name](*args, **kwargs)
        return None
    
    @abstractmethod
    def set_selected_file(self, file_path: Optional[str]):
        """
        선택된 파일 설정 (추상 메서드)
        
        자식 클래스에서 구현해야 합니다.
        
        Args:
            file_path: 파일 경로 또는 None
        """
        pass
    
    @abstractmethod
    def focus_entry(self):
        """
        입력 필드에 포커스 설정 (추상 메서드)
        
        자식 클래스에서 구현해야 합니다.
        """
        pass


class BaseResultView(BaseTkComponent):
    """결과 표시 컴포넌트의 기본 클래스"""
    
    def __init__(self, parent: Any, **kwargs):
        """
        초기화
        
        Args:
            parent: 부모 위젯
            **kwargs: 추가 인자
        """
        super().__init__(parent, **kwargs)
        self.results = []
    
    def add_result(self, result: Any, clear_first: bool = False):
        """
        결과 추가
        
        Args:
            result: 추가할 결과
            clear_first: 기존 결과 초기화 여부
        """
        if clear_first:
            self.clear()
        self.results.append(result)
        self._display_result(result)
    
    def _display_result(self, result: Any):
        """
        결과 표시 (하위 클래스에서 오버라이드)
        
        Args:
            result: 표시할 결과
        """
        pass