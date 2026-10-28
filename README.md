# Perceptra - Product Perception Intelligence

## 1. Project introduction

Perceptra helps small businesses and product teams understand customer feedback at
both product and feature level. Its goal is to turn scattered reviews into useful
sentiment summaries, supporting evidence, and product-improvement insights.

The current MVP is a **local, dataset-backed Streamlit application**. It analyzes
real, historical clothing reviews with VADER and estimates feature sentiment from
reviews mentioning each feature. It is a working demonstration prototype, not a
production system or a validated measure of current market perception.

The original project vision also includes multi-source collection, contextual
aspect-based sentiment, competitive benchmarking, PostgreSQL, and Airflow. Those
capabilities are future work; they are not required to run this MVP.

## 2. Working features

- Select either of two real anonymized clothing products from the bundled dataset.
- Validate data, filter language/unusable text, preserve sentiment cues, and remove
  duplicate text within a product.
- Classify reviews as positive, negative, or neutral with actual local VADER inference.
- Calculate overall perception ratings and retain individual predictions/evidence.
- Extract POS-tagged frequent nouns and estimate their sentiment with stable review-ID joins.
- Inspect sentiment charts/counts, aspect estimates, and supporting customer reviews.
- Search original review text, filter by sentiment, and browse 25 reviews per page.
- Clear outdated results when changing products and handle empty/error states.
- Run a structured analysis CLI independently of Streamlit.
- Operate offline after dependency and NLTK setup, without credentials or paid APIs.

Live ecommerce ingestion, hosted Hugging Face inference, contextual ABSA, TF-IDF,
product comparison, persistence, orchestration, and production deployment are not
implemented. The separate legacy YouTube collector is optional and not live-verified.

## 3. Technology stack

| Technology | Current responsibility |
|---|---|
| Python | Processing, contracts, preparation, CLI, and application logic |
| Streamlit | Native dashboard, tables, metrics, tabs, and Vega-Lite chart rendering |
| `vaderSentiment` | Local lexicon/rule-based sentiment scoring; lexicon bundled with package |
| `langdetect` | Statistical language filtering using packaged profiles |
| NLTK | Tokenization, English POS tagging, and stopwords for aspect extraction |
| Python CSV/JSON/hash libraries | Dataset preparation, loading, provenance, and integrity checks |
| pytest / Streamlit AppTest | Component, integration, compatibility, and simulated UI tests |

`pyproject.toml` is the **single source of dependency declarations**.
`requirements.txt` installs the editable runtime project; `requirements-dev.txt`
adds its `dev` extra. Streamlit's transitive dependencies include Pandas/NumPy.

The optional `collectors` extra declares `google-api-python-client` and
`python-dotenv`. Normal installation excludes them. Transformers, PyTorch,
PostgreSQL drivers, Airflow, and hosted-inference clients are not MVP dependencies.

## 4. Project structure

```text
perceptra/
+-- .env.example                    Optional configuration examples; no secrets
+-- .gitignore
+-- .streamlit/config.toml           Native theme; usage telemetry disabled
+-- README.md
+-- pyproject.toml                   Package/dependencies/extras/pytest settings
+-- requirements.txt
+-- requirements-dev.txt
+-- perceptra/
|   +-- __init__.py
|   +-- config.py                    Project paths and local NLTK resource checks
|   +-- schemas.py                   Shared review, prediction, and result contracts
|   +-- analysis.py                  Unified service and supported product-analysis CLI
|   +-- ingestion/
|   |   +-- __init__.py
|   |   +-- dataset_loader.py        Deterministic preparation and offline loading
|   |   +-- youtube.py               Optional explicitly invoked collection
|   +-- nlp/
|       +-- __init__.py
|       +-- cleaner.py               Conservative normalization, filtering, deduplication
|       +-- sentiment.py             VADER facade and review-level aggregation
|       +-- aspects.py               POS/frequency estimates and review-ID evidence joins
+-- app/streamlit_app.py             UI; delegates analysis to the service
+-- scripts/prepare_demo_data.py     Local CSV import and explicit NLTK preparation
+-- data/
|   +-- processed/
|   |   +-- demo_reviews.csv         Included CC0 demonstration subset
|   |   +-- manifest.json            Included provenance and checksums
|   +-- raw/                        Optional original CSV; ignored, not needed to run
+-- tests/
|   +-- conftest.py                  Authored fixtures and offline guards
|   +-- test_imports.py
|   +-- test_data.py
|   +-- test_preprocessing.py
|   +-- test_sentiment.py
|   +-- test_aspects.py
|   +-- test_pipeline.py
|   +-- test_dashboard.py
|   +-- test_youtube.py
+-- docs/
|   +-- demo.md                     Focused mentor demonstration runbook
|   +-- day2-verification.md         Historical Day 2 verification
|   +-- day3-verification.md         Final setup/testing/handoff evidence
+-- fetch_youtube.py                Compatibility wrappers delegating to the package
+-- save_data.py
+-- clean_data.py
+-- sentiment_analysis.py
+-- dynamic_aspects.py
```

`.venv/`, Python/build/test caches, editable-install metadata, and `data/raw/` are
local generated artifacts. No database, cloud configuration, or model directory
is needed. The five root scripts contain adapters, not duplicated NLP algorithms.

## 5. Architecture and data flow

```mermaid
flowchart TD
    UI[Streamlit product selection] --> Service[analyze_product]
    Data[Bundled CSV and provenance manifest] --> Loader[Dataset loader and validation]
    Service --> Loader
    Loader --> Cleaner[Preprocessing and product-scoped deduplication]
    Cleaner --> VADER[Local VADER predictions]
    VADER --> Summary[Review counts and weighted perception score]
    Cleaner --> Aspects[POS and noun-frequency aspect extraction]
    VADER --> Aspects
    Summary --> Result[Structured AnalysisResult]
    Aspects --> Result
    Result --> Dashboard[Metrics, charts, aspects, and review evidence]
```

The service loads one product, cleans its records, scores them, computes the overall
summary, and attaches aspect estimates. Aspect ratings do not replace the overall
review-based rating. Data loading, processing, and visualization remain separate.
There is no REST API, database, scheduled DAG, or live request in this workflow.

## 6. Prerequisites

- Python **3.11+** as declared by packaging. The complete clean-environment check
  was performed on **Python 3.13.6 on Windows**; other versions/platforms were not
  independently verified. Python 3.13 is the documented verification reference.
- Git to obtain the repository and Windows PowerShell or CMD to run commands.
- A current desktop browser. Real-browser checks used installed Microsoft Edge.
- Internet access during initial package/NLTK installation. Normal analysis uses
  local files and needs no internet, account, token, database, or GPU.
- Local disk space for the virtual environment, downloaded resources, and installation
  caches. Observed clean installation sizes were about 350 MiB for `Lib`, 2 MiB for
  `Scripts`, and 22 MiB for NLTK data, excluding pip/build caches and base Python.
  These are observations, not a fixed storage minimum.
- A CPU-based developer computer. RAM/CPU minimums and performance guarantees have
  not been benchmarked; no GPU-specific hardware is required by the implemented code.

VS Code is optional. Select `.venv\Scripts\python.exe` with **Python: Select
Interpreter** so editor actions use the same interpreter as the commands below.

## 7. Complete installation guide

Run these commands from the repository root. Do not install packages globally.

### Clone

```powershell
git clone https://github.com/Xtract01/perceptra.git
cd perceptra
```

The maintainer must publish any local changes before they appear in a new clone.
Day 3 verification used a tracked-file source snapshot and a fresh environment;
it did not create another Git checkout or change the remote repository.

### Create the project virtual environment

```powershell
python -m venv .venv
```

This is the one bootstrap command run before `.venv` exists. It creates an isolated
interpreter; it does not install project packages into system Python. If `python`
is unavailable but the Windows launcher is installed, a version-selecting bootstrap
command for this project's reference version is:

```powershell
py -3.13 -m venv .venv
```

For an existing working checkout, keep its `.venv`; do not recreate it unnecessarily.

### Optional activation

PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

CMD:

```cmd
.venv\Scripts\activate.bat
```

Activation only adjusts the current shell. It is not proof of interpreter identity.
The explicit interpreter paths below work even when activation is blocked:

```powershell
.\.venv\Scripts\python.exe -c "import sys; print(sys.executable); print(sys.prefix); print(sys.base_prefix)"
```

The executable/prefix must point into this clone's `.venv`; the base prefix should
be the underlying Python installation.

### Install dependencies

For runtime use:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

For development/testing, also run:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

The second command includes runtime requirements and adds pytest. It is safe after
the first install; dependencies are not declared twice. Do not run `pip freeze >
requirements.txt`: that would overwrite the project's installation entry point.

### Prepare NLTK resources once

```powershell
.\.venv\Scripts\python.exe scripts/prepare_demo_data.py --prepare-nltk
```

This explicit setup command downloads `punkt_tab`, `averaged_perceptron_tagger_eng`,
and `stopwords` **only into `.venv/nltk_data/`**. No transformer weights are involved.
The application restricts NLTK's resource search to that directory, ignoring a
user's global cache and `NLTK_DATA` locations. Imports/inference never download data.

NLTK setup is necessary for aspect estimates. Without it, VADER still runs and the
application reports unavailable aspects instead of inventing results.

### Verify required setup

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -c "import perceptra; print(perceptra.__file__)"
.\.venv\Scripts\python.exe -m perceptra.analysis --list-products
.\.venv\Scripts\python.exe -m perceptra.analysis --product "clothing:1078" --summary
.\.venv\Scripts\python.exe -m perceptra.analysis --product "clothing:862" --summary
```

Expected: consistent dependencies, package import from this clone, two catalog
entries, and completed analyses with nonempty `aspect_analysis.aspects` after
NLTK setup. `--summary` omits individual scored reviews; it does not change analysis.

**Dataset regeneration is not required.** The included processed CSV and manifest
are sufficient. No `.env` file or secret credential is required for the dashboard.

## 8. Running the Streamlit dashboard

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app/streamlit_app.py
```

The normal local address is `http://localhost:8501`. Open the address printed by
Streamlit. For an explicit loopback address and fixed presentation port:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app/streamlit_app.py --server.address 127.0.0.1 --server.port 8501
```

Select a product and click **Analyze product**. The overview shows analyzed count,
overall perception, and three sentiment percentages. Tabs expose the distribution,
feature estimates and their evidence, and the review explorer. Review search is
case-insensitive; pages contain at most 25 reviews. Aspect evidence previews at
most ten supporting reviews. Changing products clears previous results and filters.

Stop Streamlit with **Ctrl+C** in its launching terminal and wait for it to exit.
Closing the browser alone does not stop the server. Restart with the same command.
See the port-conflict recovery steps below if the chosen port is occupied.

## 9. Running individual tasks and configuration

| Task | Supported entry point |
|---|---|
| Catalog/manifest/checksum validation | `python -m perceptra.analysis --list-products` |
| Complete product analysis | `python -m perceptra.analysis --product "clothing:1078" --summary` |
| Dataset regeneration | `scripts/prepare_demo_data.py --input-csv ...` (optional; next section) |
| NLTK setup | `scripts/prepare_demo_data.py --prepare-nltk` |
| Preprocessing existing raw JSON | `clean_data.py --input raw_comments.json --output cleaned_comments.json` |
| VADER analysis of existing cleaned JSON | `sentiment_analysis.py --input cleaned_comments.json --output sentiment_results.json` |
| Aspect estimates from existing JSON outputs | `dynamic_aspects.py --query "Product name" --input cleaned_comments.json --sentiment sentiment_results.json --output aspect_results.json` |

In the table, **always invoke `python` as `.\.venv\Scripts\python.exe`**. The three
legacy file commands require their named input JSON files; they are not additional
steps required by the dataset-backed dashboard. Their functions retain practical
legacy outputs and share the package implementations. They were checked with real
bundled reviews in disposable JSON files.

There is no separate CLI for `load_reviews()` or `analyze_text()`. Use their Python
interfaces, or the unified service:

```python
from perceptra.analysis import analyze_product
from perceptra.ingestion.dataset_loader import list_products, load_reviews
from perceptra.nlp.sentiment import analyze_text

products = list_products()
reviews = load_reviews("clothing:1078")
prediction = analyze_text("I love this dress!", engine="vader")
result = analyze_product("clothing:1078", engine="vader")
```

`perceptra/config.py` resolves default paths from the editable project location,
not the current working directory. The optional process environment variable
`PERCEPTRA_DATA_DIR` changes the data root; it must contain `processed/` with both
files. The analysis CLI also accepts `--data-dir`. NLTK remains in this clone's
`.venv/nltk_data/`. Core configuration does **not** automatically load `.env`.

The optional YouTube code lives in `perceptra/ingestion/youtube.py`. Its dependencies
are declared by the `collectors` extra; only explicit collection loads `.env`/reads
`YOUTUBE_API_KEY` and initializes the client. Normal imports and dashboard use never
collect data. This collector's live API access is unverified and is not part of the
required installation or mentor demonstration. CLI options are available through:

```powershell
.\.venv\Scripts\python.exe fetch_youtube.py --help
.\.venv\Scripts\python.exe save_data.py --help
```

## 10. Dataset and optional regeneration

- **Dataset:** Women's E-Commerce Clothing Reviews, version 1.
- **Publisher/curator:** Kaggle account `nicapotato`; the original retailer is anonymous.
- **Source:** [publisher dataset page](https://www.kaggle.com/datasets/nicapotato/womens-ecommerce-clothing-reviews).
- **License declaration:** [publisher metadata](https://www.kaggle.com/datasets/nicapotato/womens-ecommerce-clothing-reviews/metadata), CC0-1.0.
- **Prepared files:** `data/processed/demo_reviews.csv` and `manifest.json`, both included in the repository.

The original CSV has 23,486 rows; 22,641 have valid IDs/nonempty review text.
Preparation rejects 845 empty/invalid records, ranks products by valid review
count descending and numeric Clothing ID ascending, and takes the first 200
source-order reviews per selected product. No sentiment results or star ratings
influence selection. Product labels use actual Clothing IDs and categories, not
fabricated brand/model names.

| Product | Valid source reviews | Prepared subset |
|---|---:|---:|
| Clothing 1078 - Dresses | 987 | 200 |
| Clothing 862 - Knits | 778 | 200 |

Stable review IDs retain original source row IDs. The manifest records provenance,
selection policy, excluded fields, version, and SHA-256 integrity checks. Ratings,
recommendation flags, positive-feedback counts, age, and title are excluded from
NLP inputs. Likes are zero; helpful-feedback counts are not substituted for likes.

Source CSV SHA-256:

```text
bd93cc515747ad1f87b8bc863c9e40da758509e6db6506a96d06976e61e36ee0
```

Prepared CSV SHA-256:

```text
965943770b4b4479f5a037d036128d30ee9404be4e1a28517205d1d3ca8f0ae0
```

To regenerate **optionally**, obtain the version-1 publisher CSV, place it at
`data/raw/Womens Clothing E-Commerce Reviews.csv` (create `raw/` if needed), then run:

```powershell
.\.venv\Scripts\python.exe scripts/prepare_demo_data.py --input-csv "data/raw/Womens Clothing E-Commerce Reviews.csv"
```

The script accepts another local CSV path too and copies that source into ignored
`data/raw/`. It does not download dataset records. To compare regeneration safely
without overwriting the included subset:

```powershell
.\.venv\Scripts\python.exe scripts/prepare_demo_data.py --input-csv "data/raw/Womens Clothing E-Commerce Reviews.csv" --data-dir ".venv/day3-regenerated"
```

Day 3 reproduced the exact included manifest and prepared checksum. Ordinary setup
was also verified with no original CSV present. Historical anonymized reviews and
a limited subset cannot establish current market-wide product perception.

## 11. Understanding results

**Sentiment labels.** VADER compound ranges from -1 to +1. A score at least +0.05
is positive; at most -0.05 is negative; values between are neutral. The score is a
lexicon/rule-based sentiment measure, not a calibrated probability or accuracy.
Predictions include explicit engine/model/version metadata, raw scores, and
`class_probabilities=None`.

**Overall perception.** The existing formula is:

```text
weight = 1 + log(1 + likes)
overall_score = sum(compound * weight) / sum(weight)
perception_rating = 5 * (overall_score + 1)
```

Zero likes makes every weight one, so this dataset uses the mean review compound
mapped to 0-10. It is **not a customer star-rating average**. Counts/percentages
refer to retained analyzed reviews. Original = rejected + duplicates + analyzed;
positive + negative + neutral = analyzed. Empty results have unavailable ratings.
Calculations retain precision; the UI rounds only for presentation.

**Aspects.** The extractor POS-tags nouns, ranks their frequency, filters through
an existing dimension list, and uses a frequent-noun fallback when needed. Exact
whole tokens determine review support. Sentiment joins use review IDs, not text
identity; missing/invalid predictions are excluded rather than assumed neutral.

Each aspect's estimate maps the mean compound of supporting whole reviews onto
0-10. A review praising design but criticizing material can therefore give both
features the same overall review sentiment. This is **not contextual ABSA**.
Supporting review count measures distinct reviews; mention count measures noun
occurrences and can be larger.

| Evidence volume | Supporting reviews |
|---|---:|
| Low | Fewer than 7 |
| Medium | 7-14 |
| High | At least 15 |

These tiers describe evidence quantity, not model accuracy. The original minimum-
length, English-language, and question filters can discard useful opinions; rejection
counts expose their effect. Sarcasm, mixed sentiment, and noisy nouns remain limitations.

## 12. Testing guide

Complete suite:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp=.venv/day3-test-tmp
.\.venv\Scripts\python.exe -m pip check
```

Focused pipeline/UI/offline checks:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_pipeline.py tests/test_dashboard.py -q --basetemp=.venv/day3-focused-tmp
```

For an individual file, replace the test paths with a listed file such as
`tests/test_aspects.py`. Pipeline execution is independently available through
`python -m perceptra.analysis` with the explicit `.venv` interpreter above.

`test_dashboard.py` uses Streamlit AppTest in isolated `.venv` subprocesses. It
covers real result display and controlled failure cases. Other tests cover data
integrity, identifiers, provenance, label leakage, preprocessing, scoring formulas,
ID joins, evidence tiers, imports, legacy adapters, and product isolation. Authored
fixtures are synthetic tests, never substituted for demonstration data.

The tests block external network access and runtime NLTK downloads; Windows'
internal loopback coordination is allowed in AppTest. Offline CLI analysis was
also tested with credentials removed. Internet is needed only for initial setup.

A passing run exits zero. A failed assertion, dependency problem, or timeout needs
investigation; a prior report does not prove a later environment passes. **Verification
snapshot, October 28, 2026:** 71 tests passed in both the original and fresh Windows
Python 3.13.6 environments. See [Day 3 evidence](docs/day3-verification.md).

For actual-browser checks, launch the dashboard and follow [the runbook](docs/demo.md).
Check both products, stale-result clearing, aspect evidence, a matching search,
an empty search, negative filtering, and page 2. Inspect at common desktop sizes.
AppTest alone is not browser verification. Day 3 used real Edge automation with
temporary task helpers; those helpers are not a packaged browser-test command.

## 13. Live mentor demonstration guide

This walkthrough covers preparation, the live presentation, recovery, and shutdown.
It can be followed using this README alone. Keep [docs/demo.md](docs/demo.md) nearby
as a separate presentation runbook with additional talking points.

### A. Prepare before the demonstration

**First-time setup only.** Open PowerShell in the parent directory where you want
the project, then run:

```powershell
git clone https://github.com/Xtract01/perceptra.git
cd perceptra
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe scripts/prepare_demo_data.py --prepare-nltk
```

Use Python 3.11+; the Day 3 reference environment is Python 3.13.6 on Windows.
Only the bootstrap command uses the base interpreter. All subsequent installs,
scripts, and tests use this clone's `.venv` explicitly. Activation is optional;
see section 7 for PowerShell/CMD activation and Python-launcher alternatives.
Packages stay inside `.venv` and NLTK resources inside `.venv/nltk_data/`.
Initial installation needs internet; the prepared dashboard then runs locally
without an API key, `.env` file, PostgreSQL, or the original publisher CSV.
Keep an existing working `.venv` rather than repeating first-time setup.

**Before every demonstration.** Open PowerShell in the repository root (the
directory containing `pyproject.toml`, `app/`, and `data/`) and run:

```powershell
.\.venv\Scripts\python.exe -c "import sys; print(sys.executable)"
.\.venv\Scripts\python.exe -m pip check
Test-Path -LiteralPath "data/processed/demo_reviews.csv"
Test-Path -LiteralPath "data/processed/manifest.json"
.\.venv\Scripts\python.exe -c "from perceptra.config import check_nltk_resources; check_nltk_resources(); print('Local NLTK resources ready')"
.\.venv\Scripts\python.exe -m perceptra.analysis --list-products
.\.venv\Scripts\python.exe -m perceptra.analysis --product "clothing:1078" --summary
.\.venv\Scripts\python.exe -m pytest -q --basetemp=.venv/day3-test-tmp
Get-NetTCPConnection -LocalPort 8501 -State Listen -ErrorAction SilentlyContinue
```

Confirm the executable is this project's `.venv\Scripts\python.exe`, dependency
checks pass, both file checks return `True`, NLTK validation succeeds, and both
products appear in the catalog. The smoke analysis should report `complete` with
available aspects. Tests should exit zero; 71 passed in the dated Day 3 snapshot.
Resolve failures before presenting. No listener output means port 8501 is free
when the network query succeeds; if the query is denied, availability is unverified.
For an occupied port, use the safe alternate-port procedure below.

### B. Start Streamlit

From the repository root, run:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app/streamlit_app.py
```

Keep this terminal open. Successful startup prints a local URL and leaves the
server running without a startup error. Open the printed address, normally
`http://localhost:8501`, manually if a browser does not open. The page should show
the Perceptra header, the Product selector, and the **Analyze product** button.
The initial prompt asks you to select/analyze a product; metrics appear after
analysis. Allow the first run to load the local NLP resources.

If 8501 is occupied, leave its owner running. Check 8502 first:

```powershell
Get-NetTCPConnection -LocalPort 8502 -State Listen -ErrorAction SilentlyContinue
.\.venv\Scripts\python.exe -m streamlit run app/streamlit_app.py --server.address 127.0.0.1 --server.port 8502
```

Run the second command only if 8502 is free, then open `http://127.0.0.1:8502`.
If it is occupied too, choose another available port and use that port throughout
the presentation and shutdown checks. Use a second PowerShell terminal at the
repository root for the CLI and test steps while Streamlit stays running.

### C. Present the complete working MVP

1. **Introduce Perceptra.**

   **Show:** The dashboard header before analysis.
   **Expect:** A compact product selector and introductory prompt.
   **Say:** "Perceptra helps product teams turn customer reviews into sentiment
   summaries and feature estimates, with evidence they can inspect. This MVP
   implements a local dataset-to-dashboard workflow."

2. **Explain the data source.**

   **Show:** The sidebar's Dataset, License, and Dataset source controls. The
   publisher link needs internet; the bundled manifest in `data/processed/` can
   be shown offline instead.
   **Expect:** Women's E-Commerce Clothing Reviews and CC0-1.0 provenance.
   **Say:** "These are bundled historical reviews with anonymized Clothing IDs.
   The demo needs no YouTube key because it reads local files. A separate legacy
   YouTube collector exists, but its live API access is unverified."

3. **Analyze Clothing 1078 - Dresses.**

   **Click:** Choose Clothing 1078 in **Product**, then **Analyze product**.
   **Expect:** A loading indicator followed by five overview metrics and three
   analysis tabs. The Day 3 reference has 200 analyzed reviews, an 8.85/10 rating,
   and 94.5% positive, 4.5% negative, and 1.0% neutral sentiment.
   **Say:** "These counts reflect usable reviews after preprocessing. Perception
   is an NLP-derived rating, not an average of customers' star ratings."

4. **Explain the sentiment visualization.**

   **Click:** **Sentiment overview**; point to the bar chart and exact-count table.
   Expand **Read full review** under positive or negative evidence.
   **Expect:** 189 positive, 9 negative, and 2 neutral reviews in the reference run.
   **Say:** "Local VADER uses a sentiment lexicon and rules to assign a compound
   score from -1 to +1. At least +0.05 is positive; at most -0.05 is negative.
   Here likes are zero, so perception is `5 * (mean compound + 1)`, mapped to 0-10.
   Sentiment percentages describe reviews, not model accuracy."

5. **Demonstrate aspect extraction and evidence.**

   **Click:** **Aspect estimates**, expand **Inspect supporting review evidence**,
   and select **Size** in the Aspect dropdown.
   **Expect:** Aspect names, estimated ratings, supporting counts, evidence-volume
   tiers, and up to ten supporting reviews with IDs and individual predictions.
   The Day 3 Dresses Size reference is 8.98/10 from 53 supporting reviews.
   **Say:** "We identify frequent POS-tagged nouns using a dimension list and
   fallback. An estimate averages the sentiment of whole reviews mentioning the
   term. This is not full contextual aspect-based sentiment analysis: a review
   can praise design and criticize material, yet contribute one score to both.
   High evidence volume means more supporting reviews, not proven accuracy."

6. **Explore customer reviews.**

   **Click:** **Customer reviews**. With **All sentiments** selected and search
   empty, choose **Page** 2. Then try **Positive**, **Negative**, and **Neutral**
   under **Filter sentiment**. Return to **All sentiments**, search `MATERIAL`,
   try `__no_review_matches__`, and clear the search afterward.
   **Expect:** Page 2 shows reviews 26-50; pages contain at most 25 rows. Filters
   show the chosen sentiment, matching search ignores case, and an unmatched
   search produces a useful empty message. Search/filter changes reset the page.
   **Say:** "These are original review texts linked to stable review IDs and
   predictions. Filtering changes the table, not the overall product metrics.
   Supporting evidence is also available in the aspect and sentiment views."

7. **Switch to Clothing 862 - Knits.**

   **Click:** Change **Product** to Clothing 862 and pause before analyzing.
   Then click **Analyze product** and inspect all three tabs again.
   **Expect:** Old results disappear immediately on selection. The new analysis
   has 198 usable reviews and an 8.78/10 reference rating; two of its 200 prepared
   reviews were filtered. Previous review filters/search are cleared.
   **Say:** "This is an independent product analysis: 187 positive, 10 negative,
   and 1 neutral review in our reference run. Differences describe these retained
   subsets; they do not establish a market-wide ranking of the products."

8. **Show the technical pipeline.**

   **Show:** `perceptra/ingestion/dataset_loader.py`, `nlp/cleaner.py`,
   `nlp/sentiment.py`, `nlp/aspects.py`, `analysis.py`, and `schemas.py` inside
   `perceptra/`, then `app/streamlit_app.py`. Run in the second terminal:

   ```powershell
   .\.venv\Scripts\python.exe -m perceptra.analysis --list-products
   .\.venv\Scripts\python.exe -m perceptra.analysis --product "clothing:862" --summary
   ```

   **Expect:** The catalog and structured service output, including sentiment
   totals, rating, aspect estimates, warnings, and provenance. `--summary` omits
   individual scored-review text.
   **Say:** "Data loading and validation feed preprocessing, VADER scoring,
   overall aggregation, and aspect extraction with review-ID evidence joins.
   The service returns structured results. Streamlit calls the same
   `analyze_product()` service and displays its values without duplicating the
   scoring logic. The CLI proves that analysis also works independently of UI."

9. **Demonstrate regression testing and local operation.**

   **Run:** In the second terminal:

   ```powershell
   .\.venv\Scripts\python.exe -m pytest -q --basetemp=.venv/day3-test-tmp
   ```

   **Expect:** A zero exit code and a passing summary; allow about a minute in
   the presentation schedule rather than promising a fixed runtime. A dated
   reference count is not a substitute for the actual result.
   **Show:** `.env.example` and the package dependencies in `pyproject.toml`;
   do not display a private `.env` or credentials.
   **Say:** "Regression tests cover data, filters, scoring, evidence joins,
   product isolation, and UI failures. The core workflow needs no YouTube
   credentials or PostgreSQL. Tests block external connections, and Day 3 also
   verified offline analysis and an actual browser with external access blocked."
   If asked for a live offline rehearsal, disconnect networking only if it will
   not interrupt the presentation, then reanalyze a bundled product; no install,
   download, or publisher-link access should be needed after setup.

10. **Explain limits and next steps.**

    **Show:** Expand **Method, provenance, and limitations** below the results.
    **Expect:** Engine/version, limitations, processing notes where applicable,
    and the prepared dataset checksum.
    **Say:** "We have local ingestion, VADER, whole-review aspect estimates,
    review evidence, CLI, dashboard, and tests. Contextual ABSA, verified live
    YouTube ingestion, transformer models, competitive benchmarking, PostgreSQL
    persistence, and Apache Airflow automation remain future work. The current
    historical subset and heuristic models do not establish production accuracy."

### D. Expected demo results

**Day 3 verified reference results - October 28, 2026:**

| Product | Reviews | Positive | Negative | Neutral | Rating |
|---|---:|---:|---:|---:|---:|
| Clothing 1078 | 200 | 189 | 9 | 2 | 8.85/10 |
| Clothing 862 | 198 | 187 | 10 | 1 | 8.78/10 |

These are measured reference results, not hardcoded application outputs. Reviews
means retained analyzed reviews; both prepared subsets contain 200 records.
Results may change when the dataset, preprocessing, model version, or analysis
implementation changes. Compare the current UI with current CLI output before
claiming a mismatch. See [Day 3 verification](docs/day3-verification.md) for evidence.

### E. Recover from common live-demo problems

| Problem | Safe recovery |
|---|---|
| Streamlit does not start | Read the launching terminal. Confirm the repository root and interpreter, run `pip check`, check the selected port, then retry the command in B. A printed URL alone does not prove the page loaded. |
| Browser does not open automatically | Open the URL printed in the terminal manually, usually `http://localhost:8501`; use `http://127.0.0.1:8502` for the alternate command. |
| Incorrect Python / missing packages | Print `sys.executable` with the command below, select that interpreter in the editor, and reinstall development requirements through the explicit `.venv` path. Activation is optional. |
| Missing NLTK resources | Run the NLTK preparation command below before resuming the full demo. Sentiment remains usable while aspects are unavailable. Resource download requires internet. |
| Missing or invalid dataset | Run both `Test-Path` checks in A; verify `PERCEPTRA_DATA_DIR` points at the intended data root. If it is an accidental override, clear it as below and restart Streamlit. For missing files, obtain an intact bundled CSV/manifest pair from the maintainer; ordinary setup needs no original CSV. Optional regeneration is in section 10. |
| Port 8501 already in use | Inspect its listener with the command in A; leave unrelated applications running and follow B to use a free alternate port. |
| Dashboard is empty | Select a product and click **Analyze product**. For no matching reviews, clear search and select **All sentiments**. For no usable analysis, inspect rejection counts/warnings and run the CLI smoke test; do not fabricate a rating. |
| Tests fail | Read the named failure/traceback, check interpreter, dependencies, NLTK, and data, then rerun the failing file. Do not claim the demo passed based on historical counts. If unresolved, show the CLI only as a diagnostic and state the limitation. |

Use these exact commands from the repository root as appropriate:

```powershell
.\.venv\Scripts\python.exe -c "import sys; print(sys.executable)"
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe scripts/prepare_demo_data.py --prepare-nltk
```

Only to clear a mistaken data override in the terminal that will launch Streamlit:

```powershell
Remove-Item Env:PERCEPTRA_DATA_DIR -ErrorAction SilentlyContinue
```

For a failing pipeline test, for example, a focused rerun is:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_pipeline.py -q --basetemp=.venv/day3-focused-tmp
```

Use the actual failing file name when another file failed. See section 14 for
additional Windows troubleshooting; never suppress checksum failures or terminate
unrelated processes to make the demonstration appear successful.

### F. Stop and verify shutdown

Press **Ctrl+C** in the terminal that launched Streamlit. Wait for the stopping
message and return of the PowerShell prompt, which confirms that command exited.
If pytest is still running in the second terminal, let it finish or interrupt it
there with Ctrl+C. Closing the browser alone does not stop Streamlit.

Check the port you used, normally 8501:

```powershell
Get-NetTCPConnection -LocalPort 8501 -State Listen -ErrorAction SilentlyContinue
```

Use `-LocalPort 8502` if you chose the alternate port. No listener output, when
the query succeeds, confirms that port is released. If one remains, inspect its
`OwningProcess` without stopping it:

```powershell
$demoListeners = Get-NetTCPConnection -LocalPort 8501 -State Listen -ErrorAction SilentlyContinue
$demoListeners | Select-Object LocalAddress, LocalPort, OwningProcess
$demoListeners | ForEach-Object { Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue }
```

Use the actual port here too. Return to your own server's terminal for graceful
shutdown; a remaining listener may belong to someone else. Do not indiscriminately
kill Python or browser processes. Close the demo tab/window you opened and retain
`.venv`, its installed packages/NLTK resources, datasets, and source files.
Restart later with the same command in B.

## 14. Windows troubleshooting

| Problem | Recovery |
|---|---|
| Python not recognized | Install the reference Python version or use the Windows `py` launcher; confirm the interpreter before creating `.venv`. |
| Python version below 3.11 | Use a suitable interpreter for a new project `.venv`; do not alter system packages. |
| PowerShell blocks activation | Skip activation and use `.\.venv\Scripts\python.exe` directly. No execution-policy change is necessary. |
| Activation points at another environment | Close/reactivate the shell or use explicit paths; print `sys.executable` and `sys.prefix`. |
| Missing packages | Run the appropriate requirements installation through this project's `.venv` interpreter, then `pip check`. |
| `No module named perceptra` | Run editable installation from the repository root and ensure VS Code uses the same `.venv`. Do not patch `sys.path`. |
| Missing NLTK resources | Run the explicit `--prepare-nltk` setup command; verify `.venv/nltk_data/`, not a global cache. |
| Missing/invalid dataset | Check both bundled processed files and the `PERCEPTRA_DATA_DIR` override. Obtain intact repository copies from the maintainer; the original CSV is not required. Regenerate only if you have the publisher source and intend to replace the subset. |
| Checksum mismatch | Restore the expected prepared CSV/manifest pair or regenerate them together. Do not edit the checksum just to hide a mismatch. |
| Streamlit fails to start | Read terminal errors, verify `.venv`, run `pip check`, check the working directory and port, then retry. |
| Invalid port/configuration | Supply a numeric free port and correct invalid overrides; configuration errors occur before the UI starts. |
| Empty analysis | Inspect rejection counts and warnings; ensure reviews are nonempty and pass retained language/length filters. No rating is fabricated. |
| Unexpected sentiment/aspects | Inspect original review evidence; VADER and whole-review feature estimates have known limitations. Do not manually change statistics. |

To clear a mistaken data override in the current PowerShell session:

```powershell
Remove-Item Env:PERCEPTRA_DATA_DIR -ErrorAction SilentlyContinue
```

Port conflicts: inspect the listener and identify its process without stopping it:

```powershell
Get-NetTCPConnection -LocalPort 8501 -State Listen -ErrorAction SilentlyContinue
```

If an unrelated application owns 8501, leave it running and use:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app/streamlit_app.py --server.address 127.0.0.1 --server.port 8502
```

Open `http://127.0.0.1:8502` and stop that instance with Ctrl+C afterward. Never use
commands that indiscriminately terminate all Python, Edge, or Node processes.

## 15. Developer handoff

| Work area | Where to change and what to preserve |
|---|---|
| New ingestion source | `perceptra/ingestion/`; return normalized review records with stable product/review IDs and provenance. Keep network collection explicit. |
| Cleaning/filtering | `nlp/cleaner.py`; preserve sentiment cues and reconciliation of rejected/duplicate/analyzed counts. |
| New sentiment engine | `nlp/sentiment.py`; extend explicit validation/metadata and output contracts, keeping VADER default. Preserve probability/score distinctions and never silently switch engines. |
| Improved aspects | `nlp/aspects.py`; preserve review-ID joins and evidence. Evaluate contextual attribution separately from the current proxy. |
| Service orchestration | `analysis.py`; keep it independent of Streamlit and retain structured empty/error behavior. |
| Dashboard | `app/streamlit_app.py`; render service values rather than duplicate scoring, and test state reset/filter behavior. |
| Shared contracts | `schemas.py`; make additive changes where possible and update service/UI/tests together. |
| Configuration | `config.py` and `.streamlit/config.toml`; keep paths clone-local and do not introduce required secrets. |
| Tests | Add focused pytest cases for behavior and failures. UI tests must not contaminate headless import checks. |

Keep compatibility wrappers delegating to the canonical package. Do not change
stable IDs, score meanings, threshold boundaries, or JSON keys without reviewing
all consumers. Keep real dataset provenance separate from authored test fixtures.

After the mentor demonstration, four contributors can own ingestion, NLP/aspects,
dashboard, and integration/testing/docs. Agree shared schema changes first, use
feature branches and pull requests under the maintainer's workflow, and integrate
small changes. No branches or Git writes were performed by the verification task.

## 16. Future roadmap - not current capabilities

- Maintained multi-source ingestion and safer live collection.
- Category-adaptive aspect/phrase extraction and TF-IDF evaluation.
- Contextual aspect-based sentiment analysis and labeled model evaluation.
- Optional appropriately licensed Hugging Face models, subject to the free-only
  constraint and approval before large weight downloads; published weights do not
  guarantee a free hosted endpoint.
- Competitive benchmarking with comparable products/evidence.
- Self-hosted PostgreSQL persistence and analysis history.
- Self-hosted Apache Airflow scheduling, retries, and monitoring.
- Accuracy/latency evaluation, deployment, and operational improvements.

## 17. Licensing and attribution

The publisher declares the dataset **CC0-1.0**, a public-domain dedication; its
[official terms](https://creativecommons.org/publicdomain/zero/1.0/) do not impose
an attribution condition. This project nevertheless retains the publisher/source,
version, selection details, and checksums so the demonstration is reproducible.
Do not imply endorsement by the original retailer, curator, or dataset publisher.

The dataset's dedication does **not** license the application source code.
**No repository software LICENSE file is currently present; this README does not
claim that Perceptra's source is MIT-licensed.** The maintainers should agree and
add an appropriate software license separately. Dependencies retain their own
licenses; their licensing does not automatically license this repository.
