"""
상태 표시줄 컴포넌트

이 모듈은 애플리케이션의 상태 정보를 표시하는 컴포넌트를 정의합니다.
"""
import tkinter as tk
import customtkinter as ctk
from typing import Any, Optional, Callable

from .base import BaseTkComponent


class StatusBar(BaseTkComponent):
    """상태 표시줄 컴포넌트"""
    
    def __init__(self, parent: Any, save_command: Optional[Callable] = None, **kwargs):
        """
        초기화
        
        Args:
            parent: 부모 위젯
            save_command: 저장 버튼 클릭 시 실행할 명령
            **kwargs: 추가 인자
        """
        self.height = kwargs.pop('height', 40)
        self.font = kwargs.pop('font', None)
        self._save_command = save_command
        super().__init__(parent, **kwargs)
    
    def _create_widgets(self, **kwargs):
        """위젯 생성"""
        # 상태바 주 프레임
        self.widget = ctk.CTkFrame(self.parent, height=self.height)
        
        # 상태바 레이아웃 설정
        self.widget.grid_columnconfigure(0, weight=1)  # 상태 메시지 (확장)
        self.widget.grid_columnconfigure(1, weight=0)  # 통계 표시
        self.widget.grid_columnconfigure(2, weight=0)  # 진행바
        self.widget.grid_columnconfigure(3, weight=0)  # 진행률 텍스트
        self.widget.grid_columnconfigure(4, weight=0)  # 저장 버튼
        self.widget.grid_columnconfigure(5, weight=0)  # 취소 버튼

        # 상태 메시지 레이블
        self.status_label = ctk.CTkLabel(
            self.widget, 
            text="입력 대기 중", 
            font=self.font, 
            anchor="w",
            width=400  # 고정 너비 설정
        )
        self.status_label.grid(row=0, column=0, padx=(10, 5), pady=5, sticky="w")
        
        # 통계 표시 레이블
        self.stats_label = ctk.CTkLabel(
            self.widget, 
            text="", 
            font=self.font, 
            anchor="e",
            width=120  # 고정 너비 설정
        )
        # 처음에는 숨김 (결과가 있을 때만 표시)
        
        # 진행률 텍스트 레이블
        self.progress_text_label = ctk.CTkLabel(
            self.widget, 
            text="", 
            font=self.font, 
            anchor="e",
            width=80  # 고정 너비 설정
        )
        # 처음에는 숨김 (진행 시에만 표시)
        
        # 진행바
        self.progressbar = ctk.CTkProgressBar(self.widget, width=150)
        # 처음에는 숨김 (진행 시에만 표시)
        self.progressbar.set(0)
        
        # 결과 저장 버튼
        self.save_button = ctk.CTkButton(
            self.widget,
            text="결과 저장",
            width=90,
            command=self._save_command,
            state="disabled",
            font=self.font
        )
        # 처음에는 숨김 (결과가 있을 때만 표시)
        
        # 취소 버튼
        self.cancel_button = ctk.CTkButton(
            self.widget, 
            text="취소", 
            width=60, 
            state="disabled", 
            font=self.font
        )
        # 처음에는 숨김 (진행 시에만 표시)
    
    def set_status(self, message: str):
        """
        상태 메시지 설정
        
        Args:
            message: 표시할 메시지
        """
        self.status_label.configure(text=message)
        
    def set_file_info(self, file_info: str):
        """
        파일 정보 설정
        
        Args:
            file_info: 표시할 파일 정보 (파일명 및 항목 수)
        """
        # 파일 정보가 비어있으면 상태 레이블만 표시
        if not file_info:
            return
            
        # 파일 정보가 있으면 상태 레이블에 추가 표시
        current_text = self.status_label.cget("text")
        if " - " in current_text:
            current_text = current_text.split(" - ")[0].strip()
        
        if file_info:
            self.status_label.configure(text=f"{current_text} - {file_info}")
        else:
            self.status_label.configure(text=current_text)
    
    def set_progress(self, value: float, current_item: int = None, total_items: int = None):
        """
        진행률 설정
        
        Args:
            value: 진행률 (0.0 ~ 1.0)
            current_item: 현재 처리 중인 항목 번호
            total_items: 전체 항목 수
        """
        # 로그 추가
        print(f"[Debug StatusBar] set_progress 호출: value={value}, current_item={current_item}, total_items={total_items}")
        
        # 다른 진행이 있으면 먼저 숨기기
        self.progressbar.grid_forget()
        self.progress_text_label.grid_forget()
        
        # 진행바 설정
        self.progressbar.configure(mode="determinate")
        self.progressbar.set(value)
        
        # 진행바 표시 (통계 뒤에 표시)
        self.progressbar.grid(row=0, column=2, padx=(5, 5), pady=5, sticky="e")
        
        # 현재 항목과 전체 항목 수가 있는 경우 텍스트 표시
        if current_item is not None and total_items is not None and total_items > 0:
            # 진행률 텍스트 업데이트
            self.progress_text_label.configure(text=f"{current_item}/{total_items}")
        else:
            # 일반 진행률만 있는 경우 백분율로 표시
            percentage = int(value * 100)
            self.progress_text_label.configure(text=f"{percentage}%")
        
        # 진행률 텍스트 표시 (진행바 뒤에 표시)
        self.progress_text_label.grid(row=0, column=3, padx=(5, 5), pady=5, sticky="e")
    
    def set_busy(self, status_text: Optional[str] = None):
        """바쁨 상태로 설정 (진행바, 취소 버튼 표시)"""
        print(f"[Debug StatusBar] set_busy 호출: status_text={status_text}")
        
        # 상태 메시지 설정
        if status_text:
            self.status_label.configure(text=status_text)
        else:
            self.status_label.configure(text="처리 중...")

        # 저장 버튼 숨김
        self.save_button.grid_forget()
        
        # 진행률 텍스트 초기화 및 표시
        self.progress_text_label.configure(text="0%")
        self.progress_text_label.grid(row=0, column=3, padx=(5, 5), pady=5, sticky="e")

        # 진행바 표시 및 설정
        self.progressbar.grid(row=0, column=2, padx=(5, 5), pady=5, sticky="e")
        self.progressbar.configure(mode="indeterminate")
        self.progressbar.start()
        
        # 통계 숨김 (진행 중에는 표시하지 않음)
        self.stats_label.grid_forget()

        # 취소 버튼 활성화 및 표시
        self.cancel_button.configure(state="normal")
        self.cancel_button.grid(row=0, column=5, padx=(5, 10), pady=5, sticky="e")
    
    def set_ready(self, status_text: str = "입력 대기 중", show_save_button: bool = False):
        """준비 상태로 설정 (진행바, 취소 버튼 숨김, 조건부 저장 버튼 표시)"""
        print(f"[Debug StatusBar] set_ready 호출: status_text={status_text}, show_save_button={show_save_button}")
        
        # 상태 메시지 설정
        self.status_label.configure(text=status_text)

        # 진행률 텍스트 초기화 및 숨김
        self.progress_text_label.configure(text="")
        self.progress_text_label.grid_forget()
        
        # 진행바 숨김
        self.progressbar.grid_forget()
        
        # 취소 버튼 숨김
        self.cancel_button.grid_forget()
        
        # 저장 버튼 숨김 (초기 상태)
        self.save_button.grid_forget()

        # 진행바 중지 및 초기화
        self.progressbar.stop()
        self.progressbar.configure(mode="determinate")
        self.progressbar.set(0)

        # 취소 버튼 비활성화
        self.cancel_button.configure(state="disabled")

        # 결과가 있는 경우 저장 버튼 표시
        if show_save_button:
            self.save_button.configure(state="normal")
            self.save_button.grid(row=0, column=4, padx=(5, 10), pady=5, sticky="e")
        else:
            self.save_button.configure(state="disabled")
    
    def set_stats(self, success_count: int, fail_count: int, total_processed: int = None, duplicates_removed: int = None):
        """
        통계 설정
        
        Args:
            success_count: 성공 개수
            fail_count: 실패 개수
            total_processed: 전체 처리된 학명 수 (선택사항)
            duplicates_removed: 중복 제거된 학명 수 (선택사항)
        """
        print(f"[Debug StatusBar] set_stats 호출: 성공={success_count}, 실패={fail_count}, 전체={total_processed}, 중복제거={duplicates_removed}")
        
        if success_count == 0 and fail_count == 0:
            # 통계가 없으면 숨김
            self.stats_label.grid_forget()
            print(f"[Debug StatusBar] 통계 숨김 (성공=0, 실패=0)")
        else:
            # 기본 통계 텍스트
            stats_text = f"성공: {success_count}개, 실패: {fail_count}개"
            
            # 전체 처리 수와 중복 제거 정보 추가
            if total_processed is not None and duplicates_removed is not None and duplicates_removed > 0:
                displayed_count = success_count + fail_count
                stats_text = f"전체 {total_processed}개 처리 → 중복 {duplicates_removed}개 제거 → {displayed_count}개 표시 (성공: {success_count}, 실패: {fail_count})"
            elif total_processed is not None:
                displayed_count = success_count + fail_count
                if total_processed != displayed_count:
                    stats_text = f"전체 {total_processed}개 → {displayed_count}개 표시 (성공: {success_count}, 실패: {fail_count})"
            
            self.stats_label.configure(text=stats_text)
            # 통계 표시 (상태 메시지 뒤에 표시)
            self.stats_label.grid(row=0, column=1, padx=(5, 5), pady=5, sticky="e")
            print(f"[Debug StatusBar] 통계 표시: '{stats_text}'")
    
    def set_save_command(self, command: Callable):
        """'결과 저장' 버튼의 명령(콜백 함수)을 설정합니다."""
        self._save_command = command
        self.save_button.configure(command=self._save_command)
    
    def set_cancel_command(self, command: Callable):
        """취소 버튼 명령 설정"""
        print(f"[Debug StatusBar] set_cancel_command 호출")
        self.cancel_button.configure(command=command)