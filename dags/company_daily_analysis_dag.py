from airflow import DAG
from airflow.operators.python import PythonOperator
import pendulum
from datetime import timedelta

from task.daily_analysis_tasks import analyze_company_daily

with DAG(
    dag_id="company_daily_analysis",
    start_date=pendulum.datetime(2026, 6, 30, tz="Asia/Seoul"),
    schedule="30 18 * * 1-5",
    catchup=False,
    max_active_runs=1,
    tags=["news", "stock", "daily-analysis"],
) as dag:
    analyze_company_daily_task = PythonOperator(
        task_id="analyze_company_daily",
        python_callable=analyze_company_daily,
        retries=2,
        retry_delay=timedelta(minutes=5),
        retry_exponential_backoff=True,
        max_retry_delay=timedelta(minutes=15),
    )