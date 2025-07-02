#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LPSN API 연결 테스트
"""

import os

def test_lpsn_api():
    print("=== LPSN API 연결 테스트 ===")
    
    # 인증 정보 확인
    username = "fishnala@gmail.com"
    password = "2025lpsn"
    
    print(f"사용자명: {username}")
    print(f"비밀번호: {'*' * len(password)}")
    
    try:
        # LPSN 패키지 import
        import lpsn
        print("✅ lpsn 패키지 로드 성공")
        
        # 클라이언트 생성
        print("클라이언트 생성 중...")
        client = lpsn.LpsnClient(username, password)
        print("✅ 클라이언트 생성 성공")
        
        # 검색 테스트 목록
        test_names = [
            "Escherichia coli",
            "Bacillus subtilis", 
            "Staphylococcus aureus",
            "Pseudomonas aeruginosa"
        ]
        
        for test_name in test_names:
            print(f"\n--- 검색 테스트: {test_name} ---")
            
            # 올바른 search 메서드 사용법
            count = client.search(taxon_name=test_name, correct_name='yes')
            print(f"검색된 항목 수: {count}")
            
            if count > 0:
                print("결과 가져오는 중...")
                # retrieve 메서드로 결과 가져오기
                for i, entry in enumerate(client.retrieve()):
                    print(f"결과 {i+1}:")
                    if isinstance(entry, dict):
                        # 올바른 키로 주요 정보 출력
                        name = entry.get('full_name', 'N/A')
                        status = entry.get('lpsn_taxonomic_status', 'N/A')
                        print(f"  이름: {name}")
                        print(f"  상태: {status}")
                        if 'lpsn_address' in entry:
                            print(f"  LPSN URL: {entry['lpsn_address']}")
                        if 'is_legitimate' in entry:
                            print(f"  정당성: {entry['is_legitimate']}")
                    else:
                        print(f"  전체 결과: {entry}")
                    
                    # 첫 번째 결과만 자세히 출력
                    if i >= 2:  # 최대 3개만 출력
                        print(f"  ... (총 {count}개 결과)")
                        break
            else:
                print("❌ 검색 결과 없음")
                
        print("\n🎉 LPSN API 테스트 완료!")
        return True
        
    except ImportError as e:
        print(f"❌ lpsn 패키지 import 실패: {e}")
        return False
        
    except Exception as e:
        print(f"❌ LPSN API 연결 실패: {e}")
        print(f"오류 타입: {type(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_lpsn_api()
    if success:
        print("\n✅ 모든 테스트 통과!")
    else:
        print("\n❌ 테스트 실패") 