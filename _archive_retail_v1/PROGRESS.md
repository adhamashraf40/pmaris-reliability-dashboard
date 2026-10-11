# PROGRESS.md

Snapshot of where the AIB902 Sales Project actually is.
**Overwrite this file each session.** History lives in SESSION_LOG.md.

**Last refreshed:** 2026-09-19 (Session 5)
**Phase:** Build complete. Both deliverables shipped and verified.
**Path:** A (single flat table with a transaction-level date column)

---

## Gates

| Gate | Status | Notes |
|---|---|---|
| `dataset_classified` | **APPROVED** | Path A |
| `data_cleaned` | **APPROVED** | Full checklist, zero defects |
| `data_modeled` | NOT APPLICABLE | Path A needs naming only |
| `initial_insights` | **APPROVED** | Stage 3 plus a seven-angle deep battery |
| `scope_brief_approved` | **WAIVED BY USER** | The user directed the build without naming an audience. Built as an honest descriptive dashboard under that assumption. Audience and target decision are still unanswered. |
| `live_refresh_verified` | **PASSED** | Measured 103ms watcher latency, well inside the 1s target |

---

## The headline finding

The dataset is technically flawless and analytically empty. Eight cleaning checks
passed with zero defects. Seven independent tests of meaning all failed.

Benford's law is the forensic proof: leading digits reject Benford at p = 2e-90 and
instead match a flat random draw. Bootstrap resampling is the persuasive proof: every
city's 95% interval overlaps every other's, and the top city holds its rank in only
46% of 4,000 resamples.

**Consequence:** no prioritisation, forecast or ranking decision is supportable.

---

## What is built

| Artifact | Path | State |
|---|---|---|
| Method playbook | `00_Method/AIB902_...Playbook.md` | **v3.0**, Sections 10-19, 2,123 lines |
| Source dataset | `01_Data/sales_data_large.csv` | 1,000 rows, restored after live testing |
| Stage 1 + 3 analysis | `02_Analysis/analyze.py` | Reproducible, stdlib only |
| Seven-angle battery | `02_Analysis/analyze_deep.py` | Reproducible, stdlib only |
| Live dashboard | `03_Dashboard/` | **6 pages** incl. the cross-filtered Dashboard; watcher, shared CSS and runtime |
| Client report | `04_Deliverables/Sales_Data_Quality_Assessment.pdf` | **10 pages**, verified, ready to send |
| Report generator | `04_Deliverables/make_report.py` | Rebuilds the PDF |
| Guidance and state | `CLAUDE.md`, `README.md`, and the three state files | Current |

## Dashboard pages

Overview, Categories, Geography, Customers, Data quality. One watcher, one
`live_data.json`, one stylesheet, one runtime. No framework, no CDN, no build step.

---

## Verification performed

- All five pages loaded in a real browser and visually inspected.
- Zero console errors. `node --check` passes on the shared runtime.
- No external resource references of any kind.
- Palette validated in both light and dark mode before any chart was written.
- Live refresh: appended a row, watcher rewrote the snapshot in 103ms, pages updated.
- One defect found and fixed: the Overview headline was static and contradicted the
  live tiles after the data changed. Prose figures are now data-bound.

---

## Reusable template

`C:/Users/hp/Downloads/Analytics_Project_Template/` holds this engagement turned into a
dataset-agnostic starting point: the playbook, CONFIG-driven analysis scripts, the
watcher and its contract, the shared runtime and stylesheet, three dashboard pages, the
report generator, and a ten-step getting-started guide. Future analytics projects start
there, not from this folder.

## Next step, concretely

Nothing is blocked on work. The project is delivered and waiting on decisions.

## Open decisions waiting on the user

1. **Who is the audience, and what one decision should this drive?** Still unanswered.
   It does not block the build any more, but it determines whether the deliverables
   are the right ones.
2. **Send the PDF to the company, or hold it?** It is ready either way.
3. **Request a production export?** Recommendation 4 in the PDF specifies what would
   be needed: about 6,000 rows to detect a 20% city difference, plus a cost column
   and stable product and customer keys.
4. **Does the dashboard need to ship anywhere,** or is local serving enough?
