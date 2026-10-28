import csv
import hashlib
import json

import pytest

from perceptra.ingestion.dataset_loader import (
    PREPARED_FIELDS, list_products, load_manifest, load_review_batch, load_reviews, prepare_dataset,
)
from perceptra.schemas import DatasetError


def rewrite_prepared(base, rows, *, count=None):
    csv_path = base / "processed" / "demo_reviews.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=PREPARED_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    path = base / "processed" / "manifest.json"
    manifest = json.loads(path.read_text())
    manifest["processed_sha256"] = hashlib.sha256(csv_path.read_bytes()).hexdigest()
    if count is not None:
        manifest["products"][0]["review_count"] = count
    path.write_text(json.dumps(manifest), encoding="utf-8")


def test_ranking_identifiers_provenance_and_no_leakage(prepared_data):
    products = list_products(prepared_data)
    assert [p["product_id"] for p in products] == ["clothing:10", "clothing:20"]
    assert products[0]["name"] == "Clothing item 10 - Dresses"
    rows = load_reviews("clothing:10", prepared_data)
    assert [r["review_id"] for r in rows] == ["wcec-v1:row:0", "wcec-v1:row:2", "wcec-v1:row:5"]
    assert all(r["likes"] == 0 for r in rows)
    assert all(r["provenance"]["source_url"].startswith("https://www.kaggle.com/") for r in rows)
    assert all(len(r["provenance"]["source_sha256"]) == 64 for r in rows)
    manifest = load_manifest(prepared_data)
    assert manifest["license"] == "CC0-1.0"
    assert manifest["source_row_count"] == 9
    assert manifest["rejected_source_row_count"] == 2
    with (prepared_data / "processed" / "demo_reviews.csv").open(newline="", encoding="utf-8") as handle:
        assert set(csv.DictReader(handle).fieldnames) == set(PREPARED_FIELDS)
    assert not {"Rating", "Recommended IND", "Positive Feedback Count"} & set(PREPARED_FIELDS)


def test_determinism_caps_and_labels_do_not_affect_selection(tmp_path, publisher_csv):
    first = prepare_dataset(publisher_csv, tmp_path / "first", max_reviews=2)
    second = prepare_dataset(publisher_csv, tmp_path / "second", max_reviews=2)
    assert first == second
    assert first["products"][0]["review_count"] == 2
    with publisher_csv.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fields, rows = reader.fieldnames, list(reader)
    for row in rows:
        row.update({"Rating": "1", "Recommended IND": "0", "Positive Feedback Count": "0"})
    with publisher_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    changed = prepare_dataset(publisher_csv, tmp_path / "changed", max_reviews=2)
    assert changed["source_sha256"] != first["source_sha256"]
    assert changed["processed_sha256"] == first["processed_sha256"]
    assert changed["products"] == first["products"]


def test_dataset_errors_are_actionable(tmp_path, prepared_data):
    with pytest.raises(DatasetError, match="prepare_demo_data"):
        list_products(tmp_path / "missing")
    with pytest.raises(DatasetError, match="Unknown product"):
        load_reviews("clothing:999", prepared_data)
    with pytest.raises(DatasetError, match="Unknown product"):
        load_reviews([], prepared_data)
    csv_path = prepared_data / "processed" / "demo_reviews.csv"
    csv_path.write_text(csv_path.read_text() + "tampered", encoding="utf-8")
    with pytest.raises(DatasetError, match="checksum mismatch"):
        load_reviews("clothing:10", prepared_data)


def test_malformed_review_is_rejected_without_mixing_products(prepared_data):
    csv_path = prepared_data / "processed" / "demo_reviews.csv"
    with csv_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    rows[0]["original_text"] = ""
    rewrite_prepared(prepared_data, rows)
    batch = load_review_batch("clothing:10", prepared_data)
    assert batch["original_count"] == 3
    assert batch["rejected_count"] == 1
    assert len(batch["reviews"]) == 2
    assert all(r["product_id"] == "clothing:10" for r in batch["reviews"])
    assert len(load_reviews("clothing:20", prepared_data)) == 3


def test_source_schema_invalid_and_empty_inputs(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("Clothing ID,Review Text\n1,hello\n", encoding="utf-8")
    with pytest.raises(DatasetError, match="requires"):
        prepare_dataset(path, tmp_path / "out")
    path.write_text("Clothing ID,Review Text,Class Name\n1,,Dresses\n", encoding="utf-8")
    with pytest.raises(DatasetError, match="no valid product reviews"):
        prepare_dataset(path, tmp_path / "out")
    assert not (tmp_path / "out").exists()


def test_missing_category_value_is_handled(tmp_path):
    path = tmp_path / "truncated.csv"
    path.write_text("Clothing ID,Review Text,Class Name\n10,This is a real input-shaped test review\n", encoding="utf-8")
    manifest = prepare_dataset(path, tmp_path / "out")
    assert manifest["products"][0]["category"] == "Unspecified"


def test_invalid_manifest_provenance_is_rejected(prepared_data):
    path = prepared_data / "processed" / "manifest.json"
    manifest = json.loads(path.read_text())
    manifest.pop("source_url")
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(DatasetError, match="provenance"):
        load_manifest(prepared_data)
