# -*- coding: utf-8 -*-
"""
Stages 0, 1, 3 and 3b for Group_9230_Team1_PMARIS_Enterprise_Dataset.csv,
per AIB902_Agentic_Analytics_Dashboard_Playbook.md (v4.0).

Every figure quoted in the dashboard, the client report and the slide deck
comes from this script. It prints a readable log and writes findings.json
beside itself, which the report and deck generators read.

Run:  python analyze_pmaris.py
Zero external dependencies. Python standard library only.
"""

import csv
import collections
import datetime
import json
import math
import random
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "01_Data" / "Group_9230_Team1_PMARIS_Enterprise_Dataset.csv"
OUT = HERE / "findings.json"

ROWS = list(csv.DictReader(SRC.read_text(encoding="utf-8-sig").splitlines()))
COLS = list(ROWS[0].keys())
N = len(ROWS)

def _isfloat(v):
    try:
        float(v)
        return True
    except ValueError:
        return False


NUM_COLS = [c for c in COLS if all(_isfloat(r[c]) for r in ROWS[:200])]
CAT_COLS = [c for c in COLS if c not in NUM_COLS
            and c not in ("Observation_ID", "Asset_ID", "Observation_Date")]

f = lambda r, c: float(r[c])  # noqa: E731

# The dimensions the scoping interview may slice by, and the measures that matter
DIMS = ["Site", "Industry_Context", "Asset_Class", "Criticality_Class",
        "Maintenance_Strategy", "Spare_Parts_Status", "Technician_Skill_Level",
        "Operating_Shift", "Environment_Severity", "Manufacturer_Group",
        "Failure_Mode_Group"]
MEASURES = ["Unplanned_Downtime_Hours_30D", "Revenue_Loss_EGP_30D",
            "Failure_Probability_Pct", "Asset_Health_Index",
            "Maintenance_Cost_EGP_30D", "Financial_Exposure_At_Risk_EGP"]

HIGH_RISK_PCT = 50.0   # failure probability at or above this counts as a high-risk observation

F = {}  # findings, written to findings.json


def rule(t):
    print("\n" + "=" * 76)
    print(t)
    print("=" * 76)


# ------------------------------------------------------------ distributions
def _betacf(a, b, x):
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) > 1e-300 else 1e-300)
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d; d = 1.0 / (d if abs(d) > 1e-300 else 1e-300)
        c = 1.0 + aa / c if abs(c) > 1e-300 else 1e300
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d; d = 1.0 / (d if abs(d) > 1e-300 else 1e-300)
        c = 1.0 + aa / c if abs(c) > 1e-300 else 1e300
        de = d * c
        h *= de
        if abs(de - 1.0) < 3e-14:
            break
    return h


def betai(a, b, x):
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    lbt = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1 - x)
    if x < (a + 1) / (a + b + 2):
        return math.exp(lbt) * _betacf(a, b, x) / a
    return 1.0 - math.exp(lbt) * _betacf(b, a, 1 - x) / b


def f_sf(F_, d1, d2):
    """Survival function of the F distribution."""
    if F_ <= 0:
        return 1.0
    return betai(d2 / 2.0, d1 / 2.0, d2 / (d2 + d1 * F_))


def _gser(a, x):
    s = term = 1.0 / a
    ap = a
    for _ in range(1000):
        ap += 1
        term *= x / ap
        s += term
        if abs(term) < abs(s) * 1e-15:
            break
    return s * math.exp(-x + a * math.log(x) - math.lgamma(a))


def _gcf(a, x):
    b = x + 1 - a
    c = 1e300
    d = 1 / b
    h = d
    for i in range(1, 1000):
        an = -i * (i - a)
        b += 2
        d = an * d + b
        d = 1 / (d if abs(d) > 1e-300 else 1e-300)
        c = b + an / c
        c = c if abs(c) > 1e-300 else 1e-300
        de = d * c
        h *= de
        if abs(de - 1) < 1e-15:
            break
    return math.exp(-x + a * math.log(x) - math.lgamma(a)) * h


def chi2_sf(x, df):
    a = df / 2.0
    x = x / 2.0
    if x <= 0:
        return 1.0
    if x < a + 1:
        return 1.0 - _gser(a, x)
    return _gcf(a, x)


def fmt_p(p):
    return "<1e-300" if p == 0 else (f"{p:.2e}" if p < 1e-3 else f"{p:.3f}")


# ------------------------------------------------------------ derived field
for r in ROWS:
    fm = r["Failure_Mode_Category"]
    r["Failure_Mode_Group"] = fm if fm in ("General Mechanical", "Bearing / Vibration", "Lubrication") \
        else "Other (sensor / hydraulic / heat)"
    r["Month"] = r["Observation_Date"][:7]


# ================================================================ STAGE 0/1
def stage0_1():
    rule("STAGE 0 - INTAKE  /  STAGE 1 - CLEANING CHECKLIST")
    dates = sorted(r["Observation_Date"] for r in ROWS)
    bad_dates = sum(1 for r in ROWS if not _isdate(r["Observation_Date"]))
    print(f"rows={N} cols={len(COLS)}  numeric={len(NUM_COLS)}  categorical={len(CAT_COLS)}")
    print(f"date range {dates[0]} -> {dates[-1]}, {len(set(dates))} distinct dates, bad dates={bad_dates}")
    missing = sum(1 for r in ROWS for c in COLS if r[c].strip() == "")
    dups = N - len({tuple(r[c] for c in COLS) for r in ROWS})
    dup_ids = N - len({r["Observation_ID"] for r in ROWS})
    type_err = sum(1 for r in ROWS for c in NUM_COLS if not _isfloat(r[c]))
    print(f"missing cells={missing} exact dups={dups} duplicate Observation_IDs={dup_ids} type errors={type_err}")
    months = collections.Counter(r["Month"] for r in ROWS)
    print("rows per month:", dict(sorted(months.items())))

    # rare / near-constant levels
    rare = {}
    for c in CAT_COLS:
        cnt = collections.Counter(r[c] for r in ROWS)
        small = {k: v for k, v in cnt.items() if v < 0.01 * N}
        if small:
            rare[c] = small
    print("levels under 1% of rows:", rare)

    # ceilings / floors
    ceil = {}
    for c in NUM_COLS:
        v = [f(r, c) for r in ROWS]
        mx, mn = max(v), min(v)
        at_mx = sum(1 for x in v if x == mx)
        at_mn = sum(1 for x in v if x == mn)
        if at_mx >= 0.05 * N or at_mn >= 0.05 * N:
            ceil[c] = {"max": mx, "at_max_pct": round(100 * at_mx / N, 1),
                       "min": mn, "at_min_pct": round(100 * at_mn / N, 1)}
    print("columns piled at a bound (>=5% of rows):")
    for c, d in ceil.items():
        print("   ", c, d)

    # outliers: >3 SD
    outl = {}
    for c in MEASURES + ["Maintenance_Cost_EGP_30D"]:
        v = [f(r, c) for r in ROWS]
        m, s = statistics.mean(v), statistics.pstdev(v)
        outl[c] = sum(1 for x in v if abs(x - m) > 3 * s)
    print("observations beyond 3 SD:", outl)
    over100 = sum(1 for r in ROWS if f(r, "Load_Factor_Pct") > 100)
    print(f"Load_Factor_Pct above 100%: {over100} rows (overload, physically possible, kept)")

    # ------- column meaning checks (Playbook s18 step 4)
    by = collections.defaultdict(list)
    for r in ROWS:
        by[r["Asset_ID"]].append(r)
    incons = {}
    for c in ["Site", "Asset_Type", "Criticality_Class", "Manufacturer_Group", "Maintenance_Strategy"]:
        incons[c] = sum(1 for rs in by.values() if len({r[c] for r in rs}) > 1)
    age_back = 0
    for rs in by.values():
        rs = sorted(rs, key=lambda r: r["Observation_Date"])
        a = [f(r, "Asset_Age_Years") for r in rs]
        if any(a[i + 1] < a[i] - 0.01 for i in range(len(a) - 1)):
            age_back += 1
    print(f"Asset_ID: {len(by)} IDs; inconsistent attributes per ID: {incons}; age runs backwards for {age_back}")

    # derived columns
    def corr(a, b):
        return statistics.correlation([f(r, a) for r in ROWS], [f(r, b) for r in ROWS])
    derived = {
        "Financial_Exposure_vs_Revenue_Loss": round(corr("Financial_Exposure_At_Risk_EGP", "Revenue_Loss_EGP_30D"), 3),
        "Failure_Probability_vs_Health_Index": round(corr("Failure_Probability_Pct", "Asset_Health_Index"), 3),
        "Operating_Hours_vs_Utilization": round(corr("Operating_Hours_30D", "Utilization_Rate_Pct"), 3),
    }
    bands = collections.defaultdict(list)
    for r in ROWS:
        bands[r["Executive_Intervention_Priority"]].append(f(r, "Maintenance_Priority_Index"))
    band_rng = {k: [round(min(v), 1), round(max(v), 1), len(v)] for k, v in sorted(bands.items())}
    print("derived-column correlations:", derived)
    print("Executive priority = banding of Maintenance_Priority_Index:", band_rng)

    F["stage0"] = {"rows": N, "cols": len(COLS), "numeric": len(NUM_COLS), "categorical": len(CAT_COLS),
                   "date_min": dates[0], "date_max": dates[-1], "distinct_dates": len(set(dates)),
                   "months": dict(sorted(months.items())), "asset_ids": len(by), "path": "A"}
    F["stage1"] = {"missing": missing, "dups": dups, "dup_ids": dup_ids, "type_errors": type_err,
                   "bad_dates": bad_dates, "rare_levels": rare, "bounded": ceil, "outliers_3sd": outl,
                   "load_over_100": over100, "asset_inconsistent": incons, "age_backwards": age_back,
                   "derived": derived, "priority_bands": band_rng}


def _isdate(v):
    try:
        datetime.date.fromisoformat(v)
        return True
    except ValueError:
        return False


# ================================================================ STAGE 3
def gini(vals):
    v = sorted(vals)
    n = len(v)
    s = sum(v)
    if s == 0:
        return 0.0
    cum = sum((i + 1) * x for i, x in enumerate(v))
    return (2 * cum) / (n * s) - (n + 1) / n


def stage3():
    rule("STAGE 3 - INITIAL INSIGHTS")
    rl = [f(r, "Revenue_Loss_EGP_30D") for r in ROWS]
    dt = [f(r, "Unplanned_Downtime_Hours_30D") for r in ROWS]
    fp = [f(r, "Failure_Probability_Pct") for r in ROWS]
    k = {
        "observations": N,
        "revenue_loss_total": sum(rl),
        "revenue_loss_mean": statistics.mean(rl),
        "downtime_total": sum(dt),
        "downtime_mean": statistics.mean(dt),
        "high_risk_n": sum(1 for x in fp if x >= HIGH_RISK_PCT),
        "high_risk_pct": 100 * sum(1 for x in fp if x >= HIGH_RISK_PCT) / N,
        "health_mean": statistics.mean(f(r, "Asset_Health_Index") for r in ROWS),
        "maint_cost_total": sum(f(r, "Maintenance_Cost_EGP_30D") for r in ROWS),
        "spare_cost_total": sum(f(r, "Spare_Parts_Cost_EGP_30D") for r in ROWS),
        "exposure_total": sum(f(r, "Financial_Exposure_At_Risk_EGP") for r in ROWS),
        "pm_compliance_mean": statistics.mean(f(r, "Preventive_Maintenance_Compliance_Pct") for r in ROWS),
        "mtbf_mean": statistics.mean(f(r, "Mean_Time_Between_Failures_Hours") for r in ROWS),
        "mttr_mean": statistics.mean(f(r, "Mean_Time_To_Repair_Hours") for r in ROWS),
        "emergency_wo_pct": 100 * sum(1 for r in ROWS if r["Work_Order_Type"] == "Corrective Emergency") / N,
        "safety_incidents": sum(f(r, "Safety_Incident_Count_12M") for r in ROWS),
        "priority_counts": dict(collections.Counter(r["Executive_Intervention_Priority"] for r in ROWS)),
    }
    for kk, vv in k.items():
        print(f"  {kk:22s} {vv:,.1f}" if isinstance(vv, float) else f"  {kk:22s} {vv}")

    # concentration
    srt = sorted(rl, reverse=True)
    top10 = sum(srt[: N // 10]) / sum(srt)
    top20 = sum(srt[: N // 5]) / sum(srt)
    srt_d = sorted(dt, reverse=True)
    top10_dt = sum(srt_d[: N // 10]) / sum(srt_d)
    conc = {"revenue_loss_top10_share": top10, "revenue_loss_top20_share": top20,
            "downtime_top10_share": top10_dt, "gini_revenue_loss": gini(rl),
            "gini_downtime": gini(dt), "zero_loss_obs": sum(1 for x in rl if x == 0)}
    # Lorenz points for charts
    cum, pts = 0.0, []
    tot = sum(srt)
    for i, x in enumerate(srt):
        cum += x
        if (i + 1) % (N // 20) == 0:
            pts.append([round(100 * (i + 1) / N, 1), round(100 * cum / tot, 1)])
    conc["lorenz_desc"] = pts
    print(f"  top 10% of observations carry {100*top10:.1f}% of revenue loss "
          f"(top 20%: {100*top20:.1f}%); Gini {conc['gini_revenue_loss']:.3f}; "
          f"downtime top10 {100*top10_dt:.1f}% Gini {conc['gini_downtime']:.3f}")

    # high-risk slice
    hr = [r for r in ROWS if f(r, "Failure_Probability_Pct") >= HIGH_RISK_PCT]
    conc["high_risk_share_of_loss"] = sum(f(r, "Revenue_Loss_EGP_30D") for r in hr) / sum(rl)
    conc["high_risk_share_of_downtime"] = sum(f(r, "Unplanned_Downtime_Hours_30D") for r in hr) / sum(dt)
    print(f"  high-risk observations ({len(hr)}, {100*len(hr)/N:.1f}%) carry "
          f"{100*conc['high_risk_share_of_loss']:.1f}% of revenue loss and "
          f"{100*conc['high_risk_share_of_downtime']:.1f}% of downtime")

    # per-dimension profiles
    prof = {}
    for d in DIMS:
        g = collections.defaultdict(list)
        for r in ROWS:
            g[r[d]].append(r)
        rows = []
        for name, rs in g.items():
            rows.append({
                "name": name, "n": len(rs),
                "downtime_mean": statistics.mean(f(r, "Unplanned_Downtime_Hours_30D") for r in rs),
                "loss_mean": statistics.mean(f(r, "Revenue_Loss_EGP_30D") for r in rs),
                "loss_total": sum(f(r, "Revenue_Loss_EGP_30D") for r in rs),
                "fp_mean": statistics.mean(f(r, "Failure_Probability_Pct") for r in rs),
                "health_mean": statistics.mean(f(r, "Asset_Health_Index") for r in rs),
                "cost_mean": statistics.mean(f(r, "Maintenance_Cost_EGP_30D") for r in rs),
                "high_risk_pct": 100 * sum(1 for r in rs if f(r, "Failure_Probability_Pct") >= HIGH_RISK_PCT) / len(rs),
                "emergency_pct": 100 * sum(1 for r in rs if r["Work_Order_Type"] == "Corrective Emergency") / len(rs),
            })
        rows.sort(key=lambda x: -x["loss_mean"])
        prof[d] = rows
        print(f"\n  {d}")
        for x in rows:
            print(f"    {x['name'][:34]:34s} n={x['n']:5d} downtime={x['downtime_mean']:6.2f}h "
                  f"loss={x['loss_mean']:>10,.0f} FP={x['fp_mean']:5.1f}% health={x['health_mean']:5.1f} "
                  f"highrisk={x['high_risk_pct']:5.1f}% emerg={x['emergency_pct']:5.1f}%")

    # monthly trend
    mon = collections.defaultdict(list)
    for r in ROWS:
        mon[r["Month"]].append(r)
    trend = [{"period": m, "n": len(rs),
              "downtime_mean": statistics.mean(f(r, "Unplanned_Downtime_Hours_30D") for r in rs),
              "loss_mean": statistics.mean(f(r, "Revenue_Loss_EGP_30D") for r in rs),
              "loss_total": sum(f(r, "Revenue_Loss_EGP_30D") for r in rs),
              "fp_mean": statistics.mean(f(r, "Failure_Probability_Pct") for r in rs),
              "health_mean": statistics.mean(f(r, "Asset_Health_Index") for r in rs)}
             for m, rs in sorted(mon.items())]
    ys = [t["loss_mean"] for t in trend]
    xs = list(range(len(ys)))
    slope = statistics.linear_regression(xs, ys).slope
    lag1 = statistics.correlation(ys[:-1], ys[1:])
    print(f"\n  monthly mean revenue loss slope {slope:,.0f} EGP/month "
          f"({100*slope/statistics.mean(ys):+.2f}% of mean), lag-1 autocorr {lag1:+.2f}")

    # drivers: correlation of every numeric with revenue loss and failure probability
    drv = {}
    for tgt in ["Revenue_Loss_EGP_30D", "Failure_Probability_Pct", "Unplanned_Downtime_Hours_30D"]:
        y = [f(r, tgt) for r in ROWS]
        res = []
        for c in NUM_COLS:
            if c == tgt:
                continue
            res.append((c, statistics.correlation([f(r, c) for r in ROWS], y)))
        res.sort(key=lambda t: -abs(t[1]))
        drv[tgt] = [[c, round(v, 3)] for c, v in res]
        print(f"\n  strongest correlates of {tgt}:")
        for c, v in res[:10]:
            print(f"    {c:44s} r={v:+.3f}")

    F["kpis"] = k
    F["concentration"] = conc
    F["profiles"] = prof
    F["trend"] = trend
    F["trend_stats"] = {"slope_loss_per_month": slope, "slope_pct_of_mean": 100 * slope / statistics.mean(ys), "lag1": lag1}
    F["drivers"] = drv


# ================================================================ STAGE 3b
def anova(groups):
    allv = [x for g in groups for x in g]
    gm = statistics.mean(allv)
    ssb = sum(len(g) * (statistics.mean(g) - gm) ** 2 for g in groups)
    ssw = sum((x - statistics.mean(g)) ** 2 for g in groups for x in g)
    d1, d2 = len(groups) - 1, len(allv) - len(groups)
    Fv = (ssb / d1) / (ssw / d2)
    return Fv, d1, d2, f_sf(Fv, d1, d2), ssb / (ssb + ssw)


def kruskal(groups):
    allv = sorted((x, gi) for gi, g in enumerate(groups) for x in g)
    ranks = [0.0] * len(allv)
    i = 0
    while i < len(allv):
        j = i
        while j + 1 < len(allv) and allv[j + 1][0] == allv[i][0]:
            j += 1
        for k in range(i, j + 1):
            ranks[k] = (i + j) / 2 + 1
        i = j + 1
    n = len(allv)
    rs = collections.defaultdict(float)
    for (x, gi), rk in zip(allv, ranks):
        rs[gi] += rk
    H = 12 / (n * (n + 1)) * sum(rs[gi] ** 2 / len(g) for gi, g in enumerate(groups)) - 3 * (n + 1)
    return H, chi2_sf(H, len(groups) - 1)


def effect_word(eta2):
    if eta2 >= 0.14:
        return "large"
    if eta2 >= 0.06:
        return "medium"
    if eta2 >= 0.01:
        return "small"
    return "negligible"


def stage3b():
    rule("STAGE 3b - SIGNIFICANCE REGISTER (ANOVA F + Kruskal-Wallis, Bonferroni)")
    test_measures = ["Unplanned_Downtime_Hours_30D", "Revenue_Loss_EGP_30D", "Failure_Probability_Pct"]
    n_tests = len(DIMS) * len(test_measures)
    alpha = 0.05 / n_tests
    reg = []
    for d in DIMS:
        for m in test_measures:
            g = collections.defaultdict(list)
            for r in ROWS:
                g[r[d]].append(f(r, m))
            groups = [v for v in g.values() if len(v) >= 2]
            Fv, d1, d2, p, eta2 = anova(groups)
            H, pk = kruskal(groups)
            sig = p < alpha and pk < alpha
            means = {k: statistics.mean(v) for k, v in g.items()}
            hi = max(means, key=means.get)
            lo = min(means, key=means.get)
            verdict = ("REAL, " + effect_word(eta2)) if sig else "NOT SIGNIFICANT"
            if sig and effect_word(eta2) == "negligible":
                verdict = "REAL but negligible"
            reg.append({"dimension": d, "measure": m, "F": Fv, "df": [d1, d2], "p_anova": p,
                        "H": H, "p_kruskal": pk, "eta2": eta2, "verdict": verdict,
                        "highest": hi, "lowest": lo, "hi_mean": means[hi], "lo_mean": means[lo]})
            print(f"  {d[:24]:24s} x {m[:28]:28s} F={Fv:8.2f} p={fmt_p(p):>9s} KW p={fmt_p(pk):>9s} "
                  f"eta2={eta2:.4f}  -> {verdict}")
    print(f"\n  {n_tests} tests, Bonferroni threshold 0.05/{n_tests} = {alpha:.5f}")
    F["register"] = reg
    F["register_meta"] = {"n_tests": n_tests, "alpha": alpha}


def bootstrap(dim, measure, iters=2000, seed=7):
    rnd = random.Random(seed)
    g = collections.defaultdict(list)
    for r in ROWS:
        g[r[dim]].append(f(r, measure))
    out = {}
    for k, v in g.items():
        n = len(v)
        means = sorted(sum(v[rnd.randrange(n)] for _ in range(n)) / n for _ in range(iters))
        out[k] = {"mean": statistics.mean(v), "lo": means[int(0.025 * iters)], "hi": means[int(0.975 * iters)], "n": n}
    return out


def stage3b_bootstrap():
    rule("BOOTSTRAP 95% INTERVALS (2,000 resamples)")
    bs = {}
    for dim, m in [("Maintenance_Strategy", "Unplanned_Downtime_Hours_30D"),
                   ("Spare_Parts_Status", "Unplanned_Downtime_Hours_30D"),
                   ("Criticality_Class", "Revenue_Loss_EGP_30D"),
                   ("Site", "Revenue_Loss_EGP_30D"),
                   ("Technician_Skill_Level", "Unplanned_Downtime_Hours_30D")]:
        res = bootstrap(dim, m)
        bs[f"{dim}|{m}"] = res
        print(f"\n  {dim} -> {m}")
        for k, v in sorted(res.items(), key=lambda kv: -kv[1]["mean"]):
            print(f"    {k[:30]:30s} mean={v['mean']:>12,.2f}  95% CI [{v['lo']:,.2f}, {v['hi']:,.2f}]  n={v['n']}")
    F["bootstrap"] = bs


def levers():
    """Controllable levers: compare low vs high bands of the variables management can move."""
    rule("CONTROLLABLE LEVERS - downtime and loss by band")
    out = {}

    def band_cmp(col, cut, label_lo, label_hi):
        lo = [r for r in ROWS if f(r, col) < cut]
        hi = [r for r in ROWS if f(r, col) >= cut]
        res = {}
        for nm, rs in ((label_lo, lo), (label_hi, hi)):
            res[nm] = {"n": len(rs),
                       "downtime_mean": statistics.mean(f(r, "Unplanned_Downtime_Hours_30D") for r in rs),
                       "loss_mean": statistics.mean(f(r, "Revenue_Loss_EGP_30D") for r in rs),
                       "fp_mean": statistics.mean(f(r, "Failure_Probability_Pct") for r in rs)}
        Fv, d1, d2, p, eta2 = anova([[f(r, "Unplanned_Downtime_Hours_30D") for r in lo],
                                     [f(r, "Unplanned_Downtime_Hours_30D") for r in hi]])
        res["p_downtime"] = p
        res["eta2"] = eta2
        print(f"  {col} < {cut}: {res[label_lo]}  |  >= {cut}: {res[label_hi]}  p={fmt_p(p)} eta2={eta2:.3f}")
        return res

    out["pm_compliance"] = band_cmp("Preventive_Maintenance_Compliance_Pct", 80, "below 80%", "80% or more")
    out["days_since_maint"] = band_cmp("Days_Since_Last_Maintenance", 60, "under 60 days", "60+ days")
    out["lubricant"] = band_cmp("Lubricant_Quality_Index", 50, "LQI under 50", "LQI 50+")
    out["backlog"] = band_cmp("Maintenance_Backlog_Days", 14, "backlog under 14d", "backlog 14d+")

    # PM compliance deciles -> downtime (for a chart)
    srt = sorted(ROWS, key=lambda r: f(r, "Preventive_Maintenance_Compliance_Pct"))
    dec = []
    for i in range(10):
        part = srt[i * N // 10:(i + 1) * N // 10]
        dec.append({"decile": i + 1,
                    "pm_mid": statistics.median(f(r, "Preventive_Maintenance_Compliance_Pct") for r in part),
                    "downtime_mean": statistics.mean(f(r, "Unplanned_Downtime_Hours_30D") for r in part),
                    "fp_mean": statistics.mean(f(r, "Failure_Probability_Pct") for r in part)})
    out["pm_deciles"] = dec
    # health index bands -> loss
    bands = [(0, 70, "<70"), (70, 80, "70-79"), (80, 90, "80-89"), (90, 101, "90+")]
    hb = []
    for lo, hi, nm in bands:
        rs = [r for r in ROWS if lo <= f(r, "Asset_Health_Index") < hi]
        hb.append({"band": nm, "n": len(rs),
                   "loss_mean": statistics.mean(f(r, "Revenue_Loss_EGP_30D") for r in rs),
                   "downtime_mean": statistics.mean(f(r, "Unplanned_Downtime_Hours_30D") for r in rs),
                   "fp_mean": statistics.mean(f(r, "Failure_Probability_Pct") for r in rs)})
    out["health_bands"] = hb
    for x in hb:
        print("  health", x)
    F["levers"] = out


def watchlist():
    rule("P1/P2 WATCHLIST")
    wl = [r for r in ROWS if r["Executive_Intervention_Priority"] in ("P1 - Immediate", "P2 - High")]
    wl.sort(key=lambda r: -f(r, "Financial_Exposure_At_Risk_EGP"))
    F["watchlist"] = {
        "n": len(wl),
        "exposure_total": sum(f(r, "Financial_Exposure_At_Risk_EGP") for r in wl),
        "exposure_share": sum(f(r, "Financial_Exposure_At_Risk_EGP") for r in wl) / F["kpis"]["exposure_total"],
        "by_site": dict(collections.Counter(r["Site"] for r in wl)),
        "by_class": dict(collections.Counter(r["Asset_Class"] for r in wl)),
        "top": [{k: r[k] for k in ("Observation_ID", "Asset_ID", "Observation_Date", "Site", "Asset_Type",
                                   "Criticality_Class", "Failure_Probability_Pct", "Asset_Health_Index",
                                   "Unplanned_Downtime_Hours_30D", "Financial_Exposure_At_Risk_EGP",
                                   "Executive_Intervention_Priority")} for r in wl[:15]],
    }
    # does the executive flag cover the observations that actually carry the loss?
    top = sorted(ROWS, key=lambda r: -f(r, "Revenue_Loss_EGP_30D"))[: N // 10]
    cov = collections.Counter(r["Executive_Intervention_Priority"] for r in top)
    top_loss = sum(f(r, "Revenue_Loss_EGP_30D") for r in top)
    flagged_loss = sum(f(r, "Revenue_Loss_EGP_30D") for r in top
                       if r["Executive_Intervention_Priority"] in ("P1 - Immediate", "P2 - High"))
    F["watchlist"]["top_decile_priority_mix"] = dict(cov)
    F["watchlist"]["top_decile_flagged_loss_share"] = flagged_loss / top_loss
    hr_unflagged = sum(1 for r in ROWS if f(r, "Failure_Probability_Pct") >= HIGH_RISK_PCT
                       and r["Executive_Intervention_Priority"] in ("P3 - Planned", "P4 - Monitor"))
    F["watchlist"]["high_risk_not_flagged"] = hr_unflagged
    print(f"  top-decile-loss observations by priority: {dict(cov)}; "
          f"P1/P2 cover {100*flagged_loss/top_loss:.1f}% of that loss; "
          f"high-risk (FP>=50%) but only P3/P4: {hr_unflagged}")
    print(f"  {len(wl)} P1/P2 observations, exposure {F['watchlist']['exposure_total']:,.0f} EGP "
          f"({100*F['watchlist']['exposure_share']:.1f}% of total); by site {F['watchlist']['by_site']}")


if __name__ == "__main__":
    stage0_1()
    stage3()
    stage3b()
    stage3b_bootstrap()
    levers()
    watchlist()
    OUT.write_text(json.dumps(F, indent=1, default=float))
    print(f"\nwrote {OUT.name}")
