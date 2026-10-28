"""Authored fixtures are synthetic tests, never demonstration product data."""

import csv
import socket

import pytest

from perceptra.ingestion.dataset_loader import prepare_dataset


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Tests and inference must not access the network")
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    import nltk
    monkeypatch.setattr(nltk, "download", forbidden)


@pytest.fixture
def record():
    return {"review_id": "fixture:1", "product_id": "clothing:10", "source": "authored-test",
            "original_text": "This dress is wonderful and I absolutely love it!", "likes": 0,
            "provenance": {"source_row": "1"}}


@pytest.fixture
def publisher_csv(tmp_path):
    path = tmp_path / "publisher.csv"
    fields = ["", "Clothing ID", "Review Text", "Class Name", "Department Name", "Division Name",
              "Rating", "Recommended IND", "Positive Feedback Count"]
    entries = [
        ("0", "10", "This dress is wonderful and I absolutely love it!"),
        ("1", "20", "This sweater is awful and I really hate it!"),
        ("2", "10", "The quality of this dress is absolutely terrible."),
        ("3", "20", "This sweater is wonderful and extremely comfortable to wear."),
        ("4", "30", "This jacket is lovely and very nice to wear."),
        ("5", "10", "This dress is wonderful and I absolutely love it!"),
        ("6", "20", "The sweater is on the table near the window."),
        ("7", "10", ""),
        ("8", "not-an-id", "This invalid item is nevertheless described in English."),
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for identity, product, text in entries:
            writer.writerow({"": identity, "Clothing ID": product, "Review Text": text,
                             "Class Name": "Dresses" if product == "10" else "Knits",
                             "Department Name": "Clothing", "Division Name": "General",
                             "Rating": "5", "Recommended IND": "1", "Positive Feedback Count": "999"})
    return path


@pytest.fixture
def prepared_data(tmp_path, publisher_csv):
    base = tmp_path / "data"
    prepare_dataset(publisher_csv, base / "processed")
    return base
