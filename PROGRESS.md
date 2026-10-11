# PROGRESS.md

Snapshot of where the project actually is.
**Overwrite this file each session.** History lives in SESSION_LOG.md.

**Last refreshed:** 2026-10-11 (Session 6)
**Dataset:** `01_Data/Group_9230_Team1_PMARIS_Enterprise_Dataset.csv` (PMARIS asset reliability)
**Phase:** Build complete. Dashboard live and verified; report, deck and playbook v4.0 shipped.
**Path:** A (single flat table with a date column; Asset_ID is not an entity key)

---

## Gates

| Gate | Status | Notes |
|---|---|---|
| `dataset_classified` | **APPROVED** | Path A, 5,000 × 60 |
| `data_cleaned` | **APPROVED** | Zero defects; nothing dropped; tail and overload kept |
| `columns_mean_what_they_say` | **DONE** | Asset_ID broken; exposure, FP and priority are derived |
| `initial_insights` | **APPROVED** | Concentration 44.7% in top decile |
| `significance_register` | **DONE** | 26 of 33 survive Bonferroni + Kruskal-Wallis |
| `scope_brief_approved` | **APPROVED BY USER** | Interview answered 2026-10-11, see brief below |
| `live_refresh_verified` | **PASSED** | 10 timed edits: 376 ms mean, 621 ms max |

## The approved Dashboard Scope Brief

- **Audience:** Head of Reliability & Maintenance across the six sites.
- **Decision:** where to put the next EGP: which controllable lever, and which windows to escalate.
- **KPIs:** mean revenue loss per window; mean unplanned downtime; high-risk share and the share of loss it carries; escalation gap.
- **Refresh:** live, with the full page set.
- **Headline:** the next EGP belongs on the controllable levers and on the escalation list.
- **Pages:** Overview, Explorer, Levers, Sites & Equipment, Risk Watchlist, Data & Method.
- **Through-line:** loss is concentrated and tracks what management controls, not where an asset sits.

## What is built

| Artifact | Path | State |
|---|---|---|
| Method playbook | `00_Method/AIB902_...Playbook.md` | **v4.0**, Part III (§20–25) added, 2,311 lines |
| Analysis | `02_Analysis/analyze_pmaris.py` → `findings.json` | Reproducible, stdlib only, ~90 s |
| Live dashboard | `03_Dashboard/` | 6 pages, watcher + stamp file, verified in light, dark and 390 px |
| Figures | `04_Deliverables/make_figures.py` → `figures/` | 18 charts + 4 dashboard screenshots |
| Client report | `04_Deliverables/PMARIS_Reliability_Assessment.pdf` | 10 pages, Pyramid structure |
| Slide deck | `04_Deliverables/PMARIS_Reliability_Deck.pptx` | 30 slides, native charts, notes on every slide, OOXML validator passes |
| Executive presentation | `04_Deliverables/PMARIS_Executive_Presentation.pptx` | 15 slides, subset of the full deck, validator passes |
| Comprehensive report | `04_Deliverables/PMARIS_Comprehensive_Analytical_Report.pdf` | 25 pages, 22 sections + appendix |
| Previous engagement | `_archive_retail_v1/` | Untouched copy of the retail-era files |

## Verification performed

- All six pages rendered headless (Chromium) in light, dark and 390 px: zero console errors, no horizontal scroll.
- Live refresh: 10 appended rows timed save-to-screen; source restored byte-identical (SHA-1 checked).
- Mid-save robustness: a truncated row was appended; the watcher skipped it and kept polling.
- Report: 10 pages, rendered and inspected. Deck: OOXML validator passes; text-fit checker reports no overflow.
- Defects found and fixed this session: hidden notices rendering as empty boxes; FP rounding moving 2 rows across the 50% threshold; 1 s poll missing the D3 target (972 ms mean); an untested "equipment mix" claim on the Sites page; the Watchlist notice describing the table as the rule's additions when it was not.

## Not verified

- The deck was not opened in PowerPoint or rendered by LibreOffice (neither is installed). Layout was checked with an approximate renderer and Arial metrics; open it in PowerPoint once before presenting.

## Open decisions waiting on the user

1. Approve the reactive-to-planned **pilot** (one site, one matched control).
2. Approve the **second escalation trigger** after a crew-capacity check (134 → 567 escalated windows).
3. Request a **stable Asset_ID** in the next export.
4. Does the dashboard need hosting beyond local serving?
