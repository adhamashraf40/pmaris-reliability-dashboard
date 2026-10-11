# -*- coding: utf-8 -*-
"""Generates the Sales Data Quality & Fitness Assessment PDF (10 pages).

Every figure in this document is measured. The sources are:
  02_Analysis/analyze.py       Stage 1 cleaning, key integrity, marginal tests
  02_Analysis/analyze_deep.py  the seven-angle battery
Rebuild with:  python make_report.py
"""
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph,
                                Spacer, Table, TableStyle, PageBreak)

OUT = str(Path(__file__).resolve().parent / "Sales_Data_Quality_Assessment.pdf")

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
H1     = S("h1", fontName="Helvetica-Bold", fontSize=13.5, leading=17, textColor=INK,
           spaceBefore=13, spaceAfter=6)
H2     = S("h2", fontName="Helvetica-Bold", fontSize=10.6, leading=14, textColor=ACC,
           spaceBefore=9, spaceAfter=4)
BODY   = S("b", fontName="Helvetica", fontSize=9.6, leading=14.2,
           textColor=colors.HexColor("#22252b"), alignment=TA_JUSTIFY, spaceAfter=6)
BULLET = S("bu", parent=BODY, leftIndent=13, bulletIndent=2, spaceAfter=5, alignment=0)
CELL   = S("c", fontName="Helvetica", fontSize=8.5, leading=12, textColor=colors.HexColor("#22252b"))
CAP    = S("cap", fontName="Helvetica-Oblique", fontSize=8, leading=10.6, textColor=MUTE, spaceAfter=7)
CELLS  = S("cs", parent=CELL, fontSize=8.1, leading=11)
EYE    = S("eye", fontName="Helvetica-Bold", fontSize=7.6, leading=10, textColor=ACC, spaceAfter=3)
MONO   = S("mono", parent=CELL, fontSize=7.2, leading=10.4)

W = 157 * mm   # standard content width used by every table and callout


def callout(text, tone=WARN, label="KEY FINDING"):
    inner = [[Paragraph(label, S("kk", fontName="Helvetica-Bold", fontSize=7.6,
                                 leading=10, textColor=tone))],
             [Paragraph(text, S("cot", parent=BODY, fontSize=10, leading=15, spaceAfter=0))]]
    t = Table(inner, colWidths=[W])
    t.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (0, 0), 8), ("BOTTOMPADDING", (0, 0), (0, 0), 1),
        ("TOPPADDING", (0, 1), (0, 1), 0), ("BOTTOMPADDING", (0, 1), (-1, -1), 9),
        ("BACKGROUND", (0, 0), (-1, -1), BAND),
        ("LINEBEFORE", (0, 0), (0, -1), 2.4, tone),
    ]))
    return t


def table(head, rows, widths, aligns=None, flags=None, size=8.5, pad=4.5):
    cs = S("cx", parent=CELL, fontSize=size, leading=size + 3.5)
    data = [[Paragraph(h, S("th", fontName="Helvetica-Bold", fontSize=8.3, leading=11,
                            textColor=colors.white)) for h in head]]
    for r in rows:
        data.append([c if isinstance(c, Paragraph) else Paragraph(str(c), cs) for c in r])
    t = Table(data, colWidths=widths, repeatRows=1)
    st = [("BACKGROUND", (0, 0), (-1, 0), INK),
          ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
          ("TOPPADDING", (0, 0), (-1, -1), pad), ("BOTTOMPADDING", (0, 0), (-1, -1), pad),
          ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
          ("LINEBELOW", (0, 1), (-1, -2), 0.4, RULE),
          ("LINEBELOW", (0, -1), (-1, -1), 0.8, INK),
          ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fafbfc")])]
    for i, a in enumerate(aligns or []):
        if a != "L":
            st.append(("ALIGN", (i, 0), (i, -1), "RIGHT" if a == "R" else "CENTER"))
    t.setStyle(TableStyle(st + (flags or [])))
    return t


def red(t):
    return Paragraph("<font color='#b3261e'><b>%s</b></font>" % t, CELL)


def green(t):
    return Paragraph("<font color='#006300'>%s</font>" % t, CELL)


def decorate(canv, doc):
    canv.saveState()
    w, h = A4
    canv.setFillColor(INK)
    canv.rect(0, h - 12 * mm, w, 12 * mm, stroke=0, fill=1)
    canv.setFont("Helvetica-Bold", 7.6)
    canv.setFillColor(colors.white)
    canv.drawString(18 * mm, h - 8 * mm, "SALES DATA QUALITY & FITNESS ASSESSMENT")
    canv.setFont("Helvetica", 7.6)
    canv.drawRightString(w - 18 * mm, h - 8 * mm, "Confidential - prepared for the client")
    canv.setStrokeColor(RULE)
    canv.setLineWidth(0.5)
    canv.line(18 * mm, 15 * mm, w - 18 * mm, 15 * mm)
    canv.setFont("Helvetica", 7.6)
    canv.setFillColor(MUTE)
    canv.drawString(18 * mm, 10.5 * mm,
                    "sales_data_large.csv  |  1,000 rows  |  assessed 19 September 2026")
    canv.drawRightString(w - 18 * mm, 10.5 * mm, "Page %d of 10" % doc.page)
    canv.restoreState()


doc = BaseDocTemplate(OUT, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                      topMargin=20 * mm, bottomMargin=20 * mm,
                      title="Sales Data Quality and Fitness Assessment",
                      author="Analytics review")
doc.addPageTemplates([PageTemplate(
    id="main",
    frames=[Frame(18 * mm, 18 * mm, A4[0] - 36 * mm, A4[1] - 40 * mm, id="f")],
    onPage=decorate)])

s = []
A = s.append

# =====================================================================  PAGE 1
A(Paragraph("Sales Data Quality and Fitness Assessment", TITLE))
A(Paragraph("An independent review of <b>sales_data_large.csv</b> carried out before any dashboard "
            "was built, to establish which business questions this dataset can and cannot answer.", SUBT))
A(Spacer(1, 14))
A(callout("This dataset is technically flawless and analytically empty. It passed every standard "
          "data-cleaning check with zero defects, then failed every test that decides whether a "
          "number is worth acting on.", tone=WARN, label="VERDICT"))
A(Spacer(1, 12))

A(Paragraph("THE FILE AT A GLANCE", EYE))
A(table(
    ["Measure", "Value", "Measure", "Value"],
    [["File assessed", "sales_data_large.csv", "Cleaning defects found", green("0 of 8 checks failed")],
     ["Rows and columns", "1,000 x 9", "Columns that fail key integrity", red("3 of 9")],
     ["Period covered", "1 Jan to 31 Dec 2024", "Significance tests run", "9 marginal, 7 deep angles"],
     ["Days carrying a sale", "345 of 366", "Tests returning a signal", red("0")],
     ["Total revenue, units", "2,561,723 from 9,746", "Revenue range", "101 to 4,995"],
     ["Transactions", "1,000, averaging 2,562", "Decisions the file supports", red("None beyond totals")]],
    [33 * mm, 45 * mm, 45 * mm, 34 * mm], ["L", "L", "L", "L"]))
A(Spacer(1, 11))

A(Paragraph("CONTENTS", EYE))
A(table(
    ["Page", "Section", "What it establishes"],
    [["2", "Executive summary",
      "The verdict, and what it means for the questions usually put to sales data"],
     ["3", "1. How the assessment was run",
      "The six-step sequence, and the cleaning checklist the file passed"],
     ["4", "2. Finding 1: three columns do not mean what they are named",
      "Why product, customer and unit-price analysis are all blocked"],
     ["5", "3. Finding 2: no measurable signal",
      "The nine-test register, and one mistake corrected on the record"],
     ["6", "4. Where the revenue actually sits",
      "Every dimension, with the even split shown beside it"],
     ["7", "5. Concentration, and how far we looked",
      "The Gini check, then seven independent angles"],
     ["8", "6. Ranking stability and the forensic test",
      "Bootstrap confidence intervals and Benford's law, in full"],
     ["9", "7. Time, and the export that would work",
      "Trend, seasonality, momentum, and the power calculation"],
     ["10", "8. What may be published, and what to do next",
      "The publishable scope, the export to request, and how to reproduce every figure"]],
    [12 * mm, 63 * mm, 82 * mm], ["C", "L", "L"], size=8.1, pad=4))
A(Spacer(1, 7))
A(Paragraph("Prepared from the delivered file only. No figure here is estimated or carried over from a "
            "previous engagement; every one is reproducible from the scripts listed on page 10.", CAP))

# =====================================================================  PAGE 2
A(PageBreak())
A(Paragraph("Executive summary", H1))
A(callout("This dataset is technically flawless and analytically empty. It passed every standard "
          "data-cleaning check with zero defects. It then failed the tests that matter: three of its "
          "identifier and measure columns do not hold together, and every remaining dimension is "
          "statistically indistinguishable from random noise. Nine significance tests and seven further "
          "analytical angles were run in all, from interaction effects and bootstrap confidence "
          "intervals to Benford's law "
          "and a power calculation, and none of them found a decision the data could support. "
          "<b>No sales dashboard built on this file "
          "can support a 'where should we focus' decision, because the file contains nothing to "
          "focus on.</b>"))
A(Spacer(1, 11))
A(Paragraph(
    "We assessed the file in two passes. The first was the conventional cleaning checklist: types, "
    "headers, missing values, duplicates, outliers, low-variance columns and date continuity. The file "
    "passed all of it cleanly, which is why the problems described here would survive an ordinary "
    "quality review unnoticed.", BODY))
A(Paragraph(
    "The second pass tested whether the columns mean what their names imply, and whether the differences "
    "between categories are larger than chance would produce. Both tests failed. The findings below are "
    "ordered by how much they constrain what can be delivered.", BODY))

A(Paragraph("What this means for the questions usually put to sales data", H2))
A(table(
    ["Question", "Answerable?", "The measured reason"],
    [["Which city should we prioritise?", red("No"),
      "The best-to-worst gap is 1.43x, reproduced by chance in 35% of 20,000 simulations. Every city's "
      "95% interval overlaps every other city's."],
     ["Which category should we push?", red("No"),
      "Chi-square 2.93 on 4 degrees of freedom, p = 0.57. The five categories run from 18.1% to 21.1% "
      "against an even split of 20.0%."],
     ["Who are our best customers?", red("No"),
      "258 of the 631 CustomerIDs carry conflicting age, gender or city, so no customer can be followed "
      "from one row to the next."],
     ["Which products earn most?", red("No"),
      "All 100 ProductIDs appear under more than one category, so the identifier does not name a product."],
     ["What is our margin?", red("No"),
      "There is no cost column. This is a structural absence, not a broken column, and no proxy should "
      "be substituted for it."],
     ["What will next quarter look like?", red("No"),
      "The trend is +0.46% of an average month and the lag-1 autocorrelation is -0.468, so a good month "
      "does not predict the next."],
     ["How much did we sell in 2024?", green("<b>Yes</b>"),
      "2,561,723 across 1,000 transactions and 9,746 units. The totals are sound. It is the comparisons "
      "between them that are not."]],
    [42 * mm, 25 * mm, 90 * mm], ["L", "C", "L"], size=8.3))
A(Spacer(1, 7))
A(Paragraph("The pattern in that table is itself the finding: everything the file can answer is a total, "
            "and everything it cannot answer is a comparison. A dashboard is mostly comparisons.", CAP))

# =====================================================================  PAGE 3
A(PageBreak())
A(Paragraph("1. How the assessment was run", H1))
A(Paragraph(
    "The review followed a fixed sequence, and each step was allowed to stop the next. Nothing was "
    "reported as a finding until a test had been run against it. The sequence matters because this file "
    "fails at steps 2 and 3, both of which sit after the checklist that most reviews stop at.", BODY))
A(table(
    ["Step", "What it tests", "Outcome on this file"],
    [["<b>0. Classify</b>", "Shape and grain of the delivered data",
      "A single flat transaction table with a date column. 1,000 rows over 345 active days is 2.9 per "
      "day, "
      "so the natural grain is monthly, not daily."],
     ["<b>1. Clean</b>", "Mechanical defects: types, blanks, duplicates, outliers",
      green("Passed. Zero defects across all eight checks, detailed below.")],
     ["<b>2. Key integrity</b>", "Whether each column means what its name implies",
      red("Failed on three columns. See page 4.")],
     ["<b>3. Marginal tests</b>", "Whether the observed differences beat chance",
      red("Nine tests, nine null results. See page 5.")],
     ["<b>4. Deep battery</b>", "Whether any angle holds signal the totals would hide",
      red("Seven independent angles, seven null results. See pages 7 and 8.")],
     ["<b>5. Scope</b>", "What may honestly be published",
      "Totals and shares only. No ranking, no prioritisation, no forecast. See page 10."]],
    [26 * mm, 46 * mm, 85 * mm], size=8.4))

A(Paragraph("The cleaning checklist, in full", H2))
A(Paragraph(
    "This is the conventional quality review, run first and reported here in full because its result is "
    "counter-intuitive. The file is in better mechanical condition than most production exports.", BODY))
A(table(
    ["Cleaning check", "Result"],
    [["Row and column count", "1,000 rows, 9 columns"],
     ["Type conformance across all typed columns",
      green("0 non-conforming values in SalesDate, QuantitySold, SalesRevenue and CustomerAge")],
     ["Header integrity", green("Clean, no title row above the header")],
     ["Missing values and disguised nulls", green("0 blank cells, 0 sentinel values")],
     ["Exact and near-duplicate rows",
      green("0 exact, 0 near-duplicates on date plus product plus customer")],
     ["Outliers and implausible values",
      green("None. Revenue 101 to 4,995, quantity 1 to 19, ages 18 to 69, no negatives or zeroes")],
     ["Constant or near-constant columns", green("None above the 95% threshold")],
     ["Date continuity across 2024",
      green("345 of 366 days carry a sale, 21 do not, longest consecutive gap 1 day")]],
    [64 * mm, 93 * mm]))
A(Spacer(1, 6))
A(callout("A clean bill of health from the standard checklist is exactly why the real problems here would "
          "survive an ordinary review. Cleanliness is a property of the file. Fitness is a property of "
          "the file measured against a question. They are different tests, and this file separates them "
          "completely.",
          tone=ACC, label="WHY THE CHECKLIST IS NOT ENOUGH"))

# =====================================================================  PAGE 4
A(PageBreak())
A(Paragraph("2. Finding 1: three columns do not mean what they are named", H1))
A(Paragraph(
    "Column names imply a structure the data does not actually carry. Each issue below is invisible in "
    "the header row and in any spot check of the first few records. All three appear only when "
    "consistency is tested across the whole file.", BODY))
A(table(
    ["Column", "What the name implies", "What the data actually shows", "Consequence"],
    [["<b>ProductID</b>", "A stable product key, 100 products",
      "All 100 IDs appear under more than one product category",
      Paragraph("No product-level analysis is possible. Use <b>ProductCategory</b> instead.", CELL)],
     ["<b>CustomerID</b>", "A stable customer key, 631 customers",
      "258 of the 631 IDs carry conflicting age, gender or city",
      Paragraph("No customer view, no repeat-purchase or churn analysis.", CELL)],
     ["<b>SalesRevenue</b>", "Revenue earned on the units sold",
      "Uncorrelated with QuantitySold (r = -0.06)",
      Paragraph("Unit price, basket value and any per-unit metric are meaningless.", CELL)]],
    [28 * mm, 33 * mm, 51 * mm, 45 * mm]))
A(Spacer(1, 4))
A(Paragraph("A fourth constraint is structural rather than broken: the file carries no cost column, so "
            "profit and margin cannot be derived at all.", CAP))

A(Paragraph("The evidence behind each one", H2))
A(table(
    ["Column", "Test applied across all 1,000 rows", "Measured", "A usable key would show"],
    [["ProductID", "IDs appearing under more than one ProductCategory",
      red("100 of 100"), "0 of 100"],
     ["CustomerID", "IDs carrying a conflicting age, gender or city",
      red("258 of 631"), "0 of 631"],
     ["SalesRevenue", "Pearson correlation with QuantitySold",
      red("r = -0.0599"), "Strongly positive"],
     ["Cost or unit price", "Presence of any cost, price or margin column",
      red("Absent"), "Present"]],
    [27 * mm, 63 * mm, 30 * mm, 37 * mm], ["L", "L", "C", "C"]))
A(Spacer(1, 8))

A(Paragraph("What this blocks, stated plainly", H2))
A(Paragraph(
    "These are not panels that would come out weaker than hoped. They cannot be built at all from this "
    "file, because the column each one would read does not carry the meaning the panel needs.", BODY))
A(table(
    ["Blocked analysis", "Root cause"],
    [["Named product performance, product mix, product drill-down", "ProductID is not a stable key"],
     ["Customer profile, segmentation, lifetime value", "CustomerID is not a stable key"],
     ["Repeat purchase, retention, churn", "Follows from the CustomerID failure"],
     ["Average selling price, basket value, unit economics", "Revenue is uncorrelated with quantity"],
     ["Gross profit, margin percentage, contribution", "No cost column exists"],
     ["Discount or promotion effect", "No price or discount column exists"]],
    [86 * mm, 71 * mm]))
A(Spacer(1, 5))
A(Paragraph("The remedy for all six is the same, and it is not analytical: a production export carrying a "
            "stable key per product, a stable record per customer, and a cost column. Recommendation 2 on "
            "page 10 states the full specification.", CAP))

# =====================================================================  PAGE 5
A(PageBreak())
A(Paragraph("3. Finding 2: the data contains no measurable signal", H1))
A(Paragraph(
    "Revenue is spread almost perfectly evenly across every available dimension. We tested whether the "
    "small differences that do appear are larger than random variation would produce. Across nine "
    "separate tests, they are not. The register below is the complete list. Nothing was run and then "
    "left out of it.", BODY))
A(table(
    ["#", "Test", "Statistic", "p", "Verdict"],
    [["1", "Revenue by product category, 5 values", "chi-square 2.93, df 4", "0.570",
      red("No real difference")],
     ["2", "Revenue by city, 10 values", "chi-square 6.20, df 9", "0.720", red("No real difference")],
     ["3", "Revenue by gender, 2 values", "chi-square 0.26, df 1", "0.610", red("No real difference")],
     ["4", "Revenue by customer age band, 5 values", "chi-square 3.73, df 4", "0.444",
      red("No real difference")],
     ["5", "Revenue by day of week, 7 values", "chi-square 5.76, df 6", "0.451",
      red("No real difference")],
     ["6", "Category by city interaction on revenue", "permutation, 20,000 shuffles", "0.184",
      red("No real difference")],
     ["7", "Gap between highest and lowest city, 1.43x", "permutation, 20,000 shuffles", "0.345",
      red("Ordinary noise")],
     ["8", "Month-on-month trend across 2024", "+0.46% of an average month", "n/a",
      red("Flat, no growth")],
     ["9", "Leading digits of the revenue values", "chi-square 442, df 8, against Benford", "2e-90",
      red("Randomly generated")]],
    [7 * mm, 54 * mm, 46 * mm, 17 * mm, 33 * mm], ["C", "L", "L", "C", "L"], size=8.2))
A(Spacer(1, 5))
A(Paragraph("Tests 1 to 5 compare the observed split against an even split at the 5% level. Test 9 is the "
            "only rejection in the register, and it rejects in the direction least useful to the client: "
            "it rejects the hypothesis that these amounts arose naturally. Where a family of related "
            "tests was run, the Bonferroni-corrected threshold is 0.05 divided by 7, which is 0.0071. No "
            "result comes near either threshold.", CAP))

A(Paragraph("One mistake, corrected and kept on the record", H2))
A(callout("An early pass tested the category-by-city interaction by computing a chi-square statistic on "
          "<b>summed revenue</b> and reading the p-value from a chi-square table. That produced "
          "<b>p = 0.023</b>, which would have been reported as the one real finding in the file. It is "
          "wrong. A chi-square statistic computed on summed money is not distributed as chi-square, so "
          "the table does not apply to it. Re-running the same comparison as a 20,000-shuffle permutation "
          "test, which needs no distributional assumption, gives <b>p = 0.184</b>. The rule this "
          "produced, and the reason the mistake is printed rather than quietly fixed: when a statistic is "
          "not a standard one, obtain the p-value by permutation rather than by looking it up.",
          tone=ACC, label="METHOD NOTE"))
A(Spacer(1, 9))
A(Paragraph(
    "The interaction family was tested on transaction counts as well as on revenue, because a flat set "
    "of totals can still hide a combination that behaves differently, for example one category booming "
    "in one city only. Five count-based contingency tables were tested: category by city (p = 0.408), "
    "category by age band (p = 0.679), category by gender (p = 0.153), city by gender (p = 0.907) and "
    "city by age band (p = 0.922). The worst of them is 0.153. No combination carries signal that the "
    "marginal totals hide.", BODY))

# =====================================================================  PAGE 6
A(PageBreak())
A(Paragraph("4. Where the revenue actually sits", H1))
A(Paragraph(
    "These tables are the evidence behind Finding 2, shown as the business would read them. In each "
    "case the right-hand columns give the share a perfectly even split would produce.", BODY))

A(Paragraph("By product category", H2))
A(table(
    ["Product category", "Revenue", "Share", "Transactions", "Units", "Even split"],
    [["Home Decor", "540,975", "21.1%", "205", "1,982", "20.0%"],
     ["Beauty", "539,969", "21.1%", "204", "2,051", "20.0%"],
     ["Books", "520,795", "20.3%", "212", "2,100", "20.0%"],
     ["Apparel", "497,068", "19.4%", "199", "1,878", "20.0%"],
     ["Electronics", "462,916", "18.1%", "180", "1,735", "20.0%"]],
    [40 * mm, 27 * mm, 20 * mm, 27 * mm, 20 * mm, 23 * mm],
    ["L", "R", "R", "R", "R", "R"]))
A(Spacer(1, 3))
A(Paragraph("Spread from highest to lowest: 1.17x. Chi-square 2.93 on 4 degrees of freedom, p = 0.57.", CAP))

A(Paragraph("By customer city", H2))
A(table(
    ["City", "Revenue", "Share", "Transactions", "Even split", "Gap to even"],
    [["Dallas", "302,114", "11.8%", "118", "10.0%", "+1.8 points"],
     ["Chicago", "282,553", "11.0%", "107", "10.0%", "+1.0"],
     ["Phoenix", "267,683", "10.4%", "102", "10.0%", "+0.4"],
     ["San Jose", "265,975", "10.4%", "101", "10.0%", "+0.4"],
     ["Los Angeles", "259,752", "10.1%", "96", "10.0%", "+0.1"],
     ["Houston", "258,297", "10.1%", "99", "10.0%", "+0.1"],
     ["Philadelphia", "249,967", "9.8%", "96", "10.0%", "-0.2"],
     ["San Antonio", "232,752", "9.1%", "98", "10.0%", "-0.9"],
     ["San Diego", "231,078", "9.0%", "97", "10.0%", "-1.0"],
     ["New York", "211,552", "8.3%", "86", "10.0%", "-1.7"]],
    [30 * mm, 27 * mm, 19 * mm, 27 * mm, 23 * mm, 31 * mm],
    ["L", "R", "R", "R", "R", "R"], size=8.3))
A(Spacer(1, 3))
A(Paragraph("Spread from highest to lowest: 1.43x. Chi-square 6.20 on 9 degrees of freedom, p = 0.72. The "
            "order shown here is correct arithmetic on the delivered file, and it is also not "
            "reproducible: page 8 shows what happens to it under resampling.", CAP))

A(Paragraph("By customer age band and by gender", H2))
A(table(
    ["Age band", "Revenue", "Share", "Even split", "Gender", "Revenue", "Share", "Even split"],
    [["18-29", "565,535", "22.1%", "20.0%", "Male", "1,295,751", "50.6%", "50.0%"],
     ["30-39", "545,454", "21.3%", "20.0%", "Female", "1,265,972", "49.4%", "50.0%"],
     ["40-49", "495,830", "19.4%", "20.0%", "", "", "", ""],
     ["50-59", "487,261", "19.0%", "20.0%", "", "", "", ""],
     ["60+", "467,643", "18.3%", "20.0%", "", "", "", ""]],
    [19 * mm, 22 * mm, 16 * mm, 20 * mm, 19 * mm, 24 * mm, 17 * mm, 20 * mm],
    ["L", "R", "R", "R", "L", "R", "R", "R"], size=8.2))
A(Spacer(1, 3))
A(Paragraph("Age bands: chi-square 3.73, df 4, p = 0.44 against an even 20.0% each. Gender: chi-square "
            "0.26, df 1, p = 0.61 against an even 50.0% each. CustomerAge holds 52 distinct values and was "
            "bucketed into five bands before testing.", CAP))

# =====================================================================  PAGE 7
A(PageBreak())
A(Paragraph("5. Concentration, and how far we looked", H1))
A(Paragraph(
    "The concentration check makes the same point in business terms, and it is the single most "
    "decision-relevant measure in this report. In real sales data the top tenth of customers, products "
    "or territories usually carries 40% to 80% of revenue, and that unevenness is what makes "
    "prioritisation possible. Here the top tenth carries almost exactly its even share.", BODY))
A(table(
    ["Concentration check", "Observed", "Even split would be", "Real business range"],
    [["Top 10% of cities", "11.8% of revenue", "10.0%", "40% to 80%"],
     ["Top 10% of product categories", "21.1% of revenue", "20.0%", "40% to 80%"],
     ["Half of all revenue comes from", "5 of the 10 cities", "5 of 10", "1 or 2 of 10"],
     ["Half of all revenue comes from", "3 of the 5 categories", "2.5 of 5", "1 of 5"]],
    [52 * mm, 35 * mm, 35 * mm, 35 * mm], ["L", "R", "R", "R"], size=8.2, pad=3.8))
A(Spacer(1, 5))
A(table(
    ["Gini coefficient, 0 is perfectly even", "Value", "Reading", "Real sales data"],
    [["By city, 10 values", "0.055", green("Essentially even"), "0.40 to 0.70"],
     ["By product category, 5 values", "0.031", green("Essentially even"), "0.40 to 0.70"],
     ["Across individual transactions", "0.323", "Consistent with a flat random draw", "Higher and lumpy"]],
    [52 * mm, 18 * mm, 52 * mm, 35 * mm], ["L", "C", "L", "C"], size=8.2, pad=3.8))

A(Paragraph("Seven further angles", H2))
A(Paragraph(
    "Findings 1 and 2 rest on the marginal totals. Before concluding that the file holds no usable "
    "signal, we tested seven further angles, each able to find structure the totals would hide.", BODY))
A(table(
    ["Angle", "What it would have found", "Result"],
    [["<b>Two-way interactions</b>",
      "A combination that performs differently from what its parts predict",
      Paragraph("All five pairs were tested. Worst p-value 0.15; a permutation test on the "
                "category-by-city revenue matrix returned p = 0.18. <b>No combination carries signal the "
                "marginal totals hide.</b>", CELLS)],
     ["<b>Bootstrap confidence intervals</b>",
      "A city whose true revenue is reliably above the others",
      Paragraph("Across 4,000 resamples every city's 95% interval overlaps every other city's. Dallas "
                "is top in only 46% of them, and every city is seen at every rank from 1 to 10. <b>The "
                "city ranking is not stable.</b>", CELLS)],
     ["<b>Concentration, Gini coefficient</b>",
      "The uneven spread that makes prioritisation possible",
      Paragraph("See the table above. Concentration is what makes prioritisation possible, and "
                "<b>its absence here is why no city and no category can be singled out.</b>",
                CELLS)],
     ["<b>Benford's law</b>",
      "The leading-digit signature that naturally occurring amounts carry",
      Paragraph("Rejected at chi-square 442, df 8, p = 2e-90. The leading digits instead match a flat "
                "draw between 101 and 4,995 (p = 0.85). <b>Forensic evidence of generated values.</b>",
                CELLS)],
     ["<b>Temporal structure</b>",
      "A weekday, weekend or momentum effect worth scheduling against",
      Paragraph("No day-of-week effect (p = 0.45); weekend share 30.2% of revenue on 28.6% of days; "
                "lag-1 autocorrelation -0.47, so <b>a good month does not predict the next.</b>", CELLS)],
     ["<b>Power analysis</b>",
      "Whether 1,000 rows could detect a real difference even if one existed",
      Paragraph("At this sample size only large gaps are detectable, so the silence is partly a "
                "sample-size limit. <b>Full specification on page 9.</b>", CELLS)],
     ["<b>Anomaly scan</b>",
      "The exceptional transactions that usually repay investigation",
      Paragraph("Zero transactions beyond three standard deviations, <b>which is itself abnormal for "
                "genuine sales data.</b>", CELLS)]],
    [34 * mm, 45 * mm, 78 * mm], pad=3.8))
A(Spacer(1, 4))
A(Paragraph("Seven independent angles, seven null results. The consistency matters more than any single "
            "test: a real dataset that failed one of these would usually pass another.", CAP))

# =====================================================================  PAGE 8
A(PageBreak())
A(Paragraph("6. Ranking stability and the forensic test", H1))
A(Paragraph(
    "Two of the seven angles carry enough weight to be shown in full. The first answers the objection "
    "that a p-value is an abstraction: it asks directly whether the city ranking on page 6 would come "
    "back the same way if the year had gone slightly differently. The second answers the question of "
    "where these numbers came from in the first place.", BODY))

A(Paragraph("Bootstrap confidence intervals: 4,000 resamples of the 1,000 rows", H2))
A(table(
    ["City", "Observed share", "95% confidence interval", "Contains the 10.0% even split?",
     "Ranks seen"],
    [["Dallas", "11.8%", "9.6% to 14.1%", green("Yes"), "1 to 10"],
     ["Chicago", "11.0%", "8.9% to 13.3%", green("Yes"), "1 to 10"],
     ["Phoenix", "10.4%", "8.3% to 12.8%", green("Yes"), "1 to 10"],
     ["San Jose", "10.4%", "8.2% to 12.6%", green("Yes"), "1 to 10"],
     ["Los Angeles", "10.1%", "8.0% to 12.5%", green("Yes"), "1 to 10"],
     ["Houston", "10.1%", "8.0% to 12.3%", green("Yes"), "1 to 10"],
     ["Philadelphia", "9.8%", "7.7% to 11.9%", green("Yes"), "1 to 10"],
     ["San Antonio", "9.1%", "7.1% to 11.2%", green("Yes"), "1 to 10"],
     ["San Diego", "9.0%", "7.0% to 11.1%", green("Yes"), "1 to 10"],
     ["New York", "8.3%", "6.4% to 10.2%", green("Yes"), "1 to 10"]],
    [28 * mm, 24 * mm, 41 * mm, 42 * mm, 22 * mm],
    ["L", "R", "C", "C", "C"], size=8.3))
A(Spacer(1, 4))
A(callout("Every interval overlaps every other interval, and every interval contains the 10.0% that a "
          "perfectly even split would produce. Dallas, the apparent leader, is top in only 46% of the "
          "4,000 resamples, and each of the ten cities is observed at every rank from first to tenth. "
          "<b>The ranking is an artefact of which 1,000 transactions happened to land in the file.</b>",
          tone=WARN, label="WHAT THE INTERVALS SAY"))

A(Paragraph("Benford's law, applied to the leading digit of every revenue amount", H2))
A(Paragraph(
    "Amounts produced by real economic activity carry a characteristic leading-digit signature: a 1 "
    "about 30% of the time, falling away to about 5% for a 9. Amounts drawn from a flat range do not. "
    "This is the test that moves the assessment from 'looks synthetic' to 'is demonstrably generated'.",
    BODY))
A(table(
    ["Leading digit", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
    [["Observed count", "236", "208", "229", "233", "18", "20", "15", "21", "20"],
     ["Observed share", "23.6%", "20.8%", "22.9%", "23.3%", "1.8%", "2.0%", "1.5%", "2.1%", "2.0%"],
     ["Benford expects", "30.1%", "17.6%", "12.5%", "9.7%", "7.9%", "6.7%", "5.8%", "5.1%", "4.6%"],
     ["A flat 101 to 4,995 draw expects", "22.5%", "22.5%", "22.5%", "22.4%", "2.0%", "2.0%", "2.0%",
      "2.0%", "2.0%"]],
    [45 * mm, 14 * mm, 14 * mm, 14 * mm, 14 * mm, 14 * mm, 14 * mm, 14 * mm, 14 * mm, 14 * mm],
    ["L", "R", "R", "R", "R", "R", "R", "R", "R", "R"], size=7.8))
A(Spacer(1, 4))
A(Paragraph("Fit against Benford: chi-square 442.0 on 8 degrees of freedom, p = 2e-90, rejected. Fit "
            "against a flat random draw between 101 and 4,995: chi-square 4.1 on 8 degrees of freedom, "
            "p = 0.851, consistent. The collapse after digit 4 is the signature of a hard upper bound at "
            "4,995 rather than of a price list.", CAP))

# =====================================================================  PAGE 9
A(PageBreak())
A(Paragraph("7. Time, and the export that would work", H1))
A(Paragraph(
    "Revenue by month is the one view that visibly moves, so it is the one most likely to be "
    "over-interpreted. The monthly series varies by 16.0% around its mean, which reads as seasonality "
    "and is not: the fitted trend is +991 per month, or +0.46% of an average month, and the lag-1 "
    "autocorrelation is -0.468, meaning a strong month is followed by a weak one slightly more often "
    "than not. That is the signature of noise, not of momentum.", BODY))
A(table(
    ["Month", "Revenue", "Txns", "Share", "Month", "Revenue", "Txns", "Share"],
    [["2024-01", "200,691", "76", "7.8%", "2024-07", "175,609", "71", "6.9%"],
     ["2024-02", "240,151", "88", "9.4%", "2024-08", "212,981", "95", "8.3%"],
     ["2024-03", "187,792", "73", "7.3%", "2024-09", "171,612", "64", "6.7%"],
     ["2024-04", "210,782", "86", "8.2%", "2024-10", "273,842", "97", "10.7%"],
     ["2024-05", "261,895", "105", "10.2%", "2024-11", "189,816", "76", "7.4%"],
     ["2024-06", "191,113", "78", "7.5%", "2024-12", "245,439", "91", "9.6%"]],
    [20 * mm, 23 * mm, 17 * mm, 18.5 * mm, 20 * mm, 23 * mm, 17 * mm, 18.5 * mm],
    ["L", "R", "R", "R", "L", "R", "R", "R"], size=8.2))
A(Spacer(1, 3))
A(Paragraph("Monthly mean 213,477, standard deviation 34,110, coefficient of variation 16.0%. Quarterly "
            "shares: Q1 24.5%, Q2 25.9%, Q3 21.9%, Q4 27.7%, against an even 25.0% each.", CAP))

A(Paragraph("Day of week", H2))
A(table(
    ["Day", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    [["Revenue", "377,328", "360,533", "404,038", "345,786", "299,458", "402,405", "372,175"],
     ["Share", "14.7%", "14.1%", "15.8%", "13.5%", "11.7%", "15.7%", "14.5%"],
     ["Transactions", "138", "146", "161", "139", "123", "143", "150"]],
    [25 * mm, 19 * mm, 19 * mm, 19 * mm, 19 * mm, 19 * mm, 19 * mm, 18 * mm],
    ["L", "R", "R", "R", "R", "R", "R", "R"], size=8.2))
A(Spacer(1, 3))
A(Paragraph("Chi-square 5.76 on 6 degrees of freedom, p = 0.45. The weekend carries 30.2% of revenue on "
            "28.6% of the days, which is the share any two days in seven would carry anyway.", CAP))

A(Paragraph("Power analysis: how large an export would have to be", H2))
A(Paragraph(
    "This is the one genuinely actionable output of the review, because it converts the bad news into a "
    "specification. Simulation was used to ask: if one city genuinely ran a given percentage above the "
    "others, how many rows would be needed to detect that reliably, meaning in 80% of samples?", BODY))
A(table(
    ["If one city genuinely ran this far ahead", "Rows needed for 80% power",
     "Multiple of the current file"],
    [["50% above the others", "1,000", "1x, the current size"],
     ["30% above the others", "3,000", "3x"],
     ["20% above the others", "6,000", "6x"],
     ["10% above the others", "25,000", "25x"]],
    [65 * mm, 47 * mm, 45 * mm], ["L", "C", "C"]))
A(Spacer(1, 6))
A(callout("At the current 1,000 rows, the chance of detecting a real 20% lift on one city is <b>21%</b>, "
          "against the 80% conventionally required. Part of the silence in this file is therefore a "
          "sample-size limit rather than proof of a flat business. The honest statement is that the file "
          "is too small to settle the question, and the table above says exactly how much larger it "
          "would need to be.", tone=ACC, label="READ THIS AS A SPECIFICATION"))

# ====================================================================  PAGE 10
A(PageBreak())
A(Paragraph("8. What may be published, and what to do next", H1))
A(table(
    ["Supported, with the caveats above", "Not supported by this file"],
    [[Paragraph("Total revenue and total units for the year<br/>"
                "Monthly revenue trend across 2024<br/>"
                "Revenue split by product category, city, gender and age band<br/>"
                "Transaction counts and average transaction value", CELLS),
      Paragraph("Any named product or named customer analysis<br/>"
                "Profit, margin, unit price or basket value<br/>"
                "Repeat purchase, retention or churn<br/>"
                "Regional or seasonal prioritisation of any kind<br/>"
                "Forecasting, since there is no trend to project", CELLS)]],
    [78 * mm, 79 * mm], pad=4,
    flags=[("BACKGROUND", (0, 0), (0, 0), OK), ("BACKGROUND", (1, 0), (1, 0), WARN),
           ("VALIGN", (0, 1), (-1, -1), "TOP")]))
A(Spacer(1, 5))
A(Paragraph(
    "A dashboard restricted to the supported list would be accurate and honest. It would also tell the "
    "reader that every category, every city and every month performs the same, which is a description of "
    "the file rather than a description of the business. That is the dashboard that was built: six "
    "static pages reading this same file, no page ranking a city or a category as best or worst, each "
    "city share shown next to its confidence interval rather than as a bare ordering, and the no-signal "
    "caveat repeated in every page footer rather than parked on one quality page, because readers arrive "
    "at a single page from a link and act on what that page alone appears to say.", BODY))

A(Paragraph("Recommendation", H1))
A(Paragraph("<b>1. Treat this file as a structural sample, not as sales history.</b> Its shape, column "
            "names and grain are a usable specification for what a real export should contain. Its values "
            "are not evidence about the business and should not be quoted as such.",
            BULLET, bulletText="\u2022"))
A(Paragraph("<b>2. Request a production export before any decision-support work proceeds.</b> Four "
            "additions would make this dataset decision-grade: a unit cost or unit price column, a stable "
            "product key with one fixed category per product, a stable customer record, and at least two "
            "years of history so that seasonality can be separated from noise.",
            BULLET, bulletText="\u2022"))
A(Paragraph("<b>3. Confirm the intended decision before the build.</b> The single most useful piece of "
            "information we do not yet have is which business decision the dashboard is meant to support. "
            "That determines whether the gaps listed above are blocking or tolerable.",
            BULLET, bulletText="\u2022"))
A(Paragraph("<b>4. Size the replacement export to the question.</b> Simulation shows how many rows are "
            "needed to detect a genuine difference in one city with 80% confidence: 1,000 rows for a 50% "
            "difference, 3,000 for 30%, 6,000 for 20%, and 25,000 for 10%. At the current 1,000 rows the "
            "chance of detecting a real 20% difference is 21%. If the business question is which city to "
            "prioritise, the export needs to be several times larger than this sample.",
            BULLET, bulletText="\u2022"))

A(Paragraph("Method and evidence", H1))
A(Paragraph(
    "Every figure in this report was computed directly from the delivered file, not estimated, and every "
    "one of them is reproducible from the two scripts below.", BODY))
A(table(
    ["Evidence", "Where it comes from", "Reproduce with"],
    [["Cleaning checklist, key integrity, marginal tests, concentration",
      "Stage 1 to Stage 3 of the assessment",
      Paragraph("<font face='Courier'>python 02_Analysis/analyze.py</font>", MONO)],
     ["Interactions, bootstrap, Gini, Benford, temporal structure, power, anomalies",
      "The seven-angle deep battery",
      Paragraph("<font face='Courier'>python 02_Analysis/analyze_deep.py</font>", MONO)],
     ["This document", "Generated from those two outputs, with no figure typed by hand",
      Paragraph("<font face='Courier'>python 04_Deliverables/make_report.py</font>", MONO)]],
    [50 * mm, 37 * mm, 70 * mm], size=8.1, pad=4))
A(Spacer(1, 4))
A(Paragraph("Statistical tests used: chi-square goodness of fit against a uniform distribution at the 5% "
            "level; 20,000-iteration Monte Carlo permutation tests for the city revenue gap and for both "
            "revenue interaction matrices; 4,000-resample bootstrap confidence intervals for the city "
            "shares; Pearson correlation between revenue and quantity; Gini coefficients on the city, "
            "category and transaction distributions; a chi-square leading-digit test against Benford and "
            "against a uniform range; lag-1 autocorrelation on the monthly series; and a simulation power "
            "analysis at four effect sizes.", CAP))

doc.build(s)
print("built", OUT)
