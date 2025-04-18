import customtkinter as ctk
from customtkinter import CTkFont
import tkinter as tk
from tkinter import filedialog, ttk
import pandas as pd
import threading
import os
import sys
import tkinter.messagebox as messagebox
import re
import webbrowser
from datetime import date, timedelta
import wikipedia
import requests
import json
import queue # Queue 추가

# --- 시간 제한 설정 (유지) ---
EXPIRY_DAYS = 547
CONTACT_EMAIL = "ecomarin@naver.com"
DATE_FILE_NAME = ".verifier_expiry_date"

# --- WoRMS API 정보 (추가) ---
WORMS_API_BASE_URL = "https://www.marinespecies.org/rest"

# --- 경로 설정 ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
# 데이터 파일 경로 설정
data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
mappings_file = os.path.join(data_dir, 'korean_scientific_mappings.json')

# --- 기본 매핑 정보 (파일이 없을 경우 사용) ---
DEFAULT_MAPPINGS = {
    "fish": {
        "넙치": "Paralichthys olivaceus",
        "조피볼락": "Sebastes schlegelii",
        "참돔": "Pagrus major",
        "감성돔": "Acanthopagrus schlegelii",
        "대서양연어": "Salmo salar",
        "무지개송어": "Oncorhynchus mykiss",
        "뱀장어": "Anguilla japonica",
        "숭어": "Mugil cephalus",
        "전갱이": "Trachurus japonicus"
    },
    "shellfish_and_crustaceans": {
        "전복": "Haliotis discus hannai",
        "키조개": "Atrina pectinata",
        "굴": "Crassostrea gigas",
        "진주담치": "Mytilus edulis",
        "가리비": "Patinopecten yessoensis",
        "바지락": "Ruditapes philippinarum",
        "대합": "Meretrix lusoria",
        "꽃게": "Portunus trituberculatus",
        "대게": "Chionoecetes opilio",
        "붉은대게": "Chionoecetes japonicus"
    },
    "cephalopods": {
        "오징어": "Todarodes pacificus",
        "문어": "Octopus vulgaris"
    }
}

# --- 매핑 정보 로드 함수 ---
def load_korean_mappings():
    """JSON 파일에서 한글 국명-학명 매핑 정보를 로드합니다."""
    try:
        if os.path.exists(mappings_file):
            with open(mappings_file, 'r', encoding='utf-8') as f:
                print(f"[Info] 매핑 파일 로드: {mappings_file}")
                mappings_data = json.load(f)
                # 매핑 정보를 단일 딕셔너리로 변환
                flat_mappings = {}
                for category in mappings_data:
                    flat_mappings.update(mappings_data[category])
                
                # 매핑 개수만 로그에 출력
                total_items = len(flat_mappings)
                print(f"[Info] 매핑 항목 {total_items}개 로드 완료")
                
                return flat_mappings
        else:
            print(f"[Warning] 매핑 파일을 찾을 수 없음: {mappings_file}")
            # 기본 매핑 정보를 파일로 저장
            save_korean_mappings(DEFAULT_MAPPINGS)
            # 단일 딕셔너리로 변환하여 반환
            flat_mappings = {}
            for category in DEFAULT_MAPPINGS:
                flat_mappings.update(DEFAULT_MAPPINGS[category])
            
            # 기본 매핑 개수만 로그에 출력
            total_default_items = len(flat_mappings)
            print(f"[Info] 기본 매핑 항목 {total_default_items}개 사용")
            
            return flat_mappings
    except Exception as e:
        print(f"[Error] 매핑 파일 로드 오류: {e}")
        # 오류 발생 시 기본 매핑의 합쳐진 버전 반환
        flat_mappings = {}
        for category in DEFAULT_MAPPINGS:
            flat_mappings.update(DEFAULT_MAPPINGS[category])
        return flat_mappings

def save_korean_mappings(mappings_data):
    """한글 국명-학명 매핑 정보를 JSON 파일로 저장합니다."""
    try:
        # 디렉토리가 없으면 생성
        os.makedirs(os.path.dirname(mappings_file), exist_ok=True)
        with open(mappings_file, 'w', encoding='utf-8') as f:
            json.dump(mappings_data, f, ensure_ascii=False, indent=2)
            print(f"[Info] 매핑 파일 저장 완료: {mappings_file}")
    except Exception as e:
        print(f"[Error] 매핑 파일 저장 오류: {e}")

# --- 매핑 정보 로드 ---
KOREAN_NAME_MAPPINGS = load_korean_mappings()

# 프로젝트 루트 경로를 sys.path에 추가 (core 모듈 임포트를 위해)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# core 모듈 임포트 시도 (오류 발생 시 메시지 출력)
verify_species_list = None
check_scientific_name = None # check_scientific_name 추가
try:
    # Attempt to import necessary functions from the core module
    # Import other core functions if needed by the GUI later
    from species_verifier.core.verifier import verify_species_list, check_scientific_name
    print("[Debug] Successfully imported 'verify_species_list' and 'check_scientific_name' from core.verifier.")
except ImportError as e:
    # Capture traceback for better debugging
    import traceback
    print(f"[Error] Failed to import core modules needed for verification.")
    print(f"Specific Error: {e}")
    print("Traceback:")
    print(traceback.format_exc()) # Print full traceback
    print("GUI will start, but verification functionality will be disabled.")
    # Keep verify_species_list as None
except Exception as e: # Catch other potential errors during import (e.g., syntax errors in core modules)
    import traceback
    print(f"[Error] An unexpected error occurred during core module import.")
    print(f"Specific Error: {e}")
    print("Traceback:")
    print(traceback.format_exc()) # Print full traceback
    print("GUI will start, but verification functionality will be disabled.")
    # Keep verify_species_list as None


ctk.set_appearance_mode("System")  # Modes: "System" (default), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (default), "green", "dark-blue"

class SpeciesVerifierApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- 매핑 테이블 로드 ---
        self.korean_name_mappings = load_korean_mappings()
        print(f"[Debug] 매핑 테이블 로드 완료: {len(self.korean_name_mappings)}개 항목")
        # 전체 키 목록 대신 샘플 5개만 표시
        sample_keys = list(self.korean_name_mappings.keys())[:5]
        print(f"[Debug] 매핑 테이블 샘플 항목: {sample_keys}{'...' if len(self.korean_name_mappings) > 5 else ''}")
        
        # 플레이스홀더 텍스트 설정 - 입력 필드가 비었을 때 포커스에 따라 다른 텍스트 표시
        self.placeholder_focused = "예: Homo sapiens, Gadus morhua"
        self.placeholder_unfocused = "여러 학명은 콤마로 구분 (예: Paralichthys olivaceus, Anguilla japonica)"
        
        # 입력 필드가 비어있는지 여부를 추적하는 플래그
        self.entry_is_empty = True  # 초기 상태는 비어있음

        # 툴팁 윈도우 관리 변수 초기화
        self.tooltip_window = None

        # --- 기본 폰트 설정 (헤더 폰트 크기 조정) ---
        try:
            self.default_font = CTkFont(family="Malgun Gothic", size=11)
            self.default_bold_font = CTkFont(family="Malgun Gothic", size=11) # 볼드 제거
            self.header_font = CTkFont(family="Malgun Gothic", size=8)
            self.footer_font = CTkFont(family="Malgun Gothic", size=10)
        except Exception as e:
            print(f"[Warning] Font loading error: {e}. Using default fonts.")
            self.default_font = CTkFont(size=11)
            self.default_bold_font = CTkFont(size=11) # 볼드 제거
            self.header_font = CTkFont(size=8)
            self.footer_font = CTkFont(size=10)
        # --- 폰트 설정 끝 ---

        self.title("Species Verifier")
        self.geometry("900x750") # 높이 다시 조정 (늘어난 위젯 공간 고려)

        self.current_results = []
        self.MAX_RESULTS_DISPLAY = 500 # Treeview 결과 표시 최대 개수 (기존 100 -> 500)
        self.MAX_FILE_PROCESSING_LIMIT = 2000 # 파일 처리 최대 학명 수 (500 -> 2000)
        self.DIRECT_EXPORT_THRESHOLD = 500 # Treeview 대신 바로 파일로 저장할 임계값

        # --- 프레임 설정 --- (Title 프레임 제거, 푸터는 유지)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0) # Input frame (row 0으로 변경)
        self.grid_rowconfigure(1, weight=1) # Result frame (row 1로 변경)
        self.grid_rowconfigure(2, weight=0) # Status frame (row 2로 변경)
        self.grid_rowconfigure(3, weight=0) # Footer frame (row 3으로 변경)

        # 입력 프레임 (row 0으로 변경)
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="nsew") # pady 상단 추가
        self.input_frame.grid_columnconfigure(1, weight=1)

        # 결과 프레임 (row 1로 변경)
        self.result_frame = ctk.CTkFrame(self)
        self.result_frame.grid(row=1, column=0, padx=20, pady=(10, 10), sticky="nsew")
        self.result_frame.grid_rowconfigure(0, weight=1)
        self.result_frame.grid_columnconfigure(0, weight=1)

        # 상태 표시 프레임 (row 2로 변경)
        self.status_frame = ctk.CTkFrame(self, height=50)
        self.status_frame.grid(row=2, column=0, padx=20, pady=(10, 10), sticky="nsew")
        self.status_frame.grid_columnconfigure(0, weight=1)
        self.status_frame.grid_columnconfigure(1, weight=0)

        # 푸터 프레임 (row 3으로 변경)
        self.footer_frame = ctk.CTkFrame(self, height=30, corner_radius=0)
        self.footer_frame.grid(row=3, column=0, padx=0, pady=(5, 0), sticky="nsew")
        self.footer_frame.grid_columnconfigure(0, weight=1)
        self.footer_label = ctk.CTkLabel(self.footer_frame,
                                         text="© 2025 국립수산과학원 수산생명자원 책임기관", # 텍스트 수정
                                         font=self.footer_font,
                                         text_color=("gray50", "gray60"))
        self.footer_label.grid(row=0, column=0, pady=(0, 5))

        # --- 입력 프레임 위젯 --- (레이블 텍스트 수정)
        self.single_entry_label = ctk.CTkLabel(self.input_frame, text="학명/국명 입력:", font=self.default_font)
        self.single_entry_label.grid(row=0, column=0, padx=(20, 10), pady=15, sticky="w")
        
        # 입력 필드 설정
        self.single_entry = ctk.CTkEntry(self.input_frame, placeholder_text="예: Homo sapiens, Gadus morhua", font=self.default_font)
        self.single_entry.grid(row=0, column=1, padx=10, pady=15, sticky="ew")
        # Enter 키 바인딩 추가
        self.single_entry.bind("<Return>", lambda event: self.start_single_search_thread())
        # 포커스 이벤트 바인딩 추가
        self.single_entry.bind("<FocusIn>", self.on_entry_focus_in)
        self.single_entry.bind("<FocusOut>", self.on_entry_focus_out)
        # 키 이벤트 바인딩 추가
        self.single_entry.bind("<Key>", self.on_entry_key)
        self.single_entry.bind("<KeyRelease>", self.on_entry_key)
        
        # 검색 버튼
        self.single_search_button = ctk.CTkButton(self.input_frame, text="검색", width=90, 
                                                command=self.start_single_search_thread, 
                                                font=self.default_bold_font)
        self.single_search_button.grid(row=0, column=2, padx=(10, 20), pady=15)
        
        # 입력 도움말 레이블 제거 (빨간색 박스로 표시된 부분)
        self.input_help_label_visible = False
        
        # 파일 선택 - row 변경 (이제 1로, 도움말 레이블이 제거되었으므로)
        self.file_button = ctk.CTkButton(self.input_frame, text="파일 선택 (.csv, .xlsx)", command=self.browse_file, font=self.default_bold_font)
        self.file_button.grid(row=1, column=0, padx=(20, 10), pady=(15, 5), sticky="w") # 하단 패딩 줄임
        self.file_label = ctk.CTkLabel(self.input_frame, text="선택된 파일 없음", anchor="w", font=self.default_font)
        self.file_label.grid(row=1, column=1, padx=10, pady=(15, 5), sticky="ew") # 하단 패딩 줄임
        self.file_search_button = ctk.CTkButton(self.input_frame, text="파일 검증", width=90, command=self.start_file_search_thread, state="disabled", font=self.default_bold_font)
        self.file_search_button.grid(row=1, column=2, padx=(10, 20), pady=(15, 5), sticky="e") # 하단 패딩 줄임

        self.selected_file_path = None

        # 파일 처리 제한 안내 레이블 추가 (위치 수정)
        self.file_limit_label = ctk.CTkLabel(self.input_frame, 
                                             text=f"*파일 처리 시 최대 {self.MAX_FILE_PROCESSING_LIMIT}개 학명까지 가능합니다 (처리량이 {self.DIRECT_EXPORT_THRESHOLD}개 초과 시 Excel로 자동 저장).", 
                                             font=CTkFont(family="Malgun Gothic", size=10), 
                                             text_color=("gray40", "gray70"))
        # 위치를 파일 선택 행(row=1) 바로 다음에 배치, 파일 선택 첫 번째 열 아래
        self.file_limit_label.grid(row=2, column=0, columnspan=3, padx=(20, 20), pady=(0, 5), sticky="w")
        
        # 매핑 관리 버튼 추가 - row 변경 (이제 3으로)
        self.mapping_button = ctk.CTkButton(self.input_frame, text="국명-학명 매핑 관리", 
                                          command=self.open_mapping_manager, 
                                          font=self.default_bold_font)
        self.mapping_button.grid(row=3, column=0, columnspan=3, padx=20, pady=(2, 10), sticky="w") # 상단 패딩 5에서 2로 줄임

        # --- 결과 프레임 위젯 ---
        style = ttk.Style()
        # Treeview 스타일 설정 (CustomTkinter 테마와 유사하게)
        # 테마에 따라 색상 코드 조정 필요
        bg_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["fg_color"])
        text_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkLabel"]["text_color"])
        selected_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkButton"]["fg_color"])

        # 기본 행 폰트 및 높이 설정
        row_height = self.default_font.metrics('linespace') + 8 # 폰트 높이 + 상하 여백
        style.configure("Treeview",
                        background=bg_color,
                        foreground=text_color,
                        fieldbackground=bg_color,
                        borderwidth=0,
                        rowheight=row_height, # 행 높이 설정
                        font=self.default_font) # 행 폰트 설정
        style.map('Treeview', background=[('selected', selected_color)], foreground=[('selected', text_color)])

        # Treeview 헤더 스타일 재조정
        header_bg_color = ("gray85", "gray28")
        header_fg_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkLabel"]["text_color"])
        header_border_color = ("gray70", "gray40") # 테두리 색상 정의

        style.configure("Treeview.Heading",
                        background=self._apply_appearance_mode(header_bg_color),
                        foreground=header_fg_color,
                        relief="flat",
                        font=(self.header_font.cget("family"), self.header_font.cget("size"), "normal"),
                        padding=[10, 5],
                        borderwidth=1,
                        bordercolor=self._apply_appearance_mode(header_border_color)
                       )
        style.map("Treeview.Heading",
                  background=[('active', self._apply_appearance_mode(ctk.ThemeManager.theme["CTkButton"]["hover_color"]))]
                  )

        # Treeview 태그 스타일 정의
        self.result_tree = None  # 먼저 None으로 초기화
        
        # 나중에 태그 스타일을 설정하기 위해 스타일 변수 저장
        self.tree_style = style

        self.result_frame.grid_rowconfigure(0, weight=1)    # Treeview가 들어갈 행 확장
        self.result_frame.grid_columnconfigure(0, weight=1) # Treeview가 들어갈 열 확장

        # Treeview 생성 및 배치 (컬럼 추가: "Mapped Name")
        self.result_tree = ttk.Treeview(self.result_frame, 
                                       columns=("Mapped Name", "Verified", "Status", "WoRMS_ID", "WoRMS Link", "Wiki Summary"), 
                                       show='tree headings')
        self.result_tree.grid(row=0, column=0, padx=(15, 0), pady=(15, 0), sticky="nsew")

        # Treeview 태그 설정
        self.result_tree.tag_configure('verified', background='#EEFFEE')  # 연한 녹색 배경 (검증됨)
        self.result_tree.tag_configure('unverified', background='#FFEEEE')  # 연한 빨간색 배경 (미검증)
        self.result_tree.tag_configure('caution', background='#FFEE99')  # 노란색 배경 (주의 필요)

        # 컬럼 설정 (새 컬럼 추가: "Mapped Name")
        self.result_tree.heading("#0", text="입력명") # 첫 번째 열(#0) 헤더 설정
        self.result_tree.heading("Mapped Name", text="학명") # "매핑된 학명"에서 "학명"으로 변경
        self.result_tree.heading("Verified", text="검증됨")
        self.result_tree.heading("Status", text="WoRMS 상태")
        self.result_tree.heading("WoRMS_ID", text="WoRMS ID(?)") # 기호 추가 및 간격 제거
        self.result_tree.heading("WoRMS Link", text="WoRMS 링크(?)") # 기호 추가
        self.result_tree.heading("Wiki Summary", text="종정보(?)") # 기호 추가 및 간격 제거

        # 컬럼 너비 조정 (새 컬럼 추가: "Mapped Name")
        self.result_tree.column("#0", width=120, anchor=tk.CENTER) # 입력명 중앙 정렬
        self.result_tree.column("Mapped Name", width=120, anchor=tk.W) # 매핑된 학명 열 추가
        self.result_tree.column("Verified", width=60, anchor=tk.CENTER)
        self.result_tree.column("Status", width=100, anchor=tk.CENTER) # WoRMS 상태 중앙 정렬
        self.result_tree.column("WoRMS_ID", width=95, anchor=tk.CENTER) # WoRMS ID 중앙 정렬, 너비 조금 더 늘림
        self.result_tree.column("WoRMS Link", width=150, anchor=tk.W)
        self.result_tree.column("Wiki Summary", width=220, anchor=tk.W) # 크기 조정

        # 스크롤바 생성 (grid() 호출은 나중에)
        self.tree_scrollbar_y = ctk.CTkScrollbar(self.result_frame, command=self.result_tree.yview)
        self.tree_scrollbar_x = ctk.CTkScrollbar(self.result_frame, command=self.result_tree.xview, orientation="horizontal")
        self.result_tree.configure(yscrollcommand=self.tree_scrollbar_y.set, xscrollcommand=self.tree_scrollbar_x.set)
        # self.tree_scrollbar_y.grid(...) # 초기에는 배치하지 않음
        # self.tree_scrollbar_x.grid(...) # 초기에는 배치하지 않음

        # --- 상태 표시 프레임 위젯 --- (grid() 호출은 나중에)
        self.status_frame = ctk.CTkFrame(self, height=50)
        self.status_frame.grid(row=2, column=0, padx=20, pady=(10, 10), sticky="nsew")
        self.status_frame.grid_columnconfigure(0, weight=1)
        self.status_frame.grid_columnconfigure(1, weight=0)

        self.progress_bar = ctk.CTkProgressBar(self.status_frame)
        # self.progress_bar.grid(...) # 초기에는 배치하지 않음
        self.progress_label = ctk.CTkLabel(self.status_frame, text="", anchor="w", font=self.default_font) # 초기 텍스트 비움
        # self.progress_label.grid(...) # 초기에는 배치하지 않음

        self.export_button = ctk.CTkButton(self.status_frame, text="결과 저장 (Excel)", command=self.export_results_to_excel, state="disabled", font=self.default_bold_font)
        self.export_button.grid(row=0, column=1, padx=(10, 20), pady=15, sticky="e") # 내보내기 버튼은 항상 표시될 수 있음

        # --- 푸터 프레임 --- 
        # ... (기존 푸터 설정) ...

        self._reset_status_ui() # 초기 상태 설정 (스크롤바, 진행률 숨김 포함)
        # 창 크기 변경 시 스크롤바 업데이트를 위한 바인딩 (선택 사항, 복잡성 증가)
        # self.result_tree.bind("<Configure>", self._update_scrollbars)

        # WoRMS Link 컬럼 더블 클릭 이벤트 바인딩 (컬럼 인덱스 수정 #5 -> #4)
        self.result_tree.bind("<Double-1>", self.on_tree_double_click)
        # 오른쪽 클릭 메뉴 바인딩 추가
        self.result_tree.bind("<Button-3>", self._show_context_menu)
        # 마우스 움직임 및 테이블 벗어남 이벤트 바인딩 (툴팁용)
        self.result_tree.bind("<Motion>", self._on_tree_motion)
        self.result_tree.bind("<Leave>", self._on_tree_leave)

        self.focus_entry()

    def _reset_status_ui(self, reset_file_label=False):
        """Resets the status UI elements, hiding progress and scrollbars."""
        # 진행률 표시 숨기기
        self.progress_bar.grid_forget()
        self.progress_label.grid_forget()
        self.progress_label.configure(text="") # 레이블 텍스트 초기화
        self.progress_bar.set(0)
        self.progress_bar.stop()

        # 파일 레이블 초기화 (옵션)
        if reset_file_label:
            self.selected_file_path = None
            self.file_label.configure(text="선택된 파일 없음")
            self.file_search_button.configure(state="disabled")

        # 결과 없으면 내보내기 버튼 비활성화
        if not self.current_results:
            self.export_button.configure(state="disabled")

        # 스크롤바 숨기기
        self.tree_scrollbar_y.grid_forget()
        self.tree_scrollbar_x.grid_forget()

    def _show_progress_ui(self, initial_text=""):
        """Shows the progress bar and label."""
        self.progress_bar.grid(row=0, column=0, padx=(20, 10), pady=15, sticky="ew")
        self.progress_label.grid(row=0, column=0, padx=25, pady=15, sticky="w")
        self.progress_label.configure(text=initial_text)

    def _update_scrollbars(self, event=None):
        """Checks content and shows/hides scrollbars accordingly.
           Note: Reliably checking overflow, especially horizontal, can be tricky.
                 This is a simplified version.
        """
        # 수직 스크롤바 체크 (결과가 있으면 일단 표시 시도)
        # 더 정확하게 하려면 Treeview 높이와 아이템 높이 비교 필요
        if self.current_results: # 결과가 있을 때만 표시
            self.tree_scrollbar_y.grid(row=0, column=1, padx=(0, 15), pady=(15, 0), sticky="ns")
        else:
            self.tree_scrollbar_y.grid_forget()

        # 수평 스크롤바 체크 (내용 너비 > Treeview 너비)
        # winfo_width()는 위젯이 그려진 후에 정확한 값을 반환하므로
        # update_idletasks() 또는 after 사용 필요할 수 있음
        self.update_idletasks() # 레이아웃 업데이트 강제
        total_col_width = sum(self.result_tree.column(col, "width") for col in self.result_tree["columns"])
        tree_width = self.result_tree.winfo_width()
        
        # print(f"Debug Scroll: Total Col Width: {total_col_width}, Tree Width: {tree_width}") # 디버깅용

        if tree_width > 0 and total_col_width > tree_width:
            self.tree_scrollbar_x.grid(row=1, column=0, padx=(15, 0), pady=(0, 15), sticky="ew")
        else:
            self.tree_scrollbar_x.grid_forget()

    def update_progress(self, progress_value):
        """Updates the progress bar and label. Designed to be called safely via self.after."""
        self.progress_bar.set(progress_value)
        if progress_value >= 1.0:
            self.progress_label.configure(text="완료") # 100% 도달 시 '완료'로 표시
        else:
            self.progress_label.configure(text=f"검증 중... {progress_value*100:.0f}%") # 진행률 표시

    def _update_progress_label(self, text):
        """진행 레이블 텍스트를 업데이트합니다."""
        self.progress_label.configure(text=text)

    def browse_file(self):
        """파일 탐색기를 열어 CSV 또는 Excel 파일을 선택합니다."""
        file_path = filedialog.askopenfilename(
            title="학명 목록 파일 선택",
            filetypes=[("Excel files", "*.xlsx"), ("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if file_path:
            self.selected_file_path = file_path
            # 파일 이름만 표시 (경로가 길 경우 대비)
            self.file_label.configure(text=os.path.basename(file_path))
            self.file_search_button.configure(state="normal") # 파일 선택 시 버튼 활성화
        else:
            self.selected_file_path = None
            self.file_label.configure(text="선택된 파일 없음")
            self.file_search_button.configure(state="disabled")

    # --- 특수문자 제거 함수 개선 ---
    def _clean_scientific_name(self, input_name):
        """학명에서 불필요한 특수문자를 제거합니다."""
        if not input_name or not isinstance(input_name, str):
            return input_name

        # 제거할 특수문자 목록 (한글/학명 공용)
        chars_to_remove = r"[',*#\"\[\]\{\}]"
        # 정규식을 사용하여 특수문자 제거
        cleaned_name = re.sub(chars_to_remove, '', input_name)
        # 연속된 공백을 단일 공백으로 치환
        cleaned_name = re.sub(r'\s+', ' ', cleaned_name).strip()
        # 원본과 달라졌다면 로그 출력
        if cleaned_name != input_name:
            print(f"[Info] 입력 정리: '{input_name}' -> '{cleaned_name}'")
        return cleaned_name

    # --- start_single_search_thread 함수 수정 ---
    def start_single_search_thread(self):
        """입력창에서 단일 검색을 시작합니다."""
        input_text = self.single_entry.get().strip()
        if not input_text:
            self.search_status.config(text="검색어를 입력하세요.")
            return

        # UI 비활성화 (검색 중)
        self._set_ui_state("disabled")
        
        # 한글 국명인지 또는 학명인지 확인 (간단한 휴리스틱)
        if re.search(r'[ㄱ-ㅎㅏ-ㅣ가-힣]', input_text):
            print(f"[Info] 한글 국명 입력 감지: '{input_text}'")
            # 쉼표, 공백 등으로 구분된 여러 국명이 있는지 확인
            if ',' in input_text or len(input_text.split()) > 1:
                # 여러 국명 처리 - 특수문자 제거는 _process_multiple_korean_names에서 수행
                thread = threading.Thread(target=self._process_multiple_korean_names, args=(input_text,))
            else:
                # 단일 국명 처리 - 특수문자 제거
                cleaned_input = self._clean_scientific_name(input_text)
                thread = threading.Thread(target=self._search_korean_name, args=(cleaned_input,))
        else:
            # 학명인 경우 (비-한글)
            print(f"[Info] 학명(또는 영문) 입력 감지: '{input_text}'")
            # 쉼표로 구분된 여러 학명 처리
            if ',' in input_text:
                # 쉼표로 구분된 학명 목록을 분리하고 각각 특수문자 제거
                species_list = [self._clean_scientific_name(name.strip()) for name in input_text.split(',') if name.strip()]
                thread = threading.Thread(target=self._perform_verification, args=(species_list,))
            else:
                # 단일 학명 - 특수문자 제거
                cleaned_input = self._clean_scientific_name(input_text)
                thread = threading.Thread(target=self._perform_verification, args=([cleaned_input],))
        
        thread.daemon = True
        thread.start()

    def _process_multiple_korean_names(self, korean_names):
        """여러 한글 국명을 처리하고 각각에 대한 학명을 찾아 검증합니다."""
        # 입력된 국명 문자열 처리
        # 쉼표, 스페이스, 탭 등으로 구분된 국명을 분리
        if isinstance(korean_names, str):
            # 문자열이 입력된 경우 구분자로 분리
            korean_names = re.split(r'[,\s\t]+', korean_names)
            # 공백 제거, 특수문자 제거 및 빈 문자열 필터링
            korean_names = [self._clean_scientific_name(name.strip()) for name in korean_names if name.strip()]
            print(f"[Debug] 입력 문자열에서 분리된 국명: {korean_names}")
        
        if not korean_names:
            print("[Warning] 처리할 국명이 없습니다.")
            self.after(0, lambda: self.show_centered_message("warning", "입력 오류", "처리할 국명이 없습니다."))
            return
        
        self.after(0, self._show_progress_ui, f"{len(korean_names)}개의 국명 처리 중...")
        self.after(0, self.progress_bar.start)
        self.after(0, self._set_ui_state, "disabled")
        
        # --- 수정: verification_list에 모든 국명 포함 (학명 없으면 None) ---
        verification_list_with_status = [] # (국명, 학명 or None) 튜플 저장
        # not_found_names = [] # 제거
        # not_found_results = [] # 제거
        
        print(f"[Info] {len(korean_names)}개 국명 처리 시작: {', '.join(korean_names)}")
        
        for i, korean_name in enumerate(korean_names):
            self.after(0, self._update_progress_label, f"'{korean_name}' 학명 찾는 중... ({i+1}/{len(korean_names)})")
            print(f"[Info] '{korean_name}' (#{i+1}/{len(korean_names)})에 대한 학명 검색 시작")
            
            scientific_name = self._find_scientific_name_from_korean_name(korean_name)
            
            if scientific_name:
                print(f"[Success] '{korean_name}'에 대한 학명 '{scientific_name}' 찾기 성공")
                verification_list_with_status.append((korean_name, scientific_name)) # (국명, 학명) 추가
            else:
                print(f"[Info] '{korean_name}'에 대한 학명을 찾지 못했습니다. (WoRMS 검증 생략 예정)") # 메시지 변경
                verification_list_with_status.append((korean_name, None)) # (국명, None) 추가
                # not_found_names.append(korean_name) # 제거
                # --- 기본 결과 생성 로직 제거 --- 
                # result = { ... } # 제거
                # not_found_results.append(result) # 제거
        
        # print(f"[Info] 국명 처리 결과: 총 {len(korean_names)}개 중 {len(verification_list)}개 성공, {len(not_found_names)}개 실패") # 로그 수정 필요 (아래에서 처리)
        
        # 학명을 찾지 못한 항목들에 대한 결과 먼저 표시 (결과 테이블 업데이트) -> 이 로직 제거
        # if not_found_results: # 제거
        #    self.after(0, lambda results=not_found_results: self.update_results(results)) # 제거
        
        # --- 수정: 항상 _perform_verification 호출 (리스트가 비어있지 않다면) ---
        if verification_list_with_status:
            print(f"[Info] Starting verification for {len(verification_list_with_status)} names (including those without scientific names).")
            thread = threading.Thread(target=self._perform_verification, args=(verification_list_with_status,)) # 수정된 리스트 전달, not_found_names 제거
            thread.daemon = True
            thread.start()
        else: # 처리할 국명이 아예 없는 경우 (매우 드문 케이스)
            print("[Warning] No valid Korean names found to process.")
            self.after(0, self.progress_bar.stop) # 진행 멈춤
            self.after(0, self._reset_status_ui) # 상태 초기화
            self.after(0, lambda: self.show_centered_message("warning", "처리 불가", "처리할 국명이 없습니다."))
            self.after(0, self._set_ui_state, "normal") # UI 활성화
            # 입력창 비우기 및 포커스 (처리할 이름 없을 시)
            self.after(10, self.single_entry.delete, 0, tk.END)
            self.after(20, self.focus_entry)

        # --- 이전의 '모두 실패' 로직 제거 ---
        # elif not_found_names: ... (제거됨) ... 

    def _find_scientific_name_from_korean_name(self, korean_name):
        """한글 이름에서 학명을 찾는 모든 방법을 순차적으로 시도합니다."""
        # 1. 매핑 테이블에서 학명 찾기 (이제 flat dictionary)
        # 수정: 직접 딕셔너리에서 key(korean_name) 존재 여부 확인
        if korean_name in KOREAN_NAME_MAPPINGS:
            scientific_name = KOREAN_NAME_MAPPINGS[korean_name]
            print(f"[Info] 매핑 테이블에서 '{korean_name}'의 학명 찾음: {scientific_name}") # 로그 추가
            return scientific_name
        
        # 2. 위키백과에서 학명 추출 시도
        scientific_name = self._extract_scientific_name_from_wiki(korean_name)
        if scientific_name:
            return scientific_name
            
        # 3. WoRMS API 직접 검색 (미래 기능)
        # 현재는 미구현
        
        return None

    def _search_korean_name(self, korean_name):
        """입력된 국명(한글)으로 학명을 검색하고 결과를 표시합니다."""
        self.search_status.config(text=f"'{korean_name}' 검색 중...")
        self.update_idletasks()
        
        try:
            # 위키백과 검색 전 KOREAN_NAME_MAPPINGS에서 매핑된 학명을 먼저 확인 - 우선순위 1
            scientific_name = None
            
            # 한글 이름을 사전에서 검색
            scientific_name = self._find_scientific_name_from_korean_name(korean_name)
            
            if scientific_name:
                print(f"[Info] Found scientific name in mapping: '{scientific_name}' for '{korean_name}'.")
                
                # 데이터 처리 (표준 형식)
                species_list = [(korean_name, scientific_name, korean_name)]  # 입력국명, 학명, 표시국명
                
                # WoRMS 확인 및 결과 처리
                results = None
                try:
                    # GUI 콜백 정의 (진행률 표시용)
                    def progress_callback(progress_value):
                        self.after(0, self.update_progress, progress_value)
                    
                    # WoRMS 검증 수행
                    results = verify_species_list(species_list, progress_callback=progress_callback)
                except Exception as e:
                    print(f"[Error] WoRMS verification failed: {e}")
                    messagebox.showerror("오류", f"WoRMS 검증 중 오류가 발생했습니다.\n{str(e)}")
                    self._set_ui_state("normal")
                    return False
                
                if results:
                    # 기존 결과 유지 (clear_existing=False)
                    self._update_results_display(results, clear_existing=False)
                    # 성공 메시지
                    self.search_status.config(text=f"'{korean_name}'의 학명 '{scientific_name}' 조회 완료")
                    # --- 검색 후 입력창 비우기 및 포커스 --- 
                    self.after(0, self.single_entry.delete, 0, tk.END)
                    self.after(10, self.focus_entry) # 포커스 복원
                    # --- 추가 끝 ---
                    return True
                return False
            
            # 우선순위 2: 위키백과 검색 (국명을 전달하여 그 정보도 활용)
            print(f"[Info] No mapping found for '{korean_name}', trying Wikipedia search.")
            scientific_name = self._extract_scientific_name_from_wiki(korean_name)
            
            if scientific_name:
                print(f"[Info] Found scientific name from Wikipedia: '{scientific_name}' for '{korean_name}'.")
                
                # 데이터 처리
                species_list = [(korean_name, scientific_name, korean_name)]  # 입력국명, 학명, 표시국명
                
                # WoRMS 확인 및 결과 처리
                results = None
                try:
                    # GUI 콜백 정의 (진행률 표시용)
                    def progress_callback(progress_value):
                        self.after(0, self.update_progress, progress_value)
                    
                    # WoRMS 검증 수행
                    results = verify_species_list(species_list, progress_callback=progress_callback)
                except Exception as e:
                    print(f"[Error] WoRMS verification failed: {e}")
                    messagebox.showerror("오류", f"WoRMS 검증 중 오류가 발생했습니다.\n{str(e)}")
                    self._set_ui_state("normal")
                    return False
                
                if results:
                    # 기존 결과 유지 (clear_existing=False)
                    self._update_results_display(results, clear_existing=False)
                    # 성공 메시지
                    self.search_status.config(text=f"'{korean_name}'의 학명 '{scientific_name}' 조회 완료")
                    # --- 검색 후 입력창 비우기 및 포커스 --- 
                    self.after(0, self.single_entry.delete, 0, tk.END)
                    self.after(10, self.focus_entry) # 포커스 복원
                    # --- 추가 끝 ---
                    return True
            
            # 우선순위 3: WoRMS 한글 검색 API 시도
            try:
                # WoRMS에서 직접 한글 이름으로 검색 (향후 기능)
                print(f"[Info] WoRMS API로 '{korean_name}' 직접 검색 시도")
                # 현재 미구현 - 향후 WoRMS API에서 한글 지원시 추가
                pass
            except Exception as api_err:
                print(f"[Error] WoRMS API 검색 오류: {api_err}")
            
            # 모든 시도 실패 시
            self.search_status.config(text=f"'{korean_name}'에 대한 학명을 찾을 수 없습니다.")
            messagebox.showinfo("검색 실패", f"'{korean_name}'에 대한 학명을 찾을 수 없습니다.\n사전에 등록되지 않은 이름입니다.")
            # --- 실패 시에도 입력창 비우기 및 포커스 ---
            self.after(0, self.single_entry.delete, 0, tk.END)
            self.after(10, self.focus_entry)
            # --- 추가 끝 ---
            return False
            
        except Exception as e:
            print(f"[Error] 한글 이름 검색 오류: {e}")
            self.search_status.config(text=f"검색 오류: {str(e)}")
            messagebox.showerror("오류", f"검색 중 오류가 발생했습니다.\n{str(e)}")
            # --- 오류 시에도 입력창 비우기 및 포커스 ---
            self.after(0, self.single_entry.delete, 0, tk.END)
            self.after(10, self.focus_entry)
            # --- 추가 끝 ---
            return False

    def _perform_verification(self, verification_list_input): # 인자 이름 변경 (범용적으로)
        """주어진 목록(학명 문자열 리스트 또는 (국명, 학명 or None) 튜플 리스트)을 처리합니다."""
        # --- 입력 타입 확인 --- 
        is_korean_search = False
        if verification_list_input and isinstance(verification_list_input[0], tuple):
            is_korean_search = True
            original_input_display = verification_list_input[0][0] # 첫 국명
        elif verification_list_input: # 문자열 리스트인 경우
            original_input_display = verification_list_input[0] # 첫 학명
        else:
            original_input_display = "" # 빈 리스트
            
        error_occurred = False # 오류 발생 플래그
        error_message_details = "" # 오류 메시지 저장
        processed_results = [] # 최종 결과를 담을 리스트
        num_skipped_worms = 0 # WoRMS 검증 건너뛴 횟수 (국명 검색 시)

        try:
            if verify_species_list is None:
                raise ImportError("Core verifier module not loaded.")

            # UI 업데이트: 진행 중 표시 (총 개수 기준)
            total_items = len(verification_list_input)
            self.after(0, self._update_progress_label, f"총 {total_items}개 항목 처리 중...")
            self.after(0, self.progress_bar.set, 0) # 진행률 초기화

            # --- 처리 로직 분기 ---
            if is_korean_search:
                # --- 국명 입력 처리 --- 
                for i, item in enumerate(verification_list_input):
                    korean_name, scientific_name = item # 튜플 언패킹
                    
                    # 학명이 있는 경우 특수문자 제거 (제거, 이미 입력 시 특수문자 제거 완료)
                    # if scientific_name:
                    #    scientific_name = self._clean_scientific_name(scientific_name)
                    
                    # 진행률 표시 (개별 항목 시작 시 업데이트)
                    self.after(0, self._update_progress_label, f"'{korean_name}' 처리 중... ({i+1}/{total_items})")
                    self.after(0, self.update_progress, (i) / total_items) # 약간의 진행 표시
                    
                    result_entry = {} # 각 국명에 대한 결과 딕셔너리
                    
                    if scientific_name: # 학명이 있는 경우
                        # 단일 항목에 대한 WoRMS 검증 수행
                        print(f"[Info] Performing WoRMS verification for '{korean_name}' with scientific name '{scientific_name}'")
                        species_to_verify = [(korean_name, scientific_name, korean_name)]
                        
                        try:
                            verified_results = verify_species_list(species_to_verify)
                            if verified_results and len(verified_results) > 0:
                                result_entry = verified_results[0].copy()
                                result_entry['mapped_name'] = scientific_name # 매핑된 학명 필드 추가
                            else:
                                print(f"[Warning] No WoRMS result for {korean_name} (SciName: {scientific_name}). Creating basic entry.")
                                result_entry = self._create_basic_result(korean_name, scientific_name, False, "WoRMS 처리 오류")
                        except Exception as e:
                            print(f"[Error] WoRMS verification failed for '{korean_name}': {e}")
                            result_entry = self._create_basic_result(korean_name, scientific_name, False, "WoRMS 오류: " + str(e))
                    else: # 학명이 없었던 경우 (매핑 실패 등)
                        num_skipped_worms += 1 # WoRMS 생략 카운트 증가
                        result_entry = self._create_basic_result(korean_name, '-', False, 'N/A')

                    # 위키피디아 요약 검색 (학명이 성공적으로 찾아진 경우에만 국명으로 시도)
                    wiki_summary = '-' # 기본값
                    if scientific_name: # 학명이 있는 경우만 위키 검색
                        self.after(0, self._update_progress_label, f"'{korean_name}' 위키백과 검색 중... ({i+1}/{total_items})")
                        # wiki_summary = result_entry.get('wiki_summary', '-') # 이전 결과가 있을 수 있으나, 새로 가져옴
                        wiki_summary = self._get_wiki_summary(korean_name) # 헬퍼 함수 사용
                    
                    result_entry['wiki_summary'] = wiki_summary if wiki_summary else '정보 없음' # 최종 설정
                    
                    # 항목 하나에 대한 결과를 즉시 표시
                    self.after(0, self._update_results_display, [result_entry], False)
                    
                    # 진행률 업데이트
                    self.after(0, self.update_progress, (i + 1) / total_items)
            
            else: # --- 학명 입력 처리 --- 
                for i, scientific_name in enumerate(verification_list_input):
                    # 현재 처리 중인 학명 표시
                    self.after(0, self._update_progress_label, f"'{scientific_name}' 처리 중... ({i+1}/{total_items})")
                    self.after(0, self.update_progress, i / total_items)
                    
                    print(f"[Info] Performing WoRMS verification for scientific name: '{scientific_name}'")
                    
                    result_entry = None # 결과 초기화
                    # 단일 학명에 대한 WoRMS 검증 수행
                    try:
                        result_list = verify_species_list([scientific_name])
                        if result_list and len(result_list) > 0:
                            result_entry = result_list[0].copy()
                            input_scientific_name = result_entry['input_name'] # 입력된 학명
                            
                            # mapped_name 설정 (WoRMS 추천 이름이 있으면 반영)
                            if result_entry.get("similar_name") and result_entry["similar_name"] != "-":
                                result_entry["mapped_name"] = result_entry["similar_name"] + " (WoRMS 추천)"
                            else:
                                result_entry["mapped_name"] = input_scientific_name
                            
                            # 위키 요약 검색 (WoRMS 검증이 성공적이었거나 상태가 양호한 경우에만 시도)
                            wiki_summary = '-' # 기본값
                            # 검증 성공(is_verified=True) 또는 WoRMS 상태가 오류/결과없음 등이 아닐 때만 검색
                            current_worms_status = result_entry.get('worms_status', '').lower()
                            # 오류 상태 목록 정의 (더 명확하게)
                            error_statuses = ['-', 'n/a', 'error', 'no match', 'ambiguous', '형식 오류', 
                                              'worms 결과 없음', 'worms 처리 오류', '오류:', 'worms 오류:']
                            should_search_wiki = result_entry.get('is_verified') or \
                                                 not any(status in current_worms_status for status in error_statuses)
                            
                            if should_search_wiki:
                                self.after(0, self._update_progress_label, f"'{scientific_name}' 위키백과 검색 중... ({i+1}/{total_items})")
                                name_for_wiki = result_entry.get('scientific_name', scientific_name) # Use valid name if available
                                if name_for_wiki == '-': name_for_wiki = scientific_name
                                wiki_summary = self._get_wiki_summary(name_for_wiki)
                            
                            result_entry['wiki_summary'] = wiki_summary if wiki_summary else '정보 없음' # 최종 설정
                            
                            self.after(0, self._update_results_display, [result_entry], False)
                        else:
                            # WoRMS 결과가 없는 경우 기본 결과 생성 (위키 검색 안함)
                            result_entry = self._create_basic_result(scientific_name, scientific_name, False, "WoRMS 결과 없음")
                            result_entry['wiki_summary'] = '정보 없음' # 명시적으로 설정
                            self.after(0, self._update_results_display, [result_entry], False)
                    except Exception as e:
                        print(f"[Error] Error processing '{scientific_name}': {e}")
                        result_entry = self._create_basic_result(scientific_name, scientific_name, False, "오류: " + str(e))
                        result_entry['wiki_summary'] = '정보 없음' # 명시적으로 설정
                        self.after(0, self._update_results_display, [result_entry], False)
                    
                    # 진행률 업데이트
                    self.after(0, self.update_progress, (i + 1) / total_items)

        except Exception as e:
            error_occurred = True
            error_message_details = f"처리 중 오류 발생:\n{e}"
            import traceback
            traceback.print_exc() # 콘솔에 상세 오류 출력

        finally:
            # UI 상태 복원 및 진행 표시 완료
            self.after(0, self._set_ui_state, "normal")
            
            # 진행 상태 업데이트: 진행바 완료 및 텍스트 "완료"로 변경
            self.after(50, self.progress_bar.stop)
            self.after(50, self.progress_bar.configure, {'mode': 'determinate'})
            self.after(50, self.progress_bar.set, 1.0)
            
            # 진행 레이블 텍스트 설정 - 위치 변경하여 실행 보장
            status_label_text = "오류 발생" if error_occurred else "완료"
            print(f"[Debug] 진행 상태 업데이트: '{status_label_text}'") # 디버깅 로그 추가
            self.after(50, self._update_progress_label, status_label_text)
            
            # --- 최종 요약 메시지 생성 및 표시 (수정) --- 
            num_processed = len(verification_list_input) # 입력 개수 기준
            
            if error_occurred:
                final_summary_title = "오류 발생"
                final_summary_message = error_message_details
                msg_type = "error"
            else:
                final_summary_title = "완료"
                final_summary_message = f"{num_processed}개 항목 처리 완료."
                if is_korean_search and num_skipped_worms > 0: # 국명 검색 시에만 생략 메시지 추가
                     final_summary_message += f"\n({num_skipped_worms}개 항목은 학명이 없어 WoRMS 검증 생략됨)"
                msg_type = "info"
                
            # 진행 레이블 업데이트 재확인 (중요한 변경이므로 한번 더 호출)
            self.after(100, self._update_progress_label, status_label_text)
                
            self.after(150, lambda title=final_summary_title, msg=final_summary_message: \
                       self.show_centered_message(msg_type, title, msg)) 

            # --- 입력창 비우기 및 포커스 --- 
            self.after(200, self.single_entry.delete, 0, tk.END)
            self.after(250, self.focus_entry) # 포커스 복원

    # --- 헬퍼 함수: 위키피디아 요약 가져오기 (수정: 전체 내용 반환) ---
    def _get_wiki_summary(self, search_term):
        """주어진 검색어로 위키백과 페이지의 전체 내용을 가져옵니다."""
        try:
            print(f"[Info Wiki] '{search_term}' 위키백과 페이지 검색 시도")
            wikipedia.set_lang("ko") # 한국어 먼저 시도
            try:
                page = wikipedia.page(search_term, auto_suggest=False)
                print(f"[Info Wiki] '{search_term}' 한국어 페이지 찾음")
            except wikipedia.exceptions.PageError:
                print(f"[Info Wiki] '{search_term}' 한국어 페이지 없음, 영어로 시도")
                wikipedia.set_lang("en")
                page = wikipedia.page(search_term, auto_suggest=False) # 영어로 재시도
                print(f"[Info Wiki] '{search_term}' 영어 페이지 찾음")
            except wikipedia.exceptions.DisambiguationError as e:
                # 다의어 페이지의 첫 번째 옵션으로 재시도
                first_option = e.options[0]
                print(f"[Warning Wiki] '{search_term}' 다의어 페이지 발견, 첫 옵션 '{first_option}'으로 재시도")
                return self._get_wiki_summary(first_option) # 재귀 호출

            # 페이지 전체 내용 가져오기
            content = page.content
            if content and content.strip():
                print(f"[Info Wiki] '{search_term}' 전체 내용 ({len(content)} chars) 반환")
                return content # 전체 내용 반환
            else:
                 return "위키백과 내용 없음"

        except wikipedia.exceptions.PageError: # 최종적으로 페이지 못 찾은 경우
            return "위키백과 정보 없음"
        except wikipedia.exceptions.DisambiguationError: # 재귀 호출에서 또 다의어 만난 경우 (드뭄)
            return "위키백과 정보 없음 (다의어 처리 실패)"
        except requests.exceptions.RequestException as req_e:
             print(f"[Error Wiki] '{search_term}' 위키 네트워크 오류: {req_e}")
             return "위키백과 네트워크 오류"
        except Exception as wiki_e:
            print(f"[Error Wiki] '{search_term}' 위키 검색 중 오류 발생: {wiki_e}")
            return "위키백과 조회 중 오류 발생"
            
    # --- 헬퍼 함수: Treeview 업데이트 (기존 update_results 대체) ---
    def _update_results_display(self, results_list, clear_existing=False):
        """처리된 결과 목록을 Treeview에 표시합니다."""
        if not results_list:
            return
        
        # clear_existing이 True인 경우만 기존 결과 지움
        if clear_existing:
            self._clear_results_tree()
            self.current_results = []
        
        # 목록이 'id'를 가진 경우 그대로 추가
        if isinstance(results_list, list) and all(isinstance(res, dict) for res in results_list):
            # 내부 결과 목록에 추가
            self.current_results.extend(results_list)
            
            # 결과 목록 출력
            for result in results_list:
                input_name_display = result.get('input_name', '-')
                mapped_name_display = result.get('mapped_name', '-')
                tag = 'verified' if result.get('is_verified') else 'unverified'
                # WoRMS 추천 또는 N/A 상태일 때 caution 태그 추가
                if "WoRMS 추천" in mapped_name_display or result.get('worms_status') == 'N/A':
                    tag = 'caution'

                values = (
                    mapped_name_display,
                    "Yes" if result.get('is_verified') else "No",
                    result.get('worms_status', '-'),
                    result.get('worms_id', '-'),
                    result.get('worms_url', '-'),
                    result.get('wiki_summary', '-')
                )
                self.result_tree.insert("", "end", text=input_name_display, values=values, tags=(tag,))

        # 내보내기 버튼 활성화
        self.export_button.configure(state="normal")
        # 스크롤바 업데이트
        self.after(10, self._update_scrollbars)
        
    # --- 헬퍼 함수: Treeview 비우기 (추가) ---
    def _clear_results_tree(self):
        """Treeview의 모든 항목을 지웁니다."""
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        self.current_results = [] # 내부 결과 리스트도 비움
        self.export_button.configure(state="disabled") # 내보내기 버튼 비활성화

    # --- 헬퍼 함수: 기본 결과 딕셔너리 생성 (추가) ---
    def _create_basic_result(self, input_name, scientific_name, is_verified, worms_status):
        """기본적인 결과 딕셔너리를 생성합니다."""
        return {
            'input_name': input_name,
            'mapped_name': scientific_name, # 매핑된 학명 (없으면 '-')
            'similar_name': '-',
            'is_verified': is_verified,
            'worms_status': worms_status,
            'worms_id': '-',
            'worms_url': '-',
            'wiki_summary': '-' # 위키는 나중에 채워짐
        }

    def start_file_search_thread(self):
        """파일 기반 학명 검색을 위한 스레드를 시작합니다."""
        if not self.selected_file_path:
            self.show_centered_message("warning", "파일 오류", "검증할 파일을 선택하세요.") # 헬퍼 함수 사용
            return
        
        # --- API 키 사용 안내 팝업 제거 ---
        # self.show_centered_message("info", "안내", "파일 검증 시에는 '종 정보' 요약 기능(Gemini API)이 사용되지 않습니다.\nWoRMS 기반 검증만 수행됩니다.")
        # -------------------------------

        # UI 비활성화
        self._set_ui_state("disabled")
        self._show_progress_ui("파일 읽는 중...") # 진행률 UI 표시
        self.progress_bar.set(0) # 파일 검색은 확정 모드 사용
        self.progress_bar.configure(mode='determinate')

        thread = threading.Thread(target=self.search_file, args=(self.selected_file_path,), daemon=True)
        thread.start()

    def search_file(self, file_path):
        """파일에서 학명 목록을 읽어 검증하고 결과를 표시합니다."""
        skipped_names = [] 
        results_for_skipped = [] # 건너뛴 항목 결과 저장 리스트
        try:
            if verify_species_list is None:
                raise ImportError("Core verifier module not loaded.")

            # 파일 읽기 시작 레이블 업데이트
            self.after(0, self._update_progress_label, "파일 읽는 중...")
            try:
                if file_path.lower().endswith('.csv'):
                    # header=None으로 변경하여 첫 행도 데이터로 인식
                    df = pd.read_csv(file_path, header=None, skipinitialspace=True)
                elif file_path.lower().endswith(('.xls', '.xlsx')):
                    # header=None으로 변경하여 첫 행도 데이터로 인식
                    df = pd.read_excel(file_path, header=None)
                else:
                    raise ValueError("지원하지 않는 파일 형식입니다. CSV 또는 XLSX 파일을 사용하세요.")

                # 첫 번째 컬럼에서 학명 추출 (header=None이므로 모든 행 대상)
                if df.empty or len(df.columns) == 0:
                    raise ValueError("파일이 비어있거나 읽을 수 있는 컬럼이 없습니다.")
                species_list_all = df.iloc[:, 0].dropna().astype(str).unique().tolist()
                # 추가: 공백만 있는 문자열 제거 및 특수문자 제거
                species_list_all = [self._clean_scientific_name(name.strip()) for name in species_list_all if name.strip()]

            except Exception as e:
                self.after(0, lambda e=e: self.show_centered_message("error", "파일 읽기 오류", f"파일 처리 중 오류 발생:\n{e}"))
                # 파일 읽기 실패 시 상태 초기화 예약
                self.after(2000, self._reset_status_ui)
                self.after(0, self._set_ui_state, "normal") # UI 활성화
                return # 작업 중단

            # 파일 처리 개수 제한 로직 추가
            MAX_LIMIT = 500
            original_count = len(species_list_all)
            if original_count > MAX_LIMIT:
                message = f"파일에 포함된 학명({original_count}개)이 최대 제한({MAX_LIMIT}개)을 초과하여, 처음 {MAX_LIMIT}개만 처리합니다."
                self.after(0, lambda msg=message: self.show_centered_message("warning", "처리 개수 제한", msg))
                species_list_all = species_list_all[:MAX_LIMIT]

            # 빈 파일 또는 유효 데이터 없는 경우 처리
            if not species_list_all:
                self.after(0, lambda: self.show_centered_message("warning", "파일 오류", "파일에서 유효한 학명을 찾을 수 없습니다."))
                self.after(2000, self._reset_status_ui)
                self.after(0, self._set_ui_state, "normal")
                return

            # 학명 형식 검증 및 필터링
            species_list_valid = []
            for name in species_list_all:
                if self.is_valid_scientific_name_format(name):
                    species_list_valid.append(name)
                else:
                    skipped_names.append(name)
                    # 건너뛴 항목에 대한 결과 딕셔너리 생성
                    results_for_skipped.append({
                        "input_name": name,
                        "mapped_name": "-",  # 매핑된 학명 없음
                        "is_verified": False,
                        "worms_id": "-", 
                        "worms_status": "형식 오류",
                        "description": "-",
                        "scientific_name": "-"
                    })

            # 건너뛴 이름 알림 팝업 (선택 사항)
            if skipped_names:
                message = f"{len(skipped_names)}개 항목은 형식 오류로 건너뜀"
                self.after(0, lambda msg=message: self.show_centered_message("info", "일부 항목 건너뜀", msg))

            # 유효한 이름과 건너뛴 이름 모두 없을 경우 처리
            if not species_list_valid and not skipped_names:
                # 이 경우는 species_list가 비어있는 경우와 같음 (위에서 처리됨)
                pass
            # 유효한 이름은 없고 건너뛴 이름만 있을 경우
            elif not species_list_valid and skipped_names:
                self.after(0, lambda: self.show_centered_message("warning", "처리 불가", "파일에서 유효한 형식의 학명을 찾을 수 없습니다.\n형식 오류 항목만 발견되었습니다."))
                self.current_results = results_for_skipped # 형식 오류 결과만 저장
                self.after(0, self.update_results, self.current_results) # 형식 오류 결과 표시
                self.after(10, self._update_scrollbars)
                self.after(2000, self._reset_status_ui, True) 
                self.after(0, self._set_ui_state, "normal")
                return
            
            # --- 유효한 이름 검증 진행 (유효 이름이 하나 이상 있을 때) ---
            self.after(0, self._update_progress_label, "검증 시작...")
            # GUI 업데이트 콜백 정의
            def gui_progress_callback(progress_value):
                self.after(0, self.update_progress, progress_value)

            # 실제 검증 수행
            verified_results = verify_species_list(
                species_list_valid, 
                progress_callback=gui_progress_callback
            )
            
            # 검증 결과와 건너뛴 항목 결과 병합
            # 순서를 유지하려면 원래 목록 순서대로 다시 합치는 것이 좋으나, 여기서는 단순히 합침
            all_new_results = verified_results + results_for_skipped
            
            self.after(0, self.update_results, all_new_results) # 병합된 새 결과 전달

        except FileNotFoundError:
            self.after(0, lambda: self.show_centered_message("error", "파일 오류", f"파일을 찾을 수 없습니다: {file_path}"))
        except pd.errors.EmptyDataError:
            self.after(0, lambda: self.show_centered_message("warning", "파일 오류", "파일이 비어 있거나 읽을 수 있는 데이터가 없습니다."))
        except Exception as e:
            error_message = f"파일 처리 중 오류 발생: {e}"
            print(f"[Error] {error_message}")
            import traceback
            traceback.print_exc()
            self.after(0, lambda msg=error_message: self.show_centered_message("error", "오류", msg))
        finally:
            self.after(0, self._set_ui_state, "normal")

    def update_results(self, new_results):
        """새 검증 결과를 Treeview 끝에 추가하고, 100개 초과 시 오래된 항목 제거."""
        if not new_results:
            # 새 결과가 없으면 아무것도 안 함 (기존 결과 유지)
            self.after(10, self._update_scrollbars)
            return

        # 1. 새 결과 Treeview 끝에 추가
        for result in new_results:
            # 매핑된 학명 정보 포함하여 표시 (없으면 입력 학명과 동일하게 설정)
            mapped_name = result.get('mapped_name', result.get('input_name', '-'))
            
            # 'similar_name'이 있고 'input_name'과 다르면 'WoRMS 추천' 표시 (파일 처리 시나리오 고려)
            # check_scientific_name 함수에서 similar_name 필드를 채워주어야 함
            input_name_display = result.get('input_name', '-')
            if 'similar_name' in result and result['similar_name'] != '-' and result['similar_name'].lower() != input_name_display.lower():
                 mapped_name_display = f"{mapped_name} (WoRMS 추천: {result['similar_name']})"
                 tag = 'caution'
            else:
                 mapped_name_display = mapped_name
                 tag = 'verified' if result.get('is_verified') else 'unverified'

            values = (
                mapped_name_display, # 수정된 매핑 이름 표시
                "Yes" if result.get('is_verified') else "No",
                result.get('worms_status', '-'),
                result.get('worms_id', '-'),
                result.get('worms_url', '-'),
                result.get('wiki_summary', '-')
            )
            
            self.result_tree.insert("", "end", text=input_name_display, values=values, tags=(tag,)) # input_name_display 사용

        # 2. 총 개수 확인 및 MAX_RESULTS_DISPLAY 초과 시 오래된 항목 삭제
        all_items = self.result_tree.get_children()
        current_count = len(all_items)
        if current_count > self.MAX_RESULTS_DISPLAY:
            count_to_delete = current_count - self.MAX_RESULTS_DISPLAY
            items_to_delete = all_items[:count_to_delete]
            print(f"[Info] Result limit ({self.MAX_RESULTS_DISPLAY}) exceeded. Removing {count_to_delete} oldest items.")
            for item_id in items_to_delete:
                self.result_tree.delete(item_id)

        # 3. self.current_results 업데이트 (현재 보이는 내용 기준)
        self.current_results = []
        updated_items = self.result_tree.get_children()
        for item_id in updated_items:
            item_data = self.result_tree.item(item_id)
            input_name = item_data['text']
            values = item_data['values']
            # Treeview 값에서 result 딕셔너리 재구성
            result_dict = {
                'input_name': input_name,
                'mapped_name': values[0],  # 매핑된 학명
                'is_verified': values[1] == 'Yes',
                'worms_status': values[2],
                'worms_id': values[3],
                'worms_url': values[4],
                'wiki_summary': values[5]
            }
            self.current_results.append(result_dict)

        # 4. 내보내기 버튼 상태 업데이트
        if self.current_results:
            self.export_button.configure(state="normal")
        else:
            self.export_button.configure(state="disabled")

        # 5. 스크롤바 업데이트
        self.after(10, self._update_scrollbars)

    def _set_ui_state(self, state):
        """입력 위젯들의 활성/비활성 상태를 설정합니다."""
        self.single_entry.configure(state=state)
        self.single_search_button.configure(state=state)
        self.file_button.configure(state=state)
        self.mapping_button.configure(state=state) # 매핑 버튼 상태 추가
        # 파일 검색 버튼은 파일이 선택되었을 때만 활성화되도록 별도 관리
        if state == "normal" and self.selected_file_path:
             self.file_search_button.configure(state="normal")
        else:
             self.file_search_button.configure(state="disabled")

    def export_results_to_excel(self):
        """현재 Treeview에 표시된 결과를 Excel 파일로 저장합니다."""
        if not self.current_results:
            self.show_centered_message("warning", "내보내기 오류", "내보낼 결과가 없습니다.") # 헬퍼 함수 사용
            return

        try:
            file_path = filedialog.asksaveasfilename(
                title="결과 저장 위치 선택",
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
            )
            if not file_path:
                return # 사용자가 취소

            # 현재 Treeview에 표시된 결과(self.current_results) 사용
            if not self.current_results:
                self.show_centered_message("warning", "저장 오류", "저장할 결과 데이터가 없습니다.")
                return
            
            # 결과를 DataFrame으로 변환
            df_output = pd.DataFrame(self.current_results)

            # 필요한 컬럼 선택 및 순서 지정 (mapped_name 추가)
            output_columns = ['input_name', 'mapped_name', 'is_verified', 'worms_status', 'worms_id', 'worms_url', 'wiki_summary']
            # 결과에 없는 컬럼 생성 (보통은 다 있어야 함)
            for col in output_columns:
                if col not in df_output.columns:
                    df_output[col] = '-'
            df_output = df_output[output_columns] # 순서 및 컬럼 선택

            # 엑셀 헤더 이름 변경 (Mapped Name 추가)
            column_mapping_excel = {
                'input_name': '입력명',
                'mapped_name': '학명',  # '매핑된 학명'에서 '학명'으로 변경
                'is_verified': '검증됨',
                'worms_status': 'WoRMS 상태',
                'worms_id': 'WoRMS ID',
                'worms_url': 'WoRMS 링크',
                'wiki_summary': '종정보'  # '위키백과 요약'에서 '종정보'로 변경
            }
            df_output.rename(columns=column_mapping_excel, inplace=True)

            # Excel 파일로 저장
            df_output.to_excel(file_path, index=False)
            self.show_centered_message("info", "저장 완료", f"결과가 성공적으로 저장되었습니다:\n{file_path}")

        except Exception as e:
            # 오류 팝업 (헬퍼 함수 사용)
            self.show_centered_message("error", "저장 오류", f"결과 저장 중 오류 발생:\n{e}")

    # --- 헬퍼 함수: 팝업 중앙 표시 --- 
    def show_centered_message(self, msg_type, title, message):
        """Force UI update and show messagebox centered on the app window."""
        self.update_idletasks() # Force UI update
        parent_window = self.winfo_toplevel() # Get top-level window
        if msg_type == "info":
            messagebox.showinfo(title, message, parent=parent_window)
        elif msg_type == "warning":
            messagebox.showwarning(title, message, parent=parent_window)
        elif msg_type == "error":
            messagebox.showerror(title, message, parent=parent_window)

    # --- 헬퍼 함수: 학명 형식 검증 ---
    def is_valid_scientific_name_format(self, name):
        """Checks if the name likely follows scientific name format.
        - No Hangul
        - Allowed characters: letters, space, ., (), -\n        - Minimum length 3
        - No digits (except subspecies like Balanus ampritrite var 1)
        - Minimum 2 words (e.g., Genus species)
        """
        MIN_NAME_LENGTH = 3 # 최소 길이 설정
        MIN_WORD_COUNT = 2 # 최소 단어 수 설정

        if not name or not isinstance(name, str):
            print(f"[Debug Validation] Invalid: Empty or not string: {name}")
            return False
        
        # 0. 최소 길이 확인
        if len(name) < MIN_NAME_LENGTH:
            print(f"[Debug Validation] Invalid: Too short (less than {MIN_NAME_LENGTH}): {name}")
            return False
            
        # 1. 한글 포함 여부 확인
        if re.search(r'[ㄱ-ㅎㅏ-ㅣ가-힣]', name):
            print(f"[Debug Validation] Invalid: Contains Hangul: {name}")
            return False
        
        # 2. 숫자 포함 여부 확인에서 예외 추가 (var, subsp 등의 뒤에 나오는 숫자는 허용)
        if re.search(r'\d', name) and not re.search(r'(var|subsp|subspecies|form|f|variety)[. ]\d', name):
            print(f"[Debug Validation] Invalid: Contains digits not after var/subsp: {name}")
            return False
            
        # 3. 허용되지 않는 특수 문자 포함 여부 확인 (알파벳, 공백, ., (), - 외 문자)
        # 이미 _clean_scientific_name에서 제거했으므로, 여기서는 남은 특수문자만 체크
        if re.search(r'[^a-zA-Z .()\-]', name):
            print(f"[Debug Validation] Invalid: Contains disallowed characters: {name}")
            return False
            
        # 4. 최소한 하나 이상의 알파벳 문자를 포함하는지 확인
        if not re.search(r'[a-zA-Z]', name):
            print(f"[Debug Validation] Invalid: Does not contain letters: {name}")
            return False

        # 5. 최소 단어 수 확인 (공백 기준)
        words = name.split()
        if len(words) < MIN_WORD_COUNT:
            print(f"[Debug Validation] Invalid: Less than {MIN_WORD_COUNT} words: {name}")
            return False

        # 모든 검증 통과
        print(f"[Debug Validation] Valid format: {name}")
        return True

    # --- 헬퍼 함수: Treeview 더블 클릭 처리 (링크 컬럼 인덱스 확인) ---
    def on_tree_double_click(self, event):
        region = self.result_tree.identify("region", event.x, event.y)
        column_id = self.result_tree.identify_column(event.x)
        item_id = self.result_tree.identify_row(event.y)
        
        if not item_id or region != "cell":
            return

        column_index = int(column_id.replace('#', '')) - 1 # 컬럼 인덱스 계산 (0부터 시작)
        values = self.result_tree.item(item_id, "values")

        # WoRMS ID 컬럼 더블클릭 시 ID 복사 (컬럼 인덱스 3)
        if column_id == "#4": # 실제 컬럼 ID 확인 (WoRMS_ID는 #4)
            try:
                worms_id_value = values[3] # values 인덱스는 3
                if worms_id_value and worms_id_value != '-':
                    self._copy_to_clipboard(worms_id_value)
                    # 사용자에게 알림 (선택적)
                    self.show_centered_message("info", "복사 완료", f"WoRMS ID '{worms_id_value}'가 클립보드에 복사되었습니다.")
            except IndexError:
                print("[Warning] WoRMS ID 값을 가져올 수 없습니다.")
            except Exception as e:
                print(f"[Error] WoRMS ID 복사 중 오류: {e}")
                self.show_centered_message("error", "복사 오류", "WoRMS ID 복사 중 오류가 발생했습니다.")

        # WoRMS 링크 컬럼 클릭 시 링크 열기 (컬럼 인덱스 4)
        elif column_id == "#5": # WoRMS Link 컬럼 (인덱스 확인)
            try:
                url = values[4] # values 인덱스는 4
                if url and url != '-' and url.startswith('http'):
                    webbrowser.open_new_tab(url)
            except IndexError:
                print("[Warning] WoRMS 링크 값을 가져올 수 없습니다.")
            except Exception as e:
                print(f"[Error] Failed to open URL {url}: {e}")
                self.show_centered_message("error", "링크 오류", f"URL을 여는 데 실패했습니다:\n{url}")
        
        # 위키백과 요약 컬럼 클릭 시 팝업으로 내용 표시 (컬럼 인덱스 5)
        elif column_id == "#6": # 위키백과 요약 컬럼 (인덱스 확인)
            try:
                wiki_summary = values[5] # values 인덱스는 5
                input_name = self.result_tree.item(item_id, "text")
                
                if wiki_summary and wiki_summary != '-' and wiki_summary != '위키백과 정보 없음':
                    self._show_wiki_summary_popup(input_name, wiki_summary)
                else:
                    self.show_centered_message("info", "위키백과 정보 없음", f"'{input_name}'에 대한 위키백과 정보가 없습니다.")
            except IndexError:
                 print("[Warning] 위키백과 요약 값을 가져올 수 없습니다.")
            except Exception as e:
                 print(f"[Error] 위키백과 요약 표시 중 오류: {e}")

    def focus_entry(self):
        """메인 검색창에 포커스를 설정합니다."""
        self.single_entry.focus_set()
        
    def on_entry_focus_in(self, event):
        """입력 필드가 포커스를 얻을 때 처리"""
        # 도움말 레이블 제거로 인해 필요 없어진 코드
        pass
            
    def on_entry_focus_out(self, event):
        """입력 필드가 포커스를 잃을 때 처리"""
        # 도움말 레이블 제거로 인해 필요 없어진 코드
        pass
            
    def on_entry_key(self, event):
        """입력 필드에 키 입력이 있을 때 처리"""
        # 도움말 레이블 제거로 인해 필요 없어진 코드
        pass
    
    def check_entry_content(self):
        """입력 필드의 내용에 따라 도움말 레이블 표시/숨김 처리"""
        # 도움말 레이블 제거로 인해 필요 없어진 코드
        pass

    def open_mapping_manager(self):
        """국명-학명 매핑 관리 팝업 창을 엽니다."""
        # 팝업 창 생성
        mapping_window = ctk.CTkToplevel(self)
        mapping_window.title("국명-학명 매핑 관리")
        mapping_window.geometry("800x600")
        mapping_window.grab_set()  # 모달 창으로 설정
        
        # 레이아웃 설정
        mapping_window.grid_columnconfigure(0, weight=1)
        mapping_window.grid_rowconfigure(0, weight=0)  # 카테고리 선택
        mapping_window.grid_rowconfigure(1, weight=1)  # 매핑 목록
        mapping_window.grid_rowconfigure(2, weight=0)  # 새 매핑 추가
        mapping_window.grid_rowconfigure(3, weight=0)  # 버튼 영역
        
        # 카테고리 프레임
        category_frame = ctk.CTkFrame(mapping_window)
        category_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        
        # 카테고리 선택 레이블
        category_label = ctk.CTkLabel(category_frame, text="카테고리:", font=self.default_bold_font)
        category_label.grid(row=0, column=0, padx=(20, 10), pady=10, sticky="w")
        
        # 카테고리 변수 및 기본값 설정
        categories = list(DEFAULT_MAPPINGS.keys())
        current_category = tk.StringVar(value=categories[0])
        
        # 카테고리 콤보박스
        category_combobox = ctk.CTkComboBox(category_frame, values=categories, 
                                           variable=current_category, width=200,
                                           font=self.default_font)
        category_combobox.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        
        # 매핑 목록 프레임
        mapping_frame = ctk.CTkFrame(mapping_window)
        mapping_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        mapping_frame.grid_columnconfigure(0, weight=1)
        mapping_frame.grid_rowconfigure(0, weight=1)
        
        # 매핑 목록 트리뷰
        columns = ("scientific_name")
        mapping_tree = ttk.Treeview(mapping_frame, columns=columns, show="tree headings")
        mapping_tree.grid(row=0, column=0, padx=(15, 0), pady=(15, 0), sticky="nsew")
        
        # 트리뷰 설정
        mapping_tree.heading("#0", text="한글 국명")
        mapping_tree.heading("scientific_name", text="학명")
        mapping_tree.column("#0", width=150, anchor=tk.W)
        mapping_tree.column("scientific_name", width=300, anchor=tk.W)
        
        # 트리뷰 스크롤바
        tree_scrollbar_y = ctk.CTkScrollbar(mapping_frame, command=mapping_tree.yview)
        tree_scrollbar_y.grid(row=0, column=1, padx=(0, 15), pady=(15, 0), sticky="ns")
        mapping_tree.configure(yscrollcommand=tree_scrollbar_y.set)
        
        # 새 매핑 추가 프레임
        add_frame = ctk.CTkFrame(mapping_window)
        add_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        
        # 레이블
        korean_label = ctk.CTkLabel(add_frame, text="한글 국명:", font=self.default_font)
        korean_label.grid(row=0, column=0, padx=(20, 10), pady=10, sticky="w")
        scientific_label = ctk.CTkLabel(add_frame, text="학명:", font=self.default_font)
        scientific_label.grid(row=0, column=2, padx=(20, 10), pady=10, sticky="w")
        
        # 입력 필드
        korean_entry = ctk.CTkEntry(add_frame, width=150, font=self.default_font)
        korean_entry.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        scientific_entry = ctk.CTkEntry(add_frame, width=250, font=self.default_font)
        scientific_entry.grid(row=0, column=3, padx=10, pady=10, sticky="w")
        
        # 추가 버튼
        add_button = ctk.CTkButton(add_frame, text="추가", width=80, font=self.default_bold_font)
        add_button.grid(row=0, column=4, padx=(20, 10), pady=10, sticky="w")
        
        # 버튼 프레임
        button_frame = ctk.CTkFrame(mapping_window)
        button_frame.grid(row=3, column=0, padx=20, pady=(10, 20), sticky="ew")
        button_frame.grid_columnconfigure((0, 1, 2, 3), weight=1) # 버튼 공간 분배
        
        # 버튼
        import_button = ctk.CTkButton(button_frame, text="Excel 가져오기", width=140, 
                                     font=self.default_bold_font)
        import_button.grid(row=0, column=0, padx=(20, 10), pady=10, sticky="w")
        
        export_button = ctk.CTkButton(button_frame, text="Excel 내보내기", width=140, 
                                     font=self.default_bold_font)
        export_button.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        
        delete_button = ctk.CTkButton(button_frame, text="선택 항목 삭제", width=140, 
                                     font=self.default_bold_font, fg_color="#E74C3C")
        delete_button.grid(row=0, column=2, padx=10, pady=10, sticky="e")
        
        save_button = ctk.CTkButton(button_frame, text="저장", width=140, font=self.default_bold_font)
        save_button.grid(row=0, column=3, padx=10, pady=10, sticky="e")
        
        cancel_button = ctk.CTkButton(button_frame, text="취소", width=140, font=self.default_bold_font,
                                     command=mapping_window.destroy)
        cancel_button.grid(row=0, column=4, padx=(10, 20), pady=10, sticky="e")
        
        # 현재 매핑 데이터
        mappings_data = {}
        try:
            with open(mappings_file, 'r', encoding='utf-8') as f:
                mappings_data = json.load(f)
        except Exception as e:
            print(f"[Error] 매핑 파일 로드 오류: {e}")
            mappings_data = DEFAULT_MAPPINGS.copy()
        
        # 매핑 트리뷰 업데이트 함수
        def update_mapping_tree(category):
            # 기존 항목 제거
            for item in mapping_tree.get_children():
                mapping_tree.delete(item)
            
            # 선택된 카테고리의 매핑 추가
            if category in mappings_data:
                for korean, scientific in mappings_data[category].items():
                    mapping_tree.insert("", "end", text=korean, values=(scientific,))
        
        # 카테고리 변경 시 트리뷰 업데이트
        def on_category_change(event):
            update_mapping_tree(current_category.get())
        
        category_combobox.bind("<<ComboboxSelected>>", on_category_change)
        
        # 항목 추가 함수
        def add_mapping():
            korean = korean_entry.get().strip()
            scientific = scientific_entry.get().strip()
            category = current_category.get()
            
            if not korean or not scientific:
                messagebox.showwarning("입력 오류", "한글 국명과 학명을 모두 입력해주세요.", parent=mapping_window)
                return
            
            # 카테고리가 없으면 생성
            if category not in mappings_data:
                mappings_data[category] = {}
            
            # 매핑 추가
            mappings_data[category][korean] = scientific
            
            # 트리뷰 업데이트
            update_mapping_tree(category)
            
            # 입력 필드 초기화
            korean_entry.delete(0, 'end')
            scientific_entry.delete(0, 'end')
        
        add_button.configure(command=add_mapping)
        
        # 항목 삭제 함수
        def delete_mapping():
            selected = mapping_tree.selection()
            if not selected:
                messagebox.showwarning("선택 오류", "삭제할 항목을 선택해주세요.", parent=mapping_window)
                return
            
            category = current_category.get()
            for item in selected:
                korean = mapping_tree.item(item, 'text')
                if category in mappings_data and korean in mappings_data[category]:
                    del mappings_data[category][korean]
            
            # 트리뷰 업데이트
            update_mapping_tree(category)
        
        delete_button.configure(command=delete_mapping)
        
        # 저장 함수
        def save_mappings():
            try:
                # 매핑 파일 저장
                save_korean_mappings(mappings_data)
                
                # 애플리케이션 매핑 업데이트
                flat_mappings = {}
                for cat in mappings_data:
                    flat_mappings.update(mappings_data[cat])
                    
                # 클래스 변수와 전역 변수 모두 업데이트
                self.korean_name_mappings = flat_mappings
                global KOREAN_NAME_MAPPINGS
                KOREAN_NAME_MAPPINGS = flat_mappings
                
                print(f"[Info] 매핑 정보가 업데이트되었습니다. 총 {len(flat_mappings)}개 항목.")
                print(f"[Debug] 업데이트된 매핑 테이블 내용: {list(flat_mappings.keys())}")
                
                messagebox.showinfo("저장 완료", "매핑 정보가 저장되었습니다.", parent=mapping_window)
                mapping_window.destroy()
            except Exception as e:
                messagebox.showerror("저장 오류", f"매핑 정보 저장 중 오류가 발생했습니다:\n{e}", parent=mapping_window)
        
        save_button.configure(command=save_mappings)
        
        # --- 엑셀 가져오기 함수 ---
        def import_from_excel():
            nonlocal mappings_data # 외부 함수의 변수 수정
            try:
                file_path = filedialog.askopenfilename(
                    title="매핑 정보 가져올 Excel 파일 선택",
                    filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                    parent=mapping_window
                )
                if not file_path:
                    return

                # 엑셀 파일 읽기 (첫 번째 시트, '국명', '학명' 컬럼 가정)
                try:
                    df = pd.read_excel(file_path, sheet_name=0)
                    # 필수 컬럼 확인
                    if '국명' not in df.columns or '학명' not in df.columns:
                         messagebox.showerror("가져오기 오류", "Excel 파일에 '국명' 및 '학명' 컬럼이 필요합니다.", parent=mapping_window)
                         return
                    # 카테고리 컬럼 확인 (선택 사항)
                    has_category = '카테고리' in df.columns
                except Exception as read_e:
                     messagebox.showerror("가져오기 오류", f"Excel 파일 읽기 실패:\n{read_e}", parent=mapping_window)
                     return
                
                # 기존 데이터 처리 방식 선택 (병합 또는 덮어쓰기)
                # 여기서는 간단하게 '덮어쓰기'로 구현
                # TODO: 사용자에게 병합/덮어쓰기 선택 옵션 제공 고려
                confirm = messagebox.askyesno("확인", "기존 매핑 정보를 덮어쓰시겠습니까?", parent=mapping_window)
                if not confirm:
                    return
                    
                new_mappings = {}
                imported_count = 0
                skipped_count = 0
                
                for index, row in df.iterrows():
                    korean = str(row['국명']).strip()
                    scientific = str(row['학명']).strip()
                    category = str(row['카테고리']).strip() if has_category and pd.notna(row['카테고리']) else "기타" # 기본 카테고리
                    
                    if korean and scientific:
                        if category not in new_mappings:
                            new_mappings[category] = {}
                        new_mappings[category][korean] = scientific
                        imported_count += 1
                    else:
                        skipped_count += 1
                        
                if not new_mappings:
                     messagebox.showwarning("가져오기 결과", "가져올 유효한 매핑 정보가 없습니다.", parent=mapping_window)
                     return
                
                # 기존 데이터 덮어쓰기
                mappings_data = new_mappings
                
                # 카테고리 콤보박스 업데이트
                categories = list(mappings_data.keys())
                category_combobox.configure(values=categories)
                current_category.set(categories[0] if categories else "")
                
                # 트리뷰 업데이트
                update_mapping_tree(current_category.get())
                
                info_msg = f"{imported_count}개의 매핑 정보를 가져왔습니다."
                if skipped_count > 0:
                    info_msg += f"\n{skipped_count}개의 행은 국명 또는 학명이 비어있어 건너뛰었습니다."
                messagebox.showinfo("가져오기 완료", info_msg, parent=mapping_window)

            except Exception as e:
                messagebox.showerror("가져오기 오류", f"매핑 정보 가져오기 중 오류 발생:\n{e}", parent=mapping_window)
        
        import_button.configure(command=import_from_excel)

        # --- 엑셀 내보내기 함수 ---
        def export_to_excel():
            try:
                file_path = filedialog.asksaveasfilename(
                    title="매핑 정보 저장할 Excel 파일 선택",
                    defaultextension=".xlsx",
                    filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                    parent=mapping_window
                )
                if not file_path:
                    return

                # 내보낼 데이터 준비 (카테고리 포함)
                export_data = []
                for category, items in mappings_data.items():
                    for korean, scientific in items.items():
                        export_data.append({
                            "카테고리": category,
                            "국명": korean,
                            "학명": scientific
                        })
                
                if not export_data:
                    messagebox.showwarning("내보내기 오류", "내보낼 매핑 정보가 없습니다.", parent=mapping_window)
                    return

                # DataFrame 생성 및 Excel 저장
                df = pd.DataFrame(export_data)
                df.to_excel(file_path, index=False)
                messagebox.showinfo("내보내기 완료", f"매핑 정보가 성공적으로 저장되었습니다:\n{file_path}", parent=mapping_window)

            except Exception as e:
                messagebox.showerror("내보내기 오류", f"매핑 정보 내보내기 중 오류 발생:\n{e}", parent=mapping_window)
        
        export_button.configure(command=export_to_excel)
        
        # 초기 트리뷰 업데이트
        update_mapping_tree(current_category.get())

    # --- 위키백과 학명 추출 함수 (클래스 내부) ---
    def _extract_scientific_name_from_wiki(self, korean_name):
        """주어진 국명으로 위키백과를 검색하여 학명을 추출합니다."""
        try:
            wikipedia.set_lang("ko")
            page = wikipedia.page(korean_name, auto_suggest=False) # auto_suggest=False로 정확한 이름 검색
            
            # 1. 요약(summary)에서 학명 패턴 찾기 (Genus species)
            #    더 정확한 패턴: 라틴어 단어 + 라틴어 단어 (가끔 뒤에 L. 같은 게 붙기도 함)
            #    이탤릭체로 된 학명을 찾는 것이 가장 이상적이지만, 위키피디아 라이브러리만으로는 어려움
            summary = page.summary
            # 첫 번째 이탤릭체로 감싸진 부분 찾기 (HTML 파싱이 필요할 수 있으나, 간단하게 정규식 시도)
            # 예: ''Genus species''
            italic_match = re.search(r"''([A-Z][a-z]+ [a-z]+)''", summary)
            if italic_match:
                print(f"[Debug Wiki] 요약 이탤릭체 학명 찾음: {italic_match.group(1)}")
                return italic_match.group(1)

            # 2. 요약에서 '학명:' 뒤 패턴 찾기
            #    더 구체적인 패턴으로 수정 (학명: 다음의 라틴어 이름)
            explicit_match = re.search(r"학명:\s*([A-Z][a-z]+\\s[a-z]+(?:\\s[a-z]+)?)", summary, re.IGNORECASE)
            if explicit_match:
                print(f"[Debug Wiki] '학명:' 패턴 학명 찾음: {explicit_match.group(1)}")
                return explicit_match.group(1).strip()

            # 3. 페이지 내용에서 학명 패턴 찾기 (더 일반적인 패턴)
            #    페이지 내용 전체를 검색하는 것은 비효율적이므로, 첫 문단 정도만 확인
            #    간단한 (Genus species) 형태만 찾기
            content_match = re.search(r"\(([A-Z][a-z]+ [a-z]+)\)", page.content[:500]) # 첫 500자
            if content_match:
                print(f"[Debug Wiki] 내용 괄호 학명 찾음: {content_match.group(1)}")
                return content_match.group(1)

            print(f"[Info Wiki] '{korean_name}' 위키백과에서 학명 추출 실패 (패턴 불일치)")
            return None

        except wikipedia.exceptions.PageError:
            print(f"[Info Wiki] '{korean_name}'에 대한 위키백과 페이지 없음")
            return None
        except wikipedia.exceptions.DisambiguationError as e:
            print(f"[Warning Wiki] '{korean_name}' 다의어 페이지 발견: {e.options[:3]}")
            # 다의어 페이지의 첫 번째 옵션으로 재시도 (선택적)
            try:
                first_option = e.options[0]
                print(f"[Info Wiki] 다의어 첫 번째 옵션 '{first_option}'으로 재시도")
                return self._extract_scientific_name_from_wiki(first_option) # 재귀 호출
            except Exception:
                 return None # 재시도 실패
        except requests.exceptions.RequestException as e:
             print(f"[Error Wiki] 위키백과 네트워크 오류: {e}")
             return None
        except Exception as e:
            print(f"[Error Wiki] 위키백과 처리 중 예외 발생 ({korean_name}): {e}")
            import traceback
            traceback.print_exc() # 상세 오류 출력
            return None

    # --- 오른쪽 클릭 메뉴 표시 함수 (신규) ---
    def _show_context_menu(self, event):
        """Treeview 오른쪽 클릭 시 컨텍스트 메뉴를 표시합니다."""
        # 클릭된 위치의 아이템 확인
        item_id = self.result_tree.identify_row(event.y)
        if not item_id:
            return
            
        # 해당 아이템 선택
        self.result_tree.selection_set(item_id)
        
        # 컨텍스트 메뉴 생성
        context_menu = tk.Menu(self, tearoff=0)
        
        values = self.result_tree.item(item_id, "values")
        input_name = self.result_tree.item(item_id, "text") # 위키 링크용
        
        # WoRMS ID 값 가져오기 (인덱스 3)
        try:
            worms_id_value = values[3]
            if worms_id_value and worms_id_value != '-':
                context_menu.add_command(label="WoRMS ID 복사", command=lambda w_id=worms_id_value: self._copy_to_clipboard(w_id))
            else:
                context_menu.add_command(label="복사할 WoRMS ID 없음", state="disabled")
        except IndexError:
             context_menu.add_command(label="WoRMS ID 정보 없음", state="disabled")
             
        # WoRMS 링크 열기 (인덱스 4)
        try:
            worms_url = values[4]
            if worms_url and worms_url != '-' and worms_url.startswith('http'):
                context_menu.add_command(label="WoRMS 링크 열기", command=lambda url=worms_url: webbrowser.open_new_tab(url))
            else:
                 context_menu.add_command(label="WoRMS 링크 없음", state="disabled")
        except IndexError:
             context_menu.add_command(label="WoRMS 링크 정보 없음", state="disabled")

        # 위키백과 페이지 열기 (input_name 사용)
        wiki_url = f"https://ko.wikipedia.org/wiki/{input_name.replace(' ', '_')}" # 공백을 언더스코어로
        context_menu.add_command(label="위키백과 페이지 열기", command=lambda url=wiki_url: webbrowser.open_new_tab(url))
             
        # 메뉴 표시
        context_menu.tk_popup(event.x_root, event.y_root)

    # --- 클립보드 복사 함수 (신규) ---
    def _copy_to_clipboard(self, text):
        """주어진 텍스트를 클립보드에 복사합니다."""
        try:
            self.clipboard_clear()
            self.clipboard_append(text)
            print(f"[Info] Copied to clipboard: {text}")
            # (선택적) 사용자에게 알림
            # self.show_centered_message("info", "복사 완료", f"'{text}'가 클립보드에 복사되었습니다.")
        except Exception as e:
            print(f"[Error] Failed to copy to clipboard: {e}")
            self.show_centered_message("error", "복사 오류", "클립보드 복사 중 오류가 발생했습니다.")

    # --- 헬퍼 함수: 위키 요약 팝업 (수정: 출처 표시 및 복사 버튼 추가) ---
    def _show_wiki_summary_popup(self, title, wiki_summary):
        """위키백과 요약 내용을 팝업 창으로 표시하고 복사 기능을 제공합니다."""
        popup = ctk.CTkToplevel(self)
        popup.title(f"종정보: {title}") # 제목 변경
        popup.geometry("700x550")  # 팝업 창 크기 조정 (버튼 공간 확보)
        popup.grab_set()  # 모달 창으로 설정
        
        # 레이아웃 설정
        popup.grid_columnconfigure(0, weight=1)
        popup.grid_rowconfigure(0, weight=0)  # 제목
        popup.grid_rowconfigure(1, weight=1)  # 내용
        popup.grid_rowconfigure(2, weight=0)  # 하단 프레임 (버튼, 출처)
        
        # 제목 레이블 - 볼드체 명확히 제거
        title_label = ctk.CTkLabel(popup, text=f"{title}", font=ctk.CTkFont(family="Malgun Gothic", size=14, weight="normal"))
        title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # 내용 프레임 (스크롤 가능)
        content_frame = ctk.CTkFrame(popup)
        content_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)
        
        # 텍스트 위젯 (스크롤 가능) - 명확히 normal weight 지정
        text_widget = ctk.CTkTextbox(content_frame, wrap="word", font=ctk.CTkFont(family="Malgun Gothic", size=12, weight="normal"))
        text_widget.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        text_widget.insert("1.0", wiki_summary)
        text_widget.configure(state="disabled")  # 읽기 전용으로 설정
        
        # 하단 프레임 (버튼, 출처용)
        bottom_frame = ctk.CTkFrame(popup)
        bottom_frame.grid(row=2, column=0, padx=20, pady=(10, 20), sticky="ew")
        bottom_frame.grid_columnconfigure(0, weight=1) # 출처 레이블 공간
        bottom_frame.grid_columnconfigure(1, weight=0) # 복사 버튼 공간
        bottom_frame.grid_columnconfigure(2, weight=0) # 닫기 버튼 공간

        # 출처 레이블
        source_label = ctk.CTkLabel(bottom_frame, text="자료 출처: 위키백과", 
                                      font=CTkFont(family="Malgun Gothic", size=9, slant="italic"), 
                                      text_color=("gray60", "gray50"))
        source_label.grid(row=0, column=0, padx=(0, 10), sticky="w")
        
        # 내용 복사 버튼
        copy_button = ctk.CTkButton(bottom_frame, text="내용 복사", width=90, 
                                     font=CTkFont(family="Malgun Gothic", size=10), # 작은 폰트
                                     command=lambda: self._copy_to_clipboard(wiki_summary)) # 현재 팝업 내용 복사
        copy_button.grid(row=0, column=1, padx=(0, 10))

        # 닫기 버튼
        close_button = ctk.CTkButton(bottom_frame, text="닫기", command=popup.destroy, width=90, 
                                      font=CTkFont(family="Malgun Gothic", size=11, weight="normal"))
        close_button.grid(row=0, column=2, padx=(0, 0)) # 오른쪽 끝에 배치

    # --- 헬퍼 함수: 툴팁 표시 (신규) ---
    def _show_tooltip(self, text, x, y):
        """마우스 커서 근처에 툴팁 팝업을 표시합니다."""
        if self.tooltip_window:
            self.tooltip_window.destroy()

        # 툴팁 위치 조정 (마우스 커서 오른쪽 아래)
        x_offset = 15
        y_offset = 10
        
        # 툴팁 윈도우 생성 (CTkToplevel 대신 tk.Toplevel 사용 - 더 가벼움)
        self.tooltip_window = tk.Toplevel(self)
        self.tooltip_window.wm_overrideredirect(True) # 창 테두리 및 제목 표시줄 제거
        self.tooltip_window.wm_geometry(f"+{x + x_offset}+{y + y_offset}") # 위치 설정
        
        # 툴팁 레이블 생성 및 배치
        tooltip_label = ctk.CTkLabel(self.tooltip_window, text=text, 
                                     font=CTkFont(family="Malgun Gothic", size=10), 
                                     corner_radius=4, # 약간의 둥근 모서리
                                     fg_color=("gray90", "gray20"), # 배경색
                                     padx=5, pady=3) # 내부 여백
        tooltip_label.pack()

    # --- 헬퍼 함수: 툴팁 숨기기 (신규) ---
    def _hide_tooltip(self):
        """툴팁 팝업을 숨깁니다."""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

    # --- 이벤트 핸들러: Treeview 마우스 움직임 (툴팁용, 신규) ---
    def _on_tree_motion(self, event):
        """마우스가 Treeview 위에서 움직일 때 툴팁을 표시하거나 숨깁니다."""
        region = self.result_tree.identify("region", event.x, event.y)
        
        # 헤더 영역 위에 있을 때만 툴팁 표시
        if region == "heading":
            column_id = self.result_tree.identify_column(event.x)
            tooltip_text = None
            
            if column_id == "#4": # WoRMS ID 컬럼 헤더 ("WoRMS ID(?)")
                tooltip_text = "더블 클릭 시 WoRMS ID 복사됨"
            elif column_id == "#5": # WoRMS Link 컬럼 헤더 ("WoRMS 링크(?)")
                tooltip_text = "더블 클릭 시 WoRMS 웹사이트 확인"
            elif column_id == "#6": # 종정보 컬럼 헤더 ("종정보(?)")
                tooltip_text = "더블 클릭 시 종정보 확인 가능"
            
            if tooltip_text:
                self._show_tooltip(tooltip_text, event.x_root, event.y_root)
            else:
                self._hide_tooltip() # 해당 헤더가 아니면 숨김
        else:
            self._hide_tooltip() # 헤더 영역이 아니면 숨김

    # --- 이벤트 핸들러: Treeview 마우스 벗어남 (툴팁용, 신규) ---
    def _on_tree_leave(self, event):
        """마우스가 Treeview 영역을 벗어날 때 툴팁을 숨깁니다."""
        self._hide_tooltip()


if __name__ == "__main__":
    # 매핑 테이블 확인
    print("\n=== 매핑 테이블 디버깅 정보 ===")
    print(f"전역 매핑 테이블 항목 수: {len(KOREAN_NAME_MAPPINGS)}")
    # 전체 키 대신 샘플만 표시
    sample_keys = list(KOREAN_NAME_MAPPINGS.keys())[:5]
    print(f"전역 매핑 테이블 샘플 항목: {sample_keys}{'...' if len(KOREAN_NAME_MAPPINGS) > 5 else ''}")
    print(f"'감성돔' 매핑 값: {KOREAN_NAME_MAPPINGS.get('감성돔', '없음')}")
    print(f"'전복' 매핑 값: {KOREAN_NAME_MAPPINGS.get('전복', '없음')}")
    print("==========================\n")
    
    # Check if core module loaded successfully before starting the app
    if verify_species_list is None:
        # Display a simple Tkinter error message if core parts failed to load
        root = tk.Tk()
        root.withdraw() # Hide the main window
        tk.messagebox.showerror("Initialization Error",
                               "Failed to load core components. Please check the console logs.\nApplication will now exit.")
        root.destroy()
        sys.exit(1) # Exit if core components are missing

    app = SpeciesVerifierApp()
    # 앱 시작 시 학명 입력창에 포커스 설정 (약간의 지연 시간을 두어 GUI가 완전히 로드된 후에 실행)
    app.after(100, app.focus_entry)
    app.mainloop()