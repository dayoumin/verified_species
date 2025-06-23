import sys
import os

# 프로젝트 루트 디렉토리를 sys.path에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from species_verifier.core.verifier import verify_single_microbe_lpsn

def test_lpsn_verification():
    """LPSN 검증 로직 테스트"""
    test_species = [
        "Streptococcus parauberis",
        "Escherichia coli",
        "Bacillus subtilis",
        "Lactobacillus acidophilus"
    ]
    
    print("===== LPSN 검증 테스트 시작 =====")
    for species in test_species:
        print(f"\n테스트 종: {species}")
        result = verify_single_microbe_lpsn(species)
        print(f"검증 결과: {'성공' if result['is_verified'] else '실패'}")
        print(f"상태: {result['status']}")
        print(f"유효 학명: {result['valid_name']}")
        print(f"분류체계: {result['taxonomy']}")
        print(f"LPSN 링크: {result['lpsn_link']}")
        print("-" * 50)
    
    print("\n===== LPSN 검증 테스트 완료 =====")

if __name__ == "__main__":
    test_lpsn_verification()
