# Perceptra demo instructions and verification

## Current dashboard workflow (Day 2)

Use the existing `.venv`; do not install packages globally. Optional activation:
`.\.venv\Scripts\Activate.ps1`.

```powershell
.\.venv\Scripts\python.exe -m streamlit run app/streamlit_app.py --server.address 127.0.0.1 --server.port 8501
```

Open `http://127.0.0.1:8501`. Select **Clothing 1078 · Dresses**, click **Analyze
product**, and inspect the sentiment metrics/chart and customer evidence. Open
**Aspect estimates** to see ratings, support counts, and evidence-volume indicators;
expand the supporting-evidence section to inspect real reviews. These are whole-review
sentiment estimates, not contextual aspect-based sentiment analysis.

Select **Clothing 862 · Knits**. Confirm old metrics disappear before clicking Analyze
again. In **Customer reviews**, use sentiment/text filters and page through 25 reviews
at a time. No chart or metric is hardcoded; values come from the service result.

The small prepared CC0 dataset is already included. To rebuild from the original
publisher CSV, use the preparation command in the README. Missing aspect resources
can be prepared once with `.\.venv\Scripts\python.exe scripts/prepare_demo_data.py
--prepare-nltk`; they stay in `.venv/nltk_data/`. Subsequent analysis needs no internet.

Stop the server with Ctrl+C when finished. Verify port 8501 is no longer listening
and do not terminate unrelated Python/browser processes. The [Day 2 report](day2-verification.md)
records the actual verification performed and remaining limitations.

## Day 1 baseline (historical record)

The sections below preserve the Day 1 handoff before UI/aspect integration. Current
capabilities and commands are described above and in the Day 2 report.

## Run the local service

```powershell
.\.venv\Scripts\python.exe -m perceptra.analysis --product "clothing:1078" --summary
.\.venv\Scripts\python.exe -m perceptra.analysis --product "clothing:862" --summary
.\.venv\Scripts\python.exe -m pytest -q --basetemp=.venv/test-tmp
.\.venv\Scripts\python.exe -m pip check
```

The core service uses no Streamlit, API credentials, NLTK downloads, paid inference,
or transformer weights. It uses the bundled prepared CSV and VADER's local lexicon.
The tests block inference network requests. CLI commands are short-lived and exit;
no server is started for Day 1.

## Real dataset snapshot

Publisher: https://www.kaggle.com/datasets/nicapotato/womens-ecommerce-clothing-reviews

Publisher license metadata: https://www.kaggle.com/nicapotato/womens-ecommerce-clothing-reviews/metadata

Declared license: CC0-1.0, version 1. Dataset origin is an anonymous retailer.
The full source has 23,486 records, including 22,641 valid/nonempty review records.
Preparation rejects 845 empty/invalid source records before product ranking.

| Product | Available valid source reviews | Prepared | Analyzed | Positive | Negative | Neutral | Perception /10 |
|---|---:|---:|---:|---:|---:|---:|---:|
| clothing:1078 - Dresses | 987 | 200 | 200 | 189 | 9 | 2 | 8.851130 |
| clothing:862 - Knits | 778 | 200 | 198 | 187 | 10 | 1 | 8.778843 |

Knits has two reviews rejected by the retained language/minimum-length policy.
Neither product's prepared sample has duplicates removed. The source data are
historical and anonymized; results describe this subset, not a market estimate.

Source CSV SHA-256:

```text
bd93cc515747ad1f87b8bc863c9e40da758509e6db6506a96d06976e61e36ee0
```

Prepared CSV SHA-256:

```text
965943770b4b4479f5a037d036128d30ee9404be4e1a28517205d1d3ca8f0ae0
```

Full machine-readable provenance is in `data/processed/manifest.json`. Ratings,
recommendation labels, and helpful-feedback counts are never NLP inputs. Likes are
zero. Product selection ranks nonempty review volume, not sentiment.

## Environment

Runtime and development requirements were installed sequentially into the freshly
created project `.venv`, testing both requirements files. Dependency declarations
live only in `pyproject.toml`. The virtual environment excludes system site-packages.

Verified versions: Python 3.13.6, VADER 3.3.2, langdetect 1.0.9, NLTK 3.10.4,
Streamlit 1.66.1, pytest 9.2.0. Streamlit is installed but unused by the Day 1 service.
NLTK resources live only at `.venv/nltk_data/`. No Transformers or PyTorch installed.

## Limitations and Day 2 boundary

- No dashboard, browser UI test, or Streamlit server exists yet.
- Aspect code is moved and import-safe, preserving its legacy function/CLI. It is
  deliberately not integrated into `analyze_product` on Day 1.
- Live YouTube access is unverified; the optional dependencies are not required or
  installed by the normal runtime/development requirements.
- Language filtering is statistical; short-text and question filters can reject
  useful opinions. Counts and warnings expose that limitation.
- VADER is not a contextual model and provides no calibrated class probabilities.

The Day 2 implementation can consume `list_products()` and `analyze_product()`
directly. It should add aspect ID joins/evidence labeling and the Streamlit interface
without changing the verified review-based scoring definition.

## Executed verification

Final commands and outcomes:

```text
.venv\Scripts\python.exe -m pytest -q --basetemp=.venv/test-tmp
39 passed in 4.21s; no failures or skips

.venv\Scripts\python.exe -m pip check
No broken requirements found.

.venv\Scripts\python.exe -m perceptra.analysis --product clothing:1078
Exit 0; 200 scored reviews; 189 positive, 9 negative, 2 neutral
Overall compound 0.770226; perception rating 8.851130000000001
```

The full CLI JSON was parsed and the mean/rating independently recomputed from its
individual review scores. Both products also completed the automated real-dataset
pipeline test with network connections disabled. All five root wrappers passed
their help/identity checks; cleaner and sentiment legacy file workflows were executed.
Legacy aspect inference itself and live YouTube collection remain unverified.

The initial runtime installation used `requirements.txt` in a newly created `.venv`;
the development installation then used `requirements-dev.txt` in the same environment.
Both succeeded. Installed runtime/testing module locations were verified inside
`.venv/Lib/site-packages`, and `include-system-site-packages = false` was confirmed.
The final working-tree whitespace check passed; Git only reported its ordinary
Windows LF/CRLF conversion notice. No files were staged and the branch remained `main`.

## File inventory

Modified existing files:

```text
.gitignore
README.md
requirements.txt
fetch_youtube.py
save_data.py
clean_data.py
sentiment_analysis.py
dynamic_aspects.py
```

Created project files:

```text
.env.example
pyproject.toml
requirements-dev.txt
perceptra/__init__.py
perceptra/config.py
perceptra/schemas.py
perceptra/analysis.py
perceptra/ingestion/__init__.py
perceptra/ingestion/dataset_loader.py
perceptra/ingestion/youtube.py
perceptra/nlp/__init__.py
perceptra/nlp/cleaner.py
perceptra/nlp/sentiment.py
perceptra/nlp/aspects.py
scripts/prepare_demo_data.py
data/processed/demo_reviews.csv
data/processed/manifest.json
tests/conftest.py
tests/test_imports.py
tests/test_data.py
tests/test_preprocessing.py
tests/test_sentiment.py
tests/test_aspects.py
tests/test_youtube.py
tests/test_pipeline.py
docs/demo.md
```

The original algorithms were migrated into the listed package modules, with the
five original filenames retained as wrappers. No original project file was deleted.
Generated/ignored files include `.venv/` and its dependencies, pip/test caches and
NLTK resources, editable-install `perceptra.egg-info/`, Python bytecode, and the
original `data/raw/Womens Clothing E-Commerce Reviews.csv`.

## Process and temporary-artifact cleanup

All installation, preparation, CLI, and test processes started for this task exited.
The final Windows process query found zero task-owned Python processes. No Streamlit
or development server was started, so no task-owned listening ports needed release.
No force termination or interruption of unrelated processes was necessary.

Removed the two abandoned sandbox pytest-cache temporary directories and
`.venv/test-tmp` after verification. Preserved `.venv`, installed packages, NLTK
resources, source data, prepared data, and every required project file.

Day 1 is complete and ready for Day 2 aspect-service integration and Streamlit work.
No Day 2 implementation, staging, commit, push, branch change, or upstream change
was performed.
