@echo off
chcp 65001 > nul
echo ============================================
echo Species Verifier - Supabase 설정 도구
echo ============================================
echo.

echo 📦 필요한 Python 패키지 설치 중...
pip install supabase pydantic python-dotenv

echo.
echo ✅ 패키지 설치 완료!
echo.

echo 📋 환경 변수 설정 안내:
echo ----------------------------------------
echo 1. .env 파일을 생성하거나 수정하세요
echo 2. 다음 내용을 추가하세요:
echo.
echo SUPABASE_URL=https://your-project-id.supabase.co
echo SUPABASE_ANON_KEY=your-anon-key-here
echo.

echo 🔧 Supabase 프로젝트 설정:
echo ----------------------------------------
echo 1. https://app.supabase.com/ 에 접속
echo 2. "New Project" 클릭
echo 3. 프로젝트 이름: species-verifier
echo 4. 데이터베이스 비밀번호 설정
echo 5. 지역 선택: ap-northeast-2 (한국)
echo.

echo 🗄️ 데이터베이스 스키마 생성:
echo ----------------------------------------
echo 1. Supabase 대시보드에서 SQL Editor 열기
echo 2. 'Supabase_DB_구성_가이드.md' 파일의 SQL 스크립트 실행
echo.

echo 🧪 연결 테스트:
echo ----------------------------------------
echo .env 파일 설정 후 다음 명령으로 테스트하세요:
echo python test_supabase_integration.py
echo.

echo ✨ 설정이 완료되었습니다!
pause 