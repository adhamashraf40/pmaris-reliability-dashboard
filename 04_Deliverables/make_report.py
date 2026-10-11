# -*- coding: utf-8 -*-
"""Generates the PMARIS Asset Reliability Assessment PDF (10 pages).

Every figure in this document is measured. The sources are:
  02_Analysis/analyze_pmaris.py   Stages 0, 1, 3, 3b -> findings.json
  04_Deliverables/make_figures.py the charts and two extra cross-tabs -> figures/
Rebuild with:  python make_figures.py && python make_report.py
Architecture: Playbook s19 (Pyramid Principle, ten pages, one job per page).
"""
import json
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph,
                                Spacer, Table, TableStyle, PageBreak, Image, KeepTogether)

HERE = Path(__file__).resolve().parent
OUT = str(HERE / "PMARIS_Reliability_Assessment.pdf")
FIG = HERE / "figures"
F = json.loads((HERE.parent / "02_Analysis" / "findings.json").read_text())
X = json.loads((FIG / "extras.json").read_text())
K, P, C, W_ = F["kpis"], F["profiles"], F["concentration"], F["watchlist"]

INK  = colors.HexColor("#14213d")
ACC  = colors.HexColor("#2a78d6")
WARN = colors.HexColor("#b3261e")
OK   = colors.HexColor("#006300")
MUTE = colors.HexColor("#5b5f6b")
RULE = colors.HexColor("#d7d9de")
BAND = colors.HexColor("#f2f4f7")

ss = getSampleStyleSheet()


def S(name, **kw):
    base = kw.pop("parent", ss["Normal"])
    return ParagraphStyle(name, parent=base, **kw)


TITLE  = S("t", fontName="Helvetica-Bold", fontSize=24, leading=28, textColor=INK, spaceAfter=4)
SUBT   = S("st", fontName="Helvetica", fontSize=11.5, leading=16, textColor=MUTE)
H1     = S("h1", fontName="Helvetica-Bold", fontSize=14, leading=18, textColor=INK, spaceBefore=4, spaceAfter=6)
H2     = S("h2", fontName="Helvetica-Bold", fontSize=10.6, leading=14, textColor=ACC, spaceBefore=8, spaceAfter=4)
BODY   = S("b", fontName="Helvetica", fontSize=9.6, leading=14.2, textColor=colors.HexColor("#22252b"),
           alignment=TA_JUSTIFY, spaceAfter=6)
BULLET = S("bu", parent=BODY, leftIndent=13, bulletIndent=2, spaceAfter=4, alignment=0)
CELL   = S("c", fontName="Helvetica", fontSize=8.5, leading=12, textColor=colors.HexColor("#22252b"))
CAP    = S("cap", fontName="Helvetica-Oblique", fontSize=8, leading=10.6, textColor=MUTE, spaceAfter=7)
EYE    = S("eye", fontName="Helvetica-Bold", fontSize=7.6, leading=10, textColor=ACC, spaceAfter=3)

W = 174 * mm
TOTAL_PAGES = 10


def egp(v):
    return f"EGP {v/1e9:.2f}B" if v >= 1e9 else (f"EGP {v/1e6:,.1f}M" if v >= 1e6 else f"EGP {v/1e3:,.0f}k")


def callout(text, tone=ACC, label="KEY FINDING"):
    inner = [[Paragraph(label, S("kk", fontName="Helvetica-Bold", fontSize=7.6, leading=10, textColor=tone))],
             [Paragraph(text, S("cot", parent=BODY, fontSize=10.2, leading=15, spaceAfter=0, alignment=0))]]
    t = Table(inner, colWidths=[W])
    t.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (0, 0), 8), ("BOTTOMPADDING", (0, 0), (0, 0), 1),
        ("TOPPADDING", (0, 1), (0, 1), 0), ("BOTTOMPADDING", (0, 1), (-1, -1), 9),
        ("BACKGROUND", (0, 0), (-1, -1), BAND), ("LINEBEFORE", (0, 0), (0, -1), 2.4, tone)]))
    return t


def table(head, rows, widths, aligns=None, size=8.5, pad=4.2):
    cs = S("cx", parent=CELL, fontSize=size, leading=size + 3.4)
    data = [[Paragraph(h, S("th", fontName="Helvetica-Bold", fontSize=8.2, leading=11, textColor=colors.white)) for h in head]]
    for r in rows:
        data.append([c if isinstance(c, Paragraph) else Paragraph(str(c), cs) for c in r])
    t = Table(data, colWidths=widths, repeatRows=1)
    st = [("BACKGROUND", (0, 0), (-1, 0), INK), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
          ("TOPPADDING", (0, 0), (-1, -1), pad), ("BOTTOMPADDING", (0, 0), (-1, -1), pad),
          ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
          ("LINEBELOW", (0, 1), (-1, -2), 0.4, RULE), ("LINEBELOW", (0, -1), (-1, -1), 0.8, INK),
          ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fafbfc")])]
    for i, a in enumerate(aligns or []):
        if a != "L":
            st.append(("ALIGN", (i, 0), (i, -1), "RIGHT" if a == "R" else "CENTER"))
    t.setStyle(TableStyle(st))
    return t


def tiles(items):
    """Row of stat tiles: [(value, label)]."""
    n = len(items)
    cells = [[Paragraph(f"<font size=16><b>{v}</b></font><br/><font size=7.8 color='#5b5f6b'>{lab}</font>",
                        S("tile", parent=CELL, leading=13)) for v, lab in items]]
    t = Table(cells, colWidths=[W / n] * n)
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), BAND), ("LINEAFTER", (0, 0), (-2, -1), 2, colors.white),
                           ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
                           ("LEFTPADDING", (0, 0), (-1, -1), 9), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    return t


def fig(name, width=W, caption=None):
    from reportlab.lib.utils import ImageReader
    iw, ih = ImageReader(str(FIG / f"{name}.png")).getSize()
    out = [Image(str(FIG / f"{name}.png"), width=width, height=width * ih / iw)]
    if caption:
        out.append(Paragraph(caption, CAP))
    return KeepTogether(out)


def red(t):
    return Paragraph("<font color='#b3261e'><b>%s</b></font>" % t, CELL)


def green(t):
    return Paragraph("<font color='#006300'><b>%s</b></font>" % t, CELL)


def grey(t):
    return Paragraph("<font color='#898781'><b>%s</b></font>" % t, CELL)


def decorate(canv, doc):
    canv.saveState()
    w, h = A4
    canv.setFillColor(INK)
    canv.rect(0, h - 12 * mm, w, 12 * mm, stroke=0, fill=1)
    canv.setFont("Helvetica-Bold", 7.6)
    canv.setFillColor(colors.white)
    canv.drawString(18 * mm, h - 8 * mm, "PMARIS ASSET RELIABILITY ASSESSMENT")
    canv.setFont("Helvetica", 7.6)
    canv.drawRightString(w - 18 * mm, h - 8 * mm, "Prepared for the Head of Reliability & Maintenance")
    canv.setStrokeColor(RULE)
    canv.setLineWidth(0.5)
    canv.line(18 * mm, 15 * mm, w - 18 * mm, 15 * mm)
    canv.setFillColor(MUTE)
    canv.drawString(18 * mm, 10.5 * mm, "Group_9230_Team1_PMARIS_Enterprise_Dataset.csv  |  5,000 observations  |  assessed 11 October 2026")
    canv.drawRightString(w - 18 * mm, 10.5 * mm, "Page %d of %d" % (doc.page, TOTAL_PAGES))
    canv.restoreState()


doc = BaseDocTemplate(OUT, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=20 * mm,
                      bottomMargin=20 * mm, title="PMARIS Asset Reliability Assessment", author="Analytics review")
doc.addPageTemplates([PageTemplate(id="main", frames=[Frame(18 * mm, 18 * mm, A4[0] - 36 * mm, A4[1] - 40 * mm,
                                                             id="f", leftPadding=0, rightPadding=0)], onPage=decorate)])

# ------------------------------------------------------------ derived numbers
prof = lambda dim, name: next(x for x in P[dim] if x["name"] == name)  # noqa: E731
react, pred, prev = (prof("Maintenance_Strategy", n) for n in ("Reactive", "Predictive", "Preventive"))
short, avail, limited = (prof("Spare_Parts_Status", n) for n in ("Shortage", "Available", "Limited"))
basic, expert = prof("Technician_Skill_Level", "Basic"), prof("Technician_Skill_Level", "Expert")
crit, low = prof("Criticality_Class", "Critical"), prof("Criticality_Class", "Low")
lv = F["levers"]
gap = X["gap"]
hr_n = K["high_risk_n"]
gap_n = hr_n - sum(1 for _ in range(0))  # placeholder kept simple below
gap_n = F["watchlist"]["high_risk_not_flagged"]
reg = F["register"]
n_real = sum(1 for r in reg if r["verdict"].startswith("REAL"))
save_strategy = (react["downtime_mean"] - prev["downtime_mean"]) * react["n"]
save_spares = (short["downtime_mean"] - avail["downtime_mean"]) * short["n"]
hb = {h["band"]: h for h in lv["health_bands"]}
heat = X["heatmap"]
worst_cell, best_cell = heat["values"][0][0], heat["values"][3][2]

s = []
A = s.append

# =====================================================================  PAGE 1
A(Paragraph("PMARIS Asset Reliability Assessment", TITLE))
A(Paragraph("What 5,000 asset-health observations across six industrial sites say about where the next "
            "Egyptian pound of maintenance budget should go.", SUBT))
A(Spacer(1, 14))
A(callout(f"Put the next EGP on four controllable levers and on a wider escalation list. Loss is concentrated: "
          f"the top 10% of observation windows carry <b>{100*C['revenue_loss_top10_share']:.1f}%</b> of revenue loss. "
          f"That concentration tracks things management controls (maintenance strategy, spare-parts availability, "
          f"crew skill and PM discipline), each splitting downtime by roughly 2x to 3x. Meanwhile the executive "
          f"priority flag misses <b>{gap_n}</b> of the <b>{hr_n}</b> high-risk windows.", tone=WARN, label="THE ANSWER"))
A(Spacer(1, 12))
A(tiles([(f"{K['revenue_loss_total']/1e9:.2f}B", "EGP revenue loss, 5,000 windows"),
         (f"{K['downtime_mean']:.1f} h", "mean unplanned downtime / window"),
         (f"{K['high_risk_pct']:.1f}%", "windows high-risk (FP ≥ 50%)"),
         (f"{100*C['high_risk_share_of_loss']:.1f}%", "of loss in those windows"),
         (f"{gap_n}", "high-risk, only P3/P4")]))
A(Spacer(1, 14))
A(Paragraph("The file at a glance", H2))
A(table(["Property", "Value"], [
    ["Source", "Group_9230_Team1_PMARIS_Enterprise_Dataset.csv, one flat CSV"],
    ["Shape", "5,000 rows × 60 columns (41 numeric, 16 categorical, 3 identifiers)"],
    ["Grain", "One row = one 30-day observation window of one asset"],
    ["Coverage", f"{F['stage0']['date_min']} to {F['stage0']['date_max']}, 12 months, 357–443 rows per month"],
    ["Scope", "6 sites in 4 industries: cement, oil & gas drilling, lab-equipment manufacturing, in-vitro diagnostics"],
    ["Playbook path", "Path A: single flat table with a transaction-level date column"],
    ["Quality", "0 missing cells, 0 duplicates, 0 type errors. One broken key (Asset_ID), see page 3"],
], [42 * mm, W - 42 * mm]))
A(Spacer(1, 12))
A(Paragraph("Contents", H2))
for i, t in enumerate(["Executive summary", "How the assessment was run", "Finding 1: loss is concentrated in high-risk windows",
                       "Finding 2: strategy and spares are the two biggest levers", "Finding 3: crew skill and PM discipline",
                       "Finding 4: the escalation flag misses most of the risk", "Where loss sits, and what does not matter",
                       "The significance register and the limits", "Recommendations and method"], start=2):
    A(Paragraph(f"{i}.&nbsp;&nbsp;{t}", S(f"toc{i}", parent=CELL, fontSize=9.4, leading=14)))
A(PageBreak())

# =====================================================================  PAGE 2
A(Paragraph("EXECUTIVE SUMMARY", EYE))
A(Paragraph("The money is concentrated, the drivers are controllable, and the escalation list is too narrow", H1))
A(Paragraph(f"Across 5,000 thirty-day observation windows, the assets lost <b>{egp(K['revenue_loss_total'])}</b> of revenue to "
            f"<b>{K['downtime_total']:,.0f}</b> hours of unplanned downtime. That loss is not spread evenly. Three arguments, "
            "each independently sufficient, support the answer on page 1.", BODY))
A(Paragraph("1. Loss is concentrated where risk is high", H2))
A(Paragraph(f"The top 10% of windows carry {100*C['revenue_loss_top10_share']:.1f}% of revenue loss (Gini {C['gini_revenue_loss']:.2f}). "
            f"The {hr_n} windows with failure probability of 50% or more ({K['high_risk_pct']:.1f}% of the file) carry "
            f"{100*C['high_risk_share_of_loss']:.1f}% of loss and {100*C['high_risk_share_of_downtime']:.1f}% of downtime. "
            f"Windows with health under 70 lose {hb['<70']['loss_mean']/hb['90+']['loss_mean']:.0f}x what windows above 90 lose.", BODY))
A(Paragraph("2. The concentration tracks levers management controls", H2))
A(Paragraph(f"Reactive maintenance averages {react['downtime_mean']:.1f} h of downtime per window against {pred['downtime_mean']:.1f} h "
            f"for predictive ({react['downtime_mean']/pred['downtime_mean']:.1f}x). Spare-part shortages average "
            f"{short['downtime_mean']:.1f} h against {avail['downtime_mean']:.1f} h with stock available "
            f"({short['downtime_mean']/avail['downtime_mean']:.1f}x). Basic crews run {basic['downtime_mean']/expert['downtime_mean']:.1f}x expert crews, and "
            f"windows below 80% PM compliance run {lv['pm_compliance']['below 80%']['downtime_mean']/lv['pm_compliance']['80% or more']['downtime_mean']:.1f}x those above. "
            "All survive a Bonferroni-corrected test with non-overlapping 95% intervals.", BODY))
A(Paragraph("3. The executive flag does not see most of it", H2))
A(Paragraph(f"Only {sum(K['priority_counts'].get(p,0) for p in ('P1 - Immediate','P2 - High'))} windows are flagged P1 or P2. "
            f"{gap_n} of the {hr_n} high-risk windows sit at P3 or P4, carrying {egp(gap['gap_exposure'])} of financial exposure, and "
            f"P1/P2 cover only {100*W_['top_decile_flagged_loss_share']:.1f}% of the loss in the worst 10% of windows. "
            "The flag is a fixed banding of a composite index that weighs failure probability only moderately.", BODY))
A(Spacer(1, 4))
A(Paragraph("The questions this review was asked, answered", H2))
A(table(["Question", "Answer", "Basis"], [
    ["Where should the next EGP of maintenance effort go?", green("Levers + escalation"), "Pages 4 to 7"],
    ["Is moving off reactive maintenance worth it?", green("Yes"), f"{react['downtime_mean']/pred['downtime_mean']:.1f}x downtime gap, large effect"],
    ["Should one site be prioritised over the others?", red("No"), "Site explains 1.3% of loss variance"],
    ["Does manufacturer (OEM) matter?", red("No"), "p = 0.57, not significant"],
    ["Does operating shift matter?", red("No"), "p = 0.49, not significant"],
    ["Is there a trend or season to schedule against?", red("No"), f"Slope {F['trend_stats']['slope_pct_of_mean']:+.1f}% of mean per month"],
    ["Can individual assets be tracked or replaced from this file?", red("No"), "Asset_ID is not a stable key"],
], [82 * mm, 34 * mm, W - 116 * mm], aligns=["L", "C", "L"]))
A(PageBreak())

# =====================================================================  PAGE 3
A(Paragraph("METHOD", EYE))
A(Paragraph("How the assessment was run", H1))
A(Paragraph("The file was taken through the AIB902 Agentic Analytics Playbook (v4.0) in order: intake and classification, "
            "a cleaning checklist, a check that each column means what its name says, descriptive insights, a significance "
            "gate, and a scoping interview with the stakeholder before anything was built. Method comes before findings so "
            "the findings are not read as opinion.", BODY))
A(Paragraph("Stage 1 cleaning checklist: passed", H2))
s1 = F["stage1"]
A(table(["Check", "Result", "Action"], [
    ["Missing cells", "0 of 300,000", green("None needed")],
    ["Exact duplicate rows / duplicate IDs", "0 / 0", green("None needed")],
    ["Numeric type errors, unparseable dates", "0 / 0", green("None needed")],
    ["Values beyond 3 SD (revenue loss)", f"{s1['outliers_3sd']['Revenue_Loss_EGP_30D']} rows", "Kept: a real heavy tail, not errors"],
    ["Load factor above 100%", f"{s1['load_over_100']} rows", "Kept: overload is physically possible"],
    ["Rare categorical levels (<1% of rows)", "3 failure modes, 27 rows", "Pooled as 'Other' for analysis"],
    ["Columns piled at a bound", "Efficiency index 53% at 100", "Treated as capped, not measured"],
], [62 * mm, 46 * mm, W - 108 * mm]))
A(Paragraph("Do the columns mean what they say? One does not", H2))
inc = s1["asset_inconsistent"]
A(table(["Column", "Finding", "Consequence"], [
    ["Asset_ID", red(f"{inc['Site']} of 500 IDs change site; {inc['Criticality_Class']} change criticality; age runs backwards for {s1['age_backwards']}"),
     "Not an asset key. Each row is an independent window. No per-asset history, churn or replacement view"],
    ["Financial_Exposure_At_Risk_EGP", f"r = {s1['derived']['Financial_Exposure_vs_Revenue_Loss']} with revenue loss", "Derived; never add the two"],
    ["Failure_Probability_Pct", f"r = {s1['derived']['Failure_Probability_vs_Health_Index']} with health index", "Mirror images; report one"],
    ["Executive_Intervention_Priority", "Fixed bands of the Maintenance Priority Index (P4 < 40, P3 40–60, P2 60–74, P1 79+)", "A formula, not a judgement; can be re-tuned"],
    ["Composite scores (risk, priority, RUL)", "Inter-correlated at 0.7–0.99", "Describe a formula; not treated as discoveries"],
], [44 * mm, 66 * mm, W - 110 * mm]))
A(Paragraph("The significance gate", H2))
A(Paragraph(f"Every difference reported in this document was tested before it was described. {len(reg)} tests (11 dimensions × 3 "
            f"measures) were run with one-way ANOVA and confirmed by the rank-based Kruskal-Wallis test; a difference counts only "
            f"if both clear the Bonferroni threshold of 0.05 / {len(reg)} = {F['register_meta']['alpha']:.4f}. {n_real} survive. "
            "With 5,000 rows almost any difference is detectable, so effect size (η², the share of variance explained) is reported "
            "beside every p-value and drives the wording: a real but small effect is called small.", BODY))
A(PageBreak())

# =====================================================================  PAGE 4
A(Paragraph("FINDING 1", EYE))
A(Paragraph("Loss is concentrated in the high-risk windows", H1))
A(Paragraph(f"A tenth of the windows carry {100*C['revenue_loss_top10_share']:.1f}% of revenue loss, and a fifth carry "
            f"{100*C['revenue_loss_top20_share']:.1f}%. A Gini coefficient of {C['gini_revenue_loss']:.2f} is in the range where "
            f"prioritisation pays: effort spread evenly across the fleet is mostly spent where little is lost. "
            f"{C['zero_loss_obs']} windows ({100*C['zero_loss_obs']/5000:.1f}%) lost nothing at all.", BODY))
A(fig("lorenz", width=118 * mm, caption="Figure 1. Lorenz curve of revenue loss across the 5,000 windows, largest first. The dashed diagonal is an even spread."))
A(Paragraph(f"The concentration is not random: it follows asset health. Windows below a health index of 70 average "
            f"{egp(hb['<70']['loss_mean'])} of loss, {hb['<70']['loss_mean']/hb['90+']['loss_mean']:.0f}x the {egp(hb['90+']['loss_mean'])} "
            f"of windows above 90, and run {hb['<70']['downtime_mean']:.1f} h of downtime against {hb['90+']['downtime_mean']:.1f} h.", BODY))
A(fig("health_bands", width=150 * mm, caption="Figure 2. Mean revenue loss per window by Asset Health Index band. Live version: dashboard, Levers page."))
A(callout(f"High-risk windows (failure probability ≥ 50%) are {K['high_risk_pct']:.1f}% of observations and carry "
          f"{100*C['high_risk_share_of_loss']:.1f}% of revenue loss. Targeting them is the shortest path to the money.", label="SO WHAT"))
A(PageBreak())

# =====================================================================  PAGE 5
A(Paragraph("FINDING 2", EYE))
A(Paragraph("Maintenance strategy and spare-parts availability are the two biggest levers", H1))
r_s = next(r for r in reg if r["dimension"] == "Maintenance_Strategy" and r["measure"].startswith("Unplanned"))
r_p = next(r for r in reg if r["dimension"] == "Spare_Parts_Status" and r["measure"].startswith("Unplanned"))
A(Paragraph(f"Reactive windows average <b>{react['downtime_mean']:.1f} h</b> of unplanned downtime; every planned strategy sits between "
            f"{pred['downtime_mean']:.1f} and {prev['downtime_mean']:.1f} h, and their intervals overlap. The step that matters is "
            f"leaving reactive, not choosing between the planned strategies. Reactive windows also run {react['emergency_pct']:.0f}% "
            f"emergency work orders against {pred['emergency_pct']:.0f}% for predictive (η² {r_s['eta2']:.3f} on downtime, "
            f"p = {r_s['p_anova']:.0e}).", BODY))
A(fig("ci_strategy", width=150 * mm, caption="Figure 3. Mean downtime by maintenance strategy with 95% bootstrap intervals (2,000 resamples)."))
A(Paragraph(f"Spare parts show a clean staircase: shortage {short['downtime_mean']:.1f} h, limited {limited['downtime_mean']:.1f} h, "
            f"available {avail['downtime_mean']:.1f} h, with no interval touching the next (η² {r_p['eta2']:.3f}). Spares status is the "
            "single strongest categorical split on downtime in the file.", BODY))
A(fig("ci_spares", width=150 * mm, caption="Figure 4. Mean downtime by spare-parts status with 95% bootstrap intervals."))
A(callout(f"Illustrative sizing, assuming the association were fully causal: had the {react['n']} reactive windows run at the preventive "
          f"average, downtime would have been {save_strategy:,.0f} h lower ({100*save_strategy/K['downtime_total']:.0f}% of the total). Had the "
          f"{short['n']} shortage windows run at the available-stock average, {save_spares:,.0f} h lower ({100*save_spares/K['downtime_total']:.0f}%). "
          "These are upper bounds, not forecasts: reactive windows also start in worse health.", tone=MUTE, label="ESTIMATED, NOT MEASURED"))
A(PageBreak())

# =====================================================================  PAGE 6
A(Paragraph("FINDING 3", EYE))
A(Paragraph("Crew skill and PM discipline make up the other two levers, and the levers compound", H1))
A(Paragraph(f"Basic crews average {basic['downtime_mean']:.1f} h against {expert['downtime_mean']:.1f} h for expert crews. PM compliance "
            f"shows a steady dose-response: the least compliant decile averages {lv['pm_deciles'][0]['downtime_mean']:.1f} h, the most "
            f"compliant {lv['pm_deciles'][-1]['downtime_mean']:.1f} h.", BODY))
A(fig("pm_deciles", width=150 * mm, caption="Figure 5. Mean downtime by PM-compliance decile (D1 least compliant)."))
names = {"pm_compliance": "PM compliance", "days_since_maint": "Days since last maintenance", "lubricant": "Lubricant quality index", "backlog": "Maintenance backlog"}
rows = []
for k, v in lv.items():
    if k in names:
        sides = [x for x in v if isinstance(v[x], dict)]
        a, b = sides
        worse, better = (a, b) if v[a]["downtime_mean"] > v[b]["downtime_mean"] else (b, a)
        rows.append([names[k], worse, f"{v[worse]['downtime_mean']:.1f} h", better, f"{v[better]['downtime_mean']:.1f} h",
                     f"{v[worse]['downtime_mean']/v[better]['downtime_mean']:.1f}x", f"{v['p_downtime']:.0e}", f"{v['eta2']:.3f}"])
A(Paragraph("Lever thresholds, below versus above", H2))
A(table(["Lever", "Worse side", "Downtime", "Better side", "Downtime", "Ratio", "p", "η²"], rows,
        [40 * mm, 24 * mm, 17 * mm, 28 * mm, 17 * mm, 14 * mm, 18 * mm, 16 * mm], aligns=["L", "L", "R", "L", "R", "R", "R", "R"], size=8.2))
A(Spacer(1, 8))
A(Paragraph(f"The levers compound. The worst combination, reactive strategy with a parts shortage, averages {worst_cell:.1f} h of downtime; "
            f"predictive with parts available averages {best_cell:.1f} h, a {worst_cell/best_cell:.1f}x spread.", BODY))
A(fig("heatmap", width=120 * mm, caption="Figure 6. Mean downtime by strategy × spare-parts status, with observation counts per cell."))
A(PageBreak())

# =====================================================================  PAGE 7
A(Paragraph("FINDING 4", EYE))
A(Paragraph("The executive escalation flag misses most of the risk", H1))
A(Paragraph(f"Executive Intervention Priority is a fixed banding of the Maintenance Priority Index. That index correlates only "
            f"0.75 with failure probability, so high-risk windows routinely land in P3 or P4. Of the {hr_n} windows with "
            f"failure probability of 50% or more, <b>{gap_n}</b> are not escalated. They carry <b>{egp(gap['gap_exposure'])}</b> of "
            f"financial exposure, {100*gap['gap_exposure']/K['exposure_total']:.1f}% of the file's total.", BODY))
A(fig("priority_top_decile", width=140 * mm, caption=f"Figure 7. The 500 windows with the largest revenue loss, by the flag they received. P1/P2 cover {100*W_['top_decile_flagged_loss_share']:.1f}% of their loss."))
A(fig("gap_by_site", width=140 * mm, caption="Figure 8. Unescalated high-risk windows by site. Every site has them; heavy-industry sites have the most."))
A(callout(f"Add a second escalation trigger: failure probability ≥ 50% and criticality High or Critical. On this file it would add "
          f"<b>{gap['rule_adds']}</b> windows carrying <b>{egp(gap['rule_exposure'])}</b> of exposure "
          f"({100*gap['rule_exposure']/gap['gap_exposure']:.0f}% of the gap's exposure). It would raise the escalated count from "
          f"{sum(K['priority_counts'].get(p,0) for p in ('P1 - Immediate','P2 - High'))} to "
          f"{sum(K['priority_counts'].get(p,0) for p in ('P1 - Immediate','P2 - High')) + gap['rule_adds']}, so capacity to act on it must be "
          "confirmed before it goes live.", tone=WARN, label="RECOMMENDED RULE"))
A(PageBreak())

# =====================================================================  PAGE 8
A(Paragraph("CONTEXT", EYE))
A(Paragraph("Where loss sits, and what does not matter", H1))
r_site = next(r for r in reg if r["dimension"] == "Site" and r["measure"].startswith("Revenue"))
r_crit = next(r for r in reg if r["dimension"] == "Criticality_Class" and r["measure"].startswith("Revenue"))
A(Paragraph(f"Cement and drilling sites lose more per window than the lab and diagnostics sites, and the gap is real "
            f"(p = {r_site['p_anova']:.0e}). It is also small: site explains {100*r_site['eta2']:.1f}% of loss variance. "
            f"Criticality matters more for money: critical windows average {egp(crit['loss_mean'])}, {crit['loss_mean']/low['loss_mean']:.1f}x "
            f"low-criticality ones (η² {r_crit['eta2']:.3f}).", BODY))
A(fig("ci_site", width=150 * mm, caption="Figure 9. Mean revenue loss by site with 95% bootstrap intervals. The four heavy-industry sites overlap each other."))
A(Paragraph("What was tested and found to carry no signal", H2))
A(table(["Dimension", "Downtime p", "Loss p", "Failure-prob. p", "Verdict"], [
    [d.replace("_", " ")] + [f"{next(r for r in reg if r['dimension']==d and r['measure']==m)['p_anova']:.2f}"
                             for m in ("Unplanned_Downtime_Hours_30D", "Revenue_Loss_EGP_30D", "Failure_Probability_Pct")] + [grey("No difference")]
    for d in ("Manufacturer_Group", "Operating_Shift")] + [
    ["Month (trend)", "–", f"slope {F['trend_stats']['slope_pct_of_mean']:+.2f}%/mo", "–", grey("Flat; lag-1 r = %.2f" % F['trend_stats']['lag1'])]],
    [44 * mm, 26 * mm, 32 * mm, 30 * mm, W - 132 * mm], aligns=["L", "R", "R", "R", "L"]))
A(Spacer(1, 6))
A(Paragraph("A site-versus-site campaign, an OEM switch or a shift change would be acting on a difference the data does not show. "
            "Environment severity does matter for risk (severe environments are 3.8x as likely to be high-risk as controlled ones), but "
            "environment is a condition to plan around, not a lever.", BODY))
A(fig("environment", width=130 * mm, caption="Figure 10. Share of windows that are high-risk, by environment severity."))
A(PageBreak())

# =====================================================================  PAGE 9
A(Paragraph("EVIDENCE", EYE))
A(Paragraph("The significance register, and the limits of this file", H1))
A(Paragraph(f"All {len(reg)} tests, ranked by effect size. Both tests must clear p < {F['register_meta']['alpha']:.4f}.", S("b9", parent=BODY, spaceAfter=3)))
short_m = {"Unplanned_Downtime_Hours_30D": "Downtime", "Revenue_Loss_EGP_30D": "Revenue loss", "Failure_Probability_Pct": "Failure prob."}


def pv(p):
    return "<1e-300" if p == 0 else (f"{p:.0e}" if p < 1e-3 else f"{p:.3f}")


rr = sorted(reg, key=lambda r: -r["eta2"])
A(table(["Dimension", "Measure", "F", "p (ANOVA)", "p (K-W)", "η²", "Verdict"],
        [[r["dimension"].replace("_", " "), short_m[r["measure"]], f"{r['F']:.1f}", pv(r["p_anova"]), pv(r["p_kruskal"]),
          f"{r['eta2']:.4f}", (green if r["verdict"].startswith("REAL") else grey)(r["verdict"].title().replace("Real", "Real"))]
         for r in rr],
        [38 * mm, 24 * mm, 15 * mm, 22 * mm, 22 * mm, 17 * mm, W - 138 * mm], aligns=["L", "L", "R", "R", "R", "R", "L"], size=7.2, pad=1.5))
A(Paragraph("Limits a reader must keep in mind", H2))
for t in ["<b>Association, not proof of cause.</b> This is observational data. Reactive windows start in worse health, so part of "
          "the strategy gap is which assets end up reactive. A controlled pilot is the way to measure the causal share.",
          "<b>No asset history.</b> Asset_ID is not a stable key, so nothing here tracks one machine over time, and no per-asset "
          "replacement, remaining-life or churn view is supportable.",
          "<b>Summed 30-day windows are not annual totals.</b> Totals add overlapping 30-day snapshots; use means per window "
          "for comparisons."]:
    A(Paragraph(t, BULLET, bulletText="•"))
A(PageBreak())

# =====================================================================  PAGE 10
A(Paragraph("RECOMMENDATIONS", EYE))
A(Paragraph("What to do, what may be published, and how to reproduce it", H1))
recs = [
    ("Move reactive windows onto a planned strategy, starting with critical and high-criticality assets.",
     f"{react['n']} reactive windows average {react['downtime_mean']:.1f} h vs {prev['downtime_mean']:.1f} h preventive."),
    ("Fund spare-parts availability for the asset classes that hit shortage.",
     f"Shortage {short['downtime_mean']:.1f} h vs available {avail['downtime_mean']:.1f} h; the largest categorical effect."),
    ("Hold PM compliance at 80% or above, and clear backlog beyond 14 days.",
     f"Each threshold splits downtime about 2x."),
    ("Prioritise upskilling basic and intermediate crews on high-risk assets.",
     f"Basic {basic['downtime_mean']:.1f} h vs expert {expert['downtime_mean']:.1f} h."),
    ("Add the second escalation trigger (FP ≥ 50% and criticality High/Critical), after confirming capacity.",
     f"Adds {gap['rule_adds']} windows and {egp(gap['rule_exposure'])} of exposure to the watched list."),
    ("Run a controlled pilot before scaling: convert one site's reactive fleet and measure against a matched site.",
     "Turns an association into a causal estimate before full budget is committed."),
    ("Fix the asset key in the next export.",
     "A stable Asset_ID unlocks per-asset history, remaining-life tracking and replacement planning."),
]
A(table(["#", "Recommendation", "Evidence"], [[str(i), a, b] for i, (a, b) in enumerate(recs, 1)],
        [8 * mm, 92 * mm, W - 100 * mm], aligns=["C", "L", "L"]))
A(Paragraph("What may be published", H2))
A(table(["Safe to state", "Do not state"], [
    ["Lever differences (strategy, spares, skill, PM) with their sizes", "That any lever causes the reduction, until a pilot measures it"],
    ["Criticality and environment as real risk factors", "A ranking of sites as better or worse managed"],
    ["Concentration figures and the escalation gap", "Anything about manufacturer or shift quality"],
    ["Means per 30-day window", "Per-asset histories, remaining life by machine, or annual totals"],
], [W / 2, W / 2]))
A(Paragraph("Method and reproducibility", H2))
for t in ["<b>Analysis:</b> <font name='Courier'>python 02_Analysis/analyze_pmaris.py</font>, standard library only, about 90 s; writes findings.json.",
          "<b>Figures and report:</b> <font name='Courier'>python 04_Deliverables/make_figures.py</font> then "
          "<font name='Courier'>make_report.py</font> (matplotlib, reportlab).",
          "<b>Live dashboard:</b> <font name='Courier'>python watcher.py</font> and <font name='Courier'>python -m http.server 8000</font> "
          "in 03_Dashboard, six pages. Live refresh measured at 376 ms mean, 621 ms max over 10 timed edits.",
          "<b>Measured vs estimated:</b> every figure is measured from the file except the two sizing estimates on page 5, which are labelled."]:
    A(Paragraph(t, BULLET, bulletText="•"))

doc.build(s)
print("wrote", OUT)
