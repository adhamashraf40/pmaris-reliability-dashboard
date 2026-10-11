# SESSION_LOG.md

What happened each session, **newest at top**. One block per session.
**Never delete an old entry.** Failures matter more than successes — they are what stops
the next session repeating a mistake.

---

## Session 6 — 2026-10-11

**Phase at start:** The source file had been replaced by `Group_9230_Team1_PMARIS_Enterprise_Dataset.csv`
(industrial asset reliability, 5,000 × 60). Everything in 02–04 still pointed at the retail file.
**Phase at end:** Full pipeline re-run on the new file; dashboard live; report, deck and playbook v4.0 shipped.

### What shipped

- Retail-era scripts, dashboard, PDF and state files copied to `_archive_retail_v1/` before anything changed.
- `02_Analysis/analyze_pmaris.py`: Stages 0, 1, 1b, 3, 3b; ANOVA + Kruskal-Wallis, Bonferroni, η²,
  bootstrap intervals, lever splits, escalation-gap check. Writes `findings.json`.
- Scoping interview run through the question tool; the user approved audience, decision, KPIs and page set.
- Dashboard rebuilt: CONFIG-driven watcher, dimension-keyed runtime, six pages, stamp-file polling.
- `make_figures.py`, `make_report.py` (10 pages) and `make_deck.py` (30 slides), all from `findings.json`.
- Playbook v4.0: Part III, Sections 20 to 25, plus a reliability bullet in Section 5.4.

### What was learned

- With strong signal the failure mode flips: everything is significant, so effect size decides the wording.
- The existing P1–P4 flag was the most actionable finding: a formula that misses 829 of 960 high-risk windows.
- Asset_ID repeats across dated rows and looks like a panel key; it is not (499/500 change site).

### What failed and why

- First D3 run: 972 ms mean, 1,262 ms max. The 1 s poll of a 312 KB feed is too slow. Fixed with a stamp file (376 ms mean).
- Explorer showed 962 high-risk rows against the watcher's 960: failure probability was rounded to one decimal in the feed.
- `.notice[hidden]` still displayed because `display:flex` beat the `hidden` attribute.
- Sites page claimed site differences "mostly reflect equipment mix", which no test backed. Rewritten to the measured η².
- No LibreOffice or PowerPoint on this machine, so deck QA used an approximate renderer. Flagged in PROGRESS.md.

---

## Session 5 — 2026-09-19

**Phase at start:** Both deliverables done; playbook at v3.0.
**Phase at end:** Playbook documents the real build; reusable template extracted.

### What shipped

- Playbook Sections **14.6 and 14.7**: how the build adapts to any dataset. One CONFIG
  block in the watcher, and every page discovering its dimensions from the feed instead
  of naming columns. Plus how to choose a page set rather than generating one panel per
  available column.
- Playbook **Section 19, The Client Report**: the Pyramid Principle structure, the
  ten-page architecture as a table, the rules that keep it client-grade, and the
  requirement to diff the report against the dashboard after any finding changes.
- Verification checklist gained the report-versus-dashboard drift check as item 13.
- `C:/Users/hp/Downloads/Analytics_Project_Template/` - the whole engagement turned
  into a reusable, dataset-agnostic template. I wrote the generic watcher myself as the
  keystone contract; five agents with strictly non-overlapping file ownership built the
  runtime, the pages, the analysis scripts, the report generator and the documentation.

### The design decision that made the template possible

Every dataset-specific fact lives in one CONFIG block, and the feed publishes a
`dimensions` list that every consumer iterates. A page that writes `d.by_city` is
welded to one dataset; a page that loops `d.dimensions` works on any of them. The
watcher emits `by_dimension`, `lookups`, `concentration` and the row-level `raw` feed
all keyed by dimension name, so adding a fourth dimension to the CONFIG adds a fourth
slicer, a fourth panel and a fourth concentration row with no code change.

Three things stay hand-authored and should: the headline, the per-page insight, and the
limitations text. Those are editorial judgements about a particular business question.

### What was learned

- **Agent file ownership has to be explicit and disjoint.** Last session two agents
  edited one generator and clobbered each other. This time every agent was told the
  exact files it owned and that it must touch nothing else. No collisions.
- **The keystone should be written by whoever understands the contract.** I wrote the
  generic watcher before fanning out, so five agents built against a fixed shape rather
  than negotiating one.

### Cost

No paid generation. One workflow with six agents.

### Handoff

The Sales Project is complete and unchanged except for the playbook. The template lives
in Downloads and is being acceptance-tested against a synthetic dataset with a different
shape, then zipped.

---

## Session 4 — 2026-09-19

**Phase at start:** Both deliverables shipped; dashboard was five static pages.
**Phase at end:** Six-page dashboard with cross-filtering, playbook at v3.0, report at 10 pages.

### What shipped

- `03_Dashboard/dashboard.html` - the comprehensive cross-filtered page, second in the nav.
  Four slicers, and every visual clickable. Donut, stacked composition bars, columns,
  scatter, sparkline KPI tiles, bar lists.
- `03_Dashboard/watcher.py` now publishes a compact row-level feed (~36 KB) alongside the
  aggregates, plus two new tests (age band p = 0.44, weekday p = 0.45).
- `03_Dashboard/app.js` gained the cross-filter engine, the slicer component, five new chart
  primitives and data-bound prose hooks.
- `00_Method/...Playbook.md` at **v3.0**: Part II adds Sections 10 to 18. Significance
  testing as a gate, the seven-angle battery, power analysis as a deliverable, editorial
  rules for weak data, the cross-filtered architecture, project structure, the verification
  checklist and chart design rules. Sections 1 to 9 untouched.
- `04_Deliverables/` report expanded to **10 pages**, then seven verified defects fixed.

### What was learned

- **A page that partly updates is a thrown exception, not a logic bug.** The filter chips
  toggled while nothing else moved. The cause was a line writing to an element id that the
  very next `innerHTML` assignment destroyed, so every draw after the first threw mid-render.
- **Instrumenting the real call beat reasoning about the code.** Three hypotheses were wrong.
  Wrapping the filter function to record its actual input settled it in one step.
- **Fix the shared contract before fanning out.** The five pages built in parallel in the
  previous session look like one product because the JSON shape, stylesheet and runtime were
  fixed first. That held again here.

### What failed

- **A workflow scripting error cost a full cycle.** I launched two authoring agents and both
  edited the same PDF generator; the playbook was never touched and stayed at v2.0 while both
  agents clobbered each other's page-count edits. One agent reported 10 pages and the other
  11, which is exactly what two writers on one file produces. I wrote the playbook myself
  afterwards and used a single focused agent for the PDF repairs. **Never let two agents
  write one file.**
- The workflow's own verifier caught the miss, which is the only reason it did not ship. A
  verification agent that re-reads the artifact on disk, rather than trusting the authoring
  agent's report, is what made that possible.

### Cost

No paid generation. One workflow with four agents, one standalone agent, one failed cycle.

### Handoff

Everything is delivered and verified. Run the dashboard from `03_Dashboard/` with
`python watcher.py` and `python -m http.server 8000`, then open `index.html`. The four open
decisions in `PROGRESS.md` are unchanged and all belong to the user; the audience question
still matters most.

---

## Session 3 — 2026-09-19

**Phase at start:** Stages 0, 1 and 3 done; nothing built.
**Phase at end:** Both deliverables shipped and verified. Live refresh passed at 103ms.

### What shipped

- `02_Analysis/analyze_deep.py` — seven independent analytical angles.
- `03_Dashboard/` — a five-page live dashboard: Overview, Categories, Geography,
  Customers, Data quality. One watcher, one shared stylesheet, one shared runtime.
- `04_Deliverables/Sales_Data_Quality_Assessment.pdf` — now four pages, with a new
  "How far we looked" section and a fourth recommendation carrying the power spec.
- Project reorganised into `00_Method`, `01_Data`, `02_Analysis`, `03_Dashboard`,
  `04_Deliverables`, plus a new `README.md`.

### What was learned

- **Seven angles, seven null results.** Two-way interactions, bootstrap intervals,
  Gini, Benford, temporal structure, power analysis, anomaly scan. The consistency
  matters more than any single test.
- **Benford's law is the strongest single piece of evidence.** Rejected at p = 2e-90,
  with the leading digits instead matching a flat random draw at p = 0.85. This
  turns "looks synthetic" into "is demonstrably generated".
- **Bootstrap intervals are the most persuasive artifact for a non-technical reader.**
  Ten overlapping intervals communicate what a p-value cannot.
- **The power analysis is the only actionable output,** so it became a recommendation
  rather than a footnote. It converts the bad news into a specification.
- **Workflows paid off here.** Six builders in parallel produced five pages and the
  PDF update. The thing that made it work was authoring the shared contract first:
  the JSON shape, the stylesheet and the runtime were fixed before any agent started,
  so parallel output still looks like one product.

### What failed or was avoided

- **I reported a false signal and caught it.** An early revenue-weighted interaction
  test used a rescaled chi-square, which is not a valid statistic on summed revenue,
  and returned p = 0.023 on category by city. A proper 20,000-shuffle permutation
  test gave p = 0.18. The script now carries the correction in its own output. A
  chi-square statistic on summed money is not chi-square distributed; when the
  statistic is non-standard, get the p-value by permutation.
- **Found and fixed a live-data defect.** The Overview headline was static prose
  reading "$2.56M across 1,000 transactions". After appending a row it contradicted
  the tiles directly beneath it, which read 1,001. Prose figures are now data-bound
  through classes the runtime fills on every update. Static analysis claims, such as
  "at 1,000 rows", were deliberately left static because they describe a completed
  test rather than the live file.
- **Avoided** letting the dashboard imply a ranking is actionable. Every page carries
  the no-signal caveat, and the Data quality page is designed as a real page rather
  than an apology note.
- The scope-brief gate was waived because the user directed the build without naming
  an audience. That is the user's call and it is recorded, not silently skipped.

### Post-build verification round, same session

The workflow's two review agents found defects my own browser check had missed.
Recording them because each is a class of mistake, not a one-off.

- **Two fabricated statistical claims.** The customers page said the age spread
  "tests as no signal" and the geography page called the weekday split "flat, not
  a weekend effect". Neither test existed in the data contract. Both claims turned
  out to be true once measured (age chi-square p = 0.44, weekday p = 0.45), but
  they were asserted before they were tested. Both tests are now computed and
  published in `live_data.json`, so the claims are backed.
- **A factual error that contradicted the dashboard's own other page.** The quality
  page and the client PDF both said "366 days covered" when only 345 of 366 days
  carry a sale. The overview page printed "345 of 366" correctly on the same
  dashboard. Fixed in both places.
- **Ranking-as-finding phrasing** survived in four spots: "leads the cities",
  "best and worst city", "the leading category". The editorial rule was applied to
  the notices but not to the generated strings. Fixed.
- **The confidence-interval panel was hardcoded** and contradicted the live tiles
  once the source changed. The intervals are legitimately study constants measured
  on the 1,000-row file, so the fix was not to make them live but to detect the
  mismatch: a stale-study banner now fires when `row_count` differs from 1,000.
  Verified by perturbing the file and watching it appear.
- **Unguarded array access** in three render functions would have thrown on an
  empty feed and blanked the page. Guarded.

**The lesson worth keeping:** I verified the dashboard myself in a browser and
declared it correct. It rendered perfectly and was still making claims it could not
support. Visual inspection confirms a page works; it does not confirm the page is
honest. The adversarial review was what caught that, and it was worth the tokens.

**A second lesson, on process:** `pkill` silently does nothing on this Windows
shell. Two stale watcher processes kept running with pre-edit code loaded in memory
and quietly overwrote `live_data.json` with a 7-test snapshot after I had published
9. Verify a process is dead before assuming a file is current. Use
`Get-CimInstance Win32_Process` and `Stop-Process`, and check command lines before
killing anything.

### Cost

No paid generation. One workflow with eight agents.

### Environment notes

- Background watcher and HTTP server were started for testing and have been stopped.
  The test row appended to the CSV was removed and the file restored to 1,000 rows.
- `reportlab` 5.0.1 installed in an earlier session and still required for the PDF.
- Still not a git repository.

### Handoff

Run the dashboard with two terminals from `03_Dashboard/`: `python watcher.py` and
`python -m http.server 8000`, then open `index.html`. Re-derive every published figure
with `python 02_Analysis/analyze.py` and `analyze_deep.py`. Rebuild the PDF with
`python 04_Deliverables/make_report.py`. Nothing is blocked on work; the four open
items in `PROGRESS.md` are all decisions for the user, and the audience question is
still the one that matters most.

---

## Session 2 — 2026-09-19

**Phase at start:** Stage 0 complete, nothing analysed.
**Phase at end:** Stages 1 and 3 complete, client report delivered as PDF, Stage 4 is the gate.

### What shipped

- `analyze.py` — the full Stage 1 cleaning checklist, Stage 3 insights, and the signal tests.
  Standard library only, reproducible, and the source of every figure quoted elsewhere.
- `Sales_Data_Quality_Assessment.pdf` — 3-page client-facing report of the data limitations,
  built for sending to the company. Rendered and visually verified page by page.
- `make_report.py` — regenerates that PDF. Kept in the project so the report is not a dead
  artifact that nobody can rebuild.
- Refreshed `PROJECT_MEMORY.md` and `PROGRESS.md`.

### What was learned

- **The dataset is uniform random noise on every dimension.** This is the project's central
  fact and it changes what can be delivered. Chi-square against uniform passes for category,
  city and gender. The best-to-worst city gap is reproduced by chance in 35% of 20,000
  permutation simulations. The monthly trend is +0.46% of an average month. The revenue
  values themselves match a uniform random draw between 101 and 4,995.
- **Stage 1 passing perfectly was the warning, not the reassurance.** Zero blanks, zero
  duplicates, zero type errors, zero outliers, zero near-constant columns, date continuity
  intact. A standard quality review would have signed this file off and moved to the build.
- **The eye was wrong and the test was right.** Dallas leads New York by 43% on revenue,
  which reads as a finding worth a panel. It is noise. Had the dashboard been built first,
  that ranking would have been presented to a stakeholder as a place to send sales effort.

### What failed or was avoided

- **A shell heredoc failed** while writing the report generator, with an unmatched-quote
  parse error. Switched to writing the file directly, which worked first time. For any script
  containing nested quotes and markup, write the file rather than piping it through the shell.
- **Avoided:** reporting the city and category differences as findings. They survived the eye
  and died under a significance test. This was the single most damaging thing the project
  could have shipped.
- **Avoided:** proposing KPIs. Stage 4 has not run, and the answers would have been guesses.
- **Fixed before delivery:** the report's first table broke "SalesRevenue" across two lines,
  and one sentence said "the supported column" where it meant the supported list. Both caught
  by rendering the PDF to images and reading them rather than trusting the build to be right.

### Cost

No paid generation, no API spend. One package installed, `reportlab` 5.0.1, for PDF output.

### Environment notes

- `pypdfium2` and `fitz` are available for rendering PDF pages to images. `pdfplumber` is not.
- Still not a git repository. No commit step at session end.

### Handoff

Stages 0, 1 and 3 are done and every number is reproducible by running `analyze.py`. The PDF
is ready to send to the company whenever the user chooses. Everything now waits on Stage 4,
and specifically on two questions only the user can answer: who the audience is, and what
single decision the dashboard is meant to drive. A third question follows from this session's
findings, namely whether the build should proceed on this file at all, wait for a production
export, or proceed as a template to be repointed at real data later. All five open items are
listed at the bottom of `PROGRESS.md`.

---

## Session 1 — 2026-09-19

**Phase at start:** nothing established. Folder held two files and no guidance.
**Phase at end:** Stage 0 complete, Path A classified, project scaffolding in place.

### What shipped

- `CLAUDE.md` — repository guidance covering the five-stage pipeline, both gates, the
  architecture constraints from playbook §6.4, run commands, and the measured dataset facts.
- `PROJECT_MEMORY.md` — durable rules with reasons attached.
- `PROGRESS.md` — state snapshot, gates table, next step, five open decisions.
- `SESSION_LOG.md` — this file.

### What was done

Read the playbook's structure and its load-bearing sections: Stage 0 intake and the
dataset-shape decision tree, Stage 2's join discipline, Stage 3's insight table, the Scope
Brief at §5.6, Prompt 4 at §6.4, both reference builds at §7, and the multi-page extension
at §8. Then profiled `sales_data_large.csv` directly rather than trusting its column names.

### What was learned

- **The dataset is synthetic and three of its apparent keys and measures do not hold.**
  All 100 `ProductID` values appear under more than one `ProductCategory`. 258 of 631
  `CustomerID` values carry conflicting age, gender or location. `SalesRevenue` is
  uncorrelated with `QuantitySold` at r = -0.06. Consequence: per-product drill-downs,
  customer-level and churn views, and any per-unit or margin metric are all unsupportable.
  A session that followed the playbook mechanically would have built all three before
  noticing, because every one of those columns looks legitimate from its name alone.
- **Profiling beat reading.** None of the three traps are visible in the header row or in
  the first several rows of the file. They only appear when consistency is checked across
  the whole dataset.
- **The playbook's own gates are stricter than they first read.** The Scope Brief approval
  is described as not optional at any scale, and the live-refresh checkpoint is explicitly
  graded on demonstrating a timed update, not on asserting one.

### What failed or was avoided

- No failures to report. Nothing was built, so nothing broke.
- **Avoided:** proposing a dashboard architecture before Stage 1 had run. The playbook
  gates that, and the dataset traps found later in the session would have invalidated an
  early KPI proposal anyway.

### Cost

No paid generation, no API spend. All work was local file reads and a Python profiling
pass over a 1,000-row CSV.

### Environment notes

- This folder is **not a git repository**. Verified, not assumed. There was no commit step
  at session end.
- An OpenAI Codex config and a Gemini CLI config both exist on this machine. An `/import`
  was offered to the user and not yet run.
- The MCP server `plugin:cps-core:gbrain` failed to connect this session (connection
  closed). It was not needed for this work.

### Handoff

Open the folder, read `PROJECT_MEMORY.md` then `PROGRESS.md`. The next concrete task is
Stage 1 cleaning on `sales_data_large.csv`, followed by Stage 3 insights including the
concentration check. Do not draft a Dashboard Scope Brief before Stage 3 produces numbers,
and do not begin any build before that brief is explicitly approved by the user. Five open
decisions are listed at the bottom of `PROGRESS.md`; the audience question blocks the rest.
