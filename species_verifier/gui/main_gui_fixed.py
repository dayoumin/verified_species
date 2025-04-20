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
import queue  # Queue 추가

# 기존 코드는 그대로 유지...

# _on_tab_change 메서드의 들여쓰기 수정
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

# _update_results_display 메서드의 들여쓰기 수정
def _update_results_display(self, results_list, clear_existing=False, tab_name=None):
    """검증 결과를 Treeview에 표시합니다."""
    # ... existing code ...
    
    # 결과 추가
    for result in results_list:
        # 저장 변수에 추가
        current_results_ref.append(result)
        
        if target_tab == "해양생물":
            # 해양생물 탭 표시 로직 
            self._display_marine_result(tree, result)
        elif target_tab == "미생물 (LPSN)":
            # 미생물 탭 표시 로직
            self._display_microbe_result(tree, result)

# _display_marine_result 메서드의 들여쓰기 수정
def _display_marine_result(self, tree, result):
    """해양생물 결과를 트리뷰에 표시합니다."""
    # ... existing code ...
    
    # 요약이 너무 길면 자르기
    if isinstance(wiki_summary, str) and len(wiki_summary) > 60:
        display_summary = wiki_summary[:57] + '...'
    else:
        display_summary = wiki_summary or '-'
    
    # 태그 결정 (상태에 따라)
    # ... existing code ...

# _display_microbe_result 메서드의 들여쓰기 수정
def _display_microbe_result(self, tree, result):
    """미생물 결과를 트리뷰에 표시합니다."""
    # ... existing code ...
        
    # 분류 정보 길이 제한
    if isinstance(taxonomy, str) and len(taxonomy) > 60:
        display_taxonomy = taxonomy[:57] + '...'
    else:
        display_taxonomy = taxonomy or '-'
        
    # 태그 결정 (상태에 따라)
    # ... existing code ...

# _on_tree_motion 메서드의 들여쓰기 수정
def _on_tree_motion(self, event, tree):
    """마우스가 Treeview 위에서 움직일 때 호출되는 함수"""
    # ... existing code ...
        
    # 해양생물 탭 트리뷰인 경우
    if tree == self.result_tree_marine:
        if column_id == "#4": # WoRMS ID 컬럼 헤더 ("WoRMS ID(?)")
            tooltip_text = "더블 클릭 시 WoRMS ID 복사됨"
        elif column_id == "#5": # WoRMS Link 컬럼 헤더 ("WoRMS 링크(?)")
            tooltip_text = "더블 클릭 시 WoRMS 웹사이트 확인"
    # ... existing code ... 