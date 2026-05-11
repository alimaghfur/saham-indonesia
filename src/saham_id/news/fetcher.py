"""News fetcher — retrieves articles from RSS feeds and web sources.

Uses httpx + feedparser for RSS, with caching to reduce requests.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Optional
from time import mktime

import httpx

from saham_id.cache import cached, TTL_MOVERS
from saham_id.errors import DataSourceError, error_boundary, ErrorCollector
from saham_id.news.models import NewsArticle, NewsSource

logger = logging.getLogger(__name__)

# RSS Feed URLs for IDX news
_RSS_FEEDS: dict[NewsSource, str] = {
    NewsSource.CNBC_ID: "https://www.cnbcindonesia.com/market/rss",
    NewsSource.KONTAN: "https://www.kontan.co.id/rss/bursa-saham",
    NewsSource.BISNIS: "https://market.bisnis.com/rss",
    NewsSource.INVESTING: "https://id.investing.com/rss/news_301.rss",
}

# Common IDX ticker pattern (4 uppercase letters)
_TICKER_PATTERN = re.compile(r"\b([A-Z]{4})\b")

# Known IDX tickers (top 50 for matching)
_KNOWN_TICKERS = {
    "BBCA", "BBRI", "BMRI", "BBNI", "BRIS",
    "TLKM", "ASII", "UNVR", "HMSP", "GGRM",
    "ICBP", "INDF", "KLBF", "EMTK", "SMGR",
    "ANTM", "INCO", "PTBA", "ADRO", "ITMG",
    "PGAS", "JSMR", "WIKA", "WSKT", "PTPP",
    "TOWR", "TBIG", "EXCL", "ISAT", "MNCN",
    "SCMA", "ACES", "ERAA", "MAPI", "LPPF",
    "MDKA", "AMRT", "CPIN", "JPFA", "BSDE",
    "CTRA", "SMRA", "PWON", "DMAS", "GOTO",
    "BUKA", "ARTO", "BBYB", "AMMN", "BRPT",
}


def _extract_tickers(text: str) -> list[str]:
    """Extract likely IDX tickers from text."""
    matches = _TICKER_PATTERN.findall(text)
    return [t for t in matches if t in _KNOWN_TICKERS]


def _parse_rss_date(entry) -> Optional[datetime]:
    """Parse date from RSS entry."""
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        try:
            return datetime.fromtimestamp(mktime(entry.published_parsed))
        except (TypeError, ValueError, OverflowError):
            pass
    if hasattr(entry, "updated_parsed") and entry.updated_parsed:
        try:
            return datetime.fromtimestamp(mktime(entry.updated_parsed))
        except (TypeError, ValueError, OverflowError):
            pass
    return None


def _fetch_rss(source: NewsSource, url: str, limit: int = 20) -> list[NewsArticle]:
    """Fetch and parse a single RSS feed."""
    try:
        import feedparser
    except ImportError:
        logger.warning("feedparser not installed. Run: pip install feedparser")
        return []

    try:
        resp = httpx.get(url, timeout=10, follow_redirects=True, headers={
            "User-Agent": "saham-indonesia/0.1 (news aggregator)"
        })
        resp.raise_for_status()
    except httpx.HTTPError as e:
        logger.warning(f"Failed to fetch RSS from {source.value}: {e}")
        return []

    feed = feedparser.parse(resp.text)
    articles: list[NewsArticle] = []

    for entry in feed.entries[:limit]:
        title = entry.get("title", "").strip()
        link = entry.get("link", "").strip()
        summary = entry.get("summary", entry.get("description", "")).strip()

        # Clean HTML from summary
        summary = re.sub(r"<[^>]+>", "", summary)
        summary = summary[:300]  # Truncate

        if not title or not link:
            continue

        # Extract tickers from title + summary
        tickers = _extract_tickers(f"{title} {summary}")

        # Parse publication date
        pub_date = _parse_rss_date(entry)

        # Get image if available
        image_url = None
        if hasattr(entry, "media_content") and entry.media_content:
            image_url = entry.media_content[0].get("url")
        elif hasattr(entry, "enclosures") and entry.enclosures:
            image_url = entry.enclosures[0].get("href")

        articles.append(NewsArticle(
            title=title,
            url=link,
            source=source,
            published_at=pub_date,
            summary=summary,
            tickers=tickers,
            image_url=image_url,
        ))

    return articles


@cached(ttl=TTL_MOVERS, prefix="news:all")
def get_news(
    sources: Optional[list[NewsSource]] = None,
    limit: int = 30,
) -> list[NewsArticle]:
    """Fetch latest news from all or selected sources.

    Args:
        sources: List of sources to fetch from. None = all sources.
        limit: Maximum articles per source.

    Returns:
        Combined list of articles, sorted by publication date (newest first).
    """
    if sources is None:
        sources = list(_RSS_FEEDS.keys())

    all_articles: list[NewsArticle] = []
    collector = ErrorCollector()

    for source in sources:
        url = _RSS_FEEDS.get(source)
        if not url:
            continue
        with collector.catch(source.value):
            articles = _fetch_rss(source, url, limit=limit)
            all_articles.extend(articles)

    if collector.has_errors:
        logger.warning(f"News fetch errors: {collector.summary()}")

    # Sort by date (newest first), articles without date go last
    all_articles.sort(
        key=lambda a: a.published_at or datetime.min,
        reverse=True,
    )

    return all_articles[:limit]


@cached(ttl=TTL_MOVERS, prefix="news:search")
def search_news(query: str, limit: int = 20) -> list[NewsArticle]:
    """Search news articles by keyword.

    Args:
        query: Search keyword (ticker or topic).
        limit: Maximum results.

    Returns:
        Filtered articles matching the query.
    """
    all_articles = get_news(limit=50)
    query_upper = query.upper()

    matched = [
        a for a in all_articles
        if query_upper in a.title.upper()
        or query_upper in a.summary.upper()
        or query_upper in a.tickers
    ]

    return matched[:limit]


@cached(ttl=TTL_MOVERS, prefix="news:ticker")
def get_news_for_ticker(ticker: str, limit: int = 10) -> list[NewsArticle]:
    """Get news related to a specific stock ticker.

    Args:
        ticker: Stock ticker (e.g., "BBCA").
        limit: Maximum results.

    Returns:
        Articles mentioning or related to the ticker.
    """
    all_articles = get_news(limit=50)
    ticker_upper = ticker.upper()

    matched = [a for a in all_articles if a.matches_ticker(ticker_upper)]
    return matched[:limit]
