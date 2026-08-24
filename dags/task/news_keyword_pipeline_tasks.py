import psycopg2
import requests

from core.config import settings
from core.database import DB_CONFIG

# -------------------------
# 키워드 분석 대상 뉴스 로드
# -------------------------
def fetch_keyword_data(**context):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    query = """
        SELECT
            a.id AS article_id,
            a.title,
            a.content
        FROM news_articles a
        WHERE EXISTS (
            SELECT 1
            FROM news_analysis na
            WHERE na.article_id = a.id
        )
        AND NOT EXISTS (
            SELECT 1
            FROM news_keywords nk
            WHERE nk.article_id = a.id
        )
        LIMIT 10;
    """

    cur.execute(query)
    rows = cur.fetchall()

    result = []

    for r in rows:
        result.append({
            "article_id": r[0],
            "title": r[1],
            "content": r[2]
        })

    cur.close()
    conn.close()

    return result

# -------------------------
# 뉴스 키워드 저장
# -------------------------
def store_news_keywords(**context):
    results = context["ti"].xcom_pull(task_ids="call_keyword_batch")

    if not results:
        return

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    for r in results:
        if r.get("error"):
            continue

        article_id = r["article_id"]
        keywords = r.get("keywords", [])

        for keyword in keywords:

            if not keyword:
                continue

            cur.execute("""
                INSERT INTO news_keywords (
                    article_id,
                    keyword,
                    model_version
                )
                VALUES (%s, %s, %s)
                ON CONFLICT (article_id, keyword)
                DO NOTHING
            """, (
                article_id,
                keyword.strip(),
                settings.MODEL_VERSION,
            ))

    conn.commit()
    cur.close()
    conn.close()

# -------------------------
# 뉴스 배치 단위 키워드 추출
# -------------------------
def call_keyword_batch(**context):
    data = context["ti"].xcom_pull(task_ids="fetch_keyword_data")

    if not data:
        return []

    res = requests.post(
        f"{settings.FASTAPI_BASE_URL}/keywords/batch",
        json=data,
        timeout=600
    )

    res.raise_for_status()

    return res.json()