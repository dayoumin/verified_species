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

class ColTabFrame(BaseTabFrame):
    """통합생물(COL) 탭 프레임 컴포넌트"""
    def __init__(
        self,
        parent: Any,
        font: Any,
        bold_font: Any,
        placeholder_text: str = "통합생물 이름을 입력하세요 (쉼표나 줄바꿈으로 구분)",
        max_file_processing_limit: int = 1000,
        direct_export_threshold: int = 100,
        **kwargs
    ):
        print("[DEBUG] ColTabFrame.__init__ 진입")
        self.font = font
        self.bold_font = bold_font
        self.placeholder_text = placeholder_text
        self.max_file_processing_limit = max_file_processing_limit
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
        self.tab_name = "통합생물(COL)"
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
        print("[DEBUG] ColTabFrame._create_widgets 진입")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=0)
        self.grid_rowconfigure(4, weight=0)

        # 1. 직접 입력 레이블 + 개수 프레임
        text_label_frame = ctk.CTkFrame(self, fg_color="transparent")
        text_label_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(5, 2))
        text_label_frame.grid_columnconfigure(0, weight=0)
        text_label_frame.grid_columnconfigure(1, weight=0)
        text_label_frame.grid_columnconfigure(2, weight=1)

        ctk.CTkLabel(
            text_label_frame,
            text="직접 입력",
            font=self.bold_font
        ).grid(row=0, column=0, sticky="w")

        self.text_count_label = ctk.CTkLabel(
             text_label_frame,
             text="",
             font=ctk.CTkFont(family="Malgun Gothic", size=10),
             anchor="w"
        )
        self.text_count_label.grid(row=0, column=1, sticky="w", padx=(5, 0))

        # 2. 텍스트 입력 필드 (Restore columnspan)
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
        self.entry.bind("<KeyRelease>", self._update_input_count)

        # 3. 파일 입력 레이블 + 개수 프레임
        file_label_frame = ctk.CTkFrame(self, fg_color="transparent")
        file_label_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(5, 2))
        file_label_frame.grid_columnconfigure(0, weight=0)
        file_label_frame.grid_columnconfigure(1, weight=0)
        file_label_frame.grid_columnconfigure(2, weight=1)

        ctk.CTkLabel(
            file_label_frame,
            text="파일 입력",
            font=self.bold_font
        ).grid(row=0, column=0, sticky="w")

        self.file_count_label = ctk.CTkLabel(
             file_label_frame,
             text="",
             font=ctk.CTkFont(family="Malgun Gothic", size=10),
             anchor="w"
        )
        self.file_count_label.grid(row=0, column=1, sticky="w", padx=(5, 0))

        # 4. 파일 입력 프레임 (Restore columnspan and internal layout)
        file_frame = ctk.CTkFrame(self)
        file_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=2)
        file_frame.grid_columnconfigure(0, weight=1)
        file_frame.grid_columnconfigure(1, weight=0)
        file_frame.grid_columnconfigure(2, weight=0)

        self.file_path_entry = ctk.CTkEntry(file_frame, textvariable=self.file_path_var, font=self.font, state="readonly")
        self.file_path_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        self.file_browse_button = ctk.CTkButton(file_frame, text="찾기", font=self.font, width=60, command=self._on_file_browse_click)
        self.file_browse_button.grid(row=0, column=1, padx=(0, 5))

        self.file_clear_button = ctk.CTkButton(file_frame, text="지우기", font=self.font, width=60, command=self._on_file_clear_click)
        self.file_clear_button.grid(row=0, column=2, padx=(0, 0))

        self.file_path_var.trace_add("write", self._update_input_count)

        # 5. 검증 버튼 (Restore columnspan and adjust row)
        self.verify_button = ctk.CTkButton(
            self,
            text="검증",
            font=self.bold_font,
            command=self._trigger_verify_callback,
            state="disabled"
        )
        self.verify_button.grid(row=4, column=0, pady=(5, 10))
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
        
        if self.text_count_label:
            self.text_count_label.configure(text=text_count_str)
        if self.file_count_label:
            self.file_count_label.configure(text=file_count_str)
             
        # 5. 검증 버튼 상태 업데이트
        is_text_valid = self.text_entry_count > 0
        is_file_valid = file_count > 0
        if is_text_valid or is_file_valid:
            self.verify_button.configure(state="normal")
        else:
            self.verify_button.configure(state="disabled")

    def _calculate_file_entries(self, file_path: str) -> int:
        """주어진 파일 경로에서 항목 개수를 추정합니다. (첫 번째 열 기준)"""
        if not file_path or not os.path.exists(file_path):
            return 0
            
        count = 0
        try:
            ext = os.path.splitext(file_path)[1].lower()
            if ext == '.csv':
                df = pd.read_csv(file_path, header=None, usecols=[0], skipinitialspace=True)
                count = df[0].notna().sum()
            elif ext == '.xlsx':
                df = pd.read_excel(file_path, header=None, usecols=[0])
                count = df[0].notna().sum()
            elif ext == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = [line.strip() for line in f if line.strip()] # 비어있지 않은 줄만 계산
                    count = len(lines)
            else:
                print(f"[Warning Col] Unsupported file type for count estimation: {ext}")
                # 지원하지 않는 형식은 0 반환 또는 다른 방식 고려
                
        except pd.errors.EmptyDataError:
            print(f"[Info Col] File is empty: {file_path}")
            count = 0 # 빈 파일
        except Exception as e:
            print(f"[Error Col] Failed to estimate entries in file {file_path}: {e}")
            # 오류 발생 시 0 반환 (또는 사용자에게 알림)
            count = 0 
            
        print(f"[Debug Col] Estimated entries in file {os.path.basename(file_path)}: {count}")
        return count

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
        file_path = filedialog.askopenfilename(
            title="통합생물 목록 파일 선택",
            filetypes=[
                ("Excel 파일", "*.xlsx"),
                ("CSV 파일", "*.csv"),
                ("텍스트 파일", "*.txt"),
                ("모든 파일", "*.*")
            ]
        )
        if file_path:
            # 파일 선택 시 개수 계산 및 저장
            self.file_entry_count = self._calculate_file_entries(file_path)
            self.file_path_var.set(file_path)
            self._trigger_callback("on_file_browse", file_path)
        else:
            # 파일 선택 취소 시
            self.file_entry_count = 0
            self.file_path_var.set("")
            
        # 공통 업데이트 함수 호출
        self._update_input_count()

    def _on_file_clear_click(self):
        self.file_entry_count = 0 # 파일 개수 리셋
        self.file_path_var.set("")
        self._update_input_count()

    def _trigger_verify_callback(self):
        text = self.entry.get("0.0", "end-1c").strip()
        file_path = self.file_path_var.get()
        if text and text != self.initial_text:
            self._trigger_callback("on_search", text, "col")
        elif file_path and os.path.exists(file_path):
            self._trigger_callback("on_file_search", file_path, "col")
        else:
            print("[Warning COL] Verify button clicked but no valid input found.")

    def set_selected_file(self, file_path: Optional[str]):
        self.file_path_var.set(file_path or "")
        # 파일 경로가 외부에서 설정될 때도 개수 업데이트
        if file_path and os.path.exists(file_path):
            self.file_entry_count = self._calculate_file_entries(file_path)
        else:
            self.file_entry_count = 0
        self._update_input_count()
