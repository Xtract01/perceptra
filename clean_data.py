import json
import re
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

DetectorFactory.seed = 0

def is_english(text):
    try:
        if len(text.split()) < 5:
            return False
        return detect(text) == 'en'
    except LangDetectException:
        return False

def clean_comment(text):
    text = re.sub(r'http\S+|www\S+', '', text)
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    text = re.sub(r'[^a-zA-Z0-9\s.,!?]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def is_useful(text):
    if len(text.split()) < 4:
        return False
    question_only = re.match(r'^[^.!]*\?$', text.strip())
    if question_only:
        return False
    return True

def remove_duplicates(comments):
    seen = set()
    unique = []
    for item in comments:
        normalized = item["cleaned_comment"].lower().strip()
        if normalized not in seen:
            seen.add(normalized)
            unique.append(item)
    return unique

def clean_pipeline(input_file="raw_comments.json", output_file="cleaned_comments.json"):
    with open(input_file, "r", encoding="utf-8") as f:
        comments = json.load(f)

    print(f"Total comments before cleaning: {len(comments)}")

    cleaned = []
    for item in comments:
        original = item["comment"]

        if not is_english(original):
            continue

        cleaned_text = clean_comment(original)

        if not is_useful(cleaned_text):
            continue

        cleaned.append({
            "original_comment": original,
            "cleaned_comment": cleaned_text,
            "likes": item["likes"],
            "video_title": item["video_title"],
            "search_term": item["search_term"]
        })

    print(f"Comments after cleaning: {len(cleaned)}")

    # Remove duplicates
    before_dedup = len(cleaned)
    cleaned = remove_duplicates(cleaned)
    print(f"After duplicate removal: {len(cleaned)}")
    print(f"Duplicates removed: {before_dedup - len(cleaned)}")
    print(f"Removed: {len(comments) - len(cleaned)} comments total")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)

    print(f"Saved to {output_file}")
    return cleaned

if __name__ == "__main__":
    clean_pipeline()