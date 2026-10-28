"""Shared, JSON-serializable contracts for processing and future presentation."""

from typing import Literal, TypedDict

SentimentLabel = Literal["positive", "negative", "neutral"]


class DatasetError(ValueError):
    """The local dataset is missing, invalid, or inconsistent with its manifest."""


class Product(TypedDict):
    product_id: str
    clothing_id: int
    name: str
    category: str
    department: str
    division: str
    review_count: int
    available_source_reviews: int


class ReviewRecord(TypedDict):
    review_id: str
    product_id: str
    source: str
    original_text: str
    likes: int
    provenance: dict


class CleanedReview(ReviewRecord):
    cleaned_text: str


class CleaningStats(TypedDict):
    original_count: int
    rejected_count: int
    duplicate_count: int
    analyzed_count: int
    rejection_reasons: dict[str, int]


class SentimentPrediction(TypedDict):
    label: SentimentLabel
    sentiment_score: float | None
    score_kind: str
    engine: str
    model_id: str
    model_version: str
    raw_scores: dict[str, float]
    class_probabilities: dict[str, float] | None


class ScoredReview(CleanedReview):
    prediction: SentimentPrediction
    likes_weight: float
    weighted_score: float


class SentimentSummary(TypedDict):
    analyzed_count: int
    sentiment_counts: dict[str, int]
    sentiment_percentages: dict[str, float]
    overall_sentiment_score: float | None
    perception_rating: float | None


class ReviewBatch(TypedDict):
    reviews: list[ReviewRecord]
    original_count: int
    rejected_count: int
    warnings: list[str]


class AnalysisResult(SentimentSummary):
    status: Literal["complete", "no_reviews"]
    product: Product
    dataset_provenance: dict
    original_review_count: int
    rejected_review_count: int
    duplicate_count: int
    rejection_reasons: dict[str, int]
    engine: str
    model_id: str
    model_version: str
    score_kind: str
    scored_reviews: list[ScoredReview]
    warnings: list[str]
    limitations: list[str]
