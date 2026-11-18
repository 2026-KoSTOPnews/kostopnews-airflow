import pendulum

from airflow import DAG
from airflow.operators.python import PythonOperator

from task.news_word_aggregate_pipeline_tasks import run_word_aggregate

with DAG(
    dag_id="news_word_aggregate_pipeline",
    default_args={
        "retries": 2,
        "retry_delay": pendulum.duration(minutes=5),
    },
    start_date=pendulum.datetime(2026, 6, 30, tz="Asia/Seoul"),
    schedule="30 1 * * *",
    catchup=False,
    max_active_runs=1,
    tags=["news", "word-aggregate", "nlp"],
) as dag:
    aggregate_word_task = PythonOperator(
        task_id="aggregate_daily_words",
        python_callable=run_word_aggregate,
    )
