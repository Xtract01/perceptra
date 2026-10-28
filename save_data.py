"""Compatibility entry point; implementation lives in the perceptra package."""

from perceptra.ingestion.youtube import collect_and_save, fetch_comments, main, search_videos


if __name__ == "__main__":
    main(save=True)
