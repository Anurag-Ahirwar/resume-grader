import streamlit as st
from utils.ui import apply_custom_css

st.set_page_config(
    page_title="Resume Grader - AI-Powered Resume Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_custom_css()

# Main Title
st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <h1 style='font-size: 3rem; color: #1f77b4; margin-bottom: 0.5rem;'>📊 Resume Grader</h1>
        <p style='font-size: 1.2rem; color: #666;'>AI-Powered Resume Analysis & Scoring Platform</p>
    </div>
""", unsafe_allow_html=True)

st.divider()

# Features Section
col1, col2, col3 = st.columns(3)

with col1:
    with st.container():
        st.markdown("""
        <div style='text-align: center; padding: 1.5rem; border-radius: 0.5rem; border: 2px solid rgba(31, 119, 180, 0.3);'>
            <h2 style='font-size: 2.5rem; margin-bottom: 0.5rem;'>📤</h2>
            <h3 style='color: #1f77b4;'>Upload Resumes</h3>
            <p style='opacity: 0.8;'>Upload PDF resumes in bulk and process them automatically</p>
        </div>
        """, unsafe_allow_html=True)

with col2:
    with st.container():
        st.markdown("""
        <div style='text-align: center; padding: 1.5rem; border-radius: 0.5rem; border: 2px solid rgba(31, 119, 180, 0.3);'>
            <h2 style='font-size: 2.5rem; margin-bottom: 0.5rem;'>📄</h2>
            <h3 style='color: #1f77b4;'>Resume List</h3>
            <p style='opacity: 0.8;'>View all processed resumes with filtering and sorting options</p>
        </div>
        """, unsafe_allow_html=True)

with col3:
    with st.container():
        st.markdown("""
        <div style='text-align: center; padding: 1.5rem; border-radius: 0.5rem; border: 2px solid rgba(31, 119, 180, 0.3);'>
            <h2 style='font-size: 2.5rem; margin-bottom: 0.5rem;'>📊</h2>
            <h3 style='color: #1f77b4;'>Detailed Reports</h3>
            <p style='opacity: 0.8;'>Get comprehensive scoring and improvement suggestions</p>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# Key Features
st.markdown("### ✨ Key Features")
with st.container():
    st.markdown("""
    <div style='padding: 1.5rem; border-radius: 0.5rem; margin-top: 1rem; border: 2px solid rgba(31, 119, 180, 0.2);'>
        <ul style='font-size: 1.1rem; line-height: 2; margin: 0;'>
            <li><strong>Multi-Bucket Scoring:</strong> Evaluates resumes across 7 key dimensions</li>
            <li><strong>Smart Extraction:</strong> Automatically extracts contact info, skills, experience, and projects</li>
            <li><strong>Actionable Feedback:</strong> Get specific improvement suggestions for each resume</li>
            <li><strong>Bulk Processing:</strong> Process multiple resumes simultaneously</li>
            <li><strong>Export Options:</strong> Download results as CSV, Excel, or JSON</li>
            <li><strong>Advanced Filtering:</strong> Filter by score, missing links, and project count</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# Quick Start
st.markdown("### 🚀 Quick Start")
st.markdown("""
1. **Navigate to "📤 Upload Resumes"** from the sidebar
2. **Select PDF files** you want to analyze
3. **Click "Upload & Process"** to start analysis
4. **View results** in "📄 Resume List" and click on any resume for detailed insights
""")

# Sidebar info
with st.sidebar:
    st.markdown("### 📖 Navigation")
    st.markdown("""
    - **📤 Upload Resumes**  
      Upload and process PDF resumes
    
    - **📄 Resume List**  
      Browse all processed resumes
    
    - **📊 Resume Detail**  
      View detailed analysis
    
    - **⚙️ Admin**  
      Database management
    """)
    
    st.divider()
    st.markdown("### 💡 Tips")
    st.info("💡 **Tip:** Use filters in Resume List to quickly find resumes that need attention (e.g., missing LinkedIn or GitHub)")
