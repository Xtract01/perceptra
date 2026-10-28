"""Prepare a supplied publisher CSV and explicitly provision local NLTK resources."""

import argparse
import json
from pathlib import Path
import shutil
import sys

from perceptra.config import NLTK_DATA_DIR, NLTK_RESOURCES, VENV_DIR, check_nltk_resources, configure_nltk, data_dir
from perceptra.ingestion.dataset_loader import ACQUISITION_URL, prepare_dataset


def prepare_nltk():
    if Path(sys.prefix).resolve() != VENV_DIR.resolve():
        raise RuntimeError("Use the project's .venv Python to prepare NLTK resources.")
    import nltk

    configure_nltk()
    NLTK_DATA_DIR.mkdir(parents=True, exist_ok=True)
    for name in NLTK_RESOURCES:
        # The downloader uses nltk.data.path; never fall back to a user directory.
        if not nltk.download(name, download_dir=str(NLTK_DATA_DIR), quiet=True, raise_on_error=True):
            raise RuntimeError(f"Could not prepare NLTK resource {name}.")
    check_nltk_resources()
    print(f"NLTK resources ready in {NLTK_DATA_DIR}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-csv", type=Path, help="Original CSV from the CC0 publisher dataset")
    parser.add_argument("--prepare-nltk", action="store_true", help="Explicit setup-time resource download")
    parser.add_argument("--data-dir", type=Path)
    parser.add_argument("--max-reviews", type=int, default=200)
    parser.add_argument("--products", type=int, default=2, choices=(1, 2))
    parser.add_argument("--acquisition-url", default=ACQUISITION_URL)
    args = parser.parse_args(argv)
    if not args.input_csv and not args.prepare_nltk:
        parser.error("Supply --input-csv, --prepare-nltk, or both.")
    if Path(sys.prefix).resolve() != VENV_DIR.resolve():
        parser.error("Run this script using the project's .venv Python interpreter.")
    try:
        if args.input_csv:
            base = data_dir(args.data_dir)
            # Validate and prepare first; do not overwrite a source with itself.
            manifest = prepare_dataset(args.input_csv, base / "processed", max_reviews=args.max_reviews,
                                       product_count=args.products, acquisition_url=args.acquisition_url)
            raw_target = base / "raw" / args.input_csv.name
            if args.input_csv.resolve() != raw_target.resolve():
                raw_target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(args.input_csv, raw_target)
            print(json.dumps({"products": manifest["products"], "source_sha256": manifest["source_sha256"],
                              "processed_sha256": manifest["processed_sha256"]}, indent=2))
        if args.prepare_nltk:
            prepare_nltk()
    except (OSError, ValueError, RuntimeError, LookupError) as exc:
        parser.exit(1, f"Preparation failed: {exc}\n")


if __name__ == "__main__":
    main()
