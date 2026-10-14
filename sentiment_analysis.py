import json
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Load cleaned data
with open("cleaned_comments.json", "r", encoding="utf-8") as f:
    comments = json.load(f)

# Initialize VADER
analyzer = SentimentIntensityAnalyzer()

results = []
for item in comments:
    text = item["cleaned_comment"]
    scores = analyzer.polarity_scores(text)
    
    # Classify sentiment
    compound = scores["compound"]
    if compound >= 0.05:
        sentiment = "positive"
    elif compound <= -0.05:
        sentiment = "negative"
    else:
        sentiment = "neutral"
    
    results.append({
        "comment": text,
        "likes": item["likes"],
        "video_title": item["video_title"],
        "compound_score": compound,
        "positive_score": scores["pos"],
        "negative_score": scores["neg"],
        "neutral_score": scores["neu"],
        "sentiment": sentiment
    })

# Summary stats
positive = [r for r in results if r["sentiment"] == "positive"]
negative = [r for r in results if r["sentiment"] == "negative"]
neutral = [r for r in results if r["sentiment"] == "neutral"]

total = len(results)
overall_score = sum(r["compound_score"] for r in results) / total
rating = round((overall_score + 1) * 5, 1)

print(f"PRODUCT PERCEPTION ANALYSIS: Hyundai i10")
print("="*50)
print(f"Total comments analyzed: {total}")
print(f"Positive: {len(positive)} ({round(len(positive)/total*100)}%)")
print(f"Negative: {len(negative)} ({round(len(negative)/total*100)}%)")
print(f"Neutral:  {len(neutral)} ({round(len(neutral)/total*100)}%)")
print(f"\nOverall Sentiment Score: {round(overall_score, 3)}")
print(f"Product Rating: {rating}/10")
print(f"\nTop 3 Positive Comments:")
print("-"*50)
top_positive = sorted(positive, key=lambda x: x["compound_score"], reverse=True)[:3]
for c in top_positive:
    print(f"[{c['compound_score']}] {c['comment'][:100]}")

print(f"\nTop 3 Negative Comments:")
print("-"*50)
top_negative = sorted(negative, key=lambda x: x["compound_score"])[:3]
for c in top_negative:
    print(f"[{c['compound_score']}] {c['comment'][:100]}")

# Save results
with open("sentiment_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print(f"\nSaved results to sentiment_results.json")