# Sales Project

An analytics engagement built on one dataset, `sales_data_large.csv`, following the
AIB902 Agentic Analytics method. It produces two deliverables: a client-facing data
quality report, and a live, multi-page decision dashboard.

## The headline

The dataset is **technically flawless and analytically empty**. It passes all eight
standard cleaning checks with zero defects, then fails all seven tests of meaning.
Revenue is statistically indistinguishable from uniform random noise on every
dimension tested. No prioritisation decision can be supported by this file.

Everything in this project is built to report that honestly rather than hide it.

## Layout

| Folder | What lives there |
|---|---|
| `00_Method/` | The playbook. The method and the spec for everything below. |
| `01_Data/` | `sales_data_large.csv`, the single source of truth. Never edited by scripts. |
| `02_Analysis/` | `analyze.py` and `analyze_deep.py`. Every figure quoted anywhere comes from these. |
| `03_Dashboard/` | The live dashboard: watcher, shared styles and runtime, six pages. |
| `04_Deliverables/` | `make_report.py` and the client PDF it builds. |

Four state files sit at the root and stay there: `CLAUDE.md` for agent guidance,
`PROJECT_MEMORY.md` for durable rules, `PROGRESS.md` for the current snapshot, and
`SESSION_LOG.md` for history.

## Running the dashboard

Two terminals, both from `03_Dashboard/`:

```bash
cd 03_Dashboard
python watcher.py             # terminal 1: polls the CSV, rewrites live_data.json
python -m http.server 8000    # terminal 2: serves this folder
```

Then open <http://localhost:8000/index.html>.

To see it live: edit any row in `01_Data/sales_data_large.csv`, save, and watch the
figures move. Target is under one second end to end.

## Running the analysis

```bash
python 02_Analysis/analyze.py          # cleaning checklist, insights, signal tests
python 02_Analysis/analyze_deep.py     # seven-angle battery; slow, runs 60k permutations
python 04_Deliverables/make_report.py  # rebuilds the client PDF
```

Both analysis scripts use the Python standard library only. The PDF generator needs
`reportlab`.

## The dashboard

Six pages sharing one watcher, one stylesheet and one runtime.

| Page | What it is for |
|---|---|
| `index.html` | Overview. The year in one page: KPI tiles and the monthly trend. |
| `dashboard.html` | The comprehensive cross-filtered view. Slicers on category, city, age band and gender; click any slice, bar, column or point and every visual re-filters. |
| `categories.html` | Product categories, including the category-by-city heatmap. |
| `geography.html` | Cities, including the bootstrap confidence intervals. |
| `customers.html` | Demographic attributes of transactions, not of customers. |
| `quality.html` | What the data cannot support, and why. Designed, not an apology note. |

Chart types are all hand-written SVG or CSS: KPI tiles with sparklines, area and
line trend, columns, horizontal bar lists, donut, stacked composition bars, heatmap,
dot-and-whisker confidence intervals, and a scatter.

## Architecture

No framework, no build step, no CDN, no charting library. The watcher and the pages
are two independent, restartable processes that agree on exactly one thing: the shape
of `live_data.json`. Change one side of that contract and you must change the other.

Charts are hand-written inline SVG and CSS. The colour palette is the validated
default from the data visualization method, checked in both light and dark mode.

The comprehensive page cross-filters client-side. The watcher publishes a compact
row-level feed alongside the aggregates, roughly 36 KB for this dataset, so every
visual can recompute from the same filtered row set without a server round trip.

Figures quoted in prose are bound to the feed through class hooks, so a headline can
never contradict the tiles beneath it after the data changes. Anything measured once
rather than computed live, such as the bootstrap intervals, is marked as a study
constant and shows a warning when the source file no longer matches the study.
