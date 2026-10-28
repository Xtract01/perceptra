"""POS/frequency aspect estimates joined to whole-review sentiment by stable ID."""

import argparse
from collections import Counter
import json
import math

from nltk.corpus import stopwords
from nltk.tag import pos_tag
from nltk.tokenize import word_tokenize

from perceptra.config import check_nltk_resources
from perceptra.nlp.sentiment import classify_score
from perceptra.schemas import AspectAnalysis

product_dimensions = ['performance',
 'speed',
 'power',
 'engine',
 'motor',
 'battery',
 'mileage',
 'range',
 'efficiency',
 'consumption',
 'pickup',
 'quality',
 'build',
 'durability',
 'material',
 'finish',
 'reliability',
 'strength',
 'integrity',
 'construction',
 'design',
 'looks',
 'style',
 'appearance',
 'aesthetics',
 'color',
 'colour',
 'shape',
 'size',
 'weight',
 'display',
 'screen',
 'comfort',
 'seat',
 'space',
 'room',
 'interior',
 'cabin',
 'suspension',
 'noise',
 'vibration',
 'smoothness',
 'ergonomics',
 'features',
 'technology',
 'connectivity',
 'bluetooth',
 'camera',
 'headlight',
 'light',
 'lamp',
 'infotainment',
 'airbag',
 'safety',
 'sensor',
 'control',
 'system',
 'charging',
 'carplay',
 'price',
 'cost',
 'value',
 'budget',
 'money',
 'worth',
 'service',
 'maintenance',
 'support',
 'warranty',
 'repair',
 'gearbox',
 'steering',
 'brake',
 'tire',
 'tyre',
 'wheel',
 'fuel',
 'torque',
 'clearance',
 'headroom',
 'legroom',
 'kneeroom',
 'transmission',
 'clutch',
 'gear',
 'acceleration',
 'processor',
 'ram',
 'storage',
 'speaker',
 'sound',
 'audio',
 'resolution',
 'refresh',
 'zoom',
 'lens',
 'flash',
 'rating',
 'crash',
 'test',
 'review',
 'safety',
 'standard']

UNIVERSAL_STOPWORDS = ['like',
 'better',
 'good',
 'best',
 'just',
 'really',
 'think',
 'know',
 'old',
 'new',
 'one',
 'get',
 'got',
 'even',
 'also',
 'still',
 'would',
 'could',
 'should',
 'version',
 'review',
 'video',
 'yes',
 'no',
 'not',
 'want',
 'need',
 'make',
 'take',
 'come',
 'going',
 'thing',
 'way',
 'use',
 'used',
 'using',
 'time',
 'year',
 'years',
 'people',
 'person',
 'owner',
 'ownership',
 'said',
 'please',
 'thanks',
 'thank',
 'great',
 'nice',
 'bad',
 'worst',
 'amazing',
 'awesome',
 'terrible',
 'horrible',
 'excellent',
 'bro',
 'bhai',
 'buy',
 'lakh',
 'lakhs',
 'bought',
 'purchase',
 'purchased',
 'recommend',
 'worth',
 'overall',
 'actually',
 'basically',
 'literally',
 'totally',
 'absolutely',
 'definitely',
 'probably',
 'maybe',
 'perhaps',
 'sure',
 'okay',
 'does',
 'dont',
 'did',
 'do',
 'has',
 'have',
 'had',
 'was',
 'were',
 'is',
 'are',
 'been',
 'being',
 'give',
 'given',
 'gave',
 'put',
 'look',
 'looks',
 'feel',
 'feels',
 'seem',
 'seems',
 'tell',
 'say',
 'says',
 'ask',
 'drive',
 'driving',
 'driven',
 'road',
 'car',
 'vehicle']

ASPECT_METHOD = "noun_frequency_whole_review_sentiment"
ASPECT_EXPLANATION = (
    "Aspect ratings are estimates from whole-review VADER sentiment, not contextual "
    "aspect-based sentiment analysis. Evidence volume describes review support, not model accuracy."
)


def evidence_volume(count):
    return "High" if count >= 15 else "Medium" if count >= 7 else "Low"


def extract_aspects_from_records(search_term, cleaned_reviews, scored_reviews) -> AspectAnalysis:
    """Keep the existing noun ranking/fallback; never infer a missing prediction as neutral."""
    base = {"method": ASPECT_METHOD, "explanation": ASPECT_EXPLANATION,
            "aspects": [], "warnings": [], "used_fallback": False}
    if not cleaned_reviews:
        return {**base, "status": "no_evidence"}
    check_nltk_resources()
    products = {review["product_id"] for review in cleaned_reviews}
    if len(products) != 1:
        raise ValueError("Aspect extraction requires reviews from exactly one product.")
    product_id = next(iter(products))
    review_ids = [review["review_id"] for review in cleaned_reviews]
    if len(set(review_ids)) != len(review_ids):
        raise ValueError("Duplicate review IDs in aspect input.")
    predictions = {}
    for row in scored_reviews:
        review_id = row["review_id"]
        if row["product_id"] != product_id:
            raise ValueError("Aspect sentiment predictions belong to a different product.")
        if review_id in predictions:
            raise ValueError("Duplicate sentiment prediction review ID.")
        predictions[review_id] = row.get("prediction", {}).get("sentiment_score")

    all_stopwords = set(stopwords.words("english")) | set(UNIVERSAL_STOPWORDS)
    all_stopwords.update(word.casefold() for word in search_term.split())
    noun_candidates = []
    token_sets = {}
    for review in cleaned_reviews:
        tokens = word_tokenize(review["cleaned_text"].casefold())
        token_sets[review["review_id"]] = set(tokens)
        tagged = pos_tag(tokens)
        noun_candidates.extend(word for word, tag in tagged
                               if tag in ("NN", "NNS") and word not in all_stopwords and len(word) > 3)
    noun_freq = Counter(noun_candidates)
    dimensions = set(product_dimensions)
    filtered = [word for word, count in noun_freq.most_common(50)
                if count >= 2 and word in dimensions][:10]
    use_fallback = len(filtered) < 5
    top_aspects = ([word for word, count in noun_freq.most_common(20) if count >= 2][:10]
                   if use_fallback else filtered)

    valid_scores = {}
    for review_id in review_ids:
        score = predictions.get(review_id)
        if isinstance(score, (int, float)) and not isinstance(score, bool) and math.isfinite(score) and -1 <= score <= 1:
            valid_scores[review_id] = score
    missing_count = len(review_ids) - len(valid_scores)
    warnings = []
    if missing_count:
        warnings.append(f"Excluded {missing_count} reviews with missing or invalid sentiment predictions from aspect ratings.")
    results = []
    for aspect in top_aspects:
        supporting = [review_id for review_id in review_ids
                      if review_id in valid_scores and aspect in token_sets[review_id]]
        if not supporting:
            continue
        average = math.fsum(valid_scores[review_id] for review_id in supporting) / len(supporting)
        results.append({
            "aspect": aspect, "rating": 5 * (average + 1), "avg_sentiment": average,
            "sentiment": classify_score(average), "supporting_review_count": len(supporting),
            "supporting_review_ids": supporting, "mention_count": noun_freq[aspect],
            "evidence_volume": evidence_volume(len(supporting)),
        })
    return {**base, "status": "partial" if results and missing_count else "available" if results else "no_evidence",
            "aspects": results, "warnings": warnings, "used_fallback": use_fallback}


def extract_aspects(search_term, input_file="cleaned_comments.json",
                    sentiment_file="sentiment_results.json", output_file="aspect_results.json"):
    """Legacy file adapter. Only legacy files without IDs need text-to-ID adaptation."""
    with open(input_file, encoding="utf-8") as handle:
        comments = json.load(handle)
    with open(sentiment_file, encoding="utf-8") as handle:
        sentiment_data = json.load(handle)
    if not isinstance(comments, list) or not isinstance(sentiment_data, list):
        raise ValueError("Aspect inputs must be JSON lists.")
    cleaned = []
    ids_by_text = {}
    for index, item in enumerate(comments):
        identity = item.get("review_id", f"legacy:{index}")
        text = item["cleaned_comment"]
        product_id = item.get("product_id", search_term)
        cleaned.append({"review_id": identity, "product_id": product_id, "cleaned_text": text})
        ids_by_text.setdefault(text, []).append((identity, product_id))
    by_id = {row["review_id"]: row["product_id"] for row in cleaned}
    scored = []
    for row in sentiment_data:
        identities = ([(row["review_id"], by_id.get(row["review_id"], search_term))]
                      if row.get("review_id") else ids_by_text.get(row.get("comment"), []))
        for identity, product_id in identities:
            scored.append({"review_id": identity, "product_id": product_id,
                           "prediction": {"sentiment_score": row.get("compound_score")}})
    result = extract_aspects_from_records(search_term, cleaned, scored)
    legacy_aspects = {
        item["aspect"]: {"rating": round(item["rating"], 1), "sentiment": item["sentiment"].title(),
                         "comment_count": item["supporting_review_count"], "avg_score": round(item["avg_sentiment"], 3),
                         "confidence": item["evidence_volume"], "mention_count": item["mention_count"],
                         "supporting_review_ids": item["supporting_review_ids"]}
        for item in result["aspects"]
    }
    mean = (math.fsum(item["avg_sentiment"] for item in result["aspects"]) / len(result["aspects"])
            if result["aspects"] else None)
    output = {"search_term": search_term, "overall_rating": round(5 * (mean + 1), 1) if mean is not None else None,
              "total_comments_analyzed": len(comments), "aspects": legacy_aspects,
              "warnings": result["warnings"], "method": ASPECT_METHOD, "explanation": ASPECT_EXPLANATION}
    with open(output_file, "w", encoding="utf-8") as handle:
        json.dump(output, handle, ensure_ascii=False, indent=2)
    print(f"PRODUCT: {search_term.upper()}")
    for name, item in legacy_aspects.items():
        print(f"{name}: {item['rating']}/10 | {item['comment_count']} supporting reviews | {item['confidence']} evidence volume")
    print(f"Saved to {output_file}")
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", default="Hyundai i10 review")
    parser.add_argument("--input", default="cleaned_comments.json")
    parser.add_argument("--sentiment", default="sentiment_results.json")
    parser.add_argument("--output", default="aspect_results.json")
    args = parser.parse_args(argv)
    try:
        extract_aspects(args.query, args.input, args.sentiment, args.output)
    except (OSError, ValueError, LookupError) as exc:
        parser.exit(1, f"Aspect extraction failed: {exc}\n")


if __name__ == "__main__":
    main()
