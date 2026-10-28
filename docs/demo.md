# Perceptra - live mentor demonstration runbook

Use this during the review. The README contains full setup, architecture, licensing,
troubleshooting, and developer instructions. This runbook assumes required setup is
complete; it does not require the original CSV, API keys, a database, or internet.

## Before the presentation

- Work from the repository root and select `.venv\Scripts\python.exe` in your editor.
- Optional PowerShell activation: `.\.venv\Scripts\Activate.ps1`.
- Verify the actual interpreter; activation alone is not sufficient.
- Confirm both bundled files exist: `data/processed/demo_reviews.csv` and `manifest.json`.
- Prepare NLTK resources beforehand if this is a fresh setup. Do not download during
  the presentation: `.\.venv\Scripts\python.exe scripts/prepare_demo_data.py --prepare-nltk`.
- Run the test suite before the live session using the README command.
- Open the README and this runbook, and close unrelated tabs that might distract.

Quick checks:

```powershell
.\.venv\Scripts\python.exe -c "import sys; print(sys.executable)"
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m perceptra.analysis --list-products
.\.venv\Scripts\python.exe -m perceptra.analysis --product "clothing:1078" --summary
Get-NetTCPConnection -LocalPort 8501 -State Listen -ErrorAction SilentlyContinue
```

The analysis should have nonempty aspect estimates. If a listener already owns
8501, identify it without stopping unrelated work and choose an available port.

## Start the demonstration

```powershell
.\.venv\Scripts\python.exe -m streamlit run app/streamlit_app.py --server.address 127.0.0.1 --server.port 8501
```

Open `http://127.0.0.1:8501`. Keep the launching terminal available for errors and
shutdown. Start with a common desktop window size; 1440-1000 and 1366x900 were checked.

## Demonstration sequence

| Step | Do | Say/check |
|---|---|---|
| 1 | Introduce Perceptra | "We help product teams understand customer sentiment and trace insights to review evidence." |
| 2 | Point out the dataset/source/license | "These are real historical CC0 clothing reviews. Clothing IDs are anonymized; this is not live scraping." |
| 3 | Select Clothing 1078 - Dresses | Confirm the category and 200 prepared reviews are shown. |
| 4 | Click Analyze product | "This runs validation, preprocessing, local VADER, and noun-frequency aspect extraction." |
| 5 | Explain analyzed count | "Counts reflect usable reviews after filters and duplicate checks." |
| 6 | Explain distribution | Show positive/negative/neutral percentages and exact chart counts. Do not call percentages model accuracy. |
| 7 | Explain perception rating | "It maps mean sentiment onto 0-10; it is not a customer star-rating average." |
| 8 | Open Aspect estimates | "These terms are extracted from review nouns. Ratings estimate sentiment of reviews mentioning each term." |
| 9 | Expand supporting evidence | Select Size and show its original review evidence. "Review IDs connect predictions to source text." |
| 10 | Open Customer reviews | Select page 2, filter Negative, then return to All sentiments and search MATERIAL. Try a nonsense search to show the empty state, then clear it. |
| 11 | Select Clothing 862 - Knits | Confirm old metrics disappear before analysis. |
| 12 | Click Analyze product again | Repeat the main metrics and aspect/review views for this product. |
| 13 | Summarize implemented work | "We have a modular local pipeline, stable IDs/provenance, a working dashboard, failure handling, and automated tests." |
| 14 | Explain limitations/future work | "Whole-review scores cannot separate conflicting feature opinions yet. Contextual ABSA, benchmarking, persistence, and scheduling are future work." |

Reference snapshot **October 28, 2026** (recalculate if data/model versions change):

| Product | Analyzed | Positive / negative / neutral | Overall rating | Aspects |
|---|---:|---|---:|---:|
| Clothing 1078 | 200 | 189 / 9 / 2 | 8.85/10 | 8 |
| Clothing 862 | 198 | 187 / 10 / 1 | 8.78/10 | 8 |

Dresses' Size estimate is 8.98/10 from 53 supporting reviews. Explain that High
**evidence volume** means at least 15 supporting reviews, not guaranteed correctness.
Two Knits reviews are filtered by the retained language/length policy.

## Technical talking points

- Data loading, preprocessing, sentiment, aspects, service orchestration, and UI
  have separate responsibilities in the `perceptra` package.
- Streamlit calls `analyze_product(product_id, engine="vader")`; it does not recalculate scores.
- All predictions come from local VADER; no paid API or large transformer is involved.
- Feature evidence joins on review IDs; missing predictions are excluded, not assumed neutral.
- Dataset labels such as star ratings and recommendation flags never enter inference inputs.
- Aspect scores reuse whole-review sentiment; mixed opinions and sarcasm remain limitations.
- The repository currently has no software LICENSE file; dataset CC0 is a separate matter.

## Recovery during the review

| Symptom | Safe action |
|---|---|
| The page cannot connect | Check the launch terminal/address; restart the same command if the server exited. |
| Port 8501 is occupied | Leave unrelated processes alone; use `--server.port 8502` and open port 8502. |
| Missing/invalid data message | Check the two processed files and `PERCEPTRA_DATA_DIR`. Ordinary execution needs no source CSV; restore intact bundled files if needed. |
| Aspect resources unavailable | Retain the valid sentiment result, explain the limitation, and run the explicit NLTK preparation before resuming the full demo. |
| Unexpected analysis error | Read the terminal, retry once, then show the CLI analysis as a diagnostic fallback without claiming the UI passed. |
| No review search matches | Clear the search and choose All sentiments. Overall product analysis is unchanged by review filtering. |
| An unexpected score appears | Inspect original text and the model limitation; do not alter displayed statistics. |

Do not install packages globally, alter checksums to suppress an error, or terminate
all Python/browser processes. Do not present this prototype as production-ready.

## Shutdown and restart

1. Press Ctrl+C in the terminal that launched Streamlit and wait for process exit.
2. Recheck the used port:

```powershell
Get-NetTCPConnection -LocalPort 8501 -State Listen -ErrorAction SilentlyContinue
```

Use 8502 in that command if you selected the alternate port. If a listener remains,
identify its owner before taking action; never stop unrelated work. Closing the
browser alone does not stop Streamlit. Restart with the same launch command.

The automated Day 3 verification also used an isolated Edge debug port 9333. That
port is not needed for a normal mentor demo. Task-owned verification servers and
browser processes were closed; see `docs/day3-verification.md` for final evidence.
