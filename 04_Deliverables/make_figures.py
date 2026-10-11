# -*- coding: utf-8 -*-
"""
Static chart figures for the client report and the slide deck.

Reads 02_Analysis/findings.json (every study figure) and the source CSV (for the
two views findings.json does not carry: the strategy x spares heatmap and the
escalation gap by site). Writes PNGs to 04_Deliverables/figures/.

Palette and rules match the live dashboard (03_Dashboard/styles.css): fixed
categorical slots for maintenance strategy, one-hue blue ramp for magnitude,
reserved status colours for spares and priority, hairline grids, direct labels.

Needs matplotlib (see requirements.txt). Run:  python make_figures.py
"""

import csv
import collections
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FIG = HERE / "figures"
FIG.mkdir(exist_ok=True)
F = json.loads((ROOT / "02_Analysis" / "findings.json").read_text())
SRC = ROOT / "01_Data" / "Group_9230_Team1_PMARIS_Enterprise_Dataset.csv"
ROWS = list(csv.DictReader(SRC.read_text(encoding="utf-8-sig").splitlines()))

INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#898781", "#e1e0d9"
STRAT = {"Reactive": "#eb6834", "Preventive": "#2a78d6", "Condition-Based": "#eda100", "Predictive": "#1baf7a"}
SPARE = {"Shortage": "#d03b3b", "Limited": "#fab219", "Available": "#0ca30c"}
PRIO = {"P1 - Immediate": "#d03b3b", "P2 - High": "#e8762c", "P3 - Planned": "#fab219", "P4 - Monitor": "#9a988f"}
SEQ = ["#cde2fb", "#86b6ef", "#3987e5", "#256abf", "#184f95", "#0d366b"]
CMAP = LinearSegmentedColormap.from_list("seq", SEQ)

plt.rcParams.update({
    "font.family": "Arial", "font.size": 11, "axes.edgecolor": GRID, "axes.labelcolor": INK2,
    "xtick.color": MUTED, "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
    "axes.spines.left": False, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.axisbelow": True, "figure.dpi": 200, "savefig.bbox": "tight", "savefig.pad_inches": 0.12,
})


def seq(v, vmax):
    return CMAP(0.15 + 0.85 * (v / vmax if vmax else 0.5))


def money_axis(ax, mx):
    """EGP axes read as 250k / 1.0M rather than a scientific offset."""
    if mx >= 1e5:
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v/1e6:.1f}M" if v >= 1e6 else f"{v/1e3:.0f}k"))


def save(fig, name):
    fig.savefig(FIG / f"{name}.png", facecolor="white")
    plt.close(fig)


def hbar(name, labels, values, colors, fmt, xlabel="", size=(7.2, 3.2)):
    fig, ax = plt.subplots(figsize=size)
    y = list(range(len(labels)))[::-1]
    ax.barh(y, values, color=colors, height=0.62)
    ax.set_yticks(y, labels)
    ax.grid(axis="y", visible=False)
    ax.tick_params(axis="y", length=0)
    mx = max(values)
    for yi, v in zip(y, values):
        ax.text(v + mx * 0.015, yi, fmt(v), va="center", fontsize=10.5, color=INK, fontweight="bold")
    ax.set_xlim(0, mx * 1.18)
    money_axis(ax, mx)
    if xlabel:
        ax.set_xlabel(xlabel, color=MUTED, fontsize=10)
    save(fig, name)


def whisker(name, key, order, colorfn, fmt, xlabel, size=(7.2, 3.0)):
    b = F["bootstrap"][key]
    order = [k for k in order if k in b]
    fig, ax = plt.subplots(figsize=size)
    y = list(range(len(order)))[::-1]
    for yi, k in zip(y, order):
        v = b[k]
        c = colorfn(k)
        ax.plot([v["lo"], v["hi"]], [yi, yi], color=c, lw=2.6, solid_capstyle="round")
        ax.plot([v["lo"]] * 2, [yi - .16, yi + .16], color=c, lw=2)
        ax.plot([v["hi"]] * 2, [yi - .16, yi + .16], color=c, lw=2)
        ax.scatter([v["mean"]], [yi], s=70, color=c, edgecolor="white", linewidth=1.5, zorder=3)
        ax.text(v["hi"], yi + 0.22, "  " + fmt(v["mean"]), va="bottom", fontsize=10.5, color=INK, fontweight="bold")
    ax.set_yticks(y, order)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="y", visible=False)
    ax.set_xlim(0, max(b[k]["hi"] for k in order) * 1.2)
    ax.set_ylim(-0.6, len(order) - 0.3)
    money_axis(ax, max(b[k]["hi"] for k in order))
    ax.set_xlabel(xlabel, color=MUTED, fontsize=10)
    save(fig, name)


def main():
    P = F["profiles"]
    hrs = lambda v: f"{v:.1f} h"  # noqa: E731
    egp = lambda v: f"EGP {v/1e3:,.0f}k" if v < 1e6 else f"EGP {v/1e6:.2f}M"  # noqa: E731
    pct = lambda v: f"{v:.1f}%"  # noqa: E731

    # 1-3 bootstrap whiskers
    whisker("ci_strategy", "Maintenance_Strategy|Unplanned_Downtime_Hours_30D",
            ["Reactive", "Preventive", "Condition-Based", "Predictive"], STRAT.get, hrs,
            "Mean unplanned downtime per 30-day window (hours), 95% bootstrap interval")
    whisker("ci_spares", "Spare_Parts_Status|Unplanned_Downtime_Hours_30D",
            ["Shortage", "Limited", "Available"], SPARE.get, hrs,
            "Mean unplanned downtime per 30-day window (hours), 95% bootstrap interval", size=(7.2, 2.5))
    whisker("ci_skill", "Technician_Skill_Level|Unplanned_Downtime_Hours_30D",
            ["Basic", "Intermediate", "Advanced", "Expert"], lambda k: "#256abf", hrs,
            "Mean unplanned downtime per 30-day window (hours), 95% bootstrap interval")
    bs = F["bootstrap"]["Site|Revenue_Loss_EGP_30D"]
    order = sorted(bs, key=lambda k: -bs[k]["mean"])
    mx = max(bs[k]["mean"] for k in order)
    whisker("ci_site", "Site|Revenue_Loss_EGP_30D", order, lambda k: seq(bs[k]["mean"], mx), egp,
            "Mean revenue loss per window (EGP), 95% bootstrap interval", size=(7.2, 3.4))
    bc = F["bootstrap"]["Criticality_Class|Revenue_Loss_EGP_30D"]
    whisker("ci_criticality", "Criticality_Class|Revenue_Loss_EGP_30D", ["Critical", "High", "Medium", "Low"],
            lambda k: seq(bc[k]["mean"], bc["Critical"]["mean"]), egp,
            "Mean revenue loss per window (EGP), 95% bootstrap interval")

    # 4 PM-compliance deciles
    dec = F["levers"]["pm_deciles"]
    fig, ax = plt.subplots(figsize=(7.2, 3.1))
    xs = [f"D{d['decile']}\n{d['pm_mid']:.0f}%" for d in dec]
    vals = [d["downtime_mean"] for d in dec]
    ax.bar(xs, vals, color="#256abf", width=0.66)
    for i, v in enumerate(vals):
        ax.text(i, v + 0.4, f"{v:.1f}", ha="center", fontsize=9.5, color=INK, fontweight="bold")
    ax.axhline(F["kpis"]["downtime_mean"], color=MUTED, ls="--", lw=1)
    ax.text(9.4, F["kpis"]["downtime_mean"] + 0.5, f"average {F['kpis']['downtime_mean']:.1f} h", ha="right", fontsize=9, color=INK2)
    ax.grid(axis="x", visible=False)
    ax.set_ylabel("Mean downtime (h)", color=MUTED, fontsize=10)
    ax.set_xlabel("PM-compliance decile (median compliance shown)", color=MUTED, fontsize=10)
    save(fig, "pm_deciles")

    # 5 health bands
    hb = F["levers"]["health_bands"]
    mxl = max(h["loss_mean"] for h in hb)
    hbar("health_bands", [f"Health {h['band']}" for h in hb], [h["loss_mean"] for h in hb],
         [seq(h["loss_mean"], mxl) for h in hb], egp, "Mean revenue loss per window (EGP)", size=(7.2, 2.6))

    # 6 heatmap strategy x spares
    srow, scol = ["Reactive", "Preventive", "Condition-Based", "Predictive"], ["Shortage", "Limited", "Available"]
    acc = collections.defaultdict(list)
    for r in ROWS:
        acc[(r["Maintenance_Strategy"], r["Spare_Parts_Status"])].append(float(r["Unplanned_Downtime_Hours_30D"]))
    M = [[sum(acc[(a, b)]) / len(acc[(a, b)]) for b in scol] for a in srow]
    N = [[len(acc[(a, b)]) for b in scol] for a in srow]
    fig, ax = plt.subplots(figsize=(6.6, 3.3))
    ax.imshow(M, cmap=CMAP, aspect="auto", vmin=min(map(min, M)) * 0.6)
    ax.grid(False)
    ax.set_xticks(range(3), scol)
    ax.set_yticks(range(4), srow)
    ax.tick_params(length=0)
    ax.xaxis.tick_top()
    vmax = max(map(max, M))
    for i in range(4):
        for j in range(3):
            v = M[i][j]
            ax.text(j, i, f"{v:.1f} h\nn={N[i][j]}", ha="center", va="center", fontsize=10,
                    color="white" if v > vmax * 0.55 else INK, fontweight="bold")
    save(fig, "heatmap")
    F["heatmap"] = {"rows": srow, "cols": scol, "values": M, "counts": N}

    # 7 priority distribution and top-decile mix
    pc = F["kpis"]["priority_counts"]
    order = ["P1 - Immediate", "P2 - High", "P3 - Planned", "P4 - Monitor"]
    hbar("priority_all", order, [pc.get(p, 0) for p in order], [PRIO[p] for p in order],
         lambda v: f"{v:,.0f}", "Observations", size=(7.2, 2.5))
    mix = F["watchlist"]["top_decile_priority_mix"]
    hbar("priority_top_decile", order, [mix.get(p, 0) for p in order], [PRIO[p] for p in order],
         lambda v: f"{v:,.0f}", "Top-10% loss windows (500)", size=(7.2, 2.5))

    # 8 Lorenz curve
    pts = [[0, 0]] + F["concentration"]["lorenz_desc"]
    fig, ax = plt.subplots(figsize=(5.4, 4.0))
    ax.plot([p[0] for p in pts], [p[1] for p in pts], color="#256abf", lw=2.4)
    ax.fill_between([p[0] for p in pts], [p[1] for p in pts], [p[0] for p in pts], color="#256abf", alpha=0.08)
    ax.plot([0, 100], [0, 100], color=MUTED, ls="--", lw=1)
    t10 = 100 * F["concentration"]["revenue_loss_top10_share"]
    ax.scatter([10], [t10], color="#d03b3b", zorder=3, s=40)
    ax.annotate(f"top 10% of windows\n= {t10:.1f}% of loss", (10, t10), (24, t10 - 16), fontsize=10, color=INK,
                arrowprops=dict(arrowstyle="-", color=MUTED))
    ax.set_xlabel("% of observation windows, largest loss first", color=MUTED, fontsize=10)
    ax.set_ylabel("Cumulative % of revenue loss", color=MUTED, fontsize=10)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 102)
    save(fig, "lorenz")

    # 9 monthly trend
    tr = F["trend"]
    mnames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    lab = [mnames[int(t["period"][5:]) - 1] + " " + t["period"][2:4] for t in tr]
    fig, ax = plt.subplots(figsize=(7.2, 2.8))
    ax.plot(lab, [t["loss_mean"] / 1e3 for t in tr], color="#2a78d6", lw=2.2, marker="o", ms=4)
    ax.set_ylim(0, max(t["loss_mean"] for t in tr) / 1e3 * 1.25)
    ax.set_ylabel("Mean loss (EGP k)", color=MUTED, fontsize=10)
    ax.grid(axis="x", visible=False)
    ax.tick_params(axis="x", labelsize=9)
    save(fig, "trend")

    # 10 failure mode / environment / asset class
    fm = P["Failure_Mode_Group"]
    mx = max(x["loss_mean"] for x in fm)
    hbar("failure_mode", [x["name"] for x in fm], [x["loss_mean"] for x in fm], [seq(x["loss_mean"], mx) for x in fm],
         egp, "Mean revenue loss per window (EGP)", size=(7.2, 2.6))
    env = sorted(P["Environment_Severity"], key=lambda x: ["Severe", "Harsh", "Moderate", "Controlled"].index(x["name"]))
    mx = max(x["high_risk_pct"] for x in env)
    hbar("environment", [x["name"] for x in env], [x["high_risk_pct"] for x in env], [seq(x["high_risk_pct"], mx) for x in env],
         pct, "% of windows high-risk (failure probability ≥ 50%)", size=(7.2, 2.6))
    ac = sorted(P["Asset_Class"], key=lambda x: -x["high_risk_pct"])
    mx = max(x["high_risk_pct"] for x in ac)
    hbar("asset_class", [x["name"] for x in ac], [x["high_risk_pct"] for x in ac], [seq(x["high_risk_pct"], mx) for x in ac],
         pct, "% of windows high-risk", size=(7.2, 4.0))

    # 11 escalation gap by site
    g = collections.Counter(r["Site"] for r in ROWS if float(r["Failure_Probability_Pct"]) >= 50
                            and r["Executive_Intervention_Priority"] in ("P3 - Planned", "P4 - Monitor"))
    rule = sum(1 for r in ROWS if float(r["Failure_Probability_Pct"]) >= 50
               and r["Executive_Intervention_Priority"] in ("P3 - Planned", "P4 - Monitor")
               and r["Criticality_Class"] in ("High", "Critical"))
    rule_exp = sum(float(r["Financial_Exposure_At_Risk_EGP"]) for r in ROWS if float(r["Failure_Probability_Pct"]) >= 50
                   and r["Executive_Intervention_Priority"] in ("P3 - Planned", "P4 - Monitor")
                   and r["Criticality_Class"] in ("High", "Critical"))
    gap_exp = sum(float(r["Financial_Exposure_At_Risk_EGP"]) for r in ROWS if float(r["Failure_Probability_Pct"]) >= 50
                  and r["Executive_Intervention_Priority"] in ("P3 - Planned", "P4 - Monitor"))
    items = g.most_common()
    mx = items[0][1]
    hbar("gap_by_site", [k for k, _ in items], [v for _, v in items], [seq(v, mx) for _, v in items],
         lambda v: f"{v:,.0f}", "High-risk windows flagged only P3/P4", size=(7.2, 2.9))
    F["gap"] = {"by_site": dict(items), "rule_adds": rule, "rule_exposure": rule_exp, "gap_exposure": gap_exp}

    # 12 effect sizes (eta2 on downtime) per dimension
    reg = [r for r in F["register"] if r["measure"] == "Unplanned_Downtime_Hours_30D"]
    reg.sort(key=lambda r: -r["eta2"])
    labels = [r["dimension"].replace("_", " ") for r in reg]
    cols = ["#256abf" if r["verdict"].startswith("REAL") else "#c3c2b7" for r in reg]
    hbar("effect_sizes", labels, [100 * r["eta2"] for r in reg], cols,
         lambda v: f"{v:.1f}%", "Share of downtime variance explained (η² × 100); grey = not significant", size=(7.2, 3.6))

    # 13 drivers of downtime (non-derived, controllable/measured inputs only)
    want = ["Preventive_Maintenance_Compliance_Pct", "Lubricant_Quality_Index", "Maintenance_Backlog_Days",
            "Days_Since_Last_Maintenance", "Vibration_mm_s", "Spare_Parts_Lead_Time_Days", "Temperature_C",
            "Asset_Age_Years", "Load_Factor_Pct", "Utilization_Rate_Pct"]
    d = dict(F["drivers"]["Unplanned_Downtime_Hours_30D"])
    items = sorted([(k, d[k]) for k in want if k in d], key=lambda t: -abs(t[1]))
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    y = list(range(len(items)))[::-1]
    ax.barh(y, [v for _, v in items], color=["#2a78d6" if v < 0 else "#eb6834" for _, v in items], height=0.6)
    ax.set_yticks(y, [k.replace("_", " ").replace(" Pct", " %") for k, _ in items])
    ax.axvline(0, color=MUTED, lw=1)
    for yi, (_, v) in zip(y, items):
        ax.text(v + (0.015 if v >= 0 else -0.015), yi, f"{v:+.2f}", va="center", ha="left" if v >= 0 else "right",
                fontsize=10, color=INK, fontweight="bold")
    ax.set_xlim(-0.75, 0.75)
    ax.grid(axis="y", visible=False)
    ax.tick_params(axis="y", length=0)
    ax.set_xlabel("Correlation with unplanned downtime (r); blue lowers it, orange raises it", color=MUTED, fontsize=10)
    save(fig, "drivers")
    F["drivers_inputs"] = items

    # persist the extra figures for the generators
    (HERE / "figures" / "extras.json").write_text(json.dumps(
        {"heatmap": F["heatmap"], "gap": F["gap"], "drivers_inputs": F["drivers_inputs"]}, indent=1))
    print("figures written to", FIG)


if __name__ == "__main__":
    main()
