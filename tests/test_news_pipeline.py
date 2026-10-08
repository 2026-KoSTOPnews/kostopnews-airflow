import task.news_pipeline_tasks as news_pipeline_tasks


def test_fetch_and_store_news(monkeypatch):
    calls = []

    articles = [
        {
            "title": "삼성전자 실적 발표",
            "link": "https://example.com/1",
        }
    ]

    companies = {
        "Samsung": {
            "id": 1,
            "aliases": ["삼성전자"],
        }
    }

    def mock_fetch_rss():
        calls.append("fetch_rss")
        return articles

    def mock_load_companies():
        calls.append("load_companies")
        return companies

    def mock_deduplicate_articles(articles, companies):
        calls.append("deduplicate_articles")
        return articles

    def mock_fetch_article_content(articles):
        calls.append("fetch_article_content")
        return articles

    def mock_store_articles(articles):
        calls.append("store_articles")

    monkeypatch.setattr(
        news_pipeline_tasks,
        "fetch_rss",
        mock_fetch_rss,
    )

    monkeypatch.setattr(
        news_pipeline_tasks,
        "load_companies",
        mock_load_companies,
    )

    monkeypatch.setattr(
        news_pipeline_tasks,
        "deduplicate_articles",
        mock_deduplicate_articles,
    )

    monkeypatch.setattr(
        news_pipeline_tasks,
        "fetch_article_content",
        mock_fetch_article_content,
    )

    monkeypatch.setattr(
        news_pipeline_tasks,
        "store_articles",
        mock_store_articles,
    )

    news_pipeline_tasks.fetch_and_store_news()

    assert calls == [
        "fetch_rss",
        "load_companies",
        "deduplicate_articles",
        "fetch_article_content",
        "store_articles",
    ]