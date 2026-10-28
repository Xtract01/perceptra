"""Compatibility entry point; implementation lives in the perceptra package."""

from perceptra.ingestion.youtube import (
    collect_reviews, fetch_comments, get_youtube_client, is_english, main, search_videos,
)


if __name__ == "__main__":
    main()
