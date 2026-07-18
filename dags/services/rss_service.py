import logging
import requests
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

# -------------------------
# RSS 수집 + 파싱
# -------------------------
def fetch_rss(**context):
    rss_sources = {
        "yna_economy": "https://www.yna.co.kr/rss/economy.xml",
        "hankyung_economy": "https://www.hankyung.com/feed/economy",
        "hankyung_finance": "https://www.hankyung.com/feed/finance",
        "mk_economy": "https://www.mk.co.kr/rss/30100041/",
        "mk_finance": "https://www.mk.co.kr/rss/50200011/",
        "sedaily_economy": "https://www.sedaily.com/rss/economy",
        "sedaily_finance": "https://www.sedaily.com/rss/finance",
    }

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
    }

    articles = []

    for source, url in rss_sources.items():
        try:
            res = requests.get(url, headers=headers, timeout=20)
            res.raise_for_status()

            root = ET.fromstring(res.text)

            for item in root.findall(".//item"):
                title = item.findtext("title")
                link = item.findtext("link")
                pub_date = item.findtext("pubDate")

                if title and link:
                    articles.append({
                        "title": title,
                        "link": link,
                        "pub_date": pub_date,
                        "source": source
                    })

        except Exception as e:
            logger.error(f"[RSS ERROR] {source}: {e}")
            continue

    return articles