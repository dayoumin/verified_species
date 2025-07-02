#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LPSN subspecies 처리 문제 테스트
"""

import os
import sys

def test_subspecies_handling():
    print("=== LPSN subspecies 처리 테스트 ===")
    
    try:
        # Species Verifier 모듈 import
        sys.path.append('.')
        from species_verifier.core.verifier import verify_single_microbe_lpsn
        
        # 문제가 되는 학명들 테스트 (subspecies가 많은 경우)
        problematic_microbes = [
            "Salmonella enterica",  # 13개 결과 (species 1개 + subspecies 12개)
            "Mycobacterium tuberculosis",  # 4개 결과 (species 1개 + subspecies 3개)  
            "Bacillus subtilis",  # subspecies 있을 수 있음
            "Methanobrevibacter smithii",  # 단순한 경우 (정상 작동 예상)
        ]
        
        for microbe_name in problematic_microbes:
            print(f"\n{'='*50}")
            print(f"🧪 테스트: {microbe_name}")
            print(f"{'='*50}")
            
            try:
                result = verify_single_microbe_lpsn(microbe_name)
                
                print(f"✅ 검증 완료!")
                print(f"  입력명: {result.get('input_name')}")
                print(f"  결과 학명: {result.get('scientific_name')}")
                print(f"  검증 성공: {result.get('is_verified')}")
                print(f"  상태: {result.get('status')}")
                print(f"  분류: {result.get('taxonomy')}")
                print(f"  LPSN 링크: {result.get('lpsn_link')}")
                
            except Exception as e:
                print(f"❌ 오류 발생: {e}")
                import traceback
                traceback.print_exc()
                
        print(f"\n{'='*50}")
        print("🎉 subspecies 처리 테스트 완료!")
        print(f"{'='*50}")
        
    except Exception as e:
        print(f"❌ 전체 테스트 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_subspecies_handling() 