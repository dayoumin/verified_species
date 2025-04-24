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

from species_verifier.config import app_config, ui_config
from species_verifier.gui.components.marine_tab import MarineTabFrame
from species_verifier.gui.components.microbe_tab import MicrobeTabFrame
from species_verifier.gui.components.status_bar import StatusBar
from species_verifier.gui.components.result_view import ResultTreeview
from species_verifier.models.verification_results import MarineVerificationResult, MicrobeVerificationResult

# 브릿지 모듈 임포트
from species_verifier.gui.bridge import (
    perform_verification,
    perform_microbe_verification,
    process_file,
    process_microbe_file,
    KOREAN_NAME_MAPPINGS
)


class SpeciesVerifierApp(ctk.CTk):
    """종 검증 애플리케이션 메인 클래스"""
    
    def __init__(self):
        """초기화"""
        super().__init__()
        
        # 매핑 테이블 로드
        self.korean_name_mappings = KOREAN_NAME_MAPPINGS
        
        # 내부 상태 변수 - active_tab 제거 (CTkTabview가 관리)
        # self.active_tab = "해양생물" 
        self.current_results_marine = []  # 해양생물 탭 결과
        self.current_results_microbe = []  # 미생물 탭 결과
        self.is_verifying = False # 현재 검증 작업 진행 여부 플래그
        self.result_queue = queue.Queue() # 결과 처리를 위한 큐
        
        # 디버그 로그: 초기 self ID 및 메인 스레드 ID 기록
        self.main_thread_id = threading.get_ident()
        print(f"[Debug Init] Initial self ID: {id(self)}, Type: {type(self)}, Main Thread ID: {self.main_thread_id}")
        
        # 플레이스홀더 텍스트 설정
        self.placeholder_focused = "예: Homo sapiens, Gadus morhua"
        self.placeholder_unfocused = "여러 학명은 콤마로 구분 (예: Paralichthys olivaceus, Anguilla japonica)"
        
        # 기본 설정
        self.title("Species Verifier")
        self.geometry("900x700")
        
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
        # --- 헤더 프레임 (이미지 공간) ---
        self.header_frame = ctk.CTkFrame(self, height=60, corner_radius=0)
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        self.header_frame.grid_columnconfigure(0, weight=1) # 이미지를 가운데 정렬하기 위해

        # 이미지 로드 및 배치
        try:
            # 이미지 파일 경로 설정 (실제 경로로 수정)
            image_path = os.path.join(os.path.dirname(__file__), "..", "assets", "images", "header_logo.png")
            if os.path.exists(image_path):
                # PIL로 이미지 열기
                pil_image = Image.open(image_path)
                # CTkImage 생성 (크기 조절 가능, 예: height=50)
                ctk_image = CTkImage(light_image=pil_image, dark_image=pil_image, size=(pil_image.width * 50 // pil_image.height, 50))
                
                # 이미지를 표시할 라벨 생성
                image_label = ctk.CTkLabel(self.header_frame, image=ctk_image, text="")
                # 헤더 프레임 중앙에 배치
                image_label.grid(row=0, column=0, padx=10, pady=5)
            else:
                print(f"[Warning] Header image not found at: {image_path}")
                # 이미지가 없을 경우 텍스트 라벨 표시 (수정: 텍스트 및 폰트)
                fallback_label = ctk.CTkLabel(self.header_frame, text="국립수산과학원 학명검증기", font=self.header_text_font)
                fallback_label.grid(row=0, column=0, padx=10, pady=10)
        except Exception as e:
            print(f"[Error] Failed to load header image: {e}")
            # 오류 발생 시 텍스트 라벨 표시 (수정: 텍스트 및 폰트)
            fallback_label = ctk.CTkLabel(self.header_frame, text="국립수산과학원 학명검증기", font=self.header_text_font)
            fallback_label.grid(row=0, column=0, padx=10, pady=10)

        # --- CTkTabview 생성 (1행으로 이동) ---
        self.tab_view = ctk.CTkTabview(self, command=self._on_tab_change)
        self.tab_view.grid(row=1, column=0, padx=10, pady=(5, 0), sticky="nsew") # pady 상단 추가

        # 탭 추가
        self.tab_view.add("해양생물")
        self.tab_view.add("미생물 (LPSN)")

        # --- 해양생물 탭 컨텐츠 배치 (기존과 동일, 부모만 확인) ---
        marine_tab_content = self.tab_view.tab("해양생물")
        marine_tab_content.grid_columnconfigure(0, weight=1)
        marine_tab_content.grid_rowconfigure(0, weight=0)
        marine_tab_content.grid_rowconfigure(1, weight=0)
        marine_tab_content.grid_rowconfigure(2, weight=1)
        
        self.marine_tab = MarineTabFrame(
            marine_tab_content, # 부모를 해당 탭으로 설정
            font=self.default_font,
            bold_font=self.default_bold_font,
            placeholder_text=self.placeholder_focused,
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
            placeholder_text="예: Escherichia coli",
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
        
        # --- 상태 바 생성 (2행으로 이동) ---
        self.status_bar = StatusBar(
            self,
            height=30,
            font=self.default_font,
            save_command=self.export_results_to_excel # 저장 명령 연결
        )
        self.status_bar.widget.grid(row=2, column=0, padx=10, pady=(5, 5), sticky="nsew")
        self.status_bar.set_cancel_command(self._cancel_operation) # 취소 명령 설정
        # StatusBar 초기 상태 설정 (저장 버튼 숨김)
        self.status_bar.set_ready(status_text="입력 대기 중", show_save_button=False)
        
        # --- 푸터 생성 (3행으로 이동) ---
        self.footer_frame = ctk.CTkFrame(self, height=20, corner_radius=0)
        self.footer_frame.grid(row=3, column=0, padx=0, pady=(2, 0), sticky="nsew")
        self.footer_frame.grid_columnconfigure(0, weight=1)
        
        self.footer_label = ctk.CTkLabel(
            self.footer_frame,
            text="© 2025 국립수산과학원 수산생명자원 책임기관",
            font=self.footer_font,
            text_color=("gray50", "gray60")
        )
        self.footer_label.grid(row=0, column=0, pady=(0, 2))
    
    def _setup_callbacks(self):
        """콜백 설정"""
        # 해양생물 탭 콜백
        self.marine_tab.set_callbacks(
            on_search=self._marine_search,
            on_file_browse=self._marine_file_browse,
            on_file_search=self._marine_file_search
        )
        
        # 미생물 탭 콜백
        self.microbe_tab.set_callbacks(
            on_search=self._microbe_search,
            on_file_browse=self._microbe_file_browse,
            on_file_search=self._microbe_file_search
        )
    
    # --- 해양생물 탭 콜백 함수 ---
    def _marine_search(self, input_text: str, tab_name: str = "marine"):
        """해양생물 검색 콜백"""
        if self.is_verifying:
            self.show_centered_message("warning", "작업 중", "현재 다른 검증 작업이 진행 중입니다. 잠시 후 다시 시도해주세요.")
            return
        
        if not input_text:
            return
        
        # 입력 문자열 처리
        input_text = input_text.strip()
        # 여러 학명이 콤마로 구분되어 있는지 확인
        if "," in input_text:
            # 콤마로 구분된 목록 처리
            names_list = [name.strip() for name in input_text.split(",") if name.strip()]
            if names_list:
                self._start_verification_thread(names_list)
        else:
            # 단일 학명 또는 한글명 처리
            if any(self._is_korean(char) for char in input_text):
                # 한글명인 경우 학명 매핑 확인
                scientific_name = self._find_scientific_name_from_korean_name(input_text)
                if scientific_name:
                    self._start_verification_thread([(input_text, scientific_name)])
                else:
                    self.show_centered_message("warning", "한글명 매핑 실패", 
                                               f"'{input_text}'에 해당하는 학명을 찾을 수 없습니다.")
            else:
                # 학명인 경우 바로 검증
                self._start_verification_thread([input_text])
    
    def _marine_file_browse(self) -> Optional[str]:
        """해양생물 파일 선택 콜백"""
        file_path = filedialog.askopenfilename(
            title="학명 파일 선택",
            filetypes=(("CSV 파일", "*.csv"), ("Excel 파일", "*.xlsx"), ("모든 파일", "*.*"))
        )
        return file_path if file_path else None
    
    def _marine_file_search(self, file_path: str, tab_name: str = "marine"):
        """해양생물 파일 검색 콜백"""
        if self.is_verifying:
            self.show_centered_message("warning", "작업 중", "현재 다른 검증 작업이 진행 중입니다. 잠시 후 다시 시도해주세요.")
            return
            
        if not file_path or not os.path.exists(file_path):
            self.show_centered_message("error", "파일 오류", "파일을 찾을 수 없습니다.")
            return
            
        # 파일 처리 스레드 시작
        threading.Thread(target=self._process_file, args=(file_path,), daemon=True).start()
    
    # --- 미생물 탭 콜백 함수 ---
    def _microbe_search(self, input_text: str, tab_name: str = "microbe"):
        """미생물 검색 콜백"""
        if self.is_verifying:
            self.show_centered_message("warning", "작업 중", "현재 다른 검증 작업이 진행 중입니다. 잠시 후 다시 시도해주세요.")
            return
            
        if not input_text:
            return
            
        # 입력 문자열 처리
        input_text = input_text.strip()
        # 여러 학명이 콤마로 구분되어 있는지 확인
        names_list = [name.strip() for name in input_text.split(",") if name.strip()]
        
        if names_list:
            # 직접 입력 컨텍스트(학명 리스트) 전달
            self._start_microbe_verification_thread(names_list, context=names_list) 
        # else: 단일 학명도 리스트로 처리되므로 별도 분기 불필요
    
    def _microbe_file_browse(self) -> Optional[str]:
        """미생물 파일 선택 콜백"""
        file_path = filedialog.askopenfilename(
            title="미생물 학명 파일 선택",
            filetypes=(("CSV 파일", "*.csv"), ("Excel 파일", "*.xlsx"), ("모든 파일", "*.*"))
        )
        return file_path if file_path else None
    
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
        # 컨텍스트 메뉴 표시
        tree = event.widget
        self._show_context_menu(event, tree)
    
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
        # 컨텍스트 메뉴 표시
        tree = event.widget
        self._show_context_menu(event, tree)
    
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
            # --- 디버깅 로그 추가 ---
            print(f"[Debug Tooltip] Hovering header region. Identified column_id: {column_id}") 
            
            # --- 수정: 컬럼 ID와 툴팁 매핑 확인 및 조정 ---
            # Treeview 컬럼 인덱스는 #0부터 시작하지만, identify_column은 #1부터 반환하는 경향이 있음.
            # 실제 컬럼: #1(학명), #2(검증), #3(상태), #4(분류), #5(LPSN 링크), #6(위키)
            # 따라서, 분류=#4, LPSN링크=#5, 위키=#6 으로 추정하고 조건문 수정
            if column_id == "#4":  # 분류 컬럼 헤더 (기존 #3)
                tooltip_text = "분류학적 위치 정보"
            elif column_id == "#5":  # LPSN Link 컬럼 헤더 (기존 #4)
                tooltip_text = "더블 클릭 시 LPSN 웹사이트 확인"
            elif column_id == "#6":  # Wiki Summary 컬럼 헤더 (기존 #5)
                tooltip_text = "더블 클릭 시 위키백과 요약 팝업창 확인"
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
    def _is_korean(self, char: str) -> bool:
        """한글 문자 여부 확인"""
        return ord('가') <= ord(char) <= ord('힣')
    
    def _find_scientific_name_from_korean_name(self, korean_name: str) -> Optional[str]:
        """한글명으로 학명 찾기"""
        if korean_name in self.korean_name_mappings:
            return self.korean_name_mappings[korean_name]
        return None
    
    def _start_verification_thread(self, verification_list: Union[List[str], List[Tuple[str, str]]]):
        """해양생물 검증 스레드 시작"""
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
    
    def _perform_verification(self, verification_list_input: Union[List[str], List[Tuple[str, str]]]):
        """해양생물 검증 수행 (백그라운드 스레드에서 실행)"""
        # 브릿지 모듈의 함수 호출 (result_callback 대신 queue의 put 메서드 전달)
        results = perform_verification(
            verification_list_input, 
            self.update_progress, 
            self._update_progress_label,
            # 큐에 (결과, 타입) 튜플을 넣는 함수 전달
            result_callback=lambda r, t: self.result_queue.put((r, t)) 
        )
        
        # 백그라운드 작업 완료 후 플래그 해제 및 UI 복원
        # self.after(0, lambda: self._update_results_display(results, "marine")) # 전체 결과 표시는 제거 (개별 처리됨)
        self.after(0, lambda: self._reset_status_ui())
        self.after(0, lambda: self._set_ui_state("normal"))
        self.after(0, lambda: setattr(self, 'is_verifying', False)) # 검증 완료 플래그 해제
        # 완료 후 포커스 설정은 유지
        if self.marine_tab:
            self.after(0, lambda: self.marine_tab.focus_entry())

    def _start_microbe_verification_thread(self, microbe_names_list: List[str], context: Union[List[str], str, None] = None):
        """미생물 검증 스레드 시작"""
        # 진행 UI 표시 (초기 메시지 개선)
        initial_msg = "미생물 검증 준비 중..."
        if isinstance(context, str): # 파일 경로인 경우
            initial_msg = f"파일 '{os.path.basename(context)}' 검증 준비 중..."
        elif isinstance(context, list): # 직접 입력인 경우
            initial_msg = f"입력된 {len(context)}개 학명 검증 준비 중..."
            
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
    
    def _perform_microbe_verification(self, microbe_names_list: List[str], context: Union[List[str], str, None] = None):
        """미생물 검증 수행 (백그라운드 스레드에서 실행)"""
        try:
            # 브릿지 모듈의 함수 호출 (result_callback 대신 queue의 put 메서드 전달)
            results = perform_microbe_verification(
                microbe_names_list,
                self.update_progress,
                self._update_progress_label,
                 # 큐에 (결과, 타입) 튜플을 넣는 함수 전달
                result_callback=lambda r, t: self.result_queue.put((r, t)),
                context=context # context 전달
            )
            # 여기서 results 변수는 사용되지 않지만, 호출은 필요합니다.
            # 결과 처리는 result_callback을 통해 큐로 전달됩니다.
        except Exception as e:
            print(f"[Error _perform_microbe_verification] Error during verification call: {e}")
            traceback.print_exc()
            # 오류 발생 시에도 UI 상태는 finally에서 복구

        finally:
            # 최종 진행률 및 상태 레이블 업데이트
            self.after(0, lambda: self.update_progress(1.0)) # 진행률 100%
            self.after(10, lambda: self._update_progress_label("검증 완료"))

            # 프로그레스바 정지 (수정: self.status_bar 사용)
            if hasattr(self, 'status_bar') and hasattr(self.status_bar, 'progressbar'):
                self.after(50, lambda: self.status_bar.progressbar.stop())
                self.after(50, lambda: self.status_bar.progressbar.configure(mode='determinate')) # 확정 모드로 설정

            # UI 상태를 'normal'로 설정하여 상태바/버튼 정리 (100ms 지연 후)
            self.after(100, lambda: self._set_ui_state("normal"))

            # --- is_verifying 플래그 리셋 추가 ---
            self.after(20, lambda: setattr(self, 'is_verifying', False)) # 검증 완료 플래그 해제

            # 입력창 초기화 및 포커스 설정 (수정: self.microbe_tab 사용 및 delete 인덱스 수정)
            if hasattr(self, 'microbe_tab') and hasattr(self.microbe_tab, 'entry'):
                self.after(600, lambda: self.microbe_tab.entry.delete("1.0", tk.END))
            if hasattr(self, 'microbe_tab') and hasattr(self.microbe_tab, 'focus_entry'):
                 self.after(650, self.microbe_tab.focus_entry) # focus_entry 메서드 호출

    def _process_file(self, file_path: str):
        """해양생물 파일 처리"""
        # 브릿지 모듈의 함수 호출
        names_list = process_file(file_path)
        
        if names_list:
            self._start_verification_thread(names_list)
        else:
            self.after(0, lambda: self.show_centered_message(
                "error", "파일 처리 오류", "파일에서 유효한 학명을 찾을 수 없습니다."
            ))
            self.after(0, lambda: self._reset_status_ui())
            self.after(0, lambda: self._set_ui_state("normal"))
    
    def _process_microbe_file(self, file_path: str):
        """미생물 파일 처리"""
        # 브릿지 모듈의 함수 호출
        names_list = process_microbe_file(file_path)
        
        if names_list:
            # 파일 경로를 context로 전달하며 검증 스레드 시작
            self._start_microbe_verification_thread(names_list, context=file_path) 
        else:
            self.after(0, lambda: self.show_centered_message(
                "error", "파일 처리 오류", "파일에서 유효한 학명을 찾을 수 없습니다."
            ))
            self.after(0, lambda: self._reset_status_ui())
            self.after(0, lambda: self._set_ui_state("normal"))
    
    def _update_results_display(self, results_list: List[Dict[str, Any]], tab_name: str = None, clear_first: bool = False):
        """결과 표시 업데이트"""
        if not results_list:
            return
        
        # 표시할 탭 결정 (CTkTabview의 현재 탭 사용)
        current_tab_name = self.tab_view.get() # 현재 활성화된 탭 이름 가져오기
            
        # 결과를 적절한 Treeview에 표시
        if current_tab_name == "해양생물":
            self.result_tree_marine.add_results(results_list, clear_first)
            self.current_results_marine.extend(results_list)
        elif current_tab_name == "미생물 (LPSN)":
            self.result_tree_microbe.add_results(results_list, clear_first)
            self.current_results_microbe.extend(results_list)
    
    def _update_progress_label(self, text: str):
        """진행 상태 레이블 업데이트"""
        self.status_bar.set_status(text)
    
    def update_progress(self, progress_value: float):
        """진행 상태 업데이트"""
        self.status_bar.set_progress(progress_value)
    
    def _show_progress_ui(self, initial_text: str = ""):
        """진행 UI 표시"""
        self.status_bar.set_busy(initial_text)
    
    def _reset_status_ui(self, reset_file_label: bool = False):
        """상태 UI 초기화"""
        self.status_bar.set_ready()
        
        if reset_file_label:
            self.marine_tab.set_selected_file(None)
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
         if not hasattr(self, 'tab_view'): # tab_view 로드 전 호출 방지
              print("[Debug Check Results] tab_view not found.")
              return False
         current_tab_name = self.tab_view.get()
         print(f"[Debug Check Results] Checking results for tab: {current_tab_name}")

         if current_tab_name == "해양생물":
             results_list = self.current_results_marine if hasattr(self, 'current_results_marine') else None
             list_exists = results_list is not None
             list_not_empty = bool(results_list)
             print(f"[Debug Check Results - Marine] List exists: {list_exists}, List not empty: {list_not_empty}, List content (first 5): {results_list[:5] if results_list else 'None or Empty'}")
             return list_exists and list_not_empty
         elif current_tab_name == "미생물 (LPSN)":
             results_list = self.current_results_microbe if hasattr(self, 'current_results_microbe') else None
             list_exists = results_list is not None
             list_not_empty = bool(results_list)
             print(f"[Debug Check Results - Microbe] List exists: {list_exists}, List not empty: {list_not_empty}, List content (first 5): {results_list[:5] if results_list else 'None or Empty'}")
             return list_exists and list_not_empty

         print(f"[Debug Check Results] Unknown tab name: {current_tab_name}")
         return False

    def _process_result_queue(self):
        """결과 큐를 주기적으로 확인하고 GUI를 업데이트합니다."""
        try:
            # 큐에서 모든 사용 가능한 항목 가져오기 (블로킹 없이)
            while True:
                 result_data = self.result_queue.get_nowait()
                 # 디버그 로그: 큐 처리 시점의 self 및 스레드 확인
                 current_thread_id = threading.get_ident()
                 print(f"[Debug Queue Process] Current self ID: {id(self)}, Type: {type(self)}, Current Thread ID: {current_thread_id}, Is Main Thread: {current_thread_id == self.main_thread_id}")
                 
                 # 추가 디버그: 다른 속성 접근 및 hasattr 확인
                 try:
                     print(f"[Debug Queue Process] Accessing self.title(): {self.title()}")
                     print(f"[Debug Queue Process] hasattr _update_single_result: {hasattr(self, '_update_single_result')}")
                 except Exception as e_debug:
                     print(f"[Error Debug] Error during self check: {e_debug}")
                     
                 # 큐에서 가져온 데이터는 (결과 딕셔너리, 탭 타입 문자열) 튜플이어야 함
                 if isinstance(result_data, tuple) and len(result_data) == 2:
                      result_dict, tab_type = result_data
                      # _process_result_queue는 이미 메인 스레드에서 실행되므로 직접 호출 시도
                      self._update_single_result(result_dict, tab_type)
                 else:
                      print(f"[Warning] Invalid data format in queue: {result_data}")
                 # task_done은 if/else와 같은 레벨이어야 함
                 self.result_queue.task_done() 

        except queue.Empty:
            # 큐가 비어있으면 아무것도 하지 않음
            pass
        except Exception as e:
             print(f"[Error] Error processing result queue: {e}")
             traceback.print_exc()
        finally:
            # 100ms 후에 다시 큐 확인 예약
            self.after(100, self._process_result_queue)

    def _cancel_operation(self):
        """작업 취소"""
        # 구현 예정: 스레드 종료 등
        self._reset_status_ui()
        self._set_ui_state("normal")
    
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
        """위키백과 요약 내용을 팝업 창으로 표시합니다."""
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
        self.show_centered_message("info", "복사 완료", "내용이 클립보드에 복사되었습니다.")
        
    def _show_context_menu(self, event, tree_type):
        """결과 트리뷰에서 마우스 오른쪽 버튼 클릭 시 컨텍스트 메뉴를 표시합니다."""
        context_menu = tk.Menu(self, tearoff=0)
        item_id = None # 클릭된 항목 ID

        if tree_type == 'marine':
            tree = self.result_tree_marine.tree
            current_results = self.current_results_marine
        elif tree_type == 'microbe':
            tree = self.result_tree_microbe.tree
            current_results = self.current_results_microbe
        else:
            return # 알 수 없는 트리 타입

        # 클릭 위치에 항목이 있는지 확인
        try:
            item_id = tree.identify_row(event.y)
        except tk.TclError: # 빈 공간 클릭 시 에러 방지
            item_id = None
        
        if item_id:
            tree.selection_set(item_id) # 클릭된 항목 선택
            # 개별 항목 복사 메뉴 추가
            context_menu.add_command(label="항목 복사", command=lambda: self._copy_all_info(tree, item_id))
            context_menu.add_separator() # 구분선 추가
        
        # 결과가 있을 때만 Excel 저장 메뉴 활성화
        # current_results가 비어있어도 Treeview에 직접 결과가 있을 수 있으므로 확인
        has_results = bool(current_results or tree.get_children())
        excel_export_state = tk.NORMAL if has_results else tk.DISABLED
        context_menu.add_command(label="Excel로 저장", command=self.export_results_to_excel, state=excel_export_state)

        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
             context_menu.grab_release()

    def export_results_to_excel(self):
        """현재 활성화된 탭의 결과를 Excel 파일로 저장합니다."""
        current_tab_name = self.tab_view.get()
        results_to_export = []
        columns_info = []
        default_filename = "verification_results.xlsx"

        if current_tab_name == "해양생물":
            results_to_export = self.current_results_marine
            tree = self.result_tree_marine.tree
            columns_info = [
                ("input_name", "입력명"), # Treeview의 text 컬럼
                ("mapped_name", "학명"),
                ("verified", "검증"),
                ("worms_status", "WoRMS 상태"),
                ("worms_id", "WoRMS ID"),
                ("worms_url", "WoRMS URL"),
                ("wiki_summary", "위키백과 요약")
            ]
            default_filename = "marine_verification_results.xlsx"
        elif current_tab_name == "미생물 (LPSN)":
            results_to_export = self.current_results_microbe
            tree = self.result_tree_microbe.tree
            columns_info = [
                ("input_name", "입력명"), # Treeview의 text 컬럼
                ("valid_name", "유효 학명"), # Treeview 컬럼 #1
                ("verified", "검증"), # Treeview 컬럼 #2
                ("status", "상태"), # Treeview 컬럼 #3
                ("taxonomy", "분류"), # Treeview 컬럼 #4
                ("lpsn_link", "LPSN 링크"), # Treeview 컬럼 #5
                ("wiki_summary", "위키백과 요약") # Treeview 컬럼 #6
            ]
            default_filename = "microbe_verification_results.xlsx"
        else:
            self.show_centered_message("warning", "내보내기 오류", "결과를 내보낼 활성 탭을 인식할 수 없습니다.")
            return

        if not results_to_export:
            # Treeview에 직접 결과가 있는지 확인 (current_results 리스트가 비었을 경우)
            if not tree.get_children():
                self.show_centered_message("info", "내보내기", "내보낼 결과가 없습니다.")
                return
            else:
                 # Treeview에서 직접 데이터 읽기 (대체 로직)
                 print("[Warning] Exporting directly from Treeview as current_results is empty.")
                 results_to_export = []
                 for item_id in tree.get_children():
                      item_data = {"input_name": tree.item(item_id, "text")} # 첫 컬럼(입력명) 추가
                      values = tree.item(item_id, "values")
                      # 컬럼 정보와 values 매칭
                      for i, (key, _) in enumerate(columns_info[1:]): # 첫 컬럼 제외하고 매칭
                           if i < len(values):
                                item_data[key] = values[i]
                           else:
                                item_data[key] = "-" # 값이 없으면 기본값
                      results_to_export.append(item_data)
                 if not results_to_export:
                     self.show_centered_message("info", "내보내기", "Treeview에서 결과를 읽을 수 없습니다.")
                     return

        # 파일 저장 경로 선택
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel 파일", "*.xlsx")],
            title="결과 저장 위치 선택",
            initialfile=default_filename
        )

        if not file_path:
            return # 사용자가 취소

        try:
            # pandas DataFrame 생성
            # 컬럼 순서를 columns_info 기준으로 지정
            df_columns = [col_key for col_key, _ in columns_info]
            df = pd.DataFrame(results_to_export, columns=df_columns) 
            
            # DataFrame 컬럼 이름을 한글 헤더로 변경
            df.rename(columns={col_key: col_header for col_key, col_header in columns_info}, inplace=True)

            # Excel 파일로 저장
            df.to_excel(file_path, index=False)
            
            self.show_centered_message("info", "저장 완료", f"결과가 성공적으로 저장되었습니다.\n 경로: {file_path}")

        except Exception as e:
            import traceback
            print(f"[Error] Excel 저장 오류: {e}")
            print(traceback.format_exc())
            self.show_centered_message("error", "저장 실패", f"결과를 저장하는 중 오류가 발생했습니다.\n 오류: {e}")

    def _copy_all_info(self, tree, item_id):
        """선택한 항목의 모든 정보를 클립보드에 복사합니다."""
        try:
            # 트리 타입 확인 (클래스 이름으로 구분)
            tree_type = 'marine' if isinstance(tree.master, self.result_tree_marine.__class__) else 'microbe'

            # 헤더 정보 가져오기
            if tree_type == 'marine':
                headers = ["입력명"] + [tree.heading(f"#{i}")['text'] for i in range(1, len(tree['columns']) + 1)]
                # 컬럼 키 정보 (Excel 저장 시 사용했던 정보 활용 가능)
                columns_info = [
                    ("input_name", "입력명"), ("mapped_name", "학명"), ("verified", "검증"),
                    ("worms_status", "WoRMS 상태"), ("worms_id", "WoRMS ID"), 
                    ("worms_url", "WoRMS URL"), ("wiki_summary", "위키백과 요약")
                ]
            else: # microbe
                headers = ["입력명"] + [tree.heading(f"#{i}")['text'] for i in range(1, len(tree['columns']) + 1)]
                columns_info = [
                    ("input_name", "입력명"), ("valid_name", "유효 학명"), ("verified", "검증"),
                    ("status", "상태"), ("taxonomy", "분류"), ("lpsn_link", "LPSN 링크"),
                    ("wiki_summary", "위키백과 요약")
                ]

            item = tree.item(item_id)
            values = [item['text']] + list(item['values']) # 첫 번째 컬럼(text)과 나머지 컬럼 값들

            # 헤더와 값 매칭
            info_lines = []
            for i, header in enumerate(headers):
                value = values[i] if i < len(values) else ""
                # 위키 요약은 너무 길 수 있으므로 처음 몇 자만 포함하거나 제외 고려
                if columns_info[i][0] == "wiki_summary" and len(str(value)) > 100: 
                     value = str(value)[:100] + "..." # 예시: 100자 초과 시 축약
                elif columns_info[i][0] in ["worms_url", "lpsn_link"] and not value:
                     value = "N/A" # 링크 없는 경우
                
                info_lines.append(f"{header}: {value}")

            copy_text = "\\n".join(info_lines)
            self._copy_to_clipboard(copy_text)
            
            # 상태 표시줄에 간단한 메시지 표시
            self.status_bar.set_status(f"'{item['text']}' 정보가 클립보드에 복사되었습니다.")
            self.after(3000, self._reset_status_ui) # 3초 후 상태 초기화

        except Exception as e:
            print(f"[Error] 정보 복사 중 오류: {e}")
            self.status_bar.set_status("정보 복사 실패.")
            self.after(3000, self._reset_status_ui)

    # --- 새로운 메서드: 단일 결과 업데이트 --- 
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
        
        if target_tree:
            # ResultTreeview의 add_result 메서드 호출 (결과 추가 및 UI 업데이트)
            target_tree.add_result(result) 
            # 내부 결과 리스트에도 추가 (선택적, Excel 저장 등을 위해 필요할 수 있음)
            if target_results_list is not None:
                 target_results_list.append(result)
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

        # 현재 탭의 결과 유무 확인
        results_exist = self._check_results_exist()
        print(f"[Debug Tab Change] Results exist in '{current_tab_name}': {results_exist}")

        # 상태 바 업데이트 (현재 탭 상태에 맞게)
        # '검증 완료' 또는 '입력 대기 중' 메시지와 함께 저장 버튼 상태 업데이트
        status_text = "검증 완료" if results_exist else "입력 대기 중"
        if hasattr(self, 'status_bar'):
            self.status_bar.set_ready(status_text=status_text, show_save_button=results_exist)


def run_app():
    """애플리케이션 실행"""
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    
    app = SpeciesVerifierApp()
    app.mainloop()


if __name__ == "__main__":
    run_app() 