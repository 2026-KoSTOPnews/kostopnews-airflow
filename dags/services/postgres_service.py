from dateutil import parser
import psycopg2

from core.database import DB_CONFIG

BATCH_SIZE = 50

# -------------------------
# 기사를 DB에 저장
# -------------------------
def store_articles(articles):
    if not articles:
        return []

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    saved_articles = []

    for a in articles:
        pub_date = None

        if a.get("pub_date"):
            try:
                pub_date = parser.parse(a["pub_date"])
            except Exception:
                pub_date = None

        cur.execute("""
        INSERT INTO news_articles (
            title,
            link,
            pub_date,
            source,
            content
        )
        VALUES (%s,%s,%s,%s,%s)
        ON CONFLICT (link)
        DO UPDATE SET
            link = EXCLUDED.link
        RETURNING id
        """, (
            a["title"],
            a["link"],
            pub_date,
            a["source"],
            a.get("content", "")
        ))

        article_id = cur.fetchone()[0]

        saved_articles.append({
            "id": article_id,
            "title": a["title"],
            "link": a["link"],
            "source": a["source"]
        })

    conn.commit()
    cur.close()
    conn.close()

    return saved_articles

# -------------------------
# mention을 DB에 저장
# -------------------------
def store_company_mentions(data):
    if not data:
        return

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    links = []

    for item in data:
        article = item.get("article", {})
        link = article.get("link")
        if link:
            links.append(link)

    if not links:
        return

    cur.execute("""
        SELECT id, link
        FROM news_articles
        WHERE link = ANY(%s)
    """, (links,))

    link_map = {link: id for id, link in cur.fetchall()}

    for item in data:
        article = item.get("article", {})
        link = article.get("link")

        if not link:
            continue

        matches = item.get("matches", [])
        if not matches:
            continue

        article_id = link_map.get(link)
        if not article_id:
            continue

        for m in matches:
            cur.execute("""
                INSERT INTO news_mentions (
                    article_id,
                    company_id,
                    confidence
                )
                VALUES (%s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (
                article_id,
                m["company_id"],
                m["score"]
            ))

    conn.commit()
    cur.close()
    conn.close()

# -------------------------
# DB에서 배치 별 기업 조회
# -------------------------
def get_articles_for_company_extraction(limit=BATCH_SIZE, offset=0):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT
                id,
                title,
                link,
                content,
                source
            FROM news_articles
            WHERE content IS NOT NULL
            ORDER BY id
            LIMIT %s
            OFFSET %s
        """, (limit, offset))

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
    finally:
        cur.close()
        conn.close()