# Perceptra

Perceptra provides a local Streamlit dashboard and an offline analysis service using
genuine CC0 clothing reviews, VADER sentiment, and POS/frequency aspect estimates.
This is a demonstration prototype, not a production-ready analytics system.

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
or shell activation is required. The analysis service does not import Streamlit or
start a server; the dashboard is a separate entry point.

## Launch and use the dashboard

If you prefer an activated shell, run `.\.venv\Scripts\Activate.ps1`. Activation
is optional; the explicit interpreter commands below also work without changing
PowerShell's execution policy.

```powershell
.\.venv\Scripts\python.exe scripts/prepare_demo_data.py --prepare-nltk
.\.venv\Scripts\python.exe -m streamlit run app/streamlit_app.py --server.address 127.0.0.1 --server.port 8501
```

Resource preparation is a one-time online setup step. It can be omitted when the
resources already exist in `.venv/nltk_data/`. Open `http://127.0.0.1:8501`, select
Clothing 1078 or Clothing 862, and click **Analyze product**. The application shows
five overview metrics, a sentiment chart with exact counts, positive/negative review
examples, aspect estimates with supporting evidence, and a customer review explorer.

Use the tabs to navigate. The review explorer supports text search, sentiment
filtering, and 25 reviews per page. Aspect evidence initially shows up to ten
supporting reviews. Changing products clears the previous results and filters;
click Analyze again to calculate results for the new selection.

Missing datasets produce setup guidance. Missing NLTK resources preserve the VADER
results and explain how to restore aspect estimates. Processing failures clear old
results and show a user-facing message. Empty results never receive a fabricated
rating. No credentials, paid APIs, hosted models, or cloud infrastructure are needed.

Stop the server with **Ctrl+C** when finished. See [demo instructions](docs/demo.md)
and [Day 2 verification](docs/day2-verification.md) for the tested workflow and cleanup.

## Analyze the bundled real reviews

```powershell
.\.venv\Scripts\python.exe -m perceptra.analysis --list-products
.\.venv\Scripts\python.exe -m perceptra.analysis --product "clothing:1078" --summary
.\.venv\Scripts\python.exe -m perceptra.analysis --product "clothing:862" --summary
```

Omit `--summary` to include all individual scored reviews in the JSON result.
The service returns original, rejected, duplicate, and analyzed counts; sentiment
counts and percentages; full-precision scores; product/source metadata; warnings;
and original review evidence. `aspect_analysis` adds full-precision feature estimates,
supporting review IDs/counts, evidence-volume tiers, method metadata, and warnings.
It does not write results or call a remote service.

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

Aspect extraction needs NLTK data. Prepare its small resources
explicitly, using the project virtual environment:

```powershell
.\.venv\Scripts\python.exe scripts/prepare_demo_data.py --prepare-nltk
```

The script stores `punkt_tab`, `averaged_perceptron_tagger_eng`, and `stopwords`
exclusively in `.venv/nltk_data/`. Application resource checks restrict NLTK's search
path to that location, ignoring system/user caches. Imports and inference never
download data. No transformer model weights are required.

After dependencies and these resources are prepared, analysis and the dashboard
run offline. Tests block external network access and NLTK downloads during inference;
AppTest permits Windows' internal loopback coordination.

## Package layout

```text
perceptra/
  config.py                   Local paths and explicit NLTK resource checks
  schemas.py                  Shared result and review contracts
  analysis.py                 Data -> cleaning -> VADER -> aspects -> structured results + CLI
  ingestion/dataset_loader.py Deterministic preparation and offline loading
  ingestion/youtube.py        Optional, explicitly invoked collection
  nlp/cleaner.py               Conservative cleaning and validation
  nlp/sentiment.py             VADER facade and weighted aggregation
  nlp/aspects.py               POS/frequency estimates and stable review-ID evidence joins
app/streamlit_app.py          Native Streamlit dashboard, no duplicated scoring
.streamlit/config.toml        Restrained native theme and disabled usage telemetry
scripts/prepare_demo_data.py  Dataset/resource preparation
data/processed/               Bundled real CC0 sample and provenance
tests/                       Processing, integration, compatibility, and isolated AppTest checks
docs/demo.md                 Demo instructions and Day 1 baseline
docs/day2-verification.md    Day 2 results, browser checks, and cleanup
```

No database, Airflow, or remote-model placeholder directories are created.
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
Day 2 adds aspect ID matching, exact-token boundaries, supporting counts/rating
formulas, resource failures, and AppTest scenarios for startup, analysis, matching
metrics, product switching, review pagination/search, empty states, and failures.
AppTest runs in isolated `.venv` subprocesses so UI imports cannot contaminate the
headless-service isolation checks. It complements actual-browser verification.
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

Aspect extraction remains partly whitelist-based and assigns whole-review sentiment
to mentioned terms; it is not contextual ABSA. It preserves noun-frequency ranking
and the fallback, uses complete-token matching and stable review-ID joins, and excludes
missing/invalid predictions rather than treating them as neutral. No TF-IDF, transformer,
lemmatization, or phrase extraction is added. Volume tiers are Low below 7 supporting
reviews, Medium at 7–14, and High at 15+. They are not accuracy probabilities. The
overall product rating still comes exclusively from review-level VADER aggregation.

Work remains on the fork's existing `main`; staging, commits, and pushes are manual.
