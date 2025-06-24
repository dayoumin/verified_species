"""
결과 표시 컴포넌트

이 모듈은 검증 결과를 표시하기 위한 TreeView 컴포넌트를 정의합니다.
"""
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from typing import Dict, Any, List, Optional, Callable, Tuple

from .base import BaseResultView
from species_verifier.models.verification_results import BaseVerificationResult, MarineVerificationResult, MicrobeVerificationResult


class ResultTreeview(BaseResultView):
    """검증 결과를 표시하는 Treeview 컴포넌트"""
    
    def __init__(self, parent: Any, tab_type: str = "marine", **kwargs):
        """
        초기화
        
        Args:
            parent: 부모 위젯
            tab_type: 탭 유형 ("marine", "microbe", 또는 "col")
            **kwargs: 추가 인자
        """
        self.tab_type = tab_type
        self.tree = None
        self.scrollbar_y = None
        self.scrollbar_x = None
        self.on_double_click = kwargs.pop('on_double_click', None)
        self.on_right_click_handler = kwargs.pop('on_right_click', None)
        self.on_motion = kwargs.pop('on_motion', None)
        super().__init__(parent, **kwargs)
        # 디버그 로그 추가
        print(f"[Debug ResultView] ResultTreeview initialized for tab: {self.tab_type}, on_right_click_handler exists: {callable(self.on_right_click_handler)}")
    
    def _create_widgets(self, **kwargs):
        """위젯 생성"""
        # self.widget 생성 (CTkFrame)
        self.widget = ctk.CTkFrame(self.parent)

        # self.widget 내부 레이아웃을 grid로 설정
        self.widget.grid_rowconfigure(0, weight=1)  # Treeview가 차지할 행
        self.widget.grid_columnconfigure(0, weight=1) # Treeview가 차지할 열

        # 스크롤바 생성
        self.scrollbar_y = ctk.CTkScrollbar(self.widget, orientation="vertical")
        self.scrollbar_x = ctk.CTkScrollbar(self.widget, orientation="horizontal")
        
        # Treeview 생성 (기존 코드 유지, 부모만 self.widget으로)
        columns = []
        if self.tab_type == "marine":
            columns = ("mapped_name", "verified", "worms_status", "worms_id", "worms_url", "summary")
        elif self.tab_type == "microbe":
            columns = ("valid_name", "verified", "status", "taxonomy", "link", "summary")
        elif self.tab_type == "col":
            columns = ("valid_name", "verified", "col_status", "col_id", "col_url", "summary")
            
        self.tree = ttk.Treeview(self.widget, columns=columns, show="headings", 
                                 yscrollcommand=self.scrollbar_y.set, 
                                 xscrollcommand=self.scrollbar_x.set)
        
        # --- 위젯 배치: grid 사용 --- 
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.scrollbar_y.grid(row=0, column=1, sticky="ns")
        self.scrollbar_x.grid(row=1, column=0, sticky="ew")

        # 스크롤바 연결
        self.scrollbar_y.configure(command=self.tree.yview)
        self.scrollbar_x.configure(command=self.tree.xview)
        
        # 열 설정 (탭 유형에 따라 다름)
        if self.tab_type == "marine":
            # 열 헤더 설정
            self.tree.heading("mapped_name", text="학명")
            self.tree.heading("verified", text="검증")
            self.tree.heading("worms_status", text="WoRMS 상태")
            self.tree.heading("worms_id", text="WoRMS ID")
            self.tree.heading("worms_url", text="WoRMS URL")
            self.tree.heading("summary", text="심층분석 결과")
            
            # 열 너비 설정
            self.tree.column("mapped_name", width=150, minwidth=100)
            self.tree.column("verified", width=60, minwidth=50, anchor='center')
            self.tree.column("worms_status", width=120, minwidth=80, anchor='center')
            self.tree.column("worms_id", width=80, minwidth=50, anchor='center')
            self.tree.column("worms_url", width=120, minwidth=80)
            self.tree.column("summary", width=300, minwidth=150)
            
        elif self.tab_type == "microbe":
            # 열 헤더 설정
            self.tree.heading("valid_name", text="학명")
            self.tree.heading("verified", text="검증")
            self.tree.heading("status", text="상태")
            self.tree.heading("taxonomy", text="분류")
            self.tree.heading("link", text="LPSN 링크")
            self.tree.heading("summary", text="심층분석 결과")
            
            # 열 너비 설정
            self.tree.column("valid_name", width=150, minwidth=100)
            self.tree.column("verified", width=60, minwidth=50, anchor='center')
            self.tree.column("status", width=120, minwidth=80, anchor='center')
            self.tree.column("taxonomy", width=250, minwidth=150)
            self.tree.column("link", width=120, minwidth=80)
            self.tree.column("summary", width=300, minwidth=150)
        
        elif self.tab_type == "col":
            # 열 헤더 설정
            self.tree.heading("valid_name", text="학명")
            self.tree.heading("verified", text="검증")
            self.tree.heading("col_status", text="COL 상태")
            self.tree.heading("col_id", text="COL ID")
            self.tree.heading("col_url", text="COL URL")
            self.tree.heading("summary", text="심층분석 결과")
            
            # 열 너비 설정
            self.tree.column("valid_name", width=150, minwidth=100)
            self.tree.column("verified", width=60, minwidth=50, anchor='center')
            self.tree.column("col_status", width=120, minwidth=80, anchor='center')
            self.tree.column("col_id", width=100, minwidth=50, anchor='center')
            self.tree.column("col_url", width=120, minwidth=80)
            self.tree.column("summary", width=300, minwidth=150)
        
        # 태그 설정
        self.tree.tag_configure('verified', background='#e6ffe6')
        self.tree.tag_configure('unverified', background='#fff0f0')
        self.tree.tag_configure('caution', background='#ffffd0')
        
        # 이벤트 바인딩
        if self.on_double_click:
            self.tree.bind("<Double-1>", self.on_double_click)
            print(f"[Debug ResultView] Bound <Double-1> for {self.tab_type}")
        self.tree.bind("<Button-3>", self._handle_right_click)
        print(f"[Debug ResultView] Bound <Button-3> (Right Click) to internal handler for {self.tab_type}")
        if self.on_motion:
            self.tree.bind("<Motion>", self.on_motion)
            print(f"[Debug ResultView] Bound <Motion> for {self.tab_type}")
    
    def _handle_right_click(self, event):
        """Treeview 우클릭 이벤트를 처리하고 외부 콜백을 호출합니다."""
        print(f"[Debug ResultView] _handle_right_click triggered for tab: {self.tab_type}")
        if callable(self.on_right_click_handler):
            print(f"[Debug ResultView] Calling external on_right_click_handler...")
            self.on_right_click_handler(event)
        else:
            print(f"[Warning ResultView] No valid on_right_click_handler found for tab: {self.tab_type}")
    
    def _get_bg_color(self) -> str:
        """배경색 가져오기"""
        return self._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["fg_color"])
    
    def _get_text_color(self) -> str:
        """텍스트 색상 가져오기"""
        return self._apply_appearance_mode(ctk.ThemeManager.theme["CTkLabel"]["text_color"])
    
    def _get_selected_color(self) -> str:
        """선택 배경색 가져오기"""
        return self._apply_appearance_mode(ctk.ThemeManager.theme["CTkButton"]["fg_color"])
    
    def _apply_appearance_mode(self, color_tuple: Tuple[str, str]) -> str:
        """테마에 맞는 색상 선택"""
        appearance_mode = ctk.get_appearance_mode().lower()
        return color_tuple[1] if appearance_mode == "dark" else color_tuple[0]
    
    def clear(self):
        """결과 목록 초기화"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.results = []
    
    def _display_result(self, result: Any, insert_at_index=tk.END):
        """
        결과 표시
        
        Args:
            result: 표시할 결과 (딕셔너리 또는 결과 모델)
            insert_at_index: 삽입 위치 (기본값: 맨 끝)
        """
        if self.tab_type == "marine":
            self._display_marine_result(result, insert_at_index)
        elif self.tab_type == "microbe":
            self._display_microbe_result(result, insert_at_index)
        elif self.tab_type == "col":
            self._display_col_result(result, insert_at_index)
    
    def _display_marine_result(self, result: Any, insert_at_index=tk.END):
        """
        해양생물 결과 표시
        
        Args:
            result: 표시할 결과
            insert_at_index: 삽입 위치 (기본값: 맨 끝)
        """
        # 결과가 모델 객체인지 딕셔너리인지 확인
        if isinstance(result, MarineVerificationResult):
            input_name = result.input_name 
            mapped_name = result.mapped_name
            is_verified = result.is_verified
            worms_status = result.worms_status
            worms_id = result.worms_id
            worms_link = result.worms_link
            wiki_summary = result.wiki_summary
        else:  # 딕셔너리 가정
            input_name = result.get('input_name', '-')
            mapped_name = result.get('mapped_name', '-')
            is_verified = result.get('is_verified', False)
            worms_status = result.get('worms_status', '-')
            worms_id = result.get('worms_id', '-')
            worms_link = result.get('worms_link', '-')
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
            
        # 아이템 추가
        self.tree.insert("", insert_at_index, text=input_name, values=(
            mapped_name,
            "✓" if is_verified else "✗",
            worms_status,
            worms_id,
            worms_link,
            display_summary
        ), tags=(tag,))
    
    def _display_microbe_result(self, result: Any, insert_at_index=tk.END):
        """
        미생물 결과 표시
        
        Args:
            result: 표시할 결과
            insert_at_index: 삽입 위치 (기본값: 맨 끝)
        """
        # 결과가 모델 객체인지 딕셔너리인지 확인
        if isinstance(result, MicrobeVerificationResult):
            input_name = result.input_name
            valid_name = result.valid_name
            is_verified = result.is_verified
            status = result.status
            taxonomy = result.taxonomy
            lpsn_link = result.lpsn_link
            wiki_summary = result.wiki_summary
            is_microbe = result.is_microbe
        else:  # 딕셔너리 가정
            # 리스트인 경우 첫 번째 항목을 사용
            if isinstance(result, list) and len(result) > 0:
                result = result[0]
                
            input_name = result.get('input_name', '-')
            valid_name = result.get('valid_name', '-')
            is_verified = result.get('is_verified', False)
            status = result.get('status', '-')
            taxonomy = result.get('taxonomy', '-')
            lpsn_link = result.get('lpsn_link', '-')
            wiki_summary = result.get('wiki_summary', '-')
            is_microbe = result.get('is_microbe', False)
        
        # --- 수정: valid_name이 없을 경우 input_name 사용 ---
        display_name = valid_name
        if not display_name or display_name == '-':
            display_name = input_name # 유효 학명이 없으면 입력 학명 표시

        # 요약이 너무 길면 자르기
        if isinstance(wiki_summary, str) and len(wiki_summary) > 60:
            display_summary = wiki_summary[:57] + '...'
        else:
            display_summary = wiki_summary or '-'
        
        # 태그 결정 (상태에 따라)
        tag = 'unverified'
        
        # 원본 is_verified 값을 우선 사용하고, 그 다음 status 문자열로 판단
        if is_verified:
            # 원본 검증 결과가 True이면 verified 태그 적용
            tag = 'verified'
        # 원본 is_verified가 False지만 status에 'correct'가 있으면 검증된 것으로 간주
        elif 'correct' in str(status).lower() and valid_name and valid_name != '-' and valid_name != '유효하지 않음':
            is_verified = True
            tag = 'verified'
        # 동의어인 경우 주의 표시
        elif 'synonym' in str(status).lower():
            tag = 'caution'
        # 검증 실패 상태 확인
        elif '검증 실패' in str(status) or '유효하지 않음' in str(valid_name) or '입력 오류' in str(status):
            is_verified = False
            tag = 'unverified'
        
        # 디버그 로그 추가
        print(f"[Debug Microbe Result] 입력명: {input_name}, 검증결과: {is_verified}, 상태: {status}")
            
        # 아이템 추가 (수정: display_name 사용)
        self.tree.insert("", insert_at_index, text=input_name, values=(
            display_name, # valid_name 대신 display_name 사용
            "✓" if is_verified else "✗",
            status,
            taxonomy,
            lpsn_link,
            display_summary
        ), tags=(tag,))
    
    def _display_col_result(self, result: Any, insert_at_index=tk.END):
        """
        COL(통합생물) 결과 표시
        
        Args:
            result: 표시할 결과 (딕셔너리 형태)
            insert_at_index: 삽입 위치 (기본값: 맨 끝)
        """
        # 디버그 로그 추가
        print(f"[Debug COL Result] 원본 결과: {result}")
        
        # 백엔드에서 제공한 키 사용
        input_name = result.get('input_name', '-')
        valid_name = result.get('valid_name', result.get('학명', '-')) # 백엔드 키 우선, UI 키는 대체용
        col_status = result.get('status', result.get('COL 상태', '-'))
        col_id = result.get('col_id', result.get('COL ID', '-'))
        col_url = result.get('col_url', result.get('COL URL', '-'))
        wiki_summary = result.get('summary', result.get('심층분석 결과', '-'))
        
        # 요약이 너무 길면 자르기
        if isinstance(wiki_summary, str) and len(wiki_summary) > 60:
            display_summary = wiki_summary[:57] + '...'
        else:
            display_summary = wiki_summary or '-'
        
        # 중요: 백엔드에서 제공하는 is_verified 값을 우선 사용
        is_verified = result.get('is_verified', False)
        
        # 백엔드 is_verified가 없는 경우, status 기반으로 판단
        if 'is_verified' not in result:
            # 검증 성공 조건: 상태가 'accepted' 또는 'provisionally accepted'이면 검증 성공
            is_verified = col_status.lower() in ['accepted', 'provisionally accepted']
            
            # 추가 디버그 로그
            print(f"[Debug COL Result] 백엔드 is_verified 없음, status에 따라 계산: {col_status} -> {is_verified}")
        else:
            # 디버그 로그
            print(f"[Debug COL Result] 백엔드 is_verified 값 사용: {is_verified}")
        
        # 태그 결정
        if is_verified:
            tag = 'verified'
        elif 'synonym' in str(col_status).lower() or 'ambiguous' in str(col_status).lower():
            tag = 'caution'
        else:
            tag = 'unverified'
        
        # 아이템 추가
        self.tree.insert("", insert_at_index, text=input_name, values=(
            valid_name,
            "✓" if is_verified else "✗",
            col_status,
            col_id,
            col_url,
            display_summary
        ), tags=(tag,))
    
    def add_result(self, result: Any):
        """단일 결과를 목록 맨 위에 추가하고 표시합니다."""
        if not result:
            return
        
        # 중복 검사: input_name을 기준으로 이미 존재하는 결과인지 확인
        input_name = result.get('input_name', '') if isinstance(result, dict) else getattr(result, 'input_name', '')
        
        # 기존 결과에서 같은 input_name이 있는지 확인
        for existing_result in self.results:
            existing_input_name = existing_result.get('input_name', '') if isinstance(existing_result, dict) else getattr(existing_result, 'input_name', '')
            if existing_input_name == input_name and input_name:
                print(f"[Debug ResultView] 중복 결과 무시 ({self.tab_type}): {input_name}")
                return
        
        # 트리뷰에서도 중복 확인 (추가 안전장치)
        for item_id in self.tree.get_children():
            tree_input_name = self.tree.item(item_id, "text")
            if tree_input_name == input_name and input_name:
                print(f"[Debug ResultView] 트리뷰에서 중복 결과 무시 ({self.tab_type}): {input_name}")
                return
        
        # 중복이 아닌 경우에만 추가
        self.results.insert(0, result)
        self._display_result(result, insert_at_index=0)
        print(f"[Debug ResultView] 새 결과 추가됨 ({self.tab_type}): {input_name}")
    
    def add_results(self, results: List[Any], clear_first: bool = False):
        """
        결과 목록 추가 (기존 로직 유지, 하지만 단일 업데이트 시에는 add_result 사용 권장)
        
        Args:
            results: 추가할 결과 목록
            clear_first: 기존 결과 초기화 여부
        """
        if clear_first:
            self.clear()
        
        for result in reversed(results):
            self.results.insert(0, result)
            self._display_result(result, insert_at_index=0)
    
    def get_selected_result(self) -> Optional[Any]:
        """선택된 결과 반환"""
        selection = self.tree.selection()
        if selection:
            item_id = selection[0]
            item_idx = self.tree.index(item_id)
            if 0 <= item_idx < len(self.results):
                return self.results[item_idx]
        return None 