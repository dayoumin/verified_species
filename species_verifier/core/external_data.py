import wikipediaapi
from .gemini_api import format_worms_result_with_gemini

def get_wikipedia_summary(scientific_name, lang='en'):
    """위키피디아에서 학명에 대한 요약 정보를 가져옵니다."""
    wiki = wikipediaapi.Wikipedia(lang)
    page = wiki.page(scientific_name)
    if page.exists():
        return page.summary
    return None

def enrich_with_wikipedia(species_data):
    """Gemini를 사용해 위키피디아 정보를 한국어로 요약하여 추가합니다."""
    summary = get_wikipedia_summary(species_data.get('valid_name'))
    if summary:
        prompt = f"""다음 영문 위키피디아 요약을 한국어로 번역하고 주요 정보를 추출해주세요:
{summary}

결과는 다음 형식의 JSON으로 반환:
{{
  "korean_summary": "한국어 요약",
  "key_facts": ["사실1", "사실2", "사실3"] 
}}"""
        gemini_result = format_worms_result_with_gemini(prompt, {})
        species_data.update({
            "wikipedia_summary": gemini_result.get("raw_gemini_response", ""),
            "korean_summary": gemini_result.get("gemini_conclusion", "")
        })
    return species_data