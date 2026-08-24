from airflow import DAG
from airflow.operators.python import PythonOperator
import pendulum
from datetime import timedelta

from task.news_sentiment_pipeline_tasks import call_sentiment_batch
from task.news_sentiment_pipeline_tasks import store_news_sentiment
from task.news_sentiment_pipeline_tasks import fetch_data

with DAG(
    dag_id="news_sentiment_pipeline",
    start_date=pendulum.datetime(2026, 6, 30, tz="Asia/Seoul"),
    schedule="*/20 * * * *",
    catchup=False,
    max_active_runs=1,
) as dag:
    fetch_data_task = PythonOperator(
        task_id="fetch_data",
        python_callable=fetch_data
    )

    call_sentiment_batch_task = PythonOperator(
        task_id="call_sentiment_batch",
        python_callable=call_sentiment_batch,
        retries=1,
        retry_delay=timedelta(minutes=1),
        retry_exponential_backoff=True,
        max_retry_delay=timedelta(minutes=10),
    )

    store_news_sentiment_task = PythonOperator(
        task_id="store_news_sentiment",
        python_callable=store_news_sentiment
    )

    fetch_data_task >> call_sentiment_batch_task >> store_news_sentiment_task