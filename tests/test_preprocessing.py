import json

from perceptra.nlp.cleaner import clean_comment, clean_pipeline, clean_records, is_english, is_useful, remove_duplicates


def test_sentiment_cues_are_preserved():
    text = "  I DON'T love this café dress!!!\nVisit https://example.com  "
    assert clean_comment(text) == "I DON'T love this café dress!!! Visit"
    assert is_useful("Is this dress good for summer?") is False
    assert is_english("This is a wonderful dress that I love.")
    assert not is_english("This dress works well")  # Preserve the existing five-word minimum.


def test_validation_deduplication_and_identity(record):
    original = record.copy()
    duplicate = {**record, "review_id": "fixture:2", "original_text": record["original_text"].lower()}
    other_product = {**record, "product_id": "clothing:20"}
    invalid_likes = {**record, "likes": -1}
    rows, stats = clean_records([record, duplicate, other_product, None, invalid_likes])
    assert len(rows) == 2
    assert stats == {"original_count": 5, "rejected_count": 2, "duplicate_count": 1,
                     "analyzed_count": 2, "rejection_reasons": {"invalid_record": 2}}
    assert record == original
    assert rows[0]["provenance"] == record["provenance"]
    assert rows[0]["original_text"] == record["original_text"]
    assert rows[0]["review_id"] == record["review_id"]


def test_filters_and_empty_records(record):
    rows, stats = clean_records([
        {**record, "original_text": "This is short"},
        {**record, "original_text": "Is this dress good for summer?"},
        {**record, "original_text": "Ce vêtement est vraiment horrible et très inconfortable."},
    ])
    assert rows == []
    assert stats["rejected_count"] == 3
    assert clean_records([])[1]["analyzed_count"] == 0


def test_legacy_wrappers_preserve_fields_and_dedup(tmp_path):
    import clean_data
    assert clean_data.clean_pipeline is clean_pipeline
    source = tmp_path / "raw.json"
    target = tmp_path / "cleaned.json"
    source.write_text(json.dumps([{
        "comment": "I don't like this awful camera at all!", "likes": 7,
        "search_term": "Camera", "video_id": "abc", "video_title": "Camera review",
    }]), encoding="utf-8")
    output = clean_pipeline(source, target)
    assert output[0]["video_id"] == "abc"
    assert output[0]["likes"] == 7
    assert "don't" in output[0]["cleaned_comment"]
    assert "review_id" in output[0]
    assert len(remove_duplicates(output + output)) == 1
