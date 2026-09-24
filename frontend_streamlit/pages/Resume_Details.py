import streamlit as st
import pandas as pd
from utils.api import get_resume_detail
from utils.auth import require_login, render_session_sidebar
from utils.ui import set_header, get_score_color

try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

require_login()
render_session_sidebar()

# Header
set_header(
    "📊 Resume Detail Report",
    "View detailed scoring, strengths, weaknesses, and improvement suggestions."
)

# ----------------------------
# Input with Auto-Load Support
# ----------------------------

# Check if resume_id is in session state (from Resume List page)
default_resume_id = st.session_state.get('selected_resume_id', '')

input_col1, input_col2 = st.columns([3, 1])

with input_col1:
    resume_id = st.text_input(
        "Enter Resume ID",
        value=default_resume_id,
        placeholder="Paste a resume_id from the Resume List",
        help="Copy the Resume ID from the Resume List page or use View Details button"
    )

with input_col2:
    st.write("")  # Spacing
    st.write("")  # Spacing
    fetch_btn = st.button("🔍 Fetch Report", type="primary", use_container_width=True)

# Auto-load if resume ID is pre-filled
if default_resume_id and not fetch_btn:
    st.info("💡 Resume ID loaded from Resume List! Click 'Fetch Report' to view details.")

# ----------------------------
# Fetch Report
# ----------------------------
if fetch_btn:
    if not resume_id.strip():
        st.warning("⚠️ Please enter a valid Resume ID.")
    else:
        with st.spinner("Fetching report..."):
            data = get_resume_detail(resume_id)

        # Handle backend errors
        if isinstance(data, dict) and "detail" in data:
            st.error(f"❌ Error: {data['detail']}")
        else:
            overall_score = data.get("overall_score", 0)
            color_class = get_score_color(overall_score)
            
            # ----------------------------
            # Overall Score - Enhanced Display
            # ----------------------------
            st.markdown("<br>", unsafe_allow_html=True)
            
            score_col1, score_col2, score_col3 = st.columns([1, 2, 1])
            
            with score_col2:
                # Determine gradient based on score
                if overall_score >= 80:
                    gradient = "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
                    emoji = "🌟"
                elif overall_score >= 60:
                    gradient = "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)"
                    emoji = "✨"
                else:
                    gradient = "linear-gradient(135deg, #fa709a 0%, #fee140 100%)"
                    emoji = "📈"
                    
                st.markdown(f"""
                <div style='text-align: center; padding: 3rem 2rem; background: {gradient}; 
                            border-radius: 1.5rem; color: white; box-shadow: 0 8px 16px rgba(0,0,0,0.2);'>
                    <h3 style='color: white; margin-bottom: 0.5rem; font-weight: 300; letter-spacing: 2px;'>OVERALL SCORE {emoji}</h3>
                    <h1 style='font-size: 5rem; margin: 1rem 0; color: white; font-weight: bold;'>{overall_score}</h1>
                    <p style='font-size: 1.3rem; margin-top: 0.5rem; color: rgba(255,255,255,0.95); font-weight: 300;'>out of 100</p>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.divider()
            
            # ----------------------------
            # Bucket Scores Visualization
            # ----------------------------
            st.markdown("### 📊 Scoring Breakdown")
            
            buckets = data.get("buckets", [])
            if buckets:
                # Create visualization
                bucket_df = pd.DataFrame(buckets)
                bucket_df = bucket_df.sort_values("score", ascending=True)
                
                if PLOTLY_AVAILABLE:
                    # Bar chart
                    fig = px.bar(
                        bucket_df,
                        x="score",
                        y="name",
                        orientation='h',
                        color="score",
                        color_continuous_scale="RdYlGn",
                        range_color=[0, 100],
                        title="Score by Category",
                        labels={"score": "Score", "name": "Category"}
                    )
                    fig.update_layout(
                        height=400,
                        showlegend=False,
                        xaxis_range=[0, 100],
                        yaxis={'categoryorder': 'total ascending'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    # Fallback: simple bar chart using streamlit
                    st.bar_chart(bucket_df.set_index("name")[["score"]])
                
                # Bucket scores table
                st.markdown("#### Detailed Bucket Scores")
                display_buckets = []
                for bucket in buckets:
                    weighted = bucket.get("weighted_score")
                    display_buckets.append({
                        "Category": bucket.get("name", "N/A"),
                        "Score": f"{bucket.get('score', 0):.0f}/100",
                        "Weight": f"{bucket.get('weight', 0)*100:.0f}%",
                        "Weighted Contribution": f"{weighted:.1f}" if weighted is not None else "N/A",
                    })

                st.dataframe(pd.DataFrame(display_buckets), use_container_width=True, hide_index=True)

                scoring_version = data.get("scoring_version")
                weight_total = data.get("weight_total")
                if scoring_version:
                    st.caption(
                        f"Scoring engine v{scoring_version} · weights normalized from "
                        f"{weight_total*100:.0f}% total" if weight_total else f"Scoring engine v{scoring_version}"
                    )
            
            st.divider()
            
            # ----------------------------
            # Report Summary with Enhanced Cards
            # ----------------------------
            report = data.get("report", {})
            
            # Quick stats in metric cards
            metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
            
            with metric_col1:
                strengths_count = len(report.get("strengths", []))
                st.metric("✅ Strengths", strengths_count, help="Number of identified strengths")
            
            with metric_col2:
                improvements_count = len(report.get("improvements", []))
                st.metric("⚠️ Improvements", improvements_count, help="Areas needing improvement")
            
            with metric_col3:
                buckets = data.get("buckets", [])
                avg_bucket_score = sum(b.get("score", 0) for b in buckets) / len(buckets) if buckets else 0
                st.metric("📊 Avg Bucket Score", f"{avg_bucket_score:.1f}")
            
            with metric_col4:
                mistakes_count = len(data.get("mistakes", []))
                st.metric("🔍 Issues Found", mistakes_count)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Verdict in an attractive card
            st.markdown("### 🧠 Resume Analysis Summary")
            verdict = report.get("verdict", "No summary available.")
            
            if "Excellent" in verdict or "excellent" in verdict:
                st.success(f"✅ {verdict}")
            elif "Good" in verdict or "good" in verdict:
                st.info(f"💡 {verdict}")
            else:
                st.warning(f"⚠️ {verdict}")
            
            st.divider()
            
            # ----------------------------
            # Strengths and Improvements
            # ----------------------------
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### ✅ Strengths")
                strengths = report.get("strengths", [])
                if strengths:
                    for s in strengths:
                        st.markdown(f"✅ **{s}**")
                else:
                    st.info("No major strengths detected.")
            
            with col2:
                st.markdown("### ⚠️ Areas to Improve")
                improvements = report.get("improvements", [])
                if improvements:
                    for i in improvements:
                        st.markdown(f"⚠️ **{i}**")
                else:
                    st.success("No major improvement areas detected!")
            
            st.divider()
            
            # ----------------------------
            # Top Fixes in Enhanced Format
            # ----------------------------
            st.markdown("### 🚀 Top Recommendations")
            top_fixes = report.get("top_fixes", [])
            if top_fixes:
                with st.container():
                    st.markdown("""
                    <div style='padding: 1.5rem; border-radius: 0.75rem; border: 2px solid rgba(31, 119, 180, 0.2); margin-bottom: 1rem;'>
                    """, unsafe_allow_html=True)
                    for idx, fix in enumerate(top_fixes, 1):
                        st.markdown(f"**{idx}.** {fix}")
                    st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.info("✨ No specific recommendations available - Great job!")
            
            st.divider()
            
            # ----------------------------
            # Mistakes & Feedback
            # ----------------------------
            st.markdown("### ❌ Detailed Feedback")
            
            mistakes = data.get("mistakes", [])
            if mistakes:
                mistakes_df = pd.DataFrame(mistakes)
                mistakes_by_category = mistakes_df.groupby("category").size().reset_index(name="count")
                
                # Mistakes count by category
                if len(mistakes_by_category) > 0:
                    if PLOTLY_AVAILABLE:
                        fig_mistakes = px.pie(
                            mistakes_by_category,
                            values="count",
                            names="category",
                            title="Mistakes by Category"
                        )
                        st.plotly_chart(fig_mistakes, use_container_width=True)
                    else:
                        st.bar_chart(mistakes_by_category.set_index("category")[["count"]])
                
                # Detailed mistakes table
                st.markdown("#### All Issues Found")
                severity_icons = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "⚪"}
                for mistake in mistakes:
                    icon = severity_icons.get(mistake.get("severity"), "🔴")
                    with st.expander(f"{icon} {mistake.get('category', 'General')}: {mistake.get('mistake', 'Issue')}"):
                        st.markdown(f"**Feedback:** {mistake.get('feedback', 'No feedback available.')}")
                        if mistake.get("value") or mistake.get("expected"):
                            st.caption(
                                f"Measured: {mistake.get('value', 'N/A')} · Expected: {mistake.get('expected', 'N/A')}"
                            )
                        if mistake.get('section'):
                            st.caption(f"Section: {mistake.get('section')}")
            else:
                st.success("🎉 No issues found! This resume looks great!")
            
            st.divider()
            
            # ----------------------------
            # Extracted Information with Better Layout
            # ----------------------------
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### 📋 Extracted Information")
            st.markdown("Detailed breakdown of all information extracted from the resume")
            
            info_tabs = st.tabs(["📧 Contact", "💼 Experience", "🎯 Projects", "🛠️ Skills", "📚 Education"])
            
            with info_tabs[0]:
                contact_info = data.get("contact_info", {})
                if contact_info:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("#### Email")
                        emails = contact_info.get("emails", [])
                        if emails:
                            for email in emails:
                                st.code(email, language="text")
                        else:
                            st.info("No email found")
                        
                        st.markdown("#### Phone")
                        phones = contact_info.get("phones", [])
                        if phones:
                            for phone in phones:
                                st.code(phone, language="text")
                        else:
                            st.info("No phone found")
                    
                    with col2:
                        st.markdown("#### LinkedIn")
                        linkedin = contact_info.get("linkedin")
                        if linkedin:
                            st.code(linkedin, language="text")
                        else:
                            st.warning("❌ LinkedIn not found")
                        
                        st.markdown("#### GitHub")
                        github = contact_info.get("github")
                        if github:
                            st.code(github, language="text")
                        else:
                            st.warning("❌ GitHub not found")
                else:
                    st.info("No contact information extracted")
            
            with info_tabs[1]:
                experience = data.get("experience", [])
                if experience:
                    for exp in experience:
                        st.markdown(f"**{exp.get('section', 'Experience')}**")
                        st.json(exp)
                else:
                    st.info("No experience information found")
            
            with info_tabs[2]:
                projects = data.get("projects", [])
                if projects:
                    for idx, project in enumerate(projects, 1):
                        st.markdown(f"#### Project {idx}")
                        st.json(project)
                else:
                    st.info("No projects found")
            
            with info_tabs[3]:
                skills = data.get("skills", [])
                if skills:
                    st.markdown("#### Technical Skills")
                    # Display skills as chips
                    skill_chips = " ".join([f"`{skill}`" for skill in skills])
                    st.markdown(skill_chips)
                else:
                    st.info("No skills found")
            
            with info_tabs[4]:
                education = data.get("education", [])
                if education:
                    st.json(education)
                else:
                    st.info("No education information found")
