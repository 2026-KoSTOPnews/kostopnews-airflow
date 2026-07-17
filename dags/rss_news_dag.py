from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

from services.content_service import fetch_article_content
from services.article_service import deduplicate_articles
from services.company_service import load_companies, extract_companies
from services.postgres_service import store_articles, store_company_mentions
from services.rss_service import fetch_rss

with DAG(
    dag_id="rss_news_postgres_pipeline",
    start_date=datetime(2026, 6, 30),
    schedule="0 */2 * * *",
    catchup=False
) as dag:
    fetch_rss_task  = PythonOperator(
        task_id="fetch_rss",
        python_callable=fetch_rss
    )

    deduplicate_articles_task = PythonOperator(
        task_id="deduplicate_articles",
        python_callable=deduplicate_articles
    )

    fetch_article_content_task = PythonOperator(
        task_id="fetch_article_content",
        python_callable=fetch_article_content
    )

    store_articles_task = PythonOperator(
        task_id="store_articles",
        python_callable=store_articles
    )

    load_company_task = PythonOperator(
        task_id="load_companies",
        python_callable=load_companies
    )

    extract_companies_task = PythonOperator(
        task_id="extract_companies",
        python_callable=extract_companies
    )

    store_company_mentions_task = PythonOperator(
        task_id="store_company_mentions",
        python_callable=store_company_mentions
    )

    fetch_rss_task >> deduplicate_articles_task >> fetch_article_content_task

    fetch_article_content_task >> extract_companies_task
    load_company_task >> extract_companies_task

    extract_companies_task >> store_company_mentions_task
    fetch_article_content_task >> store_articles_task
