from datetime import timedelta

import pendulum

import requests

from core.config import settings
from core.database import get_db_connection

def analyze_company_daily():
    companies = get_analysis_companies()

    if not companies:
        return

    today = pendulum.now("Asia/Seoul").date()

    if today.weekday() == 0:  # 월요일
        previous_day = today - timedelta(days=3)
    else:
        previous_day = today - timedelta(days=1)

    target_dates = [
        today.isoformat(),
        previous_day.isoformat(),
    ]

    headers = {
        "X-API-Key": settings.AIRFLOW_API_KEY,
    }

    success_count = 0
    failed_count = 0

    for target_date in target_dates:
        print(f"\n========== {target_date} 종합 분석 시작 ==========")

        for company in companies:
            company_id = company["id"]
            company_name = company["name"]

            url = (
                f"{settings.FASTAPI_BASE_URL.rstrip('/')}"
                f"/insight/{company_id}"
            )

            print(f"[{company_name}] {target_date} 분석 요청 시작")

            try:
                response = requests.post(
                    url,
                    headers=headers,
                    params={"target_date": target_date},
                    timeout=180,
                )

                if response.status_code == 404:
                    print(f"404 응답: {response.text}")

                response.raise_for_status()

                result = response.json()

                if result.get("status") != "completed":
                    raise RuntimeError(f"예상하지 못한 응답: {result}")

                success_count += 1
                print(f"[{company_name}] {target_date} 분석 완료")

            except (requests.RequestException, ValueError, RuntimeError) as e:
                failed_count += 1
                print(f"[{company_name}] {target_date} 분석 실패: {e}")

    print("\n========== 전체 종합 분석 결과 ==========")
    print(f"분석 날짜: {target_dates}")
    print(f"전체 요청: {len(companies) * len(target_dates)}")
    print(f"성공: {success_count}")
    print(f"실패: {failed_count}")

    if success_count == 0:
        raise RuntimeError("모든 기업의 종합 분석에 실패했습니다.")

def get_analysis_companies():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, ticker
                FROM companies
                WHERE ticker IS NOT NULL
                ORDER BY id
                LIMIT 10
            """)

            return [
                {
                    "id": row[0],
                    "name": row[1],
                    "ticker": row[2],
                }
                for row in cur.fetchall()
            ]