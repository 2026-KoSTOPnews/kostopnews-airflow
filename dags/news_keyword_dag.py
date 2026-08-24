from airflow import DAG
from airflow.operators.python import PythonOperator
import pendulum
from datetime import timedelta

from task.news_keyword_pipeline_tasks import fetch_keyword_data
from task.news_keyword_pipeline_tasks import call_keyword_batch
from task.news_keyword_pipeline_tasks import store_news_keywords

with DAG(
    dag_id="news_keyword_pipeline",
    start_date=pendulum.datetime(2026, 6, 30, tz="Asia/Seoul"),
    schedule="*/20 * * * *",
    catchup=False,
    max_active_runs=1,
) as dag:
    fetch_keyword_data_task = PythonOperator(
        task_id="fetch_keyword_data",
        python_callable=fetch_keyword_data
    )

    call_keyword_batch_task = PythonOperator(
        task_id="call_keyword_batch",
        python_callable=call_keyword_batch,
        retries=1,
        retry_delay=timedelta(minutes=1),
        retry_exponential_backoff=True,
        max_retry_delay=timedelta(minutes=10),
    )

    store_news_keywords_task = PythonOperator(
        task_id="store_news_keywords",
        python_callable=store_news_keywords
    )

    fetch_keyword_data_task >> call_keyword_batch_task >> store_news_keywords_task