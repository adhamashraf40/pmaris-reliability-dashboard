# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

Not a software repository. It is an analytics workspace running one dataset through
a fixed teaching method and out to two deliverables: a client PDF and a live dashboard.

```
00_Method/        AIB902_Agentic_Analytics_Dashboard_Playbook.md  - the method, the spec
01_Data/          sales_data_large.csv                            - the single source file
02_Analysis/      analyze.py, analyze_deep.py                     - all figures come from here
03_Dashboard/     watcher.py, styles.css, app.js, *.html          - the Live Decision Dashboard
04_Deliverables/  make_report.py -> Sales_Data_Quality_Assessment.pdf
```

The four state files at the root (`CLAUDE.md`, `PROJECT_MEMORY.md`, `PROGRESS.md`,
`SESSION_LOG.md`) stay at the root. The session skills read them from the project root
and they must not be moved into a subfolder.

**Path discipline:** scripts resolve their inputs relative to their own location, not the
working directory, so they run from anywhere. `analyze.py` and `watcher.py` both reach up
to `01_Data/`. If you move a script, fix its path constant rather than relying on `cd`.

## Session files, read these first

Three files in the project root carry state between sessions. Everything needed to
resume lives here; nothing outside this folder is required.

- `PROJECT_MEMORY.md` — durable rules, decisions and measured findings, each with its
  reason. Read FIRST. Append to it, do not rewrite it. Remove an entry only when it is
  proven wrong, and say so in the session log when you do.
- `PROGRESS.md` — where the project actually is: gates, what is built, next step, open
  decisions. Overwrite it each session; it is a snapshot, not a history.
- `SESSION_LOG.md` — one block per session, newest at top. Date, what shipped, what was
  learned, what failed and why. Never delete an old entry.

If one is missing, say so rather than reporting an empty state as a clean one.

## The pipeline and its gates

Stages run in order and the order is load-bearing; each stage's output is the next
stage's input. Playbook Sections 1–4 are preparation and analysis, Section 5 is the
scoping interview, Sections 6–8 are the build.

1. **Stage 0, intake** (§1) — classify the dataset, then route by the decision tree to
   Path A (flat + time), B (flat, no time), C (star schema), or D (unrelated tables).
   Everything downstream depends on this classification.
2. **Stage 1, cleaning** (§2) — dynamic checklist; constant or near-constant columns get
   dropped here and must not resurface as scoping questions later.
3. **Stage 2, modeling** (§3) — for Path C only, join fact to dimensions one at a time and
   confirm row count is unchanged after each join. A row-count increase is fan-out: stop
   and fix the dimension. Joins happen once here, never inside a refresh loop.
4. **Stage 3, insights** (§4) — compute only what Stage 0's classification supports. The
   concentration check (what share of the measure comes from the top 10% of entities) is
   the number the playbook singles out as most decision-relevant and most often skipped.
5. **Stage 4, scoping** (§5) — produces the Dashboard Scope Brief: audience, 3–5 KPIs with
   a chart type each, refresh justification, the one decision it drives, plus a headline
   sentence, a page list, and a through-line.

**Hard gate:** the Dashboard Scope Brief must be explicitly approved before any build
starts (§5.6). Do not skip ahead to writing a dashboard because the data looks obvious.

**Second gate:** Live Refresh Verification (checkpoint D3). Actually edit the source file,
save, and time the on-screen update. Target is under one second; the worked example
measured about 300ms. Claiming it should work is not the same as demonstrating it.

## Architecture constraints for the dashboard build

These are non-negotiable per §6.4. If a framework looks more convenient, the playbook's
own instruction is to push back and point at §7.1.

- **Watcher:** Python, standard library only (`csv`, `json`), no pip installs. Polls the
  source file's mtime every 0.3s, recomputes on change, rewrites `live_data.json`. It must
  never crash on a bad read (file mid-save, malformed row); skip that cycle and keep going.
  An `.xlsx` source is the one exception, add an `openpyxl` read path inside `load_rows()`.
- **Dashboard:** self-contained HTML, no CDN, no build step, no framework, no charting
  library. Fetches `live_data.json` every 1s with cache-busting. KPIs as tiles, charts as
  plain CSS/SVG. Needs a visible "live" status indicator.
- **The JSON shape `build_snapshot()` returns is the contract** between the two pieces.
  Change the reader or the writer, change both.
- **Multi-page** (§8) means several linked self-contained HTML files sharing one `<nav>`,
  one `live_data.json`, and one watcher. Overview page first, one drill-down per dimension
  the brief named. Every page opens with a one-sentence insight in plain business language
  above the first chart, never a bare chart heading.
- **Cross-filtering** lives on `dashboard.html`. The watcher publishes a compact row-level
  feed under `raw`, and the page holds filter sets that every visual reads. Clicking any
  slice, bar, column or point re-filters the whole page. This works only because the
  dataset is small; check the feed size before shipping whole rows for a larger source.
- **Prose that quotes a live figure must be data-bound.** Wrap it in one of the class hooks
  the runtime fills on every update. A headline that hardcodes a total will contradict the
  tiles beneath it the moment the source changes, and it did.
- **Anything measured once is a study constant,** not a live figure. Mark it as such and
  warn when the source no longer matches the file the study ran on. The bootstrap intervals
  do this.
- **Styling:** reuse §7.1's exact CSS custom properties and `.kpi`, `.panel`, `.bar-row`,
  `.viz-tooltip` classes on every page. Do not invent a second style per page. Light and
  dark mode both handled, tabular numbers, hairline gridlines, real hover tooltips.

## Running it, once built

Two terminals, from the folder holding the data file:

```bash
cd 03_Dashboard
python watcher.py            # terminal 1, polls ../01_Data/, writes live_data.json
python -m http.server 8000   # terminal 2, serves this folder
# then open http://localhost:8000/index.html
```

Pages: `index.html` (overview), `dashboard.html` (comprehensive, cross-filtered),
`categories.html`, `geography.html`, `customers.html`, `quality.html`.

Both terminals must run from `03_Dashboard/`, because the pages fetch `live_data.json`
as a same-folder relative path. Other useful commands:

```bash
python 02_Analysis/analyze.py         # cleaning checklist + insights, reproduces every figure
python 02_Analysis/analyze_deep.py    # the seven-angle battery (slow: 60k permutations)
python 04_Deliverables/make_report.py # rebuilds the client PDF
```

The two processes are independent and restartable by design. Closing and reopening the
dashboard tab just resumes polling.

## Measured facts about `01_Data/sales_data_large.csv`

Profiled directly from the file. Stage 0 classification: single flat CSV with a date
column, so **Path A**. 1,000 rows, 9 columns, zero missing cells, one row per sale line.

| Column | Shape |
|---|---|
| `SalesDate` | 2024-01-01 to 2024-12-31, 345 distinct dates, daily grain |
| `ProductCategory` | 5 values: Apparel, Beauty, Books, Electronics, Home Decor |
| `CustomerLocation` | 10 US cities |
| `CustomerGender` | Male, Female |
| `SalesRevenue` | 101 to 4,995, total 2,561,723 |

Three traps in this data that the naive reading of the method would walk straight into:

- **`ProductID` is not a product key.** All 100 IDs appear under more than one category.
  Treat `ProductCategory` as the product dimension; do not build a per-product drill-down
  or join `ProductID` to anything as if it were stable.
- **`CustomerID` is not a customer key.** 258 of 631 IDs carry conflicting age, gender, or
  location. Customer-level aggregation and any churn or repeat-purchase view are not
  supportable. Say so explicitly at Stage 3 rather than producing a meaningless panel.
- **`SalesRevenue` is uncorrelated with `QuantitySold`** (r = -0.06). Revenue per unit,
  average selling price, and any margin-style derived metric are not meaningful here.

These are synthetic-data artifacts. Per the playbook's own discipline, state a limit plainly
rather than forcing a view the data cannot carry.

**The fourth and largest finding: there is no signal at all.** Revenue is statistically
indistinguishable from uniform random noise on every remaining dimension. Product category,
city and gender all pass a chi-square test against a uniform distribution. The gap between
the best and worst city is reproduced by chance in 35% of 20,000 permutation simulations.
The month-on-month trend is +0.46% of an average month. The revenue values themselves match
a uniform random draw between 101 and 4,995. There is also no cost column, so profit and
margin cannot be derived.

Consequence: this file cannot support a prioritisation decision, a forecast, or any ranking
panel, because nothing in it stands out from anything else. Run `python 02_Analysis/analyze.py` to
reproduce every figure above. Do not report a difference in this dataset without testing it
for significance first; several of them look convincing and none survive.

## Writing conventions in the playbook

If you edit the playbook, match what is already there. Every figure carried over from the
Wide World Importers reference dataset is tagged **MEASURED** and was computed from real
data, never estimated. WWI numbers are one worked configuration of a generic method, not
universal constants; anything presented as method rather than measurement is labelled
"Source: Playbook methodology, not derived from any one dataset." Keep that distinction
visible when adding material.
