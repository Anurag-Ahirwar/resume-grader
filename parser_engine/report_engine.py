def generate_resume_report(buckets, mistakes):
    """
    buckets: list of {name, score, weight}
    mistakes: list of {category, mistake, feedback, section}
    """

    strengths = []
    improvements = []
    summary_lines = []

    # Analyze buckets
    for b in buckets:
        name = b["name"]
        score = b["score"]

        if score >= 80:
            strengths.append(f"{name} is strong")
        elif score >= 60:
            improvements.append(f"{name} can be improved")
        else:
            improvements.append(f"{name} is weak and needs attention")

    # Analyze mistakes
    mistake_summary = {}
    for m in mistakes:
        section = m.get("section", "General")
        mistake_summary.setdefault(section, []).append(m["feedback"])

    # Build summary
    if len(improvements) == 0:
        verdict = "Excellent resume with no major issues."
    elif len(improvements) <= 2:
        verdict = "Good resume with a few improvement areas."
    else:
        verdict = "Resume needs significant improvements."

    summary_lines.append(verdict)

    return {
        "verdict": verdict,
        "strengths": strengths,
        "improvements": improvements,
        "section_feedback": mistake_summary,
        "top_fixes": improvements[:3]
    }
