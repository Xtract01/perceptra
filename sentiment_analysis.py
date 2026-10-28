import json
import math
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

def analyze_sentiment(input_file="cleaned_comments.json", output_file="sentiment_results.json"):
    with open(input_file, "r", encoding="utf-8") as f:
        comments = json.load(f)

    analyzer = SentimentIntensityAnalyzer()
    results = []

    for item in comments:
        text = item["cleaned_comment"]
        likes = item["likes"]
        scores = analyzer.polarity_scores(text)
        compound = scores["compound"]

        # Likes weighting — more likes = more weight
        # log scale so 1000 likes doesn't dominate everything
        likes_weight = 1 + math.log1p(likes)
        weighted_score = compound * likes_weight

        if compound >= 0.05:
            sentiment = "positive"
        elif compound <= -0.05:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        results.append({
            "comment": text,
            "likes": likes,
            "video_title": item["video_title"],
            "compound_score": compound,
            "weighted_score": round(weighted_score, 4),
            "likes_weight": round(likes_weight, 3),
            "positive_score": scores["pos"],
            "negative_score": scores["neg"],
            "neutral_score": scores["neu"],
            "sentiment": sentiment
        })

    # Use weighted scores for final rating
    positive = [r for r in results if r["sentiment"] == "positive"]
    negative = [r for r in results if r["sentiment"] == "negative"]
    neutral  = [r for r in results if r["sentiment"] == "neutral"]

    total = len(results)
    
    # Overall score using weighted scores
    total_weight = sum(r["likes_weight"] for r in results)
    weighted_overall = sum(r["weighted_score"] for r in results) / total_weight
    
    # Regular unweighted for comparison
    unweighted_overall = sum(r["compound_score"] for r in results) / total
    
    weighted_rating = round((weighted_overall + 1) * 5, 1)
    unweighted_rating = round((unweighted_overall + 1) * 5, 1)

    print(f"PRODUCT PERCEPTION ANALYSIS")
    print("="*50)
    print(f"Total comments analyzed : {total}")
    print(f"Positive : {len(positive)} ({round(len(positive)/total*100)}%)")
    print(f"Negative : {len(negative)} ({round(len(negative)/total*100)}%)")
    print(f"Neutral  : {len(neutral)}  ({round(len(neutral)/total*100)}%)")
    print(f"\nUnweighted Rating : {unweighted_rating}/10")
    print(f"Likes-Weighted Rating : {weighted_rating}/10")
    print(f"\n(Weighted rating gives more importance to highly liked comments)")

    print(f"\nTop 3 Positive Comments (by weighted score):")
    print("-"*50)
    top_positive = sorted(positive, key=lambda x: x["weighted_score"], reverse=True)[:3]
    for c in top_positive:
        print(f"[score:{c['compound_score']} | likes:{c['likes']} | weight:{c['likes_weight']}]")
        print(f"{c['comment'][:100]}")
        print()

    print(f"\nTop 3 Negative Comments (by weighted score):")
    print("-"*50)
    top_negative = sorted(negative, key=lambda x: x["weighted_score"])[:3]
    for c in top_negative:
        print(f"[score:{c['compound_score']} | likes:{c['likes']} | weight:{c['likes_weight']}]")
        print(f"{c['comment'][:100]}")
        print()

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"Saved to {output_file}")
    return results, weighted_rating, weighted_overall

if __name__ == "__main__":
    analyze_sentiment()