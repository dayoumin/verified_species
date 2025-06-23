import sys
import os
import traceback
import time

# 프로젝트 루트 디렉토리를 sys.path에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 필요한 모듈 가져오기
from species_verifier.core.verifier import verify_single_microbe_lpsn

def test_lpsn():
    """LPSN 검증 테스트 - 최소 버전"""
    try:
        print("===== LPSN 검증 테스트 시작 =====")
        print("테스트 종: Streptococcus parauberis")
        
        # 타임아웃 설정
        start_time = time.time()
        timeout = 30  # 30초 타임아웃
        
        result = None
        while time.time() - start_time < timeout:
            try:
                result = verify_single_microbe_lpsn("Streptococcus parauberis")
                break
            except Exception as e:
                print(f"시도 중 오류: {e}")
                time.sleep(1)
        
        if result:
            print("\n검증 결과 요약:")
            print(f"검증 성공 여부: {'성공' if result['is_verified'] else '실패'}")
            print(f"상태: {result['status']}")
            print(f"유효 학명: {result['valid_name']}")
            print(f"분류체계: {result['taxonomy']}")
            print(f"LPSN 링크: {result['lpsn_link']}")
        else:
            print("타임아웃 또는 모든 시도 실패")
            
        print("===== LPSN 검증 테스트 완료 =====")
    except Exception as e:
        print(f"테스트 실행 중 오류 발생: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_lpsn()
