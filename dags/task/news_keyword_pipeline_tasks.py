import requests

from psycopg2.extras import execute_values

from core.config import settings
from core.database import DB_CONFIG
from core.database import get_db_connection

# -------------------------
# 키워드 분석 대상 뉴스 로드
# -------------------------
def fetch_keyword_data():
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
        LIMIT 30;
    """

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()

            result = []

            for r in rows:
                result.append({
                    "article_id": r[0],
                    "title": r[1],
                    "content": r[2]
                })

    return result

# -------------------------
# 뉴스 키워드 저장
# -------------------------
def store_news_keywords(**context):
    results = context["ti"].xcom_pull(task_ids="call_keyword_batch")

    if not results:
        return

    rows = []

    for r in results:
        if r.get("error"):
            continue

        article_id = r["article_id"]

        for keyword in r.get("keywords", []):
            if not keyword or not keyword.strip():
                continue

            rows.append((
                article_id,
                keyword.strip(),
                settings.MODEL_VERSION,
            ))

    if not rows:
        return

    with get_db_connection() as conn:
        try:
            with conn.cursor() as cur:
                if rows:
                    execute_values(
                        cur,
                        """
                        INSERT INTO news_keywords (
                            article_id,
                            keyword,
                            model_version
                        )
                        VALUES %s
                        ON CONFLICT (article_id, keyword)
                        DO NOTHING
                        """,
                        rows,
                        page_size=50,
                    )

            conn.commit()
        except Exception:
            conn.rollback()
            raise

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