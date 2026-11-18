from collections import Counter, defaultdict
from datetime import date
import re

from kiwipiepy import Kiwi
from psycopg2.extras import execute_values

from core.database import get_db_connection
from core.keywords import STOPWORDS

TARGET_POS = {"NNG", "NNP", "SL"}

# -------------------------
# 뉴스 데이터 조회
# -------------------------
def fetch_word_data(target_date: date):
    query = """
        SELECT
            a.id AS article_id,
            m.company_id,
            c.name AS company_name,
            a.title,
            a.content
        FROM news_articles a
        JOIN news_mentions m
            ON a.id = m.article_id
        JOIN companies c
            ON m.company_id = c.id
        WHERE (a.pub_date AT TIME ZONE 'Asia/Seoul')::date = %s
          AND a.title IS NOT NULL
          AND a.title <> ''
        ORDER BY a.id, m.company_id;
    """

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (target_date,))
            rows = cur.fetchall()

    word_data = [
        {
            "article_id": article_id,
            "company_id": company_id,
            "company_name": company_name,
            "title": title,
            "content": content,
        }
        for article_id, company_id, company_name, title, content in rows
    ]

    return word_data

# -------------------------
# 뉴스 텍스트 단어 추출
# -------------------------
def extract_words(kiwi: Kiwi, text: str):
    if not text:
        return []

    text = re.sub(r"[^가-힣a-zA-Z0-9\s]", " ", text)

    tokens = kiwi.tokenize(text)

    words = []

    for token in tokens:
        word = token.form.strip().lower()

        if token.tag not in TARGET_POS:
            continue

        if word in STOPWORDS:
            continue

        if len(word) < 2:
            continue

        if word.isdigit():
            continue

        words.append(word)

    return words

# -------------------------
# 기업별 단어 빈도 집계
# -------------------------
def aggregate_words(word_data, kiwi: Kiwi):
    title_counters = defaultdict(Counter)
    content_counters = defaultdict(Counter)

    for item in word_data:
        company_id = item["company_id"]

        title = item["title"] or ""
        content = item["content"] or ""

        # 제목 기준 단어 추출
        title_words = extract_words(kiwi, title)

        # 제목 + 본문 기준 단어 추출
        content_text = f"{title} {content}"
        content_words = extract_words(kiwi, content_text)

        title_counters[company_id].update(title_words)
        content_counters[company_id].update(content_words)

    return {
        "title": title_counters,
        "content": content_counters,
    }

# -------------------------
# 단어 집계 결과 저장
# -------------------------
def store_word_aggregate(target_date: date, word_counters):
    values = []

    for text_type, company_counters in word_counters.items():
        for company_id, counter in company_counters.items():
            for word, count in counter.items():
                values.append((
                    company_id,
                    target_date,
                    text_type,
                    word,
                    count,
                ))

    with get_db_connection() as conn:
        try:
            with conn.cursor() as cur:
                # 해당 날짜의 기존 집계 삭제
                cur.execute(
                    """
                    DELETE FROM news_word_aggregate
                    WHERE period_start = %s
                    """,
                    (target_date,),
                )

                # 새로운 집계 결과 저장
                if values:
                    execute_values(
                        cur,
                        """
                        INSERT INTO news_word_aggregate (
                            company_id,
                            period_start,
                            text_type,
                            word,
                            count,
                            created_at,
                            updated_at
                        )
                        VALUES %s
                        """,
                        values,
                        template="(%s, %s, %s, %s, %s, NOW(), NOW())",
                        page_size=1000,
                    )

            conn.commit()

        except Exception:
            conn.rollback()
            raise

    return len(values)

# -------------------------
# 일간 단어 집계
# -------------------------
def process_daily_word_aggregate(target_date: date):
    kiwi = Kiwi()

    # 1. 뉴스 데이터 조회
    word_data = fetch_word_data(target_date)

    if not word_data:
        # 뉴스가 없는 날짜도 기존 집계 결과 제거
        store_word_aggregate(
            target_date,
            {
                "title": {},
                "content": {},
            },
        )

        return {
            "date": str(target_date),
            "article_count": 0,
            "company_count": 0,
            "title_word_count": 0,
            "content_word_count": 0,
        }

    # 2. 제목 및 제목+본문 단어 빈도 계산
    word_counters = aggregate_words(word_data, kiwi)

    # 3. DB 저장
    saved_count = store_word_aggregate(
        target_date,
        word_counters,
    )

    result = {
        "date": str(target_date),
        "article_count": len(set(
            item["article_id"] for item in word_data
        )),
        "company_count": len(set(
            item["company_id"] for item in word_data
        )),
        "title_word_count": sum(
            len(counter)
            for counter in word_counters["title"].values()
        ),
        "content_word_count": sum(
            len(counter)
            for counter in word_counters["content"].values()
        ),
        "saved_count": saved_count,
    }

    return result