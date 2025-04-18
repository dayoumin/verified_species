from datetime import datetime
from ..core.supabase_cache import supabase, upsert_wiki_data, WORMS_TABLE
from ..core.external_data import get_wikipedia_summary
import time

def update_wikipedia_info():
    """Supabase에 저장된 모든 학명을 순회하며 Wikipedia 정보 업데이트"""
    if not supabase:
        print("Supabase 연결 실패")
        return

    # WoRMS 테이블에서 모든 학명 가져오기
    response = supabase.table(WORMS_TABLE).select("input_name").execute()
    all_species = [record['input_name'] for record in response.data]

    print(f"총 {len(all_species)}개의 학명에 대한 Wikipedia 정보 업데이트 시작...")

    for idx, species in enumerate(all_species, 1):
        try:
            print(f"{idx}/{len(all_species)} 처리 중: {species}")
            # Wikipedia 요약 정보 가져오기
            summary = get_wikipedia_summary(species)
            if summary:
                # Supabase에 저장
                upsert_wiki_data(species, summary)
            time.sleep(1)  # Wikipedia API 호출 간격 제한
        except Exception as e:
            print(f"{species} 처리 중 오류 발생: {e}")

    print("Wikipedia 정보 업데이트 완료")

if __name__ == "__main__":
    update_wikipedia_info()