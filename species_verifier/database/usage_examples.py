"""
Species Verifier 데이터베이스 시스템 사용 예시

이 파일은 새로운 기능들의 사용법을 보여줍니다:
1. 실시간 검증 결과와 캐시 비교 
2. 월간 자동 업데이트
3. 보안 모드 (LOCAL/HYBRID/CLOUD)
4. 데이터베이스별 분류 (해양생물→WoRMS, 미생물→LPSN, 담수생물→COL)
"""

# === 1. 실시간 검증 결과와 캐시 비교 예시 ===

def example_real_time_verification():
    """실시간 검증과 캐시 비교 업데이트 예시"""
    from .scheduler import get_cache_scheduler
    from ..core.verifier import check_worms_record
    
    scheduler = get_cache_scheduler()
    
    # 해양생물 실시간 검증 (캐시와 비교)
    species_name = "Gadus morhua"  # 대구
    
    print(f"=== {species_name} 실시간 검증 시작 ===")
    
    result = scheduler.verify_and_update_cache(
        scientific_name=species_name,
        source_db='worms',  # 해양생물 → WoRMS
        api_call_func=check_worms_record,
        force_update=False  # 캐시와 비교 후 필요시에만 업데이트
    )
    
    print(f"검증 결과: {result['status']}")
    if result['status'] == 'updated':
        print(f"데이터 변경 감지: {result.get('changes', [])}")
    elif result['status'] == 'cache_valid':
        print("캐시 데이터가 최신 상태입니다")
    
    return result

# === 2. 월간 업데이트 스케줄링 예시 ===

def example_monthly_update():
    """월간 정기 업데이트 예시"""
    from .scheduler import get_cache_scheduler
    
    scheduler = get_cache_scheduler()
    
    print("=== 월간 캐시 업데이트 시작 ===")
    
    # WoRMS (해양생물) 데이터만 업데이트
    worms_result = scheduler.schedule_monthly_update(
        target_db='worms',
        min_usage_count=3,  # 최소 3회 이상 사용된 종
        max_items_per_run=20  # 테스트용으로 20개만
    )
    
    print(f"WoRMS 업데이트 결과: {worms_result}")
    
    # LPSN (미생물) 데이터 업데이트
    lpsn_result = scheduler.schedule_monthly_update(
        target_db='lpsn',
        min_usage_count=3,
        max_items_per_run=15  # LPSN은 더 보수적으로
    )
    
    print(f"LPSN 업데이트 결과: {lpsn_result}")
    
    return {"worms": worms_result, "lpsn": lpsn_result}

# === 3. 보안 모드별 사용 예시 ===

def example_security_modes():
    """보안 모드별 사용법 예시"""
    import os
    from .secure_mode import SecureDatabaseManager
    
    print("=== 보안 모드 테스트 ===")
    
    # LOCAL 모드 (완전한 로컬 처리, 외부 연결 없음)
    local_db = SecureDatabaseManager(mode="local")
    print(f"LOCAL 모드 초기화: {local_db.mode}")
    
    # 캐시 저장/조회 (로컬 SQLite만 사용)
    test_data = {
        "scientific_name": "Escherichia coli",
        "status": "valid",
        "classification": ["Bacteria", "Proteobacteria", "Gammaproteobacteria"]
    }
    
    local_db.set_cache("Escherichia coli", "lpsn", test_data)
    cached = local_db.get_cache("Escherichia coli", "lpsn")
    
    print(f"로컬 캐시 테스트: {'성공' if cached else '실패'}")
    
    # HYBRID 모드 (로컬 우선 + 선택적 외부 연결)
    try:
        hybrid_db = SecureDatabaseManager(mode="hybrid")
        print(f"HYBRID 모드 초기화: {hybrid_db.mode}")
        
        # 하이브리드 모드는 로컬을 우선하되, 필요시 클라우드 연결
        hybrid_cached = hybrid_db.get_cache("Escherichia coli", "lpsn")
        print(f"하이브리드 캐시 테스트: {'성공' if hybrid_cached else '실패'}")
        
    except Exception as e:
        print(f"HYBRID 모드 테스트 실패 (외부 연결 없음): {e}")
    
    return local_db.get_cache_stats()

# === 4. 데이터베이스별 분류 사용 예시 ===

def example_database_classification():
    """데이터베이스별 분류 및 사용 예시"""
    from .scheduler import get_cache_scheduler
    
    scheduler = get_cache_scheduler()
    
    print("=== 데이터베이스별 분류 시스템 ===")
    
    # 분류 정보 확인
    schedule_info = scheduler.get_update_schedule_info()
    classifications = schedule_info['database_classifications']
    
    for species_type, database in classifications.items():
        print(f"{species_type}: {database}")
    
    # 실제 사용 예시
    species_examples = {
        "해양생물": ["Gadus morhua", "Thunnus thynnus"],      # → WoRMS
        "미생물": ["Escherichia coli", "Bacillus subtilis"],    # → LPSN
        # "담수생물": ["Salmo trutta", "Cyprinus carpio"],      # → COL (향후)
    }
    
    for category, species_list in species_examples.items():
        print(f"\n{category} 검증 예시:")
        
        for species in species_list:
            if category == "해양생물":
                source_db = "worms"
                print(f"  {species} → WoRMS 데이터베이스")
            elif category == "미생물":
                source_db = "lpsn" 
                print(f"  {species} → LPSN 데이터베이스")
            # elif category == "담수생물":
            #     source_db = "col"
            #     print(f"  {species} → COL 데이터베이스")
    
    return classifications

# === 5. 통합 사용 예시 ===

def example_integrated_workflow():
    """실제 워크플로우 통합 예시"""
    from .integration import get_verification_integrator
    
    print("=== 통합 워크플로우 테스트 ===")
    
    # 통합 시스템 초기화
    integrator = get_verification_integrator("demo_session")
    
    # 1. 해양생물 검증 (실시간 비교 포함)
    marine_species = ["Gadus morhua", "Salmo salar", "Thunnus thynnus"]
    
    marine_summary = integrator.verify_marine_species_with_cache(
        scientific_names=marine_species,
        session_name="Demo Marine Verification",
        use_real_time_validation=True  # 실시간 검증 활성화
    )
    
    print(f"해양생물 검증 결과: {marine_summary.verified_count}/{marine_summary.total_items}")
    
    # 2. 미생물 검증 (실시간 비교 포함)
    microbe_species = ["Escherichia coli", "Bacillus subtilis"]
    
    microbe_summary = integrator.verify_microbe_species_with_cache(
        scientific_names=microbe_species,
        session_name="Demo Microbe Verification", 
        use_real_time_validation=True
    )
    
    print(f"미생물 검증 결과: {microbe_summary.verified_count}/{microbe_summary.total_items}")
    
    # 3. 시스템 상태 확인
    system_status = integrator.get_integrated_system_status()
    print(f"시스템 모드: {system_status['system_mode']}")
    print(f"캐시 히트율: {system_status['performance_improvements']['cache_hit_rate']}%")
    
    return {
        "marine_summary": marine_summary,
        "microbe_summary": microbe_summary,
        "system_status": system_status
    }

# === 6. 기관 보안 환경 설정 예시 ===

def example_enterprise_security_setup():
    """기관 보안 환경 설정 예시"""
    import os
    
    print("=== 기관 보안 환경 설정 ===")
    
    # 환경 변수 설정 예시 (실제로는 .env 파일이나 시스템 환경변수로 설정)
    security_config = {
        # 데이터베이스 모드 설정
        "SPECIES_VERIFIER_DB_MODE": "local",  # local/hybrid/cloud
        
        # 기관 네트워크 여부
        "ENTERPRISE_NETWORK": "true",  # true/false
        
        # 로컬 캐시 경로 (선택사항)
        "SPECIES_CACHE_PATH": r"C:\ProgramData\SpeciesVerifier\cache",
        
        # Supabase 설정 (HYBRID/CLOUD 모드용)
        # "SUPABASE_URL": "https://your-project.supabase.co",
        # "SUPABASE_ANON_KEY": "your-anon-key"
    }
    
    print("권장 보안 설정:")
    for key, value in security_config.items():
        if not key.startswith("SUPABASE"):  # 보안상 Supabase 키는 출력 안 함
            print(f"  {key}={value}")
    
    # 보안 모드 확인
    from .secure_mode import get_secure_database_mode
    current_mode = get_secure_database_mode()
    print(f"\n현재 보안 모드: {current_mode.upper()}")
    
    # 보안 권장사항
    recommendations = {
        "LOCAL": [
            "✅ 외부 인터넷 연결 불필요",
            "✅ 모든 데이터 로컬 저장",
            "⚠️ 실시간 업데이트 제한됨",
            "⚠️ 초기 API 호출 필요"
        ],
        "HYBRID": [
            "✅ 로컬 우선 처리로 빠른 응답",
            "✅ 선택적 외부 연결로 보안성 확보",
            "✅ 실시간 업데이트 가능",
            "📋 방화벽에서 Supabase 도메인 허용 필요"
        ],
        "CLOUD": [
            "⚠️ 기관 네트워크에 권장하지 않음",
            "📋 모든 데이터가 외부 서버 경유",
            "📋 인터넷 연결 필수"
        ]
    }
    
    print(f"\n{current_mode.upper()} 모드 특징:")
    for rec in recommendations.get(current_mode.upper(), []):
        print(f"  {rec}")
    
    return {
        "current_mode": current_mode,
        "config": security_config,
        "recommendations": recommendations.get(current_mode.upper(), [])
    }

# === 실행 예시 ===
if __name__ == "__main__":
    print("Species Verifier 데이터베이스 시스템 사용 예시")
    print("=" * 50)
    
    # 1. 보안 모드 확인
    security_info = example_enterprise_security_setup()
    
    # 2. 데이터베이스 분류 확인
    classification_info = example_database_classification()
    
    # 3. 보안 모드별 테스트
    security_test = example_security_modes()
    
    print("\n모든 예시 실행 완료!")
    print(f"현재 보안 모드: {security_info['current_mode'].upper()}")
    print(f"로컬 캐시 항목 수: {security_test.get('total_cached', 0)}") 