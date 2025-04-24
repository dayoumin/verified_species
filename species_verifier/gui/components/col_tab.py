"""
통합생물(COL) 탭 프레임 컴포넌트

통합생물 검증을 위한 사용자 인터페이스 탭 컴포넌트를 정의합니다.
"""
import os
import tkinter as tk
from tkinter import filedialog
from typing import Optional, Callable, Dict, Any, List
import customtkinter as ctk

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
        self.grid_rowconfigure(5, weight=1)

        # 1. 직접 입력 레이블
        ctk.CTkLabel(
            self,
            text="직접 입력:",
            font=self.bold_font
        ).grid(row=0, column=0, sticky=tk.W, padx=10, pady=(5, 2))

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
        self.entry.bind("<KeyRelease>", self._update_verify_button_state)

        # 3. 파일 입력 레이블
        ctk.CTkLabel(
            self,
            text="파일 입력",
            font=self.bold_font
        ).grid(row=2, column=0, sticky=tk.W, padx=10, pady=(5, 2))

        # 4. 파일 입력 프레임
        file_frame = ctk.CTkFrame(self)
        file_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=2)
        file_frame.grid_columnconfigure(0, weight=1)
        self.file_path_entry = ctk.CTkEntry(file_frame, textvariable=self.file_path_var, font=self.font, width=260, state="readonly")
        self.file_path_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.file_browse_button = ctk.CTkButton(file_frame, text="찾기", font=self.font, width=60, command=self._on_file_browse_click)
        self.file_browse_button.grid(row=0, column=1, padx=(0, 0))
        self.file_clear_button = ctk.CTkButton(file_frame, text="지우기", font=self.font, width=60, command=self._on_file_clear_click)
        self.file_clear_button.grid(row=0, column=2, padx=(2, 0))
        self.file_path_var.trace_add("write", self._update_verify_button_state)

        # 5. 검증 버튼
        self.verify_button = ctk.CTkButton(
            self,
            text="검증",
            font=self.bold_font,
            command=self._on_verify_click,
            state="disabled"
        )
        self.verify_button.grid(row=4, column=0, pady=(5, 5))
        self._update_verify_button_state()

        # 6. 결과 테이블(트리뷰)
        import tkinter.ttk as ttk
        self.result_tree = ttk.Treeview(self, columns=("학명", "검증", "COL 상태", "COL ID", "COL URL", "위키백과 요약"), show="headings")
        for col in ("학명", "검증", "COL 상태", "COL ID", "COL URL", "위키백과 요약"):
            self.result_tree.heading(col, text=col)
            self.result_tree.column(col, width=100, anchor="center")
        self.result_tree.grid(row=5, column=0, sticky="nsew", padx=10, pady=5)
        self.grid_rowconfigure(5, weight=1)

        # 7. 상태바 (진행상황/메시지 등)
        self.status_label = ctk.CTkLabel(self, text="입력 대기 중", font=self.font, anchor="w")
        self.status_label.grid(row=6, column=0, sticky="ew", padx=10, pady=(0, 5))
        self.grid_rowconfigure(6, weight=0)
        self.grid_columnconfigure(0, weight=1)

    def _on_verify_click(self):
        # 입력값에서 학명 리스트 추출
        input_text = self.entry.get("0.0", "end").strip()
        if not input_text or input_text == self.initial_text:
            return
        names = [n.strip() for n in input_text.replace("\n", ",").split(",") if n.strip()]
        if not names:
            return
        try:
            from species_verifier.core.verifier import verify_col_species
            results = verify_col_species(names)
        except Exception as e:
            results = [{"학명": "오류", "검증": str(e), "COL 상태": "-", "COL ID": "-", "COL URL": "-", "위키백과 요약": "-"}]
        # 결과 테이블 초기화
        for i in self.result_tree.get_children():
            self.result_tree.delete(i)
        # 결과 표시
        for row in results:
            self.result_tree.insert("", "end", values=(row.get("학명", "-"), row.get("검증", "-"), row.get("COL 상태", "-"), row.get("COL ID", "-"), row.get("COL URL", "-"), row.get("위키백과 요약", "-")))
        # 상태바 업데이트
        if results:
            self.status_label.configure(text=f"{len(results)}건 결과 표시")
        else:
            self.status_label.configure(text="결과 없음")


    def _on_entry_focus_in(self, event=None):
        if self.entry.get("0.0", "end-1c") == self.initial_text:
            self.entry.delete("0.0", tk.END)
            self.entry.configure(text_color=("black", "white"))
        self._update_verify_button_state()

    def _on_entry_focus_out(self, event=None):
        current_text = self.entry.get("0.0", "end-1c")
        if not current_text.strip():
            self.entry.delete("0.0", tk.END)
            self.entry.insert("0.0", self.initial_text)
            self.entry.configure(text_color="gray")
        self._update_verify_button_state()

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
            self.file_path_var.set(file_path)
            self._trigger_callback("on_file_browse", file_path)
        else:
            self.file_path_var.set("")
        self._update_verify_button_state()

    def _on_file_clear_click(self):
        self.file_path_var.set("")
        self._update_verify_button_state()

    def _on_verify_click(self):
        text = self.entry.get("0.0", "end-1c").strip()
        file_path = self.file_path_var.get()
        if text and text != self.initial_text:
            self._trigger_callback("on_search", text, "col")
        elif file_path and os.path.exists(file_path):
            self._trigger_callback("on_file_search", file_path, "col")
        else:
            print("[Warning COL] Verify button clicked but no valid input found.")

    def _update_verify_button_state(self, *args):
        text_input = self.entry.get("0.0", "end-1c").strip()
        file_input = self.file_path_var.get()
        is_text_valid = text_input and text_input != self.initial_text
        is_file_valid = file_input and os.path.exists(file_input)
        if is_text_valid or is_file_valid:
            self.verify_button.configure(state="normal")
        else:
            self.verify_button.configure(state="disabled")


    def _create_widgets(self, **kwargs):
        # ... 기존 위젯 생성 코드 ...
        # 파일 입력 프레임 예시
        file_frame = ctk.CTkFrame(self)
        file_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=2)
        file_frame.grid_columnconfigure(0, weight=1)
        # 파일 경로 Entry
        self.file_path_entry = ctk.CTkEntry(file_frame, textvariable=self.file_path_var, font=self.font, width=260, state="readonly")
        self.file_path_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        # 찾기 버튼
        self.file_browse_button = ctk.CTkButton(file_frame, text="찾기", font=self.font, width=60, command=self._on_file_browse_click)
        self.file_browse_button.grid(row=0, column=1, padx=(0, 0))
        # 지우기 버튼
        self.file_clear_button = ctk.CTkButton(file_frame, text="지우기", font=self.font, width=60, command=self._on_file_clear_click)
        self.file_clear_button.grid(row=0, column=2, padx=(2, 0))
        # 나머지 위젯들(입력, 검증 버튼 등)은 기존대로 배치


    def set_selected_file(self, file_path: Optional[str]):
        self.file_path_var.set(file_path or "")

    def _on_file_clear_click(self):
        self.file_path_var.set("")
