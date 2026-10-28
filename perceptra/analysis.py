"""Local sentiment and aspect-estimate service, independent of Streamlit."""

import argparse
import json
import logging

from perceptra.ingestion.dataset_loader import list_products, load_manifest, load_review_batch
from perceptra.nlp.cleaner import clean_records
from perceptra.nlp.aspects import ASPECT_EXPLANATION, ASPECT_METHOD, extract_aspects_from_records
from perceptra.nlp.sentiment import engine_metadata, score_records, summarize_sentiment
from perceptra.schemas import AnalysisResult


def analyze_product(product_id, engine="vader", *, directory=None) -> AnalysisResult:
    metadata = engine_metadata(engine)
    manifest = load_manifest(directory)
    batch = load_review_batch(product_id, directory, manifest=manifest)
    cleaned, cleaning = clean_records(batch["reviews"])
    scored = score_records(cleaned, engine)
    summary = summarize_sentiment(scored)
    warnings = list(batch["warnings"])
    product = next(p for p in manifest["products"] if p["product_id"] == product_id)
    try:
        aspect_analysis = extract_aspects_from_records(product["name"], cleaned, scored)
    except LookupError as exc:
        aspect_analysis = {
            "status": "missing_resources", "method": ASPECT_METHOD, "explanation": ASPECT_EXPLANATION,
            "aspects": [], "warnings": [str(exc)], "used_fallback": False,
        }
    except Exception:
        logging.getLogger(__name__).exception("Aspect extraction failed for %s", product_id)
        aspect_analysis = {
            "status": "failed", "method": ASPECT_METHOD, "explanation": ASPECT_EXPLANATION,
            "aspects": [], "warnings": ["Aspect estimates could not be completed. Overall sentiment results remain available."],
            "used_fallback": False,
        }
    warnings.extend(aspect_analysis["warnings"])
    if cleaning["rejected_count"]:
        warnings.append(f"Preprocessing rejected {cleaning['rejected_count']} reviews; see rejection_reasons.")
    if cleaning["duplicate_count"]:
        warnings.append(f"Removed {cleaning['duplicate_count']} duplicate reviews within this product.")
    if not scored:
        warnings.append("No usable reviews remain. Sentiment and perception ratings are unavailable.")
    reasons = dict(cleaning["rejection_reasons"])
    if batch["rejected_count"]:
        reasons["malformed_prepared_record"] = batch["rejected_count"]
    provenance = {key: value for key, value in manifest.items() if key != "products"}
    return {
        **metadata, **summary, "status": "complete" if scored else "no_reviews",
        "product": product,
        "dataset_provenance": provenance, "original_review_count": batch["original_count"],
        "rejected_review_count": batch["rejected_count"] + cleaning["rejected_count"],
        "duplicate_count": cleaning["duplicate_count"], "rejection_reasons": reasons,
        "scored_reviews": scored, "aspect_analysis": aspect_analysis, "warnings": warnings,
        "limitations": [
            "Historical anonymized clothing reviews; product names and brands are not available.",
            "VADER is lexicon-based and can miss sarcasm and contextual sentiment.",
            "Evidence is limited to the prepared subset and retained English reviews.",
            "Perception ratings are NLP-derived, not customer star ratings or calibrated probabilities.",
            ASPECT_EXPLANATION,
            "Aspect extraction uses POS-tagged noun frequency, a dimension list, and a fallback; no TF-IDF is used.",
        ],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--product")
    parser.add_argument("--engine", default="vader")
    parser.add_argument("--data-dir")
    parser.add_argument("--list-products", action="store_true")
    parser.add_argument("--summary", action="store_true", help="Omit individual review text from JSON output")
    args = parser.parse_args(argv)
    if not args.product and not args.list_products:
        parser.error("Specify --product or --list-products.")
    try:
        if args.list_products:
            output = list_products(args.data_dir)
        else:
            output = analyze_product(args.product, args.engine, directory=args.data_dir)
            if args.summary:
                output = {k: v for k, v in output.items() if k != "scored_reviews"}
        print(json.dumps(output, ensure_ascii=True, indent=2, allow_nan=False))
    except (OSError, ValueError, RuntimeError, LookupError) as exc:
        parser.exit(1, f"Analysis failed: {exc}\n")


if __name__ == "__main__":
    main()
