"""Optional YouTube collection, invoked explicitly and never during import."""

import argparse
import json
import os

from perceptra.nlp.cleaner import is_english as _is_english

DEFAULT_QUERY = "Hyundai i10 review"


def is_english(text):
    return _is_english(text, min_words=3)


def get_youtube_client(api_key=None):
    try:
        from dotenv import load_dotenv
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise RuntimeError(
            "YouTube collection is optional. Install it with "
            ".venv\\Scripts\\python.exe -m pip install -e .[collectors]."
        ) from exc
    load_dotenv()
    key = api_key or os.environ.get("YOUTUBE_API_KEY")
    if not key:
        raise ValueError("Set YOUTUBE_API_KEY before explicitly collecting YouTube comments.")
    return build("youtube", "v3", developerKey=key, cache_discovery=False)


def search_videos(query, max_results=5, *, client=None):
    if not isinstance(query, str) or not query.strip():
        raise ValueError("Search query must be nonempty.")
    if not isinstance(max_results, int) or isinstance(max_results, bool) or not 1 <= max_results <= 50:
        raise ValueError("max_results must be an integer between 1 and 50.")
    youtube = client if client is not None else get_youtube_client()
    response = youtube.search().list(q=query, part="snippet", type="video", maxResults=max_results,
                                     relevanceLanguage="en", regionCode="IN").execute()
    videos = []
    for item in response.get("items", []):
        title = item["snippet"]["title"]
        if is_english(title):
            videos.append({"video_id": item["id"]["videoId"], "title": title})
    return videos


def fetch_comments(video_id, max_comments=100, *, client=None):
    if not isinstance(video_id, str) or not video_id.strip():
        raise ValueError("video_id must be nonempty.")
    if not isinstance(max_comments, int) or isinstance(max_comments, bool) or max_comments < 0:
        raise ValueError("max_comments must be a nonnegative integer.")
    if max_comments == 0:
        return []
    youtube = client if client is not None else get_youtube_client()
    threads = youtube.commentThreads()
    request = threads.list(part="snippet", videoId=video_id, maxResults=min(100, max_comments),
                           textFormat="plainText")
    comments = []
    while request is not None and len(comments) < max_comments:
        response = request.execute()
        for item in response.get("items", []):
            snippet = item["snippet"]["topLevelComment"]["snippet"]
            comments.append({"comment": snippet["textDisplay"], "likes": snippet["likeCount"],
                             "video_id": video_id})
            if len(comments) == max_comments:
                break
        request = threads.list_next(request, response) if len(comments) < max_comments else None
    return comments


def collect_reviews(query=DEFAULT_QUERY, max_videos=3, max_comments=50, *, client=None):
    youtube = client if client is not None else get_youtube_client()
    comments = []
    for video in search_videos(query, max_videos, client=youtube):
        for comment in fetch_comments(video["video_id"], max_comments, client=youtube):
            comments.append({**comment, "video_title": video["title"], "search_term": query})
    return comments


def collect_and_save(query=DEFAULT_QUERY, output_file="raw_comments.json", *, max_videos=3,
                     max_comments=50, client=None):
    comments = collect_reviews(query, max_videos, max_comments, client=client)
    with open(output_file, "w", encoding="utf-8") as handle:
        json.dump(comments, handle, ensure_ascii=False, indent=2)
    print(f"Saved {len(comments)} comments to {output_file}")
    return comments


def main(argv=None, *, save=False):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", default=DEFAULT_QUERY)
    parser.add_argument("--max-videos", type=int, default=3)
    parser.add_argument("--max-comments", type=int, default=50)
    parser.add_argument("--output", default="raw_comments.json")
    args = parser.parse_args(argv)
    try:
        if save:
            collect_and_save(args.query, args.output, max_videos=args.max_videos,
                             max_comments=args.max_comments)
        else:
            comments = collect_reviews(args.query, args.max_videos, args.max_comments)
            print(f"Total comments collected: {len(comments)}")
            for comment in comments[:5]:
                print(f"Comment: {comment['comment'][:100]}\nLikes: {comment['likes']}")
    except Exception as exc:
        parser.exit(1, f"YouTube collection failed: {exc}\n")


if __name__ == "__main__":
    main()
