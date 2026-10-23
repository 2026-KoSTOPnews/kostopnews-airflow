from airflow import DAG
from airflow.operators.python import PythonOperator
import pendulum

from task.news_pipeline_tasks import extract_and_store_companies

with DAG(
    dag_id="news_company_extraction",
    start_date=pendulum.datetime(2026, 6, 30, tz="Asia/Seoul"),
    schedule="10 * * * *",
    catchup=False,
) as dag:
    extract_and_store_companies_task = PythonOperator(
        task_id="extract_and_store_companies",
        python_callable=extract_and_store_companies,
    )