#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
실제 미생물 검증 프로세스 테스트
"""

import os
import sys

def test_single_microbe_verification():
    print("=== 실제 미생물 검증 프로세스 테스트 ===")
    
    # 환경변수 확인
    lpsn_email = os.getenv("LPSN_EMAIL")
    lpsn_password = os.getenv("LPSN_PASSWORD")
    
    print(f"LPSN_EMAIL: {lpsn_email}")
    print(f"LPSN_PASSWORD: {'설정됨' if lpsn_password else '없음'}")
    
    try:
        # Species Verifier 모듈 import
        sys.path.append('.')
        from species_verifier.core.verifier import verify_single_microbe_lpsn
        
        # 테스트할 미생물 목록
        test_microbes = [
            "Mycobacterium tuberculosis",
            "Escherichia coli", 
            "Bacillus subtilis",
            "잘못된학명"
        ]
        
        for microbe_name in test_microbes:
            print(f"\n--- {microbe_name} 검증 테스트 ---")
            
            try:
                result = verify_single_microbe_lpsn(microbe_name)
                
                print(f"입력명: {result.get('input_name', 'N/A')}")
                print(f"학명: {result.get('scientific_name', 'N/A')}")
                print(f"검증 결과: {result.get('is_verified', 'N/A')}")
                print(f"상태: {result.get('status', 'N/A')}")
                print(f"LPSN 링크: {result.get('lpsn_link', 'N/A')}")
                
                if result.get('is_verified'):
                    print("✅ 검증 성공!")
                else:
                    print("❌ 검증 실패")
                    
            except Exception as e:
                print(f"❌ 오류 발생: {e}")
                import traceback
                traceback.print_exc()
                
        print("\n🎉 테스트 완료!")
        
    except ImportError as e:
        print(f"❌ 모듈 import 실패: {e}")
        
    except Exception as e:
        print(f"❌ 전체 테스트 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_single_microbe_verification() 