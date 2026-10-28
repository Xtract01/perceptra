# Perceptra

Day 1 provides a local, offline product-review sentiment pipeline using genuine CC0
clothing reviews and VADER. The Streamlit dashboard and aspect integration are Day 2
work; they are not implemented in the analysis service yet.

## Setup on Windows

Tested with Python 3.13.6. Python 3.11+ is required. Create the virtual environment
once, then use its interpreter for every installation, script, and test:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pip check
```

The runtime install is sufficient for analysis; the second install adds pytest.
`pyproject.toml` is the only dependency specification. The requirements files
delegate to the editable project and its `dev` extra. No global package installation
or shell activation is required. Streamlit is installed for the approved MVP, but
Day 1 processing neither imports it nor starts a server.

## Analyze the bundled real reviews

```powershell
.\.venv\Scripts\python.exe -m perceptra.analysis --list-products
.\.venv\Scripts\python.exe -m perceptra.analysis --product "clothing:1078" --summary
.\.venv\Scripts\python.exe -m perceptra.analysis --product "clothing:862" --summary
```

Omit `--summary` to include all individual scored reviews in the JSON result.
The service returns original, rejected, duplicate, and analyzed counts; sentiment
counts and percentages; full-precision scores; product/source metadata; warnings;
and original review evidence. It does not write results or call a remote service.

```python
from perceptra.analysis import analyze_product
from perceptra.ingestion.dataset_loader import list_products, load_reviews
from perceptra.nlp.sentiment import analyze_text

result = analyze_product("clothing:1078")
prediction = analyze_text("I love this dress!", engine="vader")
```

VADER compound is a signed sentiment measure, not a probability. The prediction
includes engine/model/version, `score_kind="vader_compound"`, raw scores, and
`class_probabilities=None`. Unsupported engines fail explicitly; there is no silent
switching or Hugging Face implementation.

## Dataset and reproducibility

Source: [Women's E-Commerce Clothing Reviews, version 1](https://www.kaggle.com/datasets/nicapotato/womens-ecommerce-clothing-reviews).
The [publisher's metadata](https://www.kaggle.com/nicapotato/womens-ecommerce-clothing-reviews/metadata)
declares [CC0-1.0](https://creativecommons.org/publicdomain/zero/1.0/). The original
retailer is anonymous; these are historical, anonymized reviews, not current market
feedback. Clothing IDs are retained; names and brands are not fabricated.

The bundled subset contains the first 200 nonempty source reviews for each of the
two products with the greatest valid review counts. Ties use numeric Clothing ID.
Selection uses no sentiment predictions or customer rating labels. Original source
row IDs and exact review text are retained. Ratings, recommendation flags, positive
feedback counts, ages, and titles are excluded from NLP inputs. Likes are zero.

`data/processed/manifest.json` records source URL/version/license, acquisition URL,
selection policy, source row counts, selected products, and SHA-256 checksums.
The loader verifies the prepared CSV checksum and product isolation before analysis.

To reproduce from the publisher's original CSV:

```powershell
.\.venv\Scripts\python.exe scripts/prepare_demo_data.py --input-csv "data/raw/Womens Clothing E-Commerce Reviews.csv"
```

The script accepts a local CSV and never downloads or fabricates dataset records.
If the input is outside `data/raw/`, it also copies the source there. The full source
CSV is Git-ignored; the small CC0 subset and manifest are intended project files.
Changing source data regenerates the manifest/checksums explicitly. The included
subset is sufficient to run analysis without the original CSV.

## NLTK resources

Only legacy aspect extraction currently needs NLTK data. Prepare its small resources
explicitly, using the project virtual environment:

```powershell
.\.venv\Scripts\python.exe scripts/prepare_demo_data.py --prepare-nltk
```

The script stores `punkt_tab`, `averaged_perceptron_tagger_eng`, and `stopwords`
exclusively in `.venv/nltk_data/`. Application resource checks restrict NLTK's search
path to that location, ignoring system/user caches. Imports and inference never
download data. No transformer model weights are required.

After dependencies and these resources are prepared, the Day 1 application and
tests run offline. Tests also block network access and NLTK downloads during inference.

## Package layout

```text
perceptra/
  config.py                   Local paths and explicit NLTK resource checks
  schemas.py                  Shared result and review contracts
  analysis.py                 Data -> cleaning -> VADER -> aggregation + CLI
  ingestion/dataset_loader.py Deterministic preparation and offline loading
  ingestion/youtube.py        Optional, explicitly invoked collection
  nlp/cleaner.py               Conservative cleaning and validation
  nlp/sentiment.py             VADER facade and weighted aggregation
  nlp/aspects.py               Existing aspect algorithm, migrated for compatibility
scripts/prepare_demo_data.py  Dataset/resource preparation
data/processed/               Bundled real CC0 sample and provenance
tests/                       Day 1 component/integration checks
docs/demo.md                 Day 1 verification and limitations
```

No empty UI, database, Airflow, or model-engine placeholder directories are created.
Default paths resolve from the editable project location, not the current working
directory. Set the process environment variable `PERCEPTRA_DATA_DIR`, or pass CLI
`--data-dir`, to select an alternate data root containing `processed/`.

## Compatibility scripts and optional collection

The five original root scripts re-export the package functions and retain CLI
defaults. Algorithms exist only inside the package:

```powershell
.\.venv\Scripts\python.exe clean_data.py --input raw_comments.json --output cleaned_comments.json
.\.venv\Scripts\python.exe sentiment_analysis.py --input cleaned_comments.json --output sentiment_results.json
.\.venv\Scripts\python.exe dynamic_aspects.py --query "Hyundai i10 review"
```

`analyze_sentiment()` still returns `(results, weighted_rating, weighted_overall)`.
Empty input now returns `([], None, None)` rather than crashing. Existing JSON keys
remain available, with additive provenance fields.

YouTube collection is optional and has not been live-tested. To use it separately:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[collectors]"
# Configure YOUTUBE_API_KEY in your environment or a local, ignored .env file.
.\.venv\Scripts\python.exe fetch_youtube.py --query "Hyundai i10 review"
.\.venv\Scripts\python.exe save_data.py --query "Hyundai i10 review" --output raw_comments.json
```

Only explicit collection loads the optional dependencies and creates a client.
The offline analysis path needs no YouTube key. Do not activate paid services.

## Tests and scoring

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp=.venv/test-tmp
```

Tests cover import safety, deterministic preparation, checksums, provenance and label
exclusion, conservative preprocessing, product-scoped duplicates, real VADER scoring,
threshold boundaries, legacy wrappers, empty results, and both real prepared products.
Authored fixtures are synthetic test inputs and are not demonstration data.

Sentiment thresholds are positive at compound >= 0.05, negative at <= -0.05, otherwise
neutral. The existing perception formula is retained without intermediate rounding:

```text
weight = 1 + log(1 + likes)
overall_score = sum(compound * weight) / sum(weight)
perception_rating = 5 * (overall_score + 1)
```

With zero likes this is the mean compound score mapped to 0-10. It is not an average
customer star rating. Empty results have unavailable (`null`) scores/ratings. Short
reviews, non-English text, and question-only entries retain the existing filtering
policy, with rejection counts reported. VADER may miss sarcasm and context.

The legacy aspect implementation remains partly whitelist-based and assigns whole-
review sentiment to mentioned terms; it is not contextual ABSA. Its old text joins
and rating behavior will be addressed when integrating it on Day 2. There is no
Streamlit dashboard or aspect output in the Day 1 analysis service.

Work remains on the fork's existing `main`; staging, commits, and pushes are manual.
