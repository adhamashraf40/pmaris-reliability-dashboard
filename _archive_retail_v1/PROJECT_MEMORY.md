# PROJECT_MEMORY.md

Durable rules, decisions and hard-won findings for the AIB902 Sales Project.
Read this FIRST at the start of any session, before PROGRESS.md.

**Every entry carries its reason.** A rule without its reason gets dropped the first
time it is inconvenient. **Append, do not rewrite.** Remove an entry only when it is
proven wrong, and say so in SESSION_LOG.md when you do.

---

## Method rules

**The playbook is the spec, not background reading.**
`AIB902_Agentic_Analytics_Dashboard_Playbook.md` is self-contained and reproduces the
four classroom prompts and both reference builds in full.
*Why:* it was written so nothing else needs opening. Inventing an approach beside it
produces work that cannot be graded against the course.

**Stage order is load-bearing. Never skip ahead to the build.**
Stages: 0 intake, 1 cleaning, 2 modeling, 3 insights, 4 scoping, then build.
*Why:* each stage's output is the next stage's input. A dashboard built before Stage 3
is a guess about which KPIs matter, and the scoping interview then has nothing to
interview about.

**The Dashboard Scope Brief must be explicitly approved before any build starts.**
*Why:* this is the playbook's own gate (§5.6) and it is stated as not optional at any
scale. Building first inverts the whole point of the exercise.

**Live Refresh Verification is demonstrated, never asserted.**
Edit the source file, save, time the on-screen update. Target under one second; the
playbook's worked example measured about 300ms.
*Why:* checkpoint D3 is graded on the demonstration. "It should work" is not a result.

**State a limit plainly rather than forcing a view the data cannot carry.**
*Why:* the playbook treats an honest "this dataset cannot support that" as a finding
worth surfacing to a stakeholder, not a gap to paper over.

---

## Architecture rules

**No framework, no build step, no CDN, no charting library.**
Watcher is Python standard library only. Dashboard is self-contained HTML with plain
CSS/SVG.
*Why:* §6.4 states it explicitly, and the playbook instructs pushing back if Streamlit,
React, or a hosted BI tool is proposed. It matches the course's guided-operator promise,
the student directs the build rather than hand-configuring a stack.

**The JSON shape returned by `build_snapshot()` is the contract between watcher and page.**
*Why:* the watcher and the dashboard are deliberately two independent, restartable
processes. They agree on nothing except that shape. Change one side, change both.

**The watcher must never crash on a bad read.**
File mid-save or a malformed row means skip the cycle and keep polling.
*Why:* the source file is expected to be edited live during the verification checkpoint.
A watcher that dies on a half-written save fails the demonstration it exists to support.

**Joins, if ever needed, happen once at Stage 2, never inside a refresh loop.**
*Why:* the refresh loop runs roughly three times a second. Work placed there is repeated
forever for no gain.

**Multi-page means several linked self-contained HTML files sharing one nav, one
`live_data.json`, and one watcher.**
*Why:* §8. It stays inside the zero-framework promise while giving a stakeholder the
several distinct views they actually experience as a dashboard.

**Reuse §7.1's exact CSS custom properties and `.kpi` / `.panel` / `.bar-row` /
`.viz-tooltip` classes on every page.**
*Why:* consistency across pages is itself what reads as professional. A second style
invented for page two undoes it.

---

## Dataset findings, MEASURED from `sales_data_large.csv`

Profiled 2026-09-19 directly from the file, 1,000 rows, 9 columns, zero missing cells.

**Classified Path A:** single flat CSV with a transaction-level date column.
*Why it matters:* routes Stage 2 to naming-only modeling, no join step.

**`ProductID` is not a product key. All 100 IDs appear under more than one category.**
Use `ProductCategory` (5 values) as the product dimension.
*Why:* a per-product drill-down or any join treating `ProductID` as stable would produce
confident nonsense. This is a synthetic-data artifact.

**`CustomerID` is not a customer key. 258 of 631 IDs carry conflicting age, gender or
location.**
Customer-level aggregation, churn, and repeat-purchase views are not supportable.
*Why:* same artifact. Declare the limit at Stage 3 rather than shipping a meaningless panel.

**`SalesRevenue` is uncorrelated with `QuantitySold` (r = -0.06).**
Revenue per unit, average selling price and margin-style derived metrics are meaningless.
*Why:* revenue was clearly generated independently of quantity. Any ratio built from the
two measures describes the generator, not a business.

**Usable dimensions:** `SalesDate` (2024-01-01 to 2024-12-31, 345 distinct dates),
`ProductCategory` (5), `CustomerLocation` (10 US cities), `CustomerGender` (2),
`CustomerAge` (52 distinct, bucket it before using).
**Usable measures:** `SalesRevenue` (total 2,561,723), `QuantitySold`.

---

## Operating preferences

**Work through Bash for file reads, searches and edits while auto mode is active.**
*Why:* standing instruction for this session's mode.

**This folder is not a git repository.**
*Why:* checked 2026-09-19. Do not assume a commit step exists at session end. Verify with
`git rev-parse --git-dir` before offering to commit.

**The three root files travel with the folder; anything in `~/.claude/` does not.**
*Why:* a naive copy of this folder to another machine must still be resumable.

---

## Added Session 2 — 2026-09-19

**The dataset contains no measurable signal. This is the project's central fact.**
Revenue is statistically indistinguishable from uniform random noise on every available
dimension. Chi-square against uniform passes for category, city and gender. The best-to-worst
city gap is reproduced by chance in 35% of 20,000 permutation simulations. The monthly trend
is +0.46% of an average month. The revenue values themselves match a uniform random draw.
*Why it matters:* no "where should we focus" dashboard is possible, because nothing stands
out from anything else. Any panel that ranks cities or categories is ranking noise, and a
reader will act on that ranking as if it were real.

**Never report a difference before testing whether chance explains it.**
Every apparent gap in this dataset survived the eye and died under a significance test.
*Why:* the top city looked 43% ahead of the bottom one, which reads as a finding. It is not.
Reporting it would have been the single most damaging thing this project could ship.

**Stage 1 cleaning passed with zero defects, and that is a trap, not a reassurance.**
Zero blanks, zero duplicates, zero type errors, zero outliers, zero near-constant columns,
date continuity intact with a longest gap of one day.
*Why:* a clean bill of health from the standard checklist is exactly why the real problems
would survive an ordinary review. Cleanliness is not fitness.

**Profit and margin are not computable. There is no cost column.**
*Why:* it is a structural absence, not a broken column. Say so rather than substituting a
revenue proxy and labelling it margin.

**The natural time grain is monthly, not daily.**
1,000 rows over 366 days is 2.7 per day.
*Why:* a daily trend line on this data is noise rendered as a chart.

**`Sales_Data_Quality_Assessment.pdf` is the client-facing record of all of the above.**
Regenerate it from `make_report.py` rather than editing the PDF.
*Why:* the user asked for the traps preserved as a PDF to send to the company later. The
numbers in it must stay traceable to the analysis that produced them.

---

## Added Session 3 — 2026-09-19

**Seven independent analytical angles were run. None found a decision.**
Two-way interactions (worst p=0.15, permutation p=0.18 on the category-by-city
matrix), bootstrap confidence intervals, Gini concentration, Benford's law,
temporal structure, power analysis, anomaly scan.
*Why it matters:* the question "did we look hard enough?" is now closed. Do not
re-run these hoping for a different answer, and do not let anyone propose a new
slice as though the dataset simply has not been cut the right way yet.

**Benford's law is the forensic proof.** Leading digits reject Benford at
chi-square 442 on 8 degrees of freedom, p = 2e-90, and instead match a flat random
draw between 101 and 4,995 at p = 0.85.
*Why:* this moves the claim from "looks synthetic" to "is demonstrably generated",
which is what makes the client report defensible rather than an opinion.

**Bootstrap intervals are the most persuasive single artifact.** Every city's 95%
interval overlaps every other city's, and Dallas is top in only 46% of 4,000
resamples. Every city appears at every rank from 1 to 10.
*Why:* a stakeholder who dismisses a p-value will still understand a picture of
ten overlapping intervals. Lead with it when challenged.

**The power analysis is the only genuinely actionable output.** Rows needed for
80% power to detect a lift on one city: 1,000 rows for 50%, 3,000 for 30%,
6,000 for 20%, 25,000 for 10%. Current power to detect a 20% lift is 21%.
*Why:* it converts "your data cannot answer this" into a specification for the
export that could. Always pair the bad news with this table.

**I reported a false signal once and caught it.** An early revenue-weighted
interaction test used a rescaled chi-square, which is not a valid test statistic,
and produced p=0.023 on category by city. A proper 20,000-shuffle permutation test
gave p=0.18.
*Why:* a chi-square statistic computed on summed revenue is not chi-square
distributed. When a test statistic is not standard, get the p-value by permutation
rather than by looking up a table. The corrected script now says so in its output.

**Project structure, set this session:**
`00_Method/` the playbook · `01_Data/` the CSV · `02_Analysis/` the scripts ·
`03_Dashboard/` the live dashboard · `04_Deliverables/` the PDF and its generator.
The four state files stay at the ROOT and must not be moved.
*Why:* the session skills read `PROJECT_MEMORY.md`, `PROGRESS.md` and
`SESSION_LOG.md` from the project root. Moving them breaks session start and end.

**Scripts resolve paths from `__file__`, never from the working directory.**
*Why:* the dashboard must be served from `03_Dashboard/` while the data lives in
`01_Data/`. Relying on `cd` would break the moment a script is run from elsewhere.

**The dashboard's honesty is the product, not a disclaimer on it.**
Every page states the no-signal caveat, and `quality.html` is a designed page
rather than an apology note.
*Why:* a beautiful dashboard over meaningless rankings is worse than no dashboard.
A reader will act on a ranking they see, whatever the footnote says.

**Never state a statistical verdict that no test in the contract backs.**
Two pages claimed "tests as no signal" for age bands and weekdays before either
test existed. Both were true once measured, which made the error invisible.
*Why:* a claim that happens to be right is still fabricated if nothing computed it.
If a page wants to say "no signal", the test must exist in `live_data.json` and the
page must cite its p-value. Add the test rather than deleting the sentence.

**Study constants and live figures must be visibly different things.**
The bootstrap intervals were measured on the 1,000-row file and correctly do not
move with the data, but they sat beside live tiles with nothing marking the
difference. The fix was a stale-study banner that fires when `row_count` no longer
matches the file the study ran on.
*Why:* a reader cannot tell which numbers on a live page are live. Anything
measured once must say when it stopped describing the data.

**Visual inspection proves a page renders. It does not prove the page is honest.**
I checked all five pages in a browser, found them correct, and said so. Adversarial
review then found fabricated claims, a factual error contradicting another page,
and four instances of banned ranking phrasing.
*Why:* looking at a page confirms the charts draw. Only re-deriving the numbers and
re-reading the copy against the evidence confirms the claims. Budget for both.

**`pkill` does nothing on this Windows shell, silently.**
Two stale watcher processes survived a `pkill -f`, kept pre-edit code in memory, and
overwrote `live_data.json` with an outdated snapshot after a newer one was written.
*Why:* use `Get-CimInstance Win32_Process -Filter "Name='python.exe'"` to list with
command lines, confirm the processes are yours, then `Stop-Process -Force`. A file
that keeps reverting means something is still running.

**When the deliverables diverge, the PDF is the one that goes stale.**
The dashboard was corrected first; the PDF still carried the same "366 days" error
and was missing the two new tests until the user asked whether it had been updated.
*Why:* the dashboard is regenerated from `live_data.json` on every change, while the
PDF only changes when `make_report.py` is run. After any finding changes, rebuild the
PDF and diff its text before calling the work done.

---

## Added Session 4 — 2026-09-19

**The comprehensive page cross-filters client-side from a row-level feed.**
`watcher.py` publishes `raw` alongside the aggregates: field names, lookup lists for
the categoricals, and rows with categoricals index-encoded. About 36 KB for 1,000
rows. `app.js` holds the filter sets and `filterRows` applies them.
*Why:* it gives Power BI style interaction with no server, no framework and no build
step, which is the constraint the playbook imposes. It only works because the dataset
is small; check the size before shipping the whole file for a larger source.

**A `getElementById(...).textContent` on an element that a later `innerHTML`
assignment destroys will throw on every draw after the first.**
The filter summary wrote to `#fs-count`, then replaced its own parent's `innerHTML`,
deleting that id. The first render worked. Every later one threw silently after the
slicers had already repainted, so the chips toggled while nothing else moved.
*Why:* it presents as "the feature does not work" rather than as an error, because
the exception lands mid-render with the DOM half updated. When a page partly updates,
suspect a thrown exception in render before suspecting the logic.

**Debug by instrumenting the real call, not by reasoning about the code.**
I formed three wrong hypotheses about the filter bug. Wrapping `LDD.filterRows` to
record what it actually received settled it in one step: the filters were correct, so
the fault lay after that call.
*Why:* the symptom pointed at the filter engine and the engine was fine. Bisecting
with a live probe beats reading harder.

**Negative margins on a full-bleed element cause horizontal page overflow.**
`.filterbar` carried `margin: 0 -22px` from when it sat inside a padded container.
Once it became a top-level element that pushed the page sideways.
*Why:* the page must never scroll horizontally. `html, body { overflow-x: hidden }`
is now a backstop, but the real fix was removing the margin.

**Fit scatter axes to the data range, not to zero.**
Ten cities with similar values crushed into one corner on zero-based axes.
*Why:* the question a scatter answers is whether points fall on a line, not how large
they are against zero. Zero-basing is right for bars, wrong here.

---

## Added Session 5 — 2026-09-19

**One CONFIG block, and every consumer iterates a published dimension list.**
The watcher names the dataset once; the feed publishes `dimensions`, and
`by_dimension`, `lookups` and `concentration` are all keyed by dimension name.
*Why:* it is the difference between a bespoke dashboard and a template. Adding a
dimension to the CONFIG adds a slicer, a panel and a concentration row with no code
change. A page that writes `d.by_city` is welded to one dataset forever.

**Headline, per-page insight and limitations text stay hand-authored.**
*Why:* they are editorial judgements about a specific business question. Generated
mechanically, a dashboard ends up labelling a panel "Revenue by City" where it should
be telling the reader what to conclude.

**Give parallel agents explicit, disjoint file ownership.**
Every agent was told the exact files it owned and that it must touch nothing else.
*Why:* the previous session lost a cycle when two agents edited one file and clobbered
each other. The fix is ownership stated in the prompt, not coordination between agents.

**Write the shared contract before fanning out.**
*Why:* five agents built against a fixed feed shape instead of negotiating one. This is
the same rule that made the five dashboard pages look like one product.

**The reusable template lives at `C:/Users/hp/Downloads/Analytics_Project_Template/`.**
*Why:* future analytics projects start from it rather than from this engagement's
folder, which carries findings specific to one dataset.
