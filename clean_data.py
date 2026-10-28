"""Compatibility entry point; implementation lives in the perceptra package."""

from perceptra.nlp.cleaner import (
    clean_comment, clean_pipeline, clean_records, is_english, is_useful, main, remove_duplicates,
)


if __name__ == "__main__":
    main()
