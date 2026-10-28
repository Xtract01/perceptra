import csv
import hashlib
import json
import subprocess
import sys

import pytest

from perceptra.analysis import analyze_product
from perceptra.config import PROJECT_ROOT
from perceptra.ingestion.dataset_loader import PREPARED_FIELDS, list_products
from perceptra.nlp.sentiment import UnsupportedEngineError
from perceptra.schemas import DatasetError


def test_complete_pipeline_counts_formula_and_isolation(prepared_data):
    first = analyze_product("clothing:10", directory=prepared_data)
    second = analyze_product("clothing:20", directory=prepared_data)
    assert first["status"] == "complete"
    assert first["original_review_count"] == 3
    assert first["duplicate_count"] == 1
    assert first["analyzed_count"] == 2
    assert first["sentiment_counts"] == {"positive": 1, "negative": 1, "neutral": 0}
    for result in (first, second):
        assert result["original_review_count"] == (result["rejected_review_count"] + result["duplicate_count"]
                                                    + result["analyzed_count"])
        assert sum(result["sentiment_counts"].values()) == result["analyzed_count"]
        assert sum(result["sentiment_percentages"].values()) == pytest.approx(100)
        expected = sum(r["prediction"]["sentiment_score"] for r in result["scored_reviews"]) / result["analyzed_count"]
        assert result["overall_sentiment_score"] == pytest.approx(expected)
        assert result["perception_rating"] == pytest.approx(5 * (expected + 1))
        assert result["dataset_provenance"]["license"] == "CC0-1.0"
        assert all(r["product_id"] == result["product"]["product_id"] for r in result["scored_reviews"])
    assert not ({r["review_id"] for r in first["scored_reviews"]}
                & {r["review_id"] for r in second["scored_reviews"]})


def test_empty_product_pipeline_and_invalid_engines(prepared_data):
    path = prepared_data / "processed" / "demo_reviews.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        rows = [r for r in csv.DictReader(handle) if r["product_id"] != "clothing:10"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=PREPARED_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    manifest_path = path.with_name("manifest.json")
    manifest = json.loads(manifest_path.read_text())
    manifest["products"][0]["review_count"] = 0
    manifest["processed_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    result = analyze_product("clothing:10", directory=prepared_data)
    assert result["status"] == "no_reviews"
    assert result["overall_sentiment_score"] is None
    assert result["perception_rating"] is None
    assert result["analyzed_count"] == 0
    assert result["warnings"]
    with pytest.raises(UnsupportedEngineError):
        analyze_product("clothing:10", "huggingface", directory=prepared_data)
    with pytest.raises(DatasetError, match="Unknown product"):
        analyze_product("made-up", directory=prepared_data)


def test_real_cc0_dataset_pipeline_without_network():
    products = list_products()
    assert len(products) == 2
    for product in products:
        result = analyze_product(product["product_id"])
        assert result["status"] == "complete"
        assert result["analyzed_count"] > 0
        assert result["original_review_count"] == 200
        assert 0 <= result["perception_rating"] <= 10
        assert result["original_review_count"] == (result["analyzed_count"] + result["duplicate_count"]
                                                    + result["rejected_review_count"])
    assert "streamlit" not in sys.modules


def test_all_reviews_filtered_is_an_explicit_empty_result(prepared_data, monkeypatch):
    from perceptra.nlp import cleaner
    monkeypatch.setattr(cleaner, "is_english", lambda text: False)
    result = analyze_product("clothing:10", directory=prepared_data)
    assert result["status"] == "no_reviews"
    assert result["original_review_count"] == result["rejected_review_count"] == 3
    assert result["analyzed_count"] == result["duplicate_count"] == 0
    assert result["perception_rating"] is None


def test_cli_from_another_working_directory(prepared_data, tmp_path):
    result = subprocess.run([sys.executable, "-m", "perceptra.analysis", "--product", "clothing:10",
                             "--data-dir", str(prepared_data), "--summary"], cwd=tmp_path,
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["analyzed_count"] == 2
    invalid = subprocess.run([sys.executable, "-m", "perceptra.analysis", "--product", "invalid"],
                             cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=30)
    assert invalid.returncode == 1
    assert "Unknown product" in invalid.stderr


def test_real_aspects_are_integrated_and_do_not_change_vader():
    result = analyze_product("clothing:1078")
    analysis = result["aspect_analysis"]
    assert analysis["status"] == "available"
    assert analysis["aspects"]
    assert result["sentiment_counts"] == {"positive": 189, "negative": 9, "neutral": 2}
    assert result["perception_rating"] == pytest.approx(8.85113)
    scores = {row["review_id"]: row["prediction"]["sentiment_score"] for row in result["scored_reviews"]}
    for item in analysis["aspects"]:
        ids = item["supporting_review_ids"]
        assert len(ids) == len(set(ids)) == item["supporting_review_count"]
        assert all(identity in scores for identity in ids)
        assert item["avg_sentiment"] == pytest.approx(sum(scores[identity] for identity in ids) / len(ids))
        assert item["rating"] == pytest.approx(5 * (item["avg_sentiment"] + 1))


def test_missing_resources_preserve_sentiment(prepared_data, monkeypatch):
    from perceptra.nlp import aspects
    def missing():
        raise LookupError("Prepare local NLTK resources with prepare_demo_data.py --prepare-nltk")
    monkeypatch.setattr(aspects, "check_nltk_resources", missing)
    result = analyze_product("clothing:10", directory=prepared_data)
    assert result["status"] == "complete"
    assert result["analyzed_count"] == 2
    assert result["aspect_analysis"]["status"] == "missing_resources"
    assert result["aspect_analysis"]["aspects"] == []
    assert "prepare-nltk" in result["warnings"][0]


def test_optional_aspect_failure_does_not_erase_sentiment(prepared_data, monkeypatch):
    from perceptra import analysis
    def broken(*args):
        raise RuntimeError("Injected aspect failure")
    monkeypatch.setattr(analysis, "extract_aspects_from_records", broken)
    result = analyze_product("clothing:10", directory=prepared_data)
    assert result["status"] == "complete"
    assert result["aspect_analysis"]["status"] == "failed"
    assert result["perception_rating"] is not None
