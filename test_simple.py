import sys
import os
import traceback

# 프로젝트 루트 디렉토리를 sys.path에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 필요한 모듈 가져오기
from species_verifier.core.verifier import verify_single_microbe_lpsn

def test_lpsn():
    """LPSN 검증 테스트"""
    try:
        result = verify_single_microbe_lpsn("Streptococcus parauberis")
        print("검증 결과:", result)
        print("검증 성공 여부:", result['is_verified'])
        print("상태:", result['status'])
        print("유효 학명:", result['valid_name'])
    except Exception as e:
        print(f"오류 발생: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_lpsn()
