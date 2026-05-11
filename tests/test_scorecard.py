"""Tests for stock scorecard."""
from saham_id.scorecard import ScoreCard, generate_scorecard


class TestScoreCard:
    def test_create(self):
        card = ScoreCard(ticker="BBCA", overall_score=75, recommendation="BUY")
        assert card.ticker == "BBCA"
        assert card.overall_score == 75

    def test_nonexistent(self):
        card = generate_scorecard("ZZZZZNONEXIST")
        assert card.ticker == "ZZZZZNONEXIST"
        assert "tidak" in card.recommendation.lower() or card.recommendation in ("HOLD", "SELL", "BUY", "STRONG BUY")
