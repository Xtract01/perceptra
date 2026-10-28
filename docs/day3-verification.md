# Day 3 verification and handoff

Verification date: October 28, 2026. Platform: Windows, Python 3.13.6.
This is a dated execution record, not a compatibility or accuracy guarantee.

## Scope and changes

The repository began Day 3 on `main` with a clean working tree at
`5f67f2c` (Day 2). Existing ingestion, schemas, analysis, NLP, CLI adapters,
configuration, dependency declarations, prepared data, and dashboard were inspected.
No major feature, dependency, inference algorithm, or layout was added.

One usability issue was corrected: the missing-dataset message previously told
users only to prepare the original publisher CSV. It now explains how to check
the bundled processed CSV/manifest and `PERCEPTRA_DATA_DIR`, and makes clear that
the original CSV is optional. A browser check confirmed the corrected guidance.

Files changed:

- `app/streamlit_app.py`: dataset recovery guidance.
- `tests/test_dashboard.py`: two important coverage gaps, invalid data-root
  configuration and matching case-insensitive search with product/filter reset.
- `README.md`: complete 17-section setup, architecture, operation, data,
  interpretation, testing, mentor demonstration, troubleshooting, handoff,
  roadmap, and licensing guide, written after application stabilization.
- `docs/demo.md`: focused live mentor runbook with narration and recovery steps.
- `docs/day3-verification.md`: this execution record.

Architecture remains dataset loader -> product-scoped preprocessing -> local
VADER and noun/POS-based feature estimates -> typed analysis service -> Streamlit.
The service remains usable without importing Streamlit. Compatibility wrappers
continue to delegate to the package.

## Automated tests and dependency consistency

Baseline command in the original project:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp=.venv/day3-test-tmp
```

Baseline: **69 passed in 34.02 seconds**. After the two focused test additions and
the final recovery-text correction, the complete suite was run in both projects:

| Environment | Final full-suite result |
|---|---|
| Original project `.venv` | 71 passed in 44.29 seconds |
| Fresh source snapshot and its own `.venv` | 71 passed in 37.17 seconds |

There were no failures or skipped tests in either final run. The same command was
used from each project's root with that project's explicit interpreter.

```powershell
.\.venv\Scripts\python.exe -m pip check
```

Both environments reported **No broken requirements found**.

After writing the documentation, the documented focused command was executed in
the clean project:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_pipeline.py tests/test_dashboard.py -q --basetemp=.venv/day3-focused-tmp
```

Result: **21 passed in 36.76 seconds**, with no failures or skips.

Coverage includes data integrity/provenance, label exclusion, validation,
preprocessing, language filtering, deduplication, thresholds, scoring formula,
aspect review-ID matching, missing predictions, evidence tiers, product isolation,
empty/invalid input, missing NLTK resources, unexpected analysis errors, UI
selection/reset, filters, search, pagination, and compatibility adapters. Tests
block external connections and runtime NLTK downloads; Windows loopback use is
allowed for AppTest's internal coordination. AppTest runs in isolated subprocesses.

The three legacy processing CLIs were also executed on disposable JSON files made
from actual bundled reviews; preprocessing, VADER, and aspect output completed
successfully. No optional live collection was invoked.

## Fresh installation

A temporary source snapshot was built from the repository's tracked-file list,
then synchronized with the final application/test fixes. It contained no `.git`,
original publisher CSV, `.env`, existing virtual environment, or downloaded NLTK
resources. Its separate `.venv` was created with the existing project's explicit
Python interpreter using `-m venv`; it did not reuse installed project packages.

From the clean project root, its own interpreter successfully installed:

```powershell
.\.venv\Scripts\python.exe -m pip install --cache-dir .venv/pip-cache -r requirements.txt
.\.venv\Scripts\python.exe -m pip install --cache-dir .venv/pip-cache -r requirements-dev.txt
.\.venv\Scripts\python.exe scripts/prepare_demo_data.py --prepare-nltk
```

The cache option only kept temporary download artifacts inside the verification
environment. Dependency declarations were unchanged. Observed installed versions:

| Component | Version |
|---|---|
| Python | 3.13.6 |
| vaderSentiment | 3.3.2 |
| langdetect | 1.0.9 |
| NLTK | 3.10.4 |
| Streamlit | 1.66.1 |
| pytest | 9.2.0 |

Before downloading resources in the fresh project, setting `NLTK_DATA` to the
original project's populated directory did not make aspects available: sentiment
still completed while aspects correctly reported missing resources. Explicit
setup then downloaded the required small resources into the fresh project's own
`.venv/nltk_data/`; full analysis and all tests passed afterward. Package locations
were checked inside that virtual environment. The editable project correctly
resolved to its own source snapshot.

This is a real fresh dependency/resource installation and source isolation test
on the same Windows computer. It is **not** a remote Git clone or an independent
test on another physical computer/OS. Packaging declares Python 3.11+, but other
Python versions were not independently validated. Installation is version-ranged,
not a fully pinned dependency lockfile.

No project packages were installed globally. No required hidden file, secret,
database, source CSV, or original-environment NLTK cache was discovered.

## Data and numerical verification

The prepared CSV and manifest are tracked and were sufficient for the fresh
project. Optional regeneration from the local publisher CSV was run with a separate
temporary data directory. It reproduced the included manifest exactly and the
same prepared SHA-256 recorded in the README/manifest. The original CSV and
bundled dataset were not replaced by these checks.

Independent numerical checks reconciled analyzed counts, sentiment percentages,
the documented rating formula, and aspect support review IDs/counts:

| Product | Prepared | Analyzed | Positive | Negative | Neutral | Mean compound | Rating / 10 | Aspects |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Clothing 1078 - Dresses | 200 | 200 | 189 | 9 | 2 | 0.770226 | 8.851130 | 8 |
| Clothing 862 - Knits | 200 | 198 | 187 | 10 | 1 | 0.755768687 | 8.778843434 | 8 |

The two filtered Knits reviews are accounted for by preprocessing. Counts are not
fabricated and the dashboard contains no hardcoded expected model results.
Missing predictions do not become neutral scores; empty analyses have unavailable
ratings. Feature estimates remain whole-review sentiment proxies, not contextual ABSA.

## Actual browser, offline, and failure checks

Real installed Microsoft Edge was driven headlessly through its local debugging
protocol, using an isolated temporary browser profile. This is actual browser
automation, separate from Streamlit AppTest. Screenshots were visually inspected;
this record does not claim a separate manual click-through by a human reviewer.

The Streamlit server ran from the fresh source project's own interpreter.
Both products passed actual-browser checks for:

- Product selection, analysis, metrics matching the analysis service, and charts.
- Aspect tables and expanded supporting review evidence.
- Review page 2, negative sentiment filtering, matching `MATERIAL` search,
  no-match empty state, and search clearing.
- Clearing old metrics before analyzing the second product.
- Desktop layouts at 1440x1000 and 1366x900, with readable tables, no page-width
  overflow, and no Streamlit exception elements in the checked result view.
- Missing-data startup with useful recovery guidance and no fabricated metrics.

Offline service checks removed YouTube/Hugging Face/database credentials and
blocked external socket connections and NLTK downloads. For the browser run,
the fresh server used a temporary test-only network guard and Edge blocked external
host resolution while allowing local app/debug connections. Both products worked.
This is application-level network blocking, not a claim that the machine's network
adapter was physically disconnected.

Failure checks used temporary paths/mocks rather than damaging real files:

| Scenario | Verified behavior |
|---|---|
| Missing dataset / invalid data root | Clear UI recovery message, no stale/fabricated metrics |
| Invalid product | Controlled service error; UI does not display misleading results |
| Empty catalog/reviews | Explicit empty/unavailable state |
| Missing NLTK resources | Valid sentiment retained; aspects unavailable with setup guidance |
| Unexpected analysis exception | Friendly UI error, no stale result |
| Port 8501 conflict | Owned test listener; explicit-port startup returned useful CLI error and nonzero exit |
| Invalid Streamlit port | Invalid numeric configuration rejected with useful CLI error |
| Alternate port | Documented command became healthy on 127.0.0.1:8502 and shut down with exit 0 |

## Documentation validation

After the README/runbook were written, the clean project's interpreter repeated
dependency checks, interpreter/import identity, product listing, both summary
analyses, optional collector `--help` commands, the README Python API example,
the 21 focused tests, and alternate-port startup/shutdown. PowerShell and CMD
activation resolved to the project's interpreter. Core setup, CLI, dashboard,
and shutdown instructions agree with actual behavior.

The clone URL is documented, but no new checkout or remote Git operation was
performed. Maintainers must publish the local changes before other developers
receive this documentation and Day 3 fixes through a clone.

## Cleanup

Cleanup was completed and verified after the tests and documentation checks:

| Check | Final result |
|---|---|
| Streamlit | Task servers stopped; final browser-run servers and alternate-port server exited 0 |
| Port 8501 | No listening connection |
| Port 9333 | No listening connection; isolated Edge debugging session closed |
| Port 8502 | No listening connection after documented recovery-command check |
| Python / pytest / helper scripts | No remaining task-owned matching processes |
| Edge | No remaining processes using the task's isolated profile |
| Other background services | No task-owned services remain |
| Temporary files | Disposable source snapshot/environment, regenerated copy, legacy JSON outputs, pytest temporary directories, browser profile/screenshots/logs, and helper scripts removed |
| Original `.venv` | Preserved; its interpreter still runs and system site packages remain disabled |
| Original NLTK data | Preserved; all required resources resolve in `.venv/nltk_data/` |
| Data and project files | All tracked files remain present; prepared-data SHA-256 still matches the manifest |

Servers were shut down using their own process groups/control-break signal and
the isolated browser using the debugging protocol's close command. Final process
and listener inspection found nothing requiring termination. Unrelated user
applications were not stopped.

Deletion used an explicit list of Day 3 artifact names. Each resolved absolute
target was checked to be below the original `.venv` directory and not that
directory itself. The temporary verification copy's own dependencies/resources
were removed with that copy; the real project's installed dependencies, NLTK
resources, raw source CSV, prepared dataset, and source files were retained.

Documentation links and `git diff --check` passed. The branch remains `main`
and the staging area remains empty. Only the five Day 3 files listed above changed.

## Readiness and limitations

The implemented MVP has passed the functional, fresh-install, numerical,
offline, browser, and documentation checks needed for a mentor demonstration
and developer handoff. Process, port, artifact, and preserved-resource cleanup
checks have also passed. Day 3 is complete.

The README and focused demo runbook prepare another contributor to run the MVP
and four future contributors to work in ingestion, NLP/aspects, dashboard, and
integration/testing/docs with agreed contracts. No branches, staging, commits,
pushes, pull requests, or remote changes were performed.

No unresolved functional blocker was found in the verified MVP workflow.
Remaining limits: historical anonymized subset, heuristic language/length filters,
lexicon sentiment, whole-review aspect proxies, unverified live YouTube API,
unvalidated accuracy/hardware minimums, and testing on one Windows/Python setup.
Contextual ABSA, Hugging Face model integration, benchmarking, PostgreSQL, Airflow,
evaluation, and deployment remain future work. There is no repository software
LICENSE file; the dataset's CC0 dedication does not license the application code.
