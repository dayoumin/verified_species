"""
미생물 검증을 위한 사용자 인터페이스 탭 컴포넌트

미생물 이름 검증을 위한 입력 컴포넌트를 제공합니다.
"""
import os
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
from typing import Optional, Callable, Dict, Any, List
import pandas as pd
import time

from species_verifier.gui.components.base import BaseTabFrame


class MicrobeTabFrame(BaseTabFrame):
    """미생물 검증을 위한 탭 프레임 컴포넌트"""
    
    def __init__(
        self,
        parent: Any,
        font: Any,
        bold_font: Any,
        placeholder_text: str = "미생물 이름을 입력하세요 (쉼표나 줄바꿈으로 구분)",
        max_file_processing_limit: int = 1000,
        max_direct_input_limit: int = 20,  # 직접 입력 한계 추가
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
            max_direct_input_limit: 직접 입력 최대 항목 수
            direct_export_threshold: 직접 내보내기 임계값
            **kwargs: 추가 인자
        """
        self.font = font
        self.bold_font = bold_font
        self.placeholder_text = placeholder_text
        self.max_file_processing_limit = max_file_processing_limit
        self.max_direct_input_limit = max_direct_input_limit  # 직접 입력 한계 저장
        self.direct_export_threshold = direct_export_threshold
        
        # 입력 프레임 초기화
        self.entry_var = tk.StringVar()
        self.file_path_var = tk.StringVar()
        
        # 위젯 참조 보관
        self.entry = None
        self.file_path_entry = None
        self.verify_button = None
        self.file_browse_button = None
        self.file_clear_button = None
        
        # 초기값 설정
        self.initial_text = placeholder_text
        
        # 학명 개수 표시를 위한 변수 추가
        self.text_entry_count = 0
        self.file_entry_count = 0
        self.text_count_label = None
        self.file_count_label = None
        
        # BaseTabFrame 초기화 (parent 전달)
        super().__init__(parent, **kwargs)
        self.tab_name = "미생물 (LPSN)"

    def _create_widgets(self, **kwargs):
        """위젯 생성 및 배치"""
        self.grid_columnconfigure(0, weight=1)
        # 행 간격 조정
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

        # 2. 텍스트 입력 필드
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

        # 4. 파일 입력 프레임
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
            font=self.bold_font,
            command=self._on_file_browse_click
        )
        self.file_browse_button.grid(row=0, column=1, padx=(0, 0), pady=2) # 프레임 내부 pady
        
        self.file_clear_button = ctk.CTkButton(
            file_input_frame,
            text="지우기",
            width=60,
            font=self.bold_font,
            command=self._on_file_clear_click
        )
        self.file_clear_button.grid(row=0, column=2, padx=(2, 0), pady=2) # 프레임 내부 pady
        
        self.file_path_var.trace_add("write", self._update_input_count)

        # 5. 통합 검증 버튼
        self.verify_button = ctk.CTkButton(
            self,
            text="검증",
            font=self.bold_font,
            command=self._on_verify_click,
            state="disabled"
        )
        self.verify_button.grid(row=4, column=0, pady=(5, 5))
        
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
            
        # 2. 파일 입력 개수 사용
        file_count = self.file_entry_count
        
        # 3. 레이블 텍스트 생성 및 업데이트
        text_count_str = f"학명 개수 {self.text_entry_count}개" if self.text_entry_count > 0 else ""
        file_count_str = f"학명 개수 {file_count}개" if file_count > 0 else ""
        
        # 직접 입력 개수 제한 확인
        if self.text_entry_count > self.max_direct_input_limit:
            text_count_str = f"학명 개수 {self.text_entry_count}개 (최대 {self.max_direct_input_limit}개)"
            if hasattr(self, 'text_count_label') and self.text_count_label:
                self.text_count_label.configure(text=text_count_str, text_color=("red", "red"))
            is_text_valid = False  # 개수 초과로 입력 무효화
        else:
            if hasattr(self, 'text_count_label') and self.text_count_label:
                self.text_count_label.configure(text=text_count_str, text_color=("black", "white"))
            is_text_valid = self.text_entry_count > 0
            
        # 파일 개수 업데이트
        if hasattr(self, 'file_count_label') and self.file_count_label:
            self.file_count_label.configure(text=file_count_str)
            
        # 4. 검증 버튼 상태 업데이트
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
                print(f"[Warning Microbe] Unsupported file type for count estimation: {ext}")
                # 지원하지 않는 형식은 0 반환 또는 다른 방식 고려
                
        except pd.errors.EmptyDataError:
            print(f"[Info Microbe] File is empty: {file_path}")
            count = 0 # 빈 파일
        except Exception as e:
            print(f"[Error Microbe] Failed to estimate entries in file {file_path}: {e}")
            # 오류 발생 시 0 반환 (또는 사용자에게 알림)
            count = 0 
            
        print(f"[Debug Microbe] Estimated entries in file {os.path.basename(file_path)}: {count}")
        return count

    def _on_entry_focus_in(self, event=None):
        """입력 필드 포커스인 이벤트 처리"""
        if self.entry.get("0.0", "end-1c") == self.initial_text:
            self.entry.delete("0.0", tk.END)
            self.entry.configure(text_color=("black", "white"))
        self._update_input_count()

    def _on_entry_focus_out(self, event=None):
        """입력 필드 포커스아웃 이벤트 처리"""
        current_text = self.entry.get("0.0", "end-1c")
        if not current_text.strip():
            self.entry.delete("0.0", tk.END)
            self.entry.insert("0.0", self.initial_text)
            self.entry.configure(text_color="gray")
        self._update_input_count()
    
    def _on_file_browse_click(self):
        """파일 찾기 버튼 클릭 이벤트 처리"""
        file_path = filedialog.askopenfilename(
            title="미생물 목록 파일 선택",
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
            self._update_input_count()
        else:
            self.file_path_var.set("")
            self.file_entry_count = 0
            self._update_input_count()

    def _on_file_clear_click(self):
        """파일 지우기 버튼 클릭 이벤트 처리"""
        self.file_path_var.set("")
        self.file_entry_count = 0
        self._update_input_count()

    def _on_verify_click(self):
        """통합 검증 버튼 클릭 이벤트 처리"""
        text = self.entry.get("0.0", "end-1c").strip()
        file_path = self.file_path_var.get()

        if text and text != self.initial_text:
            print(f"[Debug Microbe] Triggering on_search with text: {text[:50]}...") # 디버그
            self.trigger_callback("on_search", text, "microbe")
        elif file_path and os.path.exists(file_path):
            print(f"[Debug Microbe] Triggering on_file_search with path: {file_path}") # 디버그
            self.trigger_callback("on_file_search", file_path, "microbe")
        else:
            print("[Warning Microbe] Verify button clicked but no valid input found.")

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

    def set_input_state(self, state: str):
        """탭 내 입력 관련 위젯들의 상태를 설정합니다."""
        # state는 tk.NORMAL 또는 tk.DISABLED 여야 합니다.
        # CTkTextbox 상태 변경 (CTkEntry와 동일하게 state 사용)
        if self.entry:
            self.entry.configure(state=state)

        # 파일 경로 엔트리 (읽기 전용이지만 시각적/기능적 상태 변경 가능)
        # if self.file_path_entry:
        #     self.file_path_entry.configure(state=state) # 읽기 전용이므로 상태 변경 불필요할 수 있음

        # 파일 찾기 버튼
        if self.file_browse_button:
            self.file_browse_button.configure(state=state)

        # 검증 버튼 (전체적인 활성화/비활성화 제어)
        # 세부적인 활성화는 _update_verify_button_state에서 관리
        if self.verify_button:
            if state == tk.DISABLED:
                self.verify_button.configure(state=tk.DISABLED)
            else:
                # normal 상태일 때는 _update_verify_button_state가 실제 상태 결정
                self._update_verify_button_state()

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
            
    def set_selected_file(self, file_path: Optional[str]):
        """선택된 파일 설정"""
        if file_path:
            self.file_entry_count = self._calculate_file_entries(file_path)
            self.file_path_var.set(file_path)
        else:
            self.file_entry_count = 0
            self.file_path_var.set("")
        self._update_input_count()

    def reset_file_info(self):
        """파일 정보 초기화 - 취소 시 호출됨"""
        # 파일 경로 초기화
        self.file_path_var.set("")
        # 파일 항목 개수 초기화
        self.file_entry_count = 0
        # 파일 개수 레이블 초기화
        if hasattr(self, 'file_count_label') and self.file_count_label:
            self.file_count_label.configure(text="")
        # 검증 버튼 상태 업데이트
        self._update_verify_button_state()

    def _perform_microbe_verification_with_sleep(self, names_list):
        batch_size = 5  # 배치 크기
        for i in range(0, len(names_list), batch_size):
            batch = names_list[i:i+batch_size]
            # 배치 처리
            for name in batch:
                result = verify_microbe_species(name)
                self.result_queue.put((result, 'microbe'))
            
            # 배치 간 대기
            progress = min(1.0, (i + batch_size) / len(names_list))
            self.update_progress(progress)
            time.sleep(1.0)  # 1초 대기