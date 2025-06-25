"""
종 검증 애플리케이션 메인 클래스

이 모듈은 종 검증 애플리케이션의
메인 클래스와 애플리케이션 실행 함수를 정의합니다.
"""
import os
import tkinter as tk
import threading
import queue # queue 임포트
import traceback # traceback 임포트
import customtkinter as ctk
from tkinter import filedialog
from typing import Optional, List, Dict, Any, Tuple, Union
# Pillow 및 CTkImage 임포트 추가
from PIL import Image
from customtkinter import CTkImage 
# Pandas 임포트 추가
import pandas as pd
import time

from species_verifier.config import app_config, ui_config
from species_verifier.gui.components.marine_tab import MarineTabFrame
from species_verifier.gui.components.microbe_tab import MicrobeTabFrame
from species_verifier.gui.components.col_tab import ColTabFrame
from species_verifier.gui.components.status_bar import StatusBar
from species_verifier.gui.components.result_view import ResultTreeview
from species_verifier.models.verification_results import MarineVerificationResult, MicrobeVerificationResult

# 브릿지 모듈 임포트
from species_verifier.gui.bridge import (
    perform_verification,
    perform_microbe_verification,
    process_file,
    process_microbe_file
)


class SpeciesVerifierApp(ctk.CTk):
    """종 검증 애플리케이션 메인 클래스"""
    
    # 탭 색상 상수 정의 (공통 관리)
    TAB_COLORS = {
        'selected_color': ("#1f538d", "#2a5a9e"),  # 활성 탭 색상 (파란색)
        'selected_hover_color': ("#144870", "#1f4a7d"),  # 활성 탭 호버
        'unselected_color': ("#d0d0d0", "#404040"),  # 비활성 탭 배경
        'unselected_hover_color': ("#c0c0c0", "#4a4a4a"),  # 비활성 탭 호버
        'text_color': ("#ffffff", "#ffffff"),  # 활성 탭 텍스트 색상 (흰색)
        'text_color_disabled': ("#2d3748", "#a0aec0"),  # 비활성 탭 텍스트 색상
        'fg_color': ("#f8f9fa", "#2b2b2b")  # 탭 영역 배경색
    }
    
    def __init__(self):
        """초기화"""
        super().__init__()
        
        # 한국어 매핑 기능 사용하지 않음
        
        # 내부 상태 변수 - active_tab 제거 (CTkTabview가 관리)
        # self.active_tab = "해양생물" 
        self.current_results_marine = []  # 해양생물 탭 결과
        self.current_results_microbe = []  # 미생물 탭 결과
        self.current_results_col = []     # 통합생물(COL) 탭 결과
        self.is_verifying = False # 현재 검증 작업 진행 여부 플래그
        self.is_cancelled = False # 작업 취소 요청 플래그 (추가)
        self.result_queue = queue.Queue() # 결과 처리를 위한 큐
        
        # 미생물 파일 로드 관련 변수 초기화
        self.current_microbe_names = None  # 파일에서 로드된 미생물 학명 목록
        self.current_microbe_context = None  # 미생물 파일 경로
        
        # 디버그 로그: 초기 self ID 및 메인 스레드 ID 기록
        self.main_thread_id = threading.get_ident()
        # 초기화 완료
        
        # 플레이스홀더 텍스트 설정
        self.placeholder_focused = "예: Homo sapiens, Gadus morhua"
        self.placeholder_unfocused = "여러 학명은 콤마로 구분 (예: Paralichthys olivaceus, Anguilla japonica)"
        
        # 기본 설정 - 모던한 디자인
        self.title("🐟 국립수산과학원 학명검증기 v1.1")
        self.geometry("950x750")  # 크기 증가
        self.minsize(850, 650)  # 최소 크기 설정
        
        # 모던한 색상 테마 설정
        ctk.set_appearance_mode("system")  # 시스템 테마 따라가기
        ctk.set_default_color_theme("blue")  # 파란색 테마
        
        # 폰트 설정
        try:
            self.default_font = ctk.CTkFont(family="Malgun Gothic", size=11)
            self.default_bold_font = ctk.CTkFont(family="Malgun Gothic", size=11, weight="bold")
            self.header_text_font = ctk.CTkFont(family="Malgun Gothic", size=13, weight="bold")
            self.header_font = ctk.CTkFont(family="Malgun Gothic", size=8)
            self.footer_font = ctk.CTkFont(family="Malgun Gothic", size=10)
        except Exception as e:
            print(f"[Warning] Font loading error: {e}. Using default fonts.")
            self.default_font = ctk.CTkFont(size=11)
            self.default_bold_font = ctk.CTkFont(size=11, weight="bold")
            self.header_text_font = ctk.CTkFont(size=13, weight="bold")
            self.header_font = ctk.CTkFont(size=8)
            self.footer_font = ctk.CTkFont(size=10)
        
        # 설정값 적용
        self.MAX_RESULTS_DISPLAY = app_config.MAX_RESULTS_DISPLAY
        self.MAX_FILE_PROCESSING_LIMIT = app_config.MAX_FILE_PROCESSING_LIMIT
        self.DIRECT_EXPORT_THRESHOLD = app_config.DIRECT_EXPORT_THRESHOLD
        self.MAX_DIRECT_INPUT_LIMIT = app_config.MAX_DIRECT_INPUT_LIMIT  # 새로 추가
        
        # 그리드 설정 (수정: 헤더 추가)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # 헤더 프레임 (고정 높이)
        self.grid_rowconfigure(1, weight=1)  # CTkTabview (확장)
        self.grid_rowconfigure(2, weight=0)  # 상태 바
        self.grid_rowconfigure(3, weight=0)  # 푸터
        
        # UI 컴포넌트 생성
        self._create_widgets()
        
        # 콜백 설정
        self._setup_callbacks()
        
        # 큐 처리기 시작
        self._process_result_queue()
    
    def _create_widgets(self):
        """UI 컴포넌트 생성"""
        # --- 헤더 프레임 (모던한 디자인) ---
        self.header_frame = ctk.CTkFrame(
            self, 
            height=70,  # 높이 증가
            corner_radius=6,
            fg_color=("#ffffff", "#1a1a1a"),  # 깔끔한 배경색
            border_width=1,
            border_color=("#e0e0e0", "#404040")  # 하단 테두리
        )
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        # 그리드 설정: 로고(왼쪽 정렬), 공간, 도움말 버튼(오른쪽 정렬)
        self.header_frame.grid_columnconfigure(0, weight=1)
        self.header_frame.grid_columnconfigure(1, weight=0)

        # 헤더 텍스트 라벨 표시 (더 큰 폰트와 그라데이션 색상)
        header_label = ctk.CTkLabel(
            self.header_frame, 
            text="🐟 국립수산과학원 학명검증기",  # 이모지 추가
            font=ctk.CTkFont(family="Malgun Gothic", size=20, weight="bold"),  # 크기 증가
            text_color=("#1f538d", "#4a9eff")  # 파란색 계열
        )
        header_label.grid(row=0, column=0, padx=20, pady=15, sticky="w")

        # 도움말 버튼 추가 (모던한 스타일)
        self.help_button = ctk.CTkButton(
            self.header_frame,
            text="❓ 도움말",  # 이모지 추가
            width=100,
            height=35,
            font=ctk.CTkFont(family="Malgun Gothic", size=12, weight="bold"),
            fg_color=("#1f538d", "#14375e"),  # 파란색 계열
            hover_color=("#144870", "#0d2a47"),
            corner_radius=8,
            command=self._show_help_popup
        )
        self.help_button.grid(row=0, column=1, padx=(0, 20), pady=15, sticky="e")

        # --- CTkTabview 생성 (1행으로 이동) - 더 세련된 디자인 ---
        self.tab_view = ctk.CTkTabview(
            self, 
            command=self._on_tab_change,
            corner_radius=6,  # 둥근 모서리 줄임
            border_width=0,   # 테두리 제거
            fg_color="transparent",  # 배경색 투명하게
            segmented_button_fg_color=self.TAB_COLORS['fg_color'],  # 탭 영역 배경색
            segmented_button_selected_color=self.TAB_COLORS['selected_color'],  # 활성 탭 색상
            segmented_button_selected_hover_color=self.TAB_COLORS['selected_hover_color'],  # 활성 탭 호버
            segmented_button_unselected_color=self.TAB_COLORS['unselected_color'],  # 비활성 탭 배경
            segmented_button_unselected_hover_color=self.TAB_COLORS['unselected_hover_color'],  # 비활성 탭 호버
            text_color=self.TAB_COLORS['text_color'],  # 활성 탭 텍스트 색상
            text_color_disabled=self.TAB_COLORS['text_color_disabled']  # 비활성 탭 텍스트 색상
        )
        self.tab_view.grid(row=1, column=0, padx=25, pady=20, sticky="nsew")  # 패딩 더 증가

        # 탭 추가 및 현대적 스타일 적용
        tab_font = ctk.CTkFont(family="Malgun Gothic", size=14, weight="bold")  # 탭 폰트 크기 증가
        
        self.tab_view.add("해양생물(WoRMS)")
        self.tab_view.add("미생물 (LPSN)")
        self.tab_view.add("담수 등 전체생물(COL)")
        
        # 탭 버튼 스타일 커스터마이징 (공통 색상 사용)
        self._apply_tab_colors_to_segmented_button(tab_font)
        
        # 탭뷰 전체 배경 스타일링 (투명 배경)
        self.tab_view.configure(
            fg_color="transparent"  # 투명 배경
        )
        
        # 개별 탭 버튼에 추가 스타일 적용 (공통 색상 사용)
        self._apply_tab_colors_to_individual_buttons(tab_font)

        # --- 해양생물 탭 컨텐츠 배치 (기존과 동일, 부모만 확인) ---
        marine_tab_content = self.tab_view.tab("해양생물(WoRMS)")
        marine_tab_content.grid_columnconfigure(0, weight=1)
        marine_tab_content.grid_rowconfigure(0, weight=0)
        marine_tab_content.grid_rowconfigure(1, weight=0)
        marine_tab_content.grid_rowconfigure(2, weight=1)
        
        self.marine_tab = MarineTabFrame(
            marine_tab_content, # 부모를 해당 탭으로 설정
            font=self.default_font,
            bold_font=self.default_bold_font,
            placeholder_text=self.placeholder_focused,
            max_direct_input_limit=self.MAX_DIRECT_INPUT_LIMIT,  # 직접 입력 제한 전달
            max_file_processing_limit=self.MAX_FILE_PROCESSING_LIMIT,
            direct_export_threshold=self.DIRECT_EXPORT_THRESHOLD
        )
        self.marine_tab.grid(row=0, column=0, sticky="ew", padx=5, pady=(5, 0))

        # 안내 레이블 추가 및 배치
        self.marine_info_label = ctk.CTkLabel(
            marine_tab_content,
            text="※ 결과가 100건을 초과하면 자동으로 파일로 저장됩니다.",
            font=ctk.CTkFont(family="Malgun Gothic", size=10),
            text_color=("gray50", "gray70"),
            anchor="e"
        )
        self.marine_info_label.grid(row=1, column=0, sticky="e", padx=5, pady=(0, 5))
        
        # 결과 트리뷰 생성 및 배치
        self.result_tree_marine = ResultTreeview(
            marine_tab_content, # 부모를 해당 탭으로 설정
            tab_type="marine",
            on_double_click=self._on_marine_tree_double_click,
            on_right_click=self._on_marine_tree_right_click,
            on_motion=self._on_marine_tree_motion
        )
        # ResultTreeview의 내부 widget (CTkFrame)을 grid로 배치
        self.result_tree_marine.widget.grid(row=2, column=0, sticky="nsew", padx=5, pady=(0, 5))

        # --- 미생물 탭 컨텐츠 배치 (기존과 동일, 부모만 확인) ---
        microbe_tab_content = self.tab_view.tab("미생물 (LPSN)")
        microbe_tab_content.grid_columnconfigure(0, weight=1)
        microbe_tab_content.grid_rowconfigure(0, weight=0)
        microbe_tab_content.grid_rowconfigure(1, weight=0)
        microbe_tab_content.grid_rowconfigure(2, weight=1)
        
        self.microbe_tab = MicrobeTabFrame(
            microbe_tab_content, # 부모를 해당 탭으로 설정
            font=self.default_font,
            bold_font=self.default_bold_font,
            placeholder_text=self.placeholder_focused, # 수정: 통일된 플레이스홀더 사용
            max_direct_input_limit=self.MAX_DIRECT_INPUT_LIMIT,  # 직접 입력 제한 전달
            max_file_processing_limit=self.MAX_FILE_PROCESSING_LIMIT
        )
        self.microbe_tab.grid(row=0, column=0, sticky="ew", padx=5, pady=(5, 0))
        
        # 안내 레이블 추가 및 배치
        self.microbe_info_label = ctk.CTkLabel(
            microbe_tab_content,
            text="※ 결과가 100건을 초과하면 자동으로 파일로 저장됩니다.",
            font=ctk.CTkFont(family="Malgun Gothic", size=10),
            text_color=("gray50", "gray70"),
            anchor="e"
        )
        self.microbe_info_label.grid(row=1, column=0, sticky="e", padx=5, pady=(0, 5))
        
        # 결과 트리뷰 생성 및 배치
        self.result_tree_microbe = ResultTreeview(
            microbe_tab_content, # 부모를 해당 탭으로 설정
            tab_type="microbe",
            on_double_click=self._on_microbe_tree_double_click,
            on_right_click=self._on_microbe_tree_right_click,
            on_motion=self._on_microbe_tree_motion
        )
        # ResultTreeview의 내부 widget (CTkFrame)을 grid로 배치
        self.result_tree_microbe.widget.grid(row=2, column=0, sticky="nsew", padx=5, pady=(0, 5))
        
        # --- COL(통합생물) 탭 ---
        # COL 탭 컨텐츠 위젯 생성
        col_tab_content = self.tab_view.tab("담수 등 전체생물(COL)")  # "통합생물(COL)"에서 변경
        col_tab_content.grid_columnconfigure(0, weight=1)
        col_tab_content.grid_rowconfigure(0, weight=0)
        col_tab_content.grid_rowconfigure(1, weight=0) # 추가: 안내 레이블 공간
        col_tab_content.grid_rowconfigure(2, weight=1)
        
        self.col_tab = ColTabFrame(
            col_tab_content,
            font=self.default_font,
            bold_font=self.default_bold_font,
            placeholder_text="예: Homo sapiens, Gadus morhua",
            max_direct_input_limit=self.MAX_DIRECT_INPUT_LIMIT,  # 직접 입력 제한 전달
            max_file_processing_limit=self.MAX_FILE_PROCESSING_LIMIT,
            direct_export_threshold=self.DIRECT_EXPORT_THRESHOLD
        )
        self.col_tab.grid(row=0, column=0, sticky="ew", padx=5, pady=(5, 0))

        # 안내 레이블 추가 및 배치 (COL 탭)
        self.col_info_label = ctk.CTkLabel(
            col_tab_content,
            text="※ 결과가 100건을 초과하면 자동으로 파일로 저장됩니다.",
            font=ctk.CTkFont(family="Malgun Gothic", size=10),
            text_color=("gray50", "gray70"),
            anchor="e"
        )
        self.col_info_label.grid(row=1, column=0, sticky="e", padx=5, pady=(0, 5))

        # 결과 트리뷰 생성 및 배치 (COL 탭)
        self.result_tree_col = ResultTreeview(
            col_tab_content, # 부모를 해당 탭으로 설정
            tab_type="col",
            on_double_click=self._on_col_tree_double_click, 
            on_right_click=self._on_col_tree_right_click, 
            on_motion=self._on_col_tree_motion
        )
        self.result_tree_col.widget.grid(row=2, column=0, sticky="nsew", padx=5, pady=(0, 5))
        
        # --- 상태 바 생성 (2행으로 이동) - 모던한 디자인 ---
        self.status_bar = StatusBar(
            self,
            height=35,  # 높이 증가
            font=self.default_font,
            save_command=self._export_active_tab_results # 현재 탭 결과 저장 명령 연결
        )
        self.status_bar.widget.grid(row=2, column=0, padx=15, pady=8, sticky="nsew")  # 패딩 증가
        self.status_bar.set_cancel_command(self._cancel_operation) # 취소 명령 설정
        # StatusBar 초기 상태 설정 (저장 버튼 숨김)
        self.status_bar.set_ready(status_text="✅ 입력 대기 중", show_save_button=False)  # 이모지 추가
        
        # --- 푸터 생성 (3행으로 이동) - 모던한 디자인 ---
        self.footer_frame = ctk.CTkFrame(
            self, 
            height=35,  # 높이 증가
            corner_radius=6,
            fg_color=("#f0f0f0", "#2b2b2b"),  # 라이트/다크 모드 배경색
            border_width=1,
            border_color=("#e0e0e0", "#404040")  # 상단 테두리
        )
        self.footer_frame.grid(row=3, column=0, padx=0, pady=0, sticky="nsew")
        self.footer_frame.grid_columnconfigure(0, weight=1)  # 중앙 정렬을 위해 전체 가중치
        
        # 중앙 컨테이너 프레임 생성
        center_container = ctk.CTkFrame(
            self.footer_frame,
            fg_color="transparent"  # 투명 배경
        )
        center_container.grid(row=0, column=0, pady=8)
        center_container.grid_columnconfigure(0, weight=0)
        center_container.grid_columnconfigure(1, weight=0)
        
        # 메인 책임기관 라벨 (중앙 배치)
        self.footer_label = ctk.CTkLabel(
            center_container,
            text="© 2025 국립수산과학원 수산생명자원 책임기관",
            font=ctk.CTkFont(family="Malgun Gothic", size=12, weight="bold"),  # 크기와 굵기 증가
            text_color=("#1f538d", "#4a9eff")  # 파란색 계열로 강조
        )
        self.footer_label.grid(row=0, column=0, padx=(0, 10))
        
        # 버전 정보 라벨 추가 (중앙 배치)
        self.version_label = ctk.CTkLabel(
            center_container,
            text="v0.5",  # 버전 수정
            font=ctk.CTkFont(family="Malgun Gothic", size=10),
            text_color=("gray50", "gray70")
        )
        self.version_label.grid(row=0, column=1)
    
    def _setup_callbacks(self):
        """콜백 설정"""
        # 해양생물 탭 콜백
        self.marine_tab.register_callback("on_search", self._marine_search)
        self.marine_tab.register_callback("on_file_browse", self._marine_file_browse)

        # 미생물 탭 콜백
        self.microbe_tab.register_callback("on_microbe_search", self._microbe_search)
        self.microbe_tab.register_callback("on_microbe_file_browse", self._microbe_file_browse)

        # 담수/기타(COL) 탭 콜백
        self.col_tab.register_callback("on_search", self._col_search)
        self.col_tab.register_callback("on_col_file_browse", self._col_file_browse)

        # 탭 변경 시 테이블 업데이트 콜백 연결
        self.tab_view.configure(command=self._on_tab_change)
    
    # --- 통합 검색 함수 ---
    def _search_species(self, input_text: str, tab_name: str = "marine"):
        """통합 학명 검색 콜백"""
        if self.is_verifying:
            self.show_centered_message("warning", "작업 중", "현재 다른 검증 작업이 진행 중입니다. 잠시 후 다시 시도해주세요.")
            return
        
        # 파일에서 로드된 데이터가 있는지 확인하고 우선 사용
        names_list = None
        context = None
        
        if tab_name == "marine":
            # 해양생물 탭: 파일 데이터 우선 사용
            if hasattr(self, 'current_marine_names') and self.current_marine_names:
                names_list = self.current_marine_names
                context = getattr(self, 'current_marine_context', None)
                print(f"[Debug] 해양생물 탭: 파일에서 로드된 {len(names_list)}개 학명 사용")
                # 사용 후 초기화하지 않음 (재사용 가능하도록)
        elif tab_name == "microbe":
            # 미생물 탭: 파일 데이터 우선 사용
            if hasattr(self, 'current_microbe_names') and self.current_microbe_names:
                names_list = self.current_microbe_names
                context = getattr(self, 'current_microbe_context', None)
                print(f"[Debug] 미생물 탭: 파일에서 로드된 {len(names_list)}개 학명 사용")
                # 사용 후 초기화하지 않음 (재사용 가능하도록)
        elif tab_name == "col":
            # COL 탭: 파일 데이터 우선 사용
            if hasattr(self, 'current_col_names') and self.current_col_names:
                names_list = self.current_col_names
                context = getattr(self, 'current_col_context', None)
                print(f"[Debug] COL 탭: 파일에서 로드된 {len(names_list)}개 학명 사용")
                # 사용 후 초기화하지 않음 (재사용 가능하도록)
        
        # 파일 데이터가 없으면 입력 텍스트 사용
        if not names_list:
            if not input_text:
                return
            
            # 입력 문자열 처리
            input_text = input_text.strip()
            # 모든 입력을 콤마로 구분된 리스트로 처리 (LPSN 방식으로 통일)
            names_list = [name.strip() for name in input_text.split(",") if name.strip()]
            context = names_list  # 직접 입력인 경우 context는 입력 리스트
            
            if not names_list:
                return
            
            print(f"[Debug] {tab_name} 탭: 직접 입력된 {len(names_list)}개 학명 사용")
        
        # 탭에 따라 적절한 검증 스레드 시작
        if tab_name == "marine":
            self._start_verification_thread(names_list)
        elif tab_name == "microbe":
            # LPSN 탭은 context도 전달
            self._start_microbe_verification_thread(names_list, context=context)
        elif tab_name == "col":
            self._start_col_verification_thread(names_list)
    
    # --- 해양생물 탭 콜백 함수 ---
    def _marine_search(self, input_text: str, tab_name: str = "marine"):
        """해양생물 검색 콜백"""
        print(f"[Debug] _marine_search 호출됨: input_text='{input_text[:50] if input_text else 'None'}', tab_name='{tab_name}'")
        
        # 파일에서 로드된 학명 목록이 있는 경우 우선 사용
        if hasattr(self, 'current_marine_names') and self.current_marine_names:
            print(f"[Debug] 해양생물 탭: 파일에서 로드된 {len(self.current_marine_names)}개 학명 사용")
            self._start_verification_thread(self.current_marine_names)
            # 사용 후 초기화하지 않음 (재사용 가능하도록)
        else:
            # 직접 입력된 텍스트로 검증
            print(f"[Debug] 해양생물 탭: 직접 입력된 텍스트로 검증 시작")
            self._search_species(input_text, tab_name="marine")

    # --- COL(통합생물) 탭 콜백 함수 ---
    def _col_search(self, input_text: str, tab_name: str = "col"):
        """COL 통합생물 검색 콜백"""
        print(f"[Debug] _col_search 호출됨: input_text='{input_text[:50] if input_text else 'None'}', tab_name='{tab_name}'")
        
        # 파일에서 로드된 학명 목록이 있는 경우 우선 사용
        if hasattr(self, 'current_col_names') and self.current_col_names:
            print(f"[Debug] COL 탭: 파일에서 로드된 {len(self.current_col_names)}개 학명 사용")
            self._start_col_verification_thread(self.current_col_names)
            # 사용 후 초기화하지 않음 (재사용 가능하도록)
        else:
            # 직접 입력된 텍스트로 검증
            print(f"[Debug] COL 탭: 직접 입력된 텍스트로 검증 시작")
            self._search_species(input_text, tab_name="col")

    def _col_file_browse(self):
        """COL 파일 선택 콜백. 파일을 선택하고 처리를 시작합니다."""
        file_path = filedialog.askopenfilename(
            title="담수 등 전체생물 학명 파일 선택",
            filetypes=(("Excel 파일", "*.xlsx"), ("CSV 파일", "*.csv"), ("모든 파일", "*.*"))
        )
        if file_path:
            # 파일 경로를 탭에 설정
            self.col_tab.set_selected_file(file_path)
            # 파일 처리 스레드 시작
            self._col_file_search(file_path)

    def _col_file_search(self, file_path: str, tab_name: str = "col"):
        """COL 파일 검색 콜백"""
        if self.is_verifying:
            self.show_centered_message("warning", "작업 중", "현재 다른 검증 작업이 진행 중입니다. 잠시 후 다시 시도해주세요.")
            return
        if not file_path or not os.path.exists(file_path):
            self.show_centered_message("error", "파일 오류", "파일을 찾을 수 없습니다.")
            return
        # 파일 처리 스레드 시작 - COL 전용 함수 사용
        threading.Thread(target=self._process_col_file, args=(file_path,), daemon=True).start()

    def _setup_cancel_button(self):
        """취소 버튼 설정"""
        # 취소 플래그 초기화
        self.is_cancelled = False
        
        # 취소 버튼 활성화 및 기능 설정
        if hasattr(self.status_bar, 'cancel_button'):
            self.status_bar.cancel_button.configure(state="normal")
            self.status_bar.set_cancel_command(self._cancel_operation)
        # 취소 버튼 설정 완료
    
    def _start_col_verification_thread(self, verification_list):
        # 파일 항목 수 초기화 (이전 값이 남아있지 않도록)
        self.current_file_item_count = 0
        self.marine_file_item_count = 0
        self.microbe_file_item_count = 0
        
        # 검증 중 플래그 설정
        self.is_verifying = True
        
        # 전체 항목 수 저장 (진행률 표시용)
        self.total_verification_items = len(verification_list)
        # COL 탭용 별도 변수에도 저장
        self.col_total_items = len(verification_list)
        
        # 다른 탭 변수 초기화
        self.marine_total_items = 0
        self.microbe_total_items = 0
        
        # 진행 UI 표시 (취소 버튼 활성화 포함)
        self._show_progress_ui("COL 검증 준비 중...")
        self._set_ui_state("disabled")  # UI 비활성화
        
        # COL 글로벌 API를 이용한 검증 스레드 시작
        import threading
        thread = threading.Thread(target=self._perform_col_verification, args=(verification_list,))
        thread.daemon = True
        thread.start()

    def _perform_col_verification(self, verification_list):
        """COL 글로벌 API를 이용한 검증 (백그라운드) - 배치 처리 적용"""
        from species_verifier.core.col_api import verify_col_species
        import time
        
        try:
            # 취소 플래그 초기화
            self.is_cancelled = False
            
            # 전체 항목 수 저장
            self.total_verification_items = len(verification_list)
            print(f"[Debug COL] 전체 COL 항목 수 설정: {self.total_verification_items}")
            
            # 배치 처리 설정
            from species_verifier.config import app_config, api_config
            BATCH_SIZE = app_config.BATCH_SIZE  # 100개
            BATCH_DELAY = api_config.BATCH_DELAY  # 2.0초
            
            total_items = len(verification_list)
            total_batches = (total_items + BATCH_SIZE - 1) // BATCH_SIZE  # 올림 나눗셈
            
            print(f"[Info COL] 배치 처리 시작: 총 {total_items}개 항목을 {total_batches}개 배치로 처리")
            print(f"[Info COL] 배치 크기: {BATCH_SIZE}개, 배치간 지연: {BATCH_DELAY}초")
            
            # 배치별 처리
            processed_items = 0
            for batch_idx in range(total_batches):
                # 취소 확인
                if self.is_cancelled:
                    print(f"[Info COL] 배치 {batch_idx + 1}/{total_batches} 처리 전 취소 감지")
                    break
                
                # 현재 배치 생성
                start_idx = batch_idx * BATCH_SIZE
                end_idx = min(start_idx + BATCH_SIZE, total_items)
                current_batch = verification_list[start_idx:end_idx]
                
                print(f"[Info COL] 배치 {batch_idx + 1}/{total_batches} 처리 시작 ({start_idx + 1}-{end_idx})")
                
                # 배치 진행률 업데이트
                batch_progress = batch_idx / total_batches
                self.after(0, lambda p=batch_progress: self.update_progress(p, batch_idx * BATCH_SIZE, total_items))
                self.after(0, lambda: self._update_progress_label(f"배치 {batch_idx + 1}/{total_batches} 처리 중..."))
                
                # 현재 배치 내 개별 항목 처리
                try:
                    for item_idx, name in enumerate(current_batch):
                        # 항목별 취소 확인
                        if self.is_cancelled:
                            print(f"[Info COL] 배치 {batch_idx + 1} 내 항목 처리 중 취소 감지")
                            break
                        
                        input_name_display = name
                        query = name
                        if isinstance(name, (tuple, list)):
                            input_name_display = name[0]
                            query = name[1] if len(name) > 1 else name[0]
                        
                        # 항목별 진행률 업데이트
                        current_item = batch_idx * BATCH_SIZE + item_idx + 1
                        item_progress = batch_progress + ((item_idx + 1) / len(current_batch)) / total_batches
                        self.after(0, lambda p=item_progress, c=current_item: self.update_progress(p, c, total_items))
                        self.after(0, lambda d=input_name_display, c=current_item: 
                                  self._update_progress_label(f"배치 {batch_idx + 1}/{total_batches}: '{d[:20]}' 검증 중... ({c}/{total_items})"))
                        
                        # 검증 실행
                        start_time = time.time()
                        # COL API 함수는 rank 매개변수를 지원하지 않으므로 제거
                        result = verify_col_species(query)
                        duration = time.time() - start_time
                        
                        print(f"[Debug] COL 항목 {current_item}/{total_items} '{input_name_display[:20]}' 완료: 소요시간 {duration:.2f}초")
                        
                        # 결과 처리
                        result['input_name'] = input_name_display
                        if not self.is_cancelled:
                            self.result_queue.put((result, 'col'))
                            print(f"[Debug] COL 결과를 COL 탭에 추가: {result.get('input_name', '')}")
                        
                        processed_items += 1
                    
                    print(f"[Info COL] 배치 {batch_idx + 1}/{total_batches} 완료, 처리된 항목: {processed_items}/{total_items}")
                    
                except Exception as e:
                    print(f"[Error COL] 배치 {batch_idx + 1} 처리 중 오류: {e}")
                    import traceback
                    traceback.print_exc()
                
                # 마지막 배치가 아니면 배치간 지연 시간 적용
                if batch_idx < total_batches - 1 and not self.is_cancelled:
                    print(f"[Info COL] 배치간 지연 시간 적용: {BATCH_DELAY}초 대기")
                    time.sleep(BATCH_DELAY)
                
                # 취소 확인 (지연 후)
                if self.is_cancelled:
                    print(f"[Info COL] 배치 {batch_idx + 1}/{total_batches} 처리 후 취소 감지")
                    break
            
            if not self.is_cancelled:
                print(f"[Info COL] 모든 배치 처리 완료: {processed_items}/{total_items}개 항목 처리됨")
                # 검증 완료 후 파일 캐시 삭제
                self.after(0, lambda: self._clear_file_cache("col"))
            else:
                print(f"[Info COL] 배치 처리 취소됨: {processed_items}/{total_items}개 항목 처리됨")
            
        except Exception as e:
            print(f"[Error _perform_col_verification] Error during batch verification: {e}")
            import traceback
            traceback.print_exc()
            self.after(0, lambda: self.show_centered_message("error", "COL 검증 오류", f"COL 검증 중 오류 발생: {e}"))
        finally:
            # 작업 완료/취소 상태 처리
            if self.is_cancelled:
                self.after(0, lambda: self._update_progress_label("검증 취소됨"))
            else:
                self.after(0, lambda: self._update_progress_label("검증 완료"))
            
            # 최종 진행률 및 상태 레이블 업데이트
            self.after(10, lambda: self.update_progress(1.0))
            
            # 프로그레스바 정지
            if hasattr(self, 'status_bar') and hasattr(self.status_bar, 'progressbar'):
                self.after(50, lambda: self.status_bar.progressbar.stop())
                self.after(50, lambda: self.status_bar.progressbar.configure(mode='determinate'))

            # UI 상태 복원 및 is_verifying 플래그 해제
            self.after(100, lambda: self._set_ui_state("normal"))
            self.after(110, lambda: setattr(self, 'is_verifying', False))
            
            # 입력 필드 초기화 및 포커스
            if hasattr(self, 'col_tab') and hasattr(self.col_tab, 'entry'):
                self.after(600, lambda: self.col_tab.entry.delete("0.0", tk.END))
    
    def _process_col_file(self, file_path: str):
        """COL 파일 처리"""
        # 이미 검증 중인지 확인
        if self.is_verifying:
            print("[Warning] 이미 검증 작업이 진행 중입니다.")
            self.after(0, lambda: self.show_centered_message(
                "warning", "작업 중", "현재 다른 검증 작업이 진행 중입니다. 잠시 후 다시 시도해주세요."
            ))
            return
            
        # 취소 상태 초기화
        self.is_cancelled = False
        
        # 검증 중 플래그 설정
        self.is_verifying = True
        
        try:
            # 브릿지 모듈의 함수 호출
            from species_verifier.gui.bridge import process_file
            names_list = process_file(file_path)
            
            # 취소 여부 확인
            if self.is_cancelled:
                print("[Info] COL 파일 처리 중 취소 요청 받음")
                self.after(0, lambda: self._reset_status_ui())
                self.after(0, lambda: self._set_ui_state("normal"))
                self.after(0, lambda: setattr(self, 'is_verifying', False))
                return
            
            if names_list:
                # 파일에서 추출한 학명 수 저장 (검증 버튼 클릭 시 사용)
                self.current_col_names = names_list
                print(f"[Debug] COL 파일에서 추출된 학명 수: {len(names_list)}")
                
                # 추출된 학명 수가 많은 경우 주의 메시지
                if len(names_list) > 50:
                    print(f"[Info App] 주의: 총 {len(names_list)}개 항목 중 일부만 처리되는 문제가 있을 수 있습니다. 모든 항목 처리를 확인합니다.")
                
                # 학명 저장 완료 로그
                print(f"[Debug] COL 파일에서 추출된 학명이 저장됨: {len(names_list)}개")
                
                # 상태 초기화 (자동 검증 시작하지 않음)
                self.after(0, lambda: self._reset_status_ui())
                self.after(0, lambda: self._set_ui_state("normal"))
                # is_verifying 플래그 해제
                self.after(0, lambda: setattr(self, 'is_verifying', False))
            else:
                self.after(0, lambda: self.show_centered_message(
                    "error", "파일 처리 오류", "파일에서 유효한 학명을 찾을 수 없습니다."
                ))
                self.after(0, lambda: self._reset_status_ui())
                self.after(0, lambda: self._set_ui_state("normal"))
                # 검증 중 플래그 해제
                self.after(0, lambda: setattr(self, 'is_verifying', False))
        except Exception as e:
            print(f"[Error] COL 파일 처리 중 오류 발생: {e}")
            self.after(0, lambda: self.show_centered_message(
                "error", "파일 처리 오류", f"파일 처리 중 오류가 발생했습니다: {e}"
            ))
            self.after(0, lambda: self._reset_status_ui())
            self.after(0, lambda: self._set_ui_state("normal"))
            # 검증 중 플래그 해제
            self.after(0, lambda: setattr(self, 'is_verifying', False))
    
    def _marine_file_browse(self):
        """해양생물 파일 선택 콜백. 파일을 선택하고 처리를 시작합니다."""
        file_path = filedialog.askopenfilename(
            title="해양생물 학명 파일 선택",
            filetypes=(("Excel 파일", "*.xlsx"), ("CSV 파일", "*.csv"), ("모든 파일", "*.*"))
        )
        if file_path:
            # 파일 경로를 탭에 설정
            self.marine_tab.set_selected_file(file_path)
            # 파일 처리 스레드 시작
            self._marine_file_search(file_path)
    
    def _marine_file_search(self, file_path: str, tab_name: str = "marine"):
        """해양생물 파일 검색 콜백"""
        if self.is_verifying:
            self.show_centered_message("warning", "작업 중", "현재 다른 검증 작업이 진행 중입니다. 잠시 후 다시 시도해주세요.")
            return
        if not file_path or not os.path.exists(file_path):
            self.show_centered_message("error", "파일 오류", "파일을 찾을 수 없습니다.")
            return
        # 파일 처리 스레드 시작
        threading.Thread(target=self._process_file, args=(file_path, "marine"), daemon=True).start()
    
    # --- 미생물 탭 콜백 함수 ---
    def _microbe_search(self, input_text: str, tab_name: str = "microbe"):
        """미생물 검색 콜백"""
        print(f"[Debug] _microbe_search 호출됨: input_text='{input_text[:50] if input_text else 'None'}', tab_name='{tab_name}'")
        
        # 파일에서 로드된 학명 목록이 있는 경우 우선 사용
        if hasattr(self, 'current_microbe_names') and self.current_microbe_names:
            print(f"[Debug] 파일에서 로드된 {len(self.current_microbe_names)}개 학명으로 검증 시작")
            context = getattr(self, 'current_microbe_context', None)
            self._start_microbe_verification_thread(self.current_microbe_names, context=context)
            # 사용 후 초기화하지 않음 (재사용 가능하도록)
        else:
            # 직접 입력된 텍스트로 검증
            print(f"[Debug] 직접 입력된 텍스트로 검증 시작: '{input_text[:50] if input_text else 'None'}'")
            self._search_species(input_text, tab_name="microbe")
    
    def _microbe_file_browse(self):
        """미생물 파일 선택 콜백. 파일을 선택하고 처리를 시작합니다."""
        file_path = filedialog.askopenfilename(
            title="미생물 학명 파일 선택",
            filetypes=(("Excel 파일", "*.xlsx"), ("CSV 파일", "*.csv"), ("모든 파일", "*.*"))
        )
        if file_path:
            # 파일 경로를 탭에 설정
            self.microbe_tab.set_selected_file(file_path)
            # 파일 처리 스레드 시작
            self._microbe_file_search(file_path)
    
    def _microbe_file_search(self, file_path: str, tab_name: str = "microbe"):
        """미생물 파일 검색 콜백"""
        if self.is_verifying:
            self.show_centered_message("warning", "작업 중", "현재 다른 검증 작업이 진행 중입니다. 잠시 후 다시 시도해주세요.")
            return
            
        if not file_path or not os.path.exists(file_path):
            self.show_centered_message("error", "파일 오류", "파일을 찾을 수 없습니다.")
            return
            
        # 파일 처리 스레드 시작 (파일 경로를 컨텍스트로 전달)
        threading.Thread(target=self._process_microbe_file, args=(file_path,), daemon=True).start()
    
    # --- 트리뷰 이벤트 처리 ---
    def _on_marine_tree_double_click(self, event):
        """해양생물 결과 더블 클릭 이벤트 처리"""
        # 현재 위치에서 컬럼과 아이템 확인
        tree = event.widget
        region = tree.identify_region(event.x, event.y)
        column = tree.identify_column(event.x)
        item_id = tree.identify("item", event.x, event.y)
        
        if not item_id or region != "cell":
            return
            
        # 컬럼 인덱스 계산 (0부터 시작)
        column_idx = int(column.replace("#", "")) - 1
        values = tree.item(item_id, "values")
        
        if column_idx >= len(values):
            return
            
        value = values[column_idx]
        
        # 컬럼별 동작 정의
        if column_idx == 4:  # WoRMS 링크
            if value and value != "-":
                # 웹 브라우저로 링크 열기
                import webbrowser
                webbrowser.open(value)
        elif column_idx == 5:  # 위키 정보
            if value and value != "-":
                # 위키 정보 팝업 표시
                self._show_wiki_summary_popup(tree.item(item_id, "text"), values[5])
    
    def _on_marine_tree_right_click(self, event):
        """해양생물 결과 우클릭 이벤트 처리"""
        # 컨텍스트 메뉴 표시 (수정: 공통 함수 호출)
        self._show_context_menu(event, "marine")
    
    def _on_marine_tree_motion(self, event):
        """해양생물 결과 마우스 이동 이벤트 처리"""
        # 현재 위치에서 컬럼 아이디 확인
        tree = event.widget
        x, y = event.x, event.y
        region = tree.identify_region(x, y)
        column_id = tree.identify_column(x)
        
        tooltip_text = None
        
        # 헤더 영역이고 특정 컬럼인 경우 툴팁 표시
        if region == "heading":
            if column_id == "#4":  # WoRMS ID 컬럼 헤더
                tooltip_text = "더블 클릭 시 WoRMS ID 복사됨"
            elif column_id == "#5":  # WoRMS Link 컬럼 헤더
                tooltip_text = "더블 클릭 시 WoRMS 웹사이트 확인"
            elif column_id == "#6":  # Wiki Summary 컬럼 헤더
                tooltip_text = "더블 클릭 시 심층분석 결과 팝업창 확인"
        
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
    
    def _on_microbe_tree_double_click(self, event):
        """미생물 결과 더블 클릭 이벤트 처리"""
        # 현재 위치에서 컬럼과 아이템 확인
        tree = event.widget
        region = tree.identify_region(event.x, event.y)
        column = tree.identify_column(event.x)
        item_id = tree.identify("item", event.x, event.y)
        
        if not item_id or region != "cell":
            return
            
        column_idx = int(column.replace("#", "")) - 1
        values = tree.item(item_id, "values")
        
        if column_idx >= len(values):
            return
            
        value = values[column_idx]
        
        # 컬럼별 동작 정의
        if column_idx == 4:  # LPSN 링크 (인덱스 4)
            if value and value != "-":
                import webbrowser
                webbrowser.open(value)
        elif column_idx == 5:  # 위키 정보 (수정: 인덱스 5)
            if value and value != "-":
                # 위키 정보 팝업 표시
                self._show_wiki_summary_popup(tree.item(item_id, "text"), values[5])
    
    def _on_microbe_tree_right_click(self, event):
        """미생물 결과 우클릭 이벤트 처리"""
        # 컨텍스트 메뉴 표시 (수정: 공통 함수 호출)
        self._show_context_menu(event, "microbe")
    
    def _on_microbe_tree_motion(self, event):
        """미생물 결과 마우스 이동 이벤트 처리"""
        # 현재 위치에서 컬럼 아이디 확인
        tree = event.widget
        x, y = event.x, event.y
        region = tree.identify_region(x, y)
        column_id = tree.identify_column(x)
        
        tooltip_text = None
        
        # 헤더 영역이고 특정 컬럼인 경우 툴팁 표시
        if region == "heading":
            # --- 디버깅 로그 주석 처리 (사용자 요청) ---
            # print(f"[Debug Tooltip] Hovering header region. Identified column_id: {column_id}")
            
            # --- 수정: 컬럼 ID와 툴팁 매핑 확인 및 조정 ---
            # Treeview 컬럼 인덱스는 #0부터 시작하지만, identify_column은 #1부터 반환하는 경향이 있음.
            # 실제 컬럼: #1(학명), #2(검증), #3(상태), #4(분류), #5(LPSN 링크), #6(위키)
            # 따라서, 분류=#4, LPSN링크=#5, 위키=#6 으로 추정하고 조건문 수정
            if column_id == "#4":  # 분류 컬럼 헤더 (기존 #3)
                tooltip_text = "분류학적 위치 정보"
            elif column_id == "#5":  # LPSN Link 컬럼 헤더 (기존 #4)
                tooltip_text = "더블 클릭 시 LPSN 웹사이트 확인"
            elif column_id == "#6":  # Wiki Summary 컬럼 헤더 (기존 #5)
                tooltip_text = "더블 클릭 시 심층분석 결과 팝업창 확인"
            # --- 수정 끝 ---
        
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
    
    # --- 공통 유틸리티 함수 ---
    
    def _start_verification_thread(self, verification_list):
        # 파일 항목 수 초기화 (이전 값이 남아있지 않도록)
        self.current_file_item_count = 0
        self.marine_file_item_count = 0
        self.microbe_file_item_count = 0
        self.col_file_item_count = 0
        
        # 전체 항목 수 초기화
        self.total_verification_items = 0
        
        # 해양생물 탭 항목 수 설정
        self.marine_total_items = len(verification_list)
        # 다른 탭 변수 초기화
        self.microbe_total_items = 0
        self.col_total_items = 0
        
        # 진행 UI 표시
        self._show_progress_ui("검증 준비 중...")
        self._set_ui_state("disabled")
        self.is_verifying = True # 검증 시작 플래그 설정
        
        # 검증 스레드 시작
        threading.Thread(
            target=self._perform_verification,
            args=(verification_list,),
            daemon=True
        ).start()

        # 입력 필드 초기화
        if self.marine_tab and self.marine_tab.entry:
            self.marine_tab.entry.delete("0.0", tk.END)
            self.marine_tab.entry.insert("0.0", self.marine_tab.initial_text)
            self.marine_tab.entry.configure(text_color="gray")
        if self.marine_tab:
             self.marine_tab.file_path_var.set("") # 파일 경로 초기화 (버튼 상태도 업데이트됨)
    
    def _perform_verification(self, verification_list_input):
        """해양생물 검증 수행 (백그라운드 스레드에서 실행) - 배치 처리 적용"""
        try:
            # 취소 플래그 초기화
            self.is_cancelled = False
            
            # 취소 확인 함수 정의
            def check_cancelled():
                return self.is_cancelled
            
            # 전체 항목 수 저장
            self.total_verification_items = len(verification_list_input)
            print(f"[Debug Marine] 전체 해양생물 항목 수 설정: {self.total_verification_items}")
            
            # 배치 처리 설정
            from species_verifier.config import app_config, api_config
            BATCH_SIZE = app_config.BATCH_SIZE  # 100개
            BATCH_DELAY = api_config.BATCH_DELAY  # 2.0초
            
            total_items = len(verification_list_input)
            total_batches = (total_items + BATCH_SIZE - 1) // BATCH_SIZE  # 올림 나눗셈
            
            print(f"[Info Marine] 배치 처리 시작: 총 {total_items}개 항목을 {total_batches}개 배치로 처리")
            print(f"[Info Marine] 배치 크기: {BATCH_SIZE}개, 배치간 지연: {BATCH_DELAY}초")
            
            # 결과 콜백 함수 정의
            def result_callback_wrapper(result, tab_type):
                if not self.is_cancelled:
                    self.result_queue.put((result, tab_type))
                    print(f"[Debug] 해양생물 결과를 해양생물 탭에 추가: {result.get('input_name', '')}")
                else:
                    print(f"[Debug] 취소되어 결과 무시: {result.get('input_name', '')}")
            
            # 배치별 처리
            processed_items = 0
            for batch_idx in range(total_batches):
                # 취소 확인
                if self.is_cancelled:
                    print(f"[Info Marine] 배치 {batch_idx + 1}/{total_batches} 처리 전 취소 감지")
                    break
                
                # 현재 배치 생성
                start_idx = batch_idx * BATCH_SIZE
                end_idx = min(start_idx + BATCH_SIZE, total_items)
                current_batch = verification_list_input[start_idx:end_idx]
                
                print(f"[Info Marine] 배치 {batch_idx + 1}/{total_batches} 처리 시작 ({start_idx + 1}-{end_idx})")
                
                # 배치 진행률 업데이트
                batch_progress = batch_idx / total_batches
                self.after(0, lambda p=batch_progress: self.update_progress(p, batch_idx * BATCH_SIZE, total_items))
                self.after(0, lambda: self._update_progress_label(f"배치 {batch_idx + 1}/{total_batches} 처리 중..."))
                
                # 현재 배치 처리
                try:
                    from species_verifier.gui.bridge import perform_verification
                    batch_results = perform_verification(
                        current_batch,
                        lambda p, curr=None, total=None: self.after(0, lambda: self.update_progress(
                            batch_progress + (p / total_batches), 
                            processed_items + (curr or 0), 
                            total_items
                        )),
                        lambda msg: self.after(0, lambda: self._update_progress_label(f"배치 {batch_idx + 1}/{total_batches}: {msg}")),
                        result_callback=result_callback_wrapper,
                        check_cancelled=check_cancelled
                    )
                    
                    processed_items += len(current_batch)
                    print(f"[Info Marine] 배치 {batch_idx + 1}/{total_batches} 완료, 처리된 항목: {processed_items}/{total_items}")
                    
                except Exception as e:
                    print(f"[Error Marine] 배치 {batch_idx + 1} 처리 중 오류: {e}")
                    import traceback
                    traceback.print_exc()
                
                # 마지막 배치가 아니면 배치간 지연 시간 적용
                if batch_idx < total_batches - 1 and not self.is_cancelled:
                    print(f"[Info Marine] 배치간 지연 시간 적용: {BATCH_DELAY}초 대기")
                    time.sleep(BATCH_DELAY)
                
                # 취소 확인 (지연 후)
                if self.is_cancelled:
                    print(f"[Info Marine] 배치 {batch_idx + 1}/{total_batches} 처리 후 취소 감지")
                    break
            
            if not self.is_cancelled:
                print(f"[Info Marine] 모든 배치 처리 완료: {processed_items}/{total_items}개 항목 처리됨")
                # 검증 완료 후 파일 캐시 삭제
                self.after(0, lambda: self._clear_file_cache("marine"))
            else:
                print(f"[Info Marine] 배치 처리 취소됨: {processed_items}/{total_items}개 항목 처리됨")
            
        except Exception as e:
            print(f"[Error _perform_verification] Error during batch verification: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # UI 상태 복원
            self.after(0, lambda: self._reset_status_ui())
            self.after(0, lambda: self._set_ui_state("normal"))
            self.after(0, lambda: setattr(self, 'is_verifying', False))
            # 완료 후 포커스 설정은 유지
            if self.marine_tab:
                self.after(0, lambda: self.marine_tab.focus_entry())

    def _start_microbe_verification_thread(self, microbe_names_list, context: Union[List[str], str, None] = None):
        """미생물 검증 스레드 시작"""
        # 진행 UI 표시 (초기 메시지 개선)
        initial_msg = "미생물 검증 준비 중..."
        if isinstance(context, str): # 파일 경로인 경우
            initial_msg = f"파일 '{os.path.basename(context)}' 검증 준비 중..."
        elif isinstance(context, list): # 직접 입력인 경우
            initial_msg = f"입력된 {len(context)}개 학명 검증 중..."
            
        self._show_progress_ui(initial_msg)
        self._set_ui_state("disabled")
        self.is_verifying = True # 검증 시작 플래그 설정
        
        # 검증 스레드 시작 (context 전달)
        threading.Thread(
            target=self._perform_microbe_verification,
            args=(microbe_names_list, context), # context 전달
            daemon=True
        ).start()

        # 입력 필드 초기화
        if self.microbe_tab and self.microbe_tab.entry:
            self.microbe_tab.entry.delete("0.0", tk.END)
            self.microbe_tab.entry.insert("0.0", self.microbe_tab.initial_text)
            self.microbe_tab.entry.configure(text_color="gray")
        if self.microbe_tab:
            self.microbe_tab.file_path_var.set("") # 파일 경로 초기화 (버튼 상태도 업데이트됨)
    
    def _perform_microbe_verification(self, microbe_names_list, context: Union[List[str], str, None] = None):
        """미생물 검증 수행 (백그라운드 스레드에서 실행) - 배치 처리 적용"""
        try:
            # 취소 플래그 초기화 및 취소 로깅 플래그 초기화
            self.is_cancelled = False
            if hasattr(self, '_cancel_logged'):
                delattr(self, '_cancel_logged')
            
            # 취소 확인 함수 정의
            def check_cancelled():
                return self.is_cancelled
            
            # 전체 항목 수 저장
            self.total_verification_items = len(microbe_names_list)
            print(f"[Debug Microbe] 전체 미생물 항목 수 설정: {self.total_verification_items}")
            
            # 배치 처리 설정
            from species_verifier.config import app_config, api_config
            BATCH_SIZE = app_config.BATCH_SIZE  # 100개
            BATCH_DELAY = api_config.BATCH_DELAY  # 2.0초
            
            total_items = len(microbe_names_list)
            total_batches = (total_items + BATCH_SIZE - 1) // BATCH_SIZE  # 올림 나눗셈
            
            print(f"[Info Microbe] 배치 처리 시작: 총 {total_items}개 항목을 {total_batches}개 배치로 처리")
            print(f"[Info Microbe] 배치 크기: {BATCH_SIZE}개, 배치간 지연: {BATCH_DELAY}초")
            
            # 결과 콜백 함수 정의
            def result_callback_wrapper(result, *args):
                if not self.is_cancelled:
                    self.result_queue.put((result, 'microbe'))
                    print(f"[Debug] 미생물 결과를 미생물 탭에 추가: {result.get('input_name', '')}")
                else:
                    print(f"[Debug] 취소되어 결과 무시: {result.get('input_name', '')}")
            
            # 배치별 처리
            processed_items = 0
            for batch_idx in range(total_batches):
                # 취소 확인
                if self.is_cancelled:
                    print(f"[Info Microbe] 배치 {batch_idx + 1}/{total_batches} 처리 전 취소 감지")
                    break
                
                # 현재 배치 생성
                start_idx = batch_idx * BATCH_SIZE
                end_idx = min(start_idx + BATCH_SIZE, total_items)
                current_batch = microbe_names_list[start_idx:end_idx]
                
                print(f"[Info Microbe] 배치 {batch_idx + 1}/{total_batches} 처리 시작 ({start_idx + 1}-{end_idx})")
                
                # 배치 진행률 업데이트
                batch_progress = batch_idx / total_batches
                self.after(0, lambda p=batch_progress: self.update_progress(p, batch_idx * BATCH_SIZE, total_items))
                self.after(0, lambda: self._update_progress_label(f"배치 {batch_idx + 1}/{total_batches} 처리 중..."))
                
                # 현재 배치 처리
                try:
                    from species_verifier.gui.bridge import perform_microbe_verification
                    batch_results = perform_microbe_verification(
                        current_batch,
                        lambda p, curr=None, total=None: self.after(0, lambda: self.update_progress(
                            batch_progress + (p / total_batches), 
                            processed_items + (curr or 0), 
                            total_items
                        )),
                        lambda msg: self.after(0, lambda: self._update_progress_label(f"배치 {batch_idx + 1}/{total_batches}: {msg}")),
                        result_callback=result_callback_wrapper,
                        context=context,
                        check_cancelled=check_cancelled
                    )
                    
                    processed_items += len(current_batch)
                    print(f"[Info Microbe] 배치 {batch_idx + 1}/{total_batches} 완료, 처리된 항목: {processed_items}/{total_items}")
                    
                except Exception as e:
                    print(f"[Error Microbe] 배치 {batch_idx + 1} 처리 중 오류: {e}")
                    import traceback
                    traceback.print_exc()
                
                # 마지막 배치가 아니면 배치간 지연 시간 적용
                if batch_idx < total_batches - 1 and not self.is_cancelled:
                    print(f"[Info Microbe] 배치간 지연 시간 적용: {BATCH_DELAY}초 대기")
                    time.sleep(BATCH_DELAY)
                
                # 취소 확인 (지연 후)
                if self.is_cancelled:
                    print(f"[Info Microbe] 배치 {batch_idx + 1}/{total_batches} 처리 후 취소 감지")
                    break
            
            if not self.is_cancelled:
                print(f"[Info Microbe] 모든 배치 처리 완료: {processed_items}/{total_items}개 항목 처리됨")
                # 검증 완료 후 파일 캐시 삭제
                self.after(0, lambda: self._clear_file_cache("microbe"))
            else:
                print(f"[Info Microbe] 배치 처리 취소됨: {processed_items}/{total_items}개 항목 처리됨")
            
        except Exception as e:
            print(f"[Error _perform_microbe_verification] Error during batch verification: {e}")
            import traceback
            traceback.print_exc()

        finally:
            # 최종 진행률 및 상태 레이블 업데이트
            self.after(0, lambda: self.update_progress(1.0))
            self.after(10, lambda: self._update_progress_label("검증 완료"))

            # 프로그레스바 정지
            if hasattr(self, 'status_bar') and hasattr(self.status_bar, 'progressbar'):
                self.after(50, lambda: self.status_bar.progressbar.stop())
                self.after(50, lambda: self.status_bar.progressbar.configure(mode='determinate'))

            # UI 상태를 'normal'로 설정하여 상태바/버튼 정리
            self.after(100, lambda: self._set_ui_state("normal"))
            self.after(20, lambda: setattr(self, 'is_verifying', False))

            # 입력창 초기화 및 포커스 설정
            if hasattr(self, 'microbe_tab') and hasattr(self.microbe_tab, 'entry'):
                self.after(600, lambda: self.microbe_tab.entry.delete("1.0", tk.END))
            if hasattr(self, 'microbe_tab') and hasattr(self.microbe_tab, 'focus_entry'):
                 self.after(650, self.microbe_tab.focus_entry)

    def _process_file(self, file_path: str, tab_name: str = "marine"):
        """파일 처리 (모든 탭 통합)
        
        Args:
            file_path: 처리할 파일 경로
            tab_name: 탭 이름 ('marine' 또는 'col')
        """
        # 이미 검증 중인지 확인
        if self.is_verifying:
            print(f"[Warning] 이미 검증 작업이 진행 중입니다.")
            self.after(0, lambda: self.show_centered_message(
                "warning", "작업 중", "현재 다른 검증 작업이 진행 중입니다. 잠시 후 다시 시도해주세요."
            ))
            return
            
        # 취소 상태 초기화
        self.is_cancelled = False
        
        # 검증 중 플래그 설정
        self.is_verifying = True
        
        try:
            # 브릿지 모듈의 함수 호출
            from species_verifier.gui.bridge import process_file
            names_list = process_file(file_path, korean_mode=False)  # 모든 탭에서 학명 모드로 처리
            
            # 파일에서 추출한 학명 수 저장 (진행률 표시용)
            self.current_file_item_count = len(names_list) if names_list else 0
            # 탭에 맞는 변수에도 저장
            if tab_name == "marine":
                self.marine_file_item_count = len(names_list) if names_list else 0
                print(f"[Debug] 해양생물 파일에서 추출된 학명 수: {self.marine_file_item_count}")
            elif tab_name == "col":
                self.col_file_item_count = len(names_list) if names_list else 0
                print(f"[Debug] COL 파일에서 추출된 학명 수: {self.col_file_item_count}")
            
            # 취소 여부 확인
            if self.is_cancelled:
                print(f"[Info] {tab_name} 파일 처리 중 취소 요청 받음")
                self.after(0, lambda: self._reset_status_ui())
                self.after(0, lambda: self._set_ui_state("normal"))
                self.after(0, lambda: setattr(self, 'is_verifying', False))
                return
            
            if names_list and len(names_list) > 0:
                # 전체 목록 처리 확인
                total_names = len(names_list)
                if total_names > 10:
                    print(f"[Info App] 주의: 총 {total_names}개 항목 중 일부만 처리되는 문제가 있을 수 있습니다. 모든 항목 처리를 확인합니다.")
                
                # 탭에 맞는 검증 데이터 저장 (자동 시작하지 않음)
                if tab_name == "marine":
                    # 해양생물 탭: 파일에서 로드된 학명을 저장
                    self.current_marine_names = names_list
                    self.current_marine_context = file_path
                    print(f"[Debug] 해양생물 파일에서 추출된 학명이 저장됨: {len(names_list)}개")
                elif tab_name == "col":
                    # COL 탭: 파일에서 로드된 학명을 저장 (자동 시작하지 않음)
                    self.current_col_names = names_list
                    self.current_col_context = file_path
                    print(f"[Debug] COL 파일에서 추출된 학명이 저장됨: {len(names_list)}개")
                
                # 상태 초기화 (자동 검증 시작하지 않음)
                self.after(0, lambda: self._reset_status_ui())
                self.after(0, lambda: self._set_ui_state("normal"))
                # is_verifying 플래그 해제
                self.after(0, lambda: setattr(self, 'is_verifying', False))
            else:
                self.after(0, lambda: self.show_centered_message(
                    "error", "파일 처리 오류", "파일에서 유효한 학명을 찾을 수 없습니다."
                ))
                self.after(0, lambda: self._reset_status_ui())
                self.after(0, lambda: self._set_ui_state("normal"))
                self.after(0, lambda: setattr(self, 'is_verifying', False))
        
        except Exception as e:
            print(f"[Error] {tab_name} 파일 처리 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            self.after(0, lambda: self.show_centered_message(
                "error", "파일 처리 오류", f"파일 처리 중 오류가 발생했습니다.\n{str(e)}"
            ))
            self.after(0, lambda: self._reset_status_ui())
            self.after(0, lambda: self._set_ui_state("normal"))
            self.after(0, lambda: setattr(self, 'is_verifying', False))
    
    def _process_microbe_file(self, file_path: str):
        """미생물 파일 처리"""
        # 이미 검증 중인지 확인
        if self.is_verifying:
            print("[Warning] 이미 검증 작업이 진행 중입니다.")
            self.after(0, lambda: self.show_centered_message(
                "warning", "작업 중", "현재 다른 검증 작업이 진행 중입니다. 잠시 후 다시 시도해주세요."
            ))
            return
            
        # 취소 상태 초기화
        self.is_cancelled = False
        
        # 검증 중 플래그 설정
        self.is_verifying = True
        
        try:
            # 브릿지 모듈의 함수 호출
            from species_verifier.gui.bridge import process_microbe_file
            names_list = process_microbe_file(file_path)
            
            # 취소 여부 확인
            if self.is_cancelled:
                print("[Info] 미생물 파일 처리 중 취소 요청 받음")
                self.after(0, lambda: self._reset_status_ui())
                self.after(0, lambda: self._set_ui_state("normal"))
                self.after(0, lambda: setattr(self, 'is_verifying', False))
                return
            
            if names_list:
                # 파일에서 추출한 학명 수 저장 (검증 버튼 클릭 시 사용)
                self.current_microbe_names = names_list
                self.current_microbe_context = file_path
                print(f"[Debug] 미생물 파일에서 추출된 학명 수: {len(names_list)}")
                
                # 상태 초기화 (자동 검증 시작하지 않음)
                self.after(0, lambda: self._reset_status_ui())
                self.after(0, lambda: self._set_ui_state("normal"))
                # is_verifying 플래그 해제
                self.after(0, lambda: setattr(self, 'is_verifying', False))
            else:
                self.after(0, lambda: self.show_centered_message(
                    "error", "파일 처리 오류", "파일에서 유효한 학명을 찾을 수 없습니다."
                ))
                self.after(0, lambda: self._reset_status_ui())
                self.after(0, lambda: self._set_ui_state("normal"))
                # 검증 중 플래그 해제
                self.after(0, lambda: setattr(self, 'is_verifying', False))
        except Exception as e:
            print(f"[Error] 미생물 파일 처리 중 오류 발생: {e}")
            self.after(0, lambda: self.show_centered_message(
                "error", "파일 처리 오류", f"파일 처리 중 오류가 발생했습니다: {e}"
            ))
            self.after(0, lambda: self._reset_status_ui())
            self.after(0, lambda: self._set_ui_state("normal"))
            # 검증 중 플래그 해제
            self.after(0, lambda: setattr(self, 'is_verifying', False))
    
    def _update_results_display(self, results_list: List[Dict[str, Any]], tab_name: str = None, clear_first: bool = False):
        """결과 표시 업데이트 (전체 리스트 업데이트용 - 큐 처리와 별개)"""
        if not results_list:
            return
        
        # 표시할 탭 결정 (CTkTabview의 현재 탭 사용)
        current_tab_name = self.tab_view.get() # 현재 활성화된 탭 이름 가져오기
            
        # 결과를 적절한 Treeview에 표시
        print(f"[Debug] 현재 탭 이름: '{current_tab_name}'")
        
        if current_tab_name == "해양생물(WoRMS)":
            target_tree = self.result_tree_marine
            target_results_list = self.current_results_marine
        elif current_tab_name == "미생물 (LPSN)":
            target_tree = self.result_tree_microbe
            target_results_list = self.current_results_microbe
        elif current_tab_name == "담수 등 전체생물(COL)":
            target_tree = self.result_tree_col 
            target_results_list = self.current_results_col
        else:
            print(f"[Warning] _update_results_display called for unknown or unsupported tab: {current_tab_name}")
            return

        # 대상 Treeview와 결과 리스트가 유효한 경우에만 진행
        if target_tree and target_results_list is not None:
            target_tree.add_results(results_list, clear_first)
            # 결과 리스트 업데이트 (큐와 중복될 수 있으므로 주의 필요, Excel 저장 시 필요)
            if clear_first:
                 target_results_list.clear()
            target_results_list.extend(results_list) 
        else:
             print(f"[Error] Target tree or results list not found for tab: {current_tab_name}")

    def _update_progress_label(self, text: str):
        """진행 상태 레이블 업데이트"""
        self.status_bar.set_status(text)
    
    def update_progress(self, progress_value: float, current_item: int = None, total_items: int = None):
        """진행 상황 업데이트 - 현재 탭에 따라 적절한 진행 상태 표시"""
        # 취소 상태인 경우 진행률 업데이트 무시
        if hasattr(self, 'is_cancelled') and self.is_cancelled:
            print(f"[Debug Progress] 취소 상태에서 진행률 업데이트 요청 무시")
            if hasattr(self, 'status_bar'):
                self.status_bar.set_progress(0, 0, 1)
            return
            
        print(f"[Debug Progress] 진행률: {progress_value}, 현재 항목: {current_item}, 전체 항목 수: {total_items}")
        
        # 전체 항목 수 결정
        actual_total_items = total_items
        
        # 전체 항목 수가 직접 전달된 경우 우선 사용
        if total_items is not None and total_items > 0:
            actual_total_items = total_items
        # 파일에서 추출한 항목 수 사용
        elif hasattr(self, 'current_file_item_count') and self.current_file_item_count is not None and self.current_file_item_count > 0:
            actual_total_items = self.current_file_item_count
        # 전체 항목 수 사용
        elif hasattr(self, 'total_verification_items') and self.total_verification_items is not None:
            actual_total_items = self.total_verification_items
        
        # 현재 항목 번호 결정
        actual_current_item = current_item
        if actual_current_item is None and actual_total_items is not None:
            actual_current_item = max(1, min(int(progress_value * actual_total_items), actual_total_items))
        
        # 진행률 업데이트
        if hasattr(self, 'status_bar'):
            self.status_bar.set_progress(progress_value, actual_current_item, actual_total_items)
    
    def _show_progress_ui(self, initial_text: str = "", reset_file_label: bool = False):
        """진행 UI 표시"""
        self.status_bar.set_busy(initial_text)
        
        # 취소 플래그 초기화 및 취소 버튼 설정
        self.is_cancelled = False
        if hasattr(self.status_bar, 'cancel_button'):
            self.status_bar.cancel_button.configure(state="normal")
            self.status_bar.set_cancel_command(self._cancel_operation)
        print("[Debug App] 취소 버튼 활성화 및 기능 설정 완료")
        
        # 파일 레이블 초기화 여부
        if reset_file_label:
            if hasattr(self, 'marine_tab'):
                self.marine_tab.set_selected_file(None)
            if hasattr(self, 'microbe_tab'):
                self.microbe_tab.set_selected_file(None)
    
    def _set_ui_state(self, state: str):
        """UI 상태 설정"""
        enable_state = tk.NORMAL if state in ["idle", "normal"] else tk.DISABLED
        is_idle = state in ["idle", "normal"]

        # --- UI 요소 상태 일괄 업데이트 ---
        # 해양생물 탭
        if hasattr(self, 'marine_tab'):
            self.marine_tab.set_input_state(enable_state) # 탭 내부 입력 요소 상태 변경
            if is_idle:
                 self.marine_tab._update_verify_button_state() # 입력/파일 상태 따라 버튼 업데이트

        # 미생물 탭
        if hasattr(self, 'microbe_tab'):
            self.microbe_tab.set_input_state(enable_state) # 탭 내부 입력 요소 상태 변경
            if is_idle:
                 self.microbe_tab._update_verify_button_state()

        # 탭 뷰 자체
        if hasattr(self, 'tab_view'):
            self.tab_view.configure(state=enable_state)

        # --- 상태 바 업데이트 ---
        if is_idle:
            results_exist = self._check_results_exist()
            print(f"[Debug _set_ui_state(idle)] Active Tab: {self.tab_view.get()}, Results Exist: {results_exist}")
            # StatusBar의 set_ready 호출 (저장 버튼 표시 여부 전달)
            if hasattr(self, 'status_bar'): # status_bar 객체 확인
                self.status_bar.set_ready(show_save_button=results_exist)
        else: # running/disabled 상태
            # 진행 표시는 _start_..._thread 함수에서 _show_progress_ui를 통해 처리
            pass
            
    # --- 결과 유무 확인 헬퍼 함수 추가 ---
    def _check_results_exist(self) -> bool:
        """현재 활성 탭에 결과가 있는지 확인합니다."""
        if not hasattr(self, 'tab_view'):
            return False
        current_tab_name = self.tab_view.get()
        if current_tab_name == "해양생물(WoRMS)":
            results_list = self.current_results_marine
        elif current_tab_name == "미생물 (LPSN)":
            results_list = self.current_results_microbe
        elif current_tab_name == "담수 등 전체생물(COL)":
            results_list = self.current_results_col
        else:
            print(f"[Debug Check Results] Unknown tab name: {current_tab_name}")
            return False
        
        return len(results_list) > 0
        
    def _process_result_queue(self):
        try:
            # 최대 처리할 항목 수 (None = 큐가 비어있을 때까지 모두 처리)
            max_items_per_call = None
            
            # 취소 요청 시에도 모든 결과 처리
            # 취소 상태에 대한 로그는 한 번만 출력하기 위해 플래그 사용
            if hasattr(self, 'is_cancelled') and self.is_cancelled and not hasattr(self, '_cancel_logged'):
                print(f"[Info] 취소된 작업이지만 모든 결과 처리 중")
                # 로그 출력 플래그 설정
                self._cancel_logged = True
            # 취소가 아닌 경우 로그 플래그 초기화
            elif not (hasattr(self, 'is_cancelled') and self.is_cancelled) and hasattr(self, '_cancel_logged'):
                delattr(self, '_cancel_logged')
            
            # 남은 큐 사이즈 확인
            queue_size = self.result_queue.qsize()
            if queue_size > 0 and (not hasattr(self, 'is_cancelled') or not self.is_cancelled):
                print(f"[Debug] 현재 큐에 {queue_size}개 결과 대기 중")
            
            # 항목 처리
            processed_count = 0
            while max_items_per_call is None or processed_count < max_items_per_call:
                try:
                    result_data = self.result_queue.get_nowait()
                    if isinstance(result_data, tuple) and len(result_data) == 2:
                        result_dict, tab_type = result_data
                        self._update_single_result(result_dict, tab_type)
                    else:
                        print(f"[Warning] Invalid data format in queue: {result_data}")
                    self.result_queue.task_done()
                    processed_count += 1
                except queue.Empty:
                    break  # 큐가 비어있으면 중단
        except Exception as e:
            print(f"[Error] Error processing result queue: {e}")
            traceback.print_exc()
        finally:
            # 큐 처리 함수 다시 스케줄링
            # 큐가 비어있거나 취소된 경우 더 빨리 처리
            delay = 20 if self.result_queue.empty() or (hasattr(self, 'is_cancelled') and self.is_cancelled) else 50
            self.after(delay, self._process_result_queue)

    def _cancel_operation(self):
        """작업 취소 - 모든 취소 기능을 이 메서드로 통합"""
        # 이미 취소 중인 경우 중복 실행 방지
        if getattr(self, '_is_cancelling', False):
            return
                
        try:
            self._is_cancelling = True
            # 취소 플래그 설정 및 UI 복원
            self.is_cancelled = True  # 취소 플래그 설정
            print("[Debug] 작업 취소 요청됨")
            
            # 취소 시 모든 탭의 파일 캐시 삭제
            self._clear_file_cache("marine")
            self._clear_file_cache("microbe")
            self._clear_file_cache("col")
            print("[Debug] 취소 시 모든 파일 캐시 삭제 완료")
            
            # 취소 버튼 비활성화 (연속 클릭 방지)
            if hasattr(self, 'status_bar') and hasattr(self.status_bar, 'cancel_button'):
                self.status_bar.cancel_button.configure(state="disabled")
                self.status_bar.set_status("검증 취소 중...")
            
            # 결과 큐 초기화 - 경쟁 상태를 예방하기 위해 주의해야 함
            try:
                while not self.result_queue.empty():
                    try:
                        self.result_queue.get_nowait()
                        self.result_queue.task_done()
                    except queue.Empty:
                        break
                print("[Debug] 결과 큐 초기화 완료")
            except Exception as e:
                print(f"[Error] Error processing result queue: {e}")
                traceback.print_exc()
            finally:
                # 큐 처리 함수 다시 스케줄링
                # 큐가 비어있거나 취소된 경우 더 빨리 처리
                delay = 20 if self.result_queue.empty() or (hasattr(self, 'is_cancelled') and self.is_cancelled) else 50
                self.after(delay, self._process_result_queue)
        except Exception as e:
            print(f"[Error] 작업 취소 중 오류 발생: {e}")
            traceback.print_exc()
        finally:
            # 취소 작업이 완료되었으므로 플래그 재설정
            self._is_cancelling = False

    def show_centered_message(self, msg_type: str, title: str, message: str):
        """중앙 메시지 표시"""
        from tkinter import messagebox
        
        if msg_type == "error":
            messagebox.showerror(title, message)
        elif msg_type == "warning":
            messagebox.showwarning(title, message)
        else:
            messagebox.showinfo(title, message)
            
    # --- 이벤트 처리 유틸리티 함수 ---
    def _show_tooltip(self, text: str, x: int, y: int):
        """마우스 커서 근처에 툴팁 팝업을 표시합니다."""
        # 기존 툴팁 윈도우 제거
        self._hide_tooltip()

        # 툴팁 위치 조정 (마우스 커서 오른쪽 아래)
        x_offset = 15
        y_offset = 10
        
        # 툴팁 윈도우 생성
        self.tooltip_window = tk.Toplevel(self)
        self.tooltip_window.wm_overrideredirect(True)  # 창 테두리 및 제목 표시줄 제거
        self.tooltip_window.wm_geometry(f"+{x + x_offset}+{y + y_offset}")  # 위치 설정
        
        # 툴팁 레이블 생성 및 배치
        tooltip_label = ctk.CTkLabel(
            self.tooltip_window, 
            text=text, 
            font=ctk.CTkFont(family="Malgun Gothic", size=10), 
            corner_radius=4,  # 약간의 둥근 모서리
            fg_color=("gray90", "gray20"),  # 배경색
            padx=5, pady=3  # 내부 여백
        )
        tooltip_label.pack()

    def _hide_tooltip(self):
        """툴팁 팝업을 숨깁니다."""
        if hasattr(self, 'tooltip_window') and self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None
            
    def _show_wiki_summary_popup(self, title: str, wiki_summary: str):
        """심층분석 결과 내용을 팝업 창으로 표시합니다."""
        import webbrowser
        
        popup = ctk.CTkToplevel(self)
        popup.title(f"종정보: {title}")
        popup.geometry("800x600")
        popup.grab_set()  # 모달 창으로 설정
        
        # 레이아웃 설정
        popup.grid_columnconfigure(0, weight=1)
        popup.grid_rowconfigure(0, weight=0)  # 제목
        popup.grid_rowconfigure(1, weight=1)  # 내용
        popup.grid_rowconfigure(2, weight=0)  # 하단 프레임 (버튼, 출처)
        
        # 제목 레이블
        title_label = ctk.CTkLabel(
            popup, 
            text=f"{title}", 
            font=ctk.CTkFont(family="Malgun Gothic", size=16, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # 내용 프레임 (스크롤 가능)
        content_frame = ctk.CTkFrame(popup)
        content_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)
        
        # 텍스트 위젯 (스크롤 가능)
        text_widget = ctk.CTkTextbox(
            content_frame, 
            wrap="word", 
            font=ctk.CTkFont(family="Malgun Gothic", size=14),
            corner_radius=6,
            padx=15, pady=15
        )
        text_widget.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        
        # 텍스트 삽입
        formatted_text = wiki_summary.replace('\n\n', '\n \n')  # 빈 줄 유지
        text_widget.insert("1.0", formatted_text)
        text_widget.configure(state="disabled")  # 읽기 전용으로 설정
        
        # 하단 프레임 (버튼, 출처용)
        bottom_frame = ctk.CTkFrame(popup)
        bottom_frame.grid(row=2, column=0, padx=20, pady=(10, 20), sticky="ew")
        bottom_frame.grid_columnconfigure(0, weight=1)  # 출처 레이블 공간
        bottom_frame.grid_columnconfigure(1, weight=0)  # 위키 링크 버튼 공간
        bottom_frame.grid_columnconfigure(2, weight=0)  # 복사 버튼 공간
        bottom_frame.grid_columnconfigure(3, weight=0)  # 닫기 버튼 공간

        # 출처 레이블
        source_label = ctk.CTkLabel(
            bottom_frame, 
            text="자료 출처: 위키백과", 
            font=ctk.CTkFont(family="Malgun Gothic", size=10, slant="italic"), 
            text_color=("gray60", "gray50")
        )
        source_label.grid(row=0, column=0, padx=(0, 10), sticky="w")
        
        # 위키피디아 링크 버튼
        wiki_url = f"https://ko.wikipedia.org/wiki/{title}"
        if wiki_summary.startswith('[영문]'):
            wiki_url = f"https://en.wikipedia.org/wiki/{title}"
        
        wiki_link_button = ctk.CTkButton(
            bottom_frame, 
            text="위키백과 원문", 
            width=120, 
            font=ctk.CTkFont(family="Malgun Gothic", size=12),
            command=lambda: webbrowser.open(wiki_url)
        )
        wiki_link_button.grid(row=0, column=1, padx=(0, 10))
        
        # 내용 복사 버튼
        copy_button = ctk.CTkButton(
            bottom_frame, 
            text="내용 복사", 
            width=100, 
            font=ctk.CTkFont(family="Malgun Gothic", size=12), 
            command=lambda: self._copy_to_clipboard(wiki_summary)
        ) 
        copy_button.grid(row=0, column=2, padx=(0, 10))

        # 닫기 버튼
        close_button = ctk.CTkButton(
            bottom_frame, 
            text="닫기", 
            command=popup.destroy, 
            width=100, 
            font=ctk.CTkFont(family="Malgun Gothic", size=12)
        )
        close_button.grid(row=0, column=3)
        
    def _copy_to_clipboard(self, text: str):
        """텍스트를 클립보드에 복사합니다."""
        self.clipboard_clear()
        self.clipboard_append(text)
        # 복사 완료 메시지는 필요 시 호출하는 곳에서 표시하도록 변경 (중복 방지)
        # self.show_centered_message("info", "복사 완료", "내용이 클립보드에 복사되었습니다.")

    def _show_context_menu(self, event, tree_type: str):
        """컨텍스트 메뉴 표시 (수정: 셀 복사 기능 추가)"""
        # 현재 클릭된 트리뷰 및 결과 리스트 가져오기
        tree = None
        current_results = None
        results_tree_component = None # ResultTreeview 인스턴스

        if tree_type == "marine":
            results_tree_component = self.result_tree_marine
            tree = results_tree_component.tree
            current_results = self.current_results_marine
        elif tree_type == "microbe":
            results_tree_component = self.result_tree_microbe
            tree = results_tree_component.tree
            current_results = self.current_results_microbe
        elif tree_type == "col":
            results_tree_component = self.result_tree_col
            tree = results_tree_component.tree
            current_results = self.current_results_col
        else:
            print(f"[Error] Unknown tree_type for context menu: {tree_type}")
            return

        # 클릭된 위치에서 선택된 아이템 확인
        item_id = tree.identify_row(event.y)
        if not item_id:
            # 빈 공간 클릭 시 전체 내보내기 메뉴만 표시하도록 수정
            context_menu = tk.Menu(self, tearoff=0)
            has_results = bool(current_results or tree.get_children())
            excel_export_state = tk.NORMAL if has_results else tk.DISABLED
            context_menu.add_command(
                label="전체 결과 내보내기",
                command=lambda: self.export_results_to_excel(tree_type),
                state=excel_export_state
            )
            try:
                context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                # 컨텍스트 메뉴가 닫히면 메모리에서 제거
                context_menu.bind("<FocusOut>", lambda e: context_menu.destroy(), add='+') # + 추가
            return

        # 클릭된 위치에서 선택된 컬럼 확인
        column_id_str = tree.identify_column(event.x) # 컬럼 ID (#1, #2...)
        column_idx = -1
        column_header_text = "" # 컬럼 헤더 텍스트 (예: '학명')
        if column_id_str.startswith("#"):
            try:
                column_idx = int(column_id_str.replace("#", "")) - 1
                # 컬럼 헤더 텍스트 가져오기 (Treeview 설정 기준)
                if column_idx >= 0 and column_idx < len(tree['columns']):
                    column_header_text = tree.heading(tree['columns'][column_idx])['text']
                else: # 0번 컬럼(#0)은 tree['columns']에 없으므로 직접 가져옴
                    column_header_text = tree.heading("#0")['text']
                    column_idx = -1 # 0번 컬럼은 values에 없으므로 인덱스는 무효화

            except (ValueError, IndexError, tk.TclError) as e:
                print(f"[Warning] Could not identify column header text: {e}")
                column_idx = -1

        # 선택된 아이템이 있다면 선택 상태로 변경
        tree.selection_set(item_id)

        # 컨텍스트 메뉴 생성
        context_menu = tk.Menu(self, tearoff=0)

        # 선택된 셀의 내용 복사 옵션 추가 (유효한 컬럼 및 인덱스인 경우)
        if column_idx >= 0 and column_header_text: # 컬럼 헤더 텍스트가 있어야 함
             try:
                 # 실제 값 가져오기 시도 (0번 컬럼은 제외)
                 cell_value = tree.item(item_id, "values")[column_idx]
                 context_menu.add_command(
                     label=f"'{column_header_text}' 내용 복사", # 컬럼 헤더 텍스트 사용
                     command=lambda t=tree_type, i=item_id, c=column_idx: self._copy_cell_content(t, i, c)
                 )
                 context_menu.add_separator()
             except (IndexError, TypeError) as e:
                 print(f"[Warning] Cannot get cell value for copy: {e}")
                 # 값 가져오기 실패 시 메뉴 추가 안 함
        elif column_idx == -1 and column_header_text == tree.heading("#0")['text']: # 입력명 컬럼(#0) 클릭 시
             try:
                  cell_value = tree.item(item_id, "text") # #0 컬럼은 text 속성 사용
                  context_menu.add_command(
                       label=f"'{column_header_text}' 내용 복사", # 컬럼 헤더 텍스트 사용
                       command=lambda val=cell_value: self._copy_to_clipboard(val) # 직접 복사
                  )
                  context_menu.add_separator()
             except Exception as e:
                   print(f"[Warning] Cannot get text value for #0 column copy: {e}")


        # 기존 메뉴 옵션들 추가 (수정: 모든 정보 복사, 전체 결과 내보내기)
        context_menu.add_command(label="선택 행 전체 정보 복사", command=lambda: self._copy_all_info(tree_type, item_id))

        # 결과 유무 확인
        has_results = bool(current_results or tree.get_children())
        excel_export_state = tk.NORMAL if has_results else tk.DISABLED
        context_menu.add_command(
            label="전체 결과 Excel로 저장",
            command=lambda: self.export_results_to_excel(tree_type),
            state=excel_export_state
        )

        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
             # 컨텍스트 메뉴가 닫히면 메모리에서 제거
             context_menu.bind("<FocusOut>", lambda e: context_menu.destroy(), add='+') # + 추가

    def _copy_cell_content(self, tree_type: str, item_id: str, column_idx: int):
        """선택된 셀의 내용 복사 (새로 추가)"""
        tree = None
        if tree_type == 'marine':
            tree = self.result_tree_marine.tree
        elif tree_type == 'microbe':
            tree = self.result_tree_microbe.tree
        elif tree_type == 'col':
            tree = self.result_tree_col.tree
        else:
            print(f"[Error] Unknown tree_type for cell copy: {tree_type}")
            return

        try:
            # 컬럼 헤더 텍스트 가져오기
            column_header_text = ""
            if column_idx >= 0 and column_idx < len(tree['columns']):
                column_header_text = tree.heading(tree['columns'][column_idx])['text']

            # 선택된 셀의 내용 가져오기
            cell_value = tree.item(item_id, "values")[column_idx]

            # 클립보드에 복사
            self._copy_to_clipboard(str(cell_value)) # 문자열로 변환하여 복사

            # 복사 완료 메시지 표시 (상태바 이용)
            status_msg = f"'{column_header_text}' 내용이 클립보드에 복사되었습니다." if column_header_text else "셀 내용이 클립보드에 복사되었습니다."
            if hasattr(self, 'status_bar'):
                self.status_bar.set_status(status_msg)
                # 잠시 후 상태바 초기화 (옵션)
                # self.after(3000, lambda: self.status_bar.set_ready())
            else:
                 # 상태바 없을 경우 메시지박스 표시
                 self.show_centered_message("info", "복사 완료", status_msg)

        except (IndexError, TypeError, tk.TclError) as e:
            print(f"[Error] 셀 내용 복사 실패: {e}")
            error_msg = "선택된 셀의 내용을 복사하는 중 오류가 발생했습니다."
            if hasattr(self, 'status_bar'):
                 self.status_bar.set_status(error_msg)
            else:
                 self.show_centered_message("error", "복사 실패", error_msg)


    def _export_active_tab_results(self):
        """현재 활성화된 탭의 결과를 Excel 파일로 저장합니다."""
        # 현재 탭 이름 가져오기
        current_tab_name = self.tab_view.get()
        print(f"[Debug] 현재 활성 탭: '{current_tab_name}'")
        
        # 탭 이름에 따라 tree_type 결정 (실제 탭 이름과 일치하도록 수정)
        tree_type = None
        if current_tab_name == "해양생물(WoRMS)":
            tree_type = "marine"
        elif current_tab_name == "미생물 (LPSN)":
            tree_type = "microbe"
        elif current_tab_name == "담수 등 전체생물(COL)":
            tree_type = "col"
        
        # 해당 탭 유형이 확인되면 export_results_to_excel 호출
        if tree_type:
            print(f"[Debug] 탭 유형 확인됨: {tree_type}")
            self.export_results_to_excel(tree_type)
        else:
            print(f"[Error] Unknown tab type for export: '{current_tab_name}'")
            self.show_centered_message("error", "저장 오류", f"알 수 없는 탭 유형입니다: '{current_tab_name}'")
    
    def export_results_to_excel(self, tree_type: str):
        """지정된 탭의 결과를 Excel 파일로 저장합니다."""
        print(f"[Debug Export] 저장 시작: tree_type={tree_type}")
        results_to_export = None
        tree = None
        columns_info = []
        default_filename = "verification_results.xlsx"

        # 수정: tree_type에 따라 정보 설정 (실제 데이터 키와 일치하도록 수정)
        if tree_type == "marine":
            results_to_export = self.current_results_marine
            tree = self.result_tree_marine.tree
            columns_info = [
                ("input_name", "입력명"), 
                ("mapped_name", "학명"), ("is_verified", "검증"), ("worms_status", "WoRMS 상태"),
                ("worms_id", "WoRMS ID"), ("worms_link", "WoRMS URL"), ("wiki_summary", "심층분석 결과")
            ]
            default_filename = "marine_verification_results.xlsx"
        elif tree_type == "microbe":
            results_to_export = self.current_results_microbe
            tree = self.result_tree_microbe.tree
            columns_info = [
                ("input_name", "입력명"), 
                ("valid_name", "유효 학명"), ("is_verified", "검증"), ("status", "상태"), 
                ("taxonomy", "분류"), ("lpsn_link", "LPSN 링크"), ("wiki_summary", "심층분석 결과")
            ]
            default_filename = "microbe_verification_results.xlsx"
        elif tree_type == "col":
            results_to_export = self.current_results_col
            tree = self.result_tree_col.tree
            columns_info = [
                ("input_name", "입력명"), 
                ("valid_name", "학명"), ("is_verified", "검증"), 
                ("status", "COL 상태"), ("col_id", "COL ID"), 
                ("col_url", "COL URL"), ("wiki_summary", "심층분석 결과")
            ]
            default_filename = "col_verification_results.xlsx"
        else:
            self.show_centered_message("warning", "내보내기 오류", f"알 수 없는 탭 유형({tree_type})의 결과는 내보낼 수 없습니다.")
            return

        # 결과 데이터 유효성 검사
        print(f"[Debug Export] 결과 검사: results_to_export={len(results_to_export) if results_to_export else 0}개, tree_children={len(tree.get_children()) if tree else 0}개")
        
        if not results_to_export and (not tree or not tree.get_children()):
             print("[Debug Export] 내보낼 결과가 없음")
             self.show_centered_message("info", "내보내기", "내보낼 결과가 없습니다.")
             return
        elif not results_to_export:
             # Treeview에서 직접 데이터 읽기 (current_results가 비었을 경우)
             print(f"[Warning Export] current_results가 비어있음. Treeview에서 직접 읽기: {tree_type}")
             results_to_export = []
             for item_id in tree.get_children():
                  item_data = {"input_name": tree.item(item_id, "text")} 
                  values = tree.item(item_id, "values")
                  for i, (key, _) in enumerate(columns_info[1:]): 
                       if i < len(values): item_data[key] = values[i]
                       else: item_data[key] = "-"
                  results_to_export.append(item_data)
             print(f"[Debug Export] Treeview에서 읽은 결과 수: {len(results_to_export)}")
             if not results_to_export:
                 print("[Debug Export] Treeview에서도 결과를 읽을 수 없음")
                 self.show_centered_message("info", "내보내기", "Treeview에서 결과를 읽을 수 없습니다.")
                 return

        # 파일 저장 경로 선택
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel 파일", "*.xlsx")],
            title=f"{tree_type.upper()} 결과 저장 위치 선택", # 수정: 탭 이름 표시
            initialfile=default_filename
        )

        if not file_path:
            return # 사용자가 취소

        try:
            print(f"[Debug Export] DataFrame 생성 시작: columns_info={columns_info}")
            df_columns = [col_key for col_key, _ in columns_info]
            print(f"[Debug Export] 사용할 컬럼: {df_columns}")
            print(f"[Debug Export] 첫 번째 결과 샘플: {results_to_export[0] if results_to_export else 'None'}")
            
            df = pd.DataFrame(results_to_export, columns=df_columns) 
            print(f"[Debug Export] DataFrame 생성 완료: shape={df.shape}")
            
            df.rename(columns={col_key: col_header for col_key, col_header in columns_info}, inplace=True)
            print(f"[Debug Export] 컬럼명 변경 완료: {list(df.columns)}")
            
            df.to_excel(file_path, index=False)
            print(f"[Debug Export] Excel 저장 완료: {file_path}")
            self.show_centered_message("info", "저장 완료", f"결과가 성공적으로 저장되었습니다.\n 경로: {file_path}")
        except Exception as e:
            print(f"[Error Export] Excel 저장 오류: {e}")
            print(traceback.format_exc())
            self.show_centered_message("error", "저장 실패", f"결과를 저장하는 중 오류가 발생했습니다.\n 오류: {e}")

    def _reset_status_ui(self):
        """UI 상태를 초기화하고 기본 상태로 되돌립니다."""
        if hasattr(self, 'status_bar'):
            self.status_bar.set_ready(status_text="입력 대기 중", show_save_button=False)
        self.is_verifying = False
        self.is_cancelled = False
        
        # 탭 색상 다시 적용 (검증 완료 후 색상 초기화 방지)
        self._reapply_tab_colors()
        
        print("[Debug] UI 상태가 초기화되었습니다.")

    def _copy_all_info(self, tree_type, item_id):
        """선택한 항목의 모든 정보를 클립보드에 복사합니다."""
        tree = None
        headers = []
        columns_info = []

        # 수정: tree_type에 따라 트리, 헤더, 컬럼 정보 설정 (실제 데이터 키와 일치하도록 수정)
        if tree_type == 'marine':
            tree = self.result_tree_marine.tree
            headers = ["입력명"] + [tree.heading(f"#{i}")['text'] for i in range(1, len(tree['columns']) + 1)]
            columns_info = [
                ("input_name", "입력명"), ("mapped_name", "학명"), ("is_verified", "검증"),
                ("worms_status", "WoRMS 상태"), ("worms_id", "WoRMS ID"), 
                ("worms_link", "WoRMS URL"), ("wiki_summary", "심층분석 결과")
            ]
        elif tree_type == 'microbe':
            tree = self.result_tree_microbe.tree
            headers = ["입력명"] + [tree.heading(f"#{i}")['text'] for i in range(1, len(tree['columns']) + 1)]
            columns_info = [
                ("input_name", "입력명"), ("valid_name", "유효 학명"), ("is_verified", "검증"),
                ("status", "상태"), ("taxonomy", "분류"), ("lpsn_link", "LPSN 링크"),
                ("wiki_summary", "심층분석 결과")
            ]
        elif tree_type == 'col':
            tree = self.result_tree_col.tree
            headers = ["입력명"] + [tree.heading(f"#{i}")['text'] for i in range(1, len(tree['columns']) + 1)]
            columns_info = [
                ("input_name", "입력명"), ("valid_name", "학명"), ("is_verified", "검증"), 
                ("status", "COL 상태"), ("col_id", "COL ID"), 
                ("col_url", "COL URL"), ("wiki_summary", "심층분석 결과")
            ]
        else:
            print(f"[Error] Unknown tree_type for copy: {tree_type}")
            return

        try:
            item = tree.item(item_id)
            values = [item['text']] + list(item['values']) 

            info_lines = []
            for i, header in enumerate(headers):
                value = values[i] if i < len(values) else ""
                col_key = columns_info[i][0] # 현재 컬럼의 키 가져오기

                # 위키 요약 축약 및 링크 N/A 처리 (모든 탭에 공통 적용)
                if col_key == "wiki_summary" and len(str(value)) > 100: 
                     # 전체 데이터 가져오기 시도
                     full_result = self._get_result_data_from_item_id(tree_type, item_id)
                     full_summary = full_result.get('wiki_summary', '') if full_result else ''
                     value = full_summary if full_summary else str(value)[:100] + "..." # 전체 없으면 축약
                elif col_key in ["worms_link", "lpsn_link", "col_url"] and (not value or value == '-'):
                     value = "N/A" 
                
                info_lines.append(f"{header}: {value}")

            copy_text = "\n".join(info_lines)
            self._copy_to_clipboard(copy_text)
            
            # 상태바에 메시지 표시 (메시지 박스 대신)
            status_msg = f"'{item['text']}' 정보가 클립보드에 복사되었습니다."
            if hasattr(self, 'status_bar'):
                 self.status_bar.set_status(status_msg)
                 # 잠시 후 상태바 초기화 (옵션)
                 # self.after(3000, lambda: self.status_bar.set_ready())
            else:
                 self.show_centered_message("info", "복사 완료", status_msg) # 상태바 없으면 메시지박스

        except Exception as e:
            print(f"[Error] 정보 복사 중 오류: {e}")
            self.status_bar.set_status("정보 복사 실패.")
            self.after(3000, self._reset_status_ui)

    # --- 새로운 메서드: 단일 결과 업데이트 (수정: COL 탭 추가) --- 
    def _update_single_result(self, result: Dict[str, Any], tab_type: str):
        """개별 검증 결과를 받아 GUI에 업데이트 (메인 스레드에서 실행)"""
        if not result:
            return

        target_tree = None
        target_results_list = None

        if tab_type == "marine":
            target_tree = self.result_tree_marine
            target_results_list = self.current_results_marine
        elif tab_type == "microbe":
            target_tree = self.result_tree_microbe
            target_results_list = self.current_results_microbe
        elif tab_type == "col":
            target_tree = self.result_tree_col
            target_results_list = self.current_results_col
        
        if target_tree:
            # 트리뷰에 결과 추가
            target_tree.add_result(result)
            
            # 결과 리스트에도 결과 추가 (중복 방지)
            if target_results_list is not None:
                # 입력명을 기준으로 중복 확인
                input_name = result.get('input_name', '')
                if not any(r.get('input_name', '') == input_name for r in target_results_list):
                    target_results_list.append(result)
                    print(f"[Debug] 결과 추가됨 ({tab_type}): {input_name}, 현재 결과 수: {len(target_results_list)}")
                else:
                    print(f"[Debug] 중복 결과 무시 ({tab_type}): {input_name}")
        else:
             print(f"[Error] Cannot update single result: Unknown tab_type '{tab_type}'")

    def _on_tab_change(self):
        """탭 변경 시 호출되는 콜백 함수"""
        # 현재 검증 작업 중이면 상태 변경하지 않음
        if self.is_verifying:
            print("[Debug Tab Change] Verification in progress, skipping status update.")
            return

        current_tab_name = self.tab_view.get()
        print(f"[Debug Tab Change] Tab changed to: {current_tab_name}")

        # 탭 색상 다시 적용 (검색 후 색상이 초기화되는 문제 해결)
        self._reapply_tab_colors()

        # 현재 탭의 결과 유무 확인
        results_exist = self._check_results_exist()
        print(f"[Debug Tab Change] Results exist in '{current_tab_name}': {results_exist}")

        # 상태 바 업데이트 (현재 탭 상태에 맞게)
        # '검증 완료' 또는 '입력 대기 중' 메시지와 함께 저장 버튼 상태 업데이트
        status_text = "검증 완료" if results_exist else "입력 대기 중"
        if hasattr(self, 'status_bar'):
            self.status_bar.set_ready(status_text=status_text, show_save_button=results_exist)

    def _reapply_tab_colors(self):
        """탭 색상을 다시 적용하는 메서드 (공통 색상 사용)"""
        try:
            # 탭 폰트 설정
            tab_font = ctk.CTkFont(family="Malgun Gothic", size=14, weight="bold")
            
            # 탭뷰 전체 색상 설정
            self._apply_tab_colors_to_segmented_button(tab_font)
            
            # 개별 탭 버튼 색상 설정
            self._apply_tab_colors_to_individual_buttons(tab_font)
            
            print("[Debug] 탭 색상 다시 적용 완료")
        except Exception as e:
            print(f"[Error] 탭 색상 재적용 중 오류: {e}")

    def _apply_tab_colors_to_segmented_button(self, tab_font):
        """segmented_button에 공통 탭 색상 적용"""
        self.tab_view._segmented_button.configure(
            font=tab_font,
            height=45,  # 탭 높이 증가
            corner_radius=6,  # 둥근 모서리 줄임
            border_width=0,  # 테두리 제거
            selected_color=self.TAB_COLORS['selected_color'],  # 활성 탭 색상
            selected_hover_color=self.TAB_COLORS['selected_hover_color'],  # 활성 탭 호버
            unselected_color=self.TAB_COLORS['unselected_color'],  # 비활성 탭 배경
            unselected_hover_color=self.TAB_COLORS['unselected_hover_color'],  # 비활성 탭 호버
            text_color=self.TAB_COLORS['text_color'],  # 활성 탭 텍스트 색상
            text_color_disabled=self.TAB_COLORS['text_color_disabled'],  # 비활성 탭 텍스트 색상
        )

    def _apply_tab_colors_to_individual_buttons(self, tab_font):
        """개별 탭 버튼에 공통 탭 색상 적용 (지원되는 속성만)"""
        for button in self.tab_view._segmented_button._buttons_dict.values():
            button.configure(
                font=tab_font,
                height=45,
                corner_radius=6,  # 둥근 모서리 줄임
                border_width=0,  # 테두리 제거
                # 개별 버튼에서는 selected_color 등의 속성을 지원하지 않음
                # 텍스트 색상만 설정 가능
                text_color=self.TAB_COLORS['text_color'],  # 활성 탭 텍스트 색상
                text_color_disabled=self.TAB_COLORS['text_color_disabled']  # 비활성 탭 텍스트 색상
            )

    # --- COL 탭 트리뷰 이벤트 핸들러 추가 ---
    def _on_col_tree_double_click(self, event):
        """COL 결과 더블 클릭 이벤트 처리"""
        # 공통 더블클릭 핸들러 호출 (타입 명시)
        self._on_result_double_click(event, 'col') # 수정: 공통 핸들러 호출

    def _on_col_tree_right_click(self, event):
        """COL 결과 우클릭 이벤트 처리"""
        # 컨텍스트 메뉴 표시 (트리 타입 'col' 전달) (수정: 공통 함수 호출)
        self._show_context_menu(event, 'col')

    def _on_col_tree_motion(self, event):
        """COL 결과 마우스 이동 이벤트 처리 (툴팁 등)"""
        # 공용 모션 핸들러 호출 (타입 명시)
        self._on_result_motion(event, 'col') # 수정: 공통 핸들러 호출

    # --- 공통 트리뷰 이벤트 핸들러 (이름 변경 및 수정) ---
    def _on_result_double_click(self, event, tree_type: str):
        """결과 트리뷰 더블 클릭 공통 처리"""
        # # 현재 위치에서 컬럼과 아이템 확인 <-- 이 블록 전체 삭제 시작
        # tree = event.widget 
        # region = tree.identify_region(event.x, event.y)
        # column = tree.identify_column(event.x)
        # item_id = tree.identify("item", event.x, event.y)
        # 
        # if not item_id or region != "cell":
        #     return
        #     
        # # 컬럼 인덱스 계산 (0부터 시작)
        # column_idx = int(column.replace("#", "")) - 1
        # values = tree.item(item_id, "values")
        # 
        # if column_idx >= len(values):
        #     return
        #     
        # value = values[column_idx]
        # 
        # # 컬럼별 동작 정의
        # if column_idx == 4:  # WoRMS 링크
        #     if value and value != "-":
        #         # 웹 브라우저로 링크 열기
        #         import webbrowser
        #         webbrowser.open(value)
        # elif column_idx == 5:  # 위키 정보
        #     if value and value != "-":
        #         # 위키 정보 팝업 표시
        #         self._show_wiki_summary_popup(tree.item(item_id, "text"), values[5])
        # <-- 이 블록 전체 삭제 끝
        # 타입별 실제 핸들러 호출
        if tree_type == 'marine':
            self._on_marine_tree_double_click(event)
        elif tree_type == 'microbe':
            self._on_microbe_tree_double_click(event)
        elif tree_type == 'col':
            # COL 탭의 더블 클릭 로직 (URL 및 위키 팝업)
            tree = self.result_tree_col.tree
            region = tree.identify_region(event.x, event.y)
            column = tree.identify_column(event.x)
            item_id = tree.identify("item", event.x, event.y) # 수정: 백슬래시 제거
            
            if not item_id or region != "cell": return
            column_idx = int(column.replace("#", "")) - 1 # 수정: 백슬래시 제거
            values = tree.item(item_id, "values") # 수정: 백슬래시 제거
            if column_idx >= len(values): return
            value = values[column_idx]

            if column_idx == 4:  # COL URL (인덱스 4)
                if value and value != "-": # 수정: 백슬래시 제거
                    import webbrowser
                    webbrowser.open(value)
            elif column_idx == 5:  # 위키 정보 (인덱스 5)
                 if value and value != "-": # 수정: 백슬래시 제거
                     selected_result = self._get_result_data_from_item_id('col', item_id)
                     if selected_result and selected_result.get('wiki_summary'):
                         self._show_wiki_summary_popup(tree.item(item_id, "text"), selected_result['wiki_summary']) # 수정: 백슬래시 제거
                     elif value:
                          self._show_wiki_summary_popup(tree.item(item_id, "text"), value) # 수정: 백슬래시 제거
            
    def _on_result_motion(self, event, tree_type: str):
        """결과 트리뷰 마우스 이동 공통 처리 (툴팁 등)"""
        # 타입별 실제 모션 핸들러 호출
        if tree_type == 'marine':
            self._on_marine_tree_motion(event)
        elif tree_type == 'microbe':
            self._on_microbe_tree_motion(event)
        elif tree_type == 'col':
            # COL 탭의 모션 로직 (툴팁)
            tree = self.result_tree_col.tree
            header_tooltips = {
                "#4": "더블 클릭 시 COL ID 복사됨", 
                "#5": "더블 클릭 시 COL 웹사이트 확인", 
                "#6": "더블 클릭 시 심층분석 결과 팝업창 확인" 
            }
            x, y = event.x, event.y
            region = tree.identify_region(x, y)
            column_id = tree.identify_column(x)
            tooltip_text = None

            if region == "heading": # 수정: 백슬래시 제거
                tooltip_text = header_tooltips.get(column_id)
            elif region == "cell": # 수정: 백슬래시 제거
                item_id = tree.identify("item", x, y) # 수정: 백슬래시 제거
                if item_id:
                    values = tree.item(item_id, "values") # 수정: 백슬래시 제거
                    column_idx = int(column_id.replace("#", "")) - 1 # 수정: 백슬래시 제거
                    if 0 <= column_idx < len(values):
                        value = values[column_idx]
                        if len(str(value)) > 40 and value != "-": # 수정: 백슬래시 제거
                            tooltip_text = str(value)
            
            if tooltip_text:
                self._show_tooltip(tooltip_text, event.x_root, event.y_root)
            else:
                self._hide_tooltip()

    # --- 도움말 팝업 메서드 추가 ---
    def _show_help_popup(self):
        """도움말 팝업 창 표시"""
        help_popup = ctk.CTkToplevel(self)
        help_popup.title("💡 도움말 - 학명 검증기 사용 안내") # 이모지 추가
        help_popup.geometry("750x550") # 팝업 크기 조정
        help_popup.grab_set()  # 모달 창으로 설정

        # 레이아웃 설정
        help_popup.grid_columnconfigure(0, weight=1)
        help_popup.grid_rowconfigure(0, weight=1) # 텍스트 상자 영역 확장
        help_popup.grid_rowconfigure(1, weight=0) # 닫기 버튼 영역

        # 스크롤 가능한 텍스트 상자 생성
        help_textbox = ctk.CTkTextbox(
            help_popup,
            wrap="word",
            font=ctk.CTkFont(family="Malgun Gothic", size=12),
            corner_radius=6,
            border_width=1, # 테두리 추가
            padx=10, pady=10
        )
        help_textbox.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="nsew")

        # --- 도움말 내용 파일에서 읽기 (수정) ---
        help_text = "도움말 파일을 불러올 수 없습니다."
        try:
            # 현재 app.py 파일의 디렉토리를 기준으로 상대 경로 설정
            current_dir = os.path.dirname(__file__)
            help_file_path = os.path.join(current_dir, "..", "사용법_팝업.txt")
            
            # UTF-8 인코딩으로 파일 읽기
            with open(help_file_path, 'r', encoding='utf-8') as f:
                help_text = f.read()
        except FileNotFoundError:
            print(f"[Error] Help file not found at: {help_file_path}")
            help_text = f"오류: 도움말 파일({os.path.basename(help_file_path)})을 찾을 수 없습니다."
        except Exception as e:
            print(f"[Error] Failed to read help file: {e}")
            help_text = "오류: 도움말 파일을 읽는 중 문제가 발생했습니다."
        # --- 수정 끝 ---

        # 텍스트 상자에 도움말 내용 삽입 및 읽기 전용 설정
        help_textbox.insert("1.0", help_text)
        help_textbox.configure(state="disabled")

        # 닫기 버튼
        close_button = ctk.CTkButton(
            help_popup,
            text="닫기",
            command=help_popup.destroy,
            width=100,
            font=self.default_bold_font
        )
        close_button.grid(row=1, column=0, padx=20, pady=(0, 20))

    def _clear_file_cache(self, tab_type: str):
        """탭별 파일 캐시 삭제"""
        if tab_type == "marine":
            self.current_marine_names = []
            print(f"[Debug] 해양생물 파일 캐시 삭제됨")
        elif tab_type == "microbe":
            self.current_microbe_names = []
            print(f"[Debug] 미생물 파일 캐시 삭제됨")
        elif tab_type == "col":
            self.current_col_names = []
            print(f"[Debug] COL 파일 캐시 삭제됨")

    def _marine_search(self, input_text: str, tab_name: str = "marine"):
        """해양생물 검색 콜백"""
        print(f"[Debug] _marine_search 호출됨: input_text='{input_text[:50] if input_text else 'None'}', tab_name='{tab_name}'")
        
        # 파일에서 로드된 학명 목록이 있는 경우 우선 사용
        if hasattr(self, 'current_marine_names') and self.current_marine_names:
            print(f"[Debug] 해양생물 탭: 파일에서 로드된 {len(self.current_marine_names)}개 학명 사용")
            self._start_verification_thread(self.current_marine_names)
            # 사용 후 초기화하지 않음 (재사용 가능하도록)
        else:
            # 직접 입력된 텍스트로 검증
            print(f"[Debug] 해양생물 탭: 직접 입력된 텍스트로 검증 시작")
            self._search_species(input_text, tab_name="marine")


def run_app():
    """애플리케이션 실행"""
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    
    app = SpeciesVerifierApp()
    app.mainloop()


if __name__ == "__main__":
    run_app() 