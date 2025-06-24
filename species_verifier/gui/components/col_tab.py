"""
통합생물(COL) 탭 프레임 컴포넌트

통합생물 검증을 위한 사용자 인터페이스 탭 컴포넌트를 정의합니다.
"""
import os
import tkinter as tk
from tkinter import filedialog
from typing import Optional, Callable, Dict, Any, List
import customtkinter as ctk
import pandas as pd

from species_verifier.gui.components.base import BaseTabFrame
from species_verifier.utils.helpers import calculate_file_entries

class ColTabFrame(BaseTabFrame):
    """통합생물(COL) 탭 프레임 컴포넌트"""
    def __init__(
        self,
        parent: Any,
        font: Any,
        bold_font: Any,
        placeholder_text: str = "통합생물 이름을 입력하세요 (쉼표나 줄바꿈으로 구분)",
        max_file_processing_limit: int = 3000,
        max_direct_input_limit: int = 20,  # 직접 입력 한계 추가
        direct_export_threshold: int = 100,
        **kwargs
    ):
        self.font = font
        self.bold_font = bold_font
        self.placeholder_text = placeholder_text
        self.max_file_processing_limit = max_file_processing_limit
        self.max_direct_input_limit = max_direct_input_limit  # 직접 입력 한계 저장
        self.direct_export_threshold = direct_export_threshold
        self.entry_var = tk.StringVar()
        self.file_path_var = tk.StringVar()
        self.entry = None
        self.file_path_entry = None
        self.verify_button = None
        self.file_browse_button = None
        self.file_clear_button = None
        self.initial_text = placeholder_text
        self._callbacks = {}
        self.text_entry_count = 0
        self.file_entry_count = 0
        self.text_count_label = None
        self.file_count_label = None
        super().__init__(parent, **kwargs)
        self.tab_name = "담수 등 전체생물(COL)"
        self._create_widgets()

    def set_callbacks(self, **callbacks):
        """
        콜백 함수 등록 (on_search, on_file_browse, on_file_search)
        """
        for event_name, callback in callbacks.items():
            self._callbacks[event_name] = callback

    def _trigger_callback(self, event_name, *args, **kwargs):
        cb = self._callbacks.get(event_name)
        if cb:
            cb(*args, **kwargs)

    def _create_widgets(self, **kwargs):
        """위젯 생성 및 배치 - 개선된 디자인"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0) 
        self.grid_rowconfigure(1, weight=0) 
        self.grid_rowconfigure(2, weight=0) 
        
        # 1. 직접 입력 섹션 (배경 프레임 추가)
        direct_input_section = ctk.CTkFrame(self, corner_radius=8)
        direct_input_section.grid(row=0, column=0, sticky="ew", padx=15, pady=(10, 8))
        direct_input_section.grid_columnconfigure(0, weight=1)
        
        # 직접 입력 헤더
        header_frame = ctk.CTkFrame(direct_input_section, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 8))
        header_frame.grid_columnconfigure(0, weight=0)
        header_frame.grid_columnconfigure(1, weight=1)
        header_frame.grid_columnconfigure(2, weight=0)

        ctk.CTkLabel(
            header_frame,
            text="🌍 직접 입력",
            font=ctk.CTkFont(family="Malgun Gothic", size=14, weight="bold"),
            text_color=("#1f538d", "#4a9eff")
        ).grid(row=0, column=0, sticky="w")

        self.text_count_label = ctk.CTkLabel(
            header_frame,
            text="",
            font=ctk.CTkFont(family="Malgun Gothic", size=11),
            text_color=("gray60", "gray40")
        )
        self.text_count_label.grid(row=0, column=2, sticky="e")

        # 텍스트 입력 필드 (높이 증가)
        self.entry = ctk.CTkTextbox(
            direct_input_section,
            height=80,
            font=self.font,
            corner_radius=6,
            border_width=1
        )
        self.entry.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 15))
        self.entry.insert("0.0", self.initial_text)
        self.entry.configure(text_color="gray")
        self.entry.bind("<FocusIn>", self._on_entry_focus_in)
        self.entry.bind("<FocusOut>", self._on_entry_focus_out)
        self.entry.bind("<KeyRelease>", self._update_input_count)

        # 2. 파일 입력 섹션 (배경 프레임 추가)
        file_input_section = ctk.CTkFrame(self, corner_radius=8)
        file_input_section.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 15))
        file_input_section.grid_columnconfigure(0, weight=1)

        # 파일 입력 헤더
        file_header_frame = ctk.CTkFrame(file_input_section, fg_color="transparent")
        file_header_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 8))
        file_header_frame.grid_columnconfigure(0, weight=0)
        file_header_frame.grid_columnconfigure(1, weight=1)
        file_header_frame.grid_columnconfigure(2, weight=0)

        ctk.CTkLabel(
            file_header_frame,
            text="📁 파일 입력",
            font=ctk.CTkFont(family="Malgun Gothic", size=14, weight="bold"),
            text_color=("#1f538d", "#4a9eff")
        ).grid(row=0, column=0, sticky="w")

        self.file_count_label = ctk.CTkLabel(
            file_header_frame,
            text="",
            font=ctk.CTkFont(family="Malgun Gothic", size=11),
            text_color=("gray60", "gray40")
        )
        self.file_count_label.grid(row=0, column=2, sticky="e")

        # 파일 입력 컨트롤
        file_controls_frame = ctk.CTkFrame(file_input_section, fg_color="transparent")
        file_controls_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 15))
        file_controls_frame.grid_columnconfigure(0, weight=1)

        self.file_path_entry = ctk.CTkEntry(
            file_controls_frame,
            textvariable=self.file_path_var,
            font=self.font,
            placeholder_text="파일을 선택하세요... (CSV, XLSX, TXT 지원)",
            state="readonly",
            height=35,
            corner_radius=6
        )
        self.file_path_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        # 버튼 컨테이너
        button_frame = ctk.CTkFrame(file_controls_frame, fg_color="transparent")
        button_frame.grid(row=0, column=1)

        self.file_browse_button = ctk.CTkButton(
            button_frame,
            text="📂 찾기",
            width=80,
            height=35,
            font=ctk.CTkFont(family="Malgun Gothic", size=12, weight="bold"),
            corner_radius=6,
            command=self._on_file_browse_click
        )
        self.file_browse_button.grid(row=0, column=0, padx=(0, 5))

        self.file_clear_button = ctk.CTkButton(
            button_frame,
            text="🗑️ 지우기",
            width=80,
            height=35,
            font=ctk.CTkFont(family="Malgun Gothic", size=12, weight="bold"),
            corner_radius=6,
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray40"),
            command=self._on_file_clear_click
        )
        self.file_clear_button.grid(row=0, column=1)

        self.file_path_var.trace_add("write", self._update_input_count)

        # 3. 검증 버튼 (적당한 크기로 중앙 배치)
        self.verify_button = ctk.CTkButton(
            self,
            text="🔍 검증 시작",
            font=ctk.CTkFont(family="Malgun Gothic", size=16, weight="bold"),
            width=200,
            height=45,
            corner_radius=8,
            fg_color=("#1f538d", "#4a9eff"),
            hover_color=("#174a7a", "#3d8ae6"),
            command=self._trigger_verify_callback,
            state="disabled"
        )
        self.verify_button.grid(row=2, column=0, pady=(0, 15))
        self._update_input_count()

    def _update_input_count(self, *args):
        """입력된 텍스트 및 파일의 항목 개수를 계산하고 UI를 업데이트합니다."""
        # 1. 텍스트 입력 개수 계산
        current_text = self.entry.get("0.0", "end-1c")
        if current_text and current_text != self.initial_text:
            # 쉼표 또는 줄바꿈으로 분리하고 빈 항목 제거 후 개수 세기
            entries = [entry.strip() for entry in current_text.replace("\n", ",").split(",") if entry.strip()]
            self.text_entry_count = len(entries)
        else:
            self.text_entry_count = 0
            
        # 2. 파일 입력 개수는 self.file_entry_count 사용 (파일 선택/지우기 시 업데이트됨)
        file_count = self.file_entry_count
        
        # 3. 레이블 텍스트 생성 및 업데이트 (개별적으로)
        text_count_str = f"학명 개수 {self.text_entry_count}개" if self.text_entry_count > 0 else ""
        file_count_str = f"학명 개수 {file_count}개" if file_count > 0 else ""
        
        # 직접 입력 개수 제한 확인
        if self.text_entry_count > self.max_direct_input_limit:
            text_count_str = f"학명 개수 {self.text_entry_count}개 (최대 {self.max_direct_input_limit}개)"
            if self.text_count_label:
                self.text_count_label.configure(text=text_count_str, text_color=("red", "red"))
            is_text_valid = False  # 개수 초과로 입력 무효화
        else:
            if self.text_count_label:
                self.text_count_label.configure(text=text_count_str, text_color=("black", "white"))
            is_text_valid = self.text_entry_count > 0
        
        # 파일 개수 표시 업데이트
        if self.file_count_label:
            self.file_count_label.configure(text=file_count_str)
             
        # 5. 검증 버튼 상태 업데이트
        is_file_valid = file_count > 0
        if is_text_valid or is_file_valid:
            self.verify_button.configure(state="normal")
        else:
            self.verify_button.configure(state="disabled")

    def _calculate_file_entries(self, file_path: str) -> int:
        """주어진 파일 경로에서 항목 개수를 추정합니다. (첫 번째 열 기준)"""
        return calculate_file_entries(file_path, "Col")

    def _on_entry_focus_in(self, event=None):
        if self.entry.get("0.0", "end-1c") == self.initial_text:
            self.entry.delete("0.0", tk.END)
            self.entry.configure(text_color=("black", "white"))
        self._update_input_count()

    def _on_entry_focus_out(self, event=None):
        current_text = self.entry.get("0.0", "end-1c")
        if not current_text.strip():
            self.entry.delete("0.0", tk.END)
            self.entry.insert("0.0", self.initial_text)
            self.entry.configure(text_color="gray")
        self._update_input_count()

    def _on_file_browse_click(self):
        """파일 찾기 버튼 클릭 시 파일 처리 콜백 호출"""
        print("[Debug COL] 파일 찾기 버튼 클릭. 'on_col_file_browse' 콜백 트리거.")
        self.trigger_callback("on_col_file_browse")

    def _on_file_clear_click(self):
        """파일 지우기 버튼 클릭 이벤트 처리"""
        self.file_entry_count = 0
        self.file_path_var.set("")
        self._update_input_count()

    def _trigger_verify_callback(self):
        """검증 시작 버튼 클릭 시 항상 on_search 콜백 호출"""
        print("[Debug COL] 검증 버튼 클릭됨")
        text_input = self.entry.get("0.0", "end-1c").strip()
        
        # 'on_search' 콜백은 app._search_species를 호출합니다.
        # 이 함수는 파일에서 로드된 데이터가 있는지 먼저 확인하고, 
        # 없으면 텍스트 입력을 사용합니다.
        print("[Debug COL] 'on_search' 콜백 트리거 (tab=col)")
        self.trigger_callback("on_search", text_input, "col")

    def set_selected_file(self, file_path: str):
        """app.py에서 파일 경로와 항목 수를 설정하기 위해 호출하는 함수"""
        if file_path and os.path.exists(file_path):
            self.file_path_var.set(file_path)
        else:
            self.file_path_var.set("")

    def reset_file_info(self):
        """취소 시 파일 정보 초기화"""
        # 파일 경로와 개수 초기화
        self.file_path_var.set("")
        self.file_entry_count = 0
        self._update_input_count()
