# -*- coding: utf-8 -*-
"""
Live Decision Dashboard - watcher script.

Watches sales_data_large.csv and rewrites live_data.json whenever the file
changes. Every dashboard page polls live_data.json once per second, so an edit
to the source file appears on screen in well under a second.

Zero external dependencies - Python standard library only (csv, json).
If you repoint this at an .xlsx source, add an openpyxl read path in
load_rows(); the JSON shape build_snapshot() produces is the contract the
dashboard pages expect and must not change.

Run:
    python watcher.py
Then in a second terminal, from this same folder:
    python -m http.server 8000
Then open http://localhost:8000/index.html

Live Refresh Verification (checkpoint D3): with both running, open
sales_data_large.csv, change or add a row, save, and watch the dashboard
update. Target is under 1 second.
"""

import csv
import json
import time
import datetime
import collections
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE_FILE = HERE.parent / "01_Data" / "sales_data_large.csv"
OUTPUT_FILE = HERE / "live_data.json"
POLL_SECONDS = 0.3   # well under 1s so poll + page fetch stays inside the 1s target

CATEGORY_ORDER = ["Apparel", "Beauty", "Books", "Electronics", "Home Decor"]
AGE_BANDS = ["18-29", "30-39", "40-49", "50-59", "60+"]
DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def load_rows(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def age_band(age):
    a = int(age)
    if a < 30:
        return "18-29"
    if a < 40:
        return "30-39"
    if a < 50:
        return "40-49"
    if a < 60:
        return "50-59"
    return "60+"


def _rank(d, total):
    out = [{"name": k, "revenue": int(round(v["rev"])), "lines": v["n"],
            "units": v["u"], "share": round(v["rev"] / total, 4) if total else 0}
           for k, v in d.items()]
    out.sort(key=lambda x: -x["revenue"])
    return out


def build_snapshot(rows):
    total_rev = 0.0
    total_units = 0

    def bucket():
        return collections.defaultdict(lambda: {"rev": 0.0, "n": 0, "u": 0})

    cat, city, gender, band, month, dow = (bucket() for _ in range(6))
    matrix = collections.defaultdict(float)
    cats_seen, cities_seen = set(), set()

    for r in rows:
        rev = float(r["SalesRevenue"])
        units = int(r["QuantitySold"])
        total_rev += rev
        total_units += units

        c, ct = r["ProductCategory"], r["CustomerLocation"]
        g, b = r["CustomerGender"], age_band(r["CustomerAge"])
        m = r["SalesDate"][:7]
        wd = DOW[datetime.date.fromisoformat(r["SalesDate"]).weekday()]

        for d, k in ((cat, c), (city, ct), (gender, g), (band, b), (month, m), (dow, wd)):
            d[k]["rev"] += rev
            d[k]["n"] += 1
            d[k]["u"] += units

        matrix[(c, ct)] += rev
        cats_seen.add(c)
        cities_seen.add(ct)

    n = len(rows)
    cat_list = _rank(cat, total_rev)
    city_list = _rank(city, total_rev)

    # concentration: share held by the top tenth of each dimension
    def top_decile(ranked):
        if not ranked:
            return 0.0
        k = max(1, round(len(ranked) * 0.10))
        return round(sum(x["share"] for x in ranked[:k]), 4)

    cats = sorted(cats_seen, key=lambda x: (CATEGORY_ORDER.index(x)
                                            if x in CATEGORY_ORDER else 99, x))
    cities = [c["name"] for c in city_list]

    # Compact row-level feed. 1,000 rows is small enough to ship whole, which is
    # what lets the comprehensive page cross-filter client-side without a server
    # round trip. Categoricals are sent as indices into the lookup lists.
    cat_ix = {c: i for i, c in enumerate(cats)}
    city_ix = {c: i for i, c in enumerate(cities)}
    gender_vals = sorted({r["CustomerGender"] for r in rows})
    gen_ix = {g: i for i, g in enumerate(gender_vals)}
    raw = [[r["SalesDate"],
            cat_ix.get(r["ProductCategory"], -1),
            city_ix.get(r["CustomerLocation"], -1),
            gen_ix.get(r["CustomerGender"], -1),
            int(r["CustomerAge"]),
            int(r["QuantitySold"]),
            int(round(float(r["SalesRevenue"])))]
           for r in rows]

    return {
        "last_updated": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "row_count": n,
        "raw": {
            "fields": ["date", "cat", "city", "gender", "age", "qty", "rev"],
            "cats": cats,
            "cities": cities,
            "genders": gender_vals,
            "age_bands": AGE_BANDS,
            "rows": raw,
        },
        "kpis": {
            "total_revenue": int(round(total_rev)),
            "total_units": total_units,
            "transactions": n,
            "avg_transaction": int(round(total_rev / n)) if n else 0,
            "active_days": len({r["SalesDate"] for r in rows}),
            "categories": len(cats_seen),
            "cities": len(cities_seen),
        },
        "trend": [{"month": k, "revenue": int(round(v["rev"])), "lines": v["n"]}
                  for k, v in sorted(month.items())],
        "by_category": cat_list,
        "by_city": city_list,
        "by_gender": _rank(gender, total_rev),
        "by_age_band": sorted(_rank(band, total_rev),
                              key=lambda x: AGE_BANDS.index(x["name"])
                              if x["name"] in AGE_BANDS else 99),
        "by_weekday": sorted(_rank(dow, total_rev),
                             key=lambda x: DOW.index(x["name"]) if x["name"] in DOW else 99),
        "matrix": {
            "categories": cats,
            "cities": cities,
            "values": [[int(round(matrix[(c, ct)])) for ct in cities] for c in cats],
        },
        "concentration": {
            "top_decile_cities": top_decile(city_list),
            "top_decile_categories": top_decile(cat_list),
            "even_split_cities": round(1 / len(cities), 4) if cities else 0,
            "even_split_categories": round(1 / len(cats), 4) if cats else 0,
        },
        # Static, from analyze.py and analyze_deep.py. Surfaced so the dashboard
        # can never present this data as if it were decision-grade.
        "limitations": {
            "headline": "Every difference on this page is inside the range random "
                        "variation produces. Read the totals, not the rankings.",
            "tests": [
                {"test": "Revenue by category", "result": "chi-square p = 0.57", "verdict": "no signal"},
                {"test": "Revenue by city", "result": "chi-square p = 0.72", "verdict": "no signal"},
                {"test": "Revenue by gender", "result": "chi-square p = 0.61", "verdict": "no signal"},
                {"test": "Revenue by age band", "result": "chi-square p = 0.44", "verdict": "no signal"},
                {"test": "Revenue by weekday", "result": "chi-square p = 0.45", "verdict": "no signal"},
                {"test": "Category x city interaction", "result": "permutation p = 0.18", "verdict": "no signal"},
                {"test": "Best vs worst city gap", "result": "matched by chance 35% of the time", "verdict": "noise"},
                {"test": "Month-on-month trend", "result": "+0.46% of an average month", "verdict": "flat"},
                {"test": "Benford's law on revenue", "result": "rejected, p = 2e-90", "verdict": "generated"},
            ],
            "blocked": [
                "Named product or customer analysis: ProductID and CustomerID are not stable keys",
                "Profit and margin: there is no cost column",
                "Unit price and basket value: revenue is uncorrelated with quantity",
                "Repeat purchase and churn: follows from the CustomerID failure",
                "Forecasting and prioritisation: there is no trend and no concentration",
            ],
        },
    }


def main():
    print(f"Watching {SOURCE_FILE.name} -> writing {OUTPUT_FILE.name}")
    print(f"Polling every {POLL_SECONDS}s. Ctrl+C to stop.")
    last = None
    while True:
        try:
            mtime = SOURCE_FILE.stat().st_mtime
            if mtime != last:
                snap = build_snapshot(load_rows(SOURCE_FILE))
                OUTPUT_FILE.write_text(json.dumps(snap, indent=2), encoding="utf-8")
                last = mtime
                print(f"[{snap['last_updated']}] source changed -> {OUTPUT_FILE.name} "
                      f"rewritten ({snap['row_count']} rows, "
                      f"{snap['kpis']['total_revenue']:,} revenue)")
        except FileNotFoundError:
            print(f"Waiting for {SOURCE_FILE.name} to exist...")
        except Exception as exc:  # noqa: BLE001 - keep polling through a mid-save read
            print(f"Skipped a snapshot (source mid-write or malformed): {exc}")
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
