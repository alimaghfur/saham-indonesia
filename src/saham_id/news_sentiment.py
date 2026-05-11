"""News sentiment — basic keyword-based sentiment analysis from headlines.

Provides simple sentiment scoring for IDX-related news by analyzing
keyword presence in headlines. No NLP model required.

Usage:
    from saham_id.news_sentiment import SentimentAnalyzer, HeadlineSentiment

    analyzer = SentimentAnalyzer()
    score = analyzer.score_headline("BBCA cetak laba bersih naik 15% YoY")
    print(score.sentiment)   # "positive"
    print(score.score)       # 0.7
    print(score.keywords_found)  # ["laba", "naik"]
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Optional


# --- Keyword dictionaries for IDX/Indonesian market ---

POSITIVE_KEYWORDS: dict[str, float] = {
    # Profitability
    "laba": 0.8, "profit": 0.8, "untung": 0.7, "surplus": 0.7,
    "naik": 0.6, "meningkat": 0.6, "tumbuh": 0.7, "growth": 0.7,
    "rekor": 0.8, "record": 0.8, "tertinggi": 0.7, "highest": 0.7,
    # Dividends
    "dividen": 0.6, "dividend": 0.6, "bagi dividen": 0.7,
    # Upgrades
    "upgrade": 0.6, "buy": 0.5, "outperform": 0.6, "overweight": 0.5,
    "target naik": 0.7, "recommended": 0.5,
    # Market
    "rally": 0.7, "bullish": 0.8, "breakout": 0.6, "rebound": 0.6,
    "menguat": 0.6, "hijau": 0.5, "positif": 0.5,
    # Business
    "ekspansi": 0.6, "akuisisi": 0.5, "kontrak baru": 0.7,
    "kerjasama": 0.5, "partnership": 0.5,
}

NEGATIVE_KEYWORDS: dict[str, float] = {
    # Losses
    "rugi": -0.8, "loss": -0.8, "merugi": -0.8,
    "turun": -0.6, "menurun": -0.6, "anjlok": -0.9, "jatuh": -0.8,
    # Downgrades
    "downgrade": -0.6, "sell": -0.5, "underperform": -0.6, "underweight": -0.5,
    "target turun": -0.7, "pangkas target": -0.7,
    # Market
    "bearish": -0.8, "crash": -0.9, "koreksi": -0.5, "melemah": -0.6,
    "merah": -0.5, "negatif": -0.5, "tekanan": -0.5,
    # Risk
    "gagal bayar": -0.9, "default": -0.9, "bankrut": -1.0, "bangkrut": -1.0,
    "fraud": -0.9, "manipulasi": -0.8, "suspend": -0.7,
    "delisting": -0.8, "PKPU": -0.8, "pailit": -0.9,
    # Business
    "PHK": -0.6, "lay off": -0.6, "tutup": -0.5, "kerugian": -0.7,
}

NEUTRAL_KEYWORDS: list[str] = [
    "RUPS", "laporan", "jadwal", "pengumuman", "IHSG", "BEI",
    "OJK", "regulasi", "kebijakan",
]


@dataclass
class HeadlineSentiment:
    """Sentiment analysis result for a headline."""

    headline: str
    sentiment: Literal["positive", "negative", "neutral"]
    score: float  # -1.0 to +1.0
    confidence: float  # 0.0 to 1.0
    keywords_found: list[str] = field(default_factory=list)
    ticker_mentions: list[str] = field(default_factory=list)
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class SentimentSummary:
    """Aggregated sentiment for multiple headlines."""

    ticker: str
    total_headlines: int
    positive_count: int
    negative_count: int
    neutral_count: int
    average_score: float
    overall: Literal["positive", "negative", "neutral"]
    headlines: list[HeadlineSentiment] = field(default_factory=list)


class SentimentAnalyzer:
    """Keyword-based sentiment analyzer for IDX news headlines.

    Simple but effective: scans for known positive/negative keywords
    and produces a weighted sentiment score.
    """

    def __init__(
        self,
        positive_keywords: Optional[dict[str, float]] = None,
        negative_keywords: Optional[dict[str, float]] = None,
    ):
        self.positive = positive_keywords or POSITIVE_KEYWORDS
        self.negative = negative_keywords or NEGATIVE_KEYWORDS

    def score_headline(self, headline: str, ticker: str = "") -> HeadlineSentiment:
        """Score a single headline for sentiment.

        Parameters:
            headline: News headline text
            ticker: Optional ticker context (for relevance)

        Returns:
            HeadlineSentiment with score, sentiment label, and matched keywords
        """
        text = headline.lower()
        keywords_found: list[str] = []
        total_score = 0.0
        total_weight = 0.0

        # Check positive keywords
        for keyword, weight in self.positive.items():
            if keyword.lower() in text:
                total_score += weight
                total_weight += abs(weight)
                keywords_found.append(keyword)

        # Check negative keywords
        for keyword, weight in self.negative.items():
            if keyword.lower() in text:
                total_score += weight  # negative weight
                total_weight += abs(weight)
                keywords_found.append(keyword)

        # Normalize score to [-1, 1]
        if total_weight > 0:
            normalized_score = total_score / total_weight
        else:
            normalized_score = 0.0

        # Determine sentiment
        if normalized_score > 0.1:
            sentiment = "positive"
        elif normalized_score < -0.1:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        # Confidence based on number of keywords matched
        confidence = min(1.0, len(keywords_found) * 0.25) if keywords_found else 0.0

        # Detect ticker mentions
        ticker_mentions = self._find_tickers(headline)

        return HeadlineSentiment(
            headline=headline,
            sentiment=sentiment,
            score=round(normalized_score, 3),
            confidence=confidence,
            keywords_found=keywords_found,
            ticker_mentions=ticker_mentions,
        )

    def score_multiple(self, headlines: list[str], ticker: str = "") -> SentimentSummary:
        """Score multiple headlines and aggregate results."""
        results: list[HeadlineSentiment] = []
        for h in headlines:
            results.append(self.score_headline(h, ticker))

        positive = sum(1 for r in results if r.sentiment == "positive")
        negative = sum(1 for r in results if r.sentiment == "negative")
        neutral = sum(1 for r in results if r.sentiment == "neutral")
        avg_score = sum(r.score for r in results) / len(results) if results else 0.0

        if avg_score > 0.1:
            overall = "positive"
        elif avg_score < -0.1:
            overall = "negative"
        else:
            overall = "neutral"

        return SentimentSummary(
            ticker=ticker,
            total_headlines=len(results),
            positive_count=positive,
            negative_count=negative,
            neutral_count=neutral,
            average_score=round(avg_score, 3),
            overall=overall,
            headlines=results,
        )

    def _find_tickers(self, text: str) -> list[str]:
        """Find potential ticker mentions in text (4-letter uppercase words)."""
        import re
        # IDX tickers are typically 4 uppercase letters
        matches = re.findall(r'\b[A-Z]{4}\b', text)
        # Filter out common non-ticker words
        non_tickers = {"IHSG", "RUPS", "PKPU", "BUMN", "PSBB", "UMKM", "APBN"}
        return [m for m in matches if m not in non_tickers]
