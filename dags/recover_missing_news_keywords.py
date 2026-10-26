from datetime import timedelta

import pendulum
import requests
from airflow import DAG
from airflow.operators.python import PythonOperator
from psycopg2.extras import execute_values

from core.config import settings
from core.database import get_db_connection

BATCH_SIZE = 50

def recover_missing_keywords():
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
        ORDER BY a.id;
    """

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()

    total_saved = 0

    # API에 50개씩 요청
    for start in range(0, len(rows), BATCH_SIZE):
        batch = rows[start : start + BATCH_SIZE]

        keyword_data = [
            {
                "article_id": article_id,
                "title": title,
                "content": content,
            }
            for article_id, title, content in batch
        ]

        response = requests.post(
            f"{settings.FASTAPI_BASE_URL}/keywords/batch",
            json=keyword_data,
            timeout=600,
        )
        response.raise_for_status()

        results = response.json()

        keyword_rows = []

        for result in results:
            if result.get("error"):
                continue

            article_id = result["article_id"]

            for keyword in result.get("keywords", []):
                if not keyword or not keyword.strip():
                    continue

                keyword_rows.append(
                    (
                        article_id,
                        keyword.strip(),
                        settings.MODEL_VERSION,
                    )
                )

        if not keyword_rows:
            continue

        with get_db_connection() as conn:
            try:
                with conn.cursor() as cur:
                    execute_values(
                        cur,
                        """
                        INSERT INTO news_keywords (
                            article_id,
                            keyword,
                            model_version
                        )
                        VALUES %s
                        ON CONFLICT (article_id, keyword) DO NOTHING
                        """,
                        keyword_rows,
                        page_size=BATCH_SIZE,
                    )

                conn.commit()
                total_saved += len(keyword_rows)

            except Exception:
                conn.rollback()
                raise

with DAG(
    dag_id="recover_missing_news_keywords",
    start_date=pendulum.datetime(2026, 10, 26, tz="Asia/Seoul"),
    schedule=None,  # 수동 실행 전용
    catchup=False,
    max_active_runs=1,
    tags=["recovery", "keywords"],
) as dag:
    recover_task = PythonOperator(
        task_id="recover_missing_keywords",
        python_callable=recover_missing_keywords,
        retries=1,
        retry_delay=timedelta(minutes=1),
    )