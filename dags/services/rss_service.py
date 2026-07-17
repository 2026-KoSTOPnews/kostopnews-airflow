import requests
import xml.etree.ElementTree as ET

# -------------------------
# RSS 수집 + 파싱
# -------------------------
def fetch_rss(**context):
    urls = [
        "https://www.yna.co.kr/rss/economy.xml",
        "https://www.hankyung.com/feed/economy",
        "https://www.hankyung.com/feed/finance",
        "https://www.mk.co.kr/rss/30100041/",
        "https://www.mk.co.kr/rss/50200011/",
        "https://www.sedaily.com/rss/economy",
        "https://www.sedaily.com/rss/finance",
    ]

    headers = {"User-Agent": "Mozilla/5.0"}

    articles = []

    for url in urls:
        try:
            res = requests.get(url, headers=headers, timeout=10)
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
                        "source": "rss"
                    })

        except Exception:
            continue

    return articles