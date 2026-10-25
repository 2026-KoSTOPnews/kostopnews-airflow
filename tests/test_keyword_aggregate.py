import os

import psycopg2
import pytest

from datetime import date, datetime

from dags.task.news_keyword_aggregate_pipeline_tasks import aggregate_keyword


@pytest.fixture
def test_db():
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        database=os.getenv("POSTGRES_DB", "test"),
        user=os.getenv("POSTGRES_USER", "test"),
        password=os.getenv("POSTGRES_PASSWORD", "test"),
        port=os.getenv("POSTGRES_PORT", "5432"),
    )

    cur = conn.cursor()

    # 테스트 테이블 초기화
    cur.execute("""
        DROP TABLE IF EXISTS news_keywords;
        DROP TABLE IF EXISTS news_analysis;
        DROP TABLE IF EXISTS news_articles;
        DROP TABLE IF EXISTS companies;
    """)

    # 회사
    cur.execute("""
        CREATE TABLE companies (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL
        );
    """)

    # 뉴스 기사
    cur.execute("""
        CREATE TABLE news_articles (
            id SERIAL PRIMARY KEY,
            pub_date TIMESTAMP NOT NULL
        );
    """)

    # 뉴스 분석
    cur.execute("""
        CREATE TABLE news_analysis (
            id SERIAL PRIMARY KEY,
            article_id INTEGER NOT NULL,
            company_id INTEGER NOT NULL
        );
    """)

    # 뉴스 키워드
    cur.execute("""
        CREATE TABLE news_keywords (
            id SERIAL PRIMARY KEY,
            article_id INTEGER NOT NULL,
            keyword VARCHAR(255)
        );
    """)

    # 회사 데이터
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

    # 두 기사 모두 삼성전자
    cur.execute("""
        INSERT INTO news_analysis (article_id, company_id)
        VALUES
            (1, 1),
            (2, 1);
    """)

    # 키워드
    #
    # 기사 1:
    #   반도체
    #   반도체  ← 중복
    #
    # 기사 2:
    #   반도체
    #
    # 따라서 반도체 count = 2
    cur.execute("""
        INSERT INTO news_keywords (article_id, keyword)
        VALUES
            (1, '반도체'),
            (1, '반도체'),
            (2, '반도체');
    """)

    conn.commit()

    yield conn

    conn.close()


def test_aggregate_keyword(test_db):
    """회사별 키워드 집계 시 동일 기사 내 중복 키워드를 제외하고 기사 수를 집계한다."""
    result = aggregate_keyword(
        "DAILY",
        datetime(2026, 10, 5),
        datetime(2026, 10, 6),
    )

    samsung = [
        r for r in result
        if r["company_id"] == 1
        and r["keyword"] == "반도체"
    ]

    assert len(samsung) == 1
    assert samsung[0]["count"] == 2


def test_duplicate_keyword_in_same_article_counted_once(test_db):
    """동일 기사에서 같은 키워드가 여러 번 저장되어도 한 번만 집계한다."""
    result = aggregate_keyword(
        "DAILY",
        datetime(2026, 10, 5),
        datetime(2026, 10, 6),
    )

    samsung = [
        r for r in result
        if r["company_id"] == 1
        and r["keyword"] == "반도체"
    ]

    # 같은 기사에서 '반도체'가 여러 번 매칭되어도
    # 기사 자체는 한 번만 집계되어야 함
    assert samsung[0]["count"] == 2


def test_daily_keyword_period(test_db):
    """일별 키워드 집계 결과의 집계 기간 시작일을 검증한다."""
    result = aggregate_keyword(
        "DAILY",
        datetime(2026, 10, 5),
        datetime(2026, 10, 6),
    )

    assert all(
        r["period_start"].date() == date(2026, 10, 5)
        for r in result
    )


def test_no_keyword_data_for_empty_date(test_db):
    """해당 날짜에 키워드 데이터가 없으면 빈 목록을 반환한다."""
    result = aggregate_keyword(
        "DAILY",
        datetime(2026, 10, 3),
        datetime(2026, 10, 4),
    )

    assert result == []