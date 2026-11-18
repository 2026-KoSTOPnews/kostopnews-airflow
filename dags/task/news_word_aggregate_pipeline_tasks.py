from datetime import timedelta
import pendulum

from core.database import get_db_connection
from services.news_word_aggregate_service import process_daily_word_aggregate

# -------------------------
# 일간 단어 집계 실행
# -------------------------
def run_word_aggregate():
    execution_date = pendulum.now("Asia/Seoul").date()
    target_date = execution_date - timedelta(days=1)

    return process_daily_word_aggregate(target_date)
