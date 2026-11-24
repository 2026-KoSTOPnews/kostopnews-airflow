import os

import psycopg2
import pytest

from datetime import date, datetime

from dags.task import news_keyword_aggregate_pipeline_tasks as keyword_tasks


@pytest.fixture
def test_db(monkeypatch):
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        database=os.getenv("POSTGRES_DB", "test"),
        user=os.getenv("POSTGRES_USER", "test"),
        password=os.getenv("POSTGRES_PASSWORD", "test"),
        port=os.getenv("POSTGRES_PORT", "5432"),
    )

    try:
        with conn.cursor() as cur:
            # 테스트 테이블 초기화
            cur.execute("""
                DROP TABLE IF EXISTS news_keywords;
                DROP TABLE IF EXISTS news_analysis;
                DROP TABLE IF EXISTS news_articles;
                DROP TABLE IF EXISTS companies;
            """)

            cur.execute("""
                CREATE TABLE companies (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL
                );

                CREATE TABLE news_articles (
                    id SERIAL PRIMARY KEY,
                    pub_date TIMESTAMP NOT NULL
                );

                CREATE TABLE news_analysis (
                    id SERIAL PRIMARY KEY,
                    article_id INTEGER NOT NULL,
                    company_id INTEGER NOT NULL
                );

                CREATE TABLE news_keywords (
                    id SERIAL PRIMARY KEY,
                    article_id INTEGER NOT NULL,
                    keyword VARCHAR(255)
                );
            """)

            # 기업 데이터
            cur.execute("""
                INSERT INTO companies (id, name)
                VALUES (1, '삼성전자');
            """)

            # 기사 2개
            cur.execute("""
                INSERT INTO news_articles (id, pub_date)
                VALUES
                    (1, '2026-10-05 10:00:00'),
                    (2, '2026-10-05 11:00:00');
            """)

            # 두 기사 모두 삼성전자와 연결
            cur.execute("""
                INSERT INTO news_analysis (article_id, company_id)
                VALUES
                    (1, 1),
                    (2, 1);
            """)

            # 기사 1에는 반도체가 중복 저장됨
            # 기사 2에도 반도체가 저장됨
            cur.execute("""
                INSERT INTO news_keywords (article_id, keyword)
                VALUES
                    (1, '반도체'),
                    (1, '반도체'),
                    (2, '반도체');
            """)

        conn.commit()

        # 집계 함수가 테스트 DB 연결을 사용하도록 설정
        monkeypatch.setattr(
            keyword_tasks,
            "get_db_connection",
            lambda: conn,
        )

        # 테스트 대상 키워드를 고정
        monkeypatch.setattr(
            keyword_tasks,
            "COMPANY_KEYWORDS",
            {1: ["반도체"]},
        )

        yield conn

    finally:
        conn.close()


def test_aggregate_keyword(test_db):
    """기업별 키워드 집계 시 동일 기사 내 중복 키워드를 제외한다."""
    result = keyword_tasks.aggregate_keyword(
        "DAILY",
        datetime(2026, 10, 5),
        datetime(2026, 10, 6),
    )

    samsung = [
        row for row in result
        if row["company_id"] == 1
        and row["keyword"] == "반도체"
    ]

    assert len(samsung) == 1
    assert samsung[0]["count"] == 2


def test_duplicate_keyword_in_same_article_counted_once(test_db):
    """동일 기사에 같은 키워드가 여러 번 있어도 한 번만 집계한다."""
    result = keyword_tasks.aggregate_keyword(
        "DAILY",
        datetime(2026, 10, 5),
        datetime(2026, 10, 6),
    )

    samsung = [
        row for row in result
        if row["company_id"] == 1
        and row["keyword"] == "반도체"
    ]

    assert len(samsung) == 1
    assert samsung[0]["count"] == 2


def test_daily_keyword_period(test_db):
    """일별 집계 결과의 기간 시작일을 검증한다."""
    result = keyword_tasks.aggregate_keyword(
        "DAILY",
        datetime(2026, 10, 5),
        datetime(2026, 10, 6),
    )

    assert result
    assert all(
        row["period_start"].date() == date(2026, 10, 5)
        for row in result
    )


def test_no_keyword_data_for_empty_date(test_db):
    """해당 기간에 키워드 데이터가 없으면 빈 목록을 반환한다."""
    result = keyword_tasks.aggregate_keyword(
        "DAILY",
        datetime(2026, 10, 3),
        datetime(2026, 10, 4),
    )

    assert result == []


def test_aggregate_keyword_multiple_companies(test_db, monkeypatch):
    """같은 키워드가 여러 기업에 연결된 경우 기업별로 집계한다."""
    with test_db.cursor() as cur:
        cur.execute(
            "INSERT INTO companies (id, name) VALUES (%s, %s)",
            (2, "SK하이닉스"),
        )

        cur.execute("""
            INSERT INTO news_analysis (article_id, company_id)
            VALUES
                (1, 2),
                (2, 2);
        """)

    test_db.commit()

    monkeypatch.setattr(
        keyword_tasks,
        "COMPANY_KEYWORDS",
        {
            1: ["반도체"],
            2: ["반도체"],
        },
    )

    result = keyword_tasks.aggregate_keyword(
        "DAILY",
        datetime(2026, 10, 5),
        datetime(2026, 10, 6),
    )

    counts = {
        (row["company_id"], row["keyword"]): row["count"]
        for row in result
    }

    assert counts[(1, "반도체")] == 2
    assert counts[(2, "반도체")] == 2