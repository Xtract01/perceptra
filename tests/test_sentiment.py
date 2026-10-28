import json
import math

import pytest

from perceptra.nlp.sentiment import (
    UnsupportedEngineError, analyze_sentiment, analyze_text, classify_score,
    score_records, summarize_sentiment,
)


@pytest.mark.parametrize(("text", "label"), [
    ("I absolutely love this wonderful dress!", "positive"),
    ("I hate this awful and terrible dress!", "negative"),
    ("The item is on the table.", "neutral"),
    ("", "neutral"),
])
def test_actual_vader_classification(text, label):
    prediction = analyze_text(text)
    assert prediction["label"] == label
    assert prediction["sentiment_score"] == prediction["raw_scores"]["compound"]
    assert prediction["score_kind"] == "vader_compound"
    assert prediction["engine"] == "vader"
    assert prediction["model_id"] == "vaderSentiment"
    assert prediction["model_version"]
    assert prediction["class_probabilities"] is None


@pytest.mark.parametrize(("score", "label"), [
    (0.05, "positive"), (-0.05, "negative"), (0.0499, "neutral"), (-0.0499, "neutral"),
])
def test_threshold_boundaries(score, label):
    assert classify_score(score) == label


def test_unsupported_engine_does_not_fallback():
    with pytest.raises(UnsupportedEngineError, match="no automatic fallback"):
        analyze_text("I love this", engine="huggingface")
    with pytest.raises(ValueError, match="string"):
        analyze_text(None)


def test_original_likes_weighting_and_rating_formula():
    rows = [
        {"cleaned_text": "I absolutely love this dress!", "likes": 99},
        {"cleaned_text": "I hate this terrible dress!", "likes": 0},
    ]
    scored = score_records(rows)
    assert scored[0]["likes_weight"] == pytest.approx(1 + math.log(100))
    first = analyze_text(rows[0]["cleaned_text"])["sentiment_score"]
    second = analyze_text(rows[1]["cleaned_text"])["sentiment_score"]
    expected = (first * (1 + math.log(100)) + second) / (2 + math.log(100))
    summary = summarize_sentiment(scored)
    assert summary["overall_sentiment_score"] == pytest.approx(expected)
    assert summary["perception_rating"] == pytest.approx(5 * (expected + 1))
    assert summary["sentiment_counts"] == {"positive": 1, "negative": 1, "neutral": 0}
    assert sum(summary["sentiment_percentages"].values()) == pytest.approx(100)


def test_empty_summary_and_legacy_file_result(tmp_path):
    summary = summarize_sentiment([])
    assert summary["overall_sentiment_score"] is None
    assert summary["perception_rating"] is None
    path = tmp_path / "input.json"
    output = tmp_path / "output.json"
    path.write_text("[]", encoding="utf-8")
    assert analyze_sentiment(path, output) == ([], None, None)
    assert json.loads(output.read_text()) == []


def test_legacy_json_shape_and_return_tuple(tmp_path):
    path = tmp_path / "input.json"
    output = tmp_path / "output.json"
    path.write_text(json.dumps([{"cleaned_comment": "This dress is wonderful and I love it!",
                                 "likes": 0, "video_title": "Example"}]), encoding="utf-8")
    rows, rating, overall = analyze_sentiment(path, output)
    assert rows[0]["sentiment"] == "positive"
    assert rows[0]["video_title"] == "Example"
    assert rows[0]["compound_score"] == analyze_text(rows[0]["comment"])["sentiment_score"]
    assert rating == round(5 * (overall + 1), 1)


@pytest.mark.parametrize("likes", [-1, True, "3", float("nan")])
def test_invalid_likes_are_rejected(likes):
    with pytest.raises(ValueError, match="nonnegative integer"):
        score_records([{"cleaned_text": "This dress is great.", "likes": likes}])
