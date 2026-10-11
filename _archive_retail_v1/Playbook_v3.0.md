# AIB902 Agentic Analytics & Dashboard Playbook

**Course:** AIB902, Data Analytics for Decision Making
**Anchors:** Lecture 7 ("Agentic Analytics: AI-Directed Pipelines and Live Dashboards")
**Scope:** a general, dataset-agnostic method for taking ANY input dataset (one flat file, a
multi-table star schema, a time series, a survey export, an event log, or something that
doesn't cleanly fit any of those) through cleaning, modeling, initial insights, significance
testing, a scoping interview, and a working, professionally designed Live Decision Dashboard
(LDD). Part II (Sections 10 to 18) adds the significance gate, the deep-analysis battery, the
power-analysis deliverable, the editorial rules for weak data, the cross-filtered architecture,
the pre-delivery verification checklist, and the client-report architecture.
**Status:** Version 3.0, For Review
**Self-contained:** this single document is everything needed to run the pipeline. The four
Lecture 7 template prompts and the two reference-architecture code samples are reproduced in
full in the appendices; nothing else in the course folder needs to be opened to use this
Playbook.
**Purpose:** instructor-facing teaching material for walking MBA students through building
their own interactive, live-source dashboard end to end, the Lecture 7 capstone.

## Summary

The teaching sequence never changes, no matter what dataset a student brings: fully prepare
the dataset (clean it, then model it), analyze it to generate initial insights, let those
insights inform which KPIs to propose to a stakeholder, and only then build the dashboard
around the approved KPIs. Sections 1 to 4 below are that preparation-and-analysis phase;
Section 5 is the build, and it targets a genuinely polished result: a multi-page interactive
dashboard, modern in design and coloring, that tells a story rather than just displaying
numbers, not a single bare chart. Section 6 reproduces the four classroom prompts in full;
Section 7 reproduces the two reference-architecture code samples in full. Every WWI figure
quoted below is MEASURED directly from the real dataset already in this course
(`Reference_Material/WWI_Dataset/`, 5 tables, 26,397 sale lines, 2013 to 2016), computed while
preparing this Playbook using the same steps a student runs.

**Read this alongside:** `Course_Design_Playbook.md` (05_Deliverables_Final/ root), the same
"generic method, worked example is one configuration of it" discipline this document follows.

---

## 0. How to use this document

This Playbook is the method, and it is now the single place to find it. Section 6 reproduces
the four Lecture 7 template prompts verbatim (a student still pastes those prompts into
Claude one at a time); Section 7 reproduces the two reference dashboard builds in full. This
document adds three things the four prompts deliberately leave out of scope for a single
classroom activity:

1. **Dynamic branching per dataset shape.** The prompts ask Claude to "look at my data and
   tell me what's there," which is correct but terse. This Playbook spells out what Claude
   should actually be checking for and doing differently depending on what kind of dataset
   shows up (Section 2).
2. **A comprehensive interview-question bank** (Section 5). Prompt 3 (Section 6.3) has 4
   fixed questions, the right number for one classroom activity. This Playbook's bank is
   deliberately larger and organized by situation, for an instructor adapting Lecture 7 to a
   case dataset, or building the next elective's version of this pipeline.
3. **A fully worked, real-data run-through** (the shaded WWI boxes throughout), proof that
   every stage below actually executes end to end on genuinely messy multi-table business
   data, not just on the tidy toy dataset in the reference build (Section 7.1).

Every number, tool choice, and threshold below that comes from WWI is a worked example, not a
universal constant, exactly the discipline `Course_Design_Playbook.md` established. Swap it
for whatever a student's own dataset actually says.

**Version 3.0 adds Part II (Sections 10 to 18).** Sections 1 to 9 are unchanged. Part II
closes a gap the original method did not cover: Stages 0 to 5 will carry any dataset to a
polished dashboard without ever asking whether the differences being charted are real. On a
dataset with genuine structure that never shows. On one without it, the method produces a
confident and completely misleading product. Part II adds the significance gate
(Section 10), the deep-analysis battery (Section 11), the power-analysis deliverable
(Section 12), the editorial rules for weak data (Section 13), the cross-filtered
architecture (Section 14), and the verification checklist (Section 16).

---

## 1. Stage 0, Dataset Intake & Shape Detection

Before cleaning anything, classify what has actually been handed over. The right move at
every later stage depends on this classification: don't skip it, and don't assume it's a flat
CSV just because that's what the classroom example uses.

**Check, in order:**

| Check | What to look for | Why it changes the plan |
|---|---|---|
| **File format** | `.csv`, `.xlsx`/`.xls`, `.json`, a database export, an API response, a folder of screenshots or PDFs of tables | Determines the load method (`pandas.read_csv`, `read_excel`, `read_json`, a connector) before anything else can happen |
| **Table count** | One file, or several files that reference each other by ID | One flat table needs only cleaning; 2 or more tables need a modeling/join step before anything else is possible |
| **Grain** | What does one row represent: a transaction, a daily/monthly summary, a customer, a survey respondent, a sensor reading? | Wrong grain silently breaks every aggregate downstream, e.g. treating pre-aggregated monthly rows as if they were daily |
| **Time dimension** | Is there a date/timestamp column? Is it transaction-level, or already bucketed? | No time column means no trend panel is possible; that's a legitimate answer, not a gap to force |
| **Categorical dimensions** | How many columns look like "slice by this" (region, product, segment, department)? How many distinct values does each actually have? | A column with 1 distinct value (like WWI's `Sales Territory`, see the box below) is not a usable dimension no matter how promising its name sounds |
| **Numeric measures** | Which columns are things you'd sum, average, or count? | These become the candidate KPIs in Stage 3 |
| **Scale** | Row count: dozens, thousands, millions? | Changes whether the watcher pattern in Stage 5 can re-scan the whole file every poll, or needs incremental/indexed reads |
| **Freshness** | A one-time export, a periodic export, or a genuinely live source (DB connection, API)? | Determines whether "live" dashboard refresh is even a meaningful ask (Section 4, Q-REFRESH) |

Source: Playbook methodology, not derived from any one dataset.

**Dataset-shape decision tree**, used to route to the right sub-path in Stages 2 to 3:

```
Is there more than one input file/table?
  NO  -> single flat table
          Does it have a date/timestamp column?
            YES -> flat time-series/transactional table   (Path A)
            NO  -> flat cross-sectional table, e.g. a survey or roster   (Path B)
  YES -> multiple tables
          Do the tables share ID columns that look like a fact/dimension pattern
          (one big table of events plus several small lookup tables)?
            YES -> star/snowflake schema   (Path C, this is WWI)
            NO  -> unrelated or loosely-related tables; clarify with the source
                   before proceeding, don't force a join that isn't real   (Path D)
```

> **WWI worked example, Stage 0 (MEASURED).**
> Format: 5 files, 4 CSV and 1 XLSX. Table count: 6 conceptual tables (1 fact, 5 dimensions,
> though only 4 dimensions are actually joined to the fact in practice). Grain: one row per
> sale line item, not per invoice (`WWI Invoice ID` repeats across multiple `Sale Key` rows;
> 26,397 lines resolve to 8,188 distinct invoices). Time dimension: `Invoice Date Key`,
> transaction-level, daily granularity, 2013-01-01 to 2016-05-31. Categorical dimensions
> found: Stock Item (672 distinct), Customer (402 distinct), Buying Group (2 real values plus
> nulls), City (153 distinct, used), State Province (6 distinct, used), and Sales Territory
> (1 distinct value across the entire fact table, not usable). Classified as Path C, star
> schema, routed to Stage 2's join method.

---

## 2. Stage 1, Data Cleaning (dynamic checklist)

This generalizes Prompt 1 of 4 (Section 6.1). Run the same checks regardless of dataset
shape; which specific issues turn up will differ.

**Universal checks, always run these:**

1. **Row/column count and types.** Does every column's declared type match what it actually
   contains? A "numeric" column stored as text is the single most common silent failure.
2. **Header integrity.** Is the first row actually the header, or is there a title/metadata
   row above it? Multi-table sources are the most common place this hides, because each
   export may have been generated by a different process.
3. **Missing values.** Which columns, how many, what percentage of rows. For each: is this
   genuinely unknown (flag it) or structurally absent, e.g. a delivery date on an order that
   hasn't shipped yet (also flag it, don't impute a fake date)?
4. **Duplicate rows.** Exact duplicates first, drop with a stated count, then near-duplicates
   (same business event, different formatting), which need a judgment call, not an automated
   drop.
5. **Outliers.** Values implausible for what the column represents. State why each one is
   implausible in business terms, not just "3 standard deviations out."
6. **Constant or near-constant columns.** Any column where one value covers 95% or more of
   rows carries almost no discriminating power as a dashboard dimension, even if its name
   sounds useful. Flag it now so Stage 4's scoping conversation doesn't promise a slice the
   data can't support.

**Shape-specific additions:**

- **Path C only, referential integrity.** For every foreign key in the fact table, confirm
  every value has a matching row in its dimension table (0 orphans). An orphan key means a
  sale, customer, or product that the dashboard will silently drop or crash on later; catch
  it here, not in Stage 5.
- **Path A only, date continuity.** Are there gaps in the date range not explained by the
  business calendar, e.g. missing an entire month rather than just weekends? A gap can mean
  lost data, not just a quiet period.
- **Path B only, response validity.** For Likert/categorical responses, are all values within
  the declared valid set? For free-text fields: is there anything resembling PII that needs
  redaction before this goes near a dashboard anyone else will see?
- **Path D only.** Confirm with the data's source what the intended relationship actually is
  before writing any join logic; document the assumption if no one is available to ask.

**Never silently fix.** For every issue found, propose the specific fix and the one-sentence
reason, present the full list, and wait for approval before touching the data. This is
Prompt 1's own rule and it applies at every scale, not just the classroom activity.

> **WWI worked example, Stage 1 cleaning report (MEASURED, 0 rows dropped):**
> - Header anomaly (check 2): `DimStockItem.csv` and `DimCustomer.csv` both ship with a title
>   row above the real header. Load with `header=1`, not the default `header=0`, or every
>   column name comes back as `Unnamed: N`.
> - Missing values (check 3): 13 of 26,397 rows (0.05%) have no `Delivery Date Key`; these are
>   orders not yet delivered as of the export date. Flagged as `Delivered = False`, not
>   imputed with a fake date.
> - Outliers (check 5): 566 rows (2.1%) have negative `Profit`. Investigated in business
>   terms: these are real loss-leader/clearance-priced lines, not data errors. Flagged as
>   `Loss_Leader_Sale = True` and kept in; removing them would overstate the true margin.
> - Constant columns (check 6): `DimCustomer.Category` is "Novelty Shop" for all 402
>   customers, dropped, zero discriminating power. `DimCity.Sales Territory` is "Far West"
>   for 100% of the cities the fact table actually touches, dropped for the same reason. This
>   is the Path C referential-integrity check surfacing a real scoping fact, not a data error:
>   the real geographic footprint is 6 states, not multiple territories.
> - Referential integrity (Path C check): 0 orphaned City, Customer, Stock Item, or
>   Salesperson keys in `FactSale.csv`; all 4 joins used in Stage 2 are clean.
> - Duplicates: 0 exact duplicate rows in `FactSale.csv`; 0 duplicate `Sale Key` values.

---

## 3. Stage 2, Data Modeling (dynamic by path)

**Path A / B, already one flat table.** Modeling is mostly about naming: state the grain
explicitly ("one row = one X"), identify which columns are dimensions (slice by) versus
measures (aggregate), and stop. No join step needed.

**Path C, star/snowflake schema, the join method:**

1. Identify the fact table (the one with foreign keys pointing outward and the numeric
   measures that actually matter) and every dimension table it references.
2. For each dimension, keep only the columns that will actually be used downstream (name and
   label fields, the segment fields that survived Stage 1's constant-column check). Don't
   drag every audit/metadata column through the join.
3. Left-join the fact table to each dimension on its key, one dimension at a time. Confirm
   row count is unchanged after each join; a row-count increase means a dimension table has
   duplicate keys causing fan-out. Stop and fix the dimension, don't proceed.
4. The result is one flat, denormalized table at the fact's original grain. This is what
   feeds Stage 3 and what the Stage 5 watcher will poll. The joins happen once, here, never
   repeatedly inside a dashboard refresh loop.
5. Persist this as its own build script, not a notebook cell that gets lost. If the source
   schema changes later, re-run the script; never hand-edit the flat output.

**Path D.** Don't build a join. Either get the real relationship from the source, or scope
the dashboard to whichever single table is actually well understood, and treat the rest as
future work.

> **WWI worked example, Stage 2 (MEASURED):** Grain confirmed as one row equals one sale line
> item, the fact's own grain, unchanged. Joined `FactSale` to `DimStockItem` (Stock Item name,
> Brand), to `DimCustomer` (Customer name, Buying Group), to `DimCity` (City, State Province).
> Row count before and after the joins: 26,397 to 26,397, 0 fan-out; all three joins are clean
> 1:1 lookups. Final dimensions available for slicing: Month, Product, Customer, Buying
> Group, City, State Province. Measures: Revenue, Profit, Quantity.

---

## 4. Stage 3, Generate Initial Insights (dynamic by what's available)

Don't run every possible statistic blindly; run the ones Stage 0's classification actually
supports, and say plainly when something isn't possible.

| If Stage 0 found... | Then compute... |
|---|---|
| A time column | A trend over the natural time grain (don't force daily if the business logic is monthly): total, and if a clear top segment exists, top-segment-over-time |
| 2 or more meaningful categorical dimensions | Top-N by each dimension for the primary measure, starting with N of 5 to 10, not an exhaustive list |
| A measure with a natural good/bad direction (revenue, profit, cost, defects) | Overall total, and a rate or ratio if two related measures exist, e.g. profit margin equals profit divided by revenue |
| Multiple entities of the same type (customers, products, regions) | A concentration check: what percentage of the total measure comes from the top 10% of entities? This is the single most decision-relevant number in most business datasets, and it is almost always skipped |
| A constant or near-constant dimension flagged in Stage 1 | Nothing; state explicitly that this dimension can't be sliced by, so Stage 4 doesn't waste a scoping question on it |

Source: Playbook methodology, not derived from any one dataset.

> **WWI worked example, Stage 3 (MEASURED, computed from the modeled flat table):**
> Total revenue $19,879,593; total profit $9,923,892; overall margin 49.9%; 8,188 distinct
> orders across 41 months. Top product by revenue: Air cushion machine (Blue) at $1,198,269;
> the top 5 products are all packaging materials, not the toy inventory the customer names
> ("Tailspin Toys," "Wingtip Toys") might suggest. Revenue by Buying Group: Tailspin Toys
> $8.06M, Wingtip Toys $5.05M, Unspecified $6.77M; the "Unspecified" bucket (customers with no
> Buying Group on file) is itself a finding worth surfacing to a stakeholder, not silently
> hidden. Revenue by State: California leads at $8.83M, then Washington $4.23M, Alaska $3.00M,
> Oregon $2.25M, Nevada $1.25M, Hawaii $0.32M; six states total, matching Stage 0/1's finding
> that `Sales Territory` is constant and unusable.

**Do not go straight to Stage 4 from here.** Everything above is a ranking, and a ranking is
a claim. Run **Stage 3b, Significance Testing (Section 10)** first, and carry its register
into the scoping conversation. Only differences that survived a test may be proposed as KPIs
or described as findings.

---

## 5. Stage 4, Dashboard Scoping Interview (comprehensive question bank)

> **Prerequisite:** Stage 3b (Section 10) has produced a test register. Propose KPIs only
> from differences that survived. A difference that failed its test may still be displayed,
> but it may never be called a finding or used to justify a recommendation.

This generalizes Prompt 3 of 4 (Section 6.3). That prompt's 4 questions (audience, primary
KPIs, refresh need, storytelling angle) are the right minimum for one classroom activity and
should always be asked. This bank adds the situational questions an instructor or a real
engagement needs, organized so only the branch that actually applies gets asked. Don't ask
about a dimension or capability Stage 0 to 3's profiling has already ruled out.

### 5.1 Universal questions, ask every time, any dataset

- **Q-AUDIENCE:** Who specifically is this for? A named role, "the regional sales manager,"
  not a category like "management."
- **Q-KPI:** What are the 3 to 5 numbers this person needs to make their decision? Push back
  past 5; more than that is a spreadsheet, not a dashboard.
- **Q-DECISION:** What is the one decision or action this dashboard should drive? Not "show
  all the data." This becomes the headline the Overview page (Section 5.6) is built around.
- **Q-REFRESH:** Does this genuinely need to update live? What decision would be wrong or
  late with only a daily refresh instead? "I don't actually need live" is a fine answer.
- **Q-DISTRIBUTION:** Where will this actually be viewed: a shared screen, a personal laptop,
  printed for a meeting? This affects layout choices Stage 5 needs to know before building.
- **Q-CADENCE:** Is this a one-time analysis, or something the same person will open
  repeatedly? A one-time answer might not need a dashboard at all; a report may be cheaper.

### 5.2 Conditional on dataset shape, from Stage 0's classification

- **If Path C (star/snowflake schema):** Which of the dimensions that survived Stage 1's
  constant-column check does the audience actually want to slice by? Explicitly confirm which
  promising-sounding dimension names got dropped and why, e.g. "there's no territory
  breakdown possible, every record here is in one territory."
- **If Path A (time-series):** What time grain matches how this person actually makes
  decisions: daily, weekly, monthly? Do they need forecasting or projection, or is a
  historical trend enough? Is there a known seasonal pattern they'd want called out
  automatically?
- **If Path B (cross-sectional/survey):** Is this a one-time snapshot, or will new responses
  keep arriving? If PII/free-text fields exist, who is allowed to see the raw responses versus
  only the aggregated dashboard?
- **If Path D (unclear table relationships):** Has the real relationship between the tables
  been confirmed with the source since Stage 2? Don't scope a dashboard around a join that's
  still a guess.
- **If the dataset is small (hundreds of rows) or has a short/frozen history:** Does the
  audience understand the data's actual boundaries, e.g. "this covers 2013 to 2016, not up to
  the present"? Should the dashboard say so on screen, or is that assumed knowledge?
- **If the dataset is large (hundreds of thousands of rows or more):** Does "live" refresh
  need to re-scan everything, or would a pre-aggregated summary table refresh faster and still
  serve the decision? This ties back to Stage 5's scale note.

### 5.3 Conditional on what Stage 1 found

- **If negative/unusual values were flagged, not removed:** Should the dashboard show these
  separately, e.g. a "loss-leader lines" counter, or fold them into the totals silently? Most
  stakeholders want to know they exist even if the answer is "fold them in."
- **If rows were flagged as incomplete (missing dates, missing IDs):** Should the dashboard
  count them in totals, exclude them, or show a separate "incomplete records" tile? There is
  no universally correct answer; this is a business decision, not a technical one.
- **If a dimension was dropped for being constant:** Confirm the audience doesn't already
  assume that slice exists in some other system they're used to. A constant field in this
  export doesn't always mean the business has no variation there, only that this export
  doesn't carry it.

### 5.4 Conditional on business domain, ask if the audience's role suggests one of these

- **Sales/revenue dashboards:** Is profit margin as important as revenue, or is this a
  top-line-only view? Is there a target or budget number to compare against, or only actuals?
- **Operations/inventory dashboards:** Is there a threshold that should trigger an alert
  color, e.g. stock below reorder point, or is this purely descriptive with no thresholds?
- **Customer/segment dashboards:** Is customer-level detail needed, or only aggregated
  segments for privacy or scale reasons? Is churn/retention in scope, and does the data
  actually support measuring it? A dataset can look like it supports churn analysis and not
  actually have enough history or enough inactive accounts to measure it against.
- **HR/people dashboards:** What level of individual identifiability is appropriate for the
  intended audience? Aggregate-only versus named-individual views often need different access
  rules, not just different chart types.
- **Financial/compliance-adjacent dashboards:** Does anyone need to audit how a number was
  calculated later? If so, the build in Stage 5 needs to log its aggregation logic somewhere
  retrievable, not just render a number.

### 5.5 Technical/governance questions, ask once, regardless of domain

- **Q-ACCESS:** Who else besides the named audience will see this? Does that change what can
  be shown (raw customer names, exact figures) versus what should be masked or aggregated?
- **Q-SOURCE-STABILITY:** Will the underlying source file or table's structure (column names,
  file location) stay stable, or is it likely to change? An unstable source means Stage 5's
  build should fail loudly on a missing column, not silently show zeros.
- **Q-OWNERSHIP:** Who maintains this after the build is handed over, the same person who
  scoped it, or someone else? If someone else, the build script's comments from Stage 2 need
  to be readable by that person, not just by whoever wrote them.

### 5.6 The Dashboard Scope Brief, now includes the story arc

Once scoping answers are collected, write a one-page Dashboard Scope Brief: audience, the
chosen KPIs with a chart type per KPI, the refresh justification, the one decision this
drives, and any scope limits Stages 0 to 3 already surfaced. Get explicit approval before
Stage 5 starts building; this is Prompt 3's own gate and it is not optional at any scale.

Because Stage 5's target is a multi-page, story-driven dashboard rather than one flat page,
the brief also names, in order:

1. **The headline.** One sentence, in plain business language, stating Q-DECISION's answer
   as if it were the dashboard's own opening line, in the shape "<action> on <the one or
   two segments that matter>: together they are <X>% of <measure>, and <the reason this
   is actionable>." A worked instance appears in the WWI box below. If Stage 3b
   (Section 10) found nothing significant, the headline must say so instead: a headline
   that names a leader the data cannot distinguish is the exact failure Section 13 exists
   to prevent.
2. **The page list.** An Overview page (always first) plus one drill-down page per dimension
   the audience actually confirmed wanting (Section 5.2), each with a one-line purpose, e.g.
   "Products: which items are worth reordering first."
3. **The through-line.** What should a reader notice by the time they've clicked through
   every page, in one sentence? This is what keeps the pages from feeling like an unrelated
   pile of charts.

> **WWI worked example, Stage 4, the brief that would result (MEASURED inputs, proposed
> scope):** Audience: the WWI regional sales director. KPIs: Total Revenue, Total Profit,
> Profit Margin percentage, Order Count, 4 KPIs, at the limit. Decision: which state to
> prioritize for the next sales push. Refresh: live is nice-to-have for a classroom demo, not
> load-bearing for a monthly sales review; daily would genuinely suffice in a real deployment.
> Scope limits disclosed up front: no territory-level view possible, since this export has a
> single territory; no churn view attempted, since the dataset's own customer count and time
> span don't support it (this echoes the AIB904 CFS's parallel finding on the same underlying
> WWI export). Segment by Buying Group, State, and Product, not Customer Category, which is
> constant and was dropped in Stage 1.
> Headline: "California and Washington are 66% of revenue on 41 months of data; the next push
> should test whether Oregon and Nevada are underserved or genuinely smaller markets."
> Pages: Overview (the 4 KPIs plus the monthly trend), Geography (revenue and profit by
> state), Products (top products by revenue, and which carry the thinnest margin), Customers
> (revenue by Buying Group, and the size of the Unspecified bucket). Through-line: revenue
> concentration, by state, by product, and by customer group, all point back to the same
> underlying question of where the next dollar of sales effort should go.

---

## 6. The Four Lecture 7 Template Prompts (reproduced in full)

These are the exact prompts a student pastes into Claude, one at a time, in order. They live
in this course's `Instructor_Toolkit/` and `Student_Toolkit/` folders as their own files;
they are reproduced here in full so this Playbook never requires opening another file.

### 6.1 Prompt 1 of 4, Data Cleaning

Used in Lecture 7, Part A (Activity 7.1). Run this in a new Claude Code (or Claude Desktop)
project, scoped to the student's own dataset for the rest of the pipeline. This is the first
thing to do with a new dataset, before any modeling or visualization; nothing downstream
should touch data this prompt hasn't already reviewed.

```
You are helping me clean a business dataset before I analyze it. The file is: <PASTE FILE PATH OR PASTE THE DATA>

Do the following, in order, and stop after step 3 to wait for my approval:

1. Load the file and tell me, in plain business language (no code shown unless I ask):
   - How many rows and columns
   - What each column appears to represent
   - Missing values: which columns, how many, what % of rows affected
   - Type errors: any column that looks numeric/date but is stored as text, or vice versa
   - Duplicate rows: how many, and a couple of examples
   - Outliers: any values that look implausible for what the column represents. Give specific
     examples, not just "some outliers exist."

2. For each issue you found, propose a specific fix (e.g. "drop 12 duplicate rows", "convert
   OrderDate from text to date", "impute missing Region with 'Unknown' rather than dropping
   the row because it's only 2% of rows"). Explain your reasoning for each proposed fix in one
   sentence.

3. Present this as a numbered list and STOP. Do not modify anything yet; wait for me to
   approve, reject, or adjust each item.

4. Once I approve, apply only the approved fixes and give me a short before/after summary
   (row count, columns affected, what changed).

Do not silently "fix" anything I haven't approved, even if it seems obviously correct.
```

What comes back: a cleaning report (the numbered list from step 2), followed only after a
response by the actual cleaned file and a before/after summary. Push back on at least one
proposed fix before approving; reviewing means actually reading each item, not just replying
"yes do all of it."

### 6.2 Prompt 2 of 4, Data Modeling & Advanced Analytics Technique Selection

Used in Lecture 7, Part B (Activity 7.2). Run this after Prompt 1 has been completed and
approved, in the same project. Once the data is clean, before touching any dashboard or
visual, this prompt's job is to decide what kind of analysis actually fits the data and the
business question, not to build anything yet.

```
My dataset is now clean (see the cleaning summary above). I want to decide how to model and
analyze it.

Business question: <STATE THE DECISION THIS ANALYSIS SHOULD SUPPORT, e.g. "which customer
segments are at risk of churning" or "which regions are under-performing their sales targets">

Do the following:

1. Propose a simple data model: what are the natural dimensions (categories to slice by) and
   measures (numbers to aggregate) in this dataset? What's the grain: what does one row
   represent?

2. Propose 2-3 candidate advanced analytics techniques that fit BOTH the data and my stated
   business question (for example: cohort analysis, RFM segmentation, anomaly detection,
   time-series forecasting, clustering; pick from whatever actually fits, don't default to
   the same technique every time). For each candidate, give me:
   - A one-paragraph plain-English description of what it does
   - Why it fits my specific business question, not a generic description of the technique
   - What decision it would help me make if the result comes back clearly

3. If my business question is too vague to match to a technique, ask me clarifying questions
   before proposing anything; don't guess.

4. Do not run or build anything yet. Wait for me to pick a technique (or ask you to recommend
   one) before proceeding.
```

What comes back: a short proposed data model, followed by 2-3 named techniques with
plain-English rationale, and a request from Claude to pick one before it does any actual
analysis. Before picking, be able to restate in one sentence what decision the chosen
technique's output will let you make; don't pick the most advanced-sounding option just
because it sounds impressive.

### 6.3 Prompt 3 of 4, Interactive Dashboard Scoping Conversation

Used in Lecture 7, Part C (Activity 7.3). Run this after Prompt 2, once a technique has
already been chosen. Before Claude builds anything, this prompt's entire purpose is to make
Claude ask questions first, the opposite failure mode of just saying "build me a dashboard"
and hoping it guesses right.

```
I've cleaned my data and chosen an analytics technique (see above). Now I want to scope a
dashboard, but before you generate anything, ask me questions first.

Ask me, one at a time or in a short structured batch, about:

1. Audience: who is this dashboard actually for? (a specific role, e.g. "the regional sales
   manager," not "management" in general)
2. Primary KPIs: what are the 3-5 numbers this person needs to see to make their decision?
   (push back if I name more than 5; a dashboard with 12 KPIs isn't a dashboard, it's a
   spreadsheet)
3. Refresh needs: does this genuinely need to update live, and why? What decision would be
   wrong or late if it only refreshed once a day instead?
4. Storytelling angle: what's the ONE decision or action this dashboard should drive? Not
   "show all the data," one decision.

Once you have my answers, write me a one-page Dashboard Scope Brief summarizing: audience,
the KPIs (with which chart type fits each), the refresh justification, and the storytelling
angle. Show me the brief and wait for my approval before building anything.
```

What comes back: a short back-and-forth (Claude asking the 4 questions above), ending in a
one-page Dashboard Scope Brief to approve before Part D's build step. Watch for these on your
own answers: don't let the KPI list creep past 5, name a specific role as the audience (not
"management" or "the business"), and if unable to say what decision would be wrong with a
daily refresh instead of live, that's a sign live refresh may not actually be needed, a fine
answer, not a failure.

### 6.4 Prompt 4 of 4, Build & Verify the Live Dashboard

Used in Lecture 7, Part D (Activity 7.4). Run this after Prompt 3, once there is an approved
Dashboard Scope Brief. Reference architecture: Section 7.1 (worked, runs as-is) and Section
7.2 (parameterized starting point). This is the step that actually produces the Live Decision
Dashboard.

```
Build me a live dashboard from my approved Dashboard Scope Brief (see above) and my modeled
dataset.

Use this exact architecture; don't substitute a framework or a hosted service:

1. A watcher script (Python, standard library only, no pandas/pip installs unless my source
   is Excel, in which case add an openpyxl read path) that:
   - Polls my source data file every ~0.3 seconds for a change in modification time
   - On change, recomputes whatever totals/groupings my KPIs need
   - Writes the result to a local live_data.json file
   - Never crashes on a bad read (e.g. the file mid-save); skip that cycle and keep polling

2. A self-contained set of HTML page(s) (no external CDN, no build step, no framework) that:
   - Fetch live_data.json every 1 second with cache-busting
   - Render the 3-5 KPIs as tiles, plus whatever chart(s) my scope brief calls for, using
     plain CSS/SVG (no charting library needed for a handful of KPIs and simple bar/trend
     visuals)
   - If my brief names more than one page (an Overview plus drill-downs), link them with a
     simple shared nav, and open the Overview page with the one-sentence headline from my
     brief, not a bare chart
   - Use a coherent modern palette (light and dark mode both handled), consistent typography,
     and hover detail on every chart, not default browser styling
   - Show a small "live" status indicator so I can tell at a glance whether it's actually
     polling

3. Tell me exactly how to run both pieces (which terminal commands, in what order).

4. Tell me how to do the Live Refresh Verification checkpoint: what to edit in my source
   file, and roughly how fast I should expect to see it change on screen (target: under 1
   second).

Build this now. I'll review what you produce and ask for changes before I consider it done.
```

What comes back: a watcher script, one or more dashboard HTML files, run instructions, and a
description of the verification test, matching the pattern in the reference architecture in
Section 7. If Claude proposes Streamlit, a Node/React stack, or a hosted BI tool instead of
the plain watcher-plus-self-contained-HTML pattern, push back and point it at Section 7.1;
that architecture is the one to insist on, not a substitute. For the graded checkpoint,
actually edit the source file and time the update; "it should work" isn't the same as
demonstrating it.

---

## 7. Reference Architecture (reproduced in full)

> **Section 14 extends this** to a multi-page, cross-filtered build with slicers, a shared
> runtime and a chart primitive library, still with no framework, no build step and no CDN.
> The architecture below remains the minimum viable version and still runs as written.

Both reference builds below live in this course's `Hands_On/` folder as their own runnable
files; they are reproduced here in full so the pattern, including the exact CSS and
JavaScript that gives it a modern, professional look, is on record in this one document.

### 7.1 Worked example, `Example_Live_Decision_Dashboard/`

This is the fully worked reference for Lecture 7, Part D (Activity 7.4). It shows the
complete pattern Claude should reproduce when a student runs the Dashboard-Build Prompt
Template against their own dataset. What's in the actual folder: `sample_sales.csv` (a tiny
30-row sample, 3 regions, 2 products, the "before" file), `watcher.py` (below), and
`dashboard.html` (below). Run it with `python watcher.py`, then in a second terminal from the
same folder `python -m http.server 8000`, then open `http://localhost:8000/dashboard.html`.

For the Live Refresh Verification checkpoint (Lecture 7, Part D, item D3): with both scripts
running, open `sample_sales.csv`, change or add a row, save, and watch the dashboard update
within about a second, with nothing manually re-run. Measured during the build of this
example: editing the source file and timing detection end to end measured approximately
300ms, comfortably under the 1-second target.

Why this architecture: no framework and no build step, matching the course's guided-operator
promise, the student directs Claude to write this, they don't hand-configure a stack. The
watcher polls the file and the dashboard polls the watcher's output, two independent,
restartable pieces rather than one fragile process; if the dashboard tab is closed and
reopened, it just resumes polling. Zero pip dependencies for the CSV path; nothing to install
beyond Python itself. If a student's own source is `.xlsx`, have Claude add an `openpyxl`
read path in `load_rows()`; the JSON shape `build_snapshot()` produces is what
`dashboard.html` expects and should stay the same.

**`watcher.py`:**

```python
"""
Live Decision Dashboard - watcher script (worked example)

Watches sample_sales.csv for changes and rewrites live_data.json whenever
the file's contents change. dashboard.html polls live_data.json roughly
once per second, so an edit to the source file appears on screen in under
1 second.

Zero external dependencies - only Python's standard library (csv, json).
If you point this at an .xlsx source instead, ask Claude to add an openpyxl
read path; the JSON shape written by build_snapshot() below is what
dashboard.html expects and should not change.

Run:
    python watcher.py
Then in a second terminal, from this same folder:
    python -m http.server 8000
Then open http://localhost:8000/dashboard.html in a browser.

To test the 1-second refresh claim: with both running, open sample_sales.csv
in Excel, change one Revenue value, save, and watch the dashboard update.
"""

import csv
import json
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

SOURCE_FILE = Path(__file__).parent / "sample_sales.csv"
OUTPUT_FILE = Path(__file__).parent / "live_data.json"
POLL_SECONDS = 0.3   # checked well under 1s so total user-visible latency (poll + dashboard fetch) stays under 1s


def load_rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def build_snapshot(rows: list[dict]) -> dict:
    revenue_by_region: dict[str, float] = defaultdict(float)
    revenue_by_date: dict[str, float] = defaultdict(float)
    total_revenue = 0.0
    total_units = 0

    for row in rows:
        revenue = float(row["Revenue"])
        units = int(row["UnitsSold"])
        revenue_by_region[row["Region"]] += revenue
        revenue_by_date[row["Date"]] += revenue
        total_revenue += revenue
        total_units += units

    revenue_by_region_sorted = dict(
        sorted(revenue_by_region.items(), key=lambda kv: kv[1], reverse=True)
    )
    trend = [
        {"date": d, "revenue": int(round(revenue_by_date[d]))}
        for d in sorted(revenue_by_date)
    ]

    return {
        "last_updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "row_count": len(rows),
        "total_revenue": int(round(total_revenue)),
        "total_units": total_units,
        "revenue_by_region": {k: int(round(v)) for k, v in revenue_by_region_sorted.items()},
        "revenue_trend": trend,
    }


def main() -> None:
    print(f"Watching {SOURCE_FILE.name} - writing snapshots to {OUTPUT_FILE.name}")
    print(f"Polling every {POLL_SECONDS}s. Ctrl+C to stop.")

    last_mtime = None
    while True:
        try:
            mtime = SOURCE_FILE.stat().st_mtime
            if mtime != last_mtime:
                rows = load_rows(SOURCE_FILE)
                snapshot = build_snapshot(rows)
                OUTPUT_FILE.write_text(json.dumps(snapshot, indent=2))
                last_mtime = mtime
                print(f"[{snapshot['last_updated']}] source changed -> live_data.json rewritten ({snapshot['row_count']} rows)")
        except FileNotFoundError:
            print(f"Waiting for {SOURCE_FILE.name} to exist...")
        except Exception as exc:  # noqa: BLE001 - a classroom tool should keep running and report, not crash on a bad edit mid-save
            print(f"Skipped a snapshot (source mid-write or malformed): {exc}")

        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
```

**`dashboard.html`:**

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Live Decision Dashboard, Sample Sales (Worked Example)</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  /* Palette per the CPS dataviz skill's validated default (references/palette.md).
     Categorical slots assigned in FIXED order per region, never re-cycled if a
     region is added/removed. Validated: node validate_palette.js "#2a78d6,#eb6834,#1baf7a"
     - all CVD/lightness/chroma checks PASS; light-mode aqua is a contrast WARN,
     mitigated by the always-visible direct value labels (the relief rule). */
  .viz-root {
    color-scheme: light;
    --surface-1:       #fcfcfb;
    --page:            #f4f4f2;
    --text-primary:    #0b0b0b;
    --text-secondary:  #52514e;
    --text-muted:      #898781;
    --gridline:        #e1e0d9;
    --baseline:        #c3c2b7;
    --border:          rgba(11,11,11,0.10);
    --good:            #006300;
    --series-1:        #2a78d6;  /* Cairo */
    --series-2:        #eb6834;  /* Alexandria */
    --series-3:        #1baf7a;  /* Giza */
  }
  @media (prefers-color-scheme: dark) {
    :root:where(:not([data-theme="light"])) .viz-root {
      color-scheme: dark;
      --surface-1:      #1a1a19;
      --page:           #0d0d0d;
      --text-primary:   #ffffff;
      --text-secondary: #c3c2b7;
      --text-muted:     #898781;
      --gridline:       #2c2c2a;
      --baseline:       #383835;
      --border:         rgba(255,255,255,0.10);
      --good:            #0ca30c;
      --series-1:       #3987e5;
      --series-2:       #d95926;
      --series-3:       #199e70;
    }
  }
  :root[data-theme="dark"] .viz-root {
    color-scheme: dark;
    --surface-1:      #1a1a19;
    --page:           #0d0d0d;
    --text-primary:   #ffffff;
    --text-secondary: #c3c2b7;
    --text-muted:     #898781;
    --gridline:       #2c2c2a;
    --baseline:        #383835;
    --border:         rgba(255,255,255,0.10);
    --good:            #0ca30c;
    --series-1:       #3987e5;
    --series-2:       #d95926;
    --series-3:       #199e70;
  }

  * { box-sizing: border-box; }
  body { margin: 0; font-family: system-ui, -apple-system, "Segoe UI", sans-serif; background: var(--page); color: var(--text-primary); }
  .viz-root { padding: 24px; }

  header { display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap; gap: 8px; margin-bottom: 20px; }
  h1 { font-size: 1.3rem; margin: 0; color: var(--text-primary); }
  #status { font-size: 0.82rem; color: var(--text-muted); }
  #status.live::before { content: "●"; color: var(--good); margin-right: 6px; }

  .kpi-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 14px; margin-bottom: 24px; }
  .kpi { background: var(--surface-1); border: 1px solid var(--border); border-radius: 10px; padding: 16px; }
  .kpi .label { font-size: 0.76rem; color: var(--text-secondary); }
  .kpi .value { font-size: 1.7rem; font-weight: 600; margin-top: 4px; color: var(--text-primary); }

  .panels { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
  @media (max-width: 720px) { .panels { grid-template-columns: 1fr; } }
  .panel { background: var(--surface-1); border: 1px solid var(--border); border-radius: 10px; padding: 18px; position: relative; overflow: visible; }
  .panel h2 { font-size: 0.95rem; margin: 0 0 4px 0; color: var(--text-primary); }
  .panel .sub { font-size: 0.76rem; color: var(--text-muted); margin-bottom: 14px; }

  /* Legend, always present for >=2 series (3 regions here) */
  .legend { display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 14px; }
  .legend-item { display: flex; align-items: center; gap: 6px; font-size: 0.78rem; color: var(--text-secondary); }
  .legend-swatch { width: 10px; height: 10px; border-radius: 2px; flex-shrink: 0; }

  /* Bars, <=24px thick, rounded data-end, square baseline, 2px surface gap between bars */
  .bar-row { display: flex; align-items: center; gap: 10px; margin-bottom: 2px; padding: 3px 0; border-radius: 4px; }
  .bar-row:hover { background: var(--page); }
  .bar-label { width: 90px; font-size: 0.82rem; color: var(--text-secondary); flex-shrink: 0; }
  .bar-track { flex: 1; background: var(--gridline); border-radius: 4px; height: 20px; overflow: hidden; }
  .bar-fill { height: 100%; border-radius: 0 4px 4px 0; }
  .bar-value { width: 90px; text-align: right; font-size: 0.82rem; color: var(--text-primary); font-variant-numeric: tabular-nums; }

  svg { width: 100%; height: 160px; overflow: visible; }
  .gridline { stroke: var(--gridline); stroke-width: 1; }
  .trend-path { fill: none; stroke: var(--series-1); stroke-width: 2; stroke-linejoin: round; stroke-linecap: round; }
  .trend-dot { fill: var(--series-1); stroke: var(--surface-1); stroke-width: 2; }
  .trend-label { fill: var(--text-primary); font-size: 11px; font-weight: 600; }

  /* Hover tooltip, a real layer, not native title */
  .viz-tooltip {
    position: fixed; pointer-events: none; z-index: 10;
    background: var(--text-primary); color: var(--surface-1);
    font-size: 0.76rem; padding: 5px 9px; border-radius: 6px;
    white-space: nowrap; opacity: 0; transition: opacity 0.1s;
  }
  .viz-tooltip.show { opacity: 1; }

  footer { margin-top: 20px; font-size: 0.74rem; color: var(--text-muted); }
</style>
</head>
<body>
<div class="viz-root">

<header>
  <h1>Live Decision Dashboard, Sample Sales (Worked Example)</h1>
  <div id="status">connecting…</div>
</header>

<div class="kpi-row">
  <div class="kpi"><div class="label">Total revenue</div><div class="value" id="kpi-revenue">…</div></div>
  <div class="kpi"><div class="label">Total units sold</div><div class="value" id="kpi-units">…</div></div>
  <div class="kpi"><div class="label">Rows in source</div><div class="value" id="kpi-rows">…</div></div>
  <div class="kpi"><div class="label">Last source update</div><div class="value" id="kpi-updated" style="font-size:1rem;">…</div></div>
</div>

<div class="panels">
  <div class="panel">
    <h2>Revenue by region</h2>
    <div class="sub">3 regions, Cairo, Alexandria, Giza</div>
    <div class="legend" id="region-legend"></div>
    <div id="region-bars"></div>
  </div>
  <div class="panel">
    <h2>Revenue trend</h2>
    <div class="sub">Daily total, all regions</div>
    <svg id="trend-svg" viewBox="0 0 400 160" preserveAspectRatio="none"></svg>
  </div>
</div>

<footer>
  Polls <code>live_data.json</code> every 1 second. Edit and save <code>sample_sales.csv</code> while
  <code>watcher.py</code> is running to see this update, that's the Live Refresh Verification checkpoint
  from Lecture 7, Part D.
</footer>

</div>
<div class="viz-tooltip" id="tooltip"></div>

<script>
const REFRESH_MS = 1000;
const statusEl = document.getElementById('status');
const tooltip = document.getElementById('tooltip');

// Fixed categorical assignment, same region always gets the same slot, never re-cycled by rank/value
const REGION_ORDER = ['Cairo', 'Alexandria', 'Giza'];
const REGION_COLOR_VAR = ['--series-1', '--series-2', '--series-3'];

function fmtMoney(n) { return '$' + Number(n).toLocaleString(); }

function seriesColor(varName) {
  return getComputedStyle(document.querySelector('.viz-root')).getPropertyValue(varName).trim();
}

function showTooltip(evt, text) {
  tooltip.textContent = text;
  tooltip.style.left = (evt.clientX + 12) + 'px';
  tooltip.style.top = (evt.clientY - 28) + 'px';
  tooltip.classList.add('show');
}
function hideTooltip() { tooltip.classList.remove('show'); }

function renderLegend(regions) {
  const el = document.getElementById('region-legend');
  el.innerHTML = regions.map((region, i) => `
    <div class="legend-item">
      <span class="legend-swatch" style="background:${seriesColor(REGION_COLOR_VAR[i % REGION_COLOR_VAR.length])}"></span>
      ${region}
    </div>
  `).join('');
}

function renderRegionBars(byRegion) {
  const el = document.getElementById('region-bars');
  // Order by the fixed REGION_ORDER when present, so a region's row position and color never shift with its rank
  const regions = REGION_ORDER.filter(r => r in byRegion).concat(Object.keys(byRegion).filter(r => !REGION_ORDER.includes(r)));
  renderLegend(regions);
  const max = Math.max(...Object.values(byRegion), 1);

  el.innerHTML = regions.map((region, i) => {
    const value = byRegion[region];
    const colorVar = REGION_COLOR_VAR[i % REGION_COLOR_VAR.length];
    return `
      <div class="bar-row" data-region="${region}" data-value="${value}">
        <div class="bar-label">${region}</div>
        <div class="bar-track"><div class="bar-fill" style="width:${(value / max * 100).toFixed(1)}%; background:var(${colorVar})"></div></div>
        <div class="bar-value">${fmtMoney(value)}</div>
      </div>
    `;
  }).join('');

  el.querySelectorAll('.bar-row').forEach(row => {
    row.addEventListener('mousemove', e => showTooltip(e, `${row.dataset.region}: ${fmtMoney(row.dataset.value)}`));
    row.addEventListener('mouseleave', hideTooltip);
  });
}

function renderTrend(trend) {
  const svg = document.getElementById('trend-svg');
  if (!trend.length) { svg.innerHTML = ''; return; }

  const values = trend.map(p => p.revenue);
  const min = Math.min(...values), max = Math.max(...values);
  const range = (max - min) || 1;
  const stepX = 400 / (trend.length - 1 || 1);
  const yOf = v => 140 - ((v - min) / range) * 110 - 8;

  const coords = trend.map((p, i) => ({ x: i * stepX, y: yOf(p.revenue), ...p }));
  const points = coords.map(c => `${c.x.toFixed(1)},${c.y.toFixed(1)}`).join(' ');

  // Recessive hairline gridlines at 0/50/100% before the data
  const gridlines = [0, 0.5, 1].map(t => {
    const y = 140 - t * 110 - 8;
    return `<line class="gridline" x1="0" y1="${y}" x2="400" y2="${y}" />`;
  }).join('');

  const last = coords[coords.length - 1];
  const dots = coords.map((c, i) => {
    const isLast = i === coords.length - 1;
    return `<circle class="trend-dot" cx="${c.x.toFixed(1)}" cy="${c.y.toFixed(1)}" r="${isLast ? 5 : 4}" data-date="${c.date}" data-revenue="${c.revenue}" />`;
  }).join('');

  // Direct label only on the endpoint (selective labeling, not one per point)
  const endLabel = `<text class="trend-label" x="${(last.x - 34).toFixed(1)}" y="${(last.y - 10).toFixed(1)}">${fmtMoney(last.revenue)}</text>`;

  svg.innerHTML = `${gridlines}<polyline class="trend-path" points="${points}" />${dots}${endLabel}`;

  svg.querySelectorAll('.trend-dot').forEach(dot => {
    dot.addEventListener('mousemove', e => showTooltip(e, `${dot.dataset.date}: ${fmtMoney(dot.dataset.revenue)}`));
    dot.addEventListener('mouseleave', hideTooltip);
  });
}

async function refresh() {
  try {
    const res = await fetch('live_data.json?t=' + Date.now(), { cache: 'no-store' });
    if (!res.ok) throw new Error('no data yet');
    const data = await res.json();

    document.getElementById('kpi-revenue').textContent = fmtMoney(data.total_revenue);
    document.getElementById('kpi-units').textContent = Number(data.total_units).toLocaleString();
    document.getElementById('kpi-rows').textContent = data.row_count;
    document.getElementById('kpi-updated').textContent = new Date(data.last_updated).toLocaleTimeString();

    renderRegionBars(data.revenue_by_region);
    renderTrend(data.revenue_trend);

    statusEl.textContent = 'live, last checked ' + new Date().toLocaleTimeString();
    statusEl.className = 'live';
  } catch (err) {
    statusEl.textContent = 'waiting for watcher.py to produce live_data.json…';
    statusEl.className = '';
  }
}

refresh();
setInterval(refresh, REFRESH_MS);
</script>

</body>
</html>
```

### 7.2 Blank template, `Blank_Live_Decision_Dashboard_Template/`

The same architecture as Section 7.1, parameterized instead of pre-filled. To adapt it to a
new dataset: copy `watcher_template.py` and `dashboard_template.html` into the project folder
alongside the data file; fill in `watcher_template.py`'s CONFIG block (`SOURCE_FILE`,
`GROUP_BY_COLUMN`, `DATE_COLUMN`, `VALUE_COLUMN`, `COUNT_COLUMN`, set to `None` if there isn't
one); in `dashboard_template.html`, replace every `ADAPT:` marker (the page title, heading,
and the 3-5 KPI labels from the Dashboard Scope Brief); run `python watcher_template.py`, then
in a second terminal `python -m http.server 8000`, then open
`http://localhost:8000/dashboard_template.html`; run the Live Refresh Verification checkpoint
(D3): edit the source file, save, time how long the dashboard takes to update, target under 1
second. If Claude is doing this for a student rather than the student doing it by hand, point
Claude at this template and the approved Dashboard Scope Brief; it should fill in the CONFIG
block and every `ADAPT:` marker itself.

**`watcher_template.py`:**

```python
"""
Live Decision Dashboard - watcher script (BLANK TEMPLATE)

Copy this alongside your own dataset and fill in the CONFIG block below.
This is what the Dashboard-Build Prompt Template (Lecture 7, Part D) should
produce when Claude adapts it to your specific data - see Section 7.1 above
for a fully worked reference.

Zero external dependencies - Python standard library only (csv, json).
If your source is .xlsx instead of .csv, ask Claude to add an openpyxl
read path in load_rows() - keep the JSON shape in build_snapshot()
unchanged, since dashboard_template.html expects it.

Run:
    python watcher_template.py
Then in a second terminal, from this same folder:
    python -m http.server 8000
Then open http://localhost:8000/dashboard_template.html
"""

import csv
import json
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

# ============ CONFIG - fill this in for your dataset ============
SOURCE_FILE = Path(__file__).parent / "ADAPT_your_data.csv"
OUTPUT_FILE = Path(__file__).parent / "live_data.json"
POLL_SECONDS = 0.3

GROUP_BY_COLUMN = "ADAPT_category_column"     # e.g. "Region", "Product", "Segment"
DATE_COLUMN = "ADAPT_date_column"             # e.g. "Date", "OrderDate"
VALUE_COLUMN = "ADAPT_numeric_value_column"   # e.g. "Revenue", "Amount"
COUNT_COLUMN = "ADAPT_secondary_count_column" # e.g. "UnitsSold" - set to None if you don't have one
# ==================================================================


def load_rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def build_snapshot(rows: list[dict]) -> dict:
    value_by_group: dict[str, float] = defaultdict(float)
    value_by_date: dict[str, float] = defaultdict(float)
    total_value = 0.0
    total_count = 0

    for row in rows:
        value = float(row[VALUE_COLUMN])
        value_by_group[row[GROUP_BY_COLUMN]] += value
        value_by_date[row[DATE_COLUMN]] += value
        total_value += value
        if COUNT_COLUMN:
            total_count += int(float(row[COUNT_COLUMN]))

    value_by_group_sorted = dict(sorted(value_by_group.items(), key=lambda kv: kv[1], reverse=True))
    trend = [
        {"date": d, "value": int(round(value_by_date[d]))}
        for d in sorted(value_by_date)
    ]

    return {
        "last_updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "row_count": len(rows),
        "total_value": int(round(total_value)),
        "total_count": total_count,
        "value_by_group": {k: int(round(v)) for k, v in value_by_group_sorted.items()},
        "trend": trend,
    }


def main() -> None:
    print(f"Watching {SOURCE_FILE.name} -> {OUTPUT_FILE.name} every {POLL_SECONDS}s. Ctrl+C to stop.")
    last_mtime = None
    while True:
        try:
            mtime = SOURCE_FILE.stat().st_mtime
            if mtime != last_mtime:
                rows = load_rows(SOURCE_FILE)
                snapshot = build_snapshot(rows)
                OUTPUT_FILE.write_text(json.dumps(snapshot, indent=2))
                last_mtime = mtime
                print(f"[{snapshot['last_updated']}] source changed -> rewrote {OUTPUT_FILE.name} ({snapshot['row_count']} rows)")
        except FileNotFoundError:
            print(f"Waiting for {SOURCE_FILE.name} to exist...")
        except Exception as exc:  # noqa: BLE001
            print(f"Skipped a snapshot (source mid-write, bad column name, or malformed row): {exc}")

        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
```

**`dashboard_template.html`:**

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<!-- ADAPT: set your dashboard's title -->
<title>Live Decision Dashboard, ADAPT Your Title</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  /* Palette per the CPS dataviz skill's validated default (references/palette.md).
     ADAPT: if your institution has its own brand colors, swap the --series-N hex
     values here (both light and dark blocks) and re-run:
       node validate_palette.js "<your 3 hexes>" --mode light
       node validate_palette.js "<your 3 dark hexes>" --mode dark
     Categorical hues are assigned in FIXED order by group identity, never
     re-cycled by rank/value. This 3-slot palette caps at 3 groups before the
     all-pairs CVD floors fail; past 3 groups, fold the smallest into "Other"
     or facet into small multiples instead of adding a 4th color. */
  .viz-root {
    color-scheme: light;
    --surface-1:       #fcfcfb;
    --page:            #f4f4f2;
    --text-primary:    #0b0b0b;
    --text-secondary:  #52514e;
    --text-muted:      #898781;
    --gridline:        #e1e0d9;
    --border:          rgba(11,11,11,0.10);
    --good:            #006300;
    --series-1:        #2a78d6;
    --series-2:        #eb6834;
    --series-3:        #1baf7a;
  }
  @media (prefers-color-scheme: dark) {
    :root:where(:not([data-theme="light"])) .viz-root {
      color-scheme: dark;
      --surface-1:      #1a1a19;
      --page:           #0d0d0d;
      --text-primary:   #ffffff;
      --text-secondary: #c3c2b7;
      --text-muted:     #898781;
      --gridline:       #2c2c2a;
      --border:         rgba(255,255,255,0.10);
      --good:            #0ca30c;
      --series-1:       #3987e5;
      --series-2:       #d95926;
      --series-3:       #199e70;
    }
  }
  :root[data-theme="dark"] .viz-root {
    color-scheme: dark;
    --surface-1:      #1a1a19;
    --page:           #0d0d0d;
    --text-primary:   #ffffff;
    --text-secondary: #c3c2b7;
    --text-muted:     #898781;
    --gridline:       #2c2c2a;
    --border:         rgba(255,255,255,0.10);
    --good:            #0ca30c;
    --series-1:       #3987e5;
    --series-2:       #d95926;
    --series-3:       #199e70;
  }

  * { box-sizing: border-box; }
  body { margin: 0; font-family: system-ui, -apple-system, "Segoe UI", sans-serif; background: var(--page); color: var(--text-primary); }
  .viz-root { padding: 24px; }

  header { display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap; gap: 8px; margin-bottom: 20px; }
  h1 { font-size: 1.3rem; margin: 0; color: var(--text-primary); }
  #status { font-size: 0.82rem; color: var(--text-muted); }
  #status.live::before { content: "●"; color: var(--good); margin-right: 6px; }

  .kpi-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 14px; margin-bottom: 24px; }
  .kpi { background: var(--surface-1); border: 1px solid var(--border); border-radius: 10px; padding: 16px; }
  .kpi .label { font-size: 0.76rem; color: var(--text-secondary); }
  .kpi .value { font-size: 1.7rem; font-weight: 600; margin-top: 4px; color: var(--text-primary); }

  .panels { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
  @media (max-width: 720px) { .panels { grid-template-columns: 1fr; } }
  .panel { background: var(--surface-1); border: 1px solid var(--border); border-radius: 10px; padding: 18px; position: relative; overflow: visible; }
  .panel h2 { font-size: 0.95rem; margin: 0 0 4px 0; color: var(--text-primary); }
  .panel .sub { font-size: 0.76rem; color: var(--text-muted); margin-bottom: 14px; }

  .legend { display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 14px; }
  .legend-item { display: flex; align-items: center; gap: 6px; font-size: 0.78rem; color: var(--text-secondary); }
  .legend-swatch { width: 10px; height: 10px; border-radius: 2px; flex-shrink: 0; }

  .bar-row { display: flex; align-items: center; gap: 10px; margin-bottom: 2px; padding: 3px 0; border-radius: 4px; }
  .bar-row:hover { background: var(--page); }
  .bar-label { width: 90px; font-size: 0.82rem; color: var(--text-secondary); flex-shrink: 0; }
  .bar-track { flex: 1; background: var(--gridline); border-radius: 4px; height: 20px; overflow: hidden; }
  .bar-fill { height: 100%; border-radius: 0 4px 4px 0; }
  .bar-value { width: 90px; text-align: right; font-size: 0.82rem; color: var(--text-primary); font-variant-numeric: tabular-nums; }

  svg { width: 100%; height: 160px; overflow: visible; }
  .gridline { stroke: var(--gridline); stroke-width: 1; }
  .trend-path { fill: none; stroke: var(--series-1); stroke-width: 2; stroke-linejoin: round; stroke-linecap: round; }
  .trend-dot { fill: var(--series-1); stroke: var(--surface-1); stroke-width: 2; }
  .trend-label { fill: var(--text-primary); font-size: 11px; font-weight: 600; }

  .viz-tooltip {
    position: fixed; pointer-events: none; z-index: 10;
    background: var(--text-primary); color: var(--surface-1);
    font-size: 0.76rem; padding: 5px 9px; border-radius: 6px;
    white-space: nowrap; opacity: 0; transition: opacity 0.1s;
  }
  .viz-tooltip.show { opacity: 1; }

  footer { margin-top: 20px; font-size: 0.74rem; color: var(--text-muted); }
</style>
</head>
<body>
<div class="viz-root">

<header>
  <!-- ADAPT: set your dashboard's on-page heading -->
  <h1>Live Decision Dashboard, ADAPT Your Title</h1>
  <div id="status">connecting…</div>
</header>

<div class="kpi-row">
  <!-- ADAPT: rename these 3-5 KPI labels to match your Dashboard Scope Brief (Lecture 7, Part C) -->
  <div class="kpi"><div class="label">ADAPT KPI 1, total value</div><div class="value" id="kpi-value">…</div></div>
  <div class="kpi"><div class="label">ADAPT KPI 2, total count</div><div class="value" id="kpi-count">…</div></div>
  <div class="kpi"><div class="label">Rows in source</div><div class="value" id="kpi-rows">…</div></div>
  <div class="kpi"><div class="label">Last source update</div><div class="value" id="kpi-updated" style="font-size:1rem;">…</div></div>
</div>

<div class="panels">
  <div class="panel">
    <!-- ADAPT: rename to match your GROUP_BY_COLUMN, e.g. "Value by Region" -->
    <h2>Value by group</h2>
    <div class="sub">Up to 3 groups, past that, fold into "Other" or facet</div>
    <div class="legend" id="group-legend"></div>
    <div id="group-bars"></div>
  </div>
  <div class="panel">
    <!-- ADAPT: rename to match what you're trending over time -->
    <h2>Trend</h2>
    <div class="sub">ADAPT, what this line tracks over time</div>
    <svg id="trend-svg" viewBox="0 0 400 160" preserveAspectRatio="none"></svg>
  </div>
</div>

<footer>
  Polls <code>live_data.json</code> every 1 second. Run <code>watcher_template.py</code> (after filling in its CONFIG
  block) alongside this page for the Live Refresh Verification checkpoint.
</footer>

</div>
<div class="viz-tooltip" id="tooltip"></div>

<script>
const REFRESH_MS = 1000;
const statusEl = document.getElementById('status');
const tooltip = document.getElementById('tooltip');

// ADAPT: list your groups in the fixed order you want them colored/displayed in,
// a group's color and row position should never shift just because its value changed rank
const GROUP_ORDER = []; // e.g. ['Region A', 'Region B', 'Region C'], leave empty to fall back to data order
const GROUP_COLOR_VAR = ['--series-1', '--series-2', '--series-3']; // caps at 3, see the palette note in <style>

// ADAPT: adjust the number format if your value isn't currency (e.g. drop the '$')
function fmtValue(n) { return '$' + Number(n).toLocaleString(); }

function seriesColor(varName) {
  return getComputedStyle(document.querySelector('.viz-root')).getPropertyValue(varName).trim();
}

function showTooltip(evt, text) {
  tooltip.textContent = text;
  tooltip.style.left = (evt.clientX + 12) + 'px';
  tooltip.style.top = (evt.clientY - 28) + 'px';
  tooltip.classList.add('show');
}
function hideTooltip() { tooltip.classList.remove('show'); }

function renderLegend(groups) {
  const el = document.getElementById('group-legend');
  el.innerHTML = groups.map((g, i) => `
    <div class="legend-item">
      <span class="legend-swatch" style="background:${seriesColor(GROUP_COLOR_VAR[i % GROUP_COLOR_VAR.length])}"></span>
      ${g}
    </div>
  `).join('');
}

function renderGroupBars(byGroup) {
  const el = document.getElementById('group-bars');
  const known = GROUP_ORDER.filter(g => g in byGroup);
  const groups = known.concat(Object.keys(byGroup).filter(g => !known.includes(g)));
  renderLegend(groups);
  const max = Math.max(...Object.values(byGroup), 1);

  el.innerHTML = groups.map((label, i) => {
    const value = byGroup[label];
    const colorVar = GROUP_COLOR_VAR[i % GROUP_COLOR_VAR.length];
    return `
      <div class="bar-row" data-label="${label}" data-value="${value}">
        <div class="bar-label">${label}</div>
        <div class="bar-track"><div class="bar-fill" style="width:${(value / max * 100).toFixed(1)}%; background:var(${colorVar})"></div></div>
        <div class="bar-value">${fmtValue(value)}</div>
      </div>
    `;
  }).join('');

  el.querySelectorAll('.bar-row').forEach(row => {
    row.addEventListener('mousemove', e => showTooltip(e, `${row.dataset.label}: ${fmtValue(row.dataset.value)}`));
    row.addEventListener('mouseleave', hideTooltip);
  });
}

function renderTrend(trend) {
  const svg = document.getElementById('trend-svg');
  if (!trend.length) { svg.innerHTML = ''; return; }

  const values = trend.map(p => p.value);
  const min = Math.min(...values), max = Math.max(...values);
  const range = (max - min) || 1;
  const stepX = 400 / (trend.length - 1 || 1);
  const yOf = v => 140 - ((v - min) / range) * 110 - 8;

  const coords = trend.map((p, i) => ({ x: i * stepX, y: yOf(p.value), ...p }));
  const points = coords.map(c => `${c.x.toFixed(1)},${c.y.toFixed(1)}`).join(' ');

  const gridlines = [0, 0.5, 1].map(t => {
    const y = 140 - t * 110 - 8;
    return `<line class="gridline" x1="0" y1="${y}" x2="400" y2="${y}" />`;
  }).join('');

  const last = coords[coords.length - 1];
  const dots = coords.map((c, i) => {
    const isLast = i === coords.length - 1;
    return `<circle class="trend-dot" cx="${c.x.toFixed(1)}" cy="${c.y.toFixed(1)}" r="${isLast ? 5 : 4}" data-date="${c.date}" data-value="${c.value}" />`;
  }).join('');

  const endLabel = `<text class="trend-label" x="${(last.x - 34).toFixed(1)}" y="${(last.y - 10).toFixed(1)}">${fmtValue(last.value)}</text>`;

  svg.innerHTML = `${gridlines}<polyline class="trend-path" points="${points}" />${dots}${endLabel}`;

  svg.querySelectorAll('.trend-dot').forEach(dot => {
    dot.addEventListener('mousemove', e => showTooltip(e, `${dot.dataset.date}: ${fmtValue(dot.dataset.value)}`));
    dot.addEventListener('mouseleave', hideTooltip);
  });
}

async function refresh() {
  try {
    const res = await fetch('live_data.json?t=' + Date.now(), { cache: 'no-store' });
    if (!res.ok) throw new Error('no data yet');
    const data = await res.json();

    document.getElementById('kpi-value').textContent = fmtValue(data.total_value);
    document.getElementById('kpi-count').textContent = Number(data.total_count).toLocaleString();
    document.getElementById('kpi-rows').textContent = data.row_count;
    document.getElementById('kpi-updated').textContent = new Date(data.last_updated).toLocaleTimeString();

    renderGroupBars(data.value_by_group);
    renderTrend(data.trend);

    statusEl.textContent = 'live, last checked ' + new Date().toLocaleTimeString();
    statusEl.className = 'live';
  } catch (err) {
    statusEl.textContent = 'waiting for watcher_template.py to produce live_data.json…';
    statusEl.className = '';
  }
}

refresh();
setInterval(refresh, REFRESH_MS);
</script>

</body>
</html>
```

---

## 8. Building the multi-page, story-driven version (Stage 5 in full)

Sections 6 and 7 above are the classroom minimum: one page, one architecture, always
verified. For the "amazing," professional result this course actually wants a student to
walk away with, extend that same architecture rather than replacing it, in three ways.

**Multi-page, without a framework.** Keep every page a self-contained HTML file (no
framework, no build step, matching Prompt 4's own rule), and link them with a plain `<nav>`
of `<a href="...">` tags, the Overview page first, then one drill-down page per dimension the
Dashboard Scope Brief named (Section 5.6). Every page polls the same `live_data.json`; the
watcher stays singular, since it already computes everything every page needs. This is
"multi-page" in the sense a stakeholder experiences (several distinct, linked views), while
staying inside the guided-operator, zero-framework promise the course is built on.

**Modern design and coloring.** Section 7.1's `dashboard.html` already carries the full
pattern this course treats as the design bar: a validated 3-color categorical palette with
both light and dark mode handled, tabular-number alignment on every value, real hover
tooltips instead of native browser titles, hairline gridlines instead of a heavy chart
border, and a single consistent type scale. Reuse those exact CSS custom properties and
component classes (`.kpi`, `.panel`, `.bar-row`, `.viz-tooltip`) on every new page rather than
inventing a second style per page; that consistency is itself part of what reads as
professional, not any single color choice.

**Professional storytelling, not just charts.** Every page opens with a one-sentence insight
in plain business language, above the first chart, not after it, mirroring the Dashboard
Scope Brief's headline (Section 5.6) on the Overview page and a page-specific finding on each
drill-down page, in the shape "<measure> is <X>% concentrated in <segments>" above the
relevant panel, not a bare "<Measure> by <Dimension>" heading with no number attached. The
WWI box below gives a worked instance. Where Stage 3b found no significant difference, the
sentence states the measured spread and says plainly that it is inside what chance produces. Close the
Overview page with the through-line sentence from the brief, so a reader who only sees that
one page still leaves with the dashboard's actual point.

> **WWI worked example, Section 8 applied:** 4 pages per the Section 5.6 brief (Overview,
> Geography, Products, Customers), one shared nav, one shared `live_data.json`, one shared
> palette from Section 7.1. Overview opens with the headline sentence quoted in Section 5.6;
> Geography opens with "California and Washington are 66% of revenue" above the by-state bars;
> Products opens with "The top 5 products by revenue are all packaging materials, not toy
> inventory" above the top-products bars; Customers opens with "6.77M of revenue, 34% of the
> total, has no Buying Group on file" above the by-group bars. All four pages reuse Section
> 7.1's exact CSS custom properties and `.kpi`/`.panel`/`.bar-row` classes unchanged.

---

## 9. Cross-reference index

Everything above is self-contained; these are the actual files on disk this Playbook
reproduces, for anyone who wants to open the runnable originals directly rather than copy
the code out of this document.

- `Instructor_Toolkit/AIB902_L07_Prompt_1_Data_Cleaning.md` through `..._Prompt_4_Dashboard_Build.md`
  and the matching files in `Student_Toolkit/` (Section 6, reproduced in full above).
- `Hands_On/Example_Live_Decision_Dashboard/` (Section 7.1, reproduced in full above).
- `Hands_On/Blank_Live_Decision_Dashboard_Template/` (Section 7.2, reproduced in full above).
- Sibling generic method for course design itself, not dashboards: `05_Deliverables_Final/Course_Design_Playbook.md`.
- Real dataset this Playbook was validated against: `Reference_Material/WWI_Dataset/`.

**Part II reference implementation.** Sections 10 to 18 were written from a second, complete
engagement. Its runnable artifacts, referenced throughout Part II:

- `02_Analysis/analyze.py` - the cleaning checklist and Stage 3 insights, standard library only.
- `02_Analysis/analyze_deep.py` - Stage 3b and the seven-angle battery, including the
  chi-square survival function, the permutation tests, the bootstrap, Benford's law and the
  simulation power analysis.
- `03_Dashboard/watcher.py` - the watcher and the extended `live_data.json` contract,
  including the compact row-level feed.
- `03_Dashboard/app.js` - the shared runtime: polling, theming, tooltips, formatting,
  data-bound prose, the cross-filter engine and the chart primitive library.
- `03_Dashboard/styles.css` - design tokens and component classes for light and dark.
- `03_Dashboard/dashboard.html` - the comprehensive cross-filtered page.
- `04_Deliverables/make_report.py` - the client report generator.

---

# Part II, Version 3.0 additions

Sections 1 to 9 above are the method as originally written and are unchanged. The
sections below were added after the method was run end to end on a second, very
different dataset: a flat 1,000-row retail transaction file that passed every
cleaning check and then turned out to contain no measurable signal at all.

That engagement exposed a gap. The original Stages 0 to 5 will faithfully carry a
dataset from raw file to polished dashboard without ever asking whether the
differences being charted are real. On a dataset with genuine structure that gap
never shows. On a dataset without it, the method produces a beautiful, confident,
completely misleading product.

Everything below closes that gap and hardens the build. It is written to be
dataset-agnostic: the new dataset appears only inside marked worked-example boxes,
exactly as WWI does above.

Source: Playbook methodology, not derived from any one dataset.

---

## 10. Stage 3b, Significance Testing

**Insert this between Stage 3 (Section 4) and Stage 4 (Section 5). It is a gate, not
an optional extra.**

### 10.1 The rule

> **Never report a difference before testing whether chance explains it.**

Stage 3 produces rankings: top categories, leading regions, best months. Every one of
those rankings is a claim, and a stakeholder will act on it. Before any of them
reaches a scoping conversation, each must survive a test that asks: if this dataset
had no real structure at all, how often would a gap this large appear anyway?

A gap that chance reproduces routinely is not a finding. Charting it as though it
were is the most damaging thing this pipeline can do, because the chart is persuasive
in exact proportion to how wrong it is.

### 10.2 Test selection

Pick by what the claim is, not by what is familiar.

| The claim you want to make | The test | What it returns |
|---|---|---|
| "These categories differ in how much they sell" | Chi-square goodness of fit against a uniform expectation | p-value; above 0.05 means the spread is ordinary |
| "This statistic is bigger than chance allows" where the statistic is non-standard, e.g. anything computed on **summed money** | **Permutation test.** Shuffle the values across the labels several thousand times and count how often the shuffled statistic beats the real one | An empirical p-value that needs no distributional assumption |
| "This ranking is stable, so we can act on the order" | Bootstrap resampling, 2,000 to 5,000 resamples, reporting a 95% interval per entity | Intervals; if they overlap, the ranking is not reproducible |
| "These amounts are genuine financial records" | Benford's law on the leading digit | Whether the digit distribution matches naturally occurring amounts |
| "There is a trend, or a season" | Fitted slope plus lag-1 autocorrelation of the periodic series | Whether one period predicts the next |
| "There is no effect" (a null claim) | **Power analysis by simulation.** See Section 12 | Whether the sample could have detected an effect if one existed |
| "This combination behaves differently from its parts" | Chi-square on the contingency table, or a permutation test if the cells hold summed money | Whether an interaction exists that marginal totals hide |

### 10.3 Two rules that are easy to get wrong

**A chi-square statistic computed on summed money is not chi-square distributed.**
The chi-square reference distribution assumes counts of independent events. Summed
revenue is neither a count nor independent across rows. Computing the usual
statistic on revenue totals and then looking it up in a chi-square table produces a
p-value that means nothing. When the statistic is non-standard, get the p-value by
permutation instead.

**Correct for multiple comparisons.** Running twenty tests at the 5% level produces
one false positive on average even when nothing is going on. State how many tests
were run and apply a Bonferroni-corrected threshold of 0.05 divided by the number of
tests, or say plainly that the result is uncorrected.

> **Worked example, Stage 3b, the mistake and its correction (MEASURED).** On a flat
> retail transaction file, an early pass tested whether product category interacted
> with city on revenue. It computed the usual chi-square expression on summed revenue,
> rescaled it by the mean transaction value, and looked the result up in a chi-square
> table. That returned p = 0.023, which reads as a real interaction and would have
> justified a category-by-city drill-down page.
>
> The statistic was not chi-square distributed, so the lookup was meaningless. A
> 20,000-shuffle permutation test on the same table returned **p = 0.184**. There was
> no interaction. Seven interaction tests had been run in total, so even the original
> 0.023 would not have survived a Bonferroni threshold of 0.05 / 7 = 0.0071.
>
> The lesson is not "be careful with chi-square". It is that a wrong test produced a
> result that looked exactly like a finding, and only re-deriving it a second way
> caught it.

### 10.4 What Stage 3b hands to Stage 4

A short register: every apparent difference Stage 3 surfaced, the test applied, the
result, and a one-word verdict. That register is what the scoping conversation is
allowed to propose KPIs from. A difference that failed its test may still be
displayed, but it may never be described as a finding, and it may never be the basis
of a recommendation.

---

## 11. The Seven-Angle Deep Battery

Run this when Stage 3b comes back null across the board and you need to establish,
defensibly, that you looked hard enough before concluding the dataset cannot answer
the question. Seven independent angles, each capable of finding structure the others
would miss.

| Angle | What it would find | Method |
|---|---|---|
| **1. Two-way interactions** | A combination that behaves unlike its parts, which flat marginal totals hide entirely | Contingency table per dimension pair; chi-square on counts, permutation on money |
| **2. Bootstrap confidence intervals** | Whether any entity is reliably ahead of the others, or whether the ranking is noise | Resample the rows with replacement a few thousand times; report a 95% interval and how often each entity holds rank 1 |
| **3. Concentration, Gini and Lorenz** | The uneven spread that makes prioritisation possible in the first place | Gini coefficient per dimension; compare against the range typical for the domain |
| **4. Benford's law** | Whether the amounts are naturally occurring or generated | Leading-digit distribution against Benford, and against the alternative you suspect |
| **5. Temporal structure** | A weekday, seasonal or momentum effect worth scheduling against | Period-of-week test, period shares, fitted trend, lag-1 autocorrelation |
| **6. Power analysis** | Whether the sample could have detected an effect at all, which decides whether "no effect" means "no effect" or "no data" | Simulation across candidate sample sizes. Section 12 |
| **7. Anomaly scan** | The exceptional records that usually repay investigation | Extreme values, and whether the absence of any is itself abnormal |

**Why seven and not one.** A single null result is weak evidence. Seven independent
nulls are strong, because a dataset with real structure that failed one of these
would ordinarily pass another. Report the consistency, not just the individual
results.

**The absence of anomalies is itself a signal.** Genuine operational data almost
always contains extreme records. A file with none has usually been generated or
heavily cleaned.

> **Worked example, the battery applied (MEASURED).** On the retail file: two-way
> interactions worst p = 0.15, with the category-by-city permutation test at p = 0.18.
> Bootstrap over 4,000 resamples put every city's 95% interval overlapping every
> other's, with the leading city holding rank 1 in only 46% of resamples and every
> city observed at every rank from 1 to 10. Gini 0.055 by city and 0.031 by category,
> against 0.40 to 0.70 for real sales data by customer. Benford rejected at
> chi-square 442 on 8 degrees of freedom, p = 2e-90, with the leading digits instead
> matching a flat random draw at p = 0.85. No day-of-week effect (p = 0.45) and a
> lag-1 autocorrelation of -0.47, meaning a good month did not predict the next. Zero
> transactions beyond three standard deviations.
>
> Seven angles, seven nulls. The Benford result is the one that converted the
> conclusion from "we found nothing" into "these values were generated", which is a
> claim a client can act on.

---

## 12. Power Analysis: turning "no" into a specification

A null result has two possible causes, and they call for opposite responses:

- there is genuinely no effect, or
- there is an effect, and the sample was too small to see it.

Power analysis separates them, and it is the single most useful thing to hand a
client who has just been told their data cannot answer their question. It converts
"this will not work" into "here is what would".

### 12.1 Method, by simulation

Do not look up a formula. Simulate, because a simulation encodes the actual test you
are running.

1. Choose the effect you would want to detect, expressed in business terms, for
   example "one region genuinely running 20% above the others".
2. For a candidate sample size, generate many synthetic datasets that contain exactly
   that effect.
3. Run your real test on each. The proportion that comes back significant is the
   statistical power at that sample size.
4. Repeat across a ladder of sample sizes until power reaches 80%, the conventional
   minimum.
5. Repeat the whole thing for two or three effect sizes, so the client sees the
   trade-off rather than a single number.

### 12.2 How to present it

As a sizing specification, never as a complaint. The table below is the deliverable.

| Effect you want to detect | Rows needed for 80% power |
|---|---|
| A large difference | fewest |
| A moderate difference | more |
| A small difference | most |

Pair it with the power the current sample actually has, so the gap is explicit.

> **Worked example, power as a specification (MEASURED).** For detecting one city
> running above the others at 80% power: a 50% lift needs about 1,000 rows, 30% needs
> 3,000, 20% needs 6,000, and 10% needs 25,000. The file in hand had 1,000 rows, giving
> it 21% power to detect a real 20% difference. Four in five genuine effects of that
> size would have been missed.
>
> That table did more work than every other finding combined. It let the
> recommendation read "send us roughly six thousand rows and a cost column" rather
> than "your data is unusable".

---

## 13. Editorial Rules for dashboards built on weak data

When Stage 3b returns null but a dashboard is still wanted, the honesty of the
wording becomes part of the engineering. A reader acts on what a chart appears to
say, not on the footnote underneath it.

### 13.1 Banned phrasings

Any verb that turns a position in a sorted list into a verdict:

> leads · top performer · best market · strongest category · underperforming ·
> outperforming · focus on · prioritise · our best · our worst

A disclaimer after the sentence does not undo the verb. Rewrite the sentence.

| Instead of | Write |
|---|---|
| "Dallas leads the cities" | "Dallas sits 1.8 points above an even split" |
| "The best and worst city" | "The highest and lowest recorded city" |
| "The leading category" | "The widest gap between any two categories" |
| "Focus on Home Decor" | "Home Decor records the largest share; the gap is inside what chance produces" |

### 13.2 Never state a verdict no published test backs

A page may not say "tests as no signal", "is flat", or "is not significant" unless a
test for exactly that claim exists in the data contract and the page cites it. A
claim that happens to be true is still fabricated if nothing computed it.

If a page needs a verdict it does not have, the fix is to **add the test**, not to
delete the sentence.

### 13.3 Every page carries the caveat

Not one page. Every page, visible without scrolling past the first chart. A reader
who arrives on a drill-down page from a link must meet the caveat there.

### 13.4 Study constants must be distinguishable from live figures

Anything measured once and frozen into the page (a bootstrap interval, a p-value, a
power table) is a property of the study, not of the live feed. It must not move with
the data, and a reader cannot tell which numbers on a live page are live.

So: mark them, and **detect when they go stale**. Store the row count the study ran
on and compare it to the live feed on every render. When they differ, show a warning
saying the constants no longer describe the data.

### 13.5 Prose that quotes a live figure must be data-bound

A headline that hardcodes a total will contradict the tiles beneath it the moment the
source changes. Wrap every live figure quoted in prose in a class hook that the
runtime fills on each update. See Section 14.4.

---

## 14. Reference Architecture v2: the cross-filtered template

Section 7 remains the minimum viable build and still runs as written. This section
extends it to the interactive, multi-page product people usually mean when they say
"like Power BI", while staying inside the same promise: no framework, no build step,
no CDN, no charting library.

The structure is four shared files plus one HTML file per page.

```
watcher.py        polls the source, writes live_data.json
live_data.json    the contract: aggregates + a compact row-level feed
styles.css        design tokens and component classes, light and dark
app.js            polling, theming, tooltips, formatting, filter engine, chart library
<page>.html       one per view; supplies only its own render(d) function
```

### 14.1 The data contract, extended

Publish aggregates for the pages that only display, and a compact row-level feed for
the page that cross-filters.

```json
{
  "last_updated": "...", "row_count": 1000,
  "kpis":   { "...": 0 },
  "trend":  [ { "period": "...", "value": 0 } ],
  "by_<dimension>": [ { "name": "...", "value": 0, "share": 0.0 } ],
  "matrix": { "rows": [], "cols": [], "values": [[]] },
  "raw": {
    "fields": ["date", "dimA", "dimB", "measure"],
    "dimA_values": ["..."], "dimB_values": ["..."],
    "rows": [ ["2024-01-01", 0, 3, 1581] ]
  },
  "limitations": { "headline": "...", "tests": [ {"test": "", "result": "", "verdict": ""} ] }
}
```

Two decisions worth copying:

**Index-encode the categoricals in `raw`.** Send the label list once and integer
indices per row. It keeps the feed small enough to ship whole.

**Publish the limitations in the contract.** The test register from Stage 3b belongs
in the data, not hardcoded in a page. Then a page that displays a verdict is
displaying a measured result, and Section 13.2 is satisfied structurally rather than
by discipline.

**Check the size before shipping whole rows.** This technique works because a small
file can live in the browser. Measure it. Past roughly a megabyte, go back to
server-side aggregation and drop the cross-filtering.

### 14.2 The cross-filter engine

One filter set per dimension, a single function that applies them all, and a group-by
that every visual shares.

```js
function newFilters() {
  return { dimA: new Set(), dimB: new Set(), period: new Set() };
}

function filterRows(raw, f) {
  return raw.rows.filter(r =>
    (!f.dimA.size   || f.dimA.has(raw.dimA_values[r[1]])) &&
    (!f.dimB.size   || f.dimB.has(raw.dimB_values[r[2]])) &&
    (!f.period.size || f.period.has(r[0].slice(0, 7))));
}

function groupBy(rows, keyFn, order) { /* -> [{name, value, count}] */ }
```

An empty set means "no filter on this dimension", which makes the unfiltered case
free rather than special.

The page then holds one `filters` object, and every visual reads the same filtered
row set. A click anywhere mutates a set and calls one repaint. That single shared
row set is the whole trick; there is no synchronisation to get wrong.

### 14.3 The chart primitive library

Build these once in the shared runtime, hand-written SVG and CSS, and every page gets
them. The list below is what one full engagement actually needed.

| Primitive | Use it for | Notes |
|---|---|---|
| KPI tile | A single headline number | Optional inline sparkline for shape |
| Bar list | Ranked magnitude across one dimension | Direct value label on every row |
| Columns | A periodic series where single bars must read individually | Dashed mean line |
| Area and line | A continuous trend | Crosshair that snaps to the nearest point |
| Donut | Composition of a whole, up to about six parts | Total in the centre |
| Stacked bars | Composition compared across rows | Fixed colour per part, 2px gaps |
| Heatmap | Two dimensions against one measure | One sequential hue, per-cell labels |
| Dot and whisker | An estimate with its uncertainty | The honest way to show a ranking that is not stable |
| Scatter | Whether two measures move together | Fit the axes to the data, do not zero-base |
| Slicer | Selecting values of a dimension | Multi-select, with a clear control |

### 14.4 Data-bound prose

Give the runtime a small set of class hooks and fill them on every update:

```js
function bindLiveText(d) {
  const set = (sel, val) =>
    document.querySelectorAll(sel).forEach(n => { n.textContent = val; });
  set('.js-rows', fmt.int(d.row_count));
  set('.js-total', fmt.compact(d.kpis.total));
}
```

Then a headline reads
`across <span class="js-rows">1,000</span> transactions` and cannot go stale.

Leave genuinely static claims static. A sentence describing a completed study, such
as "a gap this size appears routinely when 1,000 rows are assigned at random", is
correctly frozen because it describes the study, not the file.

### 14.5 Keeping several pages consistent

When more than one person or process builds pages in parallel, fix the shared pieces
**first** and treat them as a contract: the JSON shape, the stylesheet tokens and
component classes, the runtime API, and the exact nav markup. Pages built afterwards
against a fixed contract look like one product. Pages built at the same time as the
contract do not.


### 14.6 Making the build dynamic: one codebase, any dataset

Nothing in Sections 14.1 to 14.5 is specific to a domain. The way to keep it that way
is to put every dataset-specific fact in one CONFIG block at the top of the watcher,
and to have everything downstream read the feed rather than hard-coded names.

```python
# ============ CONFIG - the only place a dataset is named ============
SOURCE_FILE   = HERE.parent / "01_Data" / "ADAPT_your_file.csv"
DATE_COLUMN   = "ADAPT_date_column"        # None if the dataset has no time dimension
VALUE_COLUMN  = "ADAPT_measure_column"     # the primary measure, what you sum
COUNT_COLUMN  = "ADAPT_secondary_count"    # None if there isn't one
DIMENSIONS    = ["ADAPT_dim_1", "ADAPT_dim_2"]   # the columns you slice by
BAND_COLUMN   = "ADAPT_numeric_to_band"    # None; a numeric column to bucket, e.g. age
BANDS         = [(0, 30, "under 30"), (30, 45, "30-44"), (45, 999, "45+")]
MATRIX_PAIR   = ("ADAPT_dim_1", "ADAPT_dim_2")   # the two dimensions for the heatmap
# ====================================================================
```

The watcher then builds the snapshot by iterating `DIMENSIONS` rather than naming
columns:

```python
snapshot["by_dimension"] = {
    dim: rank(group(rows, dim)) for dim in DIMENSIONS
}
snapshot["dimensions"] = DIMENSIONS          # the pages read this, not a literal list
snapshot["labels"] = {"measure": VALUE_COLUMN, "count": COUNT_COLUMN}
```

**The pages must then discover their dimensions from the feed.** A page that writes
`d.by_city` is welded to one dataset. A page that writes
`d.dimensions.forEach(dim => renderPanel(dim, d.by_dimension[dim]))` works on any of
them. This is the single change that turns a bespoke dashboard into a template.

The same applies to the slicers and to the cross-filter engine: build one slicer per
entry in `d.dimensions`, and hold filter sets in a map keyed by dimension name rather
than as named fields.

```js
function newFilters(dims) {
  const f = {};
  dims.forEach(d => { f[d] = new Set(); });
  return f;
}
function filterRows(raw, f) {
  return raw.rows.filter(r =>
    raw.dimensions.every((dim, i) =>
      !f[dim].size || f[dim].has(raw.lookups[dim][r[raw.dimIndex + i]])));
}
```

**Three things stay hand-authored per engagement, and should.** The headline sentence,
the page-specific insight above each chart, and the limitations text. Those are
editorial judgements about a particular business question, and generating them
mechanically is how a dashboard ends up saying "Revenue by City" where it should say
what the reader is supposed to conclude.

**What adapts automatically:** the number of dimensions and their names, the number
of values in each, the time grain, the colour assignment, the axis ranges, the KPI
tiles, the slicers, the tables, and every aggregate.

### 14.7 Choosing the page set for a new dataset

The page set follows the Dashboard Scope Brief (Section 5.6), not a fixed template.

| Page | Include when |
|---|---|
| Overview | Always. First in the nav. |
| Comprehensive, cross-filtered | The audience will explore rather than read, and the row-level feed is small enough to ship. |
| One drill-down per dimension | The scoping conversation confirmed that dimension matters. Not one per dimension that exists. |
| Data quality | Stage 1 found anything material, or Stage 3b returned null. On a weak dataset this page is mandatory. |

A dashboard with a page per available column is a data dump. Three well-chosen pages
beat eight mechanical ones.

---

## 15. Project Structure and Path Discipline

```
00_Method/        the playbook, the method and the spec
01_Data/          the source file; never written to by any script
02_Analysis/      the analysis scripts; every published figure comes from here
03_Dashboard/     watcher, shared runtime, shared styles, the pages
04_Deliverables/  the report generator and its output
```

State files stay at the project root so a session can resume from a cold start:
durable rules with their reasons, a current-state snapshot, and a session history.

**Scripts resolve paths from their own location, never from the working directory.**
The dashboard is served from one folder while the data lives in another, so anything
relying on `cd` breaks the moment it is run from elsewhere.

**Keep the generator, not just the artifact.** A PDF nobody can rebuild is a dead
document. The script that produces it belongs beside it in version control.

---

## 16. Pre-delivery Verification Checklist

Run this before declaring any dashboard done. Every item is a defect that actually
shipped and had to be caught.

**Correctness**

1. Re-derive every published figure from the analysis scripts. Do not trust a number
   because it appeared on screen.
2. Does any page state a statistical verdict that no test in the contract backs?
3. Does any page contradict another page of the same dashboard? Cross-check shared
   facts, especially counts and date coverage.
4. Does any prose hardcode a figure the feed can change? Perturb the source file and
   watch for a headline that now disagrees with the tiles beneath it.

**Robustness**

5. Does every render function guard against an empty or partial feed? An unguarded
   array access throws and blanks the page rather than degrading.
6. Does any element write to an id that a later `innerHTML` assignment destroys? This
   throws on every render after the first, mid-update, so the page half-repaints and
   the bug presents as "the feature does not work" rather than as an error.
7. Does the watcher survive a mid-save read of the source file?

**Presentation**

8. Does the page scroll horizontally at any width? Wide content scrolls inside its own
   container; the page never does. Watch for negative margins on full-bleed elements.
9. Does any label break mid-word, or any value split from its unit?
10. Is the palette validated in both light and dark mode?

**Method**

11. Visual inspection is not verification. It proves the charts draw. It does not
    prove the claims are true. Budget for a separate pass that re-derives the numbers
    and re-reads every sentence against the evidence.
12. Prefer an adversarial reviewer who did not build the thing. On the engagement
    behind this section, the author checked all pages in a browser, found them
    correct, and said so. An independent review then found two fabricated statistical
    claims, a factual error contradicting another page, and four banned phrasings.

**Consistency between deliverables**

13. After any finding changes, rebuild the report and diff its extracted text against
    the dashboard's claims. The dashboard regenerates from the feed on every change;
    the report only changes when its generator is re-run, so the report is the one that
    goes stale. See Section 19.4.

**Process**

14. Confirm a process is actually dead before assuming a file is current. A stale
    watcher holding pre-edit code in memory will quietly overwrite a newer snapshot.
15. Never have two writers edit one file at the same time. Two parallel agents editing
    one generator will clobber each other, and the result will satisfy neither brief.

---

## 17. Design Rules for charts

These hold regardless of design system. Validate the palette before writing chart
code, not after.

- **Validate the categorical palette in both light and dark mode** with a tool, not by
  eye. Check colour-blind separation, a lightness band, a chroma floor and contrast
  against the surface.
- **Categorical colour is for identity only.** Assign hues in a fixed order and never
  recycle them. A filter that changes how many series are shown must not repaint the
  survivors.
- **Magnitude uses one sequential hue,** light to dark. Ten cities ranked by revenue
  are a magnitude, not ten identities, so they get one blue ramp and not ten hues.
- **Ordered categories use the ordered ramp** too. Age bands are a scale.
- **Never a dual-axis chart.** Two measures on two y-scales invite a false reading.
  Use two charts or index both to a common base.
- **Direct value labels on every bar** when any palette slot falls below 3:1 contrast
  against the surface. The label is the relief, not decoration.
- **A legend whenever two or more series share a chart.** A single-series chart needs
  none; its title names it.
- **Every chart gets a hover tooltip and a table fallback.** The table is the
  accessible view and the one people copy figures out of.
- **Recessive chrome.** Hairline gridlines, no chart border, tabular numerals so
  digits align.
- **Fit scatter axes to the data range.** Zero-basing is right for bars and wrong for a
  scatter, where the question is whether the points fall on a line.

---

## 18. Applying this to a new dataset

The shortest honest path from a new file to a defensible product:

1. **Stage 0.** Classify the file and route it (Section 1).
2. **Stage 1.** Run the cleaning checklist (Section 2). Record that it passed. A clean
   bill of health is not fitness for purpose.
3. **Stage 2.** Model only if the path requires it (Section 3).
4. **Check that the columns mean what they are named.** Not in the original checklist,
   and the most valuable ten minutes in the pipeline. For every identifier, confirm it
   maps to one stable entity. For every measure, confirm it relates to the other
   measures the way its name implies. These failures are invisible in a header row and
   in any spot check of the first few rows.
5. **Stage 3.** Generate insights (Section 4), including the concentration check.
6. **Stage 3b.** Test every apparent difference (Section 10). If the register comes
   back null, run the seven-angle battery (Section 11) and the power analysis
   (Section 12).
7. **Stage 4.** Scope the dashboard (Section 5), proposing KPIs only from differences
   that survived Stage 3b. Get the brief approved.
8. **Stage 5.** Build (Sections 6, 7, 8, 14), applying the editorial rules (Section 13)
   if the data is weak.
9. **Verify** (Section 16), then demonstrate the live refresh with a timed edit.

> **Worked example, the whole path on a second dataset (MEASURED).** A flat 1,000-row
> retail file, Path A. Stage 1 passed all eight checks with zero defects. Step 4 found
> three broken columns: an identifier that appeared under more than one category for
> every one of its 100 values, a customer identifier with conflicting attributes on 258
> of 631 values, and a revenue column uncorrelated with the quantity beside it.
> Stage 3b returned nine null tests. The seven-angle battery returned seven more
> nulls, with Benford's law supplying forensic evidence that the values were generated.
> The power analysis specified the export that would work.
>
> The delivered product was a six-page live dashboard that reports the totals
> accurately, refuses to rank anything, and carries the caveat on every page, plus a
> report whose central recommendation is the sizing specification. That is a defensible
> outcome on a dataset that could not support the question originally asked, and it was
> reached without ever pretending otherwise.

---

## 19. The Client Report

The dashboard is for people who will explore. The report is for people who will
decide, and for the record. They need different documents, and the report is the one
that survives the engagement.

### 19.1 Structure it by the Pyramid Principle

Lead with the answer. Support it with a small number of grouped arguments. Put the
evidence underneath. A reader who stops after the first page must already have the
conclusion; a reader who continues must find each claim supported one level down.

```
                    THE ANSWER
                    one sentence, on page one
                          |
        +-----------------+-----------------+
        |                 |                 |
   ARGUMENT 1        ARGUMENT 2        ARGUMENT 3
   grouped, MECE, each independently sufficient
        |                 |                 |
    evidence          evidence          evidence
    tables, tests, measured figures
```

Three consequences for how the document is written:

- **The executive summary states the verdict, not the agenda.** "This dataset is
  technically flawless and analytically empty" is a summary. "This report assesses
  the dataset across several dimensions" is a table of contents pretending to be one.
- **Arguments are MECE.** Mutually exclusive so the reader never reads the same point
  twice, collectively exhaustive so there is no unstated fourth reason.
- **Evidence never leads.** A table that appears before the claim it supports makes
  the reader do the synthesis, which is the job you were hired for.

### 19.2 The ten-page architecture

This is the shape that worked, generalised. Each numbered section starts its own page,
so a section never splits and the document can be read in any order by someone who
only wants one part.

| Page | Section | What earns its place |
|---|---|---|
| 1 | Title, the verdict callout, the file at a glance, contents | The answer, before anything else |
| 2 | Executive summary | The verdict expanded, plus the questions the audience actually asked, each answered yes or no |
| 3 | How the assessment was run | The sequence, and the checks that passed. Method before findings, so findings are not read as opinion |
| 4 | Finding 1 | The most constraining finding, with the evidence per item and what each blocks |
| 5 | Finding 2 | The second finding, as a test register with statistics and p-values |
| 6 | Where the measure actually sits | The descriptive tables the business would recognise, each against its benchmark |
| 7 | Concentration, and how far we looked | Whether the distribution supports prioritisation, plus the breadth-of-search table |
| 8 | The two strongest pieces of evidence, in full | Whatever carries the most weight. Give it a whole page and say why |
| 9 | Time, and the specification | The temporal view, then the power analysis as a sizing spec |
| 10 | What may be published, recommendations, method | Scope, the numbered recommendations, and reproducibility |

Adapt the middle. Pages 1 to 3 and 10 are structural and hold for any engagement.

### 19.3 Rules that keep it client-grade

- **Every figure traceable.** Each number comes from a named script that can be
  re-run. Say so in the method section and name the commands.
- **Tag measured versus estimated.** A reader must never have to guess which is which.
- **A limitations section strengthens the document.** Stating plainly what the data
  cannot support is what makes the rest credible. Bury it and the whole report reads
  as advocacy.
- **Pair every piece of bad news with a specification.** "This will not work" is a
  finding. "Here is what would work, at this size, with these columns" is a
  deliverable. Section 12.
- **Keep the generator, not just the PDF.** A report nobody can rebuild is dead the
  first time a number changes.
- **One page, one job.** If a page repeats a point already made without adding a
  table, a figure or a new argument, cut it. Ten substantive pages beat sixteen padded
  ones, and a client can tell the difference immediately.

### 19.4 The report and the dashboard must agree

They are built from the same analysis scripts and they will still drift, because the
dashboard regenerates from the feed on every change while the report only changes when
its generator is re-run.

On the engagement behind this section the dashboard was corrected first, and the report
kept a factual error and two missing tests until someone asked whether it had been
updated. **After any finding changes, rebuild the report and diff its extracted text
against the dashboard's claims.** Put that in the verification checklist, not in
someone's memory.
