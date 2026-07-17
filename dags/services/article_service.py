from typing import Dict, List
from rapidfuzz import fuzz

from utils.text_cleaner import normalize_title
from core.keywords import ECONOMY_KEYWORDS

# -------------------------
# 중복 제거 + 키워드 필터
# -------------------------
def deduplicate_articles(**context):
    ti = context["ti"]

    articles = ti.xcom_pull(task_ids="fetch_rss")
    companies = ti.xcom_pull(task_ids="load_companies")

    if not articles:
        return []

    company_keywords = [
        alias
        for aliases in companies.values()
        for alias in aliases
    ]

    # 1. 제목 정규화
    for article in articles:
        article["title"] = normalize_title(
            article.get("title", "")
        )

    # 2. 링크 중복 제거
    articles = remove_duplicate_links(articles)

    # 3. 키워드 필터
    articles = filter_articles(
        articles,
        company_keywords
    )

    # 4. 제목 유사도 제거
    articles = remove_similar_titles(articles)

    return articles

# -------------------------
# 링크 중복 제거
# -------------------------
def remove_duplicate_links(articles: List[Dict]) -> List[Dict]:
    seen = set()
    unique = []

    for article in articles:
        if article["link"] in seen:
            continue

        seen.add(article["link"])
        unique.append(article)

    return unique

# -------------------------
# 키워드 필터
# -------------------------
def filter_articles(articles: List[Dict], company_keywords: List[Dict]) -> List[Dict]:
    filtered = []

    for article in articles:
        title = article["title"]

        is_company_related = any(
            kw in title
            for kw in company_keywords
        )

        is_economy_related = any(
            kw in title
            for kw in ECONOMY_KEYWORDS
        )

        if is_company_related or is_economy_related:
            filtered.append(article)

    return filtered

# -------------------------
# 제목 유사도 제거
# -------------------------
def remove_similar_titles(articles: List[Dict], threshold: int = 90) -> List[Dict]:
    unique_articles = []

    for article in articles:
        is_duplicate = False

        for saved in unique_articles:
            score = fuzz.ratio(
                article["title"],
                saved["title"]
            )

            if score >= threshold:
                is_duplicate = True
                break

        if not is_duplicate:
            unique_articles.append(article)

    return unique_articles