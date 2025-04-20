"""
상태 표시줄 컴포넌트

이 모듈은 애플리케이션의 상태 정보를 표시하는 컴포넌트를 정의합니다.
"""
import tkinter as tk
import customtkinter as ctk
from typing import Any, Optional

from .base import BaseTkComponent


class StatusBar(BaseTkComponent):
    """상태 표시줄 컴포넌트"""
    
    def __init__(self, parent: Any, **kwargs):
        """
        초기화
        
        Args:
            parent: 부모 위젯
            **kwargs: 추가 인자
        """
        self.height = kwargs.pop('height', 50)
        self.font = kwargs.pop('font', None)
        super().__init__(parent, **kwargs)
    
    def _create_widgets(self, **kwargs):
        """위젯 생성"""
        self.widget = ctk.CTkFrame(self.parent, height=self.height)
        self.widget.grid_columnconfigure(0, weight=1) # 상태 레이블 영역
        self.widget.grid_columnconfigure(1, weight=0) # 프로그레스 바 영역
        # 취소 버튼 컬럼 삭제 (필요할 때만 grid로 추가)

        self.status_label = ctk.CTkLabel(self.widget, text="입력 대기 중", font=self.font) # 초기 메시지 변경
        self.status_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.progress_bar = ctk.CTkProgressBar(self.widget, width=400)
        self.progress_bar.grid(row=0, column=1, padx=10, pady=10, sticky="e") # 오른쪽 정렬
        self.progress_bar.set(0)
        
        # 취소 버튼 생성 (초기에는 배치하지 않음)
        self.cancel_button = ctk.CTkButton(self.widget, text="취소", width=60, state="disabled")
        # self.cancel_button.grid(...) # 여기서 배치하지 않음
    
    def set_status(self, message: str):
        """
        상태 메시지 설정
        
        Args:
            message: 표시할 메시지
        """
        self.status_label.configure(text=message)
    
    def set_progress(self, value: float):
        """
        진행률 설정
        
        Args:
            value: 진행률 (0.0 ~ 1.0)
        """
        self.progress_bar.set(value)
    
    def set_busy(self, status_text: Optional[str] = None):
        """바쁨 상태로 설정 (취소 버튼 표시)"""
        if status_text:
            self.status_label.configure(text=status_text)
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()
        # 취소 버튼 활성화 및 배치
        self.cancel_button.configure(state="normal")
        self.cancel_button.grid(row=0, column=2, padx=10, pady=10, sticky="e") # 2번 컬럼에 배치
    
    def set_ready(self, status_text: str = "입력 대기 중"):
        """준비 상태로 설정 (취소 버튼 숨김)"""
        self.status_label.configure(text=status_text) # 기본 메시지 변경
        self.progress_bar.stop()
        self.progress_bar.configure(mode="determinate")
        self.progress_bar.set(0)
        # 취소 버튼 비활성화 및 숨김
        self.cancel_button.configure(state="disabled")
        self.cancel_button.grid_forget() # 그리드에서 제거
    
    def set_cancel_command(self, command: Any):
        """
        취소 버튼 명령 설정
        
        Args:
            command: 취소 버튼 클릭 시 실행할 명령
        """
        self.cancel_button.configure(command=command) 