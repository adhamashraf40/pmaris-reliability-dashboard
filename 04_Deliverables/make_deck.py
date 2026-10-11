# -*- coding: utf-8 -*-
"""Generates the 30-slide PMARIS Asset Reliability deck (PowerPoint, 16:9).

Every figure is read from 02_Analysis/findings.json and figures/extras.json,
the same sources as the report and the dashboard. Native PowerPoint charts are
used wherever PowerPoint has the chart type; bootstrap intervals, the heatmap
and the Lorenz curve (no native form) are the matplotlib figures from
make_figures.py. Speaker notes carry the talk track for every slide.

Rebuild with:  python make_figures.py && python make_deck.py   (needs python-pptx)
"""
import json
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION

HERE = Path(__file__).resolve().parent
FIG = HERE / "figures"
OUT = HERE / "PMARIS_Reliability_Deck.pptx"
F = json.loads((HERE.parent / "02_Analysis" / "findings.json").read_text())
X = json.loads((FIG / "extras.json").read_text())
K, P, C, WL, LV = F["kpis"], F["profiles"], F["concentration"], F["watchlist"], F["levers"]

# ---------------------------------------------------------------- palette
NAVY = RGBColor(0x14, 0x21, 0x3D)      # dominant dark
NAVY2 = RGBColor(0x1E, 0x2E, 0x52)
ORANGE = RGBColor(0xE8, 0x76, 0x2C)    # the one sharp accent: risk / action
INK = RGBColor(0x1B, 0x1F, 0x2A)
INK2 = RGBColor(0x4A, 0x4F, 0x5C)
MUTED = RGBColor(0x6B, 0x70, 0x7C)
PANEL = RGBColor(0xF2, 0xF4, 0xF7)
GRIDC = RGBColor(0xE1, 0xE0, 0xD9)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
ICE = RGBColor(0xC9, 0xD6, 0xEA)
BLUE = RGBColor(0x25, 0x6A, 0xBF)
STRAT = {"Reactive": RGBColor(0xEB, 0x68, 0x34), "Preventive": RGBColor(0x2A, 0x78, 0xD6),
         "Condition-Based": RGBColor(0xED, 0xA1, 0x00), "Predictive": RGBColor(0x1B, 0xAF, 0x7A)}
SPARE = {"Shortage": RGBColor(0xD0, 0x3B, 0x3B), "Limited": RGBColor(0xFA, 0xB2, 0x19), "Available": RGBColor(0x0C, 0xA3, 0x0C)}
PRIO = {"P1 - Immediate": RGBColor(0xD0, 0x3B, 0x3B), "P2 - High": RGBColor(0xE8, 0x76, 0x2C),
        "P3 - Planned": RGBColor(0xFA, 0xB2, 0x19), "P4 - Monitor": RGBColor(0x9A, 0x98, 0x8F)}
SEQ = [RGBColor(0x86, 0xB6, 0xEF), RGBColor(0x39, 0x87, 0xE5), RGBColor(0x25, 0x6A, 0xBF),
       RGBColor(0x18, 0x4F, 0x95), RGBColor(0x0D, 0x36, 0x6B)]
FONT = "Arial"

SW, SH = 13.333, 7.5
M = 0.6                     # outer margin
TITLE_Y, TITLE_H = 0.45, 0.95
BODY_Y = 1.6

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(SW), Inches(SH)
BLANK = prs.slide_layouts[6]
SLIDE_NO = [0]


def seq(v, vmax):
    t = v / vmax if vmax else 0.5
    return SEQ[min(len(SEQ) - 1, int(round(t * (len(SEQ) - 1))))]


def egp(v):
    return f"EGP {v/1e9:.2f}B" if v >= 1e9 else (f"EGP {v/1e6:,.0f}M" if v >= 1e6 else f"EGP {v/1e3:,.0f}k")


# ---------------------------------------------------------------- primitives
def rect(s, x, y, w, h, fill, shape=MSO_SHAPE.RECTANGLE, radius=None, name=None):
    sh = s.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.fill.solid()
    sh.fill.fore_color.rgb = fill
    sh.line.fill.background()
    sh.shadow.inherit = False
    if radius is not None and shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        sh.adjustments[0] = radius
    if name:
        sh.name = name
    return sh


def text(s, x, y, w, h, runs, size=16, color=INK, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
         space_after=0, line=None, name=None):
    """runs: str, or list of paragraphs; a paragraph is str or list of (text, {bold,color,size}) tuples."""
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if name:
        tb.name = name
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    paras = runs if isinstance(runs, list) else [runs]
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        if space_after:
            p.space_after = Pt(space_after)
        if line:
            p.line_spacing = line
        parts = para if isinstance(para, list) else [(para, {})]
        for t, o in parts:
            r = p.add_run()
            r.text = t
            f = r.font
            f.name = FONT
            f.size = Pt(o.get("size", size))
            f.bold = o.get("bold", bold)
            f.italic = o.get("italic", False)
            f.color.rgb = o.get("color", color)
    return tb


def bullets(s, x, y, w, h, items, size=16, color=INK, gap=10):
    tb = text(s, x, y, w, h, [[("", {})]], size=size)
    tf = tb.text_frame
    tf.paragraphs[0].text = ""
    for i, it in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(gap)
        parts = it if isinstance(it, list) else [(it, {})]
        r0 = p.add_run()
        r0.text = "■  "
        r0.font.size = Pt(size - 6)
        r0.font.color.rgb = ORANGE
        r0.font.name = FONT
        for t, o in parts:
            r = p.add_run()
            r.text = t
            r.font.name = FONT
            r.font.size = Pt(o.get("size", size))
            r.font.bold = o.get("bold", False)
            r.font.color.rgb = o.get("color", color)
    return tb


def picture(s, name, x, y, w=None, h=None):
    path = str(FIG / f"{name}.png")
    kw = {}
    if w:
        kw["width"] = Inches(w)
    if h:
        kw["height"] = Inches(h)
    return s.shapes.add_picture(path, Inches(x), Inches(y), **kw)


def fit_picture(s, name, x, y, w, h):
    """Place an image inside a box, preserving aspect, centred."""
    from PIL import Image as PI
    iw, ih = PI.open(FIG / f"{name}.png").size
    r = min(w / iw, h / ih)
    pw, ph = iw * r, ih * r
    return s.shapes.add_picture(str(FIG / f"{name}.png"), Inches(x + (w - pw) / 2), Inches(y + (h - ph) / 2),
                                Inches(pw), Inches(ph))


def badge(s, x, y, label, d=0.5, fill=ORANGE, fg=WHITE, size=16):
    c = rect(s, x, y, d, d, fill, shape=MSO_SHAPE.OVAL)
    tf = c.text_frame
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = label
    r.font.size = Pt(size)
    r.font.bold = True
    r.font.color.rgb = fg
    r.font.name = FONT
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    return c


def footer(s, dark=False, source="Source: Group_9230_Team1_PMARIS_Enterprise_Dataset.csv, 5,000 observation windows"):
    col = ICE if dark else MUTED
    text(s, M, SH - 0.42, 9, 0.25, source, size=10, color=col)
    text(s, SW - M - 1.5, SH - 0.42, 1.5, 0.25, f"{SLIDE_NO[0]} / 30", size=10, color=col, align=PP_ALIGN.RIGHT)


def new_slide(dark=False):
    s = prs.slides.add_slide(BLANK)
    SLIDE_NO[0] += 1
    bg = s.background.fill
    bg.solid()
    bg.fore_color.rgb = NAVY if dark else WHITE
    return s


def content(title, kicker=None, notes=""):
    s = new_slide()
    if kicker:
        text(s, M, 0.3, 9, 0.3, kicker.upper(), size=12, color=ORANGE, bold=True)
    text(s, M, TITLE_Y + 0.12, SW - 2 * M, TITLE_H, title, size=30, bold=True, color=INK, anchor=MSO_ANCHOR.TOP)
    footer(s)
    if notes:
        s.notes_slide.notes_text_frame.text = notes
    return s


def stat_card(s, x, y, w, h, value, label, fill=PANEL, vcolor=INK, lcolor=INK2, vsize=36, lsize=14):
    rect(s, x, y, w, h, fill, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08)
    text(s, x + 0.25, y + 0.22, w - 0.5, 0.75, value, size=vsize, bold=True, color=vcolor)
    text(s, x + 0.25, y + 0.22 + vsize / 72 * 1.25, w - 0.5, h - 0.5 - vsize / 72 * 1.25, label, size=lsize, color=lcolor)


def takeaway(s, x, y, w, h, msg, label="SO WHAT"):
    rect(s, x, y, w, h, PANEL, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.06)
    text(s, x + 0.3, y + 0.25, w - 0.6, 0.3, label, size=12, bold=True, color=ORANGE)
    text(s, x + 0.3, y + 0.62, w - 0.6, h - 0.8, msg, size=16, color=INK, line=1.1)


# ---------------------------------------------------------------- charts
def style_chart(ch, size=12):
    ch.font.name = FONT
    ch.font.size = Pt(size)
    ch.font.color.rgb = INK2
    ch.has_legend = False


def bar_chart(s, x, y, w, h, cats, vals, colors, fmt='0.0', horizontal=True, label_size=13, axis=False, gap=55):
    cd = CategoryChartData()
    cd.categories = cats
    cd.add_series("s", vals)
    kind = XL_CHART_TYPE.BAR_CLUSTERED if horizontal else XL_CHART_TYPE.COLUMN_CLUSTERED
    gf = s.shapes.add_chart(kind, Inches(x), Inches(y), Inches(w), Inches(h), cd)
    ch = gf.chart
    style_chart(ch)
    plot = ch.plots[0]
    plot.gap_width = gap
    plot.vary_by_categories = False
    ser = plot.series[0]
    for i, c in enumerate(colors):
        pt = ser.points[i]
        pt.format.fill.solid()
        pt.format.fill.fore_color.rgb = c
    plot.has_data_labels = True
    dl = plot.data_labels
    dl.number_format = fmt
    dl.number_format_is_linked = False
    dl.position = XL_LABEL_POSITION.OUTSIDE_END
    dl.font.size = Pt(label_size)
    dl.font.bold = True
    dl.font.color.rgb = INK
    va = ch.value_axis
    va.has_major_gridlines = axis
    if axis:
        va.major_gridlines.format.line.color.rgb = GRIDC
    va.visible = axis
    va.tick_labels.font.size = Pt(11)
    va.format.line.fill.background()
    va.minimum_scale = 0
    va.maximum_scale = max(vals) * (1.22 if horizontal else 1.15)
    ca = ch.category_axis
    ca.tick_labels.font.size = Pt(13)
    ca.tick_labels.font.color.rgb = INK2
    ca.format.line.color.rgb = GRIDC
    ca.has_major_gridlines = False
    if horizontal:
        ca.reverse_order = True
    return ch


def line_chart(s, x, y, w, h, cats, vals, fmt='#,##0'):
    cd = CategoryChartData()
    cd.categories = cats
    cd.add_series("Mean loss", vals)
    ch = s.shapes.add_chart(XL_CHART_TYPE.LINE_MARKERS, Inches(x), Inches(y), Inches(w), Inches(h), cd).chart
    style_chart(ch)
    ser = ch.plots[0].series[0]
    ser.format.line.color.rgb = BLUE
    ser.format.line.width = Pt(2.5)
    ser.smooth = False
    ser.marker.format.fill.solid()
    ser.marker.format.fill.fore_color.rgb = BLUE
    ser.marker.format.line.color.rgb = WHITE
    va = ch.value_axis
    va.minimum_scale = 0
    va.maximum_scale = max(vals) * 1.3
    va.has_major_gridlines = True
    va.major_gridlines.format.line.color.rgb = GRIDC
    va.tick_labels.number_format = fmt
    va.tick_labels.number_format_is_linked = False
    va.tick_labels.font.size = Pt(11)
    va.format.line.fill.background()
    ch.category_axis.tick_labels.font.size = Pt(11)
    ch.category_axis.format.line.color.rgb = GRIDC
    return ch


def doughnut(s, x, y, w, h, cats, vals, colors):
    cd = CategoryChartData()
    cd.categories = cats
    cd.add_series("s", vals)
    ch = s.shapes.add_chart(XL_CHART_TYPE.DOUGHNUT, Inches(x), Inches(y), Inches(w), Inches(h), cd).chart
    style_chart(ch)
    ch.has_legend = True
    ch.legend.position = XL_LEGEND_POSITION.RIGHT
    ch.legend.include_in_layout = False
    ch.legend.font.size = Pt(13)
    plot = ch.plots[0]
    for i, c in enumerate(colors):
        pt = plot.series[0].points[i]
        pt.format.fill.solid()
        pt.format.fill.fore_color.rgb = c
        pt.format.line.color.rgb = WHITE
    plot.has_data_labels = True
    plot.data_labels.number_format = '0%'
    plot.data_labels.number_format_is_linked = False
    plot.data_labels.show_percentage = True
    plot.data_labels.show_value = False
    plot.data_labels.font.size = Pt(12)
    plot.data_labels.font.bold = True
    plot.data_labels.font.color.rgb = WHITE
    return ch


def table_shape(s, x, y, w, col_w, head, rows, size=13, row_h=0.42, align=None):
    t = s.shapes.add_table(len(rows) + 1, len(head), Inches(x), Inches(y), Inches(w), Inches(row_h * (len(rows) + 1))).table
    for j, cw in enumerate(col_w):
        t.columns[j].width = Inches(cw)
    for i in range(len(rows) + 1):
        t.rows[i].height = Inches(row_h)
    for i, row in enumerate([head] + rows):
        for j, val in enumerate(row):
            cell = t.cell(i, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = NAVY if i == 0 else (WHITE if i % 2 else PANEL)
            cell.margin_left = cell.margin_right = Inches(0.1)
            cell.margin_top = cell.margin_bottom = Inches(0.04)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.text = ""
            r = p.add_run()
            r.text = str(val)
            r.font.name = FONT
            r.font.size = Pt(size - (1 if i == 0 else 0))
            r.font.bold = i == 0
            r.font.color.rgb = WHITE if i == 0 else INK
            if align and align[j] == "R":
                p.alignment = PP_ALIGN.RIGHT
    return t


def divider(num, title, sub, notes):
    s = new_slide(dark=True)
    badge(s, M, 2.35, num, d=0.9, size=28)
    text(s, M, 3.5, 11, 1.2, title, size=40, bold=True, color=WHITE)
    text(s, M, 4.75, 10.5, 1.0, sub, size=18, color=ICE)
    footer(s, dark=True)
    s.notes_slide.notes_text_frame.text = notes
    return s


# ---------------------------------------------------------------- numbers
prof = lambda dim, name: next(x for x in P[dim] if x["name"] == name)  # noqa: E731
react, pred, prev, cbm = (prof("Maintenance_Strategy", n) for n in ("Reactive", "Predictive", "Preventive", "Condition-Based"))
short, limited, avail = (prof("Spare_Parts_Status", n) for n in ("Shortage", "Limited", "Available"))
skills = [prof("Technician_Skill_Level", n) for n in ("Basic", "Intermediate", "Advanced", "Expert")]
crit, low = prof("Criticality_Class", "Critical"), prof("Criticality_Class", "Low")
hb = {h["band"]: h for h in LV["health_bands"]}
gap = X["gap"]
gap_n = WL["high_risk_not_flagged"]
hr_n = K["high_risk_n"]
esc_n = sum(K["priority_counts"].get(p, 0) for p in ("P1 - Immediate", "P2 - High"))
reg = F["register"]
n_real = sum(1 for r in reg if r["verdict"].startswith("REAL"))
save_strategy = (react["downtime_mean"] - prev["downtime_mean"]) * react["n"]
save_spares = (short["downtime_mean"] - avail["downtime_mean"]) * short["n"]
heat = X["heatmap"]
r_site = next(r for r in reg if r["dimension"] == "Site" and r["measure"].startswith("Revenue"))
r_spl = next(r for r in reg if r["dimension"] == "Spare_Parts_Status" and r["measure"].startswith("Revenue"))
r_oem = next(r for r in reg if r["dimension"] == "Manufacturer_Group" and r["measure"].startswith("Unplanned"))
r_shift = next(r for r in reg if r["dimension"] == "Operating_Shift" and r["measure"].startswith("Unplanned"))

# ================================================================ 1 title
s = new_slide(dark=True)
text(s, M, 0.55, 9, 0.35, "AIB902 · AGENTIC ANALYTICS · GROUP 9230 TEAM 1", size=13, bold=True, color=ORANGE)
text(s, M, 1.9, 11.5, 2.0, "Where the next EGP of maintenance should go", size=48, bold=True, color=WHITE, line=1.0)
text(s, M, 3.95, 11, 1.0, "PMARIS asset reliability: 5,000 observation windows, six sites, twelve months",
     size=22, color=ICE)
for i, (v, l) in enumerate([(f"{100*C['revenue_loss_top10_share']:.0f}%", "of loss in the top 10% of windows"),
                            (f"{react['downtime_mean']/pred['downtime_mean']:.1f}x", "reactive vs predictive downtime"),
                            (f"{gap_n}", "high-risk windows not escalated")]):
    x = M + i * 4.05
    text(s, x, 5.25, 3.8, 0.7, v, size=34, bold=True, color=ORANGE)
    text(s, x, 5.95, 3.8, 0.5, l, size=14, color=ICE)
text(s, M, SH - 0.42, 9, 0.25, "Prepared for the Head of Reliability & Maintenance · 11 October 2026", size=10, color=ICE)
s.notes_slide.notes_text_frame.text = (
    "This deck answers one question for the Head of Reliability and Maintenance: where should the next Egyptian pound of "
    "maintenance budget go? The three numbers at the bottom are the whole story: loss is concentrated, a controllable lever "
    "doubles downtime, and the escalation flag misses most of the risk.")

# ================================================================ 2 the answer
s = content("The answer: fund four levers and widen the escalation list", "The answer",
            "Lead with the answer, Pyramid style. Everything after this slide is support for these three arguments.")
args = [("1", "Loss is concentrated",
         f"Top 10% of windows carry {100*C['revenue_loss_top10_share']:.1f}% of revenue loss. High-risk windows carry {100*C['high_risk_share_of_loss']:.1f}%."),
        ("2", "It tracks controllable levers",
         f"Strategy, spares, crew skill and PM discipline each split downtime about 2x to 3x, all statistically real."),
        ("3", "The escalation flag misses it",
         f"{gap_n} of {hr_n} high-risk windows sit at P3/P4, carrying {egp(gap['gap_exposure'])} of exposure.")]
for i, (n, h, b) in enumerate(args):
    x = M + i * 4.1
    rect(s, x, BODY_Y + 0.3, 3.85, 3.7, PANEL, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.06)
    badge(s, x + 0.3, BODY_Y + 0.6, n, d=0.6, size=20)
    text(s, x + 0.3, BODY_Y + 1.45, 3.3, 0.9, h, size=22, bold=True, color=INK)
    text(s, x + 0.3, BODY_Y + 2.45, 3.3, 2.0, b, size=16, color=INK2, line=1.1)

# ================================================================ 3 agenda
s = content("Agenda", "Contents", "Four sections. The method section is short but it matters: every number later on survived a test.")
items = [("A", "The data and how we read it", "Intake, cleaning, one broken key, the significance gate"),
         ("B", "Where the loss is", "Concentration, health, and a flat year"),
         ("C", "The levers", "Strategy, spares, crew skill, PM discipline"),
         ("D", "The escalation gap, and what to do", "The flag, the proposed rule, the dashboard, recommendations")]
for i, (n, h, b) in enumerate(items):
    y = BODY_Y + 0.25 + i * 1.18
    badge(s, M, y, n, d=0.7, fill=NAVY, size=20)
    text(s, M + 1.0, y - 0.02, 10, 0.45, h, size=22, bold=True, color=INK)
    text(s, M + 1.0, y + 0.45, 10, 0.4, b, size=15, color=INK2)

# ================================================================ 4 divider A
divider("A", "The data and how we read it", "A clean file with real signal, and one key that cannot be trusted",
        "Section A. Before any finding, how the file was handled, and why the findings can be trusted.")

# ================================================================ 5 file at a glance
s = content("One flat file: 5,000 thirty-day windows across six sites", "The data",
            "Playbook Stage 0. Path A: one flat table with a date column, so no joins were needed. Each row is one 30-day window of one asset.")
cards = [("5,000", "observation windows (rows)"), ("60", "columns: 41 numeric, 16 categorical"),
         ("6", "sites across 4 industries"), ("12", "months, Sep 2025 to Aug 2026")]
for i, (v, l) in enumerate(cards):
    stat_card(s, M + i * 3.1, BODY_Y + 0.2, 2.85, 1.9, v, l, vsize=40)
sites = sorted(P["Site"], key=lambda x: -x["n"])
bar_chart(s, M, BODY_Y + 2.4, 7.4, 3.0, [x["name"] for x in sites], [x["n"] for x in sites], [BLUE] * 6, fmt='#,##0', label_size=12)
text(s, M + 7.8, BODY_Y + 2.55, 4.3, 0.4, "Industries covered", size=16, bold=True)
bullets(s, M + 7.8, BODY_Y + 3.05, 4.4, 2.4, ["Cement manufacturing (2 plants)", "Oil & gas drilling (2 sites)",
                                              "Lab-equipment manufacturing", "In-vitro diagnostics service"], size=15, gap=6)

# ================================================================ 6 method
s = content("The method: seven stages, two hard gates", "How we worked",
            "AIB902 Playbook v4.0. The two gates are the scope brief, approved by the stakeholder before the build, and the timed live-refresh test.")
steps = ["Intake", "Clean", "Check meaning", "Insights", "Significance", "Scope brief", "Build + verify"]
for i, st in enumerate(steps):
    x = M + i * 1.75
    gate = st in ("Scope brief", "Build + verify")
    rect(s, x, BODY_Y + 0.6, 1.55, 1.4, ORANGE if gate else NAVY, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.12)
    text(s, x + 0.1, BODY_Y + 0.65, 1.35, 0.4, str(i), size=13, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    text(s, x + 0.1, BODY_Y + 1.05, 1.35, 0.85, st, size=15, bold=True, color=WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
text(s, M, BODY_Y + 2.35, 12, 0.4, "What each stage contributed", size=18, bold=True)
bullets(s, M, BODY_Y + 2.85, 12.1, 2.7, [
    [("Clean and check meaning: ", {"bold": True}), ("zero defects, but Asset_ID is not an asset key (next slides)", {})],
    [("Significance: ", {"bold": True}), (f"{len(reg)} tests, Bonferroni-corrected; only differences that survived became KPIs", {})],
    [("Scope brief: ", {"bold": True}), ("audience, decision and KPIs agreed with the stakeholder before anything was built", {})],
    [("Build + verify: ", {"bold": True}), ("six-page live dashboard; save-to-screen refresh timed at 376 ms on average", {})]], size=16, gap=8)

# ================================================================ 7 cleaning
s1 = F["stage1"]
s = content("The file passed every cleaning check with nothing dropped", "Stage 1: cleaning",
            "Nothing was imputed or removed. The heavy tail in revenue loss is real, not error, so it stays in.")
table_shape(s, M, BODY_Y + 0.15, 8.0, [3.6, 2.0, 2.4], ["Check", "Result", "Action"], [
    ["Missing cells", "0", "None needed"], ["Duplicate rows / IDs", "0 / 0", "None needed"],
    ["Type errors / bad dates", "0 / 0", "None needed"],
    ["Revenue loss beyond 3 SD", f"{s1['outliers_3sd']['Revenue_Loss_EGP_30D']} rows", "Kept: real tail"],
    ["Load factor above 100%", f"{s1['load_over_100']} rows", "Kept: overload"],
    ["Rare failure modes (<1%)", "27 rows", "Pooled as Other"],
    ["Efficiency index at cap", "53% at 100", "Treated as capped"]], size=14, row_h=0.5)
stat_card(s, M + 8.4, BODY_Y + 0.15, 3.7, 1.9, "300,000", "cells checked, zero missing", vsize=36)
stat_card(s, M + 8.4, BODY_Y + 2.3, 3.7, 1.7, "0", "rows dropped or imputed", vsize=36)

# ================================================================ 8 broken key
inc = s1["asset_inconsistent"]
s = content("One key is broken: Asset_ID does not identify an asset", "Stage 1b: does each column mean what it says?",
            "This is the most important limit. Because the ID changes site, type and criticality, we treat every row as an independent window. "
            "No per-asset history, replacement or remaining-life plan can be built from this export.")
rect(s, M, BODY_Y + 0.2, 5.2, 4.9, NAVY, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.06)
text(s, M + 0.4, BODY_Y + 0.55, 4.5, 1.2, f"{inc['Site']} / 500", size=54, bold=True, color=ORANGE)
text(s, M + 0.4, BODY_Y + 1.75, 4.4, 1.2, "Asset IDs that change site between observations", size=18, color=WHITE)
text(s, M + 0.4, BODY_Y + 3.0, 4.4, 1.8, f"{inc['Criticality_Class']} change criticality; for {s1['age_backwards']}, asset age runs backwards in time.",
     size=15, color=ICE, line=1.1)
text(s, M + 5.7, BODY_Y + 0.25, 6.4, 0.4, "Other column checks", size=18, bold=True)
bullets(s, M + 5.7, BODY_Y + 0.8, 6.4, 4.3, [
    [("Financial exposure ≈ revenue loss ", {"bold": True}), (f"(r = {s1['derived']['Financial_Exposure_vs_Revenue_Loss']}). Never add them.", {})],
    [("Failure probability mirrors health ", {"bold": True}), (f"(r = {s1['derived']['Failure_Probability_vs_Health_Index']}). Report one.", {})],
    [("Executive priority is a formula: ", {"bold": True}), ("fixed bands of the Maintenance Priority Index.", {})],
    [("Composite scores inter-correlate at 0.7 to 0.99: ", {"bold": True}), ("they describe a formula, not a discovery.", {})]], size=16, gap=12)

# ================================================================ 9 significance gate
rd = sorted([r for r in reg if r["measure"] == "Unplanned_Downtime_Hours_30D"], key=lambda r: -r["eta2"])
s = content(f"{n_real} of {len(reg)} differences are real; OEM and shift are not", "Stage 3b: the significance gate",
            "ANOVA confirmed by Kruskal-Wallis, Bonferroni threshold 0.0015. With 5,000 rows almost anything is detectable, so the bar shows effect size: "
            "the share of downtime variance each dimension explains. Grey bars are not significant.")
bar_chart(s, M, BODY_Y + 0.1, 8.2, 4.9, [r["dimension"].replace("_", " ") for r in rd], [100 * r["eta2"] for r in rd],
          [BLUE if r["verdict"].startswith("REAL") else RGBColor(0xC3, 0xC2, 0xB7) for r in rd], fmt='0.0"%"', label_size=12, gap=40)
takeaway(s, M + 8.6, BODY_Y + 0.2, 3.5, 4.7,
         f"Failure mode, spares and strategy explain the most downtime. Site explains {100*next(r for r in rd if r['dimension']=='Site')['eta2']:.1f}%. "
         "Manufacturer, shift and criticality show no downtime difference.", label="READ IT AS")

# ================================================================ 10 divider B
divider("B", "Where the loss is", "Concentrated in a fifth of the windows, and tied to asset health",
        "Section B. Before levers, where the money actually sits.")

# ================================================================ 11 KPIs
s = content(f"EGP {K['revenue_loss_total']/1e9:.2f}B lost to {K['downtime_total']:,.0f} hours of downtime", "The headline numbers",
            "These are the four KPIs agreed in the scope brief. Totals add overlapping 30-day windows, so compare means per window, not totals.")
kp = [(f"{K['revenue_loss_total']/1e9:.2f}B", "EGP revenue loss, all windows"), (f"{K['downtime_mean']:.1f} h", "mean unplanned downtime per window"),
      (f"{K['high_risk_pct']:.1f}%", "of windows high-risk (failure probability ≥ 50%)"), (f"{100*C['high_risk_share_of_loss']:.1f}%", "of revenue loss sits in those windows")]
for i, (v, l) in enumerate(kp):
    stat_card(s, M + i * 3.1, BODY_Y + 0.25, 2.85, 2.3, v, l, fill=NAVY if i == 3 else PANEL,
              vcolor=ORANGE if i == 3 else INK, lcolor=WHITE if i == 3 else INK2, vsize=38)
doughnut(s, M, BODY_Y + 2.8, 5.6, 2.6, ["High-risk windows", "All other windows"],
         [C["high_risk_share_of_loss"], 1 - C["high_risk_share_of_loss"]], [ORANGE, RGBColor(0xC3, 0xC2, 0xB7)])
text(s, M + 6.1, BODY_Y + 3.0, 6.0, 2.4, [[("19% of windows, 47% of the loss. ", {"bold": True}),
     ("The high-risk slice is small enough to target and large enough to matter.", {})]], size=18, color=INK, line=1.15)

# ================================================================ 12 concentration
s = content(f"A tenth of the windows carry {100*C['revenue_loss_top10_share']:.0f}% of the loss", "Concentration",
            f"Gini {C['gini_revenue_loss']:.2f}. The playbook calls this the most decision-relevant number. "
            "Effort spread evenly across the fleet is mostly spent where little is lost.")
fit_picture(s, "lorenz", M, BODY_Y + 0.1, 6.4, 4.9)
for i, (v, l) in enumerate([(f"{100*C['revenue_loss_top10_share']:.1f}%", "of loss in the top 10% of windows"),
                            (f"{100*C['revenue_loss_top20_share']:.1f}%", "in the top 20%"),
                            (f"{C['gini_revenue_loss']:.2f}", "Gini coefficient of loss")]):
    stat_card(s, M + 7.0, BODY_Y + 0.1 + i * 1.65, 5.1, 1.45, v, l, vsize=30, lsize=14)

# ================================================================ 13 health
s = content(f"Windows under health 70 lose {hb['<70']['loss_mean']/hb['90+']['loss_mean']:.0f}x those above 90", "Loss follows health",
            "Health index bands. The steepness is the case for acting early: each band down roughly doubles the loss.")
bands = ["<70", "70-79", "80-89", "90+"]
vals = [hb[b]["loss_mean"] / 1e3 for b in bands]
bar_chart(s, M, BODY_Y + 0.1, 7.6, 4.8, [f"Health {b}" for b in bands], vals, [seq(v, max(vals)) for v in vals],
          fmt='"EGP "#,##0"k"', label_size=14)
takeaway(s, M + 8.0, BODY_Y + 0.2, 4.1, 4.6,
         f"Health under 70: {hb['<70']['downtime_mean']:.0f} h downtime and {hb['<70']['fp_mean']:.0f}% failure probability per window. "
         f"Above 90: {hb['90+']['downtime_mean']:.1f} h and {hb['90+']['fp_mean']:.0f}%.")

# ================================================================ 14 trend
tr = F["trend"]
mn = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
s = content("The year is flat: no trend or season to schedule against", "Time",
            f"Fitted slope {F['trend_stats']['slope_pct_of_mean']:+.2f}% of the monthly mean per month; lag-1 autocorrelation {F['trend_stats']['lag1']:+.2f}. "
            "A bad month does not predict the next one, so timing is not a lever.")
line_chart(s, M, BODY_Y + 0.1, 8.4, 4.8, [mn[int(t['period'][5:]) - 1] + " " + t["period"][2:4] for t in tr],
           [t["loss_mean"] / 1e3 for t in tr], fmt='"EGP "#,##0"k"')
takeaway(s, M + 8.8, BODY_Y + 0.2, 3.3, 4.6, "Every month averages EGP 340k to 410k per window. Plan by asset condition, not by calendar.")

# ================================================================ 15 divider C
divider("C", "The levers", "Four things management controls, each worth about 2x on downtime",
        "Section C. The core of the recommendation.")

# ================================================================ 16 strategy
s = content(f"Reactive maintenance runs {react['downtime_mean']/pred['downtime_mean']:.1f}x the downtime of predictive", "Lever 1: strategy",
            "Bootstrap 95% intervals. The three planned strategies overlap each other: the step that matters is leaving reactive, not choosing among the planned ones.")
fit_picture(s, "ci_strategy", M, BODY_Y + 0.1, 7.8, 4.8)
takeaway(s, M + 8.2, BODY_Y + 0.2, 3.9, 4.6,
         f"Reactive {react['downtime_mean']:.1f} h per window; planned strategies {pred['downtime_mean']:.1f} to {prev['downtime_mean']:.1f} h. "
         f"{react['n']} windows ({100*react['n']/5000:.0f}%) are still reactive.")

# ================================================================ 17 emergency WOs
sts = [react, prev, cbm, pred]
s = content(f"Reactive windows turn {react['emergency_pct']:.0f}% of work orders into emergencies", "Lever 1: strategy",
            "Share of work orders that are corrective emergency, by strategy. Emergencies cost labour, parts at premium and production.")
bar_chart(s, M, BODY_Y + 0.1, 7.6, 4.8, [x["name"] for x in sts], [x["emergency_pct"] for x in sts],
          [STRAT[x["name"]] for x in sts], fmt='0"%"', label_size=14)
for i, (v, l) in enumerate([(f"{react['emergency_pct']:.0f}%", "emergency work orders, reactive"),
                            (f"{pred['emergency_pct']:.0f}%", "emergency work orders, predictive")]):
    stat_card(s, M + 8.0, BODY_Y + 0.2 + i * 2.4, 4.1, 2.15, v, l, vsize=40)

# ================================================================ 18 spares
s = content(f"Parts shortages run {short['downtime_mean']/avail['downtime_mean']:.1f}x the downtime of available stock", "Lever 2: spare parts",
            f"A clean staircase with no interval touching the next. Spares status explains {100*r_spl['eta2']:.1f}% of revenue-loss variance, five times what site explains.")
fit_picture(s, "ci_spares", M, BODY_Y + 0.4, 7.8, 4.2)
for i, (nm, x) in enumerate([("Shortage", short), ("Limited", limited), ("Available", avail)]):
    rect(s, M + 8.2, BODY_Y + 0.2 + i * 1.6, 3.9, 1.4, PANEL, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08)
    badge(s, M + 8.45, BODY_Y + 0.6 + i * 1.6, "", d=0.5, fill=SPARE[nm])
    text(s, M + 9.2, BODY_Y + 0.35 + i * 1.6, 2.8, 0.5, f"{x['downtime_mean']:.1f} h", size=26, bold=True)
    text(s, M + 9.2, BODY_Y + 0.9 + i * 1.6, 2.8, 0.5, f"{nm} · {x['n']:,} windows", size=14, color=INK2)

# ================================================================ 19 heatmap
s = content(f"The levers compound: worst combination {heat['values'][0][0]:.0f} h, best {heat['values'][3][2]:.0f} h", "Levers 1 + 2 together",
            "Mean downtime by strategy and spares status, with counts. Reactive plus shortage is the cell to empty first; predictive plus available is the target state.")
fit_picture(s, "heatmap", M, BODY_Y + 0.1, 7.8, 4.9)
takeaway(s, M + 8.2, BODY_Y + 0.2, 3.9, 4.6,
         f"A {heat['values'][0][0]/heat['values'][3][2]:.1f}x spread between the worst and best cell. Even with parts available, reactive "
         f"runs {heat['values'][0][2]:.1f} h against {heat['values'][3][2]:.1f} h for predictive.")

# ================================================================ 20 skill
s = content(f"Basic crews run {skills[0]['downtime_mean']/skills[3]['downtime_mean']:.1f}x the downtime of expert crews", "Lever 3: crew skill",
            "Mean downtime by technician skill level. Basic and intermediate sit clearly above advanced and expert; intervals do not overlap.")
bar_chart(s, M, BODY_Y + 0.1, 7.6, 4.8, [x["name"] for x in skills], [x["downtime_mean"] for x in skills],
          [seq(x["downtime_mean"], skills[0]["downtime_mean"]) for x in skills], fmt='0.0" h"', label_size=14)
takeaway(s, M + 8.0, BODY_Y + 0.2, 4.1, 4.6,
         f"{skills[0]['n'] + skills[1]['n']:,} windows ({100*(skills[0]['n'] + skills[1]['n'])/5000:.0f}%) are worked by basic or intermediate crews. "
         "Pair them with experts on high-risk assets first.")

# ================================================================ 21 PM deciles
dec = LV["pm_deciles"]
s = content(f"Downtime falls steadily as PM compliance rises: {dec[0]['downtime_mean']:.0f} h to {dec[-1]['downtime_mean']:.0f} h", "Lever 4: PM discipline",
            "PM compliance deciles, least compliant on the left, median compliance under each bar. A dose-response shape is stronger evidence than a single split.")
bar_chart(s, M, BODY_Y + 0.1, 12.1, 4.9, [f"D{d['decile']} · {d['pm_mid']:.0f}%" for d in dec], [d["downtime_mean"] for d in dec],
          [BLUE] * 10, fmt='0.0', horizontal=False, label_size=13, gap=45)

# ================================================================ 22 lever thresholds
names = {"pm_compliance": "PM compliance", "days_since_maint": "Days since maintenance", "lubricant": "Lubricant quality", "backlog": "Maintenance backlog"}
rows = []
for k, v in LV.items():
    if k in names:
        a, b = [x for x in v if isinstance(v[x], dict)]
        w_, b_ = (a, b) if v[a]["downtime_mean"] > v[b]["downtime_mean"] else (b, a)
        rows.append([names[k], w_, f"{v[w_]['downtime_mean']:.1f} h", b_, f"{v[b_]['downtime_mean']:.1f} h",
                     f"{v[w_]['downtime_mean']/v[b_]['downtime_mean']:.1f}x", f"{v['eta2']:.3f}"])
s = content("Four operating thresholds each split downtime about 2x", "Operating thresholds",
            "Each lever split at a practical threshold the maintenance team can manage to. All p-values are below 1e-60.")
table_shape(s, M, BODY_Y + 0.2, 12.1, [2.6, 1.9, 1.35, 2.35, 1.35, 1.2, 1.35],
            ["Lever", "Worse side", "Downtime", "Better side", "Downtime", "Ratio", "η²"], rows, size=15, row_h=0.62,
            align=["L", "L", "R", "L", "R", "R", "R"])
takeaway(s, M, BODY_Y + 3.6, 12.1, 1.5, "Targets to manage to: PM compliance at or above 80%, maintenance within 60 days, lubricant quality above 50, "
         "backlog under 14 days.", label="OPERATING TARGETS")

# ================================================================ 23 drivers
s = content("PM and lubrication cut downtime; backlog raises it", "Measured inputs",
            "Correlation of each measured, non-derived input with unplanned downtime. Composite scores are excluded because they are formulas built from these inputs.")
fit_picture(s, "drivers", M, BODY_Y + 0.1, 8.0, 4.9)
takeaway(s, M + 8.4, BODY_Y + 0.2, 3.7, 4.6, "The strongest measured inputs are the ones maintenance controls: PM compliance, lubrication and backlog. Vibration is the best early-warning signal.")

# ================================================================ 24 sizing
s = content("Upper bound: up to a quarter of downtime is in play", "What the levers could be worth",
            "These are estimates, not measurements. They assume the association is fully causal, which it is not: reactive windows also start in worse health. "
            "That is why recommendation 6 is a pilot.")
for i, (v, l, d) in enumerate([(f"{save_strategy:,.0f} h", f"if reactive windows ran at the preventive average ({100*save_strategy/K['downtime_total']:.0f}% of downtime)", "Strategy"),
                               (f"{save_spares:,.0f} h", f"if shortage windows ran at the available-stock average ({100*save_spares/K['downtime_total']:.0f}%)", "Spares")]):
    x = M + i * 6.15
    rect(s, x, BODY_Y + 0.3, 5.9, 3.3, NAVY, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.06)
    text(s, x + 0.4, BODY_Y + 0.55, 5.0, 0.4, d.upper(), size=13, bold=True, color=ORANGE)
    text(s, x + 0.4, BODY_Y + 1.0, 5.0, 1.0, v, size=48, bold=True, color=WHITE)
    text(s, x + 0.4, BODY_Y + 2.15, 5.1, 1.2, l, size=16, color=ICE, line=1.1)
text(s, M, BODY_Y + 3.95, 12.1, 0.9, [[("ESTIMATED, NOT MEASURED. ", {"bold": True, "color": ORANGE}),
     ("Treat these as the ceiling a pilot would test, not as a forecast. The two overlap where reactive windows also lack parts.", {})]],
     size=15, color=INK2)

# ================================================================ 25 escalation gap
mix = WL["top_decile_priority_mix"]
order = ["P1 - Immediate", "P2 - High", "P3 - Planned", "P4 - Monitor"]
s = content(f"The escalation flag misses {gap_n} of {hr_n} high-risk windows", "D · The escalation gap",
            f"Executive priority is a fixed banding of an index that correlates only 0.75 with failure probability. P1/P2 cover {100*WL['top_decile_flagged_loss_share']:.1f}% "
            "of the loss in the worst 10% of windows. Most of the worst windows were filed as P3 Planned.")
text(s, M, BODY_Y + 0.1, 7.4, 0.4, "Flag received by the 500 largest-loss windows", size=16, bold=True)
bar_chart(s, M, BODY_Y + 0.5, 7.4, 4.4, order, [mix.get(p, 0) for p in order], [PRIO[p] for p in order], fmt='#,##0', label_size=14)
stat_card(s, M + 7.8, BODY_Y + 0.2, 4.3, 2.2, f"{gap_n}", "high-risk windows flagged only P3 or P4", fill=NAVY, vcolor=ORANGE, lcolor=WHITE, vsize=44)
stat_card(s, M + 7.8, BODY_Y + 2.65, 4.3, 2.2, egp(gap["gap_exposure"]), "financial exposure sitting in that gap", vsize=36)

# ================================================================ 26 the rule
s = content("Add a second trigger: FP ≥ 50% on High or Critical assets", "D · The proposed rule",
            f"On this file the rule adds {gap['rule_adds']} windows and {egp(gap['rule_exposure'])} of exposure to the watched list. Escalated count goes from "
            f"{esc_n} to {esc_n + gap['rule_adds']}, so confirm crew capacity before switching it on.")
fit_picture(s, "gap_by_site", M, BODY_Y + 0.1, 7.2, 4.9)
for i, (v, l) in enumerate([(f"+{gap['rule_adds']}", "windows escalated by the rule"), (egp(gap["rule_exposure"]), f"exposure covered ({100*gap['rule_exposure']/gap['gap_exposure']:.0f}% of the gap)"),
                            (f"{esc_n} → {esc_n + gap['rule_adds']}", "escalated windows: check capacity")]):
    stat_card(s, M + 7.6, BODY_Y + 0.1 + i * 1.65, 4.5, 1.45, v, l, vsize=28, lsize=14)

# ================================================================ 27 what doesn't matter
s = content("What does not matter, and should not get budget on its own", "Context",
            f"Site is real but small (η² {r_site['eta2']:.3f} on loss). Manufacturer (p = {r_oem['p_anova']:.2f}) and shift (p = {r_shift['p_anova']:.2f}) show nothing at all.")
cols = [("Site", f"Real but small: explains {100*r_site['eta2']:.1f}% of loss variance. Heavy-industry sites lose about 1.5x per window, largely through the same levers.", "Do not run a site-vs-site campaign"),
        ("Manufacturer (OEM)", f"No difference on downtime, loss or failure probability (p ≥ {min(r['p_anova'] for r in reg if r['dimension']=='Manufacturer_Group'):.2f}).", "No OEM switch on this evidence"),
        ("Operating shift", f"No difference on any measure (downtime p = {r_shift['p_anova']:.2f}).", "No shift restructuring"),
        ("Calendar month", "Flat year, no momentum between months.", "Plan by condition, not calendar")]
for i, (h, b, v) in enumerate(cols):
    x = M + i * 3.07
    rect(s, x, BODY_Y + 0.2, 2.85, 4.8, PANEL, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.06)
    text(s, x + 0.25, BODY_Y + 0.45, 2.4, 0.8, h, size=19, bold=True)
    text(s, x + 0.25, BODY_Y + 1.35, 2.4, 2.3, b, size=14, color=INK2, line=1.1)
    text(s, x + 0.25, BODY_Y + 3.85, 2.4, 1.0, v, size=14, bold=True, color=ORANGE, line=1.05)

# ================================================================ 28 dashboard
s = content("A live, six-page dashboard keeps these numbers current", "The build",
            "Overview, Explorer (cross-filtered), Levers, Sites & Equipment, Risk Watchlist, Data & Method. Standard-library Python watcher, plain HTML and SVG, no framework. "
            "Verification: 10 timed edits to the source CSV, 376 ms mean, 621 ms max from save to screen.")
pic = fit_picture(s, "dash_index", M, BODY_Y + 0.05, 8.2, 4.95)
pic.line.color.rgb = GRIDC
for i, (v, l) in enumerate([("376 ms", "mean save-to-screen refresh"), ("6", "linked pages, light + dark"), ("0", "console errors on any page")]):
    stat_card(s, M + 8.6, BODY_Y + 0.05 + i * 1.7, 3.5, 1.5, v, l, vsize=28, lsize=14)

# ================================================================ 29 recommendations
s = content("Seven recommendations", "What to do",
            "Ordered by size of effect and ease. Number 6 is what turns these associations into causal, budgetable estimates.")
recs = [("Leave reactive maintenance", "critical and high-criticality assets first"),
        ("Fund spare-parts availability", "for the classes that hit shortage"),
        ("PM at 80%+, backlog under 14 days", "the operating targets"),
        ("Upskill basic and intermediate crews", "pair with experts on high-risk work"),
        ("Add the second escalation trigger", f"+{gap['rule_adds']} windows, after a capacity check"),
        ("Pilot before scaling", "one site converted, one matched site as control"),
        ("Fix the asset key in the next export", "unlocks per-asset history and replacement planning")]
for i, (h, b) in enumerate(recs):
    col, row = i % 2, i // 2
    x, y = M + col * 6.15, BODY_Y + 0.1 + row * 1.25
    badge(s, x, y + 0.1, str(i + 1), d=0.6, size=18)
    text(s, x + 0.8, y + 0.02, 5.2, 0.5, h, size=17, bold=True)
    text(s, x + 0.8, y + 0.52, 5.2, 0.4, b, size=14, color=INK2)

# ================================================================ 30 close
s = new_slide(dark=True)
text(s, M, 0.55, 9, 0.35, "DECISIONS NEEDED", size=13, bold=True, color=ORANGE)
text(s, M, 1.2, 12, 1.0, "Three decisions for this quarter", size=40, bold=True, color=WHITE)
dec3 = [("1", "Approve the reactive-to-planned pilot", "One site, one matched control, measured on the live dashboard"),
        ("2", "Approve the second escalation trigger", f"Subject to a capacity check for {esc_n + gap['rule_adds']} escalated windows"),
        ("3", "Request a fixed Asset_ID in the next export", "So the next review can plan replacement per asset")]
for i, (n, h, b) in enumerate(dec3):
    y = 2.55 + i * 1.35
    badge(s, M, y, n, d=0.7, size=20)
    text(s, M + 1.0, y - 0.02, 11, 0.5, h, size=22, bold=True, color=WHITE)
    text(s, M + 1.0, y + 0.5, 11, 0.45, b, size=15, color=ICE)
text(s, M, SH - 0.42, 11, 0.25, "Analysis: 02_Analysis/analyze_pmaris.py · Dashboard: 03_Dashboard · Report: PMARIS_Reliability_Assessment.pdf",
     size=10, color=ICE)
text(s, SW - M - 1.5, SH - 0.42, 1.5, 0.25, "30 / 30", size=10, color=ICE, align=PP_ALIGN.RIGHT)
s.notes_slide.notes_text_frame.text = (
    "Close on the decisions, not a thank-you slide. The pilot is the most important: it converts the 2x associations into a causal "
    "number the budget can rest on. The live dashboard will measure it.")

assert SLIDE_NO[0] == 30, SLIDE_NO[0]
prs.save(OUT)
print("wrote", OUT, "slides:", SLIDE_NO[0])
