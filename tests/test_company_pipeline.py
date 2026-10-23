from task.news_pipeline_tasks import extract_and_store_companies


def test_extract_and_store_companies_batches(monkeypatch):
    batches = [
        [{"id": i} for i in range(50)],
        [{"id": i} for i in range(50, 100)],
        [{"id": i} for i in range(100, 120)],
        [],
    ]

    calls = []
    saved_results = []
    processed_ids = []

    def mock_load_companies():
        return {
            "Samsung": {
                "id": 1,
                "aliases": ["삼성전자"]
            }
        }

    def mock_get_articles(limit):
        calls.append(limit)
        return batches.pop(0)

    def mock_extract(articles, companies):
        return [
            {
                "article": article,
                "matches": []
            }
            for article in articles
        ]

    def mock_store(results):
        saved_results.append(results)

    def mock_mark_articles_processed(article_ids):
        processed_ids.extend(article_ids)

    monkeypatch.setattr(
        "task.news_pipeline_tasks.load_companies",
        mock_load_companies
    )
    monkeypatch.setattr(
        "task.news_pipeline_tasks.get_articles_for_company_extraction",
        mock_get_articles
    )
    monkeypatch.setattr(
        "task.news_pipeline_tasks.extract_companies",
        mock_extract
    )
    monkeypatch.setattr(
        "task.news_pipeline_tasks.store_company_mentions",
        mock_store
    )
    monkeypatch.setattr(
        "task.news_pipeline_tasks.mark_articles_processed",
        mock_mark_articles_processed
    )

    extract_and_store_companies()

    assert calls == [50, 50, 50, 50]
    assert len(saved_results) == 3
    assert len(processed_ids) == 120
    assert processed_ids == list(range(120))