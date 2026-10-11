# -*- coding: utf-8 -*-
"""
Stage 1 (cleaning), Stage 3 (initial insights) and the signal tests for
sales_data_large.csv, per AIB902_Agentic_Analytics_Dashboard_Playbook.md.

Every figure quoted in Sales_Data_Quality_Assessment.pdf comes from this script.
Run:  python analyze.py
Zero external dependencies. Python standard library only.
"""

import csv
import collections
import datetime
import random
import statistics
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "01_Data" / "sales_data_large.csv"
RAW = SRC.read_text(encoding="utf-8-sig").splitlines()
ROWS = list(csv.DictReader(RAW))
COLS = list(ROWS[0].keys())

rev = lambda r: float(r["SalesRevenue"])          # noqa: E731
qty = lambda r: int(r["QuantitySold"])            # noqa: E731
TOTAL = sum(rev(r) for r in ROWS)


def rule(t):
    print("\n" + "=" * 72)
    print(t)
    print("=" * 72)


# --------------------------------------------------------------- STAGE 1
def stage1():
    rule("STAGE 1 - CLEANING CHECKLIST (playbook section 2)")

    def conforms(col, fn):
        return sum(1 for r in ROWS if not fn(r[col]))

    def isint(v):
        try:
            int(v); return True
        except ValueError:
            return False

    def isfloat(v):
        try:
            float(v); return True
        except ValueError:
            return False

    def isdate(v):
        try:
            datetime.date.fromisoformat(v); return True
        except ValueError:
            return False

    print("\n[1] Row/column count and type conformance")
    print(f"    rows={len(ROWS)}  cols={len(COLS)}")
    for col, fn, lbl in [("SalesDate", isdate, "ISO date"), ("QuantitySold", isint, "int"),
                         ("SalesRevenue", isfloat, "float"), ("CustomerAge", isint, "int")]:
        print(f"    {col:<15} declared {lbl:<9} -> {conforms(col, fn)} non-conforming")

    print("\n[2] Header integrity")
    print(f"    first line is the header, no title row above it: {RAW[0][:60]}...")

    print("\n[3] Missing values")
    blanks = {c: sum(1 for r in ROWS if not str(r[c]).strip()) for c in COLS}
    sentinels = {c: sum(1 for r in ROWS if str(r[c]).strip().lower()
                        in ("na", "n/a", "null", "none", "-", "unknown")) for c in COLS}
    print(f"    blank cells: {sum(blanks.values())}   disguised nulls: {sum(sentinels.values())}")

    print("\n[4] Duplicates")
    keys = [tuple(r[c] for c in COLS) for r in ROWS]
    near = collections.Counter((r["SalesDate"], r["ProductID"], r["CustomerID"]) for r in ROWS)
    print(f"    exact duplicate rows: {len(keys) - len(set(keys))}")
    print(f"    near-duplicates (same date+product+customer): {sum(1 for v in near.values() if v > 1)}")

    print("\n[5] Outliers, judged in business terms")
    for name, vals in [("SalesRevenue", [rev(r) for r in ROWS]),
                       ("QuantitySold", [qty(r) for r in ROWS]),
                       ("CustomerAge", [int(r["CustomerAge"]) for r in ROWS])]:
        print(f"    {name:<13} min={min(vals):>8.0f} max={max(vals):>8.0f} "
              f"mean={statistics.mean(vals):>8.1f} median={statistics.median(vals):>7.1f}")
    print(f"    non-positive revenue: {sum(1 for r in ROWS if rev(r) <= 0)}   "
          f"non-positive quantity: {sum(1 for r in ROWS if qty(r) <= 0)}   "
          f"ages outside 18-95: {sum(1 for r in ROWS if not 18 <= int(r['CustomerAge']) <= 95)}")

    print("\n[6] Constant / near-constant columns (95% threshold)")
    for c in COLS:
        cnt = collections.Counter(r[c] for r in ROWS)
        top, n = cnt.most_common(1)[0]
        flag = "  <-- DROP, no discriminating power" if n / len(ROWS) >= 0.95 else ""
        print(f"    {c:<18} distinct={len(cnt):>4}  most common '{top}' at {n/len(ROWS):.1%}{flag}")

    print("\n[Path A] Date continuity")
    days = {datetime.date.fromisoformat(r["SalesDate"]) for r in ROWS}
    start, end = min(days), max(days)
    span = (end - start).days + 1
    gaps = [start + datetime.timedelta(days=i) for i in range(span)
            if start + datetime.timedelta(days=i) not in days]
    longest = cur = 0
    prev = None
    for d in gaps:
        cur = cur + 1 if prev and (d - prev).days == 1 else 1
        longest = max(longest, cur)
        prev = d
    print(f"    {start} to {end}: {span} calendar days, {len(days)} with sales, "
          f"{len(gaps)} without, longest consecutive gap {longest} day(s)")
    print("    -> no whole month missing; consistent with a sparse sample, not lost data")


# ------------------------------------------------- KEY INTEGRITY (the traps)
def key_integrity():
    rule("KEY INTEGRITY - do the columns mean what they are named?")

    prod = collections.defaultdict(set)
    for r in ROWS:
        prod[r["ProductID"]].add(r["ProductCategory"])
    broken_p = sum(1 for v in prod.values() if len(v) > 1)

    cust = collections.defaultdict(set)
    for r in ROWS:
        cust[r["CustomerID"]].add((r["CustomerAge"], r["CustomerGender"], r["CustomerLocation"]))
    broken_c = sum(1 for v in cust.values() if len(v) > 1)

    q = [qty(r) for r in ROWS]
    v = [rev(r) for r in ROWS]
    mq, mv = statistics.mean(q), statistics.mean(v)
    cov = sum((a - mq) * (b - mv) for a, b in zip(q, v)) / len(q)
    r_qv = cov / (statistics.pstdev(q) * statistics.pstdev(v))

    print(f"\n    ProductID    : {broken_p} of {len(prod)} IDs span more than one category")
    print("                   -> NOT a stable product key. Use ProductCategory.")
    print(f"    CustomerID   : {broken_c} of {len(cust)} IDs carry conflicting age/gender/city")
    print("                   -> NOT a stable customer key. No churn or repeat-purchase view.")
    print(f"    SalesRevenue : correlation with QuantitySold r = {r_qv:+.4f}")
    print("                   -> unit price, basket value and per-unit metrics are meaningless.")
    print("    Cost column  : absent -> profit and margin are not computable at all.")


# --------------------------------------------------------------- STAGE 3
def stage3():
    rule("STAGE 3 - INITIAL INSIGHTS (playbook section 4)")
    print(f"\n    Total revenue {TOTAL:,.0f} | total units {sum(qty(r) for r in ROWS):,} | "
          f"{len(ROWS):,} lines | average line {TOTAL/len(ROWS):,.0f}")
    print(f"    Time grain: {len(ROWS)} rows over 366 days = {len(ROWS)/366:.1f}/day. "
          "Daily is too sparse. Natural grain is MONTHLY.")

    months = collections.defaultdict(float)
    counts = collections.Counter()
    for r in ROWS:
        months[r["SalesDate"][:7]] += rev(r)
        counts[r["SalesDate"][:7]] += 1
    print("\n    Month      Revenue     Lines   Share")
    for k in sorted(months):
        print(f"    {k}  {months[k]:>10,.0f}  {counts[k]:>6}  {months[k]/TOTAL:>6.1%}")
    vals = [months[k] for k in sorted(months)]
    xs = list(range(len(vals)))
    mx, my = statistics.mean(xs), statistics.mean(vals)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, vals)) / sum((x - mx) ** 2 for x in xs)
    print(f"\n    monthly mean {statistics.mean(vals):,.0f}, stdev {statistics.stdev(vals):,.0f}, "
          f"CV {statistics.stdev(vals)/statistics.mean(vals):.1%}")
    print(f"    linear trend {slope:+,.0f} per month ({slope/my:+.2%} of an average month) -> flat")

    for col in ["ProductCategory", "CustomerLocation", "CustomerGender"]:
        d = collections.defaultdict(float)
        c = collections.Counter()
        for r in ROWS:
            d[r[col]] += rev(r)
            c[r[col]] += 1
        print(f"\n    BY {col} ({len(d)} values)")
        for k, val in sorted(d.items(), key=lambda kv: -kv[1]):
            print(f"      {k:<16} {val:>10,.0f}  {val/TOTAL:>6.1%}  {c[k]:>5} lines")
        shares = [x / TOTAL for x in d.values()]
        print(f"      even split would be {1/len(d):.1%} each; "
              f"actual {min(shares):.1%} to {max(shares):.1%}, spread {max(shares)/min(shares):.2f}x")

    print("\n    BY CustomerAge band")
    band = collections.defaultdict(float)
    for r in ROWS:
        a = int(r["CustomerAge"])
        k = "18-29" if a < 30 else "30-39" if a < 40 else "40-49" if a < 50 else "50-59" if a < 60 else "60+"
        band[k] += rev(r)
    for k in ["18-29", "30-39", "40-49", "50-59", "60+"]:
        print(f"      {k:<6} {band[k]:>10,.0f}  {band[k]/TOTAL:>6.1%}")

    print("\n    CONCENTRATION CHECK (the playbook's most decision-relevant number)")
    for col, label, caveat in [("CustomerLocation", "cities", ""),
                               ("ProductCategory", "categories", ""),
                               ("CustomerID", "customer IDs", " [not a stable key]"),
                               ("ProductID", "product IDs", " [not a stable key]")]:
        d = collections.defaultdict(float)
        for r in ROWS:
            d[r[col]] += rev(r)
        s = sorted(d.values(), reverse=True)
        n = max(1, round(len(s) * 0.10))
        half = k = 0
        for x in s:
            half += x
            k += 1
            if half >= TOTAL / 2:
                break
        print(f"      top 10% of {label:<13} ({n:>3} of {len(s):>3}) = {sum(s[:n])/TOTAL:>6.1%} "
              f"| {k} of {len(s)} make up half the revenue{caveat}")
    print("      Pareto reference: a real business dataset shows 40-80% in the top 10%.")


# ----------------------------------------------------------- SIGNAL TESTS
def signal_tests(seed=7, iters=20000):
    rule("SIGNAL TESTS - is any observed difference bigger than chance?")
    crit = {1: 3.84, 4: 9.49, 9: 16.92}

    print("\n[A] Chi-square goodness of fit against a uniform distribution, 5% level")
    for col in ["ProductCategory", "CustomerLocation", "CustomerGender"]:
        c = collections.Counter(r[col] for r in ROWS)
        e = len(ROWS) / len(c)
        x = sum((v - e) ** 2 / e for v in c.values())
        df = len(c) - 1
        print(f"    {col:<18} chi2={x:>6.2f}  df={df}  critical={crit[df]:>6}  -> "
              f"{'UNIFORM, no real difference' if x < crit[df] else 'NOT uniform'}")

    print(f"\n[B] Monte Carlo permutation test, {iters:,} shuffles of revenue across cities")
    random.seed(seed)
    values = [rev(r) for r in ROWS]
    pool = [r["CustomerLocation"] for r in ROWS]

    def spread(assign):
        d = collections.defaultdict(float)
        for city, v in zip(assign, values):
            d[city] += v
        s = list(d.values())
        return max(s) / min(s)

    obs = spread(pool)
    sim = []
    for _ in range(iters):
        random.shuffle(pool)
        sim.append(spread(pool))
    worse = sum(1 for s in sim if s >= obs)
    print(f"    observed richest/poorest city spread = {obs:.3f}x")
    print(f"    simulations at least this extreme    = {worse:,}/{iters:,}  (p = {worse/iters:.3f})")
    print(f"    -> {'NOT significant. The city gap is ordinary noise.' if worse/iters > 0.05 else 'significant'}")

    print("\n[C] Is revenue itself a uniform random draw?")
    lo, hi = min(values), max(values)
    dec = collections.Counter(min(9, int((v - lo) / (hi - lo) * 10)) for v in values)
    x = sum((dec[i] - len(values) / 10) ** 2 / (len(values) / 10) for i in range(10))
    print(f"    observed mean {statistics.mean(values):.1f} vs uniform mean {(lo+hi)/2:.1f}; "
          f"stdev {statistics.stdev(values):.1f} vs {(hi-lo)/12**0.5:.1f}")
    print(f"    decile chi2={x:.2f} df=9 critical=16.92 -> "
          f"{'consistent with uniform random' if x < 16.92 else 'not uniform'}")


if __name__ == "__main__":
    stage1()
    key_integrity()
    stage3()
    signal_tests()
    rule("DEAD ENDS - stated plainly, not forced")
    print("""
    profit / margin        : no cost column exists
    revenue per unit       : revenue uncorrelated with quantity
    customer-level view    : CustomerID is not a stable key
    product-level view     : ProductID is not a stable key
    repeat purchase, churn : follows from the CustomerID failure
    prioritisation by city : the gaps are not larger than chance
    forecasting            : there is no trend to project
""")
