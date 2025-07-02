# LPSN API 환경변수 설정 스크립트
# 사용법: .\set_lpsn_env.ps1

Write-Host "🔧 LPSN API 환경변수 설정 중..."

# LPSN API 인증 정보 설정
$env:LPSN_EMAIL="fishnala@gmail.com"
$env:LPSN_PASSWORD="2025lpsn"

Write-Host "✅ LPSN 환경변수 설정 완료!"
Write-Host "   이메일: $env:LPSN_EMAIL"
Write-Host "   비밀번호: [설정됨]"

Write-Host ""
Write-Host "🧪 LPSN API 연결 테스트를 실행하려면:"
Write-Host "python test_lpsn_api.py"
Write-Host ""
Write-Host "🚀 Species Verifier 앱을 실행하려면:"
Write-Host "python -m species_verifier.gui.app" 