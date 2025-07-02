#!/usr/bin/env python3
"""
API 차단 방지 시스템 테스트 스크립트

이 스크립트는 새로 구현된 대량 처리 경고 시스템을 테스트합니다.
"""

import pandas as pd
import os

def create_test_files():
    """다양한 크기의 테스트 파일들을 생성합니다."""
    
    print("🔧 테스트 파일 생성 중...")
    
    # 1. 소규모 파일 (50개) - 경고 없음
    small_data = [f"Escherichia coli_{i:02d}" for i in range(1, 51)]
    df_small = pd.DataFrame(small_data, columns=['species'])
    df_small.to_excel('test_small_50.xlsx', index=False)
    print(f"✅ 소규모 테스트 파일 생성: test_small_50.xlsx ({len(small_data)}개)")
    
    # 2. 중간 규모 파일 (150개) - 일반 경고
    medium_data = [f"Bacillus subtilis_{i:03d}" for i in range(1, 151)]
    df_medium = pd.DataFrame(medium_data, columns=['species'])
    df_medium.to_excel('test_medium_150.xlsx', index=False)
    print(f"⚠️ 중간 규모 테스트 파일 생성: test_medium_150.xlsx ({len(medium_data)}개)")
    
    # 3. 대규모 파일 (350개) - 강력 경고
    large_data = [f"Staphylococcus aureus_{i:03d}" for i in range(1, 351)]
    df_large = pd.DataFrame(large_data, columns=['species'])
    df_large.to_excel('test_large_350.xlsx', index=False)
    print(f"🚨 대규모 테스트 파일 생성: test_large_350.xlsx ({len(large_data)}개)")
    
    # 4. 초대형 파일 (600개) - 자동 차단
    huge_data = [f"Pseudomonas aeruginosa_{i:03d}" for i in range(1, 601)]
    df_huge = pd.DataFrame(huge_data, columns=['species'])
    df_huge.to_excel('test_huge_600.xlsx', index=False)
    print(f"❌ 초대형 테스트 파일 생성: test_huge_600.xlsx ({len(huge_data)}개) - 자동 차단 예상")


def test_config_values():
    """설정 값들을 확인합니다."""
    
    print("\n📊 설정 값 확인:")
    
    try:
        from species_verifier.config import app_config
        
        print(f"   • MAX_FILE_PROCESSING_LIMIT: {app_config.MAX_FILE_PROCESSING_LIMIT}개")
        print(f"   • LARGE_FILE_WARNING_THRESHOLD: {app_config.LARGE_FILE_WARNING_THRESHOLD}개")
        print(f"   • CRITICAL_FILE_WARNING_THRESHOLD: {app_config.CRITICAL_FILE_WARNING_THRESHOLD}개")
        print(f"   • BATCH_SIZE: {app_config.BATCH_SIZE}개")
        print(f"   • REQUEST_DELAY: {app_config.REQUEST_DELAY}초")
        print(f"   • REALTIME_REQUEST_DELAY: {app_config.REALTIME_REQUEST_DELAY}초")
        print(f"   • BATCH_DELAY: {app_config.BATCH_DELAY}초")
        print(f"   • LPSN_REQUEST_DELAY: {app_config.LPSN_REQUEST_DELAY}초")
        
        print("\n🚨 보안 강화 내용:")
        print(f"   • 파일 처리 제한: 3000개 → {app_config.MAX_FILE_PROCESSING_LIMIT}개 (대폭 감소)")
        print(f"   • 배치 크기: 100개 → {app_config.BATCH_SIZE}개 (부하 감소)")
        print(f"   • 요청 지연: 1.2초 → {app_config.REQUEST_DELAY}초 (안전성 증가)")
        print(f"   • LPSN 지연: 1.8초 → {app_config.LPSN_REQUEST_DELAY}초 (계정 보호)")
        
    except Exception as e:
        print(f"❌ 설정 로드 오류: {e}")


def test_api_status():
    """각 API의 현재 상태를 간단히 확인합니다."""
    
    print("\n🌐 API 상태 확인:")
    
    # WoRMS API 테스트
    try:
        from species_verifier.core.worms_api import verify_species_worms
        result = verify_species_worms("Gadus morhua")
        print(f"   ✅ WoRMS API: 정상 (차단 위험: 낮음)")
    except Exception as e:
        print(f"   ❌ WoRMS API: 오류 - {e}")
    
    # COL API 테스트
    try:
        from species_verifier.core.col_api import verify_col_species
        result = verify_col_species("Homo sapiens")
        print(f"   ✅ COL API: 정상 (차단 위험: 낮음)")
    except Exception as e:
        print(f"   ❌ COL API: 오류 - {e}")
    
    # LPSN API 테스트
    try:
        from species_verifier.core.verifier import verify_microbe_species
        result = verify_microbe_species("Escherichia coli")
        print(f"   ✅ LPSN API: 정상 (차단 위험: 높음 - 특별 주의 필요)")
    except Exception as e:
        print(f"   ⚠️ LPSN API: {e} (계정 확인 필요)")


def print_usage_guide():
    """사용 가이드를 출력합니다."""
    
    print("\n📚 테스트 방법:")
    print("1. GUI 애플리케이션 실행:")
    print("   python -m species_verifier.gui.app")
    print()
    print("2. 생성된 테스트 파일들로 테스트:")
    print("   • test_small_50.xlsx: 경고 없이 진행됨")
    print("   • test_medium_150.xlsx: 중간 규모 파일 경고 표시")
    print("   • test_large_350.xlsx: 대량 처리 강력 경고 표시")
    print("   • test_huge_600.xlsx: 자동 차단됨")
    print()
    print("3. 각 탭에서 테스트:")
    print("   • 해양생물 탭: WoRMS API 테스트")
    print("   • 미생물 탭: LPSN API 테스트 (주의 필요)")
    print("   • 통합생물 탭: COL API 테스트")
    print()
    print("4. 예상 동작:")
    print("   • 소규모: 바로 처리")
    print("   • 중간: 경고 후 승인하면 처리")
    print("   • 대량: 강력 경고 후 승인하면 처리")
    print("   • 초대형: 자동 차단")


if __name__ == "__main__":
    print("🔒 API 차단 방지 시스템 테스트")
    print("=" * 50)
    
    # 테스트 파일 생성
    create_test_files()
    
    # 설정 값 확인
    test_config_values()
    
    # API 상태 확인
    test_api_status()
    
    # 사용 가이드 출력
    print_usage_guide()
    
    print("\n✅ 테스트 준비 완료!")
    print("GUI 애플리케이션을 실행하여 경고 시스템을 테스트해보세요.") 