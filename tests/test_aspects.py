"""Resource safety, ID joins, token matching, ratings, and supporting evidence."""

import json
import re
from types import SimpleNamespace

import pytest

from perceptra import config
from perceptra.nlp import aspects


def test_missing_nltk_resources_have_actionable_error(monkeypatch):
    import nltk
    def missing(*args, **kwargs):
        raise LookupError("Missing fixture resource")
    monkeypatch.setattr(nltk.data, "find", missing)
    with pytest.raises(LookupError, match="prepare_demo_data.py --prepare-nltk"):
        config.check_nltk_resources()
    assert nltk.data.path == [str(config.NLTK_DATA_DIR)]


@pytest.fixture
def fixed_pos(monkeypatch):
    """Make boundary/count tests independent of statistical POS predictions."""
    monkeypatch.setattr(aspects, "check_nltk_resources", lambda: None)
    monkeypatch.setattr(aspects, "word_tokenize", lambda text: re.findall(r"\w+", text))
    monkeypatch.setattr(aspects, "pos_tag", lambda tokens: [(word, "NN") for word in tokens])
    monkeypatch.setattr(aspects, "stopwords", SimpleNamespace(words=lambda language: []))


def cleaned(identity, text):
    return {"review_id": identity, "product_id": "clothing:10", "cleaned_text": text}


def prediction(identity, score):
    return {"review_id": identity, "product_id": "clothing:10", "prediction": {"sentiment_score": score}}


def test_complete_tokens_exclude_substrings(fixed_pos):
    reviews = [cleaned("a", "size size"), cleaned("b", "oversized sizing")]
    result = aspects.extract_aspects_from_records("Product", reviews, [prediction("a", 0.8), prediction("b", -0.8)])
    size = next(item for item in result["aspects"] if item["aspect"] == "size")
    assert size["supporting_review_ids"] == ["a"]
    assert size["supporting_review_count"] == 1
    assert size["mention_count"] == 2
    assert size["rating"] == pytest.approx(9)


def test_id_join_handles_identical_text_and_reordered_predictions(fixed_pos):
    reviews = [cleaned("a", "material"), cleaned("b", "material")]
    result = aspects.extract_aspects_from_records("Product", reviews, [prediction("b", -0.4), prediction("a", 0.8)])
    material = result["aspects"][0]
    assert material["supporting_review_ids"] == ["a", "b"]
    assert material["avg_sentiment"] == pytest.approx(0.2)
    assert material["rating"] == pytest.approx(6)
    assert material["supporting_review_count"] == 2


def test_missing_prediction_is_excluded_instead_of_neutral(fixed_pos):
    reviews = [cleaned("a", "material"), cleaned("b", "material")]
    result = aspects.extract_aspects_from_records("Product", reviews, [prediction("a", 0.8)])
    assert result["status"] == "partial"
    assert result["warnings"]
    assert result["aspects"][0]["avg_sentiment"] == pytest.approx(0.8)
    assert result["aspects"][0]["supporting_review_count"] == 1


@pytest.mark.parametrize("score", [None, float("nan"), float("inf"), 2.0, "0.5"])
def test_invalid_or_absent_predictions_have_no_ratings(fixed_pos, score):
    result = aspects.extract_aspects_from_records("Product", [cleaned("a", "material material")], [prediction("a", score)])
    assert result["status"] == "no_evidence"
    assert result["aspects"] == []
    assert result["warnings"]


@pytest.mark.parametrize(("count", "tier"), [(1, "Low"), (6, "Low"), (7, "Medium"), (14, "Medium"), (15, "High")])
def test_supporting_review_counts_and_evidence_tiers(fixed_pos, count, tier):
    reviews = [cleaned(str(index), "material material") for index in range(count)]
    scored = [prediction(str(index), 0.4) for index in range(count)]
    item = aspects.extract_aspects_from_records("Product", reviews, scored)["aspects"][0]
    assert item["supporting_review_count"] == count
    assert item["mention_count"] == count * 2
    assert item["evidence_volume"] == tier


def test_empty_and_sparse_evidence(fixed_pos):
    assert aspects.extract_aspects_from_records("Product", [], [])["aspects"] == []
    result = aspects.extract_aspects_from_records("Product", [cleaned("a", "material")], [prediction("a", 0.4)])
    assert result["status"] == "no_evidence"
    assert result["aspects"] == []


def test_product_and_duplicate_id_mismatches_are_explicit(fixed_pos):
    review = cleaned("a", "material material")
    wrong_product = {**prediction("a", 0.5), "product_id": "clothing:20"}
    with pytest.raises(ValueError, match="different product"):
        aspects.extract_aspects_from_records("Product", [review], [wrong_product])
    with pytest.raises(ValueError, match="Duplicate review IDs"):
        aspects.extract_aspects_from_records("Product", [review, review], [])


def test_legacy_file_adapter_uses_new_core_and_has_no_zero_rating_for_missing_evidence(fixed_pos, tmp_path):
    input_path, score_path, output_path = (tmp_path / name for name in ("clean.json", "scores.json", "out.json"))
    input_path.write_text(json.dumps([{"cleaned_comment": "material material"}]), encoding="utf-8")
    score_path.write_text(json.dumps([{"comment": "material material", "compound_score": 0.8}]), encoding="utf-8")
    result = aspects.extract_aspects("Product", input_path, score_path, output_path)
    assert result["aspects"]["material"]["rating"] == 9.0
    assert result["aspects"]["material"]["comment_count"] == 1
    score_path.write_text("[]", encoding="utf-8")
    result = aspects.extract_aspects("Product", input_path, score_path, output_path)
    assert result["aspects"] == {}
    assert result["overall_rating"] is None
