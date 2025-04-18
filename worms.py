import requests
import json
import os
# import google.generativeai as genai # core 모듈 사용으로 주석 처리 또는 삭제
import time
from datetime import datetime, timedelta, timezone
# from supabase import create_client, Client # core 모듈 사용으로 주석 처리 또는 삭제
from dotenv import load_dotenv
import argparse
import csv
import pandas as pd # 결과 출력을 위해 추가
from tqdm import tqdm # 진행률 표시를 위해 추가
import sys # sys.exit 사용 및 경로 추가

# 프로젝트 루트 경로를 sys.path에 추가 (core 모듈 임포트를 위해)
# cli.py 와 동일한 로직 사용
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- 설정 ---
# 프로젝트 루트 경로에서 .env 파일 로드
dotenv_path = os.path.join(project_root, '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
    print(f"[Info] Loaded environment variables from: {dotenv_path}")
else:
    print(f"[Warning] .env file not found at: {dotenv_path}. Some features might not work.")

# .env.local 파일도 로드 (있는 경우 .env 파일의 변수를 덮어씀)
dotenv_local_path = os.path.join(project_root, '.env.local')
if os.path.exists(dotenv_local_path):
    load_dotenv(dotenv_local_path, override=True)
    print(f"[Info] Loaded environment variables from: {dotenv_local_path}")
else:
    print(f"[Info] No .env.local file found at: {dotenv_local_path}")
# load_dotenv() # .env 파일 로드 - 이 줄 제거 또는 주석 처리

# WORMS_BASE_URL = "https://www.marinespecies.org/rest" # core 모듈에서 관리
# REQUEST_TIMEOUT = 30
# API_DELAY = 0.5

# GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY") # core 모듈에서 관리
# GEMINI_MODEL_NAME = "gemini-1.5-flash" # core 모듈에서 관리 (또는 .env에서 가져옴)

# SUPABASE_URL = os.getenv("SUPABASE_URL") # core 모듈에서 관리
# SUPABASE_KEY = os.getenv("SUPABASE_KEY") # core 모듈에서 관리 (이름 통일)
# SUPABASE_TABLE_NAME = "scientific_names" # core 모듈에서 관리
# CACHE_EXPIRY_DAYS = 30 # core 모듈에서 관리

# supabase: Client = None # core 모듈에서 관리

# --- Core 모듈 임포트 및 의존성 확인 --- (기존 check_dependencies_and_api_key 대체)
try:
    from species_verifier.core.verifier import verify_species_list
    # 필요한 경우 다른 core 함수 임포트
    print("[Info] Successfully imported 'verify_species_list' from core.verifier.")
except ImportError as e:
    print(f"[Error] Failed to import core modules: {e}")
    print("Please ensure the script is run from the project root directory")
    print("and required dependencies (requests, google-generativeai, supabase, python-dotenv) are installed.")
    sys.exit(1)
except Exception as e:
    print(f"[Error] An unexpected error occurred during core module import: {e}")
    sys.exit(1)

# --- WoRMS API 함수 --- (core 모듈 사용으로 제거)
# def get_aphia_id(scientific_name): ...
# def get_aphia_record(aphia_id): ...

# --- Gemini API 함수 --- (core 모듈 사용으로 제거)
# def translate_and_format_with_gemini(input_name, worms_result): ...

# --- Supabase 연동 함수 --- (core 모듈 사용으로 제거)
# def get_cached_data(input_name): ...
# def upsert_data_to_supabase(input_name, record, gemini_data): ...

# --- 메인 검사 함수 --- (core 모듈 사용으로 제거)
# def check_scientific_name(name_to_check): ...

# --- 결과 출력 함수 ---
def display_results_terminal(results):
    """검증 결과를 터미널에 표 형태로 출력 (지정된 컬럼만)"""
    if not results:
        print("표시할 결과가 없습니다.")
        return

    df = pd.DataFrame(results)
    # 표시할 컬럼 및 순서 지정 (worms_id, worms_status 포함)
    display_columns = [
        'input_name', 'is_verified', 'worms_id', 'worms_status', 'gemini_description'
    ]
    # 결과에 없는 컬럼은 생성 (기본값으로 채움)
    for col in display_columns:
        if col not in df.columns:
            df[col] = '-' # 또는 적절한 기본값

    # 필요한 컬럼만 선택하고 순서대로 재정렬
    df = df[display_columns]

    if 'is_verified' in df.columns:
        df['is_verified'] = df['is_verified'].fillna(False).apply(lambda x: "Yes" if x else "No")

    column_mapping = {
        'input_name': '입력 학명',
        'is_verified': '검증됨',
        'worms_id': 'WoRMS ID', # 다시 추가
        'worms_status': 'WoRMS 상태', # 다시 추가
        'gemini_description': 'Gemini 요약'
    }
    df.rename(columns=column_mapping, inplace=True)

    print("\n--- 검증 결과 ---") # 제목 변경
    with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.width', 1000):
        print(df.to_string(index=False))
    print("---------------")

def write_results_to_excel(results, output_filename):
    """검증 결과를 Excel (.xlsx) 파일로 저장합니다 (지정된 컬럼만)."""
    if not results:
        print("[Warning] No results to write to Excel.")
        return

    # 출력 파일명 .xlsx 확장자 확인 및 강제
    if not output_filename.lower().endswith('.xlsx'):
        output_filename = os.path.splitext(output_filename)[0] + '.xlsx'
        print(f"[Info] Output filename adjusted to: {output_filename}")

    try:
        df = pd.DataFrame(results)

        # 필요한 컬럼 선택 및 순서 지정 (worms_id, worms_status 포함)
        output_columns = ['input_name', 'is_verified', 'worms_id', 'worms_status', 'gemini_description']
        # 결과에 없는 컬럼은 생성 (기본값으로 채움)
        for col in output_columns:
            if col not in df.columns:
                df[col] = '-'

        # 필요한 컬럼만 포함하고 순서대로 재정렬
        df_output = df[output_columns].copy()

        # is_verified 값을 Yes/No로 변환
        if 'is_verified' in df_output.columns:
            df_output['is_verified'] = df_output['is_verified'].fillna(False).apply(lambda x: "Yes" if x else "No")

        # Excel 파일로 저장 (index=False 옵션으로 인덱스 열 제외)
        df_output.to_excel(output_filename, index=False, engine='openpyxl') # openpyxl 엔진 사용 명시
        print(f"\n[Info] Results successfully saved to '{output_filename}'.")
    except ImportError:
         print("[Error] 'openpyxl' library is required to write Excel files. Please install it: pip install openpyxl")
    except Exception as e:
        print(f"[Error] An unexpected error occurred while writing Excel file: {e}")


# --- 스크립트 실행 ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify scientific names, save results to Excel (.xlsx). Columns: input_name, is_verified, worms_id, worms_status, gemini_description.")
    parser.add_argument("input_file", help="Path to the input file (.csv or .xlsx).")
    parser.add_argument("output_file", help="Path to the output Excel file (.xlsx). Extension will be enforced.")

    args = parser.parse_args()
    input_filename = args.input_file
    output_filename = args.output_file

    # 입력 파일 존재 확인
    if not os.path.exists(input_filename):
        print(f"[Error] Input file not found: {input_filename}")
        sys.exit(1)

    # CSV/Excel 파일 읽기
    scientific_names_from_file = []
    try:
        print(f"[Info] Reading file: {input_filename}...")
        if input_filename.lower().endswith('.csv'):
            df_input = pd.read_csv(input_filename)
        elif input_filename.lower().endswith('.xlsx'):
            df_input = pd.read_excel(input_filename)
        else:
            print("[Error] Unsupported file format. Please use .csv or .xlsx.")
            sys.exit(1)

        if df_input.empty or len(df_input.columns) == 0:
            print("[Error] Input file is empty or has no columns.")
            sys.exit(1)

        # 첫 번째 컬럼 사용, 중복 제거, 문자열 변환
        scientific_names_from_file = df_input.iloc[:, 0].astype(str).drop_duplicates().tolist()
        print(f"[Info] Found {len(scientific_names_from_file)} unique names to verify.")

        if not scientific_names_from_file:
            print("[Warning] No valid species names found in the first column of the file.")
            sys.exit(0)

    except Exception as e:
        print(f"[Error] Failed to read or process input file: {e}")
        sys.exit(1)

    # 진행률 표시를 위한 pbar 변수 초기화 (콜백 함수 외부)
    pbar = None

    # 진행률 콜백 함수 정의 (try 블록 외부)
    def progress_callback(progress):
        global pbar # global 키워드 사용 시도 (nonlocal 대신)
        if pbar is None:
            pbar = tqdm(total=100, desc="Verifying", unit="%")
        update_amount = int(progress * 100) - pbar.n
        if update_amount > 0:
            pbar.update(update_amount)

    # 검증 실행 (Core 모듈 사용)
    all_results = []
    try:
        print("\n[Info] Starting verification process using core modules...")
        all_results = verify_species_list(scientific_names_from_file, progress_callback=progress_callback)
        print("\n[Info] Verification process completed.")

        # 터미널에 결과 요약 출력 (변경된 컬럼 기준)
        display_results_terminal(all_results)

        # 결과를 Excel 파일로 저장 (변경된 함수 사용)
        write_results_to_excel(all_results, output_filename)

    except Exception as e:
        print(f"\n[Error] An error occurred during verification: {e}")
        import traceback
        print("Traceback:")
        print(traceback.format_exc())
        sys.exit(1)
    finally:
        # finally 블록에서 pbar 정리
        if pbar:
            if pbar.n < 100:
                 pbar.update(100 - pbar.n) # 100% 채우기
            pbar.close()