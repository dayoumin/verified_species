#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LPSN 라이브러리 메서드 탐색
"""

def test_lpsn_methods():
    print("=== LPSN 라이브러리 메서드 탐색 ===")
    
    try:
        import lpsn
        print("✅ lpsn 패키지 로드 성공")
        
        # 클라이언트 생성
        client = lpsn.LpsnClient("fishnala@gmail.com", "2025lpsn")
        print("✅ 클라이언트 생성 성공")
        
        # 클라이언트의 모든 메서드 확인
        print("\n--- 클라이언트 메서드 목록 ---")
        methods = [method for method in dir(client) if not method.startswith('_')]
        for method in methods:
            print(f"  {method}")
        
        # search 메서드의 도움말 확인
        print("\n--- search 메서드 정보 ---")
        try:
            print(f"search 메서드: {client.search}")
            print(f"search.__doc__: {client.search.__doc__}")
        except Exception as e:
            print(f"search 메서드 정보 확인 실패: {e}")
        
        # 여러 방법으로 검색 시도
        test_name = "Escherichia coli"
        print(f"\n--- {test_name} 검색 테스트 ---")
        
        # 방법 1: 원래 방법
        try:
            print("방법 1: search(taxon_name='name', correct_name='yes')")
            count = client.search(taxon_name=test_name, correct_name='yes')
            print(f"✅ 성공! 결과 수: {count}")
            
            if count > 0:
                print("결과 가져오기:")
                for i, entry in enumerate(client.retrieve()):
                    print(f"항목 {i+1}:")
                    print(f"  타입: {type(entry)}")
                    print(f"  내용: {entry}")
                    if isinstance(entry, dict):
                        print("  딕셔너리 키들:")
                        for key in entry.keys():
                            print(f"    {key}: {entry[key]}")
                    if i >= 2:  # 최대 3개만
                        break
        except Exception as e:
            print(f"❌ 방법 1 실패: {e}")
        
        # 방법 2: 키워드 없이
        try:
            print("\n방법 2: search(taxon_name='name')")
            count = client.search(taxon_name=test_name)
            print(f"✅ 성공! 결과 수: {count}")
        except Exception as e:
            print(f"❌ 방법 2 실패: {e}")
        
        # 방법 3: 단순한 매개변수
        try:
            print("\n방법 3: search('name')")
            count = client.search(test_name)
            print(f"✅ 성공! 결과 수: {count}")
        except Exception as e:
            print(f"❌ 방법 3 실패: {e}")
            
        print("\n🎉 메서드 탐색 완료!")
        return True
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_lpsn_methods() 