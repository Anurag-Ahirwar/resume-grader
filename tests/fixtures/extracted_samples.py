"""Hand-built `extracted` dicts + raw_text used across the V2 scorer unit tests.

Scorers consume the post-parsing `extracted` dict (and/or raw_text) rather than a PDF directly,
so these fixtures give equivalent, deterministic coverage without needing curated PDF assets.
"""
import copy

_COMPLETE_RAW_TEXT = """JOHN DOE
Email: john@example.com | Phone: +91 9876543210
LinkedIn: linkedin.com/in/johndoe | GitHub: github.com/johndoe

EDUCATION
B.Tech in Computer Science, XYZ University, 2022

PROJECTS
- Built a web application using React and Node.js for task management
- Developed a machine learning model to predict housing prices

EXPERIENCE
Software Engineering Intern at Tech Corp (2021-2022)
- Worked on backend services, developed REST APIs, led a small team
- Improved response time by 30%

SKILLS
Python, JavaScript, React, Node, SQL, Docker

SOFT SKILLS
Strong communication, leadership, and teamwork skills. Collaboration across teams.
"""

_COMPLETE_DIAGNOSTICS = {
    "page_count": 1,
    "font_consistency": {"score": 90, "issues": []},
    "margins": {"left": 54, "right": 54, "top": 54, "bottom": 54, "page_width": 612, "page_height": 792},
    "links": [],
}


def complete_extracted():
    return {
        "contact": {
            "phones": ["+919876543210"],
            "emails": ["john@example.com"],
            "linkedin": "linkedin.com/in/johndoe",
            "github": "github.com/johndoe",
        },
        "sections_found": ["education", "projects", "experience", "skills"],
        "skills": ["python", "javascript", "react", "node", "sql", "docker"],
        "experience_blocks": [{"section": "experience", "raw": "...", "bullets": ["Worked on backend services"]}],
        "projects": [{"title_and_desc": "Built a web app"}, {"title_and_desc": "Developed an ML model"}],
        "raw_text": _COMPLETE_RAW_TEXT,
        "raw_text_length": len(_COMPLETE_RAW_TEXT),
        "_diagnostics": copy.deepcopy(_COMPLETE_DIAGNOSTICS),
    }


def empty_extracted():
    return {
        "contact": {"phones": [], "emails": [], "linkedin": None, "github": None},
        "sections_found": [],
        "skills": [],
        "experience_blocks": [],
        "projects": [],
        "raw_text": "",
        "raw_text_length": 0,
        "_diagnostics": {"page_count": None, "font_consistency": None, "margins": None, "links": []},
    }


def missing_contact_extracted():
    data = complete_extracted()
    data["contact"] = {"phones": [], "emails": [], "linkedin": None, "github": None}
    data["raw_text"] = "EDUCATION\nB.Tech in Computer Science, XYZ University, 2022\n\nNo contact details here."
    return data


def missing_education_extracted():
    data = complete_extracted()
    data["sections_found"] = ["projects", "experience", "skills"]
    data["raw_text"] = _COMPLETE_RAW_TEXT.replace("EDUCATION\nB.Tech in Computer Science, XYZ University, 2022\n\n", "")
    return data


def missing_projects_and_experience_extracted():
    data = complete_extracted()
    data["projects"] = []
    data["experience_blocks"] = []
    data["raw_text"] = (
        "JOHN DOE\nEmail: john@example.com | Phone: +91 9876543210\n\n"
        "EDUCATION\nB.Tech in Computer Science, XYZ University, 2022\n\n"
        "SKILLS\nPython, JavaScript, React, Node, SQL, Docker\n"
    )
    return data


def narrow_margins_extracted():
    data = complete_extracted()
    data["_diagnostics"]["margins"] = {"left": 20, "right": 20, "top": 54, "bottom": 54, "page_width": 612, "page_height": 792}
    return data


def wide_margins_extracted():
    data = complete_extracted()
    data["_diagnostics"]["margins"] = {"left": 100, "right": 100, "top": 100, "bottom": 100, "page_width": 612, "page_height": 792}
    return data


def unbalanced_margins_extracted():
    data = complete_extracted()
    data["_diagnostics"]["margins"] = {"left": 40, "right": 80, "top": 40, "bottom": 80, "page_width": 612, "page_height": 792}
    return data


def inconsistent_fonts_extracted():
    data = complete_extracted()
    data["_diagnostics"]["font_consistency"] = {
        "score": 20,
        "issues": ["Too many font sizes detected (7). Use 2-3 consistent sizes."],
    }
    return data


def multi_page_extracted():
    data = complete_extracted()
    data["_diagnostics"]["page_count"] = 3
    return data


ALL_FIXTURES = {
    "complete": complete_extracted,
    "empty": empty_extracted,
    "missing_contact": missing_contact_extracted,
    "missing_education": missing_education_extracted,
    "missing_projects_and_experience": missing_projects_and_experience_extracted,
    "narrow_margins": narrow_margins_extracted,
    "wide_margins": wide_margins_extracted,
    "unbalanced_margins": unbalanced_margins_extracted,
    "inconsistent_fonts": inconsistent_fonts_extracted,
    "multi_page": multi_page_extracted,
}
