"""Legacy aspect algorithm, migrated without Day 2 service integration."""

import argparse
import json
import nltk
from collections import Counter
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
from nltk.corpus import stopwords
from perceptra.config import check_nltk_resources

# ============================================================
# PRODUCT DIMENSION WHITELIST
# Universal across any product category
# ============================================================
product_dimensions = [
    # Performance
    "performance", "speed", "power", "engine", "motor", "battery",
    "mileage", "range", "efficiency", "consumption", "pickup",
    # Quality
    "quality", "build", "durability", "material", "finish", "reliability",
    "strength", "integrity", "construction",
    # Design
    "design", "looks", "style", "appearance", "aesthetics", "color",
    "colour", "shape", "size", "weight", "display", "screen",
    # Comfort
    "comfort", "seat", "space", "room", "interior", "cabin",
    "suspension", "noise", "vibration", "smoothness", "ergonomics",
    # Features
    "features", "technology", "connectivity", "bluetooth", "camera",
    "headlight", "light", "lamp", "infotainment", "airbag", "safety",
    "sensor", "control", "system", "charging", "carplay",
    # Price
    "price", "cost", "value", "budget", "money", "worth",
    # Service
    "service", "maintenance", "support", "warranty", "repair",
    # Automotive specific but generic enough
    "gearbox", "steering", "brake", "tire", "tyre", "wheel",
    "fuel", "torque", "clearance", "headroom", "legroom", "kneeroom",
    "transmission", "clutch", "gear", "acceleration",
    # Electronics specific
    "processor", "ram", "storage", "speaker", "sound", "audio",
    "resolution", "refresh", "zoom", "lens", "flash",
    # General
    "rating", "crash", "test", "review", "safety", "standard"
]

def extract_aspects(search_term, input_file="cleaned_comments.json",
                    sentiment_file="sentiment_results.json",
                    output_file="aspect_results.json"):

    check_nltk_resources()

    # ============================================================
    # LOAD DATA
    # ============================================================
    with open(input_file, "r", encoding="utf-8") as f:
        comments = json.load(f)

    with open(sentiment_file, "r", encoding="utf-8") as f:
        sentiment_data = json.load(f)

    sentiment_lookup = {item["comment"]: item["compound_score"] for item in sentiment_data}
    texts = [item["cleaned_comment"] for item in comments]

    # ============================================================
    # STOPWORDS
    # ============================================================
    universal_stopwords = [
        "like", "better", "good", "best", "just", "really", "think", "know",
        "old", "new", "one", "get", "got", "even", "also", "still", "would",
        "could", "should", "version", "review", "video", "yes", "no", "not",
        "want", "need", "make", "take", "come", "going", "thing", "way",
        "use", "used", "using", "time", "year", "years", "people", "person",
        "owner", "ownership", "said", "please", "thanks", "thank", "great",
        "nice", "bad", "worst", "amazing", "awesome", "terrible", "horrible",
        "excellent", "bro", "bhai", "buy", "lakh", "lakhs", "bought",
        "purchase", "purchased", "recommend", "worth", "overall", "actually",
        "basically", "literally", "totally", "absolutely", "definitely",
        "probably", "maybe", "perhaps", "sure", "okay", "does", "dont",
        "did", "do", "has", "have", "had", "was", "were", "is", "are",
        "been", "being", "give", "given", "gave", "put", "look", "looks",
        "feel", "feels", "seem", "seems", "tell", "say", "says", "ask",
        "drive", "driving", "driven", "road", "car", "vehicle"
    ]

    # Dynamic stopwords from search term only
    dynamic_stopwords = [word.lower() for word in search_term.split()]

    nltk_stopwords = set(stopwords.words("english"))
    all_stopwords = nltk_stopwords.union(set(universal_stopwords + dynamic_stopwords))

    # ============================================================
    # STEP 1: EXTRACT NOUNS USING POS TAGGING
    # ============================================================
    noun_candidates = []
    for text in texts:
        tokens = word_tokenize(text.lower())
        tagged = pos_tag(tokens)
        for word, tag in tagged:
            if tag in ("NN", "NNS"):
                if word not in all_stopwords and len(word) > 3:
                    noun_candidates.append(word)

    noun_freq = Counter(noun_candidates)

    # ============================================================
    # STEP 2: FILTER TO PRODUCT DIMENSIONS ONLY
    # ============================================================
    filtered_aspects = []
    for word, count in noun_freq.most_common(50):
        if count >= 2:
            if any(dim in word or word in dim for dim in product_dimensions):
                filtered_aspects.append(word)
        if len(filtered_aspects) == 10:
            break

    # Fallback if less than 5 genuine aspects found
    if len(filtered_aspects) < 5:
        top_aspects = [word for word, count in noun_freq.most_common(20) if count >= 2][:10]
        print("(Using fallback aspect extraction)")
    else:
        top_aspects = filtered_aspects

    print(f"PRODUCT: {search_term.upper()}")
    print(f"\nAUTO-DETECTED ASPECTS:")
    print("="*50)
    for i, aspect in enumerate(top_aspects, 1):
        print(f"{i}. {aspect} (mentioned {noun_freq[aspect]} times)")

    # ============================================================
    # STEP 3: SCORE EACH ASPECT
    # ============================================================
    print(f"\nASPECT SENTIMENT ANALYSIS:")
    print("="*50)

    aspect_results = {}
    for aspect in top_aspects:
        relevant_scores = []
        for item in comments:
            if aspect.lower() in item["cleaned_comment"].lower():
                score = sentiment_lookup.get(item["cleaned_comment"], 0)
                relevant_scores.append(score)

        if relevant_scores:
            avg_sentiment = sum(relevant_scores) / len(relevant_scores)
            rating = round((avg_sentiment + 1) * 5, 1)
            comment_count = len(relevant_scores)
            sentiment_label = (
                "Positive" if avg_sentiment > 0.05
                else "Negative" if avg_sentiment < -0.05
                else "Neutral"
            )

            # Confidence scoring
            if comment_count >= 15:
                confidence = "High"
            elif comment_count >= 7:
                confidence = "Medium"
            else:
                confidence = "Low"

            aspect_results[aspect] = {
                "rating": rating,
                "sentiment": sentiment_label,
                "comment_count": comment_count,
                "avg_score": round(avg_sentiment, 3),
                "confidence": confidence,
                "mention_count": noun_freq[aspect]
            }

            print(f"{aspect.upper():<20} | {rating}/10 | {sentiment_label:<10} | {confidence:<8} confidence | {comment_count} comments")

    # ============================================================
    # STEP 4: OVERALL RATING
    # ============================================================
    overall_rating = 0
    if aspect_results:
        overall_score = sum(r["avg_score"] for r in aspect_results.values()) / len(aspect_results)
        overall_rating = round((overall_score + 1) * 5, 1)

        positive_aspects = [k for k, v in aspect_results.items() if v["sentiment"] == "Positive"]
        negative_aspects = [k for k, v in aspect_results.items() if v["sentiment"] == "Negative"]
        neutral_aspects  = [k for k, v in aspect_results.items() if v["sentiment"] == "Neutral"]

        print(f"\nOVERALL PRODUCT RATING : {overall_rating}/10")
        print("="*50)
        print(f"Strongest aspects : {', '.join(positive_aspects) if positive_aspects else 'None'}")
        print(f"Weakest aspects   : {', '.join(negative_aspects) if negative_aspects else 'None'}")
        print(f"Neutral aspects   : {', '.join(neutral_aspects)  if neutral_aspects  else 'None'}")

    # ============================================================
    # STEP 5: SAVE
    # ============================================================
    output = {
        "search_term": search_term,
        "overall_rating": overall_rating,
        "total_comments_analyzed": len(comments),
        "aspects": aspect_results
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"\nSaved to aspect_results.json")
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
