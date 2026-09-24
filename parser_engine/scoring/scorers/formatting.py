"""Formatting & Styling bucket scorer.

Rules are unchanged from the original parser_engine/scoring_engine.py (V1):
  - 1-page rule: page_count == 1 -> +25, 2 pages -> +15, else 0
  - bullet consistency -> +15 (or +8 partial)
  - spacing consistency -> up to +20
  - font consistency -> up to +20
  - margin analysis -> up to +20
  - contact info present at top -> +20

Double-counting check (V2 execution plan Phase 13): margin narrow/wide/unbalanced-lr/unbalanced-tb
deductions each target a distinct measurement (different sides / different failure mode) drawn from
a single 20-point pool for this bucket, and no other bucket also penalizes margins — verified during
the V2 audit, no change needed here.
"""
import re
from typing import Dict, List, Tuple

from ..contract import BucketScore, Finding
from ..config import BUCKET_NAMES, BUCKET_WEIGHTS

BUCKET_ID = "formatting"


def score(raw_text: str, extracted: dict) -> BucketScore:
    diagnostics = extracted.get("_diagnostics", {})
    page_count = diagnostics.get("page_count", None)
    total = 0
    findings: List[Finding] = []

    # 1. Page rule (max 25)
    if page_count == 1:
        total += 25
    elif page_count == 2:
        total += 15
        findings.append(_neg(
            "page_count", "More than 1 page",
            "Try fitting to 1 page if you are an early-career candidate; condense less relevant details.",
            "formatting", impact=10, value=str(page_count), expected="1",
        ))
    else:
        findings.append(_neg(
            "page_count", "Multiple pages",
            "Multiple pages detected — ensure only necessary info remains.",
            "formatting", impact=25, value=str(page_count), expected="1",
        ))

    # 2. Bullet consistency (max 15)
    bullet_patterns = [
        r"(^|\n)\s*[-•\*]\s+",
        r"(^|\n)\s*[-•\*]",
        r"(^|\n)\s*\d+[\.\)]\s+",
        r"(^|\n)\s*[a-z][\.\)]\s+",
    ]
    bullet_count = sum(1 for pattern in bullet_patterns if re.search(pattern, raw_text, re.MULTILINE))
    inline_bullets = len(re.findall(r"[-•\*]\s+[A-Z]", raw_text))

    if bullet_count > 0 or inline_bullets >= 2:
        all_bullets = re.findall(r"(^|\n)\s*[-•\*]\s*", raw_text, re.MULTILINE)
        numbered = re.findall(r"(^|\n)\s*\d+[\.\)]\s+", raw_text, re.MULTILINE)
        total_bullet_indicators = len(all_bullets) + inline_bullets

        if total_bullet_indicators >= 3 or len(numbered) >= 3:
            total += 15
        else:
            total += 8
            findings.append(_neg(
                "bullet_consistency", "Inconsistent bullet usage",
                "Use consistent bullet points or numbering throughout your resume for better readability.",
                "formatting", impact=7,
            ))
    else:
        findings.append(_neg(
            "bullet_consistency", "No bullets detected",
            "Use concise bullets for experience and projects to improve readability.",
            "formatting", impact=15,
        ))

    # 3. Spacing (max 20)
    spacing_score, spacing_findings = _analyze_spacing_consistency(raw_text)
    total += spacing_score
    findings.extend(spacing_findings)

    # 4. Font consistency (max 20)
    font_score, font_findings = _analyze_font_consistency(diagnostics)
    total += font_score
    findings.extend(font_findings)

    # 5. Margins (max 20)
    margin_score, margin_findings = _analyze_margins(diagnostics)
    total += margin_score
    findings.extend(margin_findings)

    # 6. Contact info present (max 20)
    contact = extracted.get("contact", {})
    if contact.get("phones") or contact.get("emails") or contact.get("linkedin") or contact.get("github"):
        total += 20
    else:
        findings.append(_neg(
            "contact_at_top", "Missing contact info",
            "Add phone/email/LinkedIn so recruiters can reach you.",
            "formatting", impact=20,
        ))

    raw_score = max(0.0, min(100.0, float(total)))
    return BucketScore(
        bucket_id=BUCKET_ID,
        name=BUCKET_NAMES[BUCKET_ID],
        raw_score=raw_score,
        weight=BUCKET_WEIGHTS[BUCKET_ID],
        findings=findings,
    )


def _neg(criterion, message, feedback, section, impact=None, value=None, expected=None) -> Finding:
    return Finding(
        criterion=criterion, type="negative", category=BUCKET_NAMES[BUCKET_ID],
        message=message, feedback=feedback, section=section,
        impact=impact, value=value, expected=expected,
    )


def _analyze_spacing_consistency(raw_text: str) -> Tuple[int, List[Finding]]:
    lines = raw_text.splitlines()
    if not lines:
        return 0, [_neg("spacing", "Empty resume", "Resume appears to be empty.", "formatting", impact=20)]

    total = 20
    findings: List[Finding] = []

    blank_lines = [i for i, line in enumerate(lines) if not line.strip()]
    total_blank = len(blank_lines)
    total_lines = len(lines)

    if total_lines > 30:
        if total_blank == 0:
            findings.append(_neg(
                "spacing", "No spacing between sections",
                "Add blank lines between major sections for better readability.", "formatting", impact=5,
            ))
            total -= 5
        else:
            blank_ratio = total_blank / total_lines
            if blank_ratio > 0.25:
                findings.append(_neg(
                    "spacing", "Excessive blank lines",
                    f"Too many blank lines ({blank_ratio*100:.1f}% of resume). Remove extra spacing to make it more compact.",
                    "formatting", impact=10, value=f"{blank_ratio*100:.1f}%", expected="<25%",
                ))
                total -= 10
            elif blank_ratio < 0.02:
                findings.append(_neg(
                    "spacing", "Insufficient spacing",
                    "Add more spacing between sections for better visual separation.", "formatting", impact=3,
                ))
                total -= 3

    non_blank_runs = []
    current_run = 0
    for line in lines:
        if line.strip():
            current_run += 1
        else:
            if current_run > 0:
                non_blank_runs.append(current_run)
            current_run = 0
    if current_run > 0:
        non_blank_runs.append(current_run)

    if len(non_blank_runs) > 3:
        avg_run = sum(non_blank_runs) / len(non_blank_runs)
        max_run = max(non_blank_runs)
        min_run = min(non_blank_runs)
        if max_run > avg_run * 2.5 or min_run < avg_run * 0.3:
            findings.append(_neg(
                "spacing", "Inconsistent spacing between sections",
                "Maintain consistent spacing between all sections for a professional look.", "formatting", impact=5,
            ))
            total -= 5

    consec_blank = len(re.findall(r"\n\s*\n\s*\n+", raw_text))
    if consec_blank > 0:
        findings.append(_neg(
            "spacing", "Multiple consecutive blank lines",
            f"Found {consec_blank} instances of 3+ consecutive blank lines. Use single blank lines between sections.",
            "formatting", impact=8, value=str(consec_blank), expected="0",
        ))
        total -= 8

    return max(0, total), findings


def _analyze_font_consistency(diagnostics: dict) -> Tuple[int, List[Finding]]:
    font_info = diagnostics.get("font_consistency")

    if font_info is None:
        # No font info available (pypdf fallback was used) - neutral full points, no findings.
        return 20, []

    if isinstance(font_info, dict):
        font_score = font_info.get("score", 0)
        issues = font_info.get("issues", [])
        findings: List[Finding] = []

        if font_score >= 80:
            total = 20
        elif font_score >= 60:
            total = 15
            findings.append(_neg(
                "font_consistency", "Minor font inconsistencies",
                "Consider using more consistent font sizes throughout your resume.", "formatting", impact=5,
            ))
        elif font_score >= 40:
            total = 10
            findings.append(_neg(
                "font_consistency", "Font inconsistencies detected",
                "Use 2-3 consistent font sizes (e.g., one for headers, one for body text) for a professional appearance.",
                "formatting", impact=10,
            ))
        else:
            total = 5
            findings.append(_neg(
                "font_consistency", "Significant font inconsistencies",
                "Your resume uses too many different font sizes. Standardize to 2-3 sizes for better readability.",
                "formatting", impact=15,
            ))

        for issue in issues:
            findings.append(_neg("font_consistency", "Font formatting issue", issue, "formatting", impact=5))

        return total, findings

    return 15, []


def _analyze_margins(diagnostics: dict) -> Tuple[int, List[Finding]]:
    margins = diagnostics.get("margins")
    if margins is None:
        return 20, []  # No margin data available - neutral score, no penalty.

    total = 20
    findings: List[Finding] = []

    left = margins.get("left", 0)
    right = margins.get("right", 0)
    top = margins.get("top", 0)
    bottom = margins.get("bottom", 0)

    MIN_MARGIN = 36  # 0.5 inch
    MAX_MARGIN = 90  # 1.25 inch
    BALANCE_THRESHOLD = 18  # 0.25 inch

    narrow_margins = []
    if left < MIN_MARGIN:
        narrow_margins.append(f'left ({left/72:.2f}")')
    if right < MIN_MARGIN:
        narrow_margins.append(f'right ({right/72:.2f}")')
    if top < MIN_MARGIN:
        narrow_margins.append(f'top ({top/72:.2f}")')
    if bottom < MIN_MARGIN:
        narrow_margins.append(f'bottom ({bottom/72:.2f}")')
    if narrow_margins:
        total -= 8
        margins_str = ", ".join(narrow_margins)
        findings.append(_neg(
            "margins", f"Narrow margin(s): {margins_str}",
            f'The {margins_str} margin(s) are too narrow (< 0.5"). Increase to at least 0.5-0.75 inch for better readability and printing.',
            "formatting", impact=8, expected='>= 0.5"',
        ))

    wide_margins = []
    if left > MAX_MARGIN:
        wide_margins.append(f'left ({left/72:.2f}")')
    if right > MAX_MARGIN:
        wide_margins.append(f'right ({right/72:.2f}")')
    if top > MAX_MARGIN:
        wide_margins.append(f'top ({top/72:.2f}")')
    if bottom > MAX_MARGIN:
        wide_margins.append(f'bottom ({bottom/72:.2f}")')
    if wide_margins:
        total -= 5
        margins_str = ", ".join(wide_margins)
        findings.append(_neg(
            "margins", f"Excessive margin(s): {margins_str}",
            f'The {margins_str} margin(s) are too wide (> 1.25"). Reduce to 0.5-1 inch to utilize space better.',
            "formatting", impact=5, expected='<= 1.25"',
        ))

    lr_diff = abs(left - right)
    if lr_diff > BALANCE_THRESHOLD:
        total -= 4
        findings.append(_neg(
            "margins", "Unbalanced left-right margins",
            f'Left margin ({left/72:.2f}") and right margin ({right/72:.2f}") differ by {lr_diff/72:.2f}". Make them equal for a professional look.',
            "formatting", impact=4, value=f'{lr_diff/72:.2f}"', expected='<= 0.25"',
        ))

    tb_diff = abs(top - bottom)
    if tb_diff > BALANCE_THRESHOLD:
        total -= 3
        findings.append(_neg(
            "margins", "Unbalanced top-bottom margins",
            f'Top margin ({top/72:.2f}") and bottom margin ({bottom/72:.2f}") differ by {tb_diff/72:.2f}". Balance them for better visual appeal.',
            "formatting", impact=3, value=f'{tb_diff/72:.2f}"', expected='<= 0.25"',
        ))

    if any(m < 10 for m in [left, right, top, bottom]):
        total = 0
        edge_issues = []
        if left < 10:
            edge_issues.append("left")
        if right < 10:
            edge_issues.append("right")
        if top < 10:
            edge_issues.append("top")
        if bottom < 10:
            edge_issues.append("bottom")
        edges_str = ", ".join(edge_issues)
        findings.append(_neg(
            "margins", f"Text touching {edges_str} edge(s)",
            f'Text appears to touch the {edges_str} page edge(s). Add proper margins (0.5-1 inch on all sides) for professional appearance and printing.',
            "formatting", impact=20,
        ))

    return max(0, total), findings
