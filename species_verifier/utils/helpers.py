# species_verifier/utils/helpers.py

"""Utility functions used across the application."""

# Imports will be added later 

import re

def clean_scientific_name(input_name):
    """학명 또는 국명에서 불필요한 특수문자를 제거하고 공백을 정리합니다."""
    if not input_name or not isinstance(input_name, str):
        return input_name

    # 제거할 특수문자 목록 (한글/학명 공용)
    chars_to_remove = r"[',*#\"\\\[\\\]\\\{\}]"
    # 정규식을 사용하여 특수문자 제거
    cleaned_name = re.sub(chars_to_remove, '', input_name)
    # 연속된 공백을 단일 공백으로 치환
    cleaned_name = re.sub(r'\s+', ' ', cleaned_name).strip()
    # 원본과 달라졌다면 로그 출력 (로깅은 호출하는 쪽에서 처리하는 것이 좋을 수 있음)
    # if cleaned_name != input_name:
    #     print(f"[Info] 입력 정리: '{input_name}' -> '{cleaned_name}'")
    return cleaned_name

def create_basic_marine_result(input_name, scientific_name, is_verified, worms_status):
    """기본적인 해양생물 결과 딕셔너리를 생성합니다."""
    return {
        'input_name': input_name,
        'scientific_name': scientific_name,
        'mapped_name': scientific_name,  # 기본적으로 동일
        'is_verified': is_verified,
        'worms_status': worms_status,
        'worms_id': '-',
        'worms_url': '-',
        'wiki_summary': '-' # 위키 요약은 별도 함수에서 채워짐
    }

def get_default_taxonomy(microbe_name):
    """미생물 학명에 대한 기본 분류 정보를 반환합니다. (샘플 데이터 기반)
    향후에는 더 정확한 데이터 소스나 로직으로 대체될 수 있습니다.
    """
    # 학명별 분류 정보 (샘플)
    taxonomy_info = {
        "Vibrio parahaemolyticus": "Domain: Bacteria > Phylum: Proteobacteria > Class: Gammaproteobacteria > Order: Vibrionales > Family: Vibrionaceae",
        "Listeria monocytogenes": "Domain: Bacteria > Phylum: Firmicutes > Class: Bacilli > Order: Bacillales > Family: Listeriaceae",
        "Salmonella enterica": "Domain: Bacteria > Phylum: Proteobacteria > Class: Gammaproteobacteria > Order: Enterobacterales > Family: Enterobacteriaceae",
        "Aeromonas hydrophila": "Domain: Bacteria > Phylum: Proteobacteria > Class: Gammaproteobacteria > Order: Aeromonadales > Family: Aeromonadaceae",
        "Clostridium botulinum": "Domain: Bacteria > Phylum: Firmicutes > Class: Clostridia > Order: Clostridiales > Family: Clostridiaceae",
        "Escherichia coli": "Domain: Bacteria > Phylum: Proteobacteria > Class: Gammaproteobacteria > Order: Enterobacterales > Family: Enterobacteriaceae"
    }

    # 속명 기반 분류 정보 (정확한 종명이 없을 때 사용)
    genus_taxonomy = {
        "Vibrio": "Domain: Bacteria > Phylum: Proteobacteria > Class: Gammaproteobacteria > Order: Vibrionales > Family: Vibrionaceae",
        "Listeria": "Domain: Bacteria > Phylum: Firmicutes > Class: Bacilli > Order: Bacillales > Family: Listeriaceae",
        "Salmonella": "Domain: Bacteria > Phylum: Proteobacteria > Class: Gammaproteobacteria > Order: Enterobacterales > Family: Enterobacteriaceae",
        "Aeromonas": "Domain: Bacteria > Phylum: Proteobacteria > Class: Gammaproteobacteria > Order: Aeromonadales > Family: Aeromonadaceae",
        "Clostridium": "Domain: Bacteria > Phylum: Firmicutes > Class: Clostridia > Order: Clostridiales > Family: Clostridiaceae",
        "Escherichia": "Domain: Bacteria > Phylum: Proteobacteria > Class: Gammaproteobacteria > Order: Enterobacterales > Family: Enterobacteriaceae",
        "Bacillus": "Domain: Bacteria > Phylum: Firmicutes > Class: Bacilli > Order: Bacillales > Family: Bacillaceae",
        "Pseudomonas": "Domain: Bacteria > Phylum: Proteobacteria > Class: Gammaproteobacteria > Order: Pseudomonadales > Family: Pseudomonadaceae",
        "Staphylococcus": "Domain: Bacteria > Phylum: Firmicutes > Class: Bacilli > Order: Bacillales > Family: Staphylococcaceae",
        "Streptococcus": "Domain: Bacteria > Phylum: Firmicutes > Class: Bacilli > Order: Lactobacillales > Family: Streptococcaceae",
        "Lactobacillus": "Domain: Bacteria > Phylum: Firmicutes > Class: Bacilli > Order: Lactobacillales > Family: Lactobacillaceae"
    }

    # 전체 학명이 매핑에 있는지 확인
    if microbe_name in taxonomy_info:
        return taxonomy_info[microbe_name]

    # 속명만 추출하여 매핑 확인
    parts = microbe_name.split()
    if len(parts) > 0 and parts[0] in genus_taxonomy:
        return genus_taxonomy[parts[0]]

    # 기본 분류 제공
    return "Domain: Bacteria"

def create_basic_microbe_result(input_name, valid_name, status, taxonomy, link, wiki_summary='-'):
    """기본적인 미생물 결과 딕셔너리를 생성합니다."""
    # 분류 정보가 불완전한 경우 기본 분류 정보로 대체
    if not taxonomy or taxonomy in ["조회실패", "조회 실패", "-", ""] or "실패" in taxonomy:
        taxonomy = get_default_taxonomy(input_name)

    return {
        'input_name': input_name,
        'valid_name': valid_name,
        'status': status,
        'taxonomy': taxonomy,
        'lpsn_link': link,
        'wiki_summary': wiki_summary # 위키 요약은 별도 함수에서 채워짐
    }

def is_korean(char):
    """주어진 문자가 한글 유니코드 범위 내에 있는지 확인합니다."""
    return '\uAC00' <= char <= '\uD7A3' or '\u1100' <= char <= '\u11FF' or '\u3130' <= char <= '\u318F' 