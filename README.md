# Sales Project (now: PMARIS asset reliability)

**Live site (snapshot):** https://adhamashraf40.github.io/pmaris-reliability-dashboard/

An analytics engagement following the AIB902 Agentic Analytics method. Since
11 October 2026 the source is `Group_9230_Team1_PMARIS_Enterprise_Dataset.csv`, an
industrial asset-health file: 5,000 thirty-day observation windows, 60 columns, six
sites in four industries, September 2025 to August 2026. The earlier retail engagement
(`sales_data_large.csv`) is preserved untouched in `_archive_retail_v1/`.

It produces a live six-page decision dashboard, a 15-slide Executive Presentation, a
25-page Comprehensive Analytical Report, plus a ten-page assessment and a thirty-slide deck. All three read the same `02_Analysis/findings.json`.

## The headline

Put the next EGP on four controllable levers and on a wider escalation list.

- Loss is concentrated: the top 10% of windows carry 44.7% of revenue loss; the 19.2%
  of windows with failure probability ≥ 50% carry 46.7%.
- It tracks levers management controls: reactive maintenance runs 2.3x the downtime of
  predictive, spare-part shortages 2.9x available stock, basic crews 1.8x expert, PM
  compliance below 80% about 2.2x above it. All survive a Bonferroni-corrected test.
- The executive P1/P2 flag misses 829 of the 960 high-risk windows (EGP 723M exposure).

Limits: `Asset_ID` is not a stable asset key, so nothing tracks one machine over time;
and the lever effects are associations from observational data, not proven causes.

## Layout

| Folder | What lives there |
|---|---|
| `00_Method/` | The playbook, v4.0. Part III (Sections 20 to 25) was written from this engagement. |
| `01_Data/` | The source CSV. Never edited by scripts. |
| `02_Analysis/` | `analyze_pmaris.py` → `findings.json` and `analysis_log.txt`. Every figure comes from here. |
| `03_Dashboard/` | Watcher, shared styles and runtime, six pages. |
| `04_Deliverables/` | `make_figures.py`, `make_report.py`, `make_deck.py` and their outputs. |
| `_archive_retail_v1/` | The previous engagement's scripts, dashboard, PDF and state files. |

## Running the dashboard

Two terminals, both from `03_Dashboard/`:

```bash
cd 03_Dashboard
python3 watcher.py             # terminal 1: polls the CSV, rewrites live_data.json
python3 -m http.server 8000    # terminal 2: serves this folder
```

Then open <http://localhost:8000/index.html>. Edit and save any row of the CSV and the
pages update in under a second (measured: 376 ms mean, 621 ms max over 10 edits).

| Page | What it is for |
|---|---|
| `index.html` | Overview: the headline, five KPI tiles, the two biggest levers, the flat year, the priority mix. |
| `dashboard.html` | Explorer: slicers on six dimensions; click any bar, column, slice or heatmap cell and every visual re-filters. |
| `levers.html` | Strategy, spares and skill with bootstrap intervals; PM-compliance deciles; lever thresholds; health bands. |
| `sites.html` | Sites, criticality, asset class, environment; manufacturer and shift shown as non-findings. |
| `watchlist.html` | The escalation gap: live list of high-risk windows not flagged P1/P2, ranked by exposure. |
| `quality.html` | Data & Method: cleaning checklist, the broken key, derived columns, the full significance register. |

## Rebuilding everything

```bash
python3 02_Analysis/analyze_pmaris.py          # stdlib only, ~90 s; writes findings.json
cd 04_Deliverables
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # once
.venv/bin/python make_figures.py               # charts -> figures/
.venv/bin/python make_report.py                # PMARIS_Reliability_Assessment.pdf
.venv/bin/python make_deck.py                  # PMARIS_Reliability_Deck.pptx
.venv/bin/python make_exec_deck.py             # PMARIS_Executive_Presentation.pptx (15 slides, subset of the deck)
.venv/bin/python make_full_report.py           # PMARIS_Comprehensive_Analytical_Report.pdf (25 pages)
```

Restart `watcher.py` after re-running the analysis so the dashboard picks up the new
study constants.

## Architecture

No framework, no build step, no CDN, no charting library. The watcher and the pages are
two independent, restartable processes that agree on one thing: the shape of
`live_data.json`. The watcher also writes a tiny `live_stamp.json`; pages poll it every
250 ms and fetch the ~310 KB feed only when it changes. Prose figures are bound to the
feed through class hooks; study constants (tests, intervals) carry a staleness warning
when the live row count no longer matches the study.
