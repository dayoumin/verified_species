#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LPSN API 라이브러리 진단
"""

import os

def debug_lpsn_api():
    print("=== LPSN API 라이브러리 진단 ===")
    
    # 1. 환경변수 확인
    lpsn_email = os.environ.get('LPSN_EMAIL')
    lpsn_password = os.environ.get('LPSN_PASSWORD')
    
    print(f"1. 환경변수 확인:")
    print(f"   LPSN_EMAIL: {lpsn_email}")
    print(f"   LPSN_PASSWORD: {'설정됨' if lpsn_password else '없음'}")
    
    # 2. LPSN 라이브러리 import 테스트
    print(f"\n2. LPSN 라이브러리 import 테스트:")
    try:
        import lpsn
        print("   ✅ lpsn 라이브러리 import 성공")
        
        # 3. 클라이언트 생성 테스트
        print(f"\n3. 클라이언트 생성 테스트:")
        if lpsn_email and lpsn_password:
            try:
                client = lpsn.LpsnClient(lpsn_email, lpsn_password)
                print("   ✅ 클라이언트 생성 성공")
                
                # 4. 간단한 검색 테스트
                print(f"\n4. 간단한 검색 테스트:")
                try:
                    count = client.search(taxon_name="Escherichia coli", correct_name='yes')
                    print(f"   ✅ 검색 성공: {count}개 결과")
                    
                    if count > 0:
                        print("   첫 번째 결과:")
                        for i, entry in enumerate(client.retrieve()):
                            if i == 0:  # 첫 번째만
                                print(f"     이름: {entry.get('full_name', 'N/A')}")
                                print(f"     상태: {entry.get('lpsn_taxonomic_status', 'N/A')}")
                                break
                    
                except Exception as e:
                    print(f"   ❌ 검색 실패: {e}")
                
            except Exception as e:
                print(f"   ❌ 클라이언트 생성 실패: {e}")
        else:
            print("   ❌ 환경변수 없음")
            
    except ImportError as e:
        print(f"   ❌ lpsn 라이브러리 import 실패: {e}")
    except Exception as e:
        print(f"   ❌ 예상치 못한 오류: {e}")
    
    print(f"\n=== 진단 완료 ===")

if __name__ == "__main__":
    debug_lpsn_api() 