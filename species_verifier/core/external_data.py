import wikipediaapi
import requests
import urllib3
from .gemini_api import format_worms_result_with_gemini

# SSL 경고 관리 (보안 강화)
try:
    from species_verifier.config import SSL_CONFIG
    if SSL_CONFIG.get("allow_insecure_fallback", False):
        # 기업 환경 지원이 활성화된 경우에만 경고 비활성화
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        print("[Info] 🔒 Wikipedia 모듈 - 기업 네트워크 환경 지원")
except ImportError:
    # 설정 파일이 없는 경우 기본 동작
    pass

def get_wikipedia_summary(scientific_name, lang='en'):
    """위키피디아에서 학명에 대한 요약 정보를 가져옵니다. (보안 강화)"""
    try:
        from species_verifier.config import SSL_CONFIG
        
        # SSL 설정 (보안 우선)
        ssl_configs = [
            {'verify': True, 'description': 'SSL 검증 활성화'}
        ]
        
        # 기업 환경 지원이 활성화된 경우에만 SSL 우회 추가
        if SSL_CONFIG.get("allow_insecure_fallback", False):
            ssl_configs.append({
                'verify': False, 
                'description': 'SSL 검증 우회 (기업 환경)'
            })
        
        for ssl_config in ssl_configs:
            try:
                # SSL 우회 사용 시 로깅
                if not ssl_config['verify'] and SSL_CONFIG.get("log_ssl_bypass", True):
                    print(f"[Warning] ⚠️ Wikipedia API - SSL 검증 우회 사용 중")
                
                # wikipediaapi에 SSL 설정 적용
                wiki = wikipediaapi.Wikipedia(
                    language=lang,
                    user_agent='SpeciesVerifier/1.0'
                )
                
                # 세션 설정 적용
                if hasattr(wiki, 'session'):
                    wiki.session.verify = ssl_config['verify']
                
                page = wiki.page(scientific_name)
                if page.exists():
                    # 성공 로깅
                    if ssl_config['verify']:
                        print(f"[Debug] ✅ Wikipedia 보안 연결 성공")
                    else:
                        print(f"[Info] ⚠️ Wikipedia SSL 우회로 연결 성공")
                    return page.summary
                return None
                
            except requests.exceptions.SSLError:
                print(f"[Debug] Wikipedia SSL 오류: {ssl_config['description']}")
                if ssl_config['verify']:
                    continue  # SSL 검증 실패시 다음 설정으로 시도
                else:
                    raise  # SSL 우회도 실패하면 예외 발생
            except Exception as e:
                print(f"[Debug] Wikipedia 연결 오류: {ssl_config['description']} - {type(e).__name__}")
                if ssl_config['verify']:
                    continue  # 기타 오류시 다음 설정으로 시도
                else:
                    raise  # SSL 우회도 실패하면 예외 발생
                    
    except Exception as e:
        print(f"[Error Wikipedia] 모든 보안 연결 방법 실패: {e}")
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