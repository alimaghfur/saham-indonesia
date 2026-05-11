"""Tests for news sentiment module."""
from saham_id.news_sentiment import (
    SentimentAnalyzer, HeadlineSentiment, SentimentSummary,
    POSITIVE_KEYWORDS, NEGATIVE_KEYWORDS,
)


class TestSentimentAnalyzer:
    def test_positive_headline(self):
        analyzer = SentimentAnalyzer()
        result = analyzer.score_headline("BBCA cetak laba bersih naik 15% YoY")
        assert result.sentiment == "positive"
        assert result.score > 0
        assert len(result.keywords_found) >= 2

    def test_negative_headline(self):
        analyzer = SentimentAnalyzer()
        result = analyzer.score_headline("Saham ABCD anjlok 20% setelah laporan rugi besar")
        assert result.sentiment == "negative"
        assert result.score < 0
        assert len(result.keywords_found) >= 2

    def test_neutral_headline(self):
        analyzer = SentimentAnalyzer()
        result = analyzer.score_headline("RUPS tahunan PT XYZ dijadwalkan bulan depan")
        assert result.sentiment == "neutral"
        assert abs(result.score) <= 0.1

    def test_mixed_headline(self):
        analyzer = SentimentAnalyzer()
        result = analyzer.score_headline("Laba naik tapi tekanan jual masih kuat")
        # Has both positive and negative keywords
        assert len(result.keywords_found) >= 2

    def test_confidence_increases_with_keywords(self):
        analyzer = SentimentAnalyzer()
        r1 = analyzer.score_headline("naik")
        r2 = analyzer.score_headline("laba naik rekor tertinggi tumbuh")
        assert r2.confidence >= r1.confidence

    def test_ticker_detection(self):
        analyzer = SentimentAnalyzer()
        result = analyzer.score_headline("BBCA dan BBRI cetak rekor laba")
        assert "BBCA" in result.ticker_mentions
        assert "BBRI" in result.ticker_mentions

    def test_non_ticker_filtered(self):
        analyzer = SentimentAnalyzer()
        result = analyzer.score_headline("IHSG ditutup menguat, BUMN berkinerja baik")
        assert "IHSG" not in result.ticker_mentions
        assert "BUMN" not in result.ticker_mentions


class TestScoreMultiple:
    def test_aggregate(self):
        analyzer = SentimentAnalyzer()
        headlines = [
            "BBCA laba naik 20%",
            "Sektor banking tumbuh positif",
            "BBCA dividen Rp 275",
            "Tekanan jual di pasar",
        ]
        summary = analyzer.score_multiple(headlines, ticker="BBCA")
        assert summary.total_headlines == 4
        assert summary.positive_count >= 2
        assert summary.overall in ("positive", "negative", "neutral")
        assert len(summary.headlines) == 4


class TestHeadlineSentiment:
    def test_create(self):
        hs = HeadlineSentiment(
            headline="Test", sentiment="positive",
            score=0.5, confidence=0.8,
        )
        assert hs.headline == "Test"
        assert hs.timestamp is not None


class TestKeywords:
    def test_positive_keywords_exist(self):
        assert len(POSITIVE_KEYWORDS) >= 20
        assert "laba" in POSITIVE_KEYWORDS
        assert "dividen" in POSITIVE_KEYWORDS

    def test_negative_keywords_exist(self):
        assert len(NEGATIVE_KEYWORDS) >= 20
        assert "rugi" in NEGATIVE_KEYWORDS
        assert "anjlok" in NEGATIVE_KEYWORDS

    def test_all_positive_have_positive_score(self):
        for keyword, score in POSITIVE_KEYWORDS.items():
            assert score > 0, f"Keyword '{keyword}' should have positive score"

    def test_all_negative_have_negative_score(self):
        for keyword, score in NEGATIVE_KEYWORDS.items():
            assert score < 0, f"Keyword '{keyword}' should have negative score"
