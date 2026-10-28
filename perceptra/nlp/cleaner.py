"""Conservative preprocessing and compatibility with legacy JSON inputs."""

import argparse
from collections import Counter
from collections.abc import Mapping
import hashlib
import json
import re

from langdetect import DetectorFactory, detect
from langdetect.lang_detect_exception import LangDetectException

from perceptra.schemas import CleanedReview, CleaningStats

DetectorFactory.seed = 0


def is_english(text, min_words=5):
    if not isinstance(text, str) or len(text.split()) < min_words:
        return False
    try:
        return detect(text) == "en"
    except LangDetectException:
        return False


def clean_comment(text):
    if not isinstance(text, str):
        raise ValueError("Review text must be a string.")
    # Preserve case, Unicode, negation and emphasis; do not strip punctuation.
    text = re.sub(r"(?:https?://|www\.)\S+", "", text, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", text).strip()


def is_useful(text):
    if not isinstance(text, str) or len(text.split()) < 4:
        return False
    return re.match(r"^[^.!]*\?$", text.strip()) is None


def remove_duplicates(comments):
    """Legacy helper, with duplicate identity scoped to the product."""
    seen = set()
    unique = []
    for item in comments:
        product = item.get("product_id", item.get("search_term", "legacy"))
        key = (product, item["cleaned_comment"].casefold().strip())
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


def clean_records(records) -> tuple[list[CleanedReview], CleaningStats]:
    if not isinstance(records, (list, tuple)):
        raise ValueError("Reviews must be a list of records.")
    cleaned = []
    reasons = Counter()
    seen_texts = set()
    seen_ids = set()
    duplicates = 0
    for item in records:
        if not isinstance(item, Mapping):
            reasons["invalid_record"] += 1
            continue
        text = item.get("original_text")
        identifiers = [item.get("review_id"), item.get("product_id"), item.get("source")]
        likes = item.get("likes", 0)
        if (
            not isinstance(text, str) or not text.strip()
            or any(not isinstance(value, str) or not value.strip() for value in identifiers)
            or isinstance(likes, bool) or not isinstance(likes, int) or likes < 0
            or not isinstance(item.get("provenance", {}), Mapping)
        ):
            reasons["invalid_record"] += 1
            continue
        normalized = clean_comment(text)
        if not is_english(normalized):
            reasons["language_or_short_text"] += 1
            continue
        if not is_useful(normalized):
            reasons["unusable_text"] += 1
            continue
        text_key = (item["product_id"], normalized.casefold())
        if text_key in seen_texts:
            duplicates += 1
            continue
        id_key = (item["product_id"], item["review_id"])
        if id_key in seen_ids:
            reasons["duplicate_identifier"] += 1
            continue
        seen_texts.add(text_key)
        seen_ids.add(id_key)
        cleaned.append({
            "review_id": item["review_id"], "product_id": item["product_id"],
            "source": item["source"], "original_text": text, "likes": likes,
            "provenance": dict(item.get("provenance", {})), "cleaned_text": normalized,
        })
    return cleaned, {
        "original_count": len(records), "rejected_count": sum(reasons.values()),
        "duplicate_count": duplicates, "analyzed_count": len(cleaned),
        "rejection_reasons": dict(reasons),
    }


def clean_pipeline(input_file="raw_comments.json", output_file="cleaned_comments.json"):
    with open(input_file, encoding="utf-8") as handle:
        comments = json.load(handle)
    if not isinstance(comments, list):
        raise ValueError("Raw comments JSON must contain a list.")
    records = []
    originals = {}
    for index, item in enumerate(comments):
        if not isinstance(item, dict):
            records.append(item)
            continue
        product = item.get("product_id", item.get("search_term", "legacy"))
        digest = hashlib.sha256(str(product).encode()).hexdigest()[:12]
        review_id = item.get("review_id", f"legacy:{digest}:{index}")
        records.append({
            "review_id": review_id, "product_id": product,
            "source": item.get("source", "youtube"),
            "original_text": item.get("original_text", item.get("comment")),
            "likes": item.get("likes", 0), "provenance": item.get("provenance", {}),
        })
        if isinstance(product, str) and isinstance(review_id, str):
            originals.setdefault((product, review_id), item)
    cleaned, stats = clean_records(records)
    output = []
    for record in cleaned:
        original = originals[(record["product_id"], record["review_id"])]
        output.append({
            **original, **record, "original_comment": record["original_text"],
            "cleaned_comment": record["cleaned_text"],
            "video_title": original.get("video_title", ""),
            "search_term": original.get("search_term", record["product_id"]),
        })
    with open(output_file, "w", encoding="utf-8") as handle:
        json.dump(output, handle, ensure_ascii=False, indent=2)
    print(f"Analyzed {len(output)} usable reviews; rejected {stats['rejected_count']}; "
          f"duplicates {stats['duplicate_count']}. Saved to {output_file}")
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="raw_comments.json")
    parser.add_argument("--output", default="cleaned_comments.json")
    args = parser.parse_args(argv)
    try:
        clean_pipeline(args.input, args.output)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Preprocessing failed: {exc}\n")


if __name__ == "__main__":
    main()
