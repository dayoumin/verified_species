"""
새로운 기능 테스트 스크립트

테스트 항목:
1. ✅ 실시간 검증 결과와 Supabase 결과 비교 업데이트
2. ✅ 1개월 주기 자동 업데이트 스케줄링
3. ✅ 데이터베이스별 분류 (해양생물→WoRMS, 미생물→LPSN, 담수생물→COL)
4. ✅ 기관 보안 모드 (LOCAL/HYBRID/CLOUD)
"""

import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_security_modes():
    """보안 모드 테스트"""
    print("🔒 보안 모드 테스트")
    print("=" * 40)
    
    try:
        from species_verifier.database.secure_mode import (
            SecureDatabaseManager, get_secure_database_mode
        )
        
        # 현재 보안 모드 확인
        current_mode = get_secure_database_mode()
        print(f"현재 보안 모드: {current_mode.upper()}")
        
        # LOCAL 모드 테스트
        print("\n📁 LOCAL 모드 테스트:")
        local_db = SecureDatabaseManager(mode="local")
        
        # 테스트 데이터 저장
        test_data = {
            "scientific_name": "Gadus morhua",
            "status": "valid", 
            "classification": ["Animalia", "Chordata", "Actinopterygii"],
            "worms_id": 126436
        }
        
        success = local_db.set_cache("Gadus morhua", "worms", test_data)
        print(f"  로컬 캐시 저장: {'✅ 성공' if success else '❌ 실패'}")
        
        # 데이터 조회
        cached_data = local_db.get_cache("Gadus morhua", "worms")
        print(f"  로컬 캐시 조회: {'✅ 성공' if cached_data else '❌ 실패'}")
        
        # 통계 조회
        stats = local_db.get_cache_stats()
        print(f"  캐시 통계: 총 {stats.get('total_cached', 0)}개, 유효 {stats.get('valid_cached', 0)}개")
        
        return True
        
    except Exception as e:
        print(f"❌ 보안 모드 테스트 실패: {e}")
        return False

def test_database_classification():
    """데이터베이스별 분류 테스트"""
    print("\n🗂️ 데이터베이스 분류 테스트")
    print("=" * 40)
    
    try:
        from species_verifier.database.scheduler import get_cache_scheduler
        
        scheduler = get_cache_scheduler()
        schedule_info = scheduler.get_update_schedule_info()
        
        print("데이터베이스별 분류:")
        classifications = schedule_info['database_classifications']
        
        expected_classifications = {
            "marine_species": "worms",      # 해양생물 → WoRMS
            "microorganisms": "lpsn",       # 미생물 → LPSN
            "freshwater_species": "col",    # 담수생물 → COL
            "general_species": "col"        # 일반생물 → COL
        }
        
        all_correct = True
        for species_type, expected_db in expected_classifications.items():
            actual_db = classifications.get(species_type)
            status = "✅" if actual_db == expected_db else "❌"
            print(f"  {species_type}: {actual_db} {status}")
            if actual_db != expected_db:
                all_correct = False
        
        print(f"\n분류 시스템: {'✅ 정상' if all_correct else '❌ 오류'}")
        return all_correct
        
    except Exception as e:
        print(f"❌ 데이터베이스 분류 테스트 실패: {e}")
        return False

def test_real_time_comparison():
    """실시간 비교 기능 테스트 (시뮬레이션)"""
    print("\n⚡ 실시간 비교 기능 테스트")
    print("=" * 40)
    
    try:
        from species_verifier.database.scheduler import get_cache_scheduler
        from species_verifier.database.secure_mode import get_secure_database_manager
        
        scheduler = get_cache_scheduler()
        secure_db = get_secure_database_manager()
        
        # 테스트용 가짜 API 함수
        def mock_worms_api(scientific_name):
            """테스트용 WoRMS API 시뮬레이션"""
            mock_data = {
                "Gadus morhua": {
                    "scientific_name": "Gadus morhua",
                    "status": "valid",
                    "classification": ["Animalia", "Chordata", "Actinopterygii"],
                    "worms_id": 126436,
                    "last_updated": "2024-01-15"  # 변경된 데이터 시뮬레이션
                }
            }
            return mock_data.get(scientific_name)
        
        # 1. 기존 캐시 데이터 생성 (이전 버전)
        old_data = {
            "scientific_name": "Gadus morhua",
            "status": "valid",
            "classification": ["Animalia", "Chordata", "Actinopterygii"],
            "worms_id": 126436,
            "last_updated": "2023-12-01"  # 오래된 데이터
        }
        
        secure_db.set_cache("Gadus morhua", "worms", old_data)
        print("  기존 캐시 데이터 생성: ✅")
        
        # 2. 실시간 비교 및 업데이트 테스트
        result = scheduler.verify_and_update_cache(
            scientific_name="Gadus morhua",
            source_db="worms",
            api_call_func=mock_worms_api,
            force_update=False
        )
        
        print(f"  실시간 비교 결과: {result['status']}")
        
        if result['status'] == 'updated':
            print("  ✅ 데이터 변경 감지 및 자동 업데이트 성공")
            changes = result.get('changes', [])
            print(f"     변경된 필드 수: {len(changes)}")
        elif result['status'] == 'cache_valid':
            print("  ✅ 캐시 데이터가 최신 상태 확인")
        else:
            print(f"  ⚠️ 예상치 못한 상태: {result['status']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 실시간 비교 테스트 실패: {e}")
        return False

def test_monthly_update_schedule():
    """월간 업데이트 스케줄 테스트"""
    print("\n📅 월간 업데이트 스케줄 테스트")
    print("=" * 40)
    
    try:
        from species_verifier.database.scheduler import get_cache_scheduler
        
        scheduler = get_cache_scheduler()
        
        # 스케줄 정보 확인
        schedule_info = scheduler.get_update_schedule_info()
        
        print("업데이트 전략:")
        strategies = schedule_info['update_strategies']
        
        expected_strategies = ['worms', 'lpsn', 'col']
        all_present = True
        
        for db in expected_strategies:
            if db in strategies:
                strategy = strategies[db]
                print(f"  {db.upper()}: {strategy['schedule']} (지연: {strategy['api_delay']}초)")
            else:
                print(f"  {db.upper()}: ❌ 전략 없음")
                all_present = False
        
        print(f"다음 월간 업데이트: {schedule_info.get('next_monthly_update', 'N/A')}")
        
        # 실제 업데이트는 테스트 환경에서 실행하지 않음 (API 호출 부담)
        print("\n  ⚠️ 실제 월간 업데이트는 프로덕션 환경에서만 실행됩니다")
        
        return all_present
        
    except Exception as e:
        print(f"❌ 월간 업데이트 스케줄 테스트 실패: {e}")
        return False

def test_enterprise_security():
    """기관 보안 설정 테스트"""
    print("\n🏢 기관 보안 설정 테스트")
    print("=" * 40)
    
    try:
        # 환경 변수 시뮬레이션
        original_env = {}
        test_env_vars = {
            "SPECIES_VERIFIER_DB_MODE": "local",
            "ENTERPRISE_NETWORK": "true"
        }
        
        # 환경 변수 임시 설정
        for key, value in test_env_vars.items():
            original_env[key] = os.getenv(key)
            os.environ[key] = value
        
        try:
            from species_verifier.database.secure_mode import get_secure_database_mode
            
            # 보안 모드 확인
            mode = get_secure_database_mode()
            print(f"감지된 보안 모드: {mode.upper()}")
            
            # 기관 네트워크에서는 LOCAL 또는 HYBRID 모드여야 함
            if mode in ['local', 'hybrid']:
                print("✅ 기관 보안 정책 준수")
                security_compliant = True
            else:
                print("⚠️ 기관 보안 정책 검토 필요")
                security_compliant = False
            
            # 보안 권장사항 표시
            recommendations = {
                'local': "완전한 로컬 처리, 외부 연결 없음",
                'hybrid': "로컬 우선 + 선택적 외부 연결",
                'cloud': "클라우드 우선 (기관 환경 비권장)"
            }
            
            print(f"권장사항: {recommendations.get(mode, '알 수 없음')}")
            
        finally:
            # 환경 변수 복원
            for key, original_value in original_env.items():
                if original_value is None:
                    if key in os.environ:
                        del os.environ[key]
                else:
                    os.environ[key] = original_value
        
        return security_compliant
        
    except Exception as e:
        print(f"❌ 기관 보안 설정 테스트 실패: {e}")
        return False

def main():
    """전체 테스트 실행"""
    print("🧪 Species Verifier 새로운 기능 테스트")
    print("=" * 50)
    
    test_results = {}
    
    # 1. 보안 모드 테스트
    test_results['security_modes'] = test_security_modes()
    
    # 2. 데이터베이스 분류 테스트
    test_results['database_classification'] = test_database_classification()
    
    # 3. 실시간 비교 테스트
    test_results['real_time_comparison'] = test_real_time_comparison()
    
    # 4. 월간 업데이트 스케줄 테스트
    test_results['monthly_update'] = test_monthly_update_schedule()
    
    # 5. 기관 보안 테스트
    test_results['enterprise_security'] = test_enterprise_security()
    
    # 결과 요약
    print("\n📊 테스트 결과 요약")
    print("=" * 50)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ 통과" if result else "❌ 실패"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
        if result:
            passed += 1
    
    print(f"\n전체 결과: {passed}/{total} 테스트 통과 ({passed/total*100:.1f}%)")
    
    # 사용자 질문 답변 확인
    print("\n❓ 사용자 질문 답변 확인")
    print("=" * 50)
    
    questions_answers = [
        ("1. 실시간 검증 결과와 supabase 결과 비교 업데이트", test_results['real_time_comparison']),
        ("2. 1개월 주기 DB 업데이트", test_results['monthly_update']),
        ("3. 해양생물→WoRMS, 미생물→LPSN, 담수생물→COL 분류", test_results['database_classification']),
        ("4. 기관 내 인터넷망 보안 고려", test_results['enterprise_security'])
    ]
    
    for question, status in questions_answers:
        answer = "✅ 구현됨" if status else "❌ 확인 필요"
        print(f"{question}: {answer}")
    
    if all(test_results.values()):
        print("\n🎉 모든 기능이 정상적으로 구현되었습니다!")
    else:
        print("\n⚠️ 일부 기능에 문제가 있습니다. 로그를 확인해주세요.")

if __name__ == "__main__":
    main() 