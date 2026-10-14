import json
import re
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException
DetectorFactory.seed = 0

def is_english(text):
    try:
        # Too short to reliably detect
        if len(text.split()) < 5:
            return False
        return detect(text) == 'en'
    except LangDetectException:
        return False

def clean_comment(text):
    # Remove URLs
    text = re.sub(r'http\S+|www\S+', '', text)
    # Remove emojis
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    # Remove special characters
    text = re.sub(r'[^a-zA-Z0-9\s.,!?]', '', text)
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def is_useful(text):
    # Filter out comments that are too short
    if len(text.split()) < 4:
        return False
    # Filter out pure questions with no opinion
    question_only = re.match(r'^[^.!]*\?$', text.strip())
    if question_only:
        return False
    return True

# Load raw data
with open("raw_comments.json", "r", encoding="utf-8") as f:
    comments = json.load(f)

print(f"Total comments before cleaning: {len(comments)}")

cleaned = []
for item in comments:
    original = item["comment"]
    
    # Step 1: English filter
    if not is_english(original):
        continue
    
    # Step 2: Clean the text
    cleaned_text = clean_comment(original)
    
    # Step 3: Usefulness filter
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
print(f"Removed: {len(comments) - len(cleaned)} comments")
print(f"\nSample cleaned comments:")
print("="*50)
for c in cleaned[:5]:
    print(f"Original: {c['original_comment'][:80]}")
    print(f"Cleaned:  {c['cleaned_comment'][:80]}")
    print("---")

# Save cleaned data
with open("cleaned_comments.json", "w", encoding="utf-8") as f:
    json.dump(cleaned, f, ensure_ascii=False, indent=2)

print(f"\nSaved {len(cleaned)} cleaned comments to cleaned_comments.json")