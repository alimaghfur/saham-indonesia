"""News module for saham-indonesia.

Fetches IDX-related news from multiple sources:
- CNBC Indonesia RSS
- Kontan.co.id RSS
- Bisnis.com RSS
- IDNFinancials

Usage:
    from saham_id.news import get_news, search_news

    # Get latest market news
    articles = get_news(limit=20)

    # Search news for specific ticker
    articles = search_news("BBCA", limit=10)
"""

from saham_id.news.fetcher import get_news, search_news, get_news_for_ticker
from saham_id.news.models import NewsArticle, NewsSource

__all__ = [
    "get_news",
    "search_news",
    "get_news_for_ticker",
    "NewsArticle",
    "NewsSource",
]
