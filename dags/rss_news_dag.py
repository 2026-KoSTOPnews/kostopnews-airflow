from airflow import DAG
from airflow.operators.python import PythonOperator
import pendulum

from task.news_pipeline_tasks import fetch_and_store_news, extract_and_store_companies

with DAG(
    dag_id="rss_news_postgres_pipeline",
    start_date=pendulum.datetime(2026, 6, 30, tz="Asia/Seoul"),
    schedule="0 * * * *",
    catchup=False
) as dag:
    fetch_and_store_news_task = PythonOperator(
        task_id="fetch_and_store_news",
        python_callable=fetch_and_store_news
    )

    extract_and_store_companies_task = PythonOperator(
        task_id="extract_and_store_companies",
        python_callable=extract_and_store_companies
    )

    fetch_and_store_news_task >> extract_and_store_companies_task
