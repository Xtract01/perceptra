"""Deterministic preparation and offline loading of CC0 clothing reviews."""

from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path

from perceptra.config import data_dir
from perceptra.schemas import DatasetError, Product, ReviewBatch, ReviewRecord

SOURCE_URL = "https://www.kaggle.com/datasets/nicapotato/womens-ecommerce-clothing-reviews"
LICENSE_URL = SOURCE_URL + "/metadata"
ACQUISITION_URL = (
    "https://www.kaggle.com/api/v1/datasets/download/"
    "nicapotato/womens-ecommerce-clothing-reviews?datasetVersionNumber=1"
)
DATASET_ID = "nicapotato/womens-ecommerce-clothing-reviews"
DATASET_VERSION = "1"
PREPARED_FIELDS = ["review_id", "product_id", "source_row", "original_text", "category",
                   "department", "division", "likes"]


def sha256_file(path):
    with open(path, "rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def prepare_dataset(input_csv, output_dir=None, *, max_reviews=200, product_count=2,
                    acquisition_url=ACQUISITION_URL):
    """Prepare real supplied data; no network access and no labels used in selection."""
    if not 1 <= max_reviews <= 200 or product_count not in (1, 2):
        raise DatasetError("Choose one or two products and 1 to 200 reviews per product.")
    source_path = Path(input_csv)
    try:
        source_hash = sha256_file(source_path)
        with source_path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if not {"Clothing ID", "Review Text", "Class Name"}.issubset(reader.fieldnames or []):
                raise DatasetError("Source CSV requires Clothing ID, Review Text, and Class Name columns.")
            groups = defaultdict(list)
            seen_rows = set()
            invalid = 0
            total = 0
            for index, row in enumerate(reader):
                total += 1
                text = row.get("Review Text")
                try:
                    clothing_id = int(row.get("Clothing ID", ""))
                    if clothing_id < 0 or not isinstance(text, str) or not text.strip():
                        raise ValueError
                except (ValueError, TypeError):
                    invalid += 1
                    continue
                source_row = row.get("", row.get("Unnamed: 0", str(index)))
                if not isinstance(source_row, str) or not source_row.strip() or source_row in seen_rows:
                    raise DatasetError(f"Invalid or duplicate source row identifier at CSV record {index}.")
                seen_rows.add(source_row)
                groups[clothing_id].append({
                    "review_id": f"wcec-v1:row:{source_row}", "product_id": f"clothing:{clothing_id}",
                    "source_row": source_row, "original_text": text,
                    "category": (row.get("Class Name") or "").strip() or "Unspecified",
                    "department": (row.get("Department Name") or "").strip(),
                    "division": (row.get("Division Name") or "").strip(), "likes": 0,
                })
    except (OSError, UnicodeError, csv.Error) as exc:
        raise DatasetError(f"Cannot read publisher CSV {source_path}: {exc}") from exc
    if not groups:
        raise DatasetError("Source CSV contains no valid product reviews. No fabricated data was generated.")
    selected = sorted(groups, key=lambda identity: (-len(groups[identity]), identity))[:product_count]
    products = []
    prepared = []
    for clothing_id in selected:
        rows = groups[clothing_id]
        category = Counter(row["category"] for row in rows).most_common(1)[0][0]
        first = rows[0]
        products.append({
            "product_id": first["product_id"], "clothing_id": clothing_id,
            "name": f"Clothing item {clothing_id} - {category}", "category": category,
            "department": first["department"], "division": first["division"],
            "review_count": min(max_reviews, len(rows)), "available_source_reviews": len(rows),
        })
        prepared.extend(rows[:max_reviews])
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=PREPARED_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(prepared)
    content = buffer.getvalue().encode("utf-8")
    manifest = {
        "schema_version": 1, "dataset_id": DATASET_ID,
        "dataset_name": "Women's E-Commerce Clothing Reviews", "dataset_version": DATASET_VERSION,
        "license": "CC0-1.0", "license_metadata_url": LICENSE_URL,
        "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
        "source_url": SOURCE_URL, "acquisition_url": acquisition_url,
        "source_filename": source_path.name, "source_sha256": source_hash,
        "source_row_count": total, "valid_source_review_count": total - invalid,
        "rejected_source_row_count": invalid, "processed_filename": "demo_reviews.csv",
        "processed_sha256": hashlib.sha256(content).hexdigest(),
        "selection": {"rank": "valid_review_count_desc_then_clothing_id_asc",
                      "within_product": "original_source_row_order", "max_reviews_per_product": max_reviews},
        "excluded_input_fields": ["Rating", "Recommended IND", "Positive Feedback Count", "Age", "Title"],
        "likes_policy": "Zero: source feedback counts are not YouTube likes.",
        "products": products,
    }
    target = Path(output_dir) if output_dir is not None else data_dir() / "processed"
    target.mkdir(parents=True, exist_ok=True)
    (target / "demo_reviews.csv").write_bytes(content)
    (target / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def load_manifest(directory=None):
    target = data_dir(directory) / "processed"
    try:
        manifest = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
        if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
            raise DatasetError("Unsupported dataset manifest schema.")
        if manifest.get("dataset_id") != DATASET_ID or manifest.get("license") != "CC0-1.0":
            raise DatasetError("Dataset identity or CC0 license metadata is invalid.")
        if (manifest.get("dataset_version") != DATASET_VERSION
                or manifest.get("source_url") != SOURCE_URL
                or manifest.get("license_metadata_url") != LICENSE_URL):
            raise DatasetError("Dataset version or publisher provenance is invalid.")
        if manifest.get("processed_filename") != "demo_reviews.csv":
            raise DatasetError("Unexpected processed dataset filename.")
        for key in ("source_sha256", "processed_sha256"):
            digest = manifest.get(key)
            if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
                raise DatasetError(f"Invalid {key} in dataset manifest.")
        if sha256_file(target / "demo_reviews.csv") != manifest["processed_sha256"]:
            raise DatasetError("Prepared dataset checksum mismatch. Re-run preparation from the source CSV.")
        products = manifest.get("products")
        if not isinstance(products, list) or not products:
            raise DatasetError("Manifest contains no product catalog.")
        identities = set()
        required = set(Product.__required_keys__)
        for product in products:
            if not isinstance(product, dict) or not required.issubset(product):
                raise DatasetError("Invalid product catalog entry.")
            identity = product["product_id"]
            clothing_id = product["clothing_id"]
            if (not isinstance(clothing_id, int) or isinstance(clothing_id, bool) or clothing_id < 0
                    or identity != f"clothing:{clothing_id}" or identity in identities
                    or not isinstance(product["review_count"], int) or isinstance(product["review_count"], bool)
                    or product["review_count"] < 0
                    or not isinstance(product["name"], str)):
                raise DatasetError("Invalid or duplicate product identity/count.")
            identities.add(identity)
        return manifest
    except DatasetError:
        raise
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise DatasetError(
            f"Cannot load prepared dataset at {target}: {exc}. "
            "Run .venv\\Scripts\\python.exe scripts/prepare_demo_data.py --input-csv <publisher.csv>."
        ) from exc


def list_products(directory=None) -> list[Product]:
    return load_manifest(directory)["products"]


def load_review_batch(product_id, directory=None, *, manifest=None) -> ReviewBatch:
    manifest = manifest if manifest is not None else load_manifest(directory)
    catalog = {product["product_id"]: product for product in manifest["products"]}
    if not isinstance(product_id, str) or product_id not in catalog:
        raise DatasetError(f"Unknown product {product_id!r}. Available: {', '.join(catalog)}")
    target = data_dir(directory) / "processed" / "demo_reviews.csv"
    reviews = []
    original_count = rejected_count = 0
    seen = set()
    try:
        with target.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if not set(PREPARED_FIELDS).issubset(reader.fieldnames or []):
                raise DatasetError("Prepared CSV columns are invalid; re-run dataset preparation.")
            for row in reader:
                if row.get("product_id") not in catalog:
                    raise DatasetError("Prepared CSV contains a product absent from its catalog.")
                if row["product_id"] != product_id:
                    continue
                original_count += 1
                review_id = row.get("review_id")
                source_row = row.get("source_row")
                text = row.get("original_text")
                if (not review_id or not source_row or review_id != f"wcec-v1:row:{source_row}"
                        or review_id in seen or not isinstance(text, str) or not text.strip()
                        or row.get("likes") != "0"):
                    rejected_count += 1
                    continue
                seen.add(review_id)
                reviews.append({
                    "review_id": review_id, "product_id": product_id, "source": DATASET_ID,
                    "original_text": text, "likes": 0,
                    "provenance": {"source_row": source_row, "category": row["category"],
                                   "department": row["department"], "division": row["division"],
                                   "dataset_version": manifest["dataset_version"],
                                   "source_url": manifest["source_url"],
                                   "source_sha256": manifest["source_sha256"]},
                })
    except (OSError, UnicodeError, csv.Error) as exc:
        raise DatasetError(f"Cannot read prepared reviews: {exc}") from exc
    if original_count != catalog[product_id]["review_count"]:
        raise DatasetError("Prepared review count differs from the product manifest; re-run preparation.")
    warnings = [f"Rejected {rejected_count} malformed prepared review records."] if rejected_count else []
    return {"reviews": reviews, "original_count": original_count,
            "rejected_count": rejected_count, "warnings": warnings}


def load_reviews(product_id, directory=None) -> list[ReviewRecord]:
    return load_review_batch(product_id, directory)["reviews"]
