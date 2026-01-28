# parser_engine/scoring_engine.py
import re
from typing import Tuple, List, Dict

def score_formatting_and_styling(raw_text: str, extracted: dict) -> Tuple[int, List[Dict]]:
    """
    Enhanced formatting and styling scoring with font, spacing, and margin analysis.
    Rules:
      - 1-page rule: if page_count == 1 -> +25, else if 2 pages -> +15, else 0
      - consistent bullets: presence of '-' or '•' or numbered lists -> +15 if found
      - spacing consistency: detect irregular spacing patterns -> +20 if consistent
      - font consistency: analyze font sizes/styles -> +20 if consistent
      - margin analysis: check all 4 margins are proper (0.5-1 inch) -> +20 if good
      - presence of header/contact at top -> +20
    Returns: (score_out_of_100_for_this_bucket, list_of_mistake_dicts)
    """

    diagnostics = extracted.get("_diagnostics", {})
    page_count = diagnostics.get("page_count", None)
    score = 0
    mistakes = []

    # 1. page rule (max 25)
    if page_count == 1:
        score += 25
    elif page_count == 2:
        score += 15
        mistakes.append({
            "mistake": "More than 1 page",
            "feedback": "Try fitting to 1 page if you are an early-career candidate; condense less relevant details."
        })
    else:
        mistakes.append({
            "mistake": "Multiple pages",
            "feedback": "Multiple pages detected — ensure only necessary info remains."
        })

    # 2. bullets consistency (max 15)
    # More flexible bullet detection - handle various formats
    bullet_patterns = [
        r"(^|\n)\s*[-•\*]\s+",  # Bullet points with space after
        r"(^|\n)\s*[-•\*]",  # Bullet points without space (more lenient)
        r"(^|\n)\s*\d+[\.\)]\s+",  # Numbered lists
        r"(^|\n)\s*[a-z][\.\)]\s+",  # Lettered lists
    ]
    bullet_count = sum(1 for pattern in bullet_patterns if re.search(pattern, raw_text, re.MULTILINE))
    
    # Also check for bullets in the middle of lines (PDF extraction might break line breaks)
    inline_bullets = len(re.findall(r"[-•\*]\s+[A-Z]", raw_text))  # Bullet followed by capital letter
    
    if bullet_count > 0 or inline_bullets >= 2:
        # Check if bullets are used consistently
        all_bullets = re.findall(r"(^|\n)\s*[-•\*]\s*", raw_text, re.MULTILINE)
        numbered = re.findall(r"(^|\n)\s*\d+[\.\)]\s+", raw_text, re.MULTILINE)
        total_bullet_indicators = len(all_bullets) + inline_bullets
        
        if total_bullet_indicators >= 3 or len(numbered) >= 3:
            score += 15
        else:
            score += 8
            mistakes.append({
                "mistake": "Inconsistent bullet usage",
                "feedback": "Use consistent bullet points or numbering throughout your resume for better readability."
            })
    else:
        mistakes.append({
            "mistake": "No bullets detected",
            "feedback": "Use concise bullets for experience and projects to improve readability."
        })

    # 3. Enhanced spacing analysis (max 20)
    spacing_score, spacing_mistakes = _analyze_spacing_consistency(raw_text)
    score += spacing_score
    mistakes.extend(spacing_mistakes)

    # 4. Font consistency (max 20) - NEW!
    font_score, font_mistakes = _analyze_font_consistency(diagnostics)
    score += font_score
    mistakes.extend(font_mistakes)

    # 5. Margin analysis (max 20) - NEW!
    margin_score, margin_mistakes = _analyze_margins(diagnostics)
    score += margin_score
    mistakes.extend(margin_mistakes)

    # 6. header/contact at top (max 20)
    contact = extracted.get("contact", {})
    if contact.get("phones") or contact.get("emails") or contact.get("linkedin") or contact.get("github"):
        score += 20
    else:
        mistakes.append({
            "mistake": "Missing contact info",
            "feedback": "Add phone/email/LinkedIn so recruiters can reach you."
        })

    # clamp score to [0,100]
    final_score = max(0, min(100, int(score)))
    # structure mistakes to include category/section placeholders
    mistake_items = []
    for m in mistakes:
        mistake_items.append({
            "category": "Formatting & Styling",
            "mistake": m.get("mistake"),
            "feedback": m.get("feedback"),
            "section": m.get("section")
        })

    return final_score, mistake_items


def _analyze_spacing_consistency(raw_text: str) -> Tuple[int, List[Dict]]:
    """
    Analyze spacing consistency in the resume.
    Returns: (score_0_20, list_of_mistakes)
    """
    lines = raw_text.splitlines()
    if not lines:
        return 0, [{"mistake": "Empty resume", "feedback": "Resume appears to be empty."}]
    
    score = 20
    mistakes = []
    
    # Count blank lines
    blank_lines = [i for i, line in enumerate(lines) if not line.strip()]
    total_blank = len(blank_lines)
    total_lines = len(lines)

    # Only be strict about spacing on longer resumes; short ones can be dense without penalty
    if total_lines > 30:
        if total_blank == 0:
            # No explicit blank lines at all in a long resume
            mistakes.append({
                "mistake": "No spacing between sections",
                "feedback": "Add blank lines between major sections for better readability."
            })
            score -= 5
        else:
            blank_ratio = total_blank / total_lines

            # Too many blank lines (more than 25% of lines)
            if blank_ratio > 0.25:
                mistakes.append({
                    "mistake": "Excessive blank lines",
                    "feedback": f"Too many blank lines ({blank_ratio*100:.1f}% of resume). Remove extra spacing to make it more compact."
                })
                score -= 10

            # Too few blank lines (very dense, less than 2% of lines)
            elif blank_ratio < 0.02:
                mistakes.append({
                    "mistake": "Insufficient spacing",
                    "feedback": "Add more spacing between sections for better visual separation."
                })
                score -= 3
    
    # Check for inconsistent spacing patterns
    # Look for sections with very different spacing
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
        # Check variance in run lengths
        avg_run = sum(non_blank_runs) / len(non_blank_runs)
        max_run = max(non_blank_runs)
        min_run = min(non_blank_runs)
        
        # If there's high variance, spacing might be inconsistent
        if max_run > avg_run * 2.5 or min_run < avg_run * 0.3:
            mistakes.append({
                "mistake": "Inconsistent spacing between sections",
                "feedback": "Maintain consistent spacing between all sections for a professional look."
            })
            score -= 5
    
    # Check for consecutive blank lines (more than 2)
    consec_blank = len(re.findall(r"\n\s*\n\s*\n+", raw_text))
    if consec_blank > 0:
        mistakes.append({
            "mistake": "Multiple consecutive blank lines",
            "feedback": f"Found {consec_blank} instances of 3+ consecutive blank lines. Use single blank lines between sections."
        })
        score -= 8
    
    return max(0, score), mistakes


def _analyze_font_consistency(diagnostics: dict) -> Tuple[int, List[Dict]]:
    """
    Analyze font consistency from diagnostics.
    Returns: (score_0_20, list_of_mistakes)
    """
    font_info = diagnostics.get("font_consistency")

    if font_info is None:
        # No font info available (pypdf fallback was used) – do NOT penalize or show a warning.
        # Give neutral full points for this sub-aspect and no mistakes so users don't see this on every resume.
        return 20, []
    
    if isinstance(font_info, dict):
        font_score = font_info.get("score", 0)
        issues = font_info.get("issues", [])
        
        mistakes = []
        score = 0
        
        # Convert font consistency score (0-100) to our scale (0-20)
        if font_score >= 80:
            score = 20
        elif font_score >= 60:
            score = 15
            mistakes.append({
                "mistake": "Minor font inconsistencies",
                "feedback": "Consider using more consistent font sizes throughout your resume."
            })
        elif font_score >= 40:
            score = 10
            mistakes.append({
                "mistake": "Font inconsistencies detected",
                "feedback": "Use 2-3 consistent font sizes (e.g., one for headers, one for body text) for a professional appearance."
            })
        else:
            score = 5
            mistakes.append({
                "mistake": "Significant font inconsistencies",
                "feedback": "Your resume uses too many different font sizes. Standardize to 2-3 sizes for better readability."
            })
        
        # Add specific issues from font analysis
        for issue in issues:
            mistakes.append({
                "mistake": "Font formatting issue",
                "feedback": issue
            })
        
        return score, mistakes
    
    return 15, []


def _analyze_margins(diagnostics: dict) -> Tuple[int, List[Dict]]:
    """
    Analyze margins from PDF layout.
    Returns: (score_0_20, list_of_mistakes)
    
    Good margins (industry standard):
    - Left/Right: 36-72 points (0.5-1 inch)
    - Top/Bottom: 36-72 points (0.5-1 inch)
    - Balanced (difference < 18 points / 0.25 inch)
    """
    margins = diagnostics.get('margins')
    
    if margins is None:
        # No margin data available (pypdf fallback or margin calculation failed)
        return 20, []  # Neutral score, no penalty
    
    score = 20
    mistakes = []
    
    left = margins.get('left', 0)
    right = margins.get('right', 0)
    top = margins.get('top', 0)
    bottom = margins.get('bottom', 0)
    
    # Constants
    MIN_MARGIN = 36  # 0.5 inch
    MAX_MARGIN = 90  # 1.25 inch
    BALANCE_THRESHOLD = 18  # 0.25 inch difference
    
    # 1. Check if margins are too narrow (< 0.5 inch)
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
        score -= 8
        margins_str = ', '.join(narrow_margins)
        mistakes.append({
            'mistake': f'Narrow margin(s): {margins_str}',
            'feedback': f'The {margins_str} margin(s) are too narrow (< 0.5"). Increase to at least 0.5-0.75 inch for better readability and printing.'
        })
    
    # 2. Check if margins are too wide (> 1.25 inch)
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
        score -= 5
        margins_str = ', '.join(wide_margins)
        mistakes.append({
            'mistake': f'Excessive margin(s): {margins_str}',
            'feedback': f'The {margins_str} margin(s) are too wide (> 1.25"). Reduce to 0.5-1 inch to utilize space better.'
        })
    
    # 3. Check balance between left and right
    lr_diff = abs(left - right)
    if lr_diff > BALANCE_THRESHOLD:
        score -= 4
        mistakes.append({
            'mistake': 'Unbalanced left-right margins',
            'feedback': f'Left margin ({left/72:.2f}") and right margin ({right/72:.2f}") differ by {lr_diff/72:.2f}". Make them equal for a professional look.'
        })
    
    # 4. Check balance between top and bottom
    tb_diff = abs(top - bottom)
    if tb_diff > BALANCE_THRESHOLD:
        score -= 3
        mistakes.append({
            'mistake': 'Unbalanced top-bottom margins',
            'feedback': f'Top margin ({top/72:.2f}") and bottom margin ({bottom/72:.2f}") differ by {tb_diff/72:.2f}". Balance them for better visual appeal.'
        })
    
    # 5. Check for no margins at all (text touching edges)
    if any(m < 10 for m in [left, right, top, bottom]):  # < 0.14 inch
        score = 0
        edge_issues = []
        if left < 10:
            edge_issues.append('left')
        if right < 10:
            edge_issues.append('right')
        if top < 10:
            edge_issues.append('top')
        if bottom < 10:
            edge_issues.append('bottom')
        
        edges_str = ', '.join(edge_issues)
        mistakes.append({
            'mistake': f'Text touching {edges_str} edge(s)',
            'feedback': f'Text appears to touch the {edges_str} page edge(s). Add proper margins (0.5-1 inch on all sides) for professional appearance and printing.'
        })
    
    return max(0, score), mistakes
def score_contact_info(extracted: dict) -> Tuple[int, List[Dict]]:
    """
    Rules:
      - Phone present -> +30
      - Email present -> +30
      - LinkedIn present -> +20
      - GitHub present -> +20

    Max = 100
    Missing fields add mistakes with feedback.
    """

    contact = extracted.get("contact", {})
    raw_text = extracted.get("raw_text", "")
    score = 0
    mistakes = []

    # Phone - check both extracted and raw text as fallback
    if contact.get("phones"):
        score += 30
    else:
        # Fallback: check raw text for phone patterns
        import re
        phone_pattern = re.compile(r"(\+?\d{1,3}[-.\s]?)?(\(?\d{2,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}")
        if phone_pattern.search(raw_text):
            score += 30  # Found in raw text, extraction just missed it
        else:
            mistakes.append({
                "category": "Contact Information",
                "mistake": "Phone number missing",
                "feedback": "Add a reachable phone number so recruiters can easily contact you.",
                "section": "contact"
            })

    # Email - check both extracted and raw text as fallback
    if contact.get("emails"):
        score += 30
    else:
        # Fallback: check raw text for email patterns
        import re
        email_pattern = re.compile(r"[a-zA-Z0-9.\-+_]+@[a-zA-Z0-9.\-+_]+\.[a-zA-Z]+")
        if email_pattern.search(raw_text):
            score += 30  # Found in raw text, extraction just missed it
        else:
            mistakes.append({
                "category": "Contact Information",
                "mistake": "Email missing",
                "feedback": "Include a professional email address.",
                "section": "contact"
            })

    # LinkedIn
    if contact.get("linkedin"):
        score += 20
    else:
        # Fallback check
        import re
        linkedin_pattern = re.compile(r"(linkedin\.com\/in\/[A-Za-z0-9\-\_]+)", re.IGNORECASE)
        if linkedin_pattern.search(raw_text):
            score += 20
        else:
            mistakes.append({
                "category": "Contact Information",
                "mistake": "LinkedIn not found",
                "feedback": "Add a LinkedIn profile link to strengthen your professional presence.",
                "section": "contact"
            })

    # GitHub
    if contact.get("github"):
        score += 20
    else:
        # Fallback check
        import re
        github_pattern = re.compile(r"(github\.com\/[A-Za-z0-9\-\_]+)", re.IGNORECASE)
        if github_pattern.search(raw_text):
            score += 20
        else:
            mistakes.append({
                "category": "Contact Information",
                "mistake": "GitHub not found",
                "feedback": "Add a GitHub link to showcase your projects and contributions.",
                "section": "contact"
            })

    # clamp 0–100
    final_score = max(0, min(100, score))
    return final_score, mistakes
def score_education(extracted: dict) -> Tuple[int, List[Dict]]:
    """
    Score education section: order matters, presence of degree/year is expected.
    """
    sections = extracted.get("sections_found", [])
    mistakes = []
    score = 0
    raw = extracted.get("raw_text", "")
    raw_lower = raw.lower()

    # education must be present - check both sections and raw text
    has_edu_section = any("education" in s.lower() for s in sections)
    # Also check raw text for "EDUCATION" header (case insensitive)
    has_edu_in_text = bool(re.search(r'\b(education|educational)\b', raw_lower))
    
    if has_edu_section or has_edu_in_text:
        score += 40
    else:
        # Don't add mistake if we find degree keywords (education content exists, just section header missing)
        degree_keywords = [
            "btech", "b.tech", "be ", "b.e", "bachelor", "bachelors",
            "mtech", "m.tech", "master", "masters",
            "msc", "m.sc", "bsc", "b.sc",
            "mba", "m.b.a",
            "bba", "b.b.a",
            "bca", "b.c.a",
            "bcom", "b.com",
            "ba ", "b.a ",
            "ma ", "m.a ",
            "degree", "diploma", "graduation", "graduated",
        ]
        has_degree_content = any(k in raw_lower for k in degree_keywords)
        if not has_degree_content:
            mistakes.append({
                "category": "Education",
                "mistake": "Missing education section",
                "feedback": "Add an education section with degree, institute, and year.",
                "section": "education"
            })

    # try detect degree/years
    # Broader set of common degree keywords (engineering, management, compsci, etc.)
    degree_keywords = [
        "btech", "b.tech", "be ", "b.e", "bachelor", "bachelors",
        "mtech", "m.tech", "master", "masters",
        "msc", "m.sc", "bsc", "b.sc",
        "mba", "m.b.a",
        "bba", "b.b.a",
        "bca", "b.c.a",
        "bcom", "b.com",
        "ba ", "b.a ",
        "ma ", "m.a ",
        "bachelors of", "bachelor of",
        "master of business administration",
        "master of computer applications",
        "computer science", "artificial intelligence", "data science",
    ]
    if any(k in raw_lower for k in degree_keywords):
        score += 40
    else:
        mistakes.append({
            "category": "Education",
            "mistake": "Degree keywords not clearly detected",
            "feedback": "Ensure your degree names are clearly written (e.g. 'B.Tech in CSE', 'MBA in Marketing', 'BCA').",
            "section": "education"
        })

    # look for dates around education (years like 2024, 2025, etc.)
    if re.search(r"\b(20\d{2}|19\d{2})\b", raw):
        score += 20
    else:
        mistakes.append({
            "category": "Education",
            "mistake": "Missing year details",
            "feedback": "Include graduation year (e.g. 2023).",
            "section": "education"
        })

    final_score = min(100, max(0, score))
    return final_score, mistakes

def score_technical_skills(extracted: dict) -> Tuple[int, List[Dict]]:
    skills = extracted.get("skills", [])
    mistakes = []
    score = 0

    if len(skills) >= 5:
        score += 40
    elif len(skills) > 0:
        score += 20
    else:
        mistakes.append({
            "category": "Technical Skills",
            "mistake": "Missing technical skills",
            "feedback": "Add relevant technical skills (Python, SQL, etc.).",
            "section": "skills"
        })

    top_langs = ["python", "java", "javascript", "c++", "sql", "react", "node"]
    if any(sl.lower() in top_langs for sl in skills):
        score += 40

    if len(set(skills)) < len(skills):
        mistakes.append({
            "category": "Technical Skills",
            "mistake": "Duplicate skills detected",
            "feedback": "Avoid repeating skills.",
            "section": "skills"
        })
    else:
        score += 20

    final_score = min(100, max(0, score))
    return final_score, mistakes
def score_soft_skills(raw_text: str) -> Tuple[int, List[Dict]]:
    soft_keywords = ["communication", "leadership", "teamwork", "collaboration", "problem solving", "critical thinking"]
    lower = raw_text.lower()

    present = [s for s in soft_keywords if s in lower]
    score = min(100, len(present) * 20)
    mistakes = []

    if score == 0:
        mistakes.append({
            "category": "Soft Skills",
            "mistake": "Soft skills missing",
            "feedback": "Add soft skills such as teamwork, leadership, or communication.",
            "section": "soft_skills"
        })

    return score, mistakes

def score_projects(extracted: dict) -> Tuple[int, List[Dict]]:
    projects = extracted.get("projects", [])
    raw = extracted.get("raw_text", "")
    raw_lower = raw.lower()
    mistakes = []
    score = 0

    # Check both extracted projects and raw text
    has_projects_section = len(projects) > 0
    has_projects_in_text = bool(re.search(r'\b(project|projects)\b', raw_lower))
    # Check for project-related keywords
    project_keywords = ["github", "built", "developed", "dashboard", "application", "system", "model"]
    has_project_keywords = any(kw in raw_lower for kw in project_keywords)
    
    # number of projects
    if has_projects_section:
        if len(projects) >= 2:
            score += 50
        elif len(projects) == 1:
            score += 25
    elif has_projects_in_text and has_project_keywords:
        # Found project section in text but extraction didn't work - give partial credit
        score += 30
    else:
        mistakes.append({
            "category": "Projects",
            "mistake": "No projects found",
            "feedback": "Add at least 1–2 technical projects with clear description.",
            "section": "projects"
        })

    # action verbs
    verbs = ["developed", "built", "designed", "implemented", "created", "built a", "developed a"]
    if any(v in raw_lower for v in verbs):
        score += 30
    else:
        # Only add mistake if we actually found projects
        if has_projects_section or has_projects_in_text:
            score += 15  # Partial credit
        else:
            mistakes.append({
                "category": "Projects",
                "mistake": "Missing action verbs",
                "feedback": "Use strong action verbs in project descriptions.",
                "section": "projects"
            })

    if len(str(raw)) > 200:
        score += 20

    final_score = min(100, max(0, score))
    return final_score, mistakes
def score_work_experience(extracted: dict) -> Tuple[int, List[Dict]]:
    exp_blocks = extracted.get("experience_blocks", [])
    raw = extracted.get("raw_text", "")
    raw_lower = raw.lower()
    mistakes = []
    score = 0

    # Check both extracted blocks and raw text for experience indicators
    has_exp_section = len(exp_blocks) > 0
    has_exp_in_text = bool(re.search(r'\b(experience|work experience|employment|internship|intern)\b', raw_lower))
    # Also check for common job-related keywords
    has_job_keywords = bool(re.search(r'\b(worked|developed|managed|led|coordinated|assisted|supported)\b', raw_lower))
    
    if has_exp_section or (has_exp_in_text and has_job_keywords):
        score += 50
    else:
        mistakes.append({
            "category": "Work Experience",
            "mistake": "No work experience section found",
            "feedback": "Add internships or experience entries with responsibilities.",
            "section": "experience"
        })

    # measurable outcomes: numbers like increased % or productivity
    if re.search(r"\b\d+[%]\b", raw):
        score += 30

    if re.search(r"\b(20\d{2}|19\d{2})\b", raw):  # Years
        score += 20

    final_score = min(100, max(0, score))
    return final_score, mistakes
