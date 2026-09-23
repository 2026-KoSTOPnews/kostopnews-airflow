from airflow import DAG
from airflow.operators.python import PythonOperator
import pendulum

from task.news_sentiment_aggregate_pipeline_tasks import reaggregate_sentiment_periods
from task.news_sentiment_aggregate_pipeline_tasks import aggregate_sentiment_periods
from task.news_sentiment_aggregate_pipeline_tasks import store_sentiment_aggregate

with DAG(
    dag_id="news_sentiment_aggregate_pipeline",
    start_date=pendulum.datetime(2026, 6, 30, tz="Asia/Seoul"),
    schedule="30 3 * * *",
    catchup=False
) as dag:
    aggregate_sentiment_periods_task = PythonOperator(
        task_id="aggregate_sentiment_periods",
        python_callable=aggregate_sentiment_periods
    )

    store_sentiment_aggregate_task = PythonOperator(
        task_id="store_sentiment_aggregate",
        python_callable=store_sentiment_aggregate,
        params={
            "source_task_id": "aggregate_sentiment_periods"
        }
    )

    reaggregate_sentiment_periods_task = PythonOperator(
        task_id="reaggregate_sentiment_periods",
        python_callable=reaggregate_sentiment_periods
    )

    store_sentiment_reaggregate_task = PythonOperator(
        task_id="store_sentiment_reaggregate",
        python_callable=store_sentiment_aggregate,
        params={
            "source_task_id": "reaggregate_sentiment_periods"
        }
    )

    aggregate_sentiment_periods_task >> store_sentiment_aggregate_task
    reaggregate_sentiment_periods_task >> store_sentiment_reaggregate_task