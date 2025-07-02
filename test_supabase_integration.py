"""
Supabase 데이터베이스 연동 테스트 스크립트

이 스크립트는 Species Verifier와 Supabase 데이터베이스 연동을 테스트합니다.
"""
import os
import sys
import time
from datetime import datetime

# 현재 디렉토리를 sys.path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

def test_basic_connection():
    """기본 연결 테스트"""
    print("=" * 50)
    print("🔗 Supabase 기본 연결 테스트")
    print("=" * 50)
    
    try:
        from species_verifier.database.supabase_client import supabase_client
        
        if supabase_client.test_connection():
            print("✅ Supabase 연결 성공!")
            return True
        else:
            print("❌ Supabase 연결 실패")
            return False
    except Exception as e:
        print(f"❌ 연결 테스트 중 오류 발생: {e}")
        return False

def test_session_creation():
    """세션 생성 테스트"""
    print("\n" + "=" * 50)
    print("📝 세션 생성 테스트")
    print("=" * 50)
    
    try:
        from species_verifier.database.services import get_database_service
        from species_verifier.database.models import VerificationType
        
        db_service = get_database_service()
        
        # 테스트 세션 생성
        session_id = db_service.create_session_sync(
            session_name="테스트 세션",
            verification_type=VerificationType.MARINE,
            user_id=None  # 익명 사용자
        )
        
        print(f"✅ 세션 생성 성공! Session ID: {session_id}")
        
        # 세션 정보 조회
        session_info = db_service.get_session(session_id)
        if session_info:
            print(f"✅ 세션 조회 성공! 세션명: {session_info.get('session_name')}")
            return session_id
        else:
            print("❌ 세션 조회 실패")
            return None
            
    except Exception as e:
        print(f"❌ 세션 생성 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_verification_integration():
    """검증 통합 테스트"""
    print("\n" + "=" * 50)
    print("🧪 검증 통합 테스트")
    print("=" * 50)
    
    try:
        from species_verifier.database.integration import get_verification_integrator
        
        integrator = get_verification_integrator()
        
        # 테스트 데이터
        test_species = ["Homo sapiens", "Canis lupus"]
        
        print(f"📋 테스트 종 목록: {test_species}")
        print("🔄 해양생물 검증 시작...")
        
        # 해양생물 검증 테스트
        result = integrator.verify_and_save_marine_species(
            species_list=test_species,
            session_name="통합 테스트 세션",
            user_id=None
        )
        
        if result.get('success'):
            print(f"✅ 검증 성공! 세션 ID: {result['session_id']}")
            print(f"📊 검증 결과: {len(result['results'])}개")
            print(f"⏱️ 소요 시간: {result['duration']:.2f}초")
            
            # 결과 조회 테스트
            session_results = integrator.get_session_results(result['session_id'])
            if session_results and not session_results.get('error'):
                print(f"✅ 결과 조회 성공! DB에서 {len(session_results['results'])}개 결과 확인")
            else:
                print("❌ 결과 조회 실패")
                
            return result['session_id']
        else:
            print(f"❌ 검증 실패: {result.get('error', '알 수 없는 오류')}")
            return None
            
    except Exception as e:
        print(f"❌ 검증 통합 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_search_functionality():
    """검색 기능 테스트"""
    print("\n" + "=" * 50)
    print("🔍 검색 기능 테스트")
    print("=" * 50)
    
    try:
        from species_verifier.database.integration import get_verification_integrator
        from species_verifier.database.models import VerificationType
        
        integrator = get_verification_integrator()
        
        # 종 검색 테스트
        search_query = "Homo"
        print(f"🔎 검색어: '{search_query}'")
        
        search_results = integrator.search_previous_results(
            query=search_query,
            verification_type=VerificationType.MARINE
        )
        
        print(f"✅ 검색 성공! {len(search_results)}개 결과 발견")
        
        if search_results:
            for i, result in enumerate(search_results[:3], 1):  # 최대 3개만 표시
                print(f"  {i}. {result.get('scientific_name', 'N/A')} ({result.get('input_name', 'N/A')})")
        
        return True
        
    except Exception as e:
        print(f"❌ 검색 기능 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cache_functionality():
    """캐시 기능 테스트"""
    print("\n" + "=" * 50)
    print("⚡ 캐시 시스템 테스트")
    print("=" * 50)
    
    try:
        from species_verifier.database.cache_manager import get_cache_manager
        
        cache_manager = get_cache_manager("test_session")
        
        test_species = "Homo sapiens"
        test_db = "worms"
        test_data = {
            "scientific_name": test_species,
            "status": "accepted",
            "worms_id": "158852",
            "test_timestamp": datetime.now().isoformat()
        }
        
        print(f"🔄 캐시 테스트 데이터: {test_species}")
        
        # 1. 캐시 미스 테스트
        cached_data = cache_manager.get_cache(test_species, test_db)
        if cached_data is None:
            print("✅ 캐시 미스 정상 동작")
        
        # 2. 캐시 저장 테스트
        save_success = cache_manager.set_cache(test_species, test_db, test_data)
        if save_success:
            print("✅ 캐시 저장 성공")
        
        # 3. 캐시 히트 테스트
        cached_data = cache_manager.get_cache(test_species, test_db)
        if cached_data and cached_data.get("scientific_name") == test_species:
            print("✅ 캐시 히트 성공")
        
        # 4. 캐시 통계 테스트
        stats = cache_manager.get_cache_stats(days=1)
        if stats and 'hit_rate' in stats:
            print(f"✅ 캐시 통계 조회 성공 - 히트율: {stats['hit_rate']}%")
        
        # 5. 인기 검색어 테스트
        popular = cache_manager.get_popular_species(limit=3)
        print(f"✅ 인기 검색어 조회 성공 - {len(popular)}개 결과")
        
        return True
        
    except Exception as e:
        print(f"❌ 캐시 시스템 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_cleanup():
    """테스트 데이터 정리"""
    print("\n" + "=" * 50)
    print("🧹 테스트 데이터 정리")
    print("=" * 50)
    
    try:
        from species_verifier.database.supabase_client import get_supabase_client
        
        client = get_supabase_client()
        
        # 테스트 세션들 삭제 (세션명에 '테스트'가 포함된 것들)
        sessions_result = client.table("verification_sessions").select("id, session_name").like("session_name", "%테스트%").execute()
        
        if sessions_result.data:
            session_ids = [s["id"] for s in sessions_result.data]
            
            # 연관된 검증 결과들도 자동으로 삭제됨 (CASCADE)
            delete_result = client.table("verification_sessions").delete().in_("id", session_ids).execute()
            
            print(f"✅ {len(session_ids)}개 테스트 세션 정리 완료")
        else:
            print("ℹ️ 정리할 테스트 세션이 없습니다")
        
        # 테스트 캐시 데이터 정리
        try:
            test_cache_result = client.table("species_cache").select("id").eq("scientific_name", "Homo sapiens").execute()
            if test_cache_result.data:
                client.table("species_cache").delete().eq("scientific_name", "Homo sapiens").execute()
                print(f"✅ 테스트 캐시 데이터 정리 완료")
            
            # 테스트 세션 관련 캐시 로그 정리
            test_logs_result = client.table("cache_access_log").select("id").eq("user_session", "test_session").execute()
            if test_logs_result.data:
                client.table("cache_access_log").delete().eq("user_session", "test_session").execute()
                print(f"✅ 테스트 캐시 로그 정리 완료")
                
        except Exception as cache_cleanup_error:
            print(f"ℹ️ 캐시 테이블 정리 중 경고: {cache_cleanup_error}")
            
        return True
        
    except Exception as e:
        print(f"❌ 데이터 정리 중 오류 발생: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("🚀 Species Verifier - Supabase 통합 테스트 시작")
    print(f"📅 테스트 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 환경 변수 체크
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_ANON_KEY"):
        print("\n❌ 환경 변수가 설정되지 않았습니다!")
        print("📝 .env 파일에 다음 설정을 추가해주세요:")
        print("   SUPABASE_URL=https://your-project-id.supabase.co")
        print("   SUPABASE_ANON_KEY=your-anon-key-here")
        return
    
    test_results = []
    
    # 테스트 실행
    test_results.append(("기본 연결", test_basic_connection()))
    
    if test_results[-1][1]:  # 연결이 성공한 경우에만 계속
        test_results.append(("세션 생성", test_session_creation() is not None))
        test_results.append(("검증 통합", test_verification_integration() is not None))
        test_results.append(("검색 기능", test_search_functionality()))
        test_results.append(("캐시 시스템", test_cache_functionality()))
        test_results.append(("데이터 정리", test_database_cleanup()))
    
    # 결과 요약
    print("\n" + "=" * 50)
    print("📋 테스트 결과 요약")
    print("=" * 50)
    
    success_count = 0
    for test_name, success in test_results:
        status = "✅ 성공" if success else "❌ 실패"
        print(f"{test_name}: {status}")
        if success:
            success_count += 1
    
    print(f"\n🎯 전체 결과: {success_count}/{len(test_results)} 테스트 통과")
    
    if success_count == len(test_results):
        print("🎉 모든 테스트가 성공했습니다! Supabase 연동이 완료되었습니다.")
    else:
        print("⚠️ 일부 테스트가 실패했습니다. 설정을 확인해주세요.")
    
    print(f"\n📅 테스트 종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main() 