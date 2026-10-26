from airflow import DAG
from airflow.operators.python import PythonOperator
import pendulum
from datetime import timedelta

from task.news_analysis_pipeline_tasks import analyze_news, store_news_sentiment, store_news_keywords

with DAG(
    dag_id="news_analysis_pipeline",
    start_date=pendulum.datetime(2026, 6, 30, tz="Asia/Seoul"),
    schedule="20 * * * *",
    catchup=False,
    max_active_runs=1,
) as dag:
    analyze_news_task = PythonOperator(
        task_id="analyze_news",
        python_callable=analyze_news,
        retries=1,
        retry_delay=timedelta(minutes=1),
        retry_exponential_backoff=True,
        max_retry_delay=timedelta(minutes=10),
    )

    store_news_sentiment_task = PythonOperator(
        task_id="store_news_sentiment",
        python_callable=store_news_sentiment,
    )

    store_news_keywords_task = PythonOperator(
        task_id="store_news_keywords",
        python_callable=store_news_keywords,
    )

    analyze_news_task >> [store_news_sentiment_task, store_news_keywords_task]
