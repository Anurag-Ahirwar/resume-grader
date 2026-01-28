import streamlit as st
import pandas as pd
from utils.api import get_resume_list, export_as
from utils.ui import set_header, get_score_color
from datetime import datetime

# Header
set_header("📄 Resume List", "View all processed resumes and filter by score or attributes.")

# ----------------------------
# Filters
# ----------------------------
st.markdown("### 🔍 Filters")

filter_col1, filter_col2, filter_col3 = st.columns(3)

with filter_col1:
    min_score = st.slider("Min Score", min_value=0, max_value=100, value=0, help="Minimum overall score")

with filter_col2:
    max_score = st.slider("Max Score", min_value=0, max_value=100, value=100, help="Maximum overall score")

with filter_col3:
    sort_options = {
        "score_desc": "Score (High to Low)",
        "score_asc": "Score (Low to High)",
        "latest": "Most Recent",
        "oldest": "Oldest First"
    }
    sort_by = st.selectbox("Sort By", options=list(sort_options.keys()), format_func=lambda x: sort_options[x])

st.markdown("#### Additional Filters")
filter_check_col1, filter_check_col2, filter_check_col3 = st.columns(3)

with filter_check_col1:
    missing_linkedin = st.checkbox("Missing LinkedIn", help="Show only resumes without LinkedIn profile")

with filter_check_col2:
    missing_github = st.checkbox("Missing GitHub", help="Show only resumes without GitHub profile")

with filter_check_col3:
    no_projects = st.checkbox("No Projects", help="Show only resumes without projects")

params = {
    "min_score": min_score,
    "max_score": max_score,
    "sort_by": sort_by,
    "missing_linkedin": missing_linkedin,
    "missing_github": missing_github,
    "no_projects": no_projects
}

st.divider()

# ----------------------------
# Fetch Data
# ----------------------------
with st.spinner("Fetching resume list..."):
    data = get_resume_list(params)

resumes = data.get("resumes", [])
total_count = data.get("count", 0)

# Summary Stats
if resumes:
    avg_score = sum(r.get("overall_score", 0) for r in resumes) / len(resumes) if resumes else 0
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Resumes", total_count)
    with col2:
        st.metric("Average Score", f"{avg_score:.1f}")
    with col3:
        high_scores = sum(1 for r in resumes if r.get("overall_score", 0) >= 80)
        st.metric("High Scores (≥80)", high_scores)
    with col4:
        low_scores = sum(1 for r in resumes if r.get("overall_score", 0) < 60)
        st.metric("Needs Improvement (<60)", low_scores)
    
    st.divider()

if not resumes:
    st.warning("⚠️ No resumes found with the selected filters. Try adjusting your filter criteria.")
else:
    # Prepare data for display
    display_data = []
    for resume in resumes:
        contact = resume.get("contact_info", {})
        email = contact.get("emails", [""])[0] if contact.get("emails") else "N/A"
        phone = contact.get("phones", [""])[0] if contact.get("phones") else "N/A"
        linkedin = contact.get("linkedin", "❌ Missing")
        github = contact.get("github", "❌ Missing")
        
        # Format LinkedIn and GitHub
        linkedin_display = "✅ Present" if linkedin and linkedin != "❌ Missing" else "❌ Missing"
        github_display = "✅ Present" if github and github != "❌ Missing" else "❌ Missing"
        
        # Format date
        created_at = resume.get("created_at")
        if created_at:
            try:
                date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                date_str = date_obj.strftime("%Y-%m-%d")
            except:
                date_str = created_at[:10] if len(created_at) >= 10 else "N/A"
        else:
            date_str = "N/A"
        
        display_data.append({
            "Score": resume.get("overall_score", 0),
            "Email": email[:30] + "..." if len(email) > 30 else email,
            "Phone": phone,
            "LinkedIn": linkedin_display,
            "GitHub": github_display,
            "Projects": resume.get("projects_count", 0),
            "Created": date_str,
            "Resume ID": resume.get("resume_id", ""),  # Full ID for display
            "resume_id_internal": resume.get("resume_id", "")  # Keep for reference
        })
    
    df = pd.DataFrame(display_data)
    
    # Create Resume Table with enhanced features
    st.markdown("### 📋 Resume Table")
    st.markdown("💡 **Tip:** Click the copy button next to any Resume ID, or use View Details to see the full analysis")
    
    # Display table with better formatting
    st.dataframe(
        df[["Score", "Email", "Phone", "LinkedIn", "GitHub", "Projects", "Created", "Resume ID"]],
        use_container_width=True,
        hide_index=True,
        height=400,
        column_config={
            "Score": st.column_config.NumberColumn(
                "Score",
                help="Overall resume score",
                format="%d/100"
            ),
            "Resume ID": st.column_config.TextColumn(
                "Resume ID",
                help="Full Resume ID - Copy this to view details",
                width="medium"
            ),
        }
    )
    
    # Interactive Resume ID actions
    st.markdown("---")
    st.markdown("### 🔍 Quick Actions")
    
    # Create expandable sections for each resume with actions
    for idx, resume in enumerate(resumes):
        resume_id = resume.get("resume_id", "")
        score = resume.get("overall_score", 0)
        
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.text(f"📄 Resume {idx + 1} - Score: {score}/100")
        
        with col2:
            # Copy Resume ID button
            if st.button(f"📋 Copy ID", key=f"copy_{idx}", help="Copy Resume ID to clipboard"):
                st.code(resume_id, language="text")
                st.success("✅ Resume ID displayed above - Copy it!")
        
        with col3:
            # View Details button - sets session state and provides navigation hint
            if st.button(f"👁️ View Details", key=f"view_{idx}", type="primary"):
                st.session_state['selected_resume_id'] = resume_id
                st.info(f"📊 Resume ID: `{resume_id}`\n\n👉 Navigate to **📊 Resume Detail** page from the sidebar to view the full report!")
                st.balloons()

st.divider()

# ----------------------------
# Export Buttons
# ----------------------------
st.markdown("### 📦 Export Data")
st.markdown("Download all resumes data in your preferred format:")

export_col1, export_col2, export_col3 = st.columns(3)

with export_col1:
    if st.button("📤 Download CSV", use_container_width=True, type="secondary"):
        with st.spinner("Generating CSV..."):
            response = export_as("csv")
            if response.status_code == 200:
                st.download_button(
                    "⬇️ Download CSV File",
                    data=response.content,
                    file_name=f"resumes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            else:
                st.error("❌ CSV export failed. Please try again.")

with export_col2:
    if st.button("📘 Download Excel", use_container_width=True, type="secondary"):
        with st.spinner("Generating Excel..."):
            response = export_as("excel")
            if response.status_code == 200:
                st.download_button(
                    "⬇️ Download Excel File",
                    data=response.content,
                    file_name=f"resumes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            else:
                st.error("❌ Excel export failed. Please try again.")

with export_col3:
    if st.button("🔧 View JSON", use_container_width=True, type="secondary"):
        with st.spinner("Loading JSON..."):
            response = export_as("json")
            if response.status_code == 200:
                st.json(response.json())
            else:
                st.error("❌ JSON export failed. Please try again.")
