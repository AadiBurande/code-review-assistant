# pdf_generator.py
"""
Improved PDF Report Generator
- Cover page with score badge
- Table of Contents
- Plain-English finding cards (color-coded by severity)
- Simple problem/why/fix layout
- Before/After code blocks
- Plagiarism section support
- Clean typography throughout
"""


from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether,
)
from reportlab.platypus.flowables import Flowable
from reportlab.pdfgen import canvas as pdfcanvas
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import re


# ── Color Palette ─────────────────────────────────────────────────────────────


C_BG_DARK     = colors.HexColor("#0f1117")
C_ACCENT      = colors.HexColor("#00d4ff")
C_WHITE       = colors.HexColor("#ffffff")
C_LIGHT_GRAY  = colors.HexColor("#f5f6fa")
C_MID_GRAY    = colors.HexColor("#e1e4ec")
C_TEXT        = colors.HexColor("#1a1d27")
C_TEXT_MUTED  = colors.HexColor("#6b7280")


C_CRITICAL_BG   = colors.HexColor("#fff1f1")
C_CRITICAL_SIDE = colors.HexColor("#e53e3e")
C_HIGH_BG       = colors.HexColor("#fff7ed")
C_HIGH_SIDE     = colors.HexColor("#f97316")
C_MEDIUM_BG     = colors.HexColor("#fefce8")
C_MEDIUM_SIDE   = colors.HexColor("#eab308")
C_LOW_BG        = colors.HexColor("#eff6ff")
C_LOW_SIDE      = colors.HexColor("#3b82f6")
C_INFO_BG       = colors.HexColor("#f9fafb")
C_INFO_SIDE     = colors.HexColor("#9ca3af")


C_ACCEPT_BG     = colors.HexColor("#f0fff4")
C_ACCEPT_FG     = colors.HexColor("#276749")
C_CHANGES_BG    = colors.HexColor("#fffbeb")
C_CHANGES_FG    = colors.HexColor("#92400e")
C_REJECT_BG     = colors.HexColor("#fff5f5")
C_REJECT_FG     = colors.HexColor("#9b2c2c")


C_CODE_BG       = colors.HexColor("#1e2130")
C_CODE_FG       = colors.HexColor("#e2e8f0")


PAGE_W, PAGE_H  = A4
MARGIN          = 0.8 * inch
CONTENT_W       = PAGE_W - 2 * MARGIN



# ── Page Number Canvas ────────────────────────────────────────────────────────


class NumberedCanvas(pdfcanvas.Canvas):
    def __init__(self, *args, **kwargs):
        pdfcanvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []


    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()


    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_page_number(num_pages)
            pdfcanvas.Canvas.showPage(self)
        pdfcanvas.Canvas.save(self)


    def _draw_page_number(self, page_count):
        page_num = self._pageNumber
        if page_num <= 1:
            return
        self.setFont("Helvetica", 8)
        self.setFillColor(C_TEXT_MUTED)
        text = f"Page {page_num} of {page_count}"
        self.drawRightString(PAGE_W - MARGIN, 0.45 * inch, text)
        self.setStrokeColor(C_MID_GRAY)
        self.setLineWidth(0.5)
        self.line(MARGIN, 0.6 * inch, PAGE_W - MARGIN, 0.6 * inch)



# ── Colored Left-Border Card ──────────────────────────────────────────────────


class BorderCard(Flowable):
    """A card with a colored left border strip and background."""
    def __init__(self, content_flowables, bg_color, border_color,
                 padding=10, border_width=4):
        Flowable.__init__(self)
        self.content = content_flowables
        self.bg      = bg_color
        self.border  = border_color
        self.padding = padding
        self.bw      = border_width
        self._built  = False


    def wrap(self, availW, availH):
        self.availW = availW
        inner_w = availW - self.bw - self.padding * 2
        self._heights = []
        total_h = self.padding
        for f in self.content:
            w, h = f.wrapOn(None, inner_w, availH)
            self._heights.append(h)
            total_h += h + 4
        total_h += self.padding
        self._total_h = total_h
        return availW, total_h


    def draw(self):
        c = self.canv
        c.setFillColor(self.bg)
        c.roundRect(0, 0, self.availW, self._total_h, 4, fill=1, stroke=0)
        c.setFillColor(self.border)
        c.rect(0, 0, self.bw, self._total_h, fill=1, stroke=0)
        y = self._total_h - self.padding
        for f, h in zip(self.content, self._heights):
            y -= h
            f.drawOn(c, self.bw + self.padding, y)
            y -= 4



# ── Style Factory ─────────────────────────────────────────────────────────────


def _build_styles():
    base = getSampleStyleSheet()

    def s(name, **kwargs):
        parent = kwargs.pop("parent", base["Normal"])
        return ParagraphStyle(name, parent=parent, **kwargs)

    return {
        "cover_title": s("cover_title",
            fontName="Helvetica-Bold", fontSize=30,
            textColor=C_WHITE, alignment=TA_CENTER, spaceAfter=6,
            leading=36),
        "cover_subtitle": s("cover_sub",
            fontName="Helvetica", fontSize=13,
            textColor=colors.HexColor("#94a3b8"), alignment=TA_CENTER,
            spaceAfter=4),
        "cover_meta": s("cover_meta",
            fontName="Helvetica", fontSize=10,
            textColor=colors.HexColor("#64748b"), alignment=TA_CENTER,
            spaceAfter=3),
        "cover_score": s("cover_score",
            fontName="Helvetica-Bold", fontSize=64,
            alignment=TA_CENTER, leading=70),
        "cover_verdict": s("cover_verdict",
            fontName="Helvetica-Bold", fontSize=16,
            alignment=TA_CENTER, letterSpacing=2),

        "h1": s("h1",
            fontName="Helvetica-Bold", fontSize=18,
            textColor=C_TEXT, spaceBefore=20, spaceAfter=8,
            leading=22),
        "h2": s("h2",
            fontName="Helvetica-Bold", fontSize=13,
            textColor=C_TEXT, spaceBefore=14, spaceAfter=6,
            leading=17),
        "h3": s("h3",
            fontName="Helvetica-Bold", fontSize=11,
            textColor=C_TEXT, spaceBefore=8, spaceAfter=4),

        "body": s("body",
            fontName="Helvetica", fontSize=10,
            textColor=C_TEXT, leading=15, spaceAfter=4,
            alignment=TA_JUSTIFY),
        "body_small": s("body_small",
            fontName="Helvetica", fontSize=9,
            textColor=C_TEXT_MUTED, leading=13, spaceAfter=3),
        "bold": s("bold",
            fontName="Helvetica-Bold", fontSize=10,
            textColor=C_TEXT, leading=15),

        "finding_title": s("finding_title",
            fontName="Helvetica-Bold", fontSize=11,
            textColor=C_TEXT, spaceAfter=4, leading=14),
        "finding_label": s("finding_label",
            fontName="Helvetica-Bold", fontSize=9,
            textColor=C_TEXT_MUTED, spaceAfter=2,
            spaceBefore=6),
        "finding_text": s("finding_text",
            fontName="Helvetica", fontSize=10,
            textColor=C_TEXT, leading=15, spaceAfter=3),
        "finding_step": s("finding_step",
            fontName="Helvetica", fontSize=10,
            textColor=C_TEXT, leading=15, spaceAfter=2,
            leftIndent=12),

        "code": s("code",
            fontName="Courier", fontSize=8.5,
            textColor=C_CODE_FG, backColor=C_CODE_BG,
            leading=13, spaceAfter=2,
            leftIndent=6, rightIndent=6),

        "toc_entry": s("toc_entry",
            fontName="Helvetica", fontSize=10,
            textColor=C_TEXT, leading=16, spaceAfter=2),
        "toc_h2": s("toc_h2",
            fontName="Helvetica-Bold", fontSize=10,
            textColor=C_TEXT, leading=18, spaceAfter=1,
            spaceBefore=6),
    }



# ── Helpers ───────────────────────────────────────────────────────────────────


def _escape(text: str) -> str:
    if not text:
        return ""
    text = str(text)
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    return text


def _severity_colors(severity: str):
    return {
        "Critical": (C_CRITICAL_BG, C_CRITICAL_SIDE),
        "High":     (C_HIGH_BG,     C_HIGH_SIDE),
        "Medium":   (C_MEDIUM_BG,   C_MEDIUM_SIDE),
        "Low":      (C_LOW_BG,      C_LOW_SIDE),
        "Info":     (C_INFO_BG,     C_INFO_SIDE),
    }.get(severity, (C_INFO_BG, C_INFO_SIDE))


def _severity_emoji(severity: str) -> str:
    return {
        "Critical": "🔴 CRITICAL",
        "High":     "🟠 HIGH",
        "Medium":   "🟡 MEDIUM",
        "Low":      "🔵 LOW",
        "Info":     "⚪ INFO",
    }.get(severity, severity.upper())


def _code_block(snippet: str, styles) -> list:
    if not snippet or not snippet.strip():
        return []
    lines = snippet.strip().split("\n")[:30]
    bg_table_data = []
    for line in lines:
        safe = _escape(line) if line.strip() else " "
        bg_table_data.append([Paragraph(safe, styles["code"])])
    if not bg_table_data:
        return []
    t = Table(bg_table_data, colWidths=[CONTENT_W - 28])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_CODE_BG),
        ("LEFTPADDING",  (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING",   (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 2),
        ("ROUNDEDCORNERS", [4]),
    ]))
    return [t]


def _count_by_severity(report) -> dict:
    counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0, "Info": 0}
    for fr in report.files:
        for f in fr.findings:
            sev = f.severity if f.severity in counts else "Info"
            counts[sev] += 1
    return counts



# ── Cover Page ────────────────────────────────────────────────────────────────


def _build_cover(report, styles) -> list:
    m = report.metadata
    story = []

    verdict = m.verdict.lower()
    score   = m.score

    verdict_label, verdict_bg, verdict_fg = {
        "accept":        ("✅  ACCEPTED",      C_ACCEPT_BG,  C_ACCEPT_FG),
        "needs_changes": ("⚠️  NEEDS CHANGES", C_CHANGES_BG, C_CHANGES_FG),
        "reject":        ("❌  REJECTED",      C_REJECT_BG,  C_REJECT_FG),
    }.get(verdict, ("—", C_INFO_BG, C_TEXT_MUTED))

    score_color = (
        C_ACCEPT_FG  if score >= 80 else
        C_CHANGES_FG if score >= 60 else
        C_REJECT_FG
    )

    brand_style = ParagraphStyle("brand",
        fontName="Helvetica-Bold", fontSize=11,
        textColor=C_TEXT_MUTED, alignment=TA_LEFT)
    brand_table = Table(
        [[Paragraph("AI CODE REVIEW ASSISTANT", brand_style),
          Paragraph(datetime.now().strftime("%d %B %Y"), brand_style)]],
        colWidths=[CONTENT_W * 0.6, CONTENT_W * 0.4],
    )
    brand_table.setStyle(TableStyle([
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(brand_table)
    story.append(HRFlowable(width=CONTENT_W, thickness=1.5,
                             color=C_ACCENT, spaceAfter=30))

    story.append(Spacer(1, 0.3 * inch))
    title_s = ParagraphStyle("ct",
        fontName="Helvetica-Bold", fontSize=28,
        textColor=C_TEXT, alignment=TA_CENTER, leading=34)
    story.append(Paragraph("Code Review Report", title_s))
    story.append(Spacer(1, 6))

    proj_s = ParagraphStyle("cp",
        fontName="Helvetica", fontSize=15,
        textColor=C_TEXT_MUTED, alignment=TA_CENTER)
    story.append(Paragraph(_escape(m.project_name), proj_s))
    story.append(Spacer(1, 0.5 * inch))

    score_s = ParagraphStyle("cs",
        fontName="Helvetica-Bold", fontSize=72,
        alignment=TA_CENTER, leading=80,
        textColor=score_color)
    story.append(Paragraph(str(score), score_s))

    out_of_s = ParagraphStyle("co",
        fontName="Helvetica", fontSize=13,
        textColor=C_TEXT_MUTED, alignment=TA_CENTER)
    story.append(Paragraph("out of 100", out_of_s))
    story.append(Spacer(1, 0.25 * inch))

    verdict_s = ParagraphStyle("cv",
        fontName="Helvetica-Bold", fontSize=14,
        textColor=verdict_fg, alignment=TA_CENTER,
        backColor=verdict_bg)
    verdict_table = Table(
        [[Paragraph(verdict_label, verdict_s)]],
        colWidths=[CONTENT_W * 0.45],
    )
    verdict_table.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), verdict_bg),
        ("TOPPADDING",   (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 10),
        ("LEFTPADDING",  (0, 0), (-1, -1), 20),
        ("RIGHTPADDING", (0, 0), (-1, -1), 20),
        ("ROUNDEDCORNERS", [8]),
        ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
    ]))
    vt_outer = Table([[verdict_table]], colWidths=[CONTENT_W])
    vt_outer.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
    story.append(vt_outer)
    story.append(Spacer(1, 0.45 * inch))

    # Fixed stats row
    counts = _count_by_severity(report)
    col_w  = CONTENT_W / 5

    def _mk_val(name, val, color=C_TEXT):
        return Paragraph(str(val), ParagraphStyle(
            f"sv_{name}", fontName="Helvetica-Bold", fontSize=22,
            textColor=color, alignment=TA_CENTER,
            spaceAfter=0, spaceBefore=0, leading=26,
        ))

    def _mk_lbl(name, label):
        return Paragraph(label, ParagraphStyle(
            f"sl_{name}", fontName="Helvetica", fontSize=8,
            textColor=C_TEXT_MUTED, alignment=TA_CENTER,
            spaceAfter=0, spaceBefore=0, leading=10,
        ))

    val_row = [
        _mk_val("total_findings", m.total_findings),
        _mk_val("critical", counts["Critical"], C_CRITICAL_SIDE),
        _mk_val("high", counts["High"], C_HIGH_SIDE),
        _mk_val("medium", counts["Medium"], C_MEDIUM_SIDE),
        _mk_val("files", m.total_files),
    ]
    lbl_row = [
        _mk_lbl("total_findings", "Total Issues"),
        _mk_lbl("critical", "Critical"),
        _mk_lbl("high", "High"),
        _mk_lbl("medium", "Medium"),
        _mk_lbl("files", "Files"),
    ]

    stat_table = Table(
        [val_row, lbl_row],
        colWidths=[col_w] * 5,
        rowHeights=[36, 20],
    )
    stat_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), C_LIGHT_GRAY),
        ("TOPPADDING",    (0, 0), (-1, 0), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 0),
        ("TOPPADDING",    (0, 1), (-1, 1), 2),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 4),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, 0),  "BOTTOM"),
        ("VALIGN",        (0, 1), (-1, 1),  "TOP"),
        ("LINEAFTER",     (0, 0), (-2, -1), 0.5, C_MID_GRAY),
        ("ROUNDEDCORNERS",[6]),
    ]))
    story.append(stat_table)
    story.append(Spacer(1, 0.3 * inch))

    if m.sub_scores:
        story.append(HRFlowable(width=CONTENT_W, thickness=0.5,
                                 color=C_MID_GRAY, spaceAfter=14))
        header_s = ParagraphStyle("sh",
            fontName="Helvetica-Bold", fontSize=10,
            textColor=C_TEXT_MUTED)
        story.append(Paragraph("CATEGORY SCORES", header_s))
        story.append(Spacer(1, 8))

        sub_rows = [["Category", "Score", "Status"]]
        for cat, sc in m.sub_scores.items():
            status = "✅ Good" if sc >= 80 else "⚠️ Review" if sc >= 60 else "❌ Fix Now"
            sub_rows.append([cat.capitalize(), f"{sc}/100", status])

        sub_table = Table(sub_rows,
                          colWidths=[CONTENT_W * 0.4, CONTENT_W * 0.3, CONTENT_W * 0.3])
        sub_table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0),  C_TEXT),
            ("TEXTCOLOR",     (0, 0), (-1, 0),  C_WHITE),
            ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, -1), 9),
            ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
            ("BACKGROUND",    (0, 1), (-1, -1), C_LIGHT_GRAY),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [C_LIGHT_GRAY, C_WHITE]),
            ("GRID",          (0, 0), (-1, -1), 0.4, C_MID_GRAY),
            ("TOPPADDING",    (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(sub_table)

    story.append(PageBreak())
    return story



# ── Table of Contents ─────────────────────────────────────────────────────────


def _build_toc(report, styles) -> list:
    story = []
    story.append(Paragraph("Table of Contents", styles["h1"]))
    story.append(HRFlowable(width=CONTENT_W, thickness=1,
                             color=C_ACCENT, spaceAfter=16))

    sections = [
        ("1.", "Summary & Scores",     "Cover Page"),
        ("2.", "Findings by Severity", ""),
    ]

    counts = _count_by_severity(report)
    idx = 1
    for sev in ["Critical", "High", "Medium", "Low", "Info"]:
        c = counts.get(sev, 0)
        if c > 0:
            sections.append((f"  2.{idx}.", f"{sev} ({c} issue{'s' if c > 1 else ''})", ""))
            idx += 1

    sections.append(("3.", "What to Fix First", ""))
    sections.append(("4.", "Recommendations",   ""))

    for num, title, _ in sections:
        is_sub = num.startswith("  ")
        entry_s = ParagraphStyle(f"toc_{num.strip()}",
            fontName="Helvetica-Bold" if not is_sub else "Helvetica",
            fontSize=10 if not is_sub else 9.5,
            textColor=C_TEXT if not is_sub else C_TEXT_MUTED,
            leading=18,
            leftIndent=16 if is_sub else 0)
        story.append(Paragraph(f"{num}  {title}", entry_s))

    story.append(PageBreak())
    return story



# ── Single Finding Card ───────────────────────────────────────────────────────


def _build_finding_card(finding, index: int, styles) -> list:
    bg, border = _severity_colors(finding.severity)
    sev_label  = _severity_emoji(finding.severity)
    issue_type = finding.issue_type.upper()

    plain_problem = (
        getattr(finding, "plain_problem",  None)
        or finding.description
    )
    why_it_matters = (
        getattr(finding, "why_it_matters", None)
        or _auto_why(finding.severity, finding.issue_type)
    )
    fix_steps = getattr(finding, "fix_steps", None) or []
    if not fix_steps:
        rem_text = finding.remediation.text if hasattr(finding.remediation, "text") else str(finding.remediation)
        fix_steps = [s.strip() for s in re.split(r'[.;]\s+', rem_text) if s.strip()]
        if not fix_steps:
            fix_steps = [rem_text]

    code_snippet = (
        finding.remediation.code_snippet
        if hasattr(finding.remediation, "code_snippet")
        else getattr(finding, "code_suggestion", "")
    )

    card_parts = []

    header_text = f"<b>#{index} &nbsp; {sev_label} &nbsp; [{issue_type}]</b>"
    card_parts.append(Paragraph(header_text, styles["finding_title"]))

    loc_s = ParagraphStyle("loc",
        fontName="Helvetica", fontSize=8.5,
        textColor=C_TEXT_MUTED, spaceAfter=6)
    card_parts.append(Paragraph(
        f"📁 {_escape(finding.file_path)} &nbsp; | &nbsp; "
        f"Lines {finding.start_line}–{finding.end_line} &nbsp; | &nbsp; "
        f"Confidence: {int(finding.confidence * 100)}%",
        loc_s
    ))

    card_parts.append(HRFlowable(
        width=CONTENT_W - 40, thickness=0.4, color=C_MID_GRAY,
        spaceAfter=6, spaceBefore=2))

    card_parts.append(Paragraph("❌  What's Wrong", styles["finding_label"]))
    card_parts.append(Paragraph(_escape(plain_problem), styles["finding_text"]))

    card_parts.append(Paragraph("💡  Why It Matters", styles["finding_label"]))
    card_parts.append(Paragraph(_escape(why_it_matters), styles["finding_text"]))

    card_parts.append(Paragraph("✅  How to Fix It", styles["finding_label"]))
    for i, step in enumerate(fix_steps[:5], 1):
        if step:
            card_parts.append(Paragraph(
                f"&nbsp;&nbsp;{i}. {_escape(step)}",
                styles["finding_step"]
            ))

    if code_snippet and code_snippet.strip():
        card_parts.append(Paragraph("📝  Code Example", styles["finding_label"]))
        card_parts.extend(_code_block(code_snippet, styles))

    tags = getattr(finding, "tags", [])
    if tags:
        tag_s = ParagraphStyle("tags",
            fontName="Helvetica", fontSize=8,
            textColor=C_TEXT_MUTED, spaceBefore=4)
        card_parts.append(Paragraph(
            "🏷 " + " · ".join(_escape(t) for t in tags[:4]),
            tag_s
        ))

    return [
        BorderCard(card_parts, bg_color=bg, border_color=border, padding=10),
        Spacer(1, 10),
    ]


def _auto_why(severity: str, issue_type: str) -> str:
    if issue_type == "security":
        return "This security issue could allow attackers to access, steal, or corrupt data if left unfixed."
    if issue_type == "bug":
        return "This bug can cause the program to crash or give wrong results for some inputs."
    if issue_type == "performance":
        return "This slowdown may be unnoticeable now, but will become a serious problem as your data grows."
    if severity in ("Critical", "High"):
        return "This is a serious issue that should be fixed before shipping to users."
    return "Fixing this will improve code quality and make future maintenance easier."



# ── Findings Section ──────────────────────────────────────────────────────────


def _build_findings(report, styles) -> list:
    story = []
    story.append(Paragraph("Findings by Severity", styles["h1"]))
    story.append(HRFlowable(width=CONTENT_W, thickness=1,
                             color=C_ACCENT, spaceAfter=10))

    body_plain = ParagraphStyle("bp",
        fontName="Helvetica", fontSize=10,
        textColor=C_TEXT_MUTED, spaceAfter=16, leading=15)
    story.append(Paragraph(
        "Each issue below is explained in plain language. "
        "Start with Critical and High issues — they need immediate attention.",
        body_plain
    ))

    global_index = 1
    for severity in ["Critical", "High", "Medium", "Low", "Info"]:
        findings_for_sev = []
        for fr in report.files:
            findings_for_sev.extend([f for f in fr.findings if f.severity == severity])

        if not findings_for_sev:
            continue

        sev_header = {
            "Critical": ("🔴 Critical Issues",  C_CRITICAL_SIDE),
            "High":     ("🟠 High Issues",       C_HIGH_SIDE),
            "Medium":   ("🟡 Medium Issues",     C_MEDIUM_SIDE),
            "Low":      ("🔵 Low Issues",        C_LOW_SIDE),
            "Info":     ("⚪ Info / Style",      C_INFO_SIDE),
        }[severity]

        sev_h_s = ParagraphStyle(f"sh_{severity}",
            fontName="Helvetica-Bold", fontSize=14,
            textColor=sev_header[1], spaceBefore=18, spaceAfter=8)
        story.append(Paragraph(
            f"{sev_header[0]} ({len(findings_for_sev)})",
            sev_h_s
        ))

        for finding in findings_for_sev:
            story.extend(_build_finding_card(finding, global_index, styles))
            global_index += 1

    return story



# ── Priority Action List ───────────────────────────────────────────────────────


def _build_priority_actions(report, styles) -> list:
    story = []
    story.append(PageBreak())
    story.append(Paragraph("What to Fix First", styles["h1"]))
    story.append(HRFlowable(width=CONTENT_W, thickness=1,
                             color=C_ACCENT, spaceAfter=10))

    intro_s = ParagraphStyle("intro",
        fontName="Helvetica", fontSize=10,
        textColor=C_TEXT_MUTED, spaceAfter=14, leading=15)
    story.append(Paragraph(
        "Here is a simple priority list. Fix issues from top to bottom.",
        intro_s
    ))

    priority_findings = []
    for fr in report.files:
        for f in fr.findings:
            if f.severity in ("Critical", "High"):
                priority_findings.append(f)

    if not priority_findings:
        story.append(Paragraph(
            "✅ No Critical or High severity issues found. Good work!",
            styles["body"]
        ))
        return story

    IDX_W   = 0.35 * inch
    TITLE_W = CONTENT_W * 0.50
    REM_W   = CONTENT_W - IDX_W - TITLE_W

    for i, f in enumerate(priority_findings[:10], 1):
        bg, border = _severity_colors(f.severity)

        num_s = ParagraphStyle(f"pnum{i}",
            fontName="Helvetica-Bold", fontSize=11,
            textColor=border, alignment=TA_CENTER, leading=15)

        title_s = ParagraphStyle(f"ptitle{i}",
            fontName="Helvetica", fontSize=9,
            textColor=C_TEXT, leading=14)

        rem_s = ParagraphStyle(f"prem{i}",
            fontName="Helvetica", fontSize=9,
            textColor=C_TEXT, leading=14)

        desc = getattr(f, "plain_problem", None) or f.description
        rem  = f.remediation.text if hasattr(f.remediation, "text") else str(f.remediation)

        title_para = Paragraph(
            f"<b>{_escape(f.severity)} — {f.issue_type.upper()}</b><br/>"
            f"{_escape(desc[:130])}{'...' if len(desc) > 130 else ''}<br/>"
            f"<font color='#6b7280' size='7.5'>📁 {_escape(f.file_path)} · Line {f.start_line}</font>",
            title_s
        )
        rem_para = Paragraph(
            _escape(rem[:110]) + ("…" if len(rem) > 110 else ""),
            rem_s
        )

        row_table = Table(
            [[Paragraph(f"<b>{i}.</b>", num_s), title_para, rem_para]],
            colWidths=[IDX_W, TITLE_W, REM_W],
        )
        row_table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), bg),
            ("LEFTPADDING",   (0, 0), (-1, -1), 8),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
            ("TOPPADDING",    (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("ALIGN",         (0, 0), (0, -1),  "CENTER"),
            ("LINEABOVE",     (0, 0), (-1, 0),  0.5, C_MID_GRAY),
            ("LINEBEFORE",    (1, 0), (1, -1),  0.4, C_MID_GRAY),
            ("LINEBEFORE",    (2, 0), (2, -1),  0.4, C_MID_GRAY),
        ]))
        story.append(row_table)
        story.append(Spacer(1, 6))

    return story



# ── Recommendations ───────────────────────────────────────────────────────────


def _build_recommendations(report, styles) -> list:
    story = []
    story.append(PageBreak())
    story.append(Paragraph("Recommendations", styles["h1"]))
    story.append(HRFlowable(width=CONTENT_W, thickness=1,
                             color=C_ACCENT, spaceAfter=10))

    m = report.metadata

    recs = []
    if m.verdict == "reject":
        recs.append(("❌ Must fix before release",
                      "There are critical issues that must be resolved before this code is safe to ship to users."))
    if m.sub_scores.get("security", 100) < 80:
        recs.append(("🔒 Run a security audit",
                      "Fix all High/Critical security findings first. "
                      "Consider running an automated security scanner like Bandit or Semgrep in your CI pipeline."))
    if m.sub_scores.get("performance", 100) < 70:
        recs.append(("⚡ Improve performance",
                      "Review nested loops and database queries. "
                      "Add caching where possible and avoid loading large data sets all at once."))
    if m.sub_scores.get("bug", 100) < 75:
        recs.append(("🐛 Add more tests",
                      "Write unit tests for the functions flagged with bugs. "
                      "Try to cover edge cases like empty inputs, large numbers, and null values."))
    if m.sub_scores.get("style", 100) < 70:
        recs.append(("✏️ Add a linter",
                      "Add a tool like Flake8 or ESLint to your project. "
                      "Run it automatically every time code is committed (pre-commit hook or CI)."))
    if m.score >= 85:
        recs.append(("✅ Code quality is good",
                      "The codebase is in good shape. Keep following the same practices. "
                      "Review the remaining Low/Info issues during your next refactor."))
    if not recs:
        recs.append(("📋 Keep improving",
                      "Address the findings above starting from Critical down to Low. "
                      "Re-run this review after fixes to track your score improvement."))

    for title, detail in recs:
        rec_card = [
            Paragraph(f"<b>{_escape(title)}</b>", styles["h3"]),
            Paragraph(_escape(detail), styles["body"]),
        ]
        story.append(BorderCard(
            rec_card,
            bg_color=C_LIGHT_GRAY,
            border_color=C_ACCENT,
            padding=12,
        ))
        story.append(Spacer(1, 8))

    return story



# ── Plagiarism Section (optional) ─────────────────────────────────────────────


def _build_plagiarism_section(plagiarism_result: dict, styles) -> list:
    story = []
    score    = plagiarism_result.get("score", 0)
    summary  = plagiarism_result.get("summary", "")
    evidence = plagiarism_result.get("evidence", [])
    remedies = plagiarism_result.get("remedies", [])
    blocked  = plagiarism_result.get("blocked", False)

    bg_color     = colors.HexColor("#fff1f1") if blocked else colors.HexColor("#fff7ed")
    border_color = C_CRITICAL_SIDE if blocked else C_HIGH_SIDE

    card_parts = []
    title_text = "🤖 AI-Generated / Plagiarised Code Detected" if blocked else "⚠️ Possible AI-Generated Code"
    card_parts.append(Paragraph(f"<b>{title_text}</b>", styles["h2"]))

    score_s = ParagraphStyle("ps",
        fontName="Helvetica-Bold", fontSize=26,
        textColor=border_color, alignment=TA_CENTER)
    card_parts.append(Paragraph(f"{score}%", score_s))

    sub_s = ParagraphStyle("psub",
        fontName="Helvetica", fontSize=9,
        textColor=C_TEXT_MUTED, alignment=TA_CENTER, spaceAfter=8)
    card_parts.append(Paragraph("Plagiarism / AI Score", sub_s))

    if summary:
        card_parts.append(Paragraph("📋  Summary", styles["finding_label"]))
        card_parts.append(Paragraph(_escape(summary), styles["finding_text"]))

    if blocked:
        blocked_s = ParagraphStyle("bk",
            fontName="Helvetica-Bold", fontSize=10,
            textColor=C_REJECT_FG, backColor=C_REJECT_BG, spaceAfter=6)
        card_parts.append(Paragraph(
            "🚫  Review was not performed because the code appears to be AI-generated or plagiarised.",
            blocked_s
        ))

    if evidence:
        card_parts.append(Paragraph("🔍  Evidence Found", styles["finding_label"]))
        for ev in evidence[:5]:
            card_parts.append(Paragraph(f"• {_escape(ev)}", styles["finding_step"]))

    if remedies:
        card_parts.append(Paragraph("✅  What You Should Do", styles["finding_label"]))
        for i, rem in enumerate(remedies[:5], 1):
            card_parts.append(Paragraph(f"{i}. {_escape(rem)}", styles["finding_step"]))

    story.append(BorderCard(card_parts, bg_color=bg_color,
                             border_color=border_color, padding=14))
    story.append(Spacer(1, 16))

    if blocked:
        story.append(PageBreak())

    return story



# ── Main Entry Point ──────────────────────────────────────────────────────────


def generate_pdf_report(
    report,
    output_path: str,
    plagiarism_result: Optional[dict] = None,
) -> str:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=MARGIN,
        leftMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=0.9 * inch,
        title=f"Code Review — {report.metadata.project_name}",
        author="AI Code Review Assistant",
        subject="Automated Code Quality Report",
    )

    styles = _build_styles()
    story  = []

    story.extend(_build_cover(report, styles))
    story.extend(_build_toc(report, styles))

    if plagiarism_result and plagiarism_result.get("score", 0) > 30:
        story.extend(_build_plagiarism_section(plagiarism_result, styles))

    all_findings = sum(len(fr.findings) for fr in report.files)
    if all_findings == 0:
        no_issue_s = ParagraphStyle("ni",
            fontName="Helvetica-Bold", fontSize=14,
            textColor=C_ACCEPT_FG, alignment=TA_CENTER)
        story.append(Spacer(1, 0.5 * inch))
        story.append(Paragraph(
            "✅ No issues found! The code looks clean.", no_issue_s
        ))
    else:
        story.extend(_build_findings(report, styles))

    story.extend(_build_priority_actions(report, styles))
    story.extend(_build_recommendations(report, styles))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[PDF] Report saved → {output_path}")
    return output_path