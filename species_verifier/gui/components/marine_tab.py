"""
해양생물 탭 프레임 컴포넌트

해양생물 검증을 위한 사용자 인터페이스 탭 컴포넌트를 정의합니다.
"""
import os
import tkinter as tk
from tkinter import filedialog
from typing import Optional, Callable, Dict, Any, List
import customtkinter as ctk

from species_verifier.gui.components.base import BaseTabFrame


class MarineTabFrame(BaseTabFrame):
    """해양생물 탭 프레임 컴포넌트"""
    
    def __init__(
        self,
        parent: Any,
        font: Any,
        bold_font: Any,
        placeholder_text: str = "해양 생물 이름을 입력하세요 (쉼표나 줄바꿈으로 구분)",
        max_file_processing_limit: int = 1000,
        direct_export_threshold: int = 100,
        **kwargs
    ):
        """
        초기화
        
        Args:
            parent: 부모 위젯 (탭뷰의 탭)
            font: 기본 폰트
            bold_font: 굵은 폰트
            placeholder_text: 입력 필드 기본 텍스트
            max_file_processing_limit: 최대 파일 처리 한도
            direct_export_threshold: 직접 내보내기 임계값
            **kwargs: 추가 인자
        """
        self.font = font
        self.bold_font = bold_font
        self.placeholder_text = placeholder_text
        self.max_file_processing_limit = max_file_processing_limit
        self.direct_export_threshold = direct_export_threshold
        
        # 입력 프레임 초기화
        self.entry_var = tk.StringVar()
        self.file_path_var = tk.StringVar()
        
        # 위젯 참조 보관
        self.entry = None
        self.file_path_entry = None
        self.verify_button = None
        self.file_browse_button = None
        
        # 초기값 설정
        self.initial_text = placeholder_text
        
        # BaseTabFrame 초기화 (parent 전달)
        super().__init__(parent, **kwargs) 
        self.tab_name = "해양생물"
        # self.widget은 BaseTabFrame에서 parent로 자동 설정됨

    def _create_widgets(self, **kwargs):
        """위젯 생성 및 배치 (하나의 프레임 안에 grid 사용)"""
        
        self.grid_columnconfigure(0, weight=1)
        # 행 간격 조정
        self.grid_rowconfigure(0, weight=0) 
        self.grid_rowconfigure(1, weight=0) 
        self.grid_rowconfigure(2, weight=0) 
        self.grid_rowconfigure(3, weight=0) 
        self.grid_rowconfigure(4, weight=0) 
        
        # 1. 직접 입력 레이블 (pady 수정)
        ctk.CTkLabel(
            self,
            text="직접 입력:",
            font=self.bold_font
        ).grid(row=0, column=0, sticky=tk.W, padx=10, pady=(5, 2)) # pady 상단 줄임

        # 2. 텍스트 입력 필드 (pady 수정)
        self.entry = ctk.CTkTextbox(
            self,
            height=60, 
            font=self.font,
        )
        self.entry.grid(row=1, column=0, sticky="ew", padx=10, pady=2)
        self.entry.insert("0.0", self.initial_text)
        self.entry.configure(text_color="gray")
        
        self.entry.bind("<FocusIn>", self._on_entry_focus_in)
        self.entry.bind("<FocusOut>", self._on_entry_focus_out)
        self.entry.bind("<KeyRelease>", self._update_verify_button_state)

        # 3. 파일 입력 레이블 (pady 수정)
        ctk.CTkLabel(
            self,
            text="파일 입력",
            font=self.bold_font
        ).grid(row=2, column=0, sticky=tk.W, padx=10, pady=(5, 2)) # pady 상단 줄임

        # 4. 파일 입력 프레임 (pady 수정)
        file_input_frame = ctk.CTkFrame(self)
        file_input_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=2)
        file_input_frame.grid_columnconfigure(0, weight=1)

        self.file_path_entry = ctk.CTkEntry(
            file_input_frame,
            textvariable=self.file_path_var,
            font=self.font,
            placeholder_text="파일 경로...",
            state="readonly"
        )
        self.file_path_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5), pady=2) # 프레임 내부 pady

        self.file_browse_button = ctk.CTkButton(
            file_input_frame,
            text="찾기",
            width=60,
            font=self.font,
            command=self._on_file_browse_click
        )
        self.file_browse_button.grid(row=0, column=1, padx=(0, 0), pady=2) # 프레임 내부 pady
        
        self.file_path_var.trace_add("write", self._update_verify_button_state)

        # 5. 통합 검증 버튼 (pady 수정)
        self.verify_button = ctk.CTkButton(
            self,
            text="검증",
            font=self.bold_font,
            command=self._on_verify_click, 
            state="disabled"
        )
        self.verify_button.grid(row=4, column=0, pady=(5, 5)) # pady 상하단 줄임
        
        self._update_verify_button_state()

    def _on_entry_focus_in(self, event=None):
        """입력 필드 포커스인 이벤트 처리"""
        if self.entry.get("0.0", "end-1c") == self.initial_text:
            self.entry.delete("0.0", tk.END)
            self.entry.configure(text_color=("black", "white"))
        self._update_verify_button_state()

    def _on_entry_focus_out(self, event=None):
        """입력 필드 포커스아웃 이벤트 처리"""
        current_text = self.entry.get("0.0", "end-1c")
        if not current_text.strip():
            self.entry.delete("0.0", tk.END)
            self.entry.insert("0.0", self.initial_text)
            self.entry.configure(text_color="gray")
        self._update_verify_button_state()
    
    def _on_file_browse_click(self):
        """파일 찾기 버튼 클릭 이벤트 처리"""
        file_path = filedialog.askopenfilename(
            title="생물종 목록 파일 선택",
            filetypes=[
                ("Excel 파일", "*.xlsx"),
                ("CSV 파일", "*.csv"),
                ("텍스트 파일", "*.txt"),
                ("모든 파일", "*.*")
            ]
        )
        if file_path:
            self.file_path_var.set(file_path)
        else:
            self.file_path_var.set("")
            self._update_verify_button_state()

    def _on_verify_click(self):
        """통합 검증 버튼 클릭 이벤트 처리"""
        text = self.entry.get("0.0", "end-1c").strip()
        file_path = self.file_path_var.get()

        if text and text != self.initial_text:
            print(f"[Debug Marine] Triggering on_search with text: {text[:50]}...")
            self.trigger_callback("on_search", text, "marine")
        elif file_path and os.path.exists(file_path):
            print(f"[Debug Marine] Triggering on_file_search with path: {file_path}")
            self.trigger_callback("on_file_search", file_path, "marine")
        else:
            print("[Warning Marine] Verify button clicked but no valid input found.")

    def _update_verify_button_state(self, *args):
        """검증 버튼 활성화/비활성화 상태 업데이트"""
        text_input = self.entry.get("0.0", "end-1c").strip()
        file_input = self.file_path_var.get()
        
        is_text_valid = text_input and text_input != self.initial_text
        is_file_valid = file_input and os.path.exists(file_input)

        if is_text_valid or is_file_valid:
            self.verify_button.configure(state="normal")
        else:
            self.verify_button.configure(state="disabled")

    def focus_entry(self):
        """입력 필드에 포커스 설정"""
        if self.entry:
            self.entry.focus_set()
            
    def set_callbacks(self, **callbacks):
        """
        콜백 함수 등록
        """
        for event_name, callback in callbacks.items():
            self.register_callback(event_name, callback)