from airflow import DAG
from airflow.operators.python import PythonOperator
import pendulum

from task.news_keyword_aggregate_pipeline_tasks import aggregate_keyword_periods
from task.news_keyword_aggregate_pipeline_tasks import store_keyword_aggregate
from task.news_keyword_aggregate_pipeline_tasks import reaggregate_keyword_periods

with DAG(
    dag_id="news_keyword_aggregate_pipeline",
    start_date=pendulum.datetime(2026, 6, 30, tz="Asia/Seoul"),
    schedule="30 4 * * *",
    catchup=False,
) as dag:
    aggregate_keyword_periods_task = PythonOperator(
        task_id="aggregate_keyword_periods",
        python_callable=aggregate_keyword_periods,
    )

    store_keyword_aggregate_task = PythonOperator(
        task_id="store_keyword_aggregate",
        python_callable=store_keyword_aggregate,
        params={
            "source_task_id": "aggregate_keyword_periods"
        }
    )

    reaggregate_keyword_periods_task = PythonOperator(
        task_id="reaggregate_keyword_periods",
        python_callable=reaggregate_keyword_periods,
    )

    store_keyword_reaggregate_task = PythonOperator(
        task_id="store_keyword_reaggregate",
        python_callable=store_keyword_aggregate,
        params={
            "source_task_id": "reaggregate_keyword_periods"
        }
    )

    aggregate_keyword_periods_task >> store_keyword_aggregate_task
    reaggregate_keyword_periods_task >> store_keyword_reaggregate_task