# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

Not a software repository. It is an analytics workspace running one dataset through
a fixed teaching method and out to three deliverables: a live dashboard, a client PDF and
a 30-slide deck. Since 2026-10-11 the dataset is the PMARIS asset-reliability file; the
earlier retail engagement is archived, untouched, in `_archive_retail_v1/`.

```
00_Method/        AIB902_Agentic_Analytics_Dashboard_Playbook.md  - the method, the spec (v4.0)
01_Data/          Group_9230_Team1_PMARIS_Enterprise_Dataset.csv  - the single source file
02_Analysis/      analyze_pmaris.py -> findings.json              - all figures come from here
03_Dashboard/     watcher.py, styles.css, app.js, *.html          - the Live Decision Dashboard
04_Deliverables/  make_figures.py, make_report.py, make_deck.py   - PDF + PPTX, read findings.json
_archive_retail_v1/                                               - previous engagement, read-only
```

The four state files at the root (`CLAUDE.md`, `PROJECT_MEMORY.md`, `PROGRESS.md`,
`SESSION_LOG.md`) stay at the root. The session skills read them from the project root
and they must not be moved into a subfolder.

**Path discipline:** scripts resolve their inputs relative to their own location, not the
working directory, so they run from anywhere. `analyze_pmaris.py` and `watcher.py` both reach up
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

Pages: `index.html` (overview), `dashboard.html` (Explorer, cross-filtered),
`levers.html`, `sites.html`, `watchlist.html`, `quality.html` (Data & Method).
The watcher also writes `live_stamp.json`; pages poll it every 250 ms and fetch the
full feed only when it changes (the 1 s full poll missed the D3 target on this feed).

Both terminals must run from `03_Dashboard/`, because the pages fetch `live_data.json`
as a same-folder relative path. Other useful commands:

```bash
python3 02_Analysis/analyze_pmaris.py   # stdlib only, ~90 s; writes findings.json
# 04_Deliverables needs matplotlib, reportlab, python-pptx (requirements.txt), e.g. in a venv:
python make_figures.py && python make_report.py && python make_deck.py
# restart watcher.py after re-running the analysis so the study constants reload
```

The two processes are independent and restartable by design. Closing and reopening the
dashboard tab just resumes polling.

## Measured facts about the current source file

`01_Data/Group_9230_Team1_PMARIS_Enterprise_Dataset.csv`, profiled 2026-10-11. Path A:
one flat CSV with a date column. 5,000 rows × 60 columns, zero missing cells, zero
duplicates. One row = one 30-day observation window of one asset. 2025-09-01 to
2026-08-31; six sites in four industries (cement, oil & gas drilling, lab equipment,
in-vitro diagnostics).

Traps:

- **`Asset_ID` is not an asset key.** 499 of 500 IDs change site between observations
  and age runs backwards for 497. No per-asset history, replacement or remaining-life view.
- **Derived columns.** Financial exposure ≈ revenue loss (r = 0.999); failure probability
  mirrors the health index (r = −0.972); `Executive_Intervention_Priority` is a fixed
  banding of `Maintenance_Priority_Index`. Never add or double-show these.
- **Windowed measures.** Totals sum overlapping 30-day snapshots; compare means per window.
- **Large n.** Nearly everything clears p < 0.05; effect size (η²) and Kruskal-Wallis
  agreement decide the wording. 26 of 33 tests survive Bonferroni.

Findings (all in `02_Analysis/findings.json`): top 10% of windows carry 44.7% of loss;
high-risk windows (FP ≥ 50%, 19.2%) carry 46.7%; reactive 2.3x predictive downtime;
shortage 2.9x available; basic crews 1.8x expert; PM < 80% about 2.2x; P1/P2 flag misses
829 of 960 high-risk windows. Manufacturer and shift: no difference. Site: real, η² 0.013.

The retail file's facts (no signal, Benford rejection) are in `_archive_retail_v1/CLAUDE.md`.

## Writing conventions in the playbook

If you edit the playbook, match what is already there. Every figure carried over from the
Wide World Importers reference dataset is tagged **MEASURED** and was computed from real
data, never estimated. WWI numbers are one worked configuration of a generic method, not
universal constants; anything presented as method rather than measurement is labelled
"Source: Playbook methodology, not derived from any one dataset." Keep that distinction
visible when adding material.
