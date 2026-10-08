from services.rss_service import fetch_rss
from services.article_service import deduplicate_articles
from services.content_service import fetch_article_content
from services.company_service import load_companies
from services.postgres_service import store_articles
from services.company_service import load_companies
from services.company_service import extract_companies
from services.postgres_service import store_company_mentions
from services.postgres_service import get_articles_for_company_extraction

BATCH_SIZE = 50

def fetch_and_store_news():
    # 1. RSS 수집
    articles = fetch_rss()

    if not articles:
        return

    # 2. 기업 정보 조회
    companies = load_companies()

    # 3. 중복 제거 + 키워드 필터
    articles = deduplicate_articles(articles, companies)

    if not articles:
        return

    # 4. 기사 본문 수집
    articles = fetch_article_content(articles)

    if not articles:
        return

    # 5. DB 저장
    store_articles(articles)

def extract_and_store_companies():
    # 1. 기업 조회
    companies = load_companies()

    offset = 0

    while True:
        # 2. DB에서 기사 50개 조회
        articles = get_articles_for_company_extraction(limit=BATCH_SIZE, offset=offset)

        if not articles:
            break

        # 3. 기업 매칭
        results = extract_companies(articles, companies)

        # 4. 기업 언급 저장
        if results:
            store_company_mentions(results)

        # 다음 batch
        offset += BATCH_SIZE