
import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# ============================================================
# CONFIGURATION - This will come from user input later
# ============================================================
search_term = "Hyundai i10 review"

# ============================================================
# LOAD DATA
# ============================================================
with open("cleaned_comments.json", "r", encoding="utf-8") as f:
    comments = json.load(f)

with open("sentiment_results.json", "r", encoding="utf-8") as f:
    sentiment_data = json.load(f)

sentiment_lookup = {item["comment"]: item["compound_score"] for item in sentiment_data}
texts = [item["cleaned_comment"] for item in comments]

# ============================================================
# STOPWORDS - Two layers
# ============================================================

# Layer 1: Universal - works for any product
universal_stopwords = [
    "like", "better", "good", "best", "just", "really", "think", "know",
    "old", "new", "one", "get", "got", "even", "also", "still",
    "would", "could", "should", "version", "review", "video",
    "yes", "no", "not", "want", "need", "make", "take", "come",
    "going", "thing", "way", "use", "used", "using", "time", "year",
    "years", "people", "person", "owner", "ownership", "said",
    "please", "thanks", "thank", "great", "nice", "bad", "worst",
    "amazing", "awesome", "terrible", "horrible", "excellent",
    "bro", "bhai", "buy", "lakh", "lakhs", "bought", "purchase",
    "purchased", "recommend", "recommended", "worth", "overall",
    "actually", "basically", "literally", "totally", "absolutely",
    "definitely", "probably", "maybe", "perhaps", "sure", "okay"
]

# Layer 2: Dynamic - auto generated from search term
dynamic_stopwords = [word.lower() for word in search_term.split()]

# Combine all stopwords
all_stopwords = list(ENGLISH_STOP_WORDS) + universal_stopwords + dynamic_stopwords

# ============================================================
# STEP 1: EXTRACT DYNAMIC ASPECTS USING TF-IDF
# ============================================================
vectorizer = TfidfVectorizer(
    max_features=50,
    stop_words=all_stopwords,
    ngram_range=(1, 2),
    min_df=2
)

tfidf_matrix = vectorizer.fit_transform(texts)
feature_names = vectorizer.get_feature_names_out()

avg_scores = np.mean(tfidf_matrix.toarray(), axis=0)
keyword_scores = list(zip(feature_names, avg_scores))
keyword_scores.sort(key=lambda x: x[1], reverse=True)

top_keywords = [kw for kw, score in keyword_scores[:10]]

print(f"PRODUCT: {search_term.upper()}")
print(f"\nAUTO-DETECTED ASPECTS:")
print("="*50)
for i, kw in enumerate(top_keywords, 1):
    print(f"{i}. {kw}")

# ============================================================
# STEP 2: SCORE EACH ASPECT
# ============================================================
analyzer = SentimentIntensityAnalyzer()

print(f"\nASPECT SENTIMENT ANALYSIS:")
print("="*50)

aspect_results = {}
for keyword in top_keywords:
    relevant_comments = []

    for item in comments:
        if keyword.lower() in item["cleaned_comment"].lower():
            score = sentiment_lookup.get(item["cleaned_comment"], 0)
            relevant_comments.append(score)

    if relevant_comments:
        avg_sentiment = sum(relevant_comments) / len(relevant_comments)
        rating = round((avg_sentiment + 1) * 5, 1)
        sentiment_label = (
            "Positive" if avg_sentiment > 0.05
            else "Negative" if avg_sentiment < -0.05
            else "Neutral"
        )

        aspect_results[keyword] = {
            "rating": rating,
            "sentiment": sentiment_label,
            "comment_count": len(relevant_comments),
            "avg_score": round(avg_sentiment, 3)
        }

        print(f"{keyword.upper():<20} | {rating}/10 | {sentiment_label:<10} | {len(relevant_comments)} comments")

# ============================================================
# STEP 3: OVERALL PRODUCT RATING
# ============================================================
if aspect_results:
    overall_score = sum(r["avg_score"] for r in aspect_results.values()) / len(aspect_results)
    overall_rating = round((overall_score + 1) * 5, 1)

    positive_aspects = [k for k, v in aspect_results.items() if v["sentiment"] == "Positive"]
    negative_aspects = [k for k, v in aspect_results.items() if v["sentiment"] == "Negative"]
    neutral_aspects  = [k for k, v in aspect_results.items() if v["sentiment"] == "Neutral"]

    print(f"\nOVERALL PRODUCT RATING: {overall_rating}/10")
    print("="*50)
    print(f"Strongest aspects : {', '.join(positive_aspects) if positive_aspects else 'None'}")
    print(f"Weakest aspects   : {', '.join(negative_aspects) if negative_aspects else 'None'}")
    print(f"Neutral aspects   : {', '.join(neutral_aspects)  if neutral_aspects  else 'None'}")

# ============================================================
# STEP 4: SAVE RESULTS
# ============================================================
output = {
    "search_term": search_term,
    "overall_rating": overall_rating,
    "aspects": aspect_results
}

with open("aspect_results.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2)

print(f"\nSaved to aspect_results.json")