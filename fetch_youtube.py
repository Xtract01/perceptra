from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

DetectorFactory.seed = 0

def is_english(text):
    try:
        if len(text.split()) < 3:
            return False
        return detect(text) == 'en'
    except LangDetectException:
        return False
from googleapiclient.discovery import build
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("YOUTUBE_API_KEY")
youtube = build("youtube", "v3", developerKey=api_key)

def search_videos(query, max_results=5):
    request = youtube.search().list(
        q=query,
        part="snippet",
        type="video",
        maxResults=max_results,
        relevanceLanguage="en",  # Only English videos
        regionCode="IN"           # Indian market context
    )
    response = request.execute()
    
    videos = []
    for item in response["items"]:
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"]
        # Skip videos with non-English titles
        if not is_english(title):
            print(f"Skipping non-English video: {title}")
            continue
        videos.append({"video_id": video_id, "title": title})
        print(f"Found: {title}")
    
    return videos

def fetch_comments(video_id, max_comments=100):
    comments = []
    
    request = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id,
        maxResults=100,
        textFormat="plainText"
    )
    
    while request and len(comments) < max_comments:
        response = request.execute()
        
        for item in response["items"]:
            comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
            likes = item["snippet"]["topLevelComment"]["snippet"]["likeCount"]
            comments.append({
                "comment": comment,
                "likes": likes,
                "video_id": video_id
            })
        
        request = youtube.commentThreads().list_next(request, response)
    
    return comments

# --- Run it ---
search_term = "Hyundai i10 review"

print(f"\nSearching YouTube for: {search_term}")
print("="*50)

videos = search_videos(search_term, max_results=3)

all_comments = []
for video in videos:
    print(f"\nFetching comments from: {video['title']}")
    comments = fetch_comments(video["video_id"], max_comments=50)
    all_comments.extend(comments)
    print(f"Got {len(comments)} comments")

print(f"\nTotal comments collected: {len(all_comments)}")
print("\nSample comments:")
print("="*50)
for c in all_comments[:5]:
    print(f"Comment: {c['comment'][:100]}")
    print(f"Likes: {c['likes']}")
    print("---")