"""
종 검증 애플리케이션 메인 클래스

이 모듈은 종 검증 애플리케이션의
메인 클래스와 애플리케이션 실행 함수를 정의합니다.
"""
import os
import tkinter as tk
import threading
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
        self.tab_view = ctk.CTkTabview(self)
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
        self.status_bar = StatusBar(self, height=30, font=self.default_font)
        self.status_bar.widget.grid(row=2, column=0, padx=10, pady=(5, 5), sticky="nsew")
        self.status_bar.set_cancel_command(self._cancel_operation)
        
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
        if not file_path or not os.path.exists(file_path):
            self.show_centered_message("error", "파일 오류", "파일을 찾을 수 없습니다.")
            return
            
        # 파일 처리 스레드 시작
        threading.Thread(target=self._process_file, args=(file_path,), daemon=True).start()
    
    # --- 미생물 탭 콜백 함수 ---
    def _microbe_search(self, input_text: str, tab_name: str = "microbe"):
        """미생물 검색 콜백"""
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
            if column_id == "#3":  # Taxonomy 컬럼 헤더
                tooltip_text = "분류학적 위치 정보"
            elif column_id == "#4":  # LPSN Link 컬럼 헤더
                tooltip_text = "더블 클릭 시 LPSN 웹사이트 확인"
            elif column_id == "#5":  # Wiki Summary 컬럼 헤더
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
        # 브릿지 모듈의 함수 호출 (result_callback 추가)
        results = perform_verification(
            verification_list_input, 
            self.update_progress, 
            self._update_progress_label,
            result_callback=self._update_single_result # 단일 결과 처리 콜백 전달
        )
        
        # 결과가 콜백으로 실시간 처리되므로, 여기서 최종 결과 표시는 제거
        # if results:
        #     self.after(0, lambda: self._update_results_display(results, "marine"))
        
        # UI 상태 복원 (검증 완료 후)
        self.after(0, lambda: self._reset_status_ui())
        self.after(0, lambda: self._set_ui_state("normal"))
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
        # 브릿지 모듈의 함수 호출 (result_callback 및 context 추가)
        results = perform_microbe_verification(
            microbe_names_list,
            self.update_progress,
            self._update_progress_label,
            result_callback=self._update_single_result, # 단일 결과 처리 콜백 전달
            context=context # context 전달
        )
        
        # UI 상태 복원 (검증 완료 후)
        self.after(0, lambda: self._reset_status_ui()) # 완료 메시지는 microbe_verifier에서 설정
        self.after(0, lambda: self._set_ui_state("normal"))
        if self.microbe_tab:
            self.after(0, lambda: self.microbe_tab.focus_entry())
    
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
        # 통합된 검증 버튼과 파일 찾기 버튼의 상태를 설정
        if self.marine_tab:
            self.marine_tab.verify_button.configure(state=state)
            self.marine_tab.file_browse_button.configure(state=state)
            # verify_button의 활성화 로직은 _update_verify_button_state가 담당하므로
            # state가 'normal'일 때 추가적인 처리는 제거합니다.
        
        if self.microbe_tab:
            self.microbe_tab.verify_button.configure(state=state)
            self.microbe_tab.file_browse_button.configure(state=state)
            # 마찬가지로 state가 'normal'일 때 추가 처리 제거

        # 참고: 각 탭 내부의 _update_verify_button_state 메서드가
        # 텍스트 입력이나 파일 선택 여부에 따라 verify_button의 'normal' 상태를 
        # 세부적으로 관리합니다. 여기서는 전체적인 활성화/비활성화만 제어합니다.
    
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
        
    def _show_context_menu(self, event, tree):
        """트리뷰 항목에 대한 컨텍스트 메뉴를 표시합니다."""
        # 디버그 로그 추가
        print(f"[Debug] _show_context_menu called for tree: {tree}") 
        
        item_id = tree.identify_row(event.y)
        
        # 컨텍스트 메뉴 생성 (항상 생성 시도)
        context_menu = tk.Menu(self, tearoff=0)
        
        # 아이템 관련 메뉴 (아이템 위에서 우클릭했을 때만 추가)
        if item_id:
            tree.selection_set(item_id)
            # 복사 옵션 추가
            context_menu.add_command(label="항목 복사", command=lambda: self._copy_all_info(tree, item_id))
            context_menu.add_command(label="항목 삭제", command=lambda: self._remove_tree_item(tree, item_id))
            values = tree.item(item_id, "values")
            wiki_summary = None
            wiki_title = tree.item(item_id, "text") if item_id else ""
            # ResultTreeview 내부의 실제 tree 위젯과 비교
            if tree == self.result_tree_marine.tree and len(values) > 5:
                wiki_summary = values[5]
            elif tree == self.result_tree_microbe.tree and len(values) > 4:
                wiki_summary = values[4]
            if wiki_summary and wiki_summary != "-":
                context_menu.add_command(
                    label="위키 정보 보기", 
                    command=lambda t=wiki_title, s=wiki_summary: self._show_wiki_summary_popup(t, s)
                )
            context_menu.add_separator()

        # 전체 결과 관련 메뉴
        has_results_in_tree = bool(tree.get_children()) # Treeview 위젯 확인
        has_results_in_list = False # 내부 리스트 확인
        # 어떤 tree인지 확인하여 해당 리스트 검사
        if tree == self.result_tree_marine.tree:
            has_results_in_list = bool(self.current_results_marine)
        elif tree == self.result_tree_microbe.tree:
            has_results_in_list = bool(self.current_results_microbe)
            
        excel_save_state = "normal" if (has_results_in_tree or has_results_in_list) else "disabled"
        
        # 디버그 로그 추가
        print(f"[Debug] Context Menu - Has Results(Tree): {has_results_in_tree}, Has Results(List): {has_results_in_list}, Excel Save State: {excel_save_state}")
        
        # Excel로 저장 옵션 항상 추가 (상태만 변경)
        context_menu.add_command(label="Excel로 저장", 
                                 command=self.export_results_to_excel, 
                                 state=excel_save_state)
        
        # 메뉴 표시 시도
        try:
             print("[Debug] Attempting to popup context menu...") # 디버그 로그 추가
             context_menu.tk_popup(event.x_root, event.y_root)
             print("[Debug] Context menu popup successful.") # 디버그 로그 추가
        except Exception as e:
             print(f"[Error] Failed to popup context menu: {e}") # 오류 로깅 추가
        finally:
             context_menu.grab_release()

    def _copy_all_info(self, tree, item_id):
        """선택한 항목의 모든 정보를 클립보드에 복사합니다."""
        text = tree.item(item_id, "text")
        values = tree.item(item_id, "values")
        
        # 트리뷰에 따라 다른 형식으로 정보 구성
        if tree == self.result_tree_marine:
            info_text = f"입력명: {text}\n"
            if len(values) > 0: info_text += f"학명: {values[0]}\n"
            if len(values) > 1: info_text += f"출처: {values[1]}\n"
            if len(values) > 2: info_text += f"상태: {values[2]}\n"
            if len(values) > 3: info_text += f"WoRMS ID: {values[3]}\n"
            if len(values) > 4: info_text += f"WoRMS 링크: {values[4]}\n"
            if len(values) > 5: info_text += f"종정보: {values[5]}\n"
        else:  # 미생물 트리뷰
            info_text = f"학명: {text}\n"
            if len(values) > 0: info_text += f"유효학명: {values[0]}\n"
            if len(values) > 1: info_text += f"상태: {values[1]}\n"
            if len(values) > 2: info_text += f"분류정보: {values[2]}\n"
            if len(values) > 3: info_text += f"LPSN 링크: {values[3]}\n"
            if len(values) > 4: info_text += f"종정보: {values[4]}\n"
        
        # 클립보드에 복사
        self._copy_to_clipboard(info_text)
        
    def _remove_tree_item(self, tree, item_id):
        """트리뷰에서 항목을 삭제합니다."""
        # 항목 삭제 전 확인
        from tkinter import messagebox
        result = messagebox.askyesno("항목 삭제", "선택한 항목을 정말 삭제하시겠습니까?")
        
        if result:
            # 현재 탭에 따라 적절한 결과 리스트에서도 삭제
            if tree == self.result_tree_marine:
                index = tree.index(item_id)
                if 0 <= index < len(self.current_results_marine):
                    self.current_results_marine.pop(index)
            elif tree == self.result_tree_microbe:
                index = tree.index(item_id)
                if 0 <= index < len(self.current_results_microbe):
                    self.current_results_microbe.pop(index)
                    
            # 트리뷰에서 삭제
            tree.delete(item_id)

    # --- 새로운 메서드: 단일 결과 업데이트 (수정됨) --- 
    # tab_type 인자 추가
    def _update_single_result(self, result: Dict[str, Any], tab_type: str):
        """개별 검증 결과를 받아 GUI에 업데이트 (메인 스레드에서 실행되도록 예약)"""
        if not result:
            return
            
        # 현재 활성 탭 대신 전달받은 tab_type으로 대상 트리 결정
        # current_tab_name = self.tab_view.get() # 이 줄 제거
        target_tree = None

        if tab_type == "marine":
            target_tree = self.result_tree_marine
        elif tab_type == "microbe":
            target_tree = self.result_tree_microbe
        
        if target_tree:
            # 메인 스레드에서 실행되도록 예약
            self.after(0, lambda res=result, tree=target_tree: tree.add_result(res))
        else:
             print(f"[Error] Cannot update single result: Unknown tab_type '{tab_type}'")


def run_app():
    """애플리케이션 실행"""
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    
    app = SpeciesVerifierApp()
    app.mainloop()


if __name__ == "__main__":
    run_app() 