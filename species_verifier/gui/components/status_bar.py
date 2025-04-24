"""
상태 표시줄 컴포넌트

이 모듈은 애플리케이션의 상태 정보를 표시하는 컴포넌트를 정의합니다.
"""
import tkinter as tk
import customtkinter as ctk
from typing import Any, Optional, Callable

from .base import BaseTkComponent


class StatusBar(BaseTkComponent):
    """상태 표시줄 컴포넌트"""
    
    def __init__(self, parent: Any, save_command: Optional[Callable] = None, **kwargs):
        """
        초기화
        
        Args:
            parent: 부모 위젯
            save_command: 저장 버튼 클릭 시 실행할 명령
            **kwargs: 추가 인자
        """
        self.height = kwargs.pop('height', 40)
        self.font = kwargs.pop('font', None)
        self._save_command = save_command
        super().__init__(parent, **kwargs)
    
    def _create_widgets(self, **kwargs):
        """위젯 생성"""
        self.widget = ctk.CTkFrame(self.parent, height=self.height)
        self.widget.grid_columnconfigure(0, weight=1)
        self.widget.grid_columnconfigure(1, weight=0)
        self.widget.grid_columnconfigure(2, weight=0)

        self.status_label = ctk.CTkLabel(self.widget, text="입력 대기 중", font=self.font, anchor="w")
        self.status_label.grid(row=0, column=0, padx=(10, 5), pady=5, sticky="ew")
        
        self.progressbar = ctk.CTkProgressBar(self.widget, width=200)
        self.progressbar.grid(row=0, column=1, padx=(5, 5), pady=5, sticky="e")
        self.progressbar.set(0)
        
        self.save_button = ctk.CTkButton(
            self.widget,
            text="결과 저장",
            width=90,
            command=self._save_command,
            state="disabled",
            font=self.font
        )
        self.save_button.grid(row=0, column=1, padx=(5, 10), pady=5, sticky="e")
        
        self.cancel_button = ctk.CTkButton(self.widget, text="취소", width=60, state="disabled", font=self.font)
        self.cancel_button.grid(row=0, column=2, padx=(5, 10), pady=5, sticky="e")
    
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
        self.progressbar.configure(mode="determinate")
        self.progressbar.set(value)
    
    def set_busy(self, status_text: Optional[str] = None):
        """바쁨 상태로 설정 (진행바, 취소 버튼 표시)"""
        if status_text:
            self.status_label.configure(text=status_text)
        else:
            self.status_label.configure(text="처리 중...")

        self.save_button.grid_forget()

        self.progressbar.grid(row=0, column=1, padx=(5, 5), pady=5, sticky="e")
        self.progressbar.configure(mode="indeterminate")
        self.progressbar.start()

        self.cancel_button.configure(state="normal")
        self.cancel_button.grid(row=0, column=2, padx=(5, 10), pady=5, sticky="e")
    
    def set_ready(self, status_text: str = "입력 대기 중", show_save_button: bool = False):
        """준비 상태로 설정 (진행바, 취소 버튼 숨김, 조건부 저장 버튼 표시)"""
        self.status_label.configure(text=status_text)

        self.progressbar.grid_forget()
        self.cancel_button.grid_forget()
        self.save_button.grid_forget()

        self.progressbar.stop()
        self.progressbar.configure(mode="determinate")
        self.progressbar.set(0)

        self.cancel_button.configure(state="disabled")

        if show_save_button:
            self.save_button.configure(state="normal")
            self.save_button.grid(row=0, column=1, padx=(5, 10), pady=5, sticky="e")
        else:
            self.save_button.configure(state="disabled")
    
    def set_save_command(self, command: Callable):
        """'결과 저장' 버튼의 명령(콜백 함수)을 설정합니다."""
        self._save_command = command
        self.save_button.configure(command=self._save_command)
    
    def set_cancel_command(self, command: Callable):
        """취소 버튼 명령 설정"""
        self.cancel_button.configure(command=command) 