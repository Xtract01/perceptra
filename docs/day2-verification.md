# Day 2 implementation and verification

## Delivered

Day 2 adds the native Streamlit dashboard and connects the existing POS/frequency
aspect algorithm to the analysis service. No new dependencies were installed, no
transformer weights were downloaded, and no paid or hosted inference was added.
All commands use the existing project `.venv` interpreter. NLTK resources remain
restricted to `.venv/nltk_data/`.

The service flow is local dataset -> preprocessing -> VADER -> review aggregation
and aspect estimates -> structured result -> Streamlit rendering. The dashboard
does not implement scoring formulas. The original Day 1 review-based scores and
distribution remain unchanged.

## Aspect implementation

- Preserves noun POS tags, frequency ranking, dimension-list filtering, the
  frequent-noun fallback, and the maximum ten-aspect selection.
- Uses exact candidate/token matches instead of arbitrary substrings.
- Joins whole-review predictions by stable review ID and checks product identity.
- Counts supporting reviews separately from noun occurrences and returns their IDs.
- Excludes absent, invalid, or nonfinite predictions instead of substituting neutral.
- Reports missing resources and optional-stage failures without erasing sentiment.
- Keeps the legacy file function/CLI as an adapter around the same core algorithm.

Ratings map the mean VADER score of supporting reviews onto 0–10. Evidence volume
is Low below seven supporting reviews, Medium from seven to fourteen, and High
from fifteen. These tiers are not model probabilities or guarantees of accuracy.

Actual prepared-dataset outputs:

| Product | Analyzed | Overall rating | Aspects |
|---|---:|---:|---:|
| clothing:1078 - Dresses | 200 | 8.851130 | 8 |
| clothing:862 - Knits | 198 | 8.778843 | 8 |

| Product | Aspect | Estimated rating | Supporting reviews | Evidence volume |
|---|---|---:|---:|---|
| clothing:1078 | size | 8.98 | 53 | High |
| clothing:1078 | material | 8.84 | 34 | High |
| clothing:1078 | color | 9.51 | 23 | High |
| clothing:1078 | quality | 9.38 | 16 | High |
| clothing:1078 | style | 9.05 | 13 | Medium |
| clothing:1078 | price | 9.56 | 15 | High |
| clothing:1078 | design | 8.70 | 13 | Medium |
| clothing:1078 | shape | 8.35 | 11 | Medium |
| clothing:862 | color | 9.27 | 50 | High |
| clothing:862 | size | 9.22 | 43 | High |
| clothing:862 | material | 8.93 | 22 | High |
| clothing:862 | quality | 9.22 | 16 | High |
| clothing:862 | shape | 8.27 | 12 | Medium |
| clothing:862 | style | 8.77 | 9 | Medium |
| clothing:862 | price | 8.57 | 8 | Medium |
| clothing:862 | design | 8.20 | 6 | Low |

## Dashboard

Launch:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app/streamlit_app.py --server.address 127.0.0.1 --server.port 8501
```

The UI includes the real product IDs/categories, source and CC0 attribution, an
explicit Analyze action, five overview metrics, a consistently ordered sentiment
chart/count table, concise positive/negative evidence previews, aspect estimates,
supporting evidence, and a review explorer with text/sentiment filters and 25-row
pages. Switching products clears prior results and filters. Filtering and paging
reuse the stored service result rather than rerunning inference.

The native theme uses a restrained teal/neutral palette. No custom components,
custom CSS, authentication, database, orchestration, or external inference is used.
Usage telemetry is disabled. Empty/failed results show guidance rather than raw
JSON or tracebacks. Routine filtering notes are kept out of the main metric area.

## Automated verification

Executed after the final application changes:

```text
.venv\Scripts\python.exe -m pytest -q --basetemp=.venv/day2-test-tmp
69 passed in 32.78s

.venv\Scripts\python.exe -m pip check
No broken requirements found.
```

All 39 Day 1 checks remain in the suite. The 30 additions cover aspect integration,
ID matching, exact-token boundaries, rating formulas, evidence-volume boundaries,
missing/invalid predictions, empty evidence, local-resource failure, legacy aspect
adaptation, and eleven AppTest scenarios.

AppTest runs in fresh `.venv` subprocesses so UI imports/session state cannot affect
the headless-service isolation tests. External connections and NLTK downloads are
blocked; Windows asyncio's internal loopback coordination is allowed. AppTest
asserts displayed percentages, counts, ratings, aspect support/rating columns,
product switching, pagination/filtering, invalid selections, empty catalogs/reviews,
missing datasets/resources, wrong-product results, and processing failures.

The initial AppTest run exposed an overly strict test guard blocking Windows'
internal socketpair. That harness issue was corrected before the passing full run.

## Actual-browser verification

Executed in a real, isolated Microsoft Edge headless browser through its local
DevTools protocol, using the existing installed browser and `.venv` libraries.
This was separate from AppTest and used the real service and prepared dataset.

Verified:

1. Open the dashboard and analyze Clothing 1078.
2. See 200 analyzed reviews, 94.5% positive, 4.5% negative, 1.0% neutral, 8.85/10.
3. Render sentiment chart/counts and the aspect table; open supporting evidence.
4. Switch to Clothing 862 and confirm all prior metrics disappear before analysis.
5. Analyze Clothing 862 and see 198 reviews, 94.4% positive, 5.1% negative,
   0.5% neutral, 8.78/10, with product-specific review rows.
6. Open the review explorer and verify the first 25 of 198 reviews.
7. Inspect screenshots at 1440×1000 and 1366×900 for hierarchy, spacing, alignment,
   readable chart labels, aspect/review tables, and scrolling.

The final review table settled to 970px wide at the 1440px viewport, with 968px
rendered canvases. The 1366px layout had no horizontal document overflow, all five
metrics fit, and no Streamlit exception element was present. An early screenshot
captured a tab-resize transition; the settled layout was rechecked and inspected.

Temporary screenshots and browser helpers are verification artifacts, not project
assets. No browser test used mock sentiment percentages or modified source data.

## Files changed

Created:

- `app/streamlit_app.py`
- `.streamlit/config.toml`
- `tests/test_dashboard.py`
- `docs/day2-verification.md`

Modified:

- `perceptra/nlp/aspects.py`
- `perceptra/analysis.py`
- `perceptra/schemas.py`
- `tests/test_aspects.py`
- `tests/test_pipeline.py`
- `README.md`
- `docs/demo.md`

Dependencies and dataset contents/checksums were not changed. The pre-existing
deletion of `.gitattributes` was left untouched. Work remained on `main`; no staging,
commits, pushes, pull requests, branch changes, or upstream edits were performed.

## Limitations and Day 3 handoff

- Aspect ratings inherit whole-review sentiment and can miss mixed feature opinions.
- Extraction is a noun-frequency baseline with a dimension list/fallback; no TF-IDF,
  phrase extraction, lemmatization, or contextual transformer ABSA is implemented.
- VADER can miss sarcasm/context, and the retained language/length policy excludes
  some useful short reviews. Two prepared Knits reviews are filtered.
- The historical CC0 sample is limited to two anonymized products and 200 prepared
  reviews per product. It does not represent current market-wide perception.
- Browser verification covered common desktop sizes. Mobile accessibility and
  production deployment were not claimed or implemented.
- Live YouTube ingestion, advanced benchmarking, persistence, and orchestration
  remain outside Day 2.

Day 3 can focus on rehearsal, final regression/failure checks, and documentation
refinement. No Day 3 work is started automatically.

## Process cleanup

Final Windows verification found **zero task-owned Python/Edge processes** and
**zero listeners on ports 8501 and 9333**. Port 8501 was used by Streamlit; 9333
was used only by the isolated browser's local DevTools interface.

The final managed Streamlit runs received CTRL_BREAK, shut down gracefully, and
exited with code 0. The isolated browser was closed through `Browser.close`.
An earlier terminal-managed Streamlit instance did not respond to Ctrl+C and could
not receive CTRL_BREAK through that terminal; only its two verified task-owned
processes were terminated before switching to managed process groups. No unrelated
Python, browser, IDE, or application process was terminated.

Removed temporary pytest/AppTest directories, isolated browser profile, screenshots,
browser/server helpers, and the task server log after inspection. Also removed the
known temporary directory left by the first sandbox AppTest check. Preserved the
existing `.venv`, installed dependencies, NLTK resources, datasets, and project files.

Day 2 is complete and ready for Day 3 stabilization/rehearsal. No task server is
left running, and no Day 3 implementation was started.
