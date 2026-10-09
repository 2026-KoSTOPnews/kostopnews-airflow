import pendulum

from airflow import DAG
from airflow.operators.python import PythonOperator

from task.news_sentiment_aggregate_pipeline_tasks import aggregate_sentiment
from task.news_sentiment_aggregate_pipeline_tasks import store_sentiment_aggregate
from task.news_keyword_aggregate_pipeline_tasks import aggregate_keyword
from task.news_keyword_aggregate_pipeline_tasks import store_keyword_aggregate

from utils.date_utils import get_date_range


def reaggregate_missing_dates():
    dates = [
        pendulum.date(2026, 10, 7),
        pendulum.date(2026, 10, 8),
    ]

    results = []

    for target_date in dates:
        start_date, end_date = get_date_range(target_date)

        results.extend(
            aggregate_sentiment(
                "DAILY",
                start_date,
                end_date,
            )
        )

    return results

def reaggregate_missing_keyword_dates():
    dates = [
        pendulum.date(2026, 10, 7),
        pendulum.date(2026, 10, 8),
    ]

    results = []

    for target_date in dates:
        start_date, end_date = get_date_range(target_date)

        results.extend(
            aggregate_keyword(
                "DAILY",
                start_date,
                end_date,
            )
        )

    return results

with DAG(
    dag_id="reaggregate_missing_news",
    start_date=pendulum.datetime(2026, 10, 9, tz="Asia/Seoul"),
    schedule=None,
    catchup=False,
    tags=["maintenance", "reaggregation"],
) as dag:
    aggregate_missing_dates = PythonOperator(
        task_id="aggregate_missing_dates",
        python_callable=reaggregate_missing_dates,
    )

    store_sentiment_aggregate_task = PythonOperator(
        task_id="store_sentiment_aggregate",
        python_callable=store_sentiment_aggregate,
        params={
            "source_task_id": "aggregate_missing_dates"
        },
    )

    aggregate_missing_keywords_task = PythonOperator(
        task_id="aggregate_missing_keyword_dates",
        python_callable=reaggregate_missing_keyword_dates,
    )

    store_keyword_aggregate_task = PythonOperator(
        task_id="store_keyword_aggregate",
        python_callable=store_keyword_aggregate,
        params={
            "source_task_id": "aggregate_missing_keyword_dates"
        },
    )

    aggregate_missing_dates >> store_sentiment_aggregate_task
    aggregate_missing_keywords_task >> store_keyword_aggregate_task
