from dateutil import parser
from psycopg2.extras import execute_values

from core.database import DB_CONFIG
from core.database import get_db_connection

BATCH_SIZE = 50

# -------------------------
# 기사를 DB에 저장
# -------------------------
def store_articles(articles):
    if not articles:
        return []

    values = []

    for article in articles:
        pub_date = None

        if article.get("pub_date"):
            try:
                pub_date = parser.parse(article["pub_date"])
            except (ValueError, TypeError, OverflowError):
                pub_date = None

        values.append((
            article["title"],
            article["link"],
            pub_date,
            article["source"],
            article.get("content", ""),
        ))

    saved_articles = []

    with get_db_connection() as conn:
        try:
            with conn.cursor() as cur:
                execute_values(
                    cur,
                    """
                    INSERT INTO news_articles (
                        title,
                        link,
                        pub_date,
                        source,
                        content
                    )
                    VALUES %s
                    ON CONFLICT (link)
                    DO UPDATE SET
                        link = EXCLUDED.link
                    RETURNING id, title, link, source
                    """,
                    values,
                    page_size=BATCH_SIZE,
                )

                saved_articles = [
                    {
                        "id": row[0],
                        "title": row[1],
                        "link": row[2],
                        "source": row[3],
                    }
                    for row in cur.fetchall()
                ]

            conn.commit()
        except Exception:
            conn.rollback()
            raise

    return saved_articles

# -------------------------
# mention을 DB에 저장
# -------------------------
def store_company_mentions(data):
    if not data:
        return

    with get_db_connection() as conn:
        try:
            with conn.cursor() as cur:
                links = [
                    item.get("article", {}).get("link")
                    for item in data
                    if item.get("article", {}).get("link")
                ]

                if not links:
                    return

                cur.execute("""
                    SELECT id, link
                    FROM news_articles
                    WHERE link = ANY(%s)
                """, (list(set(links)),))

                link_map = {
                    link: article_id
                    for article_id, link in cur.fetchall()
                }

                values = []

                for item in data:
                    article = item.get("article", {})
                    link = article.get("link")

                    if not link:
                        continue

                    article_id = link_map.get(link)
                    if article_id is None:
                        continue

                    for match in item.get("matches", []):
                        values.append((
                            article_id,
                            match["company_id"],
                            match["score"],
                        ))

                if values:
                    execute_values(
                        cur,
                        """
                        INSERT INTO news_mentions (
                            article_id,
                            company_id,
                            confidence
                        )
                        VALUES %s
                        ON CONFLICT DO NOTHING
                        """,
                        values,
                        page_size=BATCH_SIZE,
                    )

            conn.commit()
        except Exception:
            conn.rollback()
            raise

# -------------------------
# DB에서 배치 별 기업 조회
# -------------------------
def get_articles_for_company_extraction(limit=BATCH_SIZE):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, title, link, content, source
                FROM news_articles
                WHERE content IS NOT NULL
                  AND company_extraction_processed = FALSE
                  AND created_at >= NOW() - INTERVAL '2 hours'
                  AND created_at <= NOW()
                ORDER BY id
                LIMIT %s
            """, (limit,))
            return [
                {
                    "id": row[0],
                    "title": row[1],
                    "link": row[2],
                    "content": row[3],
                    "source": row[4],
                }
                for row in cur.fetchall()
            ]

# -------------------------
# 기업 매칭 완료 처리
# -------------------------
def mark_articles_processed(article_ids):
    if not article_ids:
        return

    with get_db_connection() as conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE news_articles
                    SET company_extraction_processed = TRUE
                    WHERE id = ANY(%s)
                """, (article_ids,))

            conn.commit()
        except Exception:
            conn.rollback()
            raise