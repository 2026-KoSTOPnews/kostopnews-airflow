import os

import psycopg2
import pytest


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