from typing import List

import psycopg2

from core.database import DB_CONFIG

# -------------------------
# DB에 저장된 기업 로드
# -------------------------
def load_companies(**context):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute("""
    SELECT id, name, aliases
    FROM companies
    """)

    companies = {}

    for cid, name, aliases in cur.fetchall():
        companies[name] = {
            "id": cid,
            "aliases": aliases or [name]
        }

    cur.close()
    conn.close()

    return companies

# -------------------------
# 뉴스 기사  & 기업 매칭
# -------------------------
def extract_companies(**context):
    ti = context["ti"]

    articles = ti.xcom_pull(task_ids="fetch_article_content")
    companies = ti.xcom_pull(task_ids="load_companies")

    if not articles:
        return []

    results = []

    for article in articles:
        text = (article["title"] + " " + article.get("content", "")).lower()

        matches = []

        for company_name, info in companies.items():

            score = calculate_company_score(
                text=text,
                aliases=info["aliases"]
            )

            if score > 0.5:
                matches.append({
                    "company_id": info["id"],
                    "score": score
                })

        results.append({
            "article": {
                "title": article["title"],
                "link": article["link"],
                "content": article.get("content", ""),
                "source": article.get("source")
            },
            "matches": matches
        })

    return results

# -------------------------
# 기사와 기업의 연관도 계산
# -------------------------
def calculate_company_score(text: str, aliases: List[str]) -> float:
    score = 0.0

    text = text.lower()

    # alias matching
    for alias in aliases:
        if alias.lower() in text:
            score += 0.6

    # keyword boost
    if any(k in text for k in ["실적", "투자", "증설", "계약"]):
        score += 0.2
    if any(k in text for k in ["주가", "급등", "급락", "상승", "하락"]):
        score += 0.2

    return min(score, 1.0)