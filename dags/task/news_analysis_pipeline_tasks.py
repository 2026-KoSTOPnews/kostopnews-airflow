from services.news_analysis_service import fetch_news_data
from services.news_analysis_service import request_sentiment_analysis
from services.news_analysis_service import request_keyword_extraction

# -------------------------
# 뉴스 분석 실행
# -------------------------
def analyze_news():
    news_data = fetch_news_data()

    sentiment_results = request_sentiment_analysis(news_data["sentiment_data"])

    keyword_results = request_keyword_extraction(news_data["keyword_data"])

    return {
        "sentiment_results": sentiment_results,
        "keyword_results": keyword_results,
    }