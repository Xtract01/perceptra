"""VADER scoring, explicit engine metadata, and legacy file-based analysis."""

import argparse
from functools import lru_cache
from importlib.metadata import version
import json
import math

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from perceptra.schemas import ScoredReview, SentimentPrediction, SentimentSummary


class UnsupportedEngineError(ValueError):
    """An engine was requested that this installation does not implement."""


def validate_engine(engine):
    if engine != "vader":
        raise UnsupportedEngineError(
            f"Unsupported sentiment engine {engine!r}. Only local 'vader' is available; "
            "no automatic fallback or hosted inference is performed."
        )


def classify_score(compound):
    return "positive" if compound >= 0.05 else "negative" if compound <= -0.05 else "neutral"


def engine_metadata(engine="vader"):
    validate_engine(engine)
    return {"engine": "vader", "model_id": "vaderSentiment", "model_version": version("vaderSentiment"),
            "score_kind": "vader_compound"}


@lru_cache(maxsize=1)
def _analyzer():
    # Loads only package-bundled lexicons on the first explicit inference call.
    return SentimentIntensityAnalyzer()


def analyze_text(text, engine="vader") -> SentimentPrediction:
    metadata = engine_metadata(engine)
    if not isinstance(text, str):
        raise ValueError("Sentiment input must be a string.")
    raw = _analyzer().polarity_scores(text)
    return {**metadata, "label": classify_score(raw["compound"]),
            "sentiment_score": raw["compound"], "raw_scores": raw,
            "class_probabilities": None}


def score_records(records, engine="vader") -> list[ScoredReview]:
    validate_engine(engine)
    results = []
    for record in records:
        text = record.get("cleaned_text")
        likes = record.get("likes", 0)
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Scoring requires nonempty cleaned_text.")
        if isinstance(likes, bool) or not isinstance(likes, int) or likes < 0:
            raise ValueError("Likes must be a nonnegative integer.")
        prediction = analyze_text(text, engine)
        weight = 1 + math.log1p(likes)
        results.append({**record, "prediction": prediction, "likes_weight": weight,
                        "weighted_score": prediction["sentiment_score"] * weight})
    return results


def summarize_sentiment(scored_reviews) -> SentimentSummary:
    counts = dict.fromkeys(("positive", "negative", "neutral"), 0)
    for review in scored_reviews:
        counts[review["prediction"]["label"]] += 1
    total = len(scored_reviews)
    overall = None
    if total:
        total_weight = math.fsum(row["likes_weight"] for row in scored_reviews)
        overall = math.fsum(row["weighted_score"] for row in scored_reviews) / total_weight
    return {
        "analyzed_count": total, "sentiment_counts": counts,
        "sentiment_percentages": {label: count * 100 / total if total else 0.0
                                  for label, count in counts.items()},
        "overall_sentiment_score": overall,
        "perception_rating": 5 * (overall + 1) if overall is not None else None,
    }


def analyze_sentiment(input_file="cleaned_comments.json", output_file="sentiment_results.json"):
    with open(input_file, encoding="utf-8") as handle:
        comments = json.load(handle)
    if not isinstance(comments, list):
        raise ValueError("Cleaned comments JSON must contain a list.")
    records = []
    for index, item in enumerate(comments):
        if not isinstance(item, dict):
            raise ValueError(f"Invalid cleaned comment at index {index}.")
        records.append({**item, "cleaned_text": item.get("cleaned_text", item.get("cleaned_comment")),
                        "likes": item.get("likes", 0)})
    scored = score_records(records)
    summary = summarize_sentiment(scored)
    results = []
    for record in scored:
        prediction = record["prediction"]
        raw = prediction["raw_scores"]
        results.append({
            **record, "comment": record["cleaned_text"], "video_title": record.get("video_title", ""),
            "compound_score": prediction["sentiment_score"], "sentiment": prediction["label"],
            "weighted_score": round(record["weighted_score"], 4),
            "likes_weight": round(record["likes_weight"], 3),
            "positive_score": raw["pos"], "negative_score": raw["neg"], "neutral_score": raw["neu"],
        })
    with open(output_file, "w", encoding="utf-8") as handle:
        json.dump(results, handle, ensure_ascii=False, indent=2)
    rating = round(summary["perception_rating"], 1) if scored else None
    print(f"PRODUCT PERCEPTION ANALYSIS\nTotal comments analyzed: {len(scored)}")
    for label, count in summary["sentiment_counts"].items():
        print(f"{label.title()}: {count} ({summary['sentiment_percentages'][label]:.1f}%)")
    unweighted = 5 * (sum(row["prediction"]["sentiment_score"] for row in scored) / len(scored) + 1) if scored else None
    print(f"Unweighted Rating: {round(unweighted, 1) if unweighted is not None else 'N/A'}/10")
    print(f"Likes-Weighted Rating: {rating if rating is not None else 'N/A'}/10")
    for label, reverse in (("positive", True), ("negative", False)):
        print(f"Top 3 {label} comments (by weighted score):")
        subset = sorted((r for r in results if r["sentiment"] == label),
                        key=lambda r: r["weighted_score"], reverse=reverse)[:3]
        for row in subset:
            print(f"[score:{row['compound_score']} | likes:{row['likes']}] {row['comment'][:100]}")
    print(f"Saved to {output_file}")
    return results, rating, summary["overall_sentiment_score"]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="cleaned_comments.json")
    parser.add_argument("--output", default="sentiment_results.json")
    args = parser.parse_args(argv)
    try:
        analyze_sentiment(args.input, args.output)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Sentiment analysis failed: {exc}\n")


if __name__ == "__main__":
    main()
