import json
from fetch_youtube import search_videos, fetch_comments

search_term = "Hyundai i10 review"
videos = search_videos(search_term, max_results=3)

all_comments = []
for video in videos:
    comments = fetch_comments(video["video_id"], max_comments=50)
    for comment in comments:
        comment["video_title"] = video["title"]
        comment["search_term"] = search_term
    all_comments.extend(comments)

# Save to JSON file
with open("raw_comments.json", "w", encoding="utf-8") as f:
    json.dump(all_comments, f, ensure_ascii=False, indent=2)

print(f"Saved {len(all_comments)} comments to raw_comments.json")