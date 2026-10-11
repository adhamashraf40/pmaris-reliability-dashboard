# -*- coding: utf-8 -*-
"""
Live Decision Dashboard - watcher script (PMARIS asset-reliability dataset).

Watches Group_9230_Team1_PMARIS_Enterprise_Dataset.csv and rewrites
live_data.json whenever the file changes. Every dashboard page polls
live_data.json once per second, so an edit to the source file appears on
screen in well under a second.

Zero external dependencies - Python standard library only (csv, json).
The JSON shape build_snapshot() returns is the contract the pages expect.
Change the writer, change the reader.

Study constants (significance register, bootstrap intervals) are read once
from ../02_Analysis/findings.json, produced by analyze_pmaris.py. They are
published under "study" with the row count they were measured on, so the
pages can warn when the live file no longer matches the study.

Run:
    python watcher.py
Then in a second terminal, from this same folder:
    python -m http.server 8000
Then open http://localhost:8000/index.html

Live Refresh Verification (checkpoint D3): with both running, edit or append
a row in the CSV, save, and watch the dashboard update. Target under 1 second.
"""

import csv
import json
import time
import datetime
import collections
from pathlib import Path

HERE = Path(__file__).resolve().parent

# ============ CONFIG - the only place the dataset is named ============
SOURCE_FILE = HERE.parent / "01_Data" / "Group_9230_Team1_PMARIS_Enterprise_Dataset.csv"
FINDINGS_FILE = HERE.parent / "02_Analysis" / "findings.json"
OUTPUT_FILE = HERE / "live_data.json"
STAMP_FILE = HERE / "live_stamp.json"   # tiny file the pages poll fast; they fetch live_data.json only when it changes
POLL_SECONDS = 0.3   # well under 1s so poll + page fetch stays inside the 1s target

DATE_COLUMN = "Observation_Date"
DIMENSIONS = ["Site", "Maintenance_Strategy", "Spare_Parts_Status", "Criticality_Class",
              "Technician_Skill_Level", "Environment_Severity", "Asset_Class",
              "Failure_Mode_Group", "Operating_Shift", "Manufacturer_Group"]
# Ordinal dimensions keep their natural order; everything else sorts by measure
ORDERS = {
    "Maintenance_Strategy": ["Reactive", "Preventive", "Condition-Based", "Predictive"],
    "Spare_Parts_Status": ["Shortage", "Limited", "Available"],
    "Criticality_Class": ["Critical", "High", "Medium", "Low"],
    "Technician_Skill_Level": ["Basic", "Intermediate", "Advanced", "Expert"],
    "Environment_Severity": ["Severe", "Harsh", "Moderate", "Controlled"],
    "Operating_Shift": ["Day", "Evening", "Night"],
    "Executive_Intervention_Priority": ["P1 - Immediate", "P2 - High", "P3 - Planned", "P4 - Monitor"],
}
HIGH_RISK_PCT = 50.0
ESCALATED = ("P1 - Immediate", "P2 - High")
MEASURES = {  # short key -> source column
    "downtime": "Unplanned_Downtime_Hours_30D",
    "loss": "Revenue_Loss_EGP_30D",
    "fp": "Failure_Probability_Pct",
    "health": "Asset_Health_Index",
    "exposure": "Financial_Exposure_At_Risk_EGP",
    "cost": "Maintenance_Cost_EGP_30D",
    "pm": "Preventive_Maintenance_Compliance_Pct",
    "backlog": "Maintenance_Backlog_Days",
    "spare": "Spare_Parts_Cost_EGP_30D",
    "labor": "Labor_Hours_30D",
}
# ====================================================================


def load_rows(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    clean = []
    for r in rows:
        try:
            for col in MEASURES.values():
                r[col] = float(r[col])
            datetime.date.fromisoformat(r[DATE_COLUMN])
        except (ValueError, KeyError, TypeError):
            continue   # a half-typed row during a live edit is skipped, not fatal
        fm = r.get("Failure_Mode_Category", "")
        r["Failure_Mode_Group"] = fm if fm in ("General Mechanical", "Bearing / Vibration", "Lubrication") \
            else "Other (sensor / hydraulic / heat)"
        clean.append(r)
    return clean


def load_study():
    try:
        return json.loads(FINDINGS_FILE.read_text())
    except (OSError, ValueError):
        return None


def _mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def _profile(rs):
    n = len(rs)
    return {
        "n": n,
        "downtime_mean": round(_mean([r[MEASURES["downtime"]] for r in rs]), 3),
        "loss_mean": round(_mean([r[MEASURES["loss"]] for r in rs]), 1),
        "loss_total": round(sum(r[MEASURES["loss"]] for r in rs), 0),
        "fp_mean": round(_mean([r[MEASURES["fp"]] for r in rs]), 2),
        "health_mean": round(_mean([r[MEASURES["health"]] for r in rs]), 2),
        "cost_mean": round(_mean([r[MEASURES["cost"]] for r in rs]), 1),
        "spare_mean": round(_mean([r[MEASURES["spare"]] for r in rs]), 1),
        "labor_mean": round(_mean([r[MEASURES["labor"]] for r in rs]), 2),
        "high_risk_pct": round(100 * sum(1 for r in rs if r[MEASURES["fp"]] >= HIGH_RISK_PCT) / n, 2) if n else 0,
        "emergency_pct": round(100 * sum(1 for r in rs if r.get("Work_Order_Type") == "Corrective Emergency") / n, 2) if n else 0,
    }


def build_snapshot(rows, study):
    n = len(rows)
    loss = [r[MEASURES["loss"]] for r in rows]
    hr = [r for r in rows if r[MEASURES["fp"]] >= HIGH_RISK_PCT]
    total_loss = sum(loss) or 1.0
    total_dt = sum(r[MEASURES["downtime"]] for r in rows) or 1.0
    gap = [r for r in hr if r.get("Executive_Intervention_Priority") not in ESCALATED]
    srt = sorted(loss, reverse=True)
    top10 = sum(srt[: max(1, n // 10)]) / total_loss

    kpis = {
        "observations": n,
        "loss_mean": _mean(loss),
        "loss_total": sum(loss),
        "downtime_mean": _mean([r[MEASURES["downtime"]] for r in rows]),
        "downtime_total": total_dt,
        "high_risk_n": len(hr),
        "high_risk_pct": 100 * len(hr) / n if n else 0,
        "high_risk_loss_share": 100 * sum(r[MEASURES["loss"]] for r in hr) / total_loss,
        "high_risk_downtime_share": 100 * sum(r[MEASURES["downtime"]] for r in hr) / total_dt,
        "escalation_gap": len(gap),
        "escalation_gap_exposure": sum(r[MEASURES["exposure"]] for r in gap),
        "rule_adds": sum(1 for r in gap if r.get("Criticality_Class") in ("High", "Critical")),
        "escalated_n": sum(1 for r in rows if r.get("Executive_Intervention_Priority") in ESCALATED),
        "health_mean": _mean([r[MEASURES["health"]] for r in rows]),
        "pm_mean": _mean([r[MEASURES["pm"]] for r in rows]),
        "exposure_total": sum(r[MEASURES["exposure"]] for r in rows),
        "cost_total": sum(r[MEASURES["cost"]] for r in rows),
        "cost_mean": _mean([r[MEASURES["cost"]] for r in rows]),
        "spare_total": sum(r[MEASURES["spare"]] for r in rows),
        "loss_to_cost": sum(loss) / (sum(r[MEASURES["cost"]] for r in rows) or 1.0),
        "top10_loss_share": 100 * top10,
    }

    by_dim = {}
    for dim in DIMENSIONS:
        g = collections.defaultdict(list)
        for r in rows:
            g[r.get(dim, "")].append(r)
        lst = [dict(name=k, **_profile(v)) for k, v in g.items()]
        if dim in ORDERS:
            order = ORDERS[dim]
            lst.sort(key=lambda x: order.index(x["name"]) if x["name"] in order else 99)
        else:
            lst.sort(key=lambda x: -x["loss_mean"])
        by_dim[dim] = lst

    mon = collections.defaultdict(list)
    for r in rows:
        mon[r[DATE_COLUMN][:7]].append(r)
    trend = [dict(period=k, **_profile(v)) for k, v in sorted(mon.items())]

    pri = collections.Counter(r.get("Executive_Intervention_Priority", "") for r in rows)
    priority = [{"name": p, "n": pri.get(p, 0)} for p in ORDERS["Executive_Intervention_Priority"]]

    # Escalation-gap watchlist: high-risk, not escalated, ranked by exposure
    gap.sort(key=lambda r: -r[MEASURES["exposure"]])
    watch_cols = ["Observation_ID", "Asset_ID", DATE_COLUMN, "Site", "Asset_Type", "Criticality_Class",
                  "Maintenance_Strategy", "Spare_Parts_Status", "Executive_Intervention_Priority"]
    watchlist = [dict({c: r.get(c, "") for c in watch_cols},
                      fp=r[MEASURES["fp"]], health=r[MEASURES["health"]],
                      downtime=r[MEASURES["downtime"]], exposure=r[MEASURES["exposure"]])
                 for r in gap[:40]]

    # PM-compliance deciles and health bands (the lever curves)
    pm_sorted = sorted(rows, key=lambda r: r[MEASURES["pm"]])
    deciles = []
    for i in range(10):
        part = pm_sorted[i * n // 10:(i + 1) * n // 10]
        if part:
            deciles.append({"name": f"D{i+1}",
                            "pm_median": sorted(r[MEASURES["pm"]] for r in part)[len(part) // 2],
                            **_profile(part)})
    bands = []
    for lo, hi, nm in [(0, 70, "Under 70"), (70, 80, "70-79"), (80, 90, "80-89"), (90, 101, "90+")]:
        part = [r for r in rows if lo <= r[MEASURES["health"]] < hi]
        if part:
            bands.append(dict(name=nm, **_profile(part)))

    # Compact, index-encoded row-level feed for the cross-filtered page
    lookups = {d: [x["name"] for x in by_dim[d]] for d in DIMENSIONS}
    pri_lookup = ORDERS["Executive_Intervention_Priority"]
    months = [t["period"] for t in trend]
    raw_rows = []
    for r in rows:
        raw_rows.append(
            [months.index(r[DATE_COLUMN][:7])]
            + [lookups[d].index(r.get(d, "")) for d in DIMENSIONS]
            + [round(r[MEASURES["downtime"]], 2), round(r[MEASURES["loss"]]), r[MEASURES["fp"]],   # unrounded: rounding moves rows across the 50% threshold
               round(r[MEASURES["health"]], 1), round(r[MEASURES["exposure"]]),
               pri_lookup.index(r["Executive_Intervention_Priority"])
               if r.get("Executive_Intervention_Priority") in pri_lookup else 3]
        )
    raw = {"fields": ["month"] + DIMENSIONS + ["downtime", "loss", "fp", "health", "exposure", "priority"],
           "months": months, "dimensions": DIMENSIONS, "lookups": lookups,
           "priorities": pri_lookup, "rows": raw_rows}

    snap = {
        "last_updated": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="milliseconds"),
        "source_file": SOURCE_FILE.name,
        "row_count": n,
        "date_min": min((r[DATE_COLUMN] for r in rows), default=""),
        "date_max": max((r[DATE_COLUMN] for r in rows), default=""),
        "high_risk_threshold": HIGH_RISK_PCT,
        "kpis": kpis,
        "trend": trend,
        "dimensions": DIMENSIONS,
        "orders": ORDERS,
        "by_dimension": by_dim,
        "priority": priority,
        "lever_pm_deciles": deciles,
        "lever_health_bands": bands,
        "watchlist": watchlist,
        "raw": raw,
    }
    if study:
        snap["study"] = {
            "row_count": study["stage0"]["rows"],
            "register": study["register"],
            "register_meta": study["register_meta"],
            "bootstrap": study["bootstrap"],
            "levers": {k: v for k, v in study["levers"].items() if k not in ("pm_deciles", "health_bands")},
            "stage1": study["stage1"],
            "concentration": {k: v for k, v in study["concentration"].items()},
            "watchlist": {k: v for k, v in study["watchlist"].items() if k != "top"},
        }
    return snap


def main():
    print(f"Watching {SOURCE_FILE.name} -> {OUTPUT_FILE.name} every {POLL_SECONDS}s. Ctrl+C to stop.")
    last_mtime = None
    study = load_study()
    if not study:
        print("note: findings.json not found - run 02_Analysis/analyze_pmaris.py for study constants")
    while True:
        try:
            mtime = SOURCE_FILE.stat().st_mtime
            if mtime != last_mtime:
                t0 = time.perf_counter()
                rows = load_rows(SOURCE_FILE)
                if not rows:
                    raise ValueError("no parseable rows")
                snap = build_snapshot(rows, study)
                tmp = OUTPUT_FILE.with_suffix(".tmp")
                tmp.write_text(json.dumps(snap, separators=(",", ":")))
                tmp.replace(OUTPUT_FILE)   # atomic, so a page never reads half a file
                STAMP_FILE.write_text(json.dumps({"last_updated": snap["last_updated"], "row_count": snap["row_count"]}))
                last_mtime = mtime
                ms = (time.perf_counter() - t0) * 1000
                print(f"[{snap['last_updated']}] source changed -> live_data.json rewritten "
                      f"({snap['row_count']} rows, {ms:.0f} ms)", flush=True)
        except FileNotFoundError:
            print(f"Waiting for {SOURCE_FILE.name} to exist...")
        except Exception as exc:  # noqa: BLE001 - keep polling through a bad mid-save read
            print(f"Skipped a snapshot (source mid-write or malformed): {exc}", flush=True)
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
