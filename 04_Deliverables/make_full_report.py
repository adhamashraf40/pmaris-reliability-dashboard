# -*- coding: utf-8 -*-
"""Generates the PMARIS Comprehensive Analytical Report (PDF, about 23 pages).

The long-form companion to the 10-page assessment: same findings, same sources,
plus the data dictionary, descriptive statistics, the cost view, every test in
full, limitations and an implementation roadmap. Each section starts a page.

Sources (all measured):
  02_Analysis/findings.json        Stages 0, 1, 3, 3b (analyze_pmaris.py)
  04_Deliverables/figures/         charts + extras.json (make_figures.py)
  01_Data/...csv                   descriptive statistics, data dictionary, cost tables
Rebuild with:  python make_figures.py && python make_full_report.py
"""
import csv
import collections
import json
import statistics as st
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table,
                                TableStyle, PageBreak, CondPageBreak, Image, KeepTogether)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = str(HERE / "PMARIS_Comprehensive_Analytical_Report.pdf")
FIG = HERE / "figures"
F = json.loads((ROOT / "02_Analysis" / "findings.json").read_text())
X = json.loads((FIG / "extras.json").read_text())
SRC = ROOT / "01_Data" / "Group_9230_Team1_PMARIS_Enterprise_Dataset.csv"
ROWS = list(csv.DictReader(SRC.read_text(encoding="utf-8-sig").splitlines()))
K, P, C, WL, LV = F["kpis"], F["profiles"], F["concentration"], F["watchlist"], F["levers"]
N = len(ROWS)

INK, ACC = colors.HexColor("#14213d"), colors.HexColor("#2a78d6")
WARN, OK = colors.HexColor("#b3261e"), colors.HexColor("#006300")
MUTE, RULE, BAND = colors.HexColor("#5b5f6b"), colors.HexColor("#d7d9de"), colors.HexColor("#f2f4f7")
ORANGE = colors.HexColor("#e8762c")

ss = getSampleStyleSheet()


def S(name, **kw):
    return ParagraphStyle(name, parent=kw.pop("parent", ss["Normal"]), **kw)


TITLE = S("t", fontName="Helvetica-Bold", fontSize=26, leading=30, textColor=INK, spaceAfter=6)
SUBT = S("st", fontName="Helvetica", fontSize=12, leading=17, textColor=MUTE)
H1 = S("h1", fontName="Helvetica-Bold", fontSize=15, leading=19, textColor=INK, spaceAfter=7)
H2 = S("h2", fontName="Helvetica-Bold", fontSize=10.8, leading=14, textColor=ACC, spaceBefore=8, spaceAfter=4)
BODY = S("b", fontName="Helvetica", fontSize=9.6, leading=14.2, textColor=colors.HexColor("#22252b"),
         alignment=TA_JUSTIFY, spaceAfter=6)
BULLET = S("bu", parent=BODY, leftIndent=13, bulletIndent=2, spaceAfter=4, alignment=0)
CELL = S("c", fontName="Helvetica", fontSize=8.5, leading=12, textColor=colors.HexColor("#22252b"))
CAP = S("cap", fontName="Helvetica-Oblique", fontSize=8, leading=10.6, textColor=MUTE, spaceAfter=7)
EYE = S("eye", fontName="Helvetica-Bold", fontSize=7.6, leading=10, textColor=ACC, spaceAfter=3)
W = 174 * mm
TOTAL = [0]


def egp(v):
    return f"EGP {v/1e9:.2f}B" if v >= 1e9 else (f"EGP {v/1e6:,.1f}M" if v >= 1e6 else f"EGP {v/1e3:,.1f}k")


def pv(p):
    return "<1e-300" if p == 0 else (f"{p:.0e}" if p < 1e-3 else f"{p:.3f}")


def callout(text, tone=ACC, label="KEY FINDING"):
    t = Table([[Paragraph(label, S("kk", fontName="Helvetica-Bold", fontSize=7.6, leading=10, textColor=tone))],
               [Paragraph(text, S("cot", parent=BODY, fontSize=10, leading=15, spaceAfter=0, alignment=0))]], colWidths=[W])
    t.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                           ("TOPPADDING", (0, 0), (0, 0), 8), ("BOTTOMPADDING", (0, 0), (0, 0), 1),
                           ("TOPPADDING", (0, 1), (0, 1), 0), ("BOTTOMPADDING", (0, 1), (-1, -1), 9),
                           ("BACKGROUND", (0, 0), (-1, -1), BAND), ("LINEBEFORE", (0, 0), (0, -1), 2.4, tone)]))
    return t


def table(head, rows, widths, aligns=None, size=8.5, pad=4.0):
    cs = S("cx", parent=CELL, fontSize=size, leading=size + 3.2)
    data = [[Paragraph(h, S("th", fontName="Helvetica-Bold", fontSize=min(8.2, size), leading=11, textColor=colors.white)) for h in head]]
    data += [[c if isinstance(c, Paragraph) else Paragraph(str(c), cs) for c in r] for r in rows]
    t = Table(data, colWidths=widths, repeatRows=1)
    sty = [("BACKGROUND", (0, 0), (-1, 0), INK), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
           ("TOPPADDING", (0, 0), (-1, -1), pad), ("BOTTOMPADDING", (0, 0), (-1, -1), pad),
           ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
           ("LINEBELOW", (0, 1), (-1, -2), 0.4, RULE), ("LINEBELOW", (0, -1), (-1, -1), 0.8, INK),
           ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fafbfc")])]
    for i, a in enumerate(aligns or []):
        if a != "L":
            sty.append(("ALIGN", (i, 0), (i, -1), "RIGHT" if a == "R" else "CENTER"))
    t.setStyle(TableStyle(sty))
    return t


def tiles(items):
    cells = [[Paragraph(f"<font size=16><b>{v}</b></font><br/><font size=7.8 color='#5b5f6b'>{lab}</font>",
                        S("tile", parent=CELL, leading=13)) for v, lab in items]]
    t = Table(cells, colWidths=[W / len(items)] * len(items))
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), BAND), ("LINEAFTER", (0, 0), (-2, -1), 2, colors.white),
                           ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
                           ("LEFTPADDING", (0, 0), (-1, -1), 9), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    return t


def fig(name, width=W, caption=None):
    iw, ih = ImageReader(str(FIG / f"{name}.png")).getSize()
    out = [Image(str(FIG / f"{name}.png"), width=width, height=width * ih / iw)]
    if caption:
        out.append(Paragraph(caption, CAP))
    return KeepTogether(out)


def col(t, c):
    return Paragraph(f"<font color='{c}'><b>{t}</b></font>", CELL)


def green(t):
    return col(t, "#006300")


def red(t):
    return col(t, "#b3261e")


def grey(t):
    return col(t, "#898781")


def decorate(canv, doc):
    canv.saveState()
    w, h = A4
    canv.setFillColor(INK)
    canv.rect(0, h - 12 * mm, w, 12 * mm, stroke=0, fill=1)
    canv.setFont("Helvetica-Bold", 7.6)
    canv.setFillColor(colors.white)
    canv.drawString(18 * mm, h - 8 * mm, "PMARIS ASSET RELIABILITY · COMPREHENSIVE ANALYTICAL REPORT")
    canv.setFont("Helvetica", 7.6)
    canv.drawRightString(w - 18 * mm, h - 8 * mm, "Prepared for the Head of Reliability & Maintenance")
    canv.setStrokeColor(RULE)
    canv.setLineWidth(0.5)
    canv.line(18 * mm, 15 * mm, w - 18 * mm, 15 * mm)
    canv.setFillColor(MUTE)
    canv.drawString(18 * mm, 10.5 * mm, "Group_9230_Team1_PMARIS_Enterprise_Dataset.csv  |  5,000 observation windows  |  11 October 2026")
    canv.drawRightString(w - 18 * mm, 10.5 * mm, f"Page {doc.page} of {TOTAL[0] or '?'}")
    canv.restoreState()


# ------------------------------------------------------------------ numbers
prof = lambda d, n: next(x for x in P[d] if x["name"] == n)  # noqa: E731
react, pred, prev, cbm = (prof("Maintenance_Strategy", n) for n in ("Reactive", "Predictive", "Preventive", "Condition-Based"))
short, limited, avail = (prof("Spare_Parts_Status", n) for n in ("Shortage", "Limited", "Available"))
skills = [prof("Technician_Skill_Level", n) for n in ("Basic", "Intermediate", "Advanced", "Expert")]
crit, low = prof("Criticality_Class", "Critical"), prof("Criticality_Class", "Low")
reg = F["register"]
n_real = sum(1 for r in reg if r["verdict"].startswith("REAL"))
gap, heat = X["gap"], X["heatmap"]
gap_n, hr_n = WL["high_risk_not_flagged"], K["high_risk_n"]
esc_n = sum(K["priority_counts"].get(p, 0) for p in ("P1 - Immediate", "P2 - High"))
hb = {h["band"]: h for h in LV["health_bands"]}
s1 = F["stage1"]
fv = lambda r, c: float(r[c])  # noqa: E731


def grp_mean(dim, col_):
    g = collections.defaultdict(list)
    for r in ROWS:
        g[r[dim]].append(fv(r, col_))
    return {k: st.mean(v) for k, v in g.items()}


cost_by = {d: {c: grp_mean(d, c) for c in ("Maintenance_Cost_EGP_30D", "Spare_Parts_Cost_EGP_30D", "Labor_Hours_30D", "Revenue_Loss_EGP_30D")}
           for d in ("Maintenance_Strategy", "Spare_Parts_Status", "Criticality_Class", "Technician_Skill_Level")}
maint_total = sum(fv(r, "Maintenance_Cost_EGP_30D") for r in ROWS)
spare_total = sum(fv(r, "Spare_Parts_Cost_EGP_30D") for r in ROWS)
loss_total = K["revenue_loss_total"]
save_strategy = (react["downtime_mean"] - prev["downtime_mean"]) * react["n"]
save_spares = (short["downtime_mean"] - avail["downtime_mean"]) * short["n"]
cost_save_strategy = (cost_by["Maintenance_Strategy"]["Maintenance_Cost_EGP_30D"]["Reactive"]
                      - cost_by["Maintenance_Strategy"]["Maintenance_Cost_EGP_30D"]["Preventive"]) * react["n"]

DERIVED = {"Asset_Health_Index", "Failure_Probability_Pct", "Reliability_Risk_Score", "Maintenance_Priority_Index",
           "Downtime_Risk_Score", "Remaining_Useful_Life_Months", "Maintenance_Cost_Efficiency_Index",
           "Operational_Criticality_Score", "Preventive_Maintenance_Effectiveness_Index", "Replacement_Priority_Score",
           "Financial_Exposure_At_Risk_EGP", "Executive_Intervention_Priority"}


def numeric(c):
    try:
        float(ROWS[0][c])
        return True
    except ValueError:
        return False


def build():
    s = []
    A = s.append

    # ============================================================ 1 cover
    A(Spacer(1, 30))
    A(Paragraph("COMPREHENSIVE ANALYTICAL REPORT", EYE))
    A(Paragraph("PMARIS Asset Reliability: where the next EGP of maintenance should go", TITLE))
    A(Paragraph("A full analysis of 5,000 thirty-day asset-health observations across six industrial sites in four "
                "industries, September 2025 to August 2026, prepared for the Head of Reliability & Maintenance.", SUBT))
    A(Spacer(1, 18))
    A(callout(f"Put the next EGP on four controllable levers and on a wider escalation list. The top 10% of observation windows carry "
              f"<b>{100*C['revenue_loss_top10_share']:.1f}%</b> of revenue loss; that concentration tracks maintenance strategy, spare-parts "
              f"availability, crew skill and PM discipline, each worth roughly 2x on downtime. The executive priority flag misses "
              f"<b>{gap_n}</b> of the <b>{hr_n}</b> high-risk windows.", tone=WARN, label="THE ANSWER"))
    A(Spacer(1, 14))
    A(tiles([(f"{loss_total/1e9:.2f}B", "EGP revenue loss, all windows"), (f"{K['downtime_mean']:.1f} h", "mean unplanned downtime / window"),
             (f"{K['high_risk_pct']:.1f}%", "windows high-risk (FP ≥ 50%)"), (f"{100*C['high_risk_share_of_loss']:.1f}%", "of loss in those windows"),
             (f"{gap_n}", "high-risk, only P3/P4")]))
    A(Spacer(1, 16))
    A(table(["Prepared for", "Prepared by", "Method", "Status"],
            [["Head of Reliability & Maintenance", "AIB902 Group 9230, Team 1", "AIB902 Agentic Analytics Playbook v4.0", "Final, 11 October 2026"]],
            [W / 4] * 4))
    A(Spacer(1, 12))
    A(Paragraph("Companion deliverables: the live six-page dashboard (03_Dashboard), the 15-slide Executive Presentation, "
                "the 30-slide full deck and the 10-page assessment. All are generated from the same analysis output, "
                "02_Analysis/findings.json, so their figures agree.", CAP))
    A(PageBreak())

    # ============================================================ 2 contents
    A(Paragraph("Contents", H1))
    toc = [("1", "Executive summary"), ("2", "Business context and the decision"), ("3", "Methodology"),
           ("4", "Data dictionary"), ("5", "Data quality assessment"), ("6", "Do the columns mean what they say?"),
           ("7", "Descriptive statistics"), ("8", "Finding 1: loss is concentrated"), ("9", "Asset health, failure modes and risk"),
           ("10", "Time: a flat year"), ("11", "Lever 1: maintenance strategy"), ("12", "Lever 2: spare-parts availability"),
           ("13", "Levers 3 and 4: crew skill and PM discipline"), ("14", "Operating thresholds and compounding"),
           ("15", "Measured drivers of downtime"), ("16", "Sites, criticality and environment"),
           ("17", "Asset classes, and what does not matter"), ("18", "Finding 4: the escalation gap"),
           ("19", "The financial view"), ("20", "The significance register"), ("21", "Limitations and risks"),
           ("22", "Recommendations and implementation roadmap"), ("A", "Appendix: reproducibility and the live dashboard")]
    A(table(["§", "Section"], [[a, b] for a, b in toc], [14 * mm, W - 14 * mm], aligns=["C", "L"], size=9.5, pad=4.6))
    A(Spacer(1, 10))
    A(Paragraph("How to read this report. Sections 1 and 22 are the decision; sections 3 to 7 establish that the data can be "
                "trusted and how far; sections 8 to 19 are the evidence, one question per section; sections 20 and 21 are the "
                "statistical record and the limits. Every number is measured from the file unless it is marked ESTIMATED.", BODY))
    A(PageBreak())

    # ============================================================ 3 exec summary
    A(Paragraph("SECTION 1", EYE))
    A(Paragraph("Executive summary", H1))
    A(Paragraph(f"The six sites lost <b>{egp(loss_total)}</b> of revenue across 5,000 observation windows, to "
                f"<b>{K['downtime_total']:,.0f}</b> hours of unplanned downtime, against <b>{egp(maint_total)}</b> of maintenance spend. "
                "Three arguments support the answer, each sufficient on its own.", BODY))
    A(Paragraph("1. Loss is concentrated where risk is high", H2))
    A(Paragraph(f"The top 10% of windows carry {100*C['revenue_loss_top10_share']:.1f}% of revenue loss (Gini {C['gini_revenue_loss']:.2f}); the "
                f"{hr_n} windows with failure probability of 50% or more carry {100*C['high_risk_share_of_loss']:.1f}% of loss and "
                f"{100*C['high_risk_share_of_downtime']:.1f}% of downtime. Windows under health 70 lose "
                f"{hb['<70']['loss_mean']/hb['90+']['loss_mean']:.0f}x those above 90.", BODY))
    A(Paragraph("2. The concentration tracks levers management controls", H2))
    A(Paragraph(f"Reactive maintenance: {react['downtime_mean']:.1f} h of downtime per window against {pred['downtime_mean']:.1f} h for "
                f"predictive ({react['downtime_mean']/pred['downtime_mean']:.1f}x), at "
                f"{cost_by['Maintenance_Strategy']['Maintenance_Cost_EGP_30D']['Reactive']/cost_by['Maintenance_Strategy']['Maintenance_Cost_EGP_30D']['Predictive']:.1f}x "
                f"the maintenance cost. Parts shortage: {short['downtime_mean']:.1f} h against {avail['downtime_mean']:.1f} h available "
                f"({short['downtime_mean']/avail['downtime_mean']:.1f}x). Basic crews {skills[0]['downtime_mean']/skills[3]['downtime_mean']:.1f}x expert. "
                f"PM compliance below 80%: {LV['pm_compliance']['below 80%']['downtime_mean']/LV['pm_compliance']['80% or more']['downtime_mean']:.1f}x. "
                "Every split survives a Bonferroni-corrected test with non-overlapping 95% intervals.", BODY))
    A(Paragraph("3. The executive escalation flag does not see most of it", H2))
    A(Paragraph(f"Only {esc_n} windows are P1 or P2. {gap_n} of {hr_n} high-risk windows sit at P3 or P4 with {egp(gap['gap_exposure'])} "
                f"of exposure; P1/P2 cover {100*WL['top_decile_flagged_loss_share']:.1f}% of the loss in the worst 10% of windows.", BODY))
    A(Paragraph("What this report recommends", H2))
    A(table(["#", "Action", "Why"], [
        ["1", "Move reactive windows onto a planned strategy, critical assets first", f"{react['downtime_mean']/pred['downtime_mean']:.1f}x downtime, {react['emergency_pct']:.0f}% emergency WOs"],
        ["2", "Fund spare-parts availability for shortage-prone classes", f"{short['downtime_mean']/avail['downtime_mean']:.1f}x downtime; largest categorical effect"],
        ["3", "Manage to PM ≥ 80%, maintenance < 60 days, backlog < 14 days", "each threshold splits downtime about 2x"],
        ["4", "Pair basic crews with experts on high-risk work", f"{skills[0]['downtime_mean']/skills[3]['downtime_mean']:.1f}x downtime gap"],
        ["5", "Add a second escalation trigger after a capacity check", f"+{gap['rule_adds']} windows, {egp(gap['rule_exposure'])} exposure"],
        ["6", "Pilot before scaling", "turns association into a causal estimate"],
        ["7", "Fix Asset_ID in the next export", "unlocks per-asset planning"]],
        [8 * mm, 96 * mm, W - 104 * mm], aligns=["C", "L", "L"]))
    A(PageBreak())

    # ============================================================ 4 context
    A(Paragraph("SECTION 2", EYE))
    A(Paragraph("Business context and the decision", H1))
    A(Paragraph("The scope was agreed with the stakeholder before any dashboard or report was built, through the Playbook's "
                "scoping interview (Stage 4). The resulting Dashboard Scope Brief is the contract for every deliverable.", BODY))
    A(table(["Element", "Agreed scope"], [
        ["Audience", "Head of Reliability & Maintenance, accountable across all six sites"],
        ["Decision", "Where to put the next EGP: which controllable lever to fund, and which windows to escalate"],
        ["KPIs", "Mean revenue loss per window; mean unplanned downtime; high-risk share and the loss it carries; escalation gap"],
        ["Refresh", "Live (watcher re-computes within about 0.3 s of a save; verified under 1 s end to end)"],
        ["Headline", "The next EGP belongs on the controllable levers and on the escalation list"],
        ["Out of scope", "Per-asset replacement or remaining-life planning (Asset_ID is not a stable key, Section 6)"]],
        [32 * mm, W - 32 * mm]))
    A(Paragraph("The operating footprint", H2))
    sites = sorted(P["Site"], key=lambda x: -x["n"])
    ind = {r["Site"]: r["Industry_Context"] for r in ROWS}
    A(table(["Site", "Industry", "Windows", "Mean loss", "Mean downtime", "High-risk"],
            [[x["name"], ind[x["name"]], f"{x['n']:,}", egp(x["loss_mean"]), f"{x['downtime_mean']:.1f} h", f"{x['high_risk_pct']:.1f}%"] for x in sites],
            [42 * mm, 50 * mm, 18 * mm, 24 * mm, 22 * mm, 18 * mm], aligns=["L", "L", "R", "R", "R", "R"]))
    A(Spacer(1, 6))
    A(Paragraph("Why this decision matters", H2))
    A(Paragraph(f"Revenue lost to failure is {loss_total/maint_total:.1f}x what the sites spent on maintenance in the same windows "
                f"({egp(loss_total)} against {egp(maint_total)}). A maintenance budget allocated in proportion to where loss actually "
                "occurs, rather than evenly or by site, is the largest single opportunity in the file.", BODY))
    A(PageBreak())

    # ============================================================ 5 methodology
    A(Paragraph("SECTION 3", EYE))
    A(Paragraph("Methodology", H1))
    A(Paragraph("The file was taken through the AIB902 Agentic Analytics Playbook (v4.0) in a fixed order. Each stage's output is "
                "the next stage's input, and two gates (an approved scope brief, and a timed live-refresh test) were passed before "
                "anything was delivered.", BODY))
    A(table(["Stage", "What was done", "Output"], [
        ["0 Intake", "Format, grain, time dimension, dimensions, measures, scale", "Path A: one flat table with a date column"],
        ["1 Cleaning", "Types, missing, duplicates, outliers, constant and rare levels, bounds", "Zero defects; nothing dropped (Section 5)"],
        ["1b Meaning", "Entity-key stability, derived-column detection, flag banding", "Broken Asset_ID; derived scores (Section 6)"],
        ["3 Insights", "Totals, rates, concentration, per-dimension profiles, trend, correlations", "Sections 7 to 19"],
        ["3b Significance", "ANOVA + Kruskal-Wallis, Bonferroni, η², bootstrap intervals", f"{n_real} of {len(reg)} differences real (Section 20)"],
        ["4 Scoping", "Stakeholder interview: audience, decision, KPIs, refresh, pages", "Approved scope brief (Section 2)"],
        ["5 Build + verify", "Live dashboard, report, decks; headless render and timed edits", "376 ms mean refresh (Appendix)"]],
        [26 * mm, 84 * mm, W - 110 * mm]))
    A(Paragraph("Statistical tests and why each was chosen", H2))
    A(table(["Question", "Test", "Rule applied"], [
        ["Do groups differ on a measure?", "One-way ANOVA (F), with η²", "η² ≥ 0.01 small, ≥ 0.06 medium, ≥ 0.14 large"],
        ["Is that robust to skew and outliers?", "Kruskal-Wallis H", "Must agree with ANOVA to count"],
        ["Too many tests?", "Bonferroni correction", f"0.05 / {len(reg)} = {F['register_meta']['alpha']:.4f}"],
        ["Is a ranking reproducible?", "Bootstrap, 2,000 resamples", "Non-overlapping 95% intervals"],
        ["Is loss concentrated?", "Lorenz curve, Gini, top-decile share", "Top 10% share reported"],
        ["Is there a trend or momentum?", "Linear slope, lag-1 autocorrelation", "Slope as % of mean per month"],
        ["Does the flag catch the risk?", "Cross-tab of priority vs outcome deciles", "Share of top-decile loss covered"]],
        [52 * mm, 52 * mm, W - 104 * mm]))
    A(Paragraph("Why effect size, not p-value, drives the wording", H2))
    A(Paragraph("With 5,000 rows almost any difference is statistically detectable. A p-value says a difference is not chance; it "
                "does not say the difference is worth a budget line. This report therefore calls a difference a lever only when it "
                "survives both tests and carries a non-trivial effect size, and it describes real-but-small effects as small.", BODY))
    A(PageBreak())

    # ============================================================ 6 data dictionary
    A(Paragraph("SECTION 4", EYE))
    A(Paragraph("Data dictionary", H1))
    A(Paragraph("All 60 columns, with their role in the analysis and the values they actually take. 'Derived' marks a composite "
                "score or flag computed from other columns; these are reported but never treated as independent evidence.", BODY))
    dd = []
    for c in ROWS[0].keys():
        if c in ("Observation_ID", "Asset_ID"):
            role, val = "Identifier", f"{len({r[c] for r in ROWS}):,} distinct"
        elif c == "Observation_Date":
            role, val = "Date", f"{min(r[c] for r in ROWS)} to {max(r[c] for r in ROWS)}"
        elif numeric(c):
            v = [fv(r, c) for r in ROWS]
            role = "Derived score" if c in DERIVED else "Measure"
            val = f"{min(v):,.1f} to {max(v):,.1f} (median {st.median(v):,.1f})"
        else:
            cnt = collections.Counter(r[c] for r in ROWS)
            role = "Derived flag" if c in DERIVED else "Dimension"
            lv = ", ".join(k for k, _ in cnt.most_common(4)) + (f" +{len(cnt)-4} more" if len(cnt) > 4 else "")
            val = f"{len(cnt)} levels: {lv}"
        dd.append([c.replace("_", " "), role, val])
    A(table(["Column", "Role", "Values in this file"], dd, [62 * mm, 24 * mm, W - 86 * mm], size=7.3, pad=1.7))
    A(PageBreak())

    # ============================================================ 7 data quality
    A(Paragraph("SECTION 5", EYE))
    A(Paragraph("Data quality assessment", H1))
    A(Paragraph("Stage 1 ran the Playbook's universal checklist. The file passed with zero defects; nothing was dropped or imputed, "
                "and every judgement call is recorded below with its reason.", BODY))
    A(table(["Check", "Result", "Decision", "Reason"], [
        ["Missing cells", "0 of 300,000", green("None needed"), "-"],
        ["Exact duplicates / duplicate IDs", "0 / 0", green("None needed"), "-"],
        ["Numeric type errors / bad dates", "0 / 0", green("None needed"), "-"],
        ["Revenue loss beyond 3 SD", f"{s1['outliers_3sd']['Revenue_Loss_EGP_30D']} rows", "Kept", "A real heavy tail; removing it would hide the concentration"],
        ["Downtime beyond 3 SD", f"{s1['outliers_3sd']['Unplanned_Downtime_Hours_30D']} rows", "Kept", "Same reason"],
        ["Load factor above 100%", f"{s1['load_over_100']} rows", "Kept", "Overload is physically possible"],
        ["Failure modes under 1% of rows", "3 levels, 27 rows", "Pooled as 'Other'", "Too few rows per level to test separately"],
        ["P1 - Immediate", "2 rows", "Kept, combined with P2 as 'escalated'", "Too rare to analyse alone"],
        ["Rows per month", "357 to 443", "Kept", "No gap in the 12-month range"]],
        [44 * mm, 28 * mm, 34 * mm, W - 106 * mm], size=8.2))
    A(Paragraph("Columns piled at a bound", H2))
    A(Paragraph("Columns with at least 5% of rows at their minimum or maximum. A pile at a maximum usually means a capped scale, so "
                "values there are read as 'at or above the cap', not as measured.", BODY))
    A(table(["Column", "Min", "% at min", "Max", "% at max", "Interpretation"],
            [[k.replace("_", " "), f"{v['min']:,.0f}", f"{v['at_min_pct']:.1f}%", f"{v['max']:,.0f}", f"{v['at_max_pct']:.1f}%",
              "Capped index" if v["at_max_pct"] >= 5 else "Many zero windows (no event)"] for k, v in s1["bounded"].items()],
            [56 * mm, 18 * mm, 18 * mm, 22 * mm, 18 * mm, W - 132 * mm], aligns=["L", "R", "R", "R", "R", "L"], size=8))
    A(PageBreak())

    # ============================================================ 8 meaning
    inc = s1["asset_inconsistent"]
    A(Paragraph("SECTION 6", EYE))
    A(Paragraph("Do the columns mean what they say?", H1))
    A(Paragraph("A clean bill of health is not fitness for purpose. Playbook Stage 1b checks that identifiers identify and that "
                "measures relate the way their names imply. One column fails; several are formulas of others.", BODY))
    A(Paragraph("Asset_ID is not an asset key", H2))
    A(table(["Attribute that should be fixed per asset", "Asset IDs where it changes (of 500)"], [
        ["Site", f"{inc['Site']}"], ["Asset type", f"{inc['Asset_Type']}"], ["Criticality class", f"{inc['Criticality_Class']}"],
        ["Manufacturer group", f"{inc['Manufacturer_Group']}"], ["Maintenance strategy", f"{inc['Maintenance_Strategy']}"],
        ["Asset age runs backwards in date order", f"{s1['age_backwards']}"]], [100 * mm, W - 100 * mm], aligns=["L", "R"]))
    A(Spacer(1, 6))
    A(callout("Every row is treated as an independent 30-day observation window. No per-asset history, remaining-life tracking, "
              "replacement plan or churn view can be built from this export, and none is attempted.", tone=WARN, label="CONSEQUENCE"))
    A(Paragraph("Derived columns", H2))
    pb = s1["priority_bands"]
    A(table(["Column", "Evidence", "Treatment"], [
        ["Financial exposure at risk", f"r = {s1['derived']['Financial_Exposure_vs_Revenue_Loss']} with revenue loss", "Never added to loss; used only for the watchlist ranking"],
        ["Failure probability", f"r = {s1['derived']['Failure_Probability_vs_Health_Index']} with health index", "Used for the high-risk threshold; health reported in bands"],
        ["Executive Intervention Priority", f"Exact bands of the Maintenance Priority Index: P4 {pb['P4 - Monitor'][0]}–{pb['P4 - Monitor'][1]}, "
         f"P3 {pb['P3 - Planned'][0]}–{pb['P3 - Planned'][1]}, P2 {pb['P2 - High'][0]}–{pb['P2 - High'][1]}, P1 {pb['P1 - Immediate'][0]}+", "Treated as a formula that can be re-tuned (Section 18)"],
        ["Risk, priority, RUL, efficiency scores", "Inter-correlated at 0.7 to 0.99", "Excluded from the drivers analysis (Section 15)"]],
        [42 * mm, 74 * mm, W - 116 * mm], size=8.2))
    A(PageBreak())

    # ============================================================ 9 descriptive
    A(Paragraph("SECTION 7", EYE))
    A(Paragraph("Descriptive statistics", H1))
    A(Paragraph("The core measures per 30-day window. Means sit well above medians for downtime, loss and cost: the distributions "
                "are right-skewed, which is why the rank-based test is required alongside ANOVA and why concentration matters.", BODY))
    keys = ["Unplanned_Downtime_Hours_30D", "Planned_Downtime_Hours_30D", "Revenue_Loss_EGP_30D", "Production_Loss_Units",
            "Maintenance_Cost_EGP_30D", "Spare_Parts_Cost_EGP_30D", "Labor_Hours_30D", "Failure_Probability_Pct",
            "Asset_Health_Index", "Mean_Time_Between_Failures_Hours", "Mean_Time_To_Repair_Hours",
            "Preventive_Maintenance_Compliance_Pct", "Maintenance_Backlog_Days", "Days_Since_Last_Maintenance",
            "Vibration_mm_s", "Temperature_C", "Lubricant_Quality_Index", "Asset_Age_Years", "Safety_Incident_Count_12M"]
    rows = []
    for c in keys:
        v = sorted(fv(r, c) for r in ROWS)
        big = max(v) >= 10000
        f_ = (lambda x: f"{x:,.0f}") if big else (lambda x: f"{x:,.2f}")
        rows.append([c.replace("_", " "), f_(st.mean(v)), f_(st.median(v)), f_(st.pstdev(v)), f_(v[int(0.9 * N)]), f_(v[-1])])
    A(table(["Measure", "Mean", "Median", "Std dev", "90th pct", "Max"], rows,
            [62 * mm, 22 * mm, 22 * mm, 22 * mm, 22 * mm, W - 150 * mm], aligns=["L", "R", "R", "R", "R", "R"], size=8, pad=2.8))
    A(Spacer(1, 6))
    A(Paragraph("Category mix", H2))
    mix = [("Maintenance strategy", "Maintenance_Strategy"), ("Spare-parts status", "Spare_Parts_Status"),
           ("Criticality", "Criticality_Class"), ("Technician skill", "Technician_Skill_Level"), ("Environment", "Environment_Severity")]
    A(table(["Dimension", "Levels and share of windows"],
            [[a, ", ".join(f"{x['name']} {100*x['n']/N:.0f}%" for x in sorted(P[b], key=lambda x: -x['n']))] for a, b in mix],
            [40 * mm, W - 40 * mm], size=8.2))
    A(PageBreak())

    # ============================================================ 10 concentration
    A(Paragraph("SECTION 8", EYE))
    A(Paragraph("Finding 1: loss is concentrated", H1))
    A(Paragraph(f"A tenth of the windows carry {100*C['revenue_loss_top10_share']:.1f}% of revenue loss and a fifth carry "
                f"{100*C['revenue_loss_top20_share']:.1f}%. Downtime is almost as concentrated: the top 10% of windows carry "
                f"{100*C['downtime_top10_share']:.1f}% of unplanned hours (Gini {C['gini_downtime']:.2f}). {C['zero_loss_obs']} windows "
                f"({100*C['zero_loss_obs']/N:.1f}%) lost nothing at all.", BODY))
    A(fig("lorenz", width=120 * mm, caption="Figure 1. Lorenz curve of revenue loss, windows sorted largest first. The dashed diagonal is an even spread."))
    A(table(["Concentration measure", "Revenue loss", "Unplanned downtime"], [
        ["Share in the top 10% of windows", f"{100*C['revenue_loss_top10_share']:.1f}%", f"{100*C['downtime_top10_share']:.1f}%"],
        ["Gini coefficient", f"{C['gini_revenue_loss']:.3f}", f"{C['gini_downtime']:.3f}"],
        ["Share in high-risk windows (FP ≥ 50%)", f"{100*C['high_risk_share_of_loss']:.1f}%", f"{100*C['high_risk_share_of_downtime']:.1f}%"]],
        [80 * mm, 47 * mm, W - 127 * mm], aligns=["L", "R", "R"]))
    A(Spacer(1, 8))
    A(callout(f"Effort spread evenly across the fleet is mostly spent where little is lost. The {K['high_risk_pct']:.1f}% of windows that are "
              f"high-risk are where {100*C['high_risk_share_of_loss']:.1f}% of the money goes.", label="SO WHAT"))
    A(PageBreak())

    # ============================================================ 11 health and failure modes
    A(Paragraph("SECTION 9", EYE))
    A(Paragraph("Asset health, failure modes and risk", H1))
    A(Paragraph(f"Loss rises steeply as health falls. Windows below a health index of 70 average {egp(hb['<70']['loss_mean'])} of loss and "
                f"{hb['<70']['downtime_mean']:.1f} h of downtime, against {egp(hb['90+']['loss_mean'])} and {hb['90+']['downtime_mean']:.1f} h "
                "above 90. Each band down roughly doubles the loss, which is the case for intervening early.", BODY))
    A(fig("health_bands", width=150 * mm, caption="Figure 2. Mean revenue loss per window by Asset Health Index band."))
    fm = P["Failure_Mode_Group"]
    r_fm = next(r for r in reg if r["dimension"] == "Failure_Mode_Group" and r["measure"].startswith("Unplanned"))
    A(Paragraph(f"Failure mode is the strongest single categorical signal in the file (η² {r_fm['eta2']:.3f} on downtime). Bearing and "
                f"vibration failures average {egp(fm[0]['loss_mean'])} per window, {fm[0]['loss_mean']/fm[-1]['loss_mean']:.1f}x general mechanical "
                "failures. Failure mode describes what went wrong rather than a lever, but it tells the crews where condition monitoring "
                "(vibration, lubrication) pays.", BODY))
    A(fig("failure_mode", width=150 * mm, caption="Figure 3. Mean revenue loss per window by failure mode. 'Other' pools 27 rows across three rare modes."))
    A(PageBreak())

    # ============================================================ 12 time
    ts = F["trend_stats"]
    A(Paragraph("SECTION 10", EYE))
    A(Paragraph("Time: a flat year", H1))
    A(Paragraph(f"Mean revenue loss per window moves within a narrow band all year. The fitted slope is {ts['slope_pct_of_mean']:+.2f}% of the "
                f"monthly mean per month, and the lag-1 autocorrelation is {ts['lag1']:+.2f}: a bad month does not predict the next. "
                "There is no trend to extrapolate and no season to schedule maintenance around.", BODY))
    A(fig("trend", width=W, caption="Figure 4. Mean revenue loss per window by month, September 2025 to August 2026."))
    mn = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    A(table(["Month", "Windows", "Mean loss", "Mean downtime", "Failure prob.", "Health"],
            [[mn[int(t['period'][5:]) - 1] + " " + t["period"][:4], f"{t['n']:,}", egp(t["loss_mean"]), f"{t['downtime_mean']:.1f} h",
              f"{t['fp_mean']:.1f}%", f"{t['health_mean']:.1f}"] for t in F["trend"]],
            [30 * mm, 24 * mm, 32 * mm, 30 * mm, 28 * mm, W - 144 * mm], aligns=["L", "R", "R", "R", "R", "R"], size=8, pad=2.6))
    A(Spacer(1, 6))
    A(callout("Plan maintenance by asset condition, not by calendar.", label="SO WHAT"))
    A(PageBreak())

    # ============================================================ 13 strategy
    cs = cost_by["Maintenance_Strategy"]
    r_s = next(r for r in reg if r["dimension"] == "Maintenance_Strategy" and r["measure"].startswith("Unplanned"))
    A(Paragraph("SECTION 11", EYE))
    A(Paragraph("Lever 1: maintenance strategy", H1))
    A(Paragraph(f"Reactive windows average {react['downtime_mean']:.1f} h of unplanned downtime; the three planned strategies sit between "
                f"{pred['downtime_mean']:.1f} and {prev['downtime_mean']:.1f} h with overlapping intervals (η² {r_s['eta2']:.3f}, "
                f"p = {pv(r_s['p_anova'])}). The step that matters is leaving reactive, not choosing between planned strategies. "
                "Reactive is also not the cheap option: it costs more to maintain, not less.", BODY))
    A(fig("ci_strategy", width=150 * mm, caption="Figure 5. Mean downtime by strategy with 95% bootstrap intervals (2,000 resamples)."))
    A(table(["Strategy", "Windows", "Downtime", "Revenue loss", "Maint. cost", "Spare parts", "Labour h", "Emergency WOs"],
            [[x["name"], f"{x['n']:,}", f"{x['downtime_mean']:.1f} h", egp(x["loss_mean"]),
              egp(cs["Maintenance_Cost_EGP_30D"][x["name"]]), egp(cs["Spare_Parts_Cost_EGP_30D"][x["name"]]),
              f"{cs['Labor_Hours_30D'][x['name']]:.1f}", f"{x['emergency_pct']:.1f}%"] for x in (react, prev, cbm, pred)],
            [28 * mm, 17 * mm, 19 * mm, 24 * mm, 22 * mm, 22 * mm, 17 * mm, W - 149 * mm], aligns=["L"] + ["R"] * 7, size=8))
    A(Spacer(1, 6))
    A(callout(f"Reactive windows run {react['emergency_pct']:.0f}% emergency work orders against {pred['emergency_pct']:.0f}% for predictive, "
              f"and cost {egp(cs['Maintenance_Cost_EGP_30D']['Reactive'])} per window to maintain against {egp(cs['Maintenance_Cost_EGP_30D']['Predictive'])}.",
              label="SO WHAT"))
    A(PageBreak())

    # ============================================================ 14 spares
    sp = cost_by["Spare_Parts_Status"]
    r_p = next(r for r in reg if r["dimension"] == "Spare_Parts_Status" and r["measure"].startswith("Unplanned"))
    A(Paragraph("SECTION 12", EYE))
    A(Paragraph("Lever 2: spare-parts availability", H1))
    A(Paragraph(f"A clean staircase: shortage {short['downtime_mean']:.1f} h, limited {limited['downtime_mean']:.1f} h, available "
                f"{avail['downtime_mean']:.1f} h, with no interval touching the next (η² {r_p['eta2']:.3f} on downtime, the largest among the "
                "controllable dimensions). Shortages also cost more on every line: parts bought at a premium, more labour, more maintenance.", BODY))
    A(fig("ci_spares", width=150 * mm, caption="Figure 6. Mean downtime by spare-parts status with 95% bootstrap intervals."))
    A(table(["Parts status", "Windows", "Downtime", "Revenue loss", "Maint. cost", "Spare parts", "Labour h", "High-risk"],
            [[x["name"], f"{x['n']:,}", f"{x['downtime_mean']:.1f} h", egp(x["loss_mean"]), egp(sp["Maintenance_Cost_EGP_30D"][x["name"]]),
              egp(sp["Spare_Parts_Cost_EGP_30D"][x["name"]]), f"{sp['Labor_Hours_30D'][x['name']]:.1f}", f"{x['high_risk_pct']:.1f}%"]
             for x in (short, limited, avail)],
            [26 * mm, 17 * mm, 19 * mm, 24 * mm, 22 * mm, 22 * mm, 17 * mm, W - 147 * mm], aligns=["L"] + ["R"] * 7, size=8))
    A(Spacer(1, 6))
    A(callout(f"Shortage windows spend {sp['Spare_Parts_Cost_EGP_30D']['Shortage']/sp['Spare_Parts_Cost_EGP_30D']['Available']:.1f}x as much on spare parts "
              f"and {sp['Maintenance_Cost_EGP_30D']['Shortage']/sp['Maintenance_Cost_EGP_30D']['Available']:.1f}x as much on maintenance as windows with "
              "stock available, while losing far more revenue. Holding stock is cheaper than not holding it.", label="SO WHAT"))
    A(PageBreak())

    # ============================================================ 15 skill + PM
    A(Paragraph("SECTION 13", EYE))
    A(Paragraph("Levers 3 and 4: crew skill and PM discipline", H1))
    A(Paragraph(f"Basic crews average {skills[0]['downtime_mean']:.1f} h of downtime per window, intermediate {skills[1]['downtime_mean']:.1f} h, "
                f"advanced {skills[2]['downtime_mean']:.1f} h and expert {skills[3]['downtime_mean']:.1f} h. "
                f"{skills[0]['n'] + skills[1]['n']:,} windows ({100*(skills[0]['n'] + skills[1]['n'])/N:.0f}%) are worked by basic or intermediate crews.", BODY))
    A(fig("ci_skill", width=145 * mm, caption="Figure 7. Mean downtime by technician skill with 95% bootstrap intervals."))
    dec = LV["pm_deciles"]
    A(Paragraph(f"PM compliance shows a dose-response: the least compliant decile averages {dec[0]['downtime_mean']:.1f} h, the most compliant "
                f"{dec[-1]['downtime_mean']:.1f} h, falling almost every step. A steady gradient across ten groups is stronger evidence than "
                "any single split.", BODY))
    A(fig("pm_deciles", width=145 * mm, caption="Figure 8. Mean downtime by PM-compliance decile (median compliance under each bar)."))
    A(PageBreak())

    # ============================================================ 16 thresholds + heatmap
    A(Paragraph("SECTION 14", EYE))
    A(Paragraph("Operating thresholds and compounding", H1))
    A(Paragraph("Each lever was split at a practical threshold the maintenance team can manage to. Every split roughly halves "
                "downtime and is significant far beyond the corrected threshold.", BODY))
    names = {"pm_compliance": "PM compliance", "days_since_maint": "Days since maintenance", "lubricant": "Lubricant quality", "backlog": "Maintenance backlog"}
    rows = []
    for k, v in LV.items():
        if k in names:
            a, b = [x for x in v if isinstance(v[x], dict)]
            w_, b_ = (a, b) if v[a]["downtime_mean"] > v[b]["downtime_mean"] else (b, a)
            rows.append([names[k], w_, f"{v[w_]['n']:,}", f"{v[w_]['downtime_mean']:.1f} h", b_, f"{v[b_]['downtime_mean']:.1f} h",
                         f"{v[w_]['downtime_mean']/v[b_]['downtime_mean']:.1f}x", pv(v["p_downtime"]), f"{v['eta2']:.3f}"])
    A(table(["Lever", "Worse side", "Windows", "Downtime", "Better side", "Downtime", "Ratio", "p", "η²"], rows,
            [32 * mm, 22 * mm, 15 * mm, 17 * mm, 26 * mm, 17 * mm, 13 * mm, 17 * mm, W - 159 * mm], aligns=["L", "L", "R", "R", "L", "R", "R", "R", "R"], size=7.8))
    A(Spacer(1, 8))
    A(Paragraph(f"The levers compound. Reactive maintenance with a parts shortage averages {heat['values'][0][0]:.1f} h of downtime; predictive "
                f"with parts available averages {heat['values'][3][2]:.1f} h, a {heat['values'][0][0]/heat['values'][3][2]:.1f}x spread. Even with "
                f"parts available, reactive runs {heat['values'][0][2]:.1f} h against {heat['values'][3][2]:.1f} h for predictive, so the two levers "
                "are not substitutes.", BODY))
    A(fig("heatmap", width=130 * mm, caption="Figure 9. Mean downtime by strategy × spare-parts status, with observation counts."))
    A(callout("Operating targets: PM compliance at or above 80%, maintenance within 60 days, lubricant quality above 50, backlog under 14 days.",
              label="TARGETS"))
    A(PageBreak())

    # ============================================================ 17 drivers
    A(Paragraph("SECTION 15", EYE))
    A(Paragraph("Measured drivers of downtime", H1))
    A(Paragraph("Correlation of each measured, non-derived input with unplanned downtime. Composite scores are excluded because they "
                "are formulas of these inputs and would 'explain' downtime by construction (Section 6).", BODY))
    A(fig("drivers", width=W, caption="Figure 10. Correlation with unplanned downtime. Blue inputs lower it; orange raise it."))
    A(table(["Input", "r with downtime", "Reading"],
            [[k.replace("_", " "), f"{v:+.3f}", "Controllable" if k in ("Preventive_Maintenance_Compliance_Pct", "Lubricant_Quality_Index",
              "Maintenance_Backlog_Days", "Days_Since_Last_Maintenance", "Spare_Parts_Lead_Time_Days") else "Condition / operating context"]
             for k, v in X["drivers_inputs"]], [72 * mm, 32 * mm, W - 104 * mm], aligns=["L", "R", "L"], size=8.2))
    A(Spacer(1, 6))
    A(callout("The strongest measured inputs are ones maintenance controls: PM compliance, lubrication, backlog and time since the last "
              "service. Vibration is the best condition signal for early warning.", label="SO WHAT"))
    A(PageBreak())

    # ============================================================ 18 sites, criticality, environment
    r_site = next(r for r in reg if r["dimension"] == "Site" and r["measure"].startswith("Revenue"))
    r_crit = next(r for r in reg if r["dimension"] == "Criticality_Class" and r["measure"].startswith("Revenue"))
    A(Paragraph("SECTION 16", EYE))
    A(Paragraph("Sites, criticality and environment", H1))
    A(Paragraph(f"Cement and drilling sites lose more per window than the lab and diagnostics sites, and the gap is real "
                f"(p = {pv(r_site['p_anova'])}), but site explains only {100*r_site['eta2']:.1f}% of loss variance. Criticality matters more "
                f"for money: critical windows average {egp(crit['loss_mean'])}, {crit['loss_mean']/low['loss_mean']:.1f}x low-criticality ones "
                f"(η² {r_crit['eta2']:.3f}).", BODY))
    A(fig("ci_site", width=140 * mm, caption="Figure 11. Mean revenue loss by site with 95% bootstrap intervals."))
    A(fig("ci_criticality", width=140 * mm, caption="Figure 12. Mean revenue loss by criticality with 95% bootstrap intervals; every step is clear of the next."))
    A(PageBreak())

    # ============================================================ 19 asset classes + nulls
    A(Paragraph("SECTION 17", EYE))
    A(Paragraph("Asset classes, environment, and what does not matter", H1))
    A(fig("asset_class", width=140 * mm, caption="Figure 13. Share of windows that are high-risk, by asset class."))
    A(fig("environment", width=130 * mm, caption="Figure 14. Share of windows that are high-risk, by environment severity."))
    A(Paragraph("Tested and found to carry no signal", H2))
    A(table(["Dimension", "Downtime p", "Loss p", "Failure-prob. p", "Verdict"],
            [[d.replace("_", " ")] + [f"{next(r for r in reg if r['dimension']==d and r['measure']==m)['p_anova']:.2f}"
                                      for m in ("Unplanned_Downtime_Hours_30D", "Revenue_Loss_EGP_30D", "Failure_Probability_Pct")] + [grey("No difference")]
             for d in ("Manufacturer_Group", "Operating_Shift")],
            [44 * mm, 26 * mm, 26 * mm, 30 * mm, W - 126 * mm], aligns=["L", "R", "R", "R", "L"]))
    A(Spacer(1, 4))
    A(Paragraph("No OEM switch, shift restructuring or site-versus-site campaign is supported by this data. Environment is a real risk "
                "factor but a condition to plan around, not a lever.", BODY))
    A(PageBreak())

    # ============================================================ 20 escalation gap
    A(Paragraph("SECTION 18", EYE))
    A(Paragraph("Finding 4: the escalation gap", H1))
    A(Paragraph(f"Executive Intervention Priority is a fixed banding of the Maintenance Priority Index (Section 6), an index that correlates "
                f"only 0.75 with failure probability. Of {hr_n} high-risk windows, {gap_n} are not escalated, carrying {egp(gap['gap_exposure'])} "
                f"of exposure ({100*gap['gap_exposure']/K['exposure_total']:.1f}% of the total). Of the 500 largest-loss windows, P1/P2 cover "
                f"{100*WL['top_decile_flagged_loss_share']:.1f}% of the loss.", BODY))
    A(fig("priority_top_decile", width=140 * mm, caption="Figure 15. The 500 largest-loss windows by the flag they received."))
    A(fig("gap_by_site", width=140 * mm, caption="Figure 16. Unescalated high-risk windows by site."))
    A(callout(f"Add a second trigger: failure probability ≥ 50% and criticality High or Critical. On this file it adds <b>{gap['rule_adds']}</b> "
              f"windows and <b>{egp(gap['rule_exposure'])}</b> of exposure ({100*gap['rule_exposure']/gap['gap_exposure']:.0f}% of the gap), "
              f"raising escalated windows from {esc_n} to {esc_n + gap['rule_adds']}. Confirm crew capacity before switching it on.",
              tone=WARN, label="RECOMMENDED RULE"))
    A(PageBreak())

    # ============================================================ 21 financial view
    cc = cost_by["Criticality_Class"]
    A(Paragraph("SECTION 19", EYE))
    A(Paragraph("The financial view", H1))
    A(tiles([(egp(loss_total), "revenue loss, all windows"), (egp(maint_total), "maintenance spend"),
             (egp(spare_total), "spare-parts spend"), (f"{loss_total/maint_total:.1f}x", "loss per EGP of maintenance")]))
    A(Spacer(1, 8))
    A(Paragraph("Maintenance spend barely moves with criticality while loss rises steeply: the budget is not following the risk.", BODY))
    A(table(["Criticality", "Windows", "Maint. cost / window", "Revenue loss / window", "Loss per EGP spent"],
            [[x, f"{prof('Criticality_Class', x)['n']:,}", egp(cc["Maintenance_Cost_EGP_30D"][x]), egp(cc["Revenue_Loss_EGP_30D"][x]),
              f"{cc['Revenue_Loss_EGP_30D'][x]/cc['Maintenance_Cost_EGP_30D'][x]:.1f}x"] for x in ("Critical", "High", "Medium", "Low")],
            [32 * mm, 22 * mm, 40 * mm, 42 * mm, W - 136 * mm], aligns=["L", "R", "R", "R", "R"]))
    A(Paragraph("Sizing the levers", H2))
    A(table(["Scenario", "Downtime avoided", "Share of downtime", "Maintenance spend avoided"], [
        ["Reactive windows run at the preventive average", f"{save_strategy:,.0f} h", f"{100*save_strategy/K['downtime_total']:.0f}%", egp(cost_save_strategy)],
        ["Shortage windows run at the available-stock average", f"{save_spares:,.0f} h", f"{100*save_spares/K['downtime_total']:.0f}%",
         egp((sp["Maintenance_Cost_EGP_30D"]["Shortage"] - sp["Maintenance_Cost_EGP_30D"]["Available"]) * short["n"])]],
        [70 * mm, 32 * mm, 30 * mm, W - 132 * mm], aligns=["L", "R", "R", "R"]))
    A(Spacer(1, 6))
    A(callout("These are upper bounds, not forecasts. They assume each association is fully causal; reactive and shortage windows also start "
              "in worse health, and the two scenarios overlap where reactive windows lack parts. A controlled pilot measures the true share.",
              tone=MUTE, label="ESTIMATED, NOT MEASURED"))
    A(PageBreak())

    # ============================================================ 22 register
    A(Paragraph("SECTION 20", EYE))
    A(Paragraph("The significance register", H1))
    A(Paragraph(f"All {len(reg)} tests, ranked by effect size. A difference counts only if ANOVA and Kruskal-Wallis both clear "
                f"p < {F['register_meta']['alpha']:.4f}. {n_real} survive.", S("b20", parent=BODY, spaceAfter=3)))
    short_m = {"Unplanned_Downtime_Hours_30D": "Downtime", "Revenue_Loss_EGP_30D": "Revenue loss", "Failure_Probability_Pct": "Failure prob."}
    A(table(["Dimension", "Measure", "F", "p (ANOVA)", "H", "p (K-W)", "η²", "Highest group", "Verdict"],
            [[r["dimension"].replace("_", " "), short_m[r["measure"]], f"{r['F']:.1f}", pv(r["p_anova"]), f"{r['H']:.1f}", pv(r["p_kruskal"]),
              f"{r['eta2']:.4f}", r["highest"], (green if r["verdict"].startswith("REAL") else grey)(r["verdict"].title())]
             for r in sorted(reg, key=lambda r: -r["eta2"])],
            [31 * mm, 19 * mm, 12 * mm, 16 * mm, 12 * mm, 16 * mm, 14 * mm, 28 * mm, W - 148 * mm],
            aligns=["L", "L", "R", "R", "R", "R", "R", "L", "L"], size=6.9, pad=1.5))
    A(PageBreak())

    # ============================================================ 23 limitations
    A(Paragraph("SECTION 21", EYE))
    A(Paragraph("Limitations and risks", H1))
    A(table(["Limitation", "Effect on conclusions", "Mitigation"], [
        ["Observational data", "Lever effects are associations; reactive and shortage windows start in worse health", "Controlled pilot before full budget (Rec. 6)"],
        ["Asset_ID not a stable key", "No per-asset history, remaining life or replacement plan", "Fix the key in the next export (Rec. 7)"],
        ["Overlapping 30-day windows", "Summed totals are not annual figures", "All comparisons use means per window"],
        ["Derived columns", "Scores restate their inputs; exposure ≈ loss", "Excluded from drivers; never added together"],
        ["Capped indices", "Efficiency index 53% at 100; PM compliance 16% at 100", "Read values at the cap as 'at least'"],
        ["Rare categories", "P1 (2 rows), three failure modes (27 rows)", "Pooled; not analysed alone"],
        ["Twelve months only", "No multi-year seasonality can be ruled out", "Re-run on the next year's export"],
        ["Escalation rule workload", f"{gap['rule_adds']} extra escalations may exceed crew capacity", "Capacity check before go-live (Rec. 5)"]],
        [40 * mm, 72 * mm, W - 112 * mm], size=8.2))
    A(Paragraph("What may and may not be stated publicly", H2))
    A(table(["Safe to state", "Do not state"], [
        ["Lever differences with their measured sizes", "That a lever causes the reduction, until a pilot measures it"],
        ["Criticality and environment as real risk factors", "That any site is better or worse managed"],
        ["Concentration figures and the escalation gap", "Anything about manufacturer or shift quality"],
        ["Means per 30-day window", "Per-asset histories, remaining life by machine, annual totals"]], [W / 2, W / 2]))
    A(PageBreak())

    # ============================================================ 24 roadmap
    A(Paragraph("SECTION 22", EYE))
    A(Paragraph("Recommendations and implementation roadmap", H1))
    A(Paragraph("The roadmap below is proposed, not measured: it sequences the seven recommendations so that each decision is taken "
                "with evidence from the step before it. Every KPI named is already on the live dashboard.", BODY))
    A(table(["Phase", "Actions", "KPI to watch (dashboard page)", "Decision gate"], [
        ["0–30 days", "Approve pilot design; capacity check for the second trigger; request a stable Asset_ID", "Escalation gap (Risk Watchlist)", "Pilot site and control site chosen"],
        ["30–90 days", "Convert the pilot site's reactive critical/high assets to planned; switch on the second trigger if capacity allows; stock shortage-prone spares at the pilot site",
         "Downtime by strategy and spares (Levers); escalated count (Overview)", "Pilot downtime vs control, with intervals"],
        ["90–180 days", "Scale what the pilot proved; manage to PM ≥ 80% and backlog < 14 days fleet-wide; pair basic crews with experts on high-risk work",
         "PM deciles and thresholds (Levers); high-risk share (Overview)", "Budget re-allocation by measured effect"],
        ["180+ days", "Re-run the analysis on the new export with a stable Asset_ID; add per-asset remaining-life and replacement views",
         "All; Data & Method re-baselined", "Next annual plan"]],
        [22 * mm, 74 * mm, 44 * mm, W - 140 * mm], size=8))
    A(Paragraph("Decisions needed this quarter", H2))
    for t in ["<b>Approve the reactive-to-planned pilot</b>, one site with a matched control, measured on the live dashboard.",
              f"<b>Approve the second escalation trigger</b>, subject to a capacity check for {esc_n + gap['rule_adds']} escalated windows.",
              "<b>Request a stable Asset_ID</b> in the next export, so the next review can plan per asset."]:
        A(Paragraph(t, BULLET, bulletText="•"))
    A(CondPageBreak(105 * mm))
    A(Spacer(1, 10))

    # ============================================================ 25 appendix
    A(Paragraph("APPENDIX", EYE))
    A(Paragraph("Reproducibility and the live dashboard", H1))
    A(table(["Artifact", "Command / location", "Notes"], [
        ["Analysis", "python3 02_Analysis/analyze_pmaris.py", "Standard library only, about 90 s; writes findings.json"],
        ["Figures", "python make_figures.py", "matplotlib; writes 04_Deliverables/figures/"],
        ["This report", "python make_full_report.py", "reportlab"],
        ["10-page assessment", "python make_report.py", "reportlab"],
        ["30-slide deck", "python make_deck.py", "python-pptx, native charts, speaker notes"],
        ["Executive presentation", "python make_exec_deck.py", "15-slide subset of the full deck"],
        ["Live dashboard", "python3 watcher.py and python3 -m http.server 8000 in 03_Dashboard", "Open http://localhost:8000/index.html"]],
        [36 * mm, 76 * mm, W - 112 * mm], size=8.2))
    A(Paragraph("The six live dashboard pages (Overview, Explorer, Levers, Sites &amp; Equipment, Risk Watchlist, Data &amp; Method) "
                "are described in the project README.", BODY))
    A(Paragraph("Verification performed", H2))
    for t in ["All six pages rendered headless in light, dark and 390 px phone width: zero console errors, no horizontal scroll.",
              "Live refresh: ten timed edits to the source CSV, 376 ms mean and 621 ms maximum from save to screen; source restored byte-identical.",
              "A half-written row was appended mid-test; the watcher skipped it and kept polling.",
              "Key figures cross-checked between this report, the 10-page assessment, both decks and the dashboard."]:
        A(Paragraph(t, BULLET, bulletText="•"))
    return s


def make():
    doc = BaseDocTemplate(OUT, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=20 * mm, bottomMargin=20 * mm,
                          title="PMARIS Comprehensive Analytical Report", author="AIB902 Group 9230 Team 1")
    doc.addPageTemplates([PageTemplate(id="main", frames=[Frame(18 * mm, 18 * mm, A4[0] - 36 * mm, A4[1] - 40 * mm, id="f",
                                                                 leftPadding=0, rightPadding=0)], onPage=decorate)])
    doc.build(build())
    return doc.page


if __name__ == "__main__":
    TOTAL[0] = make()          # first pass counts pages
    pages = make()             # second pass prints "Page n of N"
    print("wrote", OUT, "pages:", pages)
