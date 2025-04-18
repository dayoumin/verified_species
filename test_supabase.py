import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("DB_SUPABASE_KEY")
)

try:
    result = supabase.table('scientific_names').select("*").execute()
    print("연결 성공:", result)
except Exception as e:
    print("연결 실패:", e)