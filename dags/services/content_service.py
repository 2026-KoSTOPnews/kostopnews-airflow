import trafilatura
import requests

from utils.text_cleaner import clean_content

# -------------------------
# 기사 본문 가져오기
# -------------------------
def fetch_article_content(**context):
    ti = context["ti"]
    articles = ti.xcom_pull(task_ids="deduplicate_articles")

    if not articles:
        return []

    enriched = []

    for a in articles:
        url = a["link"]
        content = None

        try:
            downloaded = trafilatura.fetch_url(url)

            if downloaded:
                content = trafilatura.extract(
                    downloaded,
                    include_comments=False,
                    include_tables=False
                )

        except Exception:
            content = None

        # fallback
        if not content or len(content) < 200:
            content = a.get("summary", "")

        content = clean_content(content)

        enriched.append({
            **a,
            "content": content
        })

    return enriched