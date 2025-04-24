import requests

def verify_col_species(scientific_name: str):
    """
    COL 글로벌 API를 이용해 학명 검증 결과를 반환합니다.
    """
    url = "https://api.catalogueoflife.org/nameusage/search"
    params = {"name": scientific_name}
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("result"):
            match = data["result"][0]
            return {
                "query": scientific_name,
                "matched": True,
                "acceptedName": match.get("scientificName"),
                "rank": match.get("rank"),
                "status": match.get("status"),
                "kingdom": match.get("kingdom"),
                "phylum": match.get("phylum"),
                "class": match.get("class"),
                "order": match.get("order"),
                "family": match.get("family"),
                "genus": match.get("genus"),
                "col_id": match.get("id"),
            }
        else:
            return {"query": scientific_name, "matched": False}
    except Exception as e:
        return {"query": scientific_name, "matched": False, "error": str(e)}
