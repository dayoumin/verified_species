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
import time
import uuid
import numpy as np

# --- 설정 로드 --- 
import config # config 모듈 임포트

# --- 모듈 임포트 ---
# 핵심 검증 로직 및 유틸리티 함수 임포트
from species_verifier.core import verifier 
from species_verifier.core import wiki
from species_verifier.utils import helpers

# --- 시간 제한 설정 (유지) ---
# config.py로 이동 고려
EXPIRY_DAYS = 547
CONTACT_EMAIL = "ecomarin@naver.com"
DATE_FILE_NAME = ".verifier_expiry_date"

# --- WoRMS API 정보 (config 사용) ---
# WORMS_API_BASE_URL = "https://www.marinespecies.org/rest" # 제거 (config 사용)

# --- 경로 설정 (config 사용) ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
# 데이터 파일 경로 설정 (config 사용)
# data_dir = os.path.join(os.path.dirname(__file__), '..', 'data') # 제거 (config 사용)
# mappings_file = os.path.join(data_dir, 'korean_scientific_mappings.json') # 제거 (config 사용)

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
        # config에서 파일 경로 사용
        if os.path.exists(config.MAPPINGS_FILE_PATH):
            with open(config.MAPPINGS_FILE_PATH, 'r', encoding='utf-8') as f:
                print(f"[Info] 매핑 파일 로드: {config.MAPPINGS_FILE_PATH}")
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
            print(f"[Warning] 매핑 파일을 찾을 수 없음: {config.MAPPINGS_FILE_PATH}")
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
        # config에서 파일 경로 사용
        # 디렉토리가 없으면 생성 (config.DATA_DIR 사용)
        os.makedirs(config.DATA_DIR, exist_ok=True)
        with open(config.MAPPINGS_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(mappings_data, f, ensure_ascii=False, indent=2)
            print(f"[Info] 매핑 파일 저장 완료: {config.MAPPINGS_FILE_PATH}")
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
# --- 추가: 미생물 검증 함수 임포트 준비 ---
verify_microbe_name = None 
try:
    # Attempt to import necessary functions from the core module
    # Import other core functions if needed by the GUI later
    from species_verifier.core.verifier import verify_species_list, check_scientific_name
    print("[Debug] Successfully imported 'verify_species_list' and 'check_scientific_name' from core.verifier.")
    # --- 미생물 검증 함수 임포트 시도 (아직 없을 수 있음) ---
    try:
        from species_verifier.core.verifier import verify_microbe_name # 실제 함수 이름으로 변경 필요
        print("[Debug] Successfully imported 'verify_microbe_name' from core.verifier.")
    except ImportError:
        print("[Warning] Microbe verification function 'verify_microbe_name' not found in core.verifier. Microbe tab functionality will be limited.")
        verify_microbe_name = None # 함수가 없으면 None으로 유지
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
        self.korean_name_mappings = KOREAN_NAME_MAPPINGS  # 전역 변수 재사용
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

        # --- 2단계: 탭 지원을 위한 변수 추가 ---
        # 활성 탭 및 탭별 결과 저장 변수
        self.active_tab = "해양생물"  # 기본 활성 탭
        self.current_results_marine = []  # 해양생물 탭 결과
        self.current_results_microbe = []  # 미생물 탭 결과
        self.current_results = []  # 이전 코드 호환성 유지 (기존 결과 저장 변수)
        # --- 변수 추가 끝 ---

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

        # --- 수정: 현재 활성 탭 결과 저장 ---
        self.current_results_marine = []
        self.current_results_microbe = []
        self.active_tab = "해양생물" # 기본 활성 탭
        # --- 수정 끝 ---

        # --- 설정 값 사용 (config 모듈 참조) ---
        self.MAX_RESULTS_DISPLAY = config.MAX_RESULTS_DISPLAY # Treeview 결과 표시 최대 개수
        self.MAX_FILE_PROCESSING_LIMIT = config.MAX_FILE_PROCESSING_LIMIT # 파일 처리 최대 학명 수
        self.DIRECT_EXPORT_THRESHOLD = config.DIRECT_EXPORT_THRESHOLD # Treeview 대신 바로 파일로 저장할 임계값

        # --- 프레임 설정 --- (Title 프레임 제거, 푸터는 유지)
        self.grid_columnconfigure(0, weight=1)
        # --- 수정: 행 구성을 탭 뷰, 상태, 푸터로 변경 ---
        self.grid_rowconfigure(0, weight=1) # Tab view (row 0)
        self.grid_rowconfigure(1, weight=0) # Status frame (row 1)
        self.grid_rowconfigure(2, weight=0) # Footer frame (row 2)
        # --- 수정 끝 ---

        # --- 탭 뷰 생성 ---
        self.tab_view = ctk.CTkTabview(self, command=self._on_tab_change)
        self.tab_view.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="nsew")
        self.tab_view.add("해양생물(WoRMS)")
        self.tab_view.add("미생물 (LPSN)")
        self.tab_view.add("담수 등 전체생물(COL)")  # "통합생물(COL)"에서 변경
        # --- 탭 뷰 생성 끝 ---

        # --- "해양생물(WoRMS)" 탭 설정 ---
        marine_tab = self.tab_view.tab("해양생물(WoRMS)")
        marine_tab.grid_columnconfigure(0, weight=1)
        marine_tab.grid_rowconfigure(0, weight=0) # Input frame
        marine_tab.grid_rowconfigure(1, weight=1) # Result frame

        # 입력 프레임 ("해양생물" 탭)
        self.input_frame = ctk.CTkFrame(marine_tab)
        self.input_frame.grid(row=0, column=0, padx=0, pady=0, sticky="nsew") # 탭 내에서는 padx/pady 0
        self.input_frame.grid_columnconfigure(1, weight=1)

        # 결과 프레임 ("해양생물" 탭)
        self.result_frame_marine = ctk.CTkFrame(marine_tab) # 이름 변경: result_frame_marine
        self.result_frame_marine.grid(row=1, column=0, padx=0, pady=(10, 0), sticky="nsew") # 상단 pady 추가
        self.result_frame_marine.grid_rowconfigure(0, weight=1)
        self.result_frame_marine.grid_columnconfigure(0, weight=1)
        # --- "해양생물" 탭 설정 끝 ---

        # --- "미생물 (LPSN)" 탭 설정 ---
        microbe_tab = self.tab_view.tab("미생물 (LPSN)")

        # --- "통합생물(COL)" 탭 설정 ---
        from species_verifier.gui.components.col_tab import ColTabFrame
        col_tab = self.tab_view.tab("담수 등 전체생물(COL)")  # "통합생물(COL)"에서 변경
        col_tab.grid_columnconfigure(0, weight=1)
        col_tab.grid_rowconfigure(0, weight=0)
        col_tab.grid_rowconfigure(1, weight=1)
        # 입력 프레임 ("담수 등 전체생물(COL)" 탭)  # 주석 변경
        self.input_frame_col = ctk.CTkFrame(col_tab)
        self.input_frame_col.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")
        self.input_frame_col.grid_columnconfigure(1, weight=1)
        # 결과 프레임 ("통합생물(COL)" 탭)
        self.result_frame_col = ctk.CTkFrame(col_tab)
        self.result_frame_col.grid(row=1, column=0, padx=0, pady=(10, 0), sticky="nsew")
        self.result_frame_col.grid_rowconfigure(0, weight=1)
        self.result_frame_col.grid_columnconfigure(0, weight=1)
        microbe_tab.grid_columnconfigure(0, weight=1)
        microbe_tab.grid_rowconfigure(0, weight=0) # Input frame microbe
        microbe_tab.grid_rowconfigure(1, weight=1) # Result frame microbe

        # 입력 프레임 ("미생물" 탭)
        self.input_frame_microbe = ctk.CTkFrame(microbe_tab)
        self.input_frame_microbe.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")
        self.input_frame_microbe.grid_columnconfigure(1, weight=1)

        # 결과 프레임 ("미생물" 탭)
        self.result_frame_microbe = ctk.CTkFrame(microbe_tab)
        self.result_frame_microbe.grid(row=1, column=0, padx=0, pady=(10, 0), sticky="nsew")
        self.result_frame_microbe.grid_rowconfigure(0, weight=1)
        self.result_frame_microbe.grid_columnconfigure(0, weight=1)
        # --- "미생물 (LPSN)" 탭 설정 끝 ---

        # --- 상태 표시 프레임 (탭 뷰 아래로 이동) ---
        self.status_frame = ctk.CTkFrame(self, height=40) # 높이 조정
        self.status_frame.grid(row=1, column=0, padx=20, pady=(10, 0), sticky="nsew") # pady 아래쪽 제거
        # 컬럼 설정: 0=상태레이블(고정폭), 1=진행바/저장버튼(확장)
        self.status_frame.grid_columnconfigure(0, weight=0) # 상태 레이블 고정
        self.status_frame.grid_columnconfigure(1, weight=1) # 진행/저장 버튼 확장

        # --- 푸터 프레임 (상태 표시 프레임 아래) ---
        self.footer_frame = ctk.CTkFrame(self, height=30, corner_radius=0)
        self.footer_frame.grid(row=2, column=0, padx=0, pady=(5, 5), sticky="nsew") # pady 추가
        self.footer_frame.grid_columnconfigure(0, weight=1) # 중앙 정렬을 위해

        # --- 상태 표시 프레임 위젯 ---
        # 상태 레이블
        self.status_label = ctk.CTkLabel(self.status_frame, text="입력 대기 중", anchor="w", font=self.default_font)
        self.status_label.grid(row=0, column=0, padx=(10, 10), pady=5, sticky="w") # padx 오른쪽 추가

        # 진행률 표시줄 (숨김 상태)
        self.progressbar = ctk.CTkProgressBar(self.status_frame)
        self.progressbar.set(0)
        # grid는 메서드에서 관리

        # 저장 버튼 (숨김 상태)
        self.save_button = ctk.CTkButton(
            self.status_frame,
            text="결과 저장",
            command=self.export_results_to_excel, # 기존 내보내기 함수 연결
            state="disabled"
        )
        # grid는 메서드에서 관리

        # --- 푸터 프레임 위젯 ---
        # 저작권 레이블 (푸터 프레임 중앙)
        self.copyright_label = ctk.CTkLabel(self.footer_frame,
                                            text="© 2025 국립수산과학원 수산생명자원과 책임기관",
                                            font=self.footer_font,
                                            text_color=("gray50", "gray60"))
        self.copyright_label.grid(row=0, column=0, pady=(0, 5)) # 푸터 중앙에 배치

        # --- 기존 상태 프레임 위젯 제거 ---
        # 주석 처리 또는 실제 코드에서 해당 라인들(약 488-500) 삭제 필요
        # self.progress_bar = ...
        # self.progress_label = ...
        # self.clear_results_button = ...
        # self.export_button = ...

        # --- 상태 표시 프레임 위젯 끝 ---

        self._reset_status_ui() # 초기 상태 설정

        self.focus_entry() # 초기 포커스는 해양생물 탭의 입력창

    # --- 탭 변경 이벤트 핸들러 추가 ---
    def _on_tab_change(self):
        """탭이 변경될 때 호출되는 함수"""
        # 참고: 이 함수는 탭 뷰 생성 후 command 매개변수로 연결될 예정
        selected_tab_name = self.tab_view.get() if hasattr(self, 'tab_view') else self.active_tab
        self.active_tab = selected_tab_name
        print(f"[Debug] Active tab changed to: {self.active_tab}")
        
        # 활성 탭에 따라 UI 상태 업데이트
        self._update_export_button_state()
        
        # 활성 탭에 따라 포커스 설정 (미생물 탭 입력 필드는 나중에 구현 예정)
        if self.active_tab == "해양생물":
            self.focus_entry()
        elif self.active_tab == "미생물 (LPSN)" and hasattr(self, 'microbe_entry'):
            # microbe_entry가 있으면 포커스 설정 (아직 구현 안 됨)
            pass
        
        # 활성 탭에 따라 스크롤바 업데이트 (아직 구현 안 됨)
        self._update_scrollbars() if hasattr(self, '_update_scrollbars') else None


    def _reset_status_ui(self, reset_file_label=False, show_save_button=False): # 파라미터 추가
        """상태 표시줄 UI를 초기 상태 또는 완료 상태로 재설정합니다."""
        # --- 기존 코드 대신 새 로직 적용 ---
        self.status_label.grid_remove() # 일단 숨김
        self.progressbar.grid_remove() # 진행률 표시줄 숨김
        self.save_button.grid_remove() # 저장 버튼 숨김

        if show_save_button:
            # 완료 상태: 저장 버튼 표시 및 상태 레이블 변경
            self.status_label.configure(text="검증 완료")
            self.status_label.grid(row=0, column=0, padx=(10, 10), pady=5, sticky="w") # 상태 레이블 표시
            self.save_button.grid(row=0, column=1, padx=(10, 10), pady=5, sticky="ew") # 저장 버튼 표시 (가운데 확장)
            self.save_button.configure(state="normal") # 저장 버튼 활성화
        else:
            # 초기 또는 결과 없는 완료 상태: '입력 대기 중' 레이블 표시
            self.status_label.configure(text="입력 대기 중")
            self.status_label.grid(row=0, column=0, padx=(10, 10), pady=5, sticky="w") # 상태 레이블 표시
            self.save_button.configure(state="disabled") # 저장 버튼 비활성화 확실히

        # 파일 레이블 초기화 (옵션)
        if reset_file_label:
            if hasattr(self, 'file_label'):
                self.selected_file_path = None
                self.file_label.configure(text="선택된 파일 없음")
                if hasattr(self, 'file_search_button'): self.file_search_button.configure(state="disabled")
            # microbe_file_label도 초기화
            if hasattr(self, 'microbe_file_label'):
                self.selected_microbe_file_path = None
                self.microbe_file_label.configure(text="선택된 파일 없음")
                if hasattr(self, 'microbe_file_search_button'): self.microbe_file_search_button.configure(state="disabled")

        # 스크롤바 숨기는 로직은 유지하거나 필요시 추가
        if hasattr(self, 'tree_scrollbar_marine_y'): self.tree_scrollbar_marine_y.grid_forget()
        if hasattr(self, 'tree_scrollbar_marine_x'): self.tree_scrollbar_marine_x.grid_forget()
        if hasattr(self, 'tree_scrollbar_microbe_y'): self.tree_scrollbar_microbe_y.grid_forget()
        if hasattr(self, 'tree_scrollbar_microbe_x'): self.tree_scrollbar_microbe_x.grid_forget()

        # 내보내기/지우기 버튼 상태 업데이트 로직 제거 (_set_ui_state에서 처리)
        # if hasattr(self, 'export_button'): self.export_button.configure(state="disabled")
        # if hasattr(self, 'clear_results_button'): self.clear_results_button.configure(state="disabled")

    def _show_progress_ui(self, initial_text=""):
        """진행률 표시줄과 상태 레이블을 표시합니다."""
        # --- 기존 코드 대신 새 로직 적용 ---
        self.status_label.grid() # 상태 레이블 표시
        self.status_label.configure(text=initial_text if initial_text else "처리 중...") # 기본 텍스트 변경
        self.progressbar.grid(row=0, column=1, padx=(10, 10), pady=5, sticky="ew") # 진행률 표시줄 표시 (가운데 확장)
        self.progressbar.set(0)
        # self.progressbar.start() # 필요시 호출 측에서 start() 호출
        self.save_button.grid_remove() # 진행 중에는 저장 버튼 숨김
        self.save_button.configure(state="disabled") # 비활성화 확실히

    def _update_scrollbars(self, event=None):
        """트리뷰 크기에 따라 스크롤바를 업데이트하고 필요에 따라 표시/숨김 처리합니다."""
        # 현재 활성 탭의 스크롤바 업데이트
        if self.active_tab == "해양생물":
            tree = self.result_tree_marine
            scrollbar_y = self.tree_scrollbar_marine_y
            scrollbar_x = self.tree_scrollbar_marine_x
            results = self.current_results_marine
            result_frame = self.result_frame_marine
        elif self.active_tab == "미생물 (LPSN)":
            tree = self.result_tree_microbe
            scrollbar_y = self.tree_scrollbar_microbe_y
            scrollbar_x = self.tree_scrollbar_microbe_x
            results = self.current_results_microbe
            result_frame = self.result_frame_microbe
        else:
            return # 알 수 없는 탭

        # 트리뷰 선택 리셋 (선택 사항)
        if tree.selection():
            tree.selection_remove(tree.selection())
        
        # 트리뷰의 맨 위로 스크롤 (새 결과가 있는 경우)
        if tree.get_children():
            tree.see(tree.get_children()[0])

        # 수직 스크롤바
        if results:
            scrollbar_y.grid(row=0, column=1, padx=(0, 15), pady=(15, 0), sticky="ns")
        else:
            scrollbar_y.grid_forget()

        # 수평 스크롤바
        total_col_width = sum(tree.column(col, "width") for col in tree["columns"])
        tree_width = tree.winfo_width()
        
        # print(f"Debug Scroll ({self.active_tab}): Total Col Width: {total_col_width}, Tree Width: {tree_width}") # 디버깅용

        if tree_width > 0 and total_col_width > tree_width:
            scrollbar_x.grid(row=1, column=0, padx=(15, 0), pady=(0, 15), sticky="ew")
        else:
            scrollbar_x.grid_forget()
        
        # 트리뷰 갱신 (UI 리프레시)
        tree.update()

    def update_progress(self, progress_value):
        """Updates the progress bar and label. Designed to be called safely via self.after."""
        self.progressbar.set(progress_value)
        if progress_value >= 1.0:
            self.status_label.configure(text="완료") # 100% 도달 시 '완료'로 표시
        else:
            # 활성 탭에 따라 메시지 조정 가능
            verb = "검증 중" if self.active_tab == "해양생물" else "검색 중"
            self.status_label.configure(text=f"{verb}... {progress_value*100:.0f}%") # 진행률 표시

    def _update_progress_label(self, text):
        """진행 레이블 텍스트를 업데이트합니다."""
        self.status_label.configure(text=text)

    def browse_file(self):
        """파일 탐색기를 열어 CSV 또는 Excel 파일을 선택합니다. (해양생물 탭 전용)"""
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

    # --- start_single_search_thread 함수 수정 (해양생물 탭) ---
    def start_single_search_thread(self):
        """입력창("해양생물" 탭)에서 단일 검색을 시작합니다."""
        input_text = self.single_entry.get().strip()
        if not input_text:
            # --- 상태 레이블 대신 메시지 박스 사용 ---
            self.show_centered_message("warning", "입력 오류", "검색어를 입력하세요.")
            # self.search_status.config(text="검색어를 입력하세요.") # 제거
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
                # --- 수정: 단일 국명 처리를 위한 별도 함수 제거하고 _perform_verification 사용 고려 ---
                # 여기서는 일단 _process_multiple_korean_names를 단일 이름으로 호출하여 일관성 유지
                thread = threading.Thread(target=self._process_multiple_korean_names, args=([cleaned_input],))
                # thread = threading.Thread(target=self._search_korean_name, args=(cleaned_input,)) # 이전 방식
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

    # --- 신규: 미생물 탭 검색 시작 함수 ---
    def start_microbe_search_thread(self):
        """입력창("미생물" 탭)에서 검색을 시작합니다."""
        input_text = self.microbe_entry.get().strip()
        if not input_text:
            self.show_centered_message("warning", "입력 오류", "미생물 학명을 입력하세요.")
            return

        if verify_microbe_name is None:
             self.show_centered_message("error", "기능 오류", "미생물 검증 기능이 로드되지 않았습니다.")
             return

        # UI 비활성화
        self._set_ui_state("disabled")
        self._show_progress_ui("미생물 학명 검색 중...")
        self.progressbar.start() # 시작 시 불확정 모드

        # 입력값 처리 로직 개선
        microbe_names_list = []
        
        # 첫 글자가 한글인지 확인
        if input_text and self._is_korean(input_text[0]):
            self.show_centered_message("warning", "기능 제한", "미생물 탭에서는 한글 국명 검색이 지원되지 않습니다. 학명으로 검색해주세요.")
            self._reset_status_ui()
            self._set_ui_state("normal")
            return
            
        # 쉼표로 구분된 학명 목록 처리    
        if "," in input_text:
            print(f"[Info] 미생물 복수 학명 검색: {input_text}")
            # 쉼표로 구분된 학명 목록을 처리
            microbe_names_list = [self._clean_scientific_name(name.strip()) for name in input_text.split(',') if name.strip()]
        else:
            # 단일 학명 처리
            print(f"[Info] 미생물 단일 학명 검색: {input_text}")
            microbe_names_list = [self._clean_scientific_name(input_text)]
        
        if not microbe_names_list:
            self.show_centered_message("warning", "입력 오류", "유효한 미생물 학명이 없습니다.")
            self._reset_status_ui()
            self._set_ui_state("normal")
            return
            
        # 검색할 학명 목록 로그 출력
        print(f"[Info] 검색할 미생물 학명 목록 ({len(microbe_names_list)}개): {microbe_names_list}")

        thread = threading.Thread(target=self._perform_microbe_verification, args=(microbe_names_list,), daemon=True)
        self.verification_thread = thread
        thread.start()

    def _process_multiple_korean_names(self, korean_names_input): # 이름 변경
        """여러 한글 국명(또는 단일 국명 리스트)을 처리하고 각각에 대한 학명을 찾아 검증합니다."""
        # --- 수정: 입력이 문자열이면 분리, 리스트면 그대로 사용 ---
        if isinstance(korean_names_input, str):
            korean_names = re.split(r'[,\s\t]+', korean_names_input)
            korean_names = [self._clean_scientific_name(name.strip()) for name in korean_names if name.strip()]
            print(f"[Debug] 입력 문자열에서 분리된 국명: {korean_names}")
        elif isinstance(korean_names_input, list):
            korean_names = [self._clean_scientific_name(name) for name in korean_names_input if name] # 리스트 내 각 이름 정리
            print(f"[Debug] 입력 리스트에서 처리할 국명: {korean_names}")
        else:
            print("[Error] Invalid input type for Korean names processing.")
            self.after(0, lambda: self.show_centered_message("error", "내부 오류", "국명 처리 입력 형식이 잘못되었습니다."))
            self.after(0, self._reset_status_ui)
            self.after(0, self._set_ui_state, "normal")
            return
        
        if not korean_names:
            print("[Warning] 처리할 국명이 없습니다.")
            self.after(0, lambda: self.show_centered_message("warning", "입력 오류", "처리할 국명이 없습니다."))
            self.after(0, self._reset_status_ui)
            self.after(0, self._set_ui_state, "normal")
            # 입력창 비우기 및 포커스 (처리할 이름 없을 시)
            self.after(10, self.single_entry.delete, 0, tk.END)
            self.after(20, self.focus_entry)
            return
        
        self.after(0, self._show_progress_ui, f"{len(korean_names)}개의 국명 처리 중...")
        self.after(0, self.progressbar.start)
        self.after(0, self._set_ui_state, "disabled")
        
        verification_list_with_status = [] # (국명, 학명 or None) 튜플 저장
        
        print(f"[Info] {len(korean_names)}개 국명 처리 시작: {', '.join(korean_names)}")
        
        for i, korean_name in enumerate(korean_names):
            self.after(0, lambda: self._update_progress_label(f"'{korean_name}' 학명 찾는 중... ({i+1}/{len(korean_names)})"))
            print(f"[Info] '{korean_name}' (#{i+1}/{len(korean_names)})에 대한 학명 검색 시작")
            
            scientific_name = self._find_scientific_name_from_korean_name(korean_name)
            
            if scientific_name:
                print(f"[Success] '{korean_name}'에 대한 학명 '{scientific_name}' 찾기 성공")
                verification_list_with_status.append((korean_name, scientific_name)) # (국명, 학명) 추가
            else:
                print(f"[Info] '{korean_name}'에 대한 학명을 찾지 못했습니다. (WoRMS 검증 생략 예정)") # 메시지 변경
                verification_list_with_status.append((korean_name, None)) # (국명, None) 추가
        
        if verification_list_with_status:
            print(f"[Info] Starting verification for {len(verification_list_with_status)} names (including those without scientific names).")
            # --- 수정: _perform_verification은 이제 해양생물 전용 ---
            thread = threading.Thread(target=self._perform_verification, args=(verification_list_with_status,))
            thread.daemon = True
            thread.start()
        else: # 처리할 국명이 아예 없는 경우 (매우 드문 케이스)
            print("[Warning] No valid Korean names found to process.")
            self.after(0, self.progressbar.stop) # 진행 멈춤
            self.after(0, self._reset_status_ui) # 상태 초기화
            self.after(0, lambda: self.show_centered_message("warning", "처리 불가", "처리할 국명이 없습니다."))
            self.after(0, self._set_ui_state, "normal") # UI 활성화
            # 입력창 비우기 및 포커스 (처리할 이름 없을 시)
            self.after(10, self.single_entry.delete, 0, tk.END)
            self.after(20, self.focus_entry)


    def _find_scientific_name_from_korean_name(self, korean_name):
        """한글 이름에서 학명을 찾는 모든 방법을 순차적으로 시도합니다."""
        # 1. 매핑 테이블에서 학명 찾기 (이제 flat dictionary)
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

    # --- _search_korean_name 함수 제거됨 ---
    # def _search_korean_name(self, korean_name): ... (제거) ...

    # --- _perform_verification 함수 수정 (해양생물 전용) ---
    def _perform_verification(self, verification_list_input):
        """주어진 목록(학명 문자열 리스트 또는 (국명, 학명 or None) 튜플 리스트)을 처리합니다. (해양생물 탭 전용)"""
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
        num_skipped_worms = 0 # WoRMS 검증 건너뛴 횟수 (국명 검색 시)

        # --- 기존 결과 초기화 코드 제거 ---
        # self.after(0, self._clear_results_tree, "해양생물")

        try:
            if verify_species_list is None:
                raise ImportError("Core verifier module not loaded.")

            # UI 업데이트: 진행 중 표시 (총 개수 기준)
            total_items = len(verification_list_input)
            self.after(0, self._show_progress_ui) # 진행률 UI 표시 (텍스트는 아래에서 설정)
            self.after(0, lambda: self._update_progress_label(f"총 {total_items}개 항목 처리 중..."))
            self.after(0, lambda: self.progressbar.set(0)) # 진행률 초기화
            self.after(0, lambda: self.progressbar.configure(mode='determinate')) # 확정 모드

            # --- 처리 로직 분기 ---
            if is_korean_search:
                # --- 국명 입력 처리 --- 
                for i, item in enumerate(verification_list_input):
                    korean_name, scientific_name = item # 튜플 언패킹
                    
                    # 진행률 표시 (개별 항목 시작 시 업데이트)
                    self.after(0, lambda: self._update_progress_label(f"'{korean_name}' 처리 중... ({i+1}/{total_items})"))
                    self.after(0, lambda: self.update_progress((i) / total_items)) # 약간의 진행 표시
                    
                    result_entry = {} # 각 국명에 대한 결과 딕셔너리
                    
                    if scientific_name: # 학명이 있는 경우
                        print(f"[Info] Performing WoRMS verification for '{korean_name}' with scientific name '{scientific_name}'")
                        species_to_verify = [(korean_name, scientific_name, korean_name)]
                        
                        try:
                            # --- GUI 콜백 전달 방식 변경 (직접 호출 대신 after 사용) ---
                            verified_results = verify_species_list(species_to_verify) # 콜백 제거
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
                        self.after(0, lambda: self._update_progress_label(f"'{korean_name}' 위키백과 검색 중... ({i+1}/{total_items})"))
                        wiki_summary = self._get_wiki_summary(korean_name) # 헬퍼 함수 사용
                    
                    result_entry['wiki_summary'] = wiki_summary if wiki_summary else '정보 없음' # 최종 설정
                    
                    # 항목 하나에 대한 결과를 즉시 표시 (해양생물 탭)
                    self.after(0, lambda: self._update_results_display([result_entry], "해양생물", False))
                    
                    # 진행률 업데이트
                    self.after(0, lambda: self.update_progress((i + 1) / total_items))
            
            else: # --- 학명 입력 처리 --- 
                for i, scientific_name in enumerate(verification_list_input):
                    # 현재 처리 중인 학명 표시
                    self.after(0, lambda: self._update_progress_label(f"'{scientific_name}' 처리 중... ({i+1}/{total_items})"))
                    self.after(0, lambda: self.update_progress(i / total_items))
                    
                    print(f"[Info] Performing WoRMS verification for scientific name: '{scientific_name}'")
                    
                    result_entry = None # 결과 초기화
                    # 단일 학명에 대한 WoRMS 검증 수행
                    try:
                        # --- GUI 콜백 전달 방식 변경 ---
                        result_list = verify_species_list([scientific_name]) # 콜백 제거
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
                            current_worms_status = result_entry.get('worms_status', '').lower()
                            error_statuses = ['-', 'n/a', 'error', 'no match', 'ambiguous', '형식 오류', 
                                              'worms 결과 없음', 'worms 처리 오류', '오류:', 'worms 오류:']
                            should_search_wiki = result_entry.get('is_verified') or \
                                                 not any(status in current_worms_status for status in error_statuses)
                            
                            if should_search_wiki:
                                self.after(0, lambda: self._update_progress_label(f"'{scientific_name}' 위키백과 검색 중... ({i+1}/{total_items})"))
                                name_for_wiki = result_entry.get('scientific_name', scientific_name) # Use valid name if available
                                if name_for_wiki == '-': name_for_wiki = scientific_name
                                wiki_summary = self._get_wiki_summary(name_for_wiki)
                            
                            result_entry['wiki_summary'] = wiki_summary if wiki_summary else '정보 없음' # 최종 설정
                            
                            # --- 추가: 로그 출력 ---
                            print(f"[Debug _perform_verification] Result before UI update for '{scientific_name}': {result_entry}")
                            # --- 로그 출력 끝 ---
                            
                            self.after(0, lambda: self._update_results_display([result_entry], "해양생물", False))
                        else:
                            # WoRMS 결과가 없는 경우 기본 결과 생성 (위키 검색 안함)
                            result_entry = self._create_basic_result(scientific_name, scientific_name, False, "WoRMS 결과 없음")
                            result_entry['wiki_summary'] = '정보 없음' # 명시적으로 설정
                            
                            # --- 추가: 로그 출력 ---
                            print(f"[Debug _perform_verification] Result before UI update (No WoRMS result) for '{scientific_name}': {result_entry}")
                            # --- 로그 출력 끝 ---
                            
                            self.after(0, lambda: self._update_results_display([result_entry], "해양생물", False))
                    except Exception as e:
                        print(f"[Error] Error processing '{scientific_name}': {e}")
                        result_entry = self._create_basic_result(scientific_name, scientific_name, False, "오류: " + str(e))
                        result_entry['wiki_summary'] = '정보 없음' # 명시적으로 설정
                        
                        # --- 추가: 로그 출력 ---
                        print(f"[Debug _perform_verification] Result before UI update (Error) for '{scientific_name}': {result_entry}")
                        # --- 로그 출력 끝 ---
                        
                        self.after(0, lambda: self._update_results_display([result_entry], "해양생물", False))
                    
                    # 진행률 업데이트
                    self.after(0, lambda: self.update_progress((i + 1) / total_items))

        except Exception as e:
            error_occurred = True
            error_message_details = f"처리 중 오류 발생:\n{e}"
            import traceback
            traceback.print_exc() # 콘솔에 상세 오류 출력

        finally:
            # UI 상태 복원 및 진행 표시 완료
            self.after(0, lambda: self._set_ui_state("normal"))
            self.after(50, lambda: self.progressbar.stop())
            self.after(50, lambda: self.progressbar.configure(mode='determinate')) # Stop 이후 확정 모드로 복원
            self.after(50, lambda: self.progressbar.set(1.0))
            
            status_label_text = "오류 발생" if error_occurred else "완료"
            print(f"[Debug] 진행 상태 업데이트: '{status_label_text}'") # 디버깅 로그 추가
            self.after(50, lambda: self._update_progress_label(status_label_text))
            
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
            self.after(100, lambda: self._update_progress_label(status_label_text))
                
            self.after(150, lambda: self.show_centered_message(msg_type, final_summary_title, final_summary_message)) 

            # --- 입력창 비우기 및 포커스 --- 
            self.after(200, lambda: self.single_entry.delete(0, tk.END))
            self.after(250, self.focus_entry) # 포커스 복원

    # --- 헬퍼 함수: 위키피디아 요약 가져오기 (수정: 전체 내용 반환) ---
    def _get_wiki_summary(self, search_term):
        """주어진 검색어로 위키백과 페이지의 전체 내용을 가져옵니다."""
        if not search_term or search_term == '-':
            return "정보 없음"
            
        try:
            print(f"[Info Wiki] '{search_term}' 위키백과 페이지 검색 시도")
            wikipedia.set_lang("ko") # 한국어 먼저 시도
            is_english_page = False
            
            try:
                page = wikipedia.page(search_term, auto_suggest=False)
                print(f"[Info Wiki] '{search_term}' 한국어 페이지 찾음")
            except wikipedia.exceptions.PageError:
                print(f"[Info Wiki] '{search_term}' 한국어 페이지 없음, 영어로 시도")
                wikipedia.set_lang("en")
                page = wikipedia.page(search_term, auto_suggest=False) # 영어로 재시도
                print(f"[Info Wiki] '{search_term}' 영어 페이지 찾음")
                is_english_page = True
            except wikipedia.exceptions.DisambiguationError as e:
                # 다의어 페이지의 첫 번째 옵션으로 재시도
                first_option = e.options[0]
                print(f"[Warning Wiki] '{search_term}' 다의어 페이지 발견, 첫 옵션 '{first_option}'으로 재시도")
                return self._get_wiki_summary(first_option) # 재귀 호출

            # 페이지 전체 내용 가져오기
            content = page.content
            if content and content.strip():
                print(f"[Info Wiki] '{search_term}' 전체 내용 ({len(content)} chars) 반환")
                
                # 내용 정제: 위키 마크업 정리 및 불필요한 섹션 제거
                # 섹션 분리
                sections = content.split('\n== ')
                
                # 영어 페이지일 경우 더 많은 섹션을 포함
                if is_english_page:
                    main_content = sections[0]  # 첫 번째 섹션(주요 내용)
                    
                    # 첫 섹션의 내용이 적을 경우(50자 미만), 추가 섹션 포함
                    if len(main_content.strip()) < 100:
                        # 최대 3개 섹션까지 포함
                        section_count = min(len(sections), 3)
                        included_sections = []
                        
                        # 첫 번째 섹션 추가
                        included_sections.append(main_content)
                        
                        # 추가 섹션 포함 (불필요한 섹션 제외)
                        for i in range(1, section_count):
                            section_title = sections[i].split('\n')[0].lower() if sections[i] else ""
                            section_content = '\n'.join(sections[i].split('\n')[1:]) if sections[i] else ""
                            
                            # 참고 문헌, 외부 링크 등 불필요한 섹션 제외
                            skip_sections = ['references', 'external links', 'see also', 'further reading']
                            if not any(skip_title in section_title.lower() for skip_title in skip_sections):
                                if section_content.strip():
                                    included_sections.append(f"== {sections[i]}")
                        
                        # 포함된 섹션 결합
                        main_content = '\n'.join(included_sections)
                        print(f"[Info Wiki] 영어 페이지: {len(included_sections)}개 섹션 포함됨")
                else:
                    # 한국어 페이지는 기존 방식대로 첫 섹션만 포함
                    main_content = sections[0]
                
                # 불필요한 마크업 제거
                main_content = re.sub(r'\[\d+\]', '', main_content)  # 각주 번호 [1], [2] 등 제거
                main_content = re.sub(r'\{\{.*?\}\}', '', main_content)  # {{...}} 템플릿 제거
                
                # 정제된 내용 반환 (영어 페이지는 더 많은 내용 포함)
                cleaned_content = main_content.strip()
                max_length = 500 if is_english_page else 300  # 영어 페이지는 더 긴 내용 허용
                
                if len(cleaned_content) > max_length:
                    cleaned_content = cleaned_content[:max_length] + "... (더 많은 내용 있음)"
                
                return cleaned_content
            else:
                return "정보 없음"

        except wikipedia.exceptions.PageError: # 최종적으로 페이지 못 찾은 경우
            print(f"[Info Wiki] '{search_term}' 위키백과 페이지를 찾을 수 없습니다")
            return "정보 없음"
        except wikipedia.exceptions.DisambiguationError: # 재귀 호출에서 또 다의어 만난 경우 (드뭄)
            print(f"[Info Wiki] '{search_term}' 위키백과 다의어 처리 실패")
            return "정보 없음 (다의어 처리 실패)"
        except requests.exceptions.RequestException as req_e:
            print(f"[Error Wiki] '{search_term}' 위키 네트워크 오류: {req_e}")
            return "정보 없음 (네트워크 오류)"
        except Exception as wiki_e:
            print(f"[Error Wiki] '{search_term}' 위키 검색 중 오류 발생: {wiki_e}")
            return "정보 없음"
            
    # --- 헬퍼 함수: Treeview 업데이트 (기존 update_results 대체) ---
    def _update_results_display(self, results_list, tab_name=None, clear_first=False):
        """검증 결과를 Treeview에 표시합니다. 새 결과는 맨 위에 추가됩니다."""
        # 결과가 비어있으면 처리하지 않음
        if not results_list:
            return
        
        # 표시할 대상 탭 결정 (지정되지 않은 경우 현재 활성 탭 사용)
        if not tab_name:
            if self.active_tab == "해양생물":
                tab_name = "marine"
            elif self.active_tab == "미생물 (LPSN)":
                tab_name = "microbe"
                
        # 결과 목록 참조 변수 결정
        current_results_ref = None
        target_tree = None
        
        if tab_name == "marine" or tab_name == "해양생물":
            current_results_ref = self.current_results_marine
            target_tree = self.result_tree_marine
        elif tab_name == "microbe" or tab_name == "미생물 (LPSN)":
            current_results_ref = self.current_results_microbe
            target_tree = self.result_tree_microbe
        else:
            return  # 적절한 탭이 아닌 경우 처리하지 않음
            
        # 기존 결과 초기화 (clear_first가 True인 경우)
        if clear_first:
            # 트리뷰 내용 삭제
            for item in target_tree.get_children():
                target_tree.delete(item)
            # 결과 목록 참조 초기화
            current_results_ref.clear()
            
        # 새로운 결과를 맨 위에 추가 (결과 목록에는 맨 앞에 추가)
        for result in reversed(results_list):
            # 결과 목록 참조의 맨 앞에 추가
            current_results_ref.insert(0, result)
            
            # 결과 유형에 따라 다른 처리
            if tab_name == "marine":
                # 맨 위에 추가 (0 인덱스 사용)
                self._display_marine_result(target_tree, result, insert_at_index=0)
            else:
                # 맨 위에 추가 (0 인덱스 사용)
                self._display_microbe_result(target_tree, result, insert_at_index=0)
        
        # 결과가 추가되었으므로 스크롤바 업데이트
        self._update_scrollbars()
        
        # 결과가 있으면 내보내기 버튼과 지우기 버튼 활성화
        self._update_export_button_state()

    def _display_marine_result(self, tree, result, insert_at_index=tk.END):
        """해양생물 결과를 트리뷰에 표시합니다."""
        input_name = result.get('input_name', '-')
        mapped_name = result.get('mapped_name', '-')
        is_verified = result.get('is_verified', False)
        worms_status = result.get('worms_status', '-')
        worms_id = result.get('worms_id', '-')
        worms_url = result.get('worms_url', '-')
        wiki_summary = result.get('wiki_summary', '-')
        
        # 요약이 너무 길면 자르기
        if isinstance(wiki_summary, str) and len(wiki_summary) > 60:
            display_summary = wiki_summary[:57] + '...'
        else:
            display_summary = wiki_summary or '-'
        
        # 태그 결정 (상태에 따라)
        tag = 'verified' if is_verified else 'unverified'
        if 'accepted' in str(worms_status).lower():
            tag = 'verified'
        elif any(status in str(worms_status).lower() for status in ['alternate', 'synonym']):
            tag = 'caution'
            
        # 아이템 추가 (맨 위 또는 지정된 위치에)
        item_id = tree.insert("", insert_at_index, text=input_name, values=(
            mapped_name,
            "✓" if is_verified else "✗",
            worms_status,
            worms_id,
            worms_url,
            display_summary
        ), tags=(tag,))
        
        # 더블 클릭 이벤트의 인식을 위해 item_id와 result 매핑
        # tree.item(item_id, values=(결과...)) 방식으로 아이템 저장됨
    
    def _display_microbe_result(self, tree, result, insert_at_index=tk.END):
        """미생물 결과를 트리뷰에 표시합니다."""
        try:
            # 리스트인 경우 첫 번째 항목을 사용
            if isinstance(result, list) and len(result) > 0:
                print(f"[Warning] 미생물 결과가 리스트 형태입니다. 첫 번째 항목만 사용합니다.")
                result = result[0]
                
            # 딕셔너리 타입 확인
            if not isinstance(result, dict):
                print(f"[Error] 미생물 결과가 딕셔너리 형태가 아닙니다. 타입: {type(result)}")
                return
                
            input_name = result.get('input_name', '-')
            valid_name = result.get('valid_name', '-')
            status = result.get('status', '-')
            taxonomy = result.get('taxonomy', '-')
            link = result.get('lpsn_link', '-')  # lpsn_link 필드 사용
            if link == '-':  # lpsn_link가 없으면 link 필드 시도
                link = result.get('link', '-')
            wiki_summary = result.get('wiki_summary', '-')  # 위키 요약 필드 추가
            
            # result의 모든 키 출력 (디버깅)
            print(f"[Debug] 미생물 결과 키: {list(result.keys())}")
            
            # 분류 정보 길이 제한
            if isinstance(taxonomy, str) and len(taxonomy) > 60:
                display_taxonomy = taxonomy[:57] + '...'
            else:
                display_taxonomy = taxonomy or '-'
                
            # 위키 요약 정보 길이 제한
            if isinstance(wiki_summary, str) and len(wiki_summary) > 60:
                display_wiki = wiki_summary[:57] + '...'
            else:
                display_wiki = wiki_summary or '-'
            
            # 태그 결정 (상태에 따라)
            tag = 'invalid'  # 기본값은 검증 안됨
            if status and 'valid' in status.lower():
                tag = 'valid'
            elif status and any(s in status.lower() for s in ['synonym', 'ambiguous']):
                tag = 'ambiguous'
                
            # 아이템 추가 (맨 위 또는 지정된 위치에)
            item_id = tree.insert("", insert_at_index, text=input_name, values=(
                valid_name,
                status,
                display_taxonomy,
                link,
                display_wiki  # 위키 정보 컬럼 추가
            ), tags=(tag,))
        except Exception as e:
            print(f"[Error] 미생물 결과 표시 중 오류 발생: {e}")

    # --- 헬퍼 함수: 위키 요약 팝업 (수정: 출처 표시 및 복사 버튼 추가) ---
    def _show_wiki_summary_popup(self, title, wiki_summary):
        """위키백과 요약 내용을 팝업 창으로 표시하고 복사 기능을 제공합니다."""
        popup = ctk.CTkToplevel(self)
        popup.title(f"종정보: {title}") # 제목 변경
        popup.geometry("800x600")  # 팝업 창 크기 키우기
        popup.grab_set()  # 모달 창으로 설정
        
        # 레이아웃 설정
        popup.grid_columnconfigure(0, weight=1)
        popup.grid_rowconfigure(0, weight=0)  # 제목
        popup.grid_rowconfigure(1, weight=1)  # 내용
        popup.grid_rowconfigure(2, weight=0)  # 하단 프레임 (버튼, 출처)
        
        # 제목 레이블 - 볼드체로 변경
        title_label = ctk.CTkLabel(popup, text=f"{title}", 
                                   font=ctk.CTkFont(family="Malgun Gothic", size=16, weight="bold"))
        title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # 내용 프레임 (스크롤 가능)
        content_frame = ctk.CTkFrame(popup)
        content_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)
        
        # 텍스트 위젯 (스크롤 가능) - 폰트 크기 키우기
        text_widget = ctk.CTkTextbox(content_frame, 
                                     wrap="word", 
                                     font=ctk.CTkFont(family="Malgun Gothic", size=14, weight="normal"),
                                     corner_radius=6,
                                     padx=15, pady=15)
        text_widget.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        
        # 텍스트 삽입 전에 컨텐츠 처리 - 줄바꿈과 탭 문자를 제대로 표시
        formatted_text = wiki_summary.replace('\n\n', '\n \n')  # 빈 줄 유지
        text_widget.insert("1.0", formatted_text)
        text_widget.configure(state="disabled")  # 읽기 전용으로 설정
        
        # 하단 프레임 (버튼, 출처용)
        bottom_frame = ctk.CTkFrame(popup)
        bottom_frame.grid(row=2, column=0, padx=20, pady=(10, 20), sticky="ew")
        bottom_frame.grid_columnconfigure(0, weight=1) # 출처 레이블 공간
        bottom_frame.grid_columnconfigure(1, weight=0) # 위키 링크 버튼 공간
        bottom_frame.grid_columnconfigure(2, weight=0) # 복사 버튼 공간
        bottom_frame.grid_columnconfigure(3, weight=0) # 닫기 버튼 공간

        # 출처 레이블
        source_label = ctk.CTkLabel(bottom_frame, text="자료 출처: 위키백과", 
                                     font=CTkFont(family="Malgun Gothic", size=10, slant="italic"), 
                                     text_color=("gray60", "gray50"))
        source_label.grid(row=0, column=0, padx=(0, 10), sticky="w")
        
        # 위키피디아 링크 버튼
        wiki_url = f"https://ko.wikipedia.org/wiki/{title}"
        if wiki_summary.startswith('[영문]'):
            wiki_url = f"https://en.wikipedia.org/wiki/{title}"
        
        wiki_link_button = ctk.CTkButton(bottom_frame, text="위키백과 원문", width=120, 
                                         font=CTkFont(family="Malgun Gothic", size=12),
                                         command=lambda: webbrowser.open(wiki_url))
        wiki_link_button.grid(row=0, column=1, padx=(0, 10))
        
        # 내용 복사 버튼
        copy_button = ctk.CTkButton(bottom_frame, text="내용 복사", width=100, 
                                    font=CTkFont(family="Malgun Gothic", size=12), 
                                    command=lambda: self._copy_to_clipboard(wiki_summary)) 
        copy_button.grid(row=0, column=2, padx=(0, 10))

        # 닫기 버튼
        close_button = ctk.CTkButton(bottom_frame, text="닫기", command=popup.destroy, width=100, 
                                     font=CTkFont(family="Malgun Gothic", size=12, weight="normal"))
        close_button.grid(row=0, column=3, padx=(0, 0)) # 오른쪽 끝에 배치

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
    def _on_tree_motion(self, event, tree):
        """마우스가 Treeview 위에서 움직일 때 호출되는 함수"""
        # 현재 위치에서 컬럼 아이디 확인
        x, y = event.x, event.y
        region = tree.identify_region(x, y)
        column_id = tree.identify_column(x)
        
        tooltip_text = None
        
        # 헤더 영역이고 특정 컬럼인 경우 툴팁 표시
        if region == "heading":
            # 해양생물 탭 트리뷰인 경우
            if tree == self.result_tree_marine:
                if column_id == "#4": # WoRMS ID 컬럼 헤더 ("WoRMS ID(?)")
                    tooltip_text = "더블 클릭 시 WoRMS ID 복사됨"
                elif column_id == "#5": # WoRMS Link 컬럼 헤더 ("WoRMS 링크(?)")
                    tooltip_text = "더블 클릭 시 WoRMS 웹사이트 확인"
                elif column_id == "#6": # Wiki Summary 컬럼 헤더 ("종정보(?)")
                    tooltip_text = "더블 클릭 시 위키백과 요약 팝업창 확인"
            # 미생물 탭 트리뷰인 경우 
            elif tree == self.result_tree_microbe:
                if column_id == "#3": # Taxonomy 컬럼 헤더 ("분류 정보(?)")
                    tooltip_text = "분류학적 위치 정보"
                elif column_id == "#4": # LPSN Link 컬럼 헤더 ("LPSN 링크(?)")
                    tooltip_text = "더블 클릭 시 LPSN 웹사이트 확인"
                elif column_id == "#5": # Wiki Summary 컬럼 헤더 ("종정보(?)")
                    tooltip_text = "더블 클릭 시 위키백과 요약 팝업창 확인"
        
        # 셀 영역이고 특정 조건인 경우 값을 툴팁으로 표시
        elif region == "cell":
            item_id = tree.identify("item", x, y)
            if item_id:
                values = tree.item(item_id, "values")
                column_idx = int(column_id.replace("#", "")) - 1
                
                # 유효한 컬럼 인덱스 확인
                if 0 <= column_idx < len(values):
                    value = values[column_idx]
                    
                    # 긴 텍스트는 전체를 툴팁으로 표시
                    if len(str(value)) > 40 and value != "-":
                        tooltip_text = str(value)
        
        # 툴팁 표시 여부 결정
        if tooltip_text:
            self._show_tooltip(tooltip_text, event.x_root, event.y_root)
        else:
            self._hide_tooltip()

    # --- 이벤트 핸들러: Treeview 마우스 벗어남 (툴팁용, 신규) ---
    def _on_tree_leave(self, event):
        """마우스가 Treeview 영역을 벗어날 때 툴팁을 숨깁니다."""
        self._hide_tooltip()

    # 아래에 _perform_microbe_verification 함수 추가
    def _perform_microbe_verification(self, microbe_names_list):
        """미생물 학명 목록을 검증하는 함수 (LPSN 사이트 이용)"""
        try:
            # 초기 설정
            total_items = len(microbe_names_list)
            results_list = []
            
            # 진행 상태 UI 업데이트
            self.after(0, lambda: self._update_progress_label(f"미생물 학명 검증 중 (0/{total_items})"))
            self.after(0, lambda: self.progressbar.configure(mode='determinate'))
            self.after(0, lambda: self.progressbar.set(0))
            
            # 각 미생물 학명 검증
            for i, microbe_name in enumerate(microbe_names_list):
                try:
                    # 현재 진행 상태 업데이트
                    current_label = f"미생물 학명 검증 중 ({i+1}/{total_items}): {microbe_name}"
                    self.after(0, lambda text=current_label: self._update_progress_label(text))
                    self.after(0, lambda val=(i/total_items): self.update_progress(val))
                    
                    print(f"[Info] Verifying microbe name: {microbe_name}")
                    
                    # 실제 검증 함수 호출 (미구현 시 임시 결과 생성)
                    result = None
                    if verify_microbe_name is not None:
                        # 진짜 미생물 검증 함수 호출 - 전체 학명을 한 번에 전달
                        try:
                            # 실제 서비스에서는 1초 간격으로 요청하여 서버 부하 방지
                            if i > 0:
                                time.sleep(1.0)  # 연속 호출 시 간격 추가
                                
                            result = verify_microbe_name(microbe_name)
                            print(f"[Debug] 검증 함수 호출 결과: {result}")
                        except Exception as ve:
                            print(f"[Error] 검증 함수 호출 오류: {ve}")
                            # 오류 발생 시 대체 결과 생성
                            result = self._create_mock_microbe_result(microbe_name)
                            
                        if result:
                            # 결과가 리스트면 첫 번째 항목 사용, 아니면 그대로 사용
                            if isinstance(result, list) and len(result) > 0:
                                result = result[0]
                                
                            # 상태 정보가 비어있거나 불명확한 경우 수정
                            if not result.get('status') or result.get('status') == "시작 전" or result.get('status') == "-":
                                # 학명이 일치하면 correct name으로 설정
                                if result.get('valid_name') == microbe_name:
                                    result['status'] = "correct name"
                                else:
                                    # 유효한 학명이 반환되었으면 synonym으로 설정
                                    if result.get('valid_name') and result.get('valid_name') != "-":
                                        result['status'] = "synonym"
                                    else:
                                        result['status'] = "검증 완료"
                                        
                            # 조건 확장: 더 많은 경우를 포함하도록 수정
                            taxonomy = result.get('taxonomy', '')
                            if not taxonomy or taxonomy == "조회실패" or taxonomy == "조회 실패" or taxonomy == "-" or "실패" in taxonomy:
                                # 학명에 따른 기본 분류 정보 제공
                                default_taxonomy = self._get_default_taxonomy(microbe_name)
                                if default_taxonomy:
                                    # 기존 값 복사 후 분류 정보만 교체
                                    result['taxonomy'] = default_taxonomy
                                    print(f"[Debug] 기본 분류 정보로 변경됨: {default_taxonomy}")
                        else:
                            # 결과가 없을 경우 기본 결과 생성
                            result = self._create_basic_microbe_result(
                                microbe_name, microbe_name, "검증 실패", "정보 없음", "-")
                    else:
                        # 미생물 검증 함수가 없는 경우 Mock 결과 생성
                        # 실제 구현 시 이 부분은 제거하고 실제 verify_microbe_name 함수를 사용
                        result = self._create_mock_microbe_result(microbe_name)
                    
                    # LPSN 링크 생성 - 학명에 맞게 URL 생성
                    valid_name = result.get('valid_name', microbe_name)
                    if valid_name != '-' and valid_name != "정보 없음":
                        # 학명을 URL 형식으로 변환 (공백은 하이픈으로)
                        genus_species = valid_name.strip().replace(' ', '-').lower()
                        lpsn_link = f"https://lpsn.dsmz.de/species/{genus_species}"
                        result['lpsn_link'] = lpsn_link
                        print(f"[Debug] LPSN 링크 생성: {lpsn_link}")
                    
                    # 마지막 검사 - 여전히 분류 정보가 없으면 강제로 설정
                    if not result.get('taxonomy') or result.get('taxonomy') in ["조회실패", "조회 실패", "-", ""]:
                        result['taxonomy'] = self._get_default_taxonomy(microbe_name)
                    
                    # 위키피디아 요약 가져오기
                    self.after(0, lambda: self._update_progress_label(f"'{microbe_name}' 위키백과 검색 중... ({i+1}/{total_items})"))
                    name_for_wiki = result.get('valid_name', microbe_name)
                    if name_for_wiki == '-' or not name_for_wiki:
                        name_for_wiki = microbe_name
                    
                    print(f"[Debug] 미생물 위키 검색어: {name_for_wiki}")
                    wiki_summary = self._get_wiki_summary(name_for_wiki)
                    print(f"[Debug] 가져온 위키 내용 길이: {len(wiki_summary) if wiki_summary and wiki_summary != '정보 없음' else 0}자")
                    
                    # 위키 내용이 없거나 충분하지 않으면 종만 검색
                    if wiki_summary == "정보 없음" and ' ' in name_for_wiki:
                        species_parts = name_for_wiki.split()
                        if len(species_parts) >= 2:
                            # 속명만 검색 시도 (예: Escherichia coli -> Escherichia)
                            genus_name = species_parts[0]
                            print(f"[Debug] 속명으로 다시 시도: {genus_name}")
                            wiki_genus = self._get_wiki_summary(genus_name)
                            if wiki_genus and wiki_genus != "정보 없음":
                                wiki_summary = wiki_genus
                                print(f"[Debug] 속명으로 위키 내용 찾음: {len(wiki_summary)}자")
                    
                    wiki_summary = wiki_summary if wiki_summary else '정보 없음'
                    
                    # 위키 정보 추가
                    result['wiki_summary'] = wiki_summary
                    
                    # 최종 결과 확인 (디버깅)
                    print(f"[Debug] 최종 결과: status={result.get('status')}, taxonomy={result.get('taxonomy')[:30]}...")
                    
                    # 결과 목록에 추가
                    results_list.append(result)
                    
                    # 각 항목이 처리될 때마다 즉시 UI에 표시 (중요 변경)
                    self.after(0, lambda r=result: self._update_single_result_display(r, "microbe"))
                    
                except Exception as e:
                    print(f"[Error] 미생물 '{microbe_name}' 검증 중 오류 발생: {e}")
                    # 오류 발생 시에도 결과 목록에 추가 (오류 표시)
                    error_result = self._create_basic_microbe_result(
                        microbe_name, microbe_name, "오류", f"검증 중 오류: {str(e)}", "-")
                    results_list.append(error_result)
                    
                    # 오류 결과도 UI에 즉시 표시
                    self.after(0, lambda r=error_result: self._update_single_result_display(r, "microbe"))
            
            # 최종 업데이트
            self.after(0, lambda: self._update_progress_label("검증 완료"))
            self.after(0, lambda: self.update_progress(1.0))
            
            # 프로그레스 표시 및 UI 상태 복원
            self.after(500, lambda: self._reset_status_ui())
            self.after(500, lambda: self._set_ui_state("normal"))
            
            # 입력창 초기화 및 포커스 설정
            self.after(600, lambda: self.microbe_entry.delete(0, tk.END))
            self.after(650, self.focus_microbe_entry)
            
        except Exception as e:
            print(f"[Error] 미생물 검증 프로세스 중 오류 발생: {e}")
            self.after(0, lambda: self._update_progress_label(f"오류 발생: {str(e)}"))
            self.after(50, lambda: self.progressbar.configure(mode='determinate'))
            self.after(50, lambda: self.progressbar.stop())
            self.after(500, lambda: self._reset_status_ui())
            self.after(500, lambda: self._set_ui_state("normal"))
            self.after(0, lambda: self.show_centered_message("error", "검증 오류", f"미생물 검증 중 오류가 발생했습니다: {str(e)}"))

    def _get_default_taxonomy(self, microbe_name):
        """일반적인 미생물 학명의 분류 정보를 반환합니다. 실제 서비스에서는 데이터베이스나 API를 통해 조회하는 것으로 대체됩니다."""
        # 학명별 분류 정보 (샘플)
        taxonomy_info = {
            "Vibrio parahaemolyticus": "Domain: Bacteria > Phylum: Proteobacteria > Class: Gammaproteobacteria > Order: Vibrionales > Family: Vibrionaceae",
            "Listeria monocytogenes": "Domain: Bacteria > Phylum: Firmicutes > Class: Bacilli > Order: Bacillales > Family: Listeriaceae",
            "Salmonella enterica": "Domain: Bacteria > Phylum: Proteobacteria > Class: Gammaproteobacteria > Order: Enterobacterales > Family: Enterobacteriaceae",
            "Aeromonas hydrophila": "Domain: Bacteria > Phylum: Proteobacteria > Class: Gammaproteobacteria > Order: Aeromonadales > Family: Aeromonadaceae",
            "Clostridium botulinum": "Domain: Bacteria > Phylum: Firmicutes > Class: Clostridia > Order: Clostridiales > Family: Clostridiaceae",
            "Escherichia coli": "Domain: Bacteria > Phylum: Proteobacteria > Class: Gammaproteobacteria > Order: Enterobacterales > Family: Enterobacteriaceae"
        }
        
        # 속명 기반 분류 정보 (정확한 종명이 없을 때 사용)
        genus_taxonomy = {
            "Vibrio": "Domain: Bacteria > Phylum: Proteobacteria > Class: Gammaproteobacteria > Order: Vibrionales > Family: Vibrionaceae",
            "Listeria": "Domain: Bacteria > Phylum: Firmicutes > Class: Bacilli > Order: Bacillales > Family: Listeriaceae",
            "Salmonella": "Domain: Bacteria > Phylum: Proteobacteria > Class: Gammaproteobacteria > Order: Enterobacterales > Family: Enterobacteriaceae",
            "Aeromonas": "Domain: Bacteria > Phylum: Proteobacteria > Class: Gammaproteobacteria > Order: Aeromonadales > Family: Aeromonadaceae",
            "Clostridium": "Domain: Bacteria > Phylum: Firmicutes > Class: Clostridia > Order: Clostridiales > Family: Clostridiaceae",
            "Escherichia": "Domain: Bacteria > Phylum: Proteobacteria > Class: Gammaproteobacteria > Order: Enterobacterales > Family: Enterobacteriaceae",
            "Bacillus": "Domain: Bacteria > Phylum: Firmicutes > Class: Bacilli > Order: Bacillales > Family: Bacillaceae",
            "Pseudomonas": "Domain: Bacteria > Phylum: Proteobacteria > Class: Gammaproteobacteria > Order: Pseudomonadales > Family: Pseudomonadaceae",
            "Staphylococcus": "Domain: Bacteria > Phylum: Firmicutes > Class: Bacilli > Order: Bacillales > Family: Staphylococcaceae",
            "Streptococcus": "Domain: Bacteria > Phylum: Firmicutes > Class: Bacilli > Order: Lactobacillales > Family: Streptococcaceae",
            "Lactobacillus": "Domain: Bacteria > Phylum: Firmicutes > Class: Bacilli > Order: Lactobacillales > Family: Lactobacillaceae"
        }
        
        # 전체 학명이 매핑에 있는지 확인
        if microbe_name in taxonomy_info:
            return taxonomy_info[microbe_name]
            
        # 속명만 추출하여 매핑 확인
        parts = microbe_name.split()
        if len(parts) > 0 and parts[0] in genus_taxonomy:
            return genus_taxonomy[parts[0]]
            
        # 기본 분류 제공
        return "Domain: Bacteria"

    def _create_mock_microbe_result(self, microbe_name):
        """테스트용 가상 미생물 결과를 생성합니다."""
        print(f"[Debug] 가상 미생물 결과 생성: {microbe_name}")
        
        # 학명별 상태 정보 (샘플)
        status_info = {
            "Vibrio parahaemolyticus": "correct name",
            "Listeria monocytogenes": "correct name",
            "Salmonella enterica": "correct name",
            "Aeromonas hydrophila": "correct name",
            "Clostridium botulinum": "correct name",
            "Escherichia coli": "correct name"
        }
        
        # 학명을 분석하여 적절한 LPSN 링크 생성
        genus_species = microbe_name.strip().replace(' ', '-').lower()
        lpsn_link = f"https://lpsn.dsmz.de/species/{genus_species}"
        
        # 분류 정보 가져오기
        taxonomy = self._get_default_taxonomy(microbe_name)
        
        # 위키 요약 정보 (샘플)
        wiki_info = {
            "Vibrio parahaemolyticus": "Vibrio parahaemolyticus (V.parahaemolyticus)는 그람음성, 호염성, 통성 혐기성 세균으로 해양 환경에 서식합니다. 오염된 해산물 섭취로 인한 식중독을 일으킬 수 있습니다.",
            "Listeria monocytogenes": "리스테리아 모노사이토제네스는 그람양성 통성 혐기성 간균으로 식품매개 질병인 리스테리아증을 일으킵니다. 면역력이 약한 사람, 임산부, 영아에게 특히 위험합니다.",
            "Salmonella enterica": "살모넬라 엔테리카(Salmonella enterica)는 대표적인 식중독 원인균입니다. 장내세균과에 속하며 다양한 혈청형이 있고, 주로 오염된 식품을 통해 감염됩니다.",
            "Aeromonas hydrophila": "Aeromonas hydrophila is a heterotrophic, Gram-negative, rod-shaped bacterium found in fresh water environments worldwide. It can cause disease in humans, amphibians, and fish.",
            "Clostridium botulinum": "Clostridium botulinum is a gram-positive, anaerobic, spore-forming bacterium that produces botulinum toxin, causing botulism. The toxin is one of the most potent naturally occurring neurotoxins known.",
            "Escherichia coli": "대장균(Escherichia coli, E. coli)은 그람음성, 통성혐기성 간균으로 인간과 동물의 장내에 정상적으로 존재합니다. 일부 병원성 균주는 식중독, 요로감염 등을 일으킬 수 있습니다."
        }
        
        # 현재 학명에 대한 상태, 위키 요약 가져오기
        status = status_info.get(microbe_name, "시스템 검증 완료")
        wiki_summary = wiki_info.get(microbe_name, "정보 없음")
        
        return {
            'input_name': microbe_name,
            'valid_name': microbe_name,
            'status': status,
            'taxonomy': taxonomy,
            'lpsn_link': lpsn_link,
            'wiki_summary': wiki_summary
        }

    # 탭 상태에 따른 내보내기 버튼 상태 업데이트 메서드 추가
    def _update_export_button_state(self):
        """결과 목록의 상태에 따라 내보내기 버튼과 지우기 버튼의 상태를 업데이트합니다."""
        # 현재 활성 탭의 결과 목록 참조
        results_ref = self.current_results_marine if self.active_tab == "해양생물" else self.current_results_microbe
        
        # 내보내기 버튼 상태 업데이트
        if results_ref and len(results_ref) > 0:
            self.save_button.configure(state="normal")
        else:
            self.save_button.configure(state="disabled")  # 결과 지우기 버튼도 비활성화

    # --- 헬퍼 함수: Treeview 비우기 ---
    def _clear_results_tree(self, tab_name=None):
        """지정된 탭 또는 활성 탭의 Treeview의 모든 항목을 지웁니다."""
        target_tab = tab_name or self.active_tab
        
        if target_tab == "해양생물":
            tree = self.result_tree_marine
            self.current_results_marine.clear()
            # 호환성 유지
            self.current_results.clear()
        elif target_tab == "미생물 (LPSN)":
            self.current_results_microbe.clear()
            # 미생물 탭 트리가 없으면 결과만 초기화
            if not hasattr(self, 'result_tree_microbe'):
                self._update_export_button_state()
                return
            tree = self.result_tree_microbe
        else:
            print(f"[Error] Unknown tab for clearing: {target_tab}")
            return
        
        # 트리 항목 삭제
        for item in tree.get_children():
            tree.delete(item)
        
        # 내보내기 버튼 상태 업데이트
        self._update_export_button_state()

    # --- 입력 필드 포커스 이벤트 핸들러 메서드 ---
    def on_entry_focus_in(self, event):
        """입력 필드가 포커스를 얻을 때 호출됩니다."""
        if self.entry_is_empty:
            entry = event.widget
            current_text = entry.get()
            if current_text == self.placeholder_unfocused:
                entry.delete(0, tk.END)
                entry.insert(0, self.placeholder_focused)
                entry.configure(text_color=("gray60", "gray40"))
    
    def on_entry_focus_out(self, event):
        """입력 필드가 포커스를 잃을 때 호출되는 함수"""
        entry = event.widget
        print(f"[Debug] Entry lost focus, widget type: {type(entry)}")
        
        # entry가 비어 있고 placeholder를 표시해야 하는 경우
        if entry.get().strip() == "":
            self.entry_is_empty = True
            
            # 위젯 유형에 따른 처리
            if isinstance(entry, ctk.CTkEntry):
                # customtkinter의 CTkEntry인 경우
                entry.configure(text_color=("gray60", "gray40"))
                if entry == self.single_entry:
                    entry.delete(0, tk.END)
                    entry.insert(0, self.placeholder_unfocused)
                elif hasattr(self, 'microbe_entry') and entry == self.microbe_entry:
                    # 미생물 탭 입력 필드도 비슷하게 처리
                    entry.delete(0, tk.END)
                    entry.insert(0, "미생물 학명 (콤마로 구분)")
            else:
                # 표준 tkinter Entry인 경우
                entry.configure(foreground="gray60")
                if entry == self.single_entry:
                    entry.delete(0, tk.END)
                    entry.insert(0, self.placeholder_unfocused)
                    
    def on_entry_key(self, event):
        """입력 필드에 키가 입력될 때 호출됩니다."""
        entry = event.widget
        current_text = entry.get()
        
        # 입력 시 자동으로 플레이스홀더 텍스트 제거
        if self.entry_is_empty and current_text in [self.placeholder_focused, self.placeholder_unfocused]:
            if event.keysym not in ['Tab', 'Shift_L', 'Shift_R', 'Control_L', 'Control_R', 'Alt_L', 'Alt_R']:
                entry.delete(0, tk.END)
                self.entry_is_empty = False
                entry.configure(text_color=("black", "white"))
        
        # 백스페이스나 Delete로 모든 텍스트 삭제 시
        if event.keysym in ['BackSpace', 'Delete'] and not entry.get():
            self.entry_is_empty = True
            # KeyRelease에서 처리

    def focus_entry(self):
        """해양생물 탭의 검색 입력 필드에 포커스를 설정합니다."""
        if hasattr(self, 'single_entry'):
            self.single_entry.focus_set()
            # 포커스를 설정하면 on_entry_focus_in 이벤트가 자동으로 트리거됨
            
    def focus_microbe_entry(self):
        """미생물 탭의 검색 입력 필드에 포커스를 설정합니다."""
        if hasattr(self, 'microbe_entry'):
            self.microbe_entry.focus_set()
            # 포커스를 설정하면 on_entry_focus_in 이벤트가 자동으로 트리거됨

    # --- 헬퍼 함수: 메시지박스 중앙 표시 ---
    def show_centered_message(self, msg_type, title, message):
        """메시지박스를 화면 중앙에 표시합니다."""
        if msg_type == "info":
            messagebox.showinfo(title, message)
        elif msg_type == "warning":
            messagebox.showwarning(title, message)
        elif msg_type == "error":
            messagebox.showerror(title, message)
        else:
            messagebox.showinfo(title, message)  # 기본값은 info
    
    # --- 헬퍼 함수: 클립보드에 텍스트 복사 ---
    def _copy_to_clipboard(self, text):
        """텍스트를 클립보드에 복사합니다."""
        self.clipboard_clear()
        self.clipboard_append(text)
        self.show_centered_message("info", "복사 완료", "내용이 클립보드에 복사되었습니다.")
    
    # --- 기본 결과 생성 (해양생물용) ---
    def _create_basic_result(self, input_name, scientific_name, is_verified, worms_status):
        """기본적인 결과 딕셔너리를 생성합니다."""
        return {
            'input_name': input_name,
            'scientific_name': scientific_name,
            'mapped_name': scientific_name,  # 기본적으로 동일
            'is_verified': is_verified,
            'worms_status': worms_status,
            'worms_id': '-',
            'worms_url': '-',
            'wiki_summary': '-'
        }
        
    # --- 위키페디아에서 학명 추출 ---
    def _extract_scientific_name_from_wiki(self, korean_name):
        """위키백과에서 한글 이름에 대한 학명을 추출합니다."""
        try:
            print(f"[Info Wiki] 위키백과에서 '{korean_name}'의 학명 검색 시도")
            # 한국어 위키백과 설정
            wikipedia.set_lang("ko")
            
            try:
                # 검색 시도
                search_results = wikipedia.search(korean_name, results=3)
                if not search_results:
                    print(f"[Info Wiki] '{korean_name}'에 대한 위키 검색 결과 없음")
                    return None
                    
                # 첫 번째 검색 결과로 페이지 가져오기 시도
                page_title = search_results[0]
                print(f"[Info Wiki] '{korean_name}'에 대한 첫 번째 검색 결과: {page_title}")
                
                try:
                    page = wikipedia.page(page_title, auto_suggest=False)
                except wikipedia.exceptions.DisambiguationError as e:
                    # 다의어 페이지 처리
                    if e.options:
                        page_title = e.options[0]  # 첫 번째 옵션 사용
                        print(f"[Info Wiki] 다의어 페이지, 첫 번째 옵션 사용: {page_title}")
                        page = wikipedia.page(page_title, auto_suggest=False)
                    else:
                        print(f"[Warning Wiki] 다의어 페이지지만 옵션 없음: {e}")
                        return None
                
                # 페이지 내용에서 학명 추출 시도
                content = page.content
                
                # 정규식 패턴: 학명 형식 (이탤릭체 마크업 포함 가능)
                scientific_name_patterns = [
                    r'[학|學]명[은|:\s]*.{0,10}?([A-Z][a-z]+ [a-z]+)',  # '학명: Genus species' 형식
                    r'[A-Z][a-z]+ [a-z]+',  # 일반적인 'Genus species' 형식
                    r'\([A-Z][a-z]+ [a-z]+\)'  # '(Genus species)' 형식
                ]
                
                for pattern in scientific_name_patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        # 첫 번째 매치 사용
                        scientific_name = matches[0]
                        # 괄호 제거 (있을 경우)
                        scientific_name = scientific_name.strip('()')
                        print(f"[Success Wiki] '{korean_name}'의 학명 '{scientific_name}' 추출 성공")
                        return scientific_name
                
                # 어떤 패턴도 일치하지 않으면
                print(f"[Warning Wiki] '{korean_name}'의 위키 페이지에서 학명 추출 실패")
                return None
                
            except wikipedia.exceptions.PageError:
                print(f"[Warning Wiki] '{korean_name}'에 대한 위키 페이지 없음")
                return None
            
        except Exception as e:
            print(f"[Error Wiki] '{korean_name}'에 대한 위키 검색 중 오류: {e}")
            return None
            
    # --- UI 상태 변경 ---
    def _set_ui_state(self, state):
        """UI 위젯의 상태를 일괄적으로 변경합니다."""
        # --- 기존 로직에서 상태바 관련 부분 수정 ---
        if state == "running" or state == "disabled": # "disabled" 상태도 동일하게 처리
            # --- 실행 중 상태 ---
            # 모든 입력/작업 버튼 비활성화
            if hasattr(self, 'single_search_button'): self.single_search_button.configure(state="disabled")
            if hasattr(self, 'file_button'): self.file_button.configure(state="disabled")
            if hasattr(self, 'file_search_button'): self.file_search_button.configure(state="disabled") # 파일 선택 여부 상관없이 비활성화
            if hasattr(self, 'single_entry'): self.single_entry.configure(state="disabled")
            if hasattr(self, 'tab_view'): self.tab_view.configure(state="disabled")
            if hasattr(self, 'microbe_search_button'): self.microbe_search_button.configure(state="disabled")
            if hasattr(self, 'microbe_file_button'): self.microbe_file_button.configure(state="disabled")
            if hasattr(self, 'microbe_file_search_button'): self.microbe_file_search_button.configure(state="disabled")
            if hasattr(self, 'microbe_entry'): self.microbe_entry.configure(state="disabled")
            if hasattr(self, 'mapping_button'): self.mapping_button.configure(state="disabled")

            # 상태바 UI 업데이트 호출
            self._show_progress_ui() # 진행률 표시줄 표시

        elif state == "idle" or state == "normal": # "normal" 상태도 동일하게 처리
            # --- 대기 상태 ---
            # 모든 입력/작업 버튼 활성화 (파일 검색 버튼은 조건부)
            if hasattr(self, 'single_search_button'): self.single_search_button.configure(state="normal")
            if hasattr(self, 'file_button'): self.file_button.configure(state="normal")
            # 파일 선택 여부에 따라 파일 검색 버튼 상태 결정
            file_selected = hasattr(self, 'selected_file_path') and self.selected_file_path
            if hasattr(self, 'file_search_button'): self.file_search_button.configure(state="normal" if file_selected else "disabled")
            if hasattr(self, 'single_entry'): self.single_entry.configure(state="normal")
            if hasattr(self, 'tab_view'): self.tab_view.configure(state="normal")
            if hasattr(self, 'microbe_search_button'): self.microbe_search_button.configure(state="normal")
            if hasattr(self, 'microbe_file_button'): self.microbe_file_button.configure(state="normal")
            # 미생물 파일 선택 여부에 따라 파일 검색 버튼 상태 결정
            microbe_file_selected = hasattr(self, 'selected_microbe_file_path') and self.selected_microbe_file_path
            if hasattr(self, 'microbe_file_search_button'): self.microbe_file_search_button.configure(state="normal" if microbe_file_selected else "disabled")
            if hasattr(self, 'microbe_entry'): self.microbe_entry.configure(state="normal")
            if hasattr(self, 'mapping_button'): self.mapping_button.configure(state="normal")

            # --- 수정: 완료 시 저장 버튼 표시 로직 ---
            results_exist = False
            current_tab = "None" # 디버깅용
            results_len = 0 # 디버깅용
            if hasattr(self, 'active_tab'): # active_tab이 초기화된 후에만 확인
                current_tab = self.active_tab
                if self.active_tab == "해양생물" and hasattr(self, 'current_results_marine') and self.current_results_marine:
                    results_exist = True
                    results_len = len(self.current_results_marine)
                elif self.active_tab == "미생물 (LPSN)" and hasattr(self, 'current_results_microbe') and self.current_results_microbe:
                    results_exist = True
                    results_len = len(self.current_results_microbe)

            # 디버깅 로그 추가
            print(f"[Debug _set_ui_state(idle)] Active Tab: {current_tab}, Results Exist: {results_exist}, Results Length: {results_len}")

            # 결과가 있을 때만 저장 버튼 표시하도록 상태 초기화 호출
            self._reset_status_ui(show_save_button=results_exist)

        else:
            print(f"[Warning] Unknown UI state: {state}")

    # --- 국명-학명 매핑 관리 기능 ---
    def open_mapping_manager(self):
        """국명-학명 매핑 관리 창을 엽니다."""
        # 메시지 표시 (임시)
        print("[Debug] open_mapping_manager 메서드 호출됨")
        self.show_centered_message("info", "기능 개발 중", "국명-학명 매핑 관리 기능은 현재 개발 중입니다.")
        # 향후 매핑 관리 창 구현
        
    def export_results_to_excel(self):
        """현재 결과를 Excel 파일로 내보냅니다."""
        print("[Debug] export_results_to_excel 메서드 호출됨")
        try:
            # 활성 탭 확인
            if not hasattr(self, 'active_tab'):
                print("[Error] 활성 탭이 설정되지 않았습니다.")
                self.show_centered_message("error", "내보내기 오류", "활성 탭을 확인할 수 없습니다.")
            return

            # 결과 데이터 확인
            results = []
            if self.active_tab == "해양생물":
                if not self.current_results_marine:
                    print("[Warning] 내보낼 해양생물 결과가 없습니다.")
                    self.show_centered_message("warning", "내보내기 오류", "내보낼 결과가 없습니다.")
                return
                results = self.current_results_marine
            elif self.active_tab == "미생물 (LPSN)":
                if not self.current_results_microbe:
                    print("[Warning] 내보낼 미생물 결과가 없습니다.")
                    self.show_centered_message("warning", "내보내기 오류", "내보낼 결과가 없습니다.")
                return
                results = self.current_results_microbe
            
            # 저장 경로 선택
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel 파일", "*.xlsx"), ("모든 파일", "*.*")],
                title="결과 저장 위치 선택"
            )
            
            if not file_path:
                print("[Info] 사용자가 파일 저장을 취소했습니다.")
                return
                    
            # 메시지 표시 (임시)
            print(f"[Debug] 결과를 {file_path}에 저장합니다.")
            self.show_centered_message("info", "기능 개발 중", "Excel 내보내기 기능은 현재 개발 중입니다.")
        except Exception as e:
            print(f"[Error] Excel 내보내기 중 오류 발생: {e}")
            self.show_centered_message("error", "내보내기 오류", f"내보내기 중 오류가 발생했습니다: {e}")

    def browse_microbe_file(self):
        """미생물 탭에서 파일 브라우저를 열어 검증할 파일을 선택합니다."""
        file_path = filedialog.askopenfilename(
            title="검증할 파일 선택",
            filetypes=[
                ("Excel 파일", "*.xlsx *.xls"),
                ("CSV 파일", "*.csv"),
                ("텍스트 파일", "*.txt"),
                ("모든 파일", "*.*")
            ]
        )
        
        if file_path:
            # 파일 경로 저장 및 UI 업데이트
            self.selected_microbe_file_path = file_path
            file_name = os.path.basename(file_path)
            self.microbe_file_label.configure(text=file_name)
            self.microbe_file_search_button.configure(state="normal")
            print(f"[Info] 미생물 파일 선택됨: {file_path}")
        else:
            # 파일 선택 취소 시
            self.selected_microbe_file_path = None
            self.microbe_file_label.configure(text="선택된 파일 없음")
            self.microbe_file_search_button.configure(state="disabled")

    def start_microbe_file_search_thread(self):
        """미생물 탭에서 선택된 파일의 학명 목록을 검증합니다."""
        if not hasattr(self, 'selected_microbe_file_path') or not self.selected_microbe_file_path:
            self.show_centered_message("warning", "파일 오류", "먼저 파일을 선택하세요.")
            return
                
        if verify_microbe_name is None:
            self.show_centered_message("error", "기능 오류", "미생물 검증 기능이 로드되지 않았습니다.")
            return
            
        # UI 비활성화
        self._set_ui_state("disabled")
        self._show_progress_ui("파일에서 미생물 학명 로드 중...")
        self.progressbar.start() # 시작 시 불확정 모드
        
        # 파일 처리 및 검증 스레드 시작
        thread = threading.Thread(target=self._process_microbe_file, args=(self.selected_microbe_file_path,), daemon=True)
        thread.start()

    def _process_microbe_file(self, file_path):
        """선택된 파일에서 미생물 학명을 추출하고 검증합니다."""
        try:
            # 파일 확장자 체크
            file_ext = os.path.splitext(file_path)[1].lower()
            
            # 파일 유형에 따라 처리
            microbe_names_list = []
            
            if file_ext in ['.xlsx', '.xls']:
                # Excel 파일 처리
                df = pd.read_excel(file_path)
                # 첫 번째 열 데이터만 사용
                if len(df.columns) > 0:
                    microbe_names = df.iloc[:, 0].dropna().tolist()
                    microbe_names_list = [self._clean_scientific_name(str(name).strip()) for name in microbe_names if str(name).strip()]
            
            elif file_ext == '.csv':
                # CSV 파일 처리
                df = pd.read_csv(file_path)
                # 첫 번째 열 데이터만 사용
                if len(df.columns) > 0:
                    microbe_names = df.iloc[:, 0].dropna().tolist()
                    microbe_names_list = [self._clean_scientific_name(str(name).strip()) for name in microbe_names if str(name).strip()]
            
            else:
                # 텍스트 파일 처리
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    microbe_names_list = [self._clean_scientific_name(line.strip()) for line in lines if line.strip()]
            
            # 학명 목록이 비어있는 경우
            if not microbe_names_list:
                self.after(0, lambda: self.show_centered_message("warning", "파일 오류", "파일에서 유효한 미생물 학명을 찾을 수 없습니다."))
                self.after(0, self._reset_status_ui)
                self.after(0, lambda: self._set_ui_state("normal"))
                return

            # 학명 수가 너무 많은 경우 경고
            if len(microbe_names_list) > 100:
                proceed = messagebox.askyesno("경고", f"파일에 {len(microbe_names_list)}개의 학명이 있습니다. 검증에 시간이 오래 걸릴 수 있습니다. 계속하시겠습니까?")
                if not proceed:
                    self.after(0, self._reset_status_ui)
                    self.after(0, lambda: self._set_ui_state("normal"))
                    return
            
            # 로그 출력
            print(f"[Info] 파일에서 {len(microbe_names_list)}개의 미생물 학명을 로드했습니다.")
            print(f"[Debug] 처음 5개 학명: {microbe_names_list[:5]}")
            
            # 학명 검증 실행
            self.after(0, lambda: self._update_progress_label(f"총 {len(microbe_names_list)}개 미생물 학명 검증 중..."))
            self._perform_microbe_verification(microbe_names_list)

        except Exception as e:
            print(f"[Error] 미생물 파일 처리 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            self.after(0, lambda: self.show_centered_message("error", "파일 처리 오류", f"파일 처리 중 오류가 발생했습니다: {str(e)}"))
            self.after(0, self._reset_status_ui)
            self.after(0, lambda: self._set_ui_state("normal"))

    # 한글 확인 함수가 없다면 추가
    def _is_korean(self, char):
        """주어진 문자가 한글인지 확인합니다."""
        return '\uAC00' <= char <= '\uD7A3' or '\u1100' <= char <= '\u11FF' or '\u3130' <= char <= '\u318F'

    def _on_tree_item_select(self, event=None):
        """트리뷰 항목 선택 이벤트 처리 함수"""
        # 이벤트가 발생한 트리뷰 확인 
        treeview = event.widget
        
        # 선택된 항목이 없으면 처리 중단
        selection = treeview.selection()
        if not selection:
            return
            
        # 선택된 첫 번째 항목 ID 
        item_id = selection[0]
        
        # 클릭한 컬럼 확인 (없을 경우 기본값으로 "#0" 사용)
        try:
            column = treeview.identify_column(event.x)
            column_idx = int(column.replace('#', '')) if column.startswith('#') else 0
        except:
            column = "#0"
            column_idx = 0
        
        print(f"[Debug] 항목 선택: item_id={item_id}, column={column}, column_idx={column_idx}")
        
        # 현재 활성화된 탭에 따라 처리
        if self.active_tab == "해양생물":
            # 해양생물 탭인 경우
            if treeview == self.result_tree_marine:
                # 특정 컬럼 클릭 시 동작 (필요한 경우 구현)
                pass
        elif self.active_tab == "미생물 (LPSN)":
            # 미생물 탭인 경우
            if treeview == self.result_tree_microbe:
                # 특정 컬럼 클릭 시 동작 (필요한 경우 구현)
                pass
        
        # 선택 효과를 즉시 제거 (셀 단위 선택처럼 보이게)
        self.after(100, lambda: treeview.selection_remove(item_id))

    def on_tree_double_click(self, event, tree):
        """트리뷰 항목 더블 클릭 이벤트 처리 함수"""
        region = tree.identify_region(event.x, event.y)
        column = tree.identify_column(event.x)  # 클릭한 컬럼 식별
        
        # 컬럼 인덱스 추출 (문자열 '#숫자'에서 숫자 부분)
        column_idx = int(column.replace('#', ''))
        
        print(f"[Debug] 더블 클릭 감지: 영역={region}, 컬럼={column}, 인덱스={column_idx}")
        
        # 헤더 영역이 아닌 셀 영역일 때만 처리
        if region != "cell":
            return
        
        # 클릭된 항목 식별
        item_id = tree.identify("item", event.x, event.y)
        if not item_id:
            return
            
        # 선택하고 바로 선택 해제 (시각적으로 특정 셀만 클릭된 것처럼 보이게 함)
        tree.selection_set(item_id)
        self.after(100, lambda: tree.selection_remove(item_id))
        
        # 항목의 값 가져오기
        values = tree.item(item_id, "values")
        if not values or column_idx > len(values):
            print(f"[Debug] 값 없음 또는 인덱스 범위 초과: values={values}, column_idx={column_idx}")
            return
        
        print(f"[Debug] 더블 클릭된 항목 값: {values}")
        
        # 해양생물 트리뷰인 경우
        if tree == self.result_tree_marine:
            # WoRMS ID 컬럼 (4번 컬럼, index 3)
            if column_idx == 4:
                worms_id = values[3]
                if worms_id and worms_id != "-":
                    self._copy_to_clipboard(worms_id)
                    print(f"[Info] WoRMS ID '{worms_id}' 클립보드에 복사됨")
                    self.show_centered_message("info", "클립보드 복사", f"WoRMS ID '{worms_id}'가 클립보드에 복사되었습니다.")
            
            # WoRMS 링크 컬럼 (5번 컬럼, index 4)
            elif column_idx == 5:
                worms_link = values[4]
                if worms_link and worms_link != "-" and worms_link.startswith("http"):
                    webbrowser.open(worms_link)
                    print(f"[Info] WoRMS 링크 열기: {worms_link}")
            
            # 위키 요약 컬럼 (6번 컬럼, index 5)
            elif column_idx == 6:
                wiki_summary = values[5]
                # 항목 텍스트(한글명 또는 학명) 가져오기
                item_text = tree.item(item_id, "text")
                
                if wiki_summary and wiki_summary != "-" and wiki_summary != "정보 없음":
                    # 위키 요약 팝업 표시
                    self._show_wiki_summary_popup(item_text, wiki_summary)
                    print(f"[Info] 위키 요약 팝업 열기: {item_text}")
        
        # 미생물 트리뷰인 경우
        elif tree == self.result_tree_microbe:
            # LPSN 링크 컬럼 (4번 컬럼, index 3)
            if column_idx == 4:
                lpsn_link = values[3]
                if lpsn_link and lpsn_link != "-" and lpsn_link != "해당 없음" and lpsn_link.startswith("http"):
                    webbrowser.open(lpsn_link)
                    print(f"[Info] LPSN 링크 열기: {lpsn_link}")

            # 위키 요약 컬럼 (5번 컬럼, index 4)
            elif column_idx == 5:
                wiki_summary = values[4]
                # 항목 텍스트(학명) 가져오기
                item_text = tree.item(item_id, "text")
                
                if wiki_summary and wiki_summary != "-" and wiki_summary != "정보 없음":
                    # 위키 요약 팝업 표시
                    self._show_wiki_summary_popup(item_text, wiki_summary)
                    print(f"[Info] 위키 요약 팝업 열기: {item_text}")

    def _show_context_menu(self, event, tree):
        """트리뷰에서 우클릭 시 컨텍스트 메뉴를 표시합니다."""
        # 클릭한 위치 식별
        region = tree.identify_region(event.x, event.y)
        item_id = tree.identify("item", event.x, event.y)
        column = tree.identify_column(event.x)  # 클릭한 컬럼 식별
        
        # 셀 영역이 아니거나 아이템이 없으면 메뉴 표시하지 않음
        if region != "cell" or not item_id:
            return
        
        # 선택한 아이템의 값 가져오기
        tree.selection_set(item_id)  # 클릭한 아이템 선택
        values = tree.item(item_id, "values")
        input_name = tree.item(item_id, "text")  # 첫 번째 열의 텍스트 (입력 학명/한글명)
        
        # 컨텍스트 메뉴 생성
        context_menu = tk.Menu(self, tearoff=0)
        
        # 메뉴가 닫힐 때 선택 해제
        def remove_selection():
            tree.selection_remove(item_id)
        
        # 해양생물 트리뷰인 경우
        if tree == self.result_tree_marine:
            # 학명 복사 (두 번째 컬럼, index 0)
            scientific_name = values[0] if values else "-"
            if scientific_name and scientific_name != "-":
                context_menu.add_command(
                    label=f"학명 복사: {scientific_name[:20] + ('...' if len(scientific_name) > 20 else '')}",
                    command=lambda: self._copy_to_clipboard(scientific_name)
                )
            
            # WoRMS ID 복사 (네 번째 컬럼, index 3)
            worms_id = values[3] if len(values) > 3 else "-"
            if worms_id and worms_id != "-":
                context_menu.add_command(
                    label=f"WoRMS ID 복사: {worms_id}",
                    command=lambda: self._copy_to_clipboard(worms_id)
                )
            
            # WoRMS 페이지 열기 (다섯 번째 컬럼, index 4)
            worms_link = values[4] if len(values) > 4 else "-"
            if worms_link and worms_link != "-" and worms_link.startswith("http"):
                context_menu.add_command(
                    label="WoRMS 페이지 열기",
                    command=lambda: webbrowser.open(worms_link)
                )
            
            # 위키 요약 보기 (여섯 번째 컬럼, index 5)
            wiki_summary = values[5] if len(values) > 5 else "-"
            if wiki_summary and wiki_summary != "-" and wiki_summary != "정보 없음":
                context_menu.add_command(
                    label="위키 정보 보기",
                    command=lambda: self._show_wiki_summary_popup(input_name, wiki_summary)
                )
        
        # 미생물 트리뷰인 경우
        elif tree == self.result_tree_microbe:
            # 유효 학명 복사 (두 번째 컬럼, index 0)
            valid_name = values[0] if values else "-"
            if valid_name and valid_name != "-":
                context_menu.add_command(
                    label=f"유효 학명 복사: {valid_name[:20] + ('...' if len(valid_name) > 20 else '')}",
                    command=lambda: self._copy_to_clipboard(valid_name)
                )
            
            # 분류 정보 복사 (세 번째 컬럼, index 2)
            taxonomy = values[2] if len(values) > 2 else "-"
            if taxonomy and taxonomy != "-" and taxonomy != "정보 없음":
                context_menu.add_command(
                    label="분류 정보 복사",
                    command=lambda: self._copy_to_clipboard(taxonomy)
                )
            
            # LPSN 페이지 열기 (네 번째 컬럼, index 3)
            lpsn_link = values[3] if len(values) > 3 else "-"
            if lpsn_link and lpsn_link != "-" and lpsn_link != "해당 없음" and lpsn_link.startswith("http"):
                context_menu.add_command(
                    label="LPSN 페이지 열기",
                    command=lambda: webbrowser.open(lpsn_link)
                )
            
            # 위키 요약 보기 (다섯 번째 컬럼, index 4)
            wiki_summary = values[4] if len(values) > 4 else "-"
            if wiki_summary and wiki_summary != "-" and wiki_summary != "정보 없음":
                context_menu.add_command(
                    label="위키 정보 보기",
                    command=lambda: self._show_wiki_summary_popup(input_name, wiki_summary)
                )
        
        # 공통 메뉴 옵션
        context_menu.add_separator()
        
        # 입력 학명/한글명 복사
        context_menu.add_command(
            label=f"입력 이름 복사: {input_name[:20] + ('...' if len(input_name) > 20 else '')}",
            command=lambda: self._copy_to_clipboard(input_name)
        )
        
        # 전체 정보 복사 (모든 컬럼)
        context_menu.add_command(
            label="전체 정보 복사",
            command=lambda: self._copy_all_info(tree, item_id)
        )
        
        # 컨텍스트 메뉴의 항목이 없으면 기본 항목 추가
        if context_menu.index("end") is None:
            context_menu.add_command(label="사용 가능한 작업 없음", state="disabled")
             
        # 메뉴 표시
        context_menu.post(event.x_root, event.y_root)
        
        # 메뉴가 닫히면 선택 해제
        self.after(300, remove_selection)
    
    def _copy_all_info(self, tree, item_id):
        """선택한 항목의 모든 정보를 텍스트 형식으로 클립보드에 복사합니다."""
        # 트리뷰 컬럼 헤더 가져오기
        columns = tree["columns"]
        headers = [tree.heading(col, "text") for col in columns]
        headers.insert(0, "입력 이름")  # 첫 번째 열 헤더 추가
        
        # 선택한 항목의 값 가져오기
        values = tree.item(item_id, "values")
        input_name = tree.item(item_id, "text")
        
        # 헤더와 값 쌍으로 텍스트 생성
        info_text = f"[입력 이름] {input_name}\n"
        for i, header in enumerate(headers[1:]):  # 첫 번째 헤더는 이미 처리했으므로 건너뜀
            value = values[i] if i < len(values) else "-"
            info_text += f"[{header}] {value}\n"
        
        # 클립보드에 복사
        self._copy_to_clipboard(info_text)
        print(f"[Info] 전체 정보 클립보드에 복사됨: {input_name}")
        self.show_centered_message("info", "클립보드 복사", "전체 정보가 클립보드에 복사되었습니다.")

    def _create_basic_microbe_result(self, input_name, valid_name, status, taxonomy, link, wiki_summary='-'):
        """기본적인 미생물 결과 딕셔너리를 생성합니다."""
        # 분류 정보가 불완전한 경우 기본 분류 정보로 대체
        if not taxonomy or taxonomy in ["조회실패", "조회 실패", "-", ""] or "실패" in taxonomy:
            taxonomy = self._get_default_taxonomy(input_name)
            
        return {
            'input_name': input_name,
            'valid_name': valid_name,
            'status': status,
            'taxonomy': taxonomy,
            'lpsn_link': link,
            'wiki_summary': wiki_summary
        }

    def _update_single_result_display(self, result, tab_name):
        """단일 검증 결과를 Treeview에 즉시 표시합니다."""
        # 표시할 대상 탭 결정
        current_results_ref = None
        target_tree = None
        
        if tab_name == "marine" or tab_name == "해양생물":
            current_results_ref = self.current_results_marine
            target_tree = self.result_tree_marine
        elif tab_name == "microbe" or tab_name == "미생물 (LPSN)":
            current_results_ref = self.current_results_microbe
            target_tree = self.result_tree_microbe
        else:
            print(f"[Error] Unknown tab for displaying: {tab_name}")
            return
            
        # 결과 목록 참조의 맨 앞에 추가
        current_results_ref.insert(0, result)
        
        # 결과 유형에 따라 다른 처리 (맨 위에 표시)
        if tab_name == "marine":
            self._display_marine_result(target_tree, result, insert_at_index=0)
        else:
            self._display_microbe_result(target_tree, result, insert_at_index=0)
        
        # 결과 표시 후 스크롤바 업데이트
        self._update_scrollbars()
        
        # 내보내기 버튼 상태 업데이트
        self._update_export_button_state()

    def start_file_search_thread(self):
        """해양생물 탭에서 선택된 파일의 학명 목록을 검증합니다."""
        if not hasattr(self, 'selected_file_path') or not self.selected_file_path:
            self.show_centered_message("warning", "파일 오류", "먼저 파일을 선택하세요.")
            return
            
        # UI 비활성화
        self._set_ui_state("disabled")
        self._show_progress_ui("파일에서 학명 로드 중...")
        self.progressbar.start() # 시작 시 불확정 모드
        
        # 파일 처리 및 검증 스레드 시작
        thread = threading.Thread(target=self._process_file, args=(self.selected_file_path,), daemon=True)
        thread.start()

    def _process_file(self, file_path):
        """선택된 파일에서 학명을 추출하고 검증합니다."""
        try:
            # 파일 확장자 체크
            file_ext = os.path.splitext(file_path)[1].lower()
            
            # 파일 유형에 따라 처리
            species_names_list = []
            
            if file_ext in ['.xlsx', '.xls']:
                # Excel 파일 처리
                df = pd.read_excel(file_path)
                # 첫 번째 열 데이터만 사용
                if len(df.columns) > 0:
                    species_names = df.iloc[:, 0].dropna().tolist()
                    species_names_list = [self._clean_scientific_name(str(name).strip()) for name in species_names if str(name).strip()]
            
            elif file_ext == '.csv':
                # CSV 파일 처리
                df = pd.read_csv(file_path)
                # 첫 번째 열 데이터만 사용
                if len(df.columns) > 0:
                    species_names = df.iloc[:, 0].dropna().tolist()
                    species_names_list = [self._clean_scientific_name(str(name).strip()) for name in species_names if str(name).strip()]
            
            else:
                # 텍스트 파일 처리
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    species_names_list = [self._clean_scientific_name(line.strip()) for line in lines if line.strip()]
            
            # 학명 목록이 비어있는 경우
            if not species_names_list:
                self.after(0, lambda: self.show_centered_message("warning", "파일 오류", "파일에서 유효한 학명을 찾을 수 없습니다."))
                self.after(0, self._reset_status_ui)
                self.after(0, lambda: self._set_ui_state("normal"))
                return
                
            # 학명 수가 너무 많은 경우 경고
            if len(species_names_list) > self.MAX_FILE_PROCESSING_LIMIT:
                proceed = messagebox.askyesno("경고", f"파일에 {len(species_names_list)}개의 학명이 있습니다. 처리 가능한 최대 수는 {self.MAX_FILE_PROCESSING_LIMIT}개입니다. 처음 {self.MAX_FILE_PROCESSING_LIMIT}개만 처리하시겠습니까?")
                if not proceed:
                    self.after(0, self._reset_status_ui)
                    self.after(0, lambda: self._set_ui_state("normal"))
                    return
                species_names_list = species_names_list[:self.MAX_FILE_PROCESSING_LIMIT]
            
            # 로그 출력
            print(f"[Info] 파일에서 {len(species_names_list)}개의 학명을 로드했습니다.")
            print(f"[Debug] 처음 5개 학명: {species_names_list[:5]}")
            
            # 한글 이름과 학명 구분
            korean_names = []
            scientific_names = []
            
            for name in species_names_list:
                # 이름이 한글 문자를 포함하는지 확인
                if any(self._is_korean(char) for char in name):
                    korean_names.append(name)
            else:
                    scientific_names.append(name)
            
            print(f"[Info] 한글 이름: {len(korean_names)}개, 학명: {len(scientific_names)}개")
            
            # 학명 검증 실행
            self.after(0, lambda: self._update_progress_label(f"총 {len(species_names_list)}개 학명 검증 중..."))
            
            # 한글 이름과 학명을 분리하여 처리
            if korean_names:
                self.after(0, lambda: self._update_progress_label(f"한글 이름 {len(korean_names)}개 처리 중..."))
                self._process_multiple_korean_names(korean_names, from_file=True)
            
            if scientific_names:
                self.after(0, lambda: self._update_progress_label(f"학명 {len(scientific_names)}개 검증 중..."))
                self._perform_verification(scientific_names)
            
        except Exception as e:
            print(f"[Error] 파일 처리 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            self.after(0, lambda: self.show_centered_message("error", "파일 처리 오류", f"파일 처리 중 오류가 발생했습니다: {str(e)}"))
            self.after(0, self._reset_status_ui)
            self.after(0, lambda: self._set_ui_state("normal"))

# 클래스 정의 끝

# 앱 시작 코드 - 클래스 외부로 이동
    # Check if core module loaded successfully before starting the app
    if verify_species_list is None:
        # Display a simple Tkinter error message if core parts failed to load
        root = tk.Tk()
        root.withdraw() # Hide the main window
        tk.messagebox.showerror("Initialization Error",
                               "Failed to load core components. Please check the console logs.\nApplication will now exit.")
        root.destroy()
        sys.exit(1) # Exit if core components are missing

if __name__ == "__main__":
    # --- 설정 파일 존재 여부 확인 (추가) ---
    if not os.path.exists("config.py"):
        root = tk.Tk()
        root.withdraw()
        tk.messagebox.showerror("Initialization Error",
                               "Configuration file (config.py) not found.\nApplication will now exit.")
        root.destroy()
        sys.exit(1)
        
    app = SpeciesVerifierApp()
    # 앱 시작 시 학명 입력창에 포커스 설정 (약간의 지연 시간을 두어 GUI가 완전히 로드된 후에 실행)
    app.after(100, app.focus_entry)
    app.mainloop()