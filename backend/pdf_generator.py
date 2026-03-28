# pdf_generator.py
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel
from typing import List

def generate_pdf_report(report: "FullReport", output_path: str) -> str:
    """
    Generate a professional PDF report from FullReport.
    Includes title page, summary, scores, findings by severity, and recommendations.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch,
    )
    
    styles = getSampleStyleSheet()
    
    # ── Custom styles ──────────────────────────────────────────────────────
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor("#1F2121"),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor("#2180D1"),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold',
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor("#1F2121"),
        alignment=TA_JUSTIFY,
        spaceAfter=6,
    )
    
    severity_styles = {
        "Critical": ParagraphStyle('Critical', parent=styles['Normal'], textColor=colors.red, fontName='Helvetica-Bold'),
        "High": ParagraphStyle('High', parent=styles['Normal'], textColor=colors.HexColor("#FF6600"), fontName='Helvetica-Bold'),
        "Medium": ParagraphStyle('Medium', parent=styles['Normal'], textColor=colors.HexColor("#FFB600"), fontName='Helvetica-Bold'),
        "Low": ParagraphStyle('Low', parent=styles['Normal'], textColor=colors.blue),
        "Info": ParagraphStyle('Info', parent=styles['Normal'], textColor=colors.grey),
    }
    
    # ── Build story ────────────────────────────────────────────────────────
    story = []
    m = report.metadata
    
    # Title page
    story.append(Spacer(1, 1.5*inch))
    story.append(Paragraph("CODE REVIEW REPORT", title_style))
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(f"Project: <b>{m.project_name}</b>", heading_style))
    story.append(Spacer(1, 0.1*inch))
    
    # Score gauge (text-based)
    verdict_color = {
        "accept": "#00AA00",
        "needs_changes": "#FF9900",
        "reject": "#DD0000",
    }.get(m.verdict, "#666666")
    
    score_text = f"""
    <b>Overall Score:</b> <font color="{verdict_color}"><b>{m.score}/100</b></font><br/>
    <b>Verdict:</b> <font color="{verdict_color}"><b>{m.verdict.upper()}</b></font><br/>
    <b>Total Findings:</b> {m.total_findings}<br/>
    <b>Files Analyzed:</b> {m.total_files}<br/>
    <b>Analyzed:</b> {m.analyzed_at.split('T')[0]} at {m.analyzed_at.split('T')[1][:8]}
    """
    story.append(Paragraph(score_text, normal_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Sub-scores table
    if m.sub_scores:
        story.append(Paragraph("Category Scores", heading_style))
        sub_table_data = [["Category", "Score", "Status"]]
        for cat, score in m.sub_scores.items():
            status_color = "#00AA00" if score >= 80 else "#FF9900" if score >= 60 else "#DD0000"
            sub_table_data.append([
                cat.capitalize(),
                f"{score}/100",
                f"<font color='{status_color}'>{'✓' if score >= 80 else '⚠' if score >= 60 else '✗'}</font>"
            ])
        
        sub_table = Table(sub_table_data, colWidths=[2*inch, 2*inch, 1.5*inch])
        sub_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2180D1")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        story.append(sub_table)
        story.append(Spacer(1, 0.3*inch))
    
    # Page break before findings
    story.append(PageBreak())
    
    # Findings by severity
    for severity in ["Critical", "High", "Medium", "Low", "Info"]:
        findings_by_sev = []
        for file_report in report.files:
            findings_by_sev.extend([f for f in file_report.findings if f.severity == severity])
        
        if not findings_by_sev:
            continue
        
        emoji = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🔵", "Info": "⚪"}.get(severity, "")
        story.append(Paragraph(f"{emoji} {severity} Severity ({len(findings_by_sev)} findings)", heading_style))
        
        for i, f in enumerate(findings_by_sev, 1):
            story.append(Spacer(1, 0.1*inch))
            finding_title = f"<b>{i}. [{f.issue_type.upper()}] {f.file_path} (Line {f.start_line})</b>"
            story.append(Paragraph(finding_title, severity_styles.get(severity, normal_style)))
            
            story.append(Paragraph(f"<b>Description:</b> {f.description}", normal_style))
            story.append(Paragraph(f"<b>Confidence:</b> {int(f.confidence*100)}%", normal_style))
            story.append(Paragraph(f"<b>Remediation:</b> {f.remediation.text}", normal_style))
            
            if f.remediation.code_snippet:
                story.append(Paragraph("<b>Code Suggestion:</b>", normal_style))
                story.append(Paragraph(f"<pre>{f.remediation.code_snippet}</pre>", normal_style))
            
            if f.tags:
                story.append(Paragraph(f"<b>Tags:</b> {', '.join(f.tags)}", normal_style))
            
            if f.references:
                story.append(Paragraph(f"<b>References:</b> {', '.join(f.references)}", normal_style))
            
            story.append(Spacer(1, 0.1*inch))
        
        story.append(Spacer(1, 0.2*inch))
    
    # Recommendations
    story.append(PageBreak())
    story.append(Paragraph("Recommendations", heading_style))
    
    recommendations = _generate_recommendations(m)
    for rec in recommendations:
        story.append(Paragraph(f"• {rec}", normal_style))
    
    # Build PDF
    doc.build(story)
    print(f"[PDF] Report saved → {output_path}")
    return output_path


def _generate_recommendations(metadata) -> List[str]:
    """Generate actionable recommendations based on report."""
    recs = []
    score = metadata.score
    verdict = metadata.verdict
    
    if verdict == "reject":
        recs.append("Critical issues must be resolved before production deployment.")
    
    if metadata.sub_scores.get("security", 100) < 80:
        recs.append("Security audit recommended — address all High/Critical findings immediately.")
    
    if metadata.sub_scores.get("performance", 100) < 70:
        recs.append("Performance optimization required — review nested loops and expensive I/O operations.")
    
    if metadata.sub_scores.get("bug", 100) < 75:
        recs.append("Increase test coverage to catch logic bugs earlier in development.")
    
    if metadata.sub_scores.get("style", 100) < 70:
        recs.append("Establish code style guidelines and run linters in CI/CD pipeline.")
    
    if score >= 85:
        recs.append("✓ Code quality is good — maintain current practices.")
    
    return recs
