import streamlit as st

def apply_custom_css():
    """Apply custom CSS styling to the entire app."""
    st.markdown(
        """
        <style>
        /* Main styling */
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        
        /* Headers */
        .big-title {
            font-size: 2.5rem;
            font-weight: 700;
            color: #1f77b4;
            margin-bottom: 0.5rem;
            padding-bottom: 0.5rem;
            border-bottom: 3px solid #1f77b4;
        }
        .sub-title {
            font-size: 1.1rem;
            color: #666;
            margin-top: 0.5rem;
            margin-bottom: 1.5rem;
        }
        
        /* Metrics and cards */
        .metric-card {
            background-color: #f0f2f6;
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 4px solid #1f77b4;
        }
        
        /* Table styling */
        .dataframe {
            font-size: 0.9rem;
        }
        .dataframe th {
            background-color: #1f77b4;
            color: white;
            font-weight: 600;
        }
        .dataframe tr:nth-child(even) {
            background-color: #f8f9fa;
        }
        .dataframe tr:hover {
            background-color: #e9ecef;
        }
        
        /* Buttons */
        .stButton > button {
            border-radius: 0.5rem;
            font-weight: 500;
            transition: all 0.3s;
        }
        
        /* Cards */
        .info-card {
            background-color: #ffffff;
            padding: 1.5rem;
            border-radius: 0.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
        }
        
        /* Score badges */
        .score-excellent { color: #28a745; font-weight: 700; }
        .score-good { color: #17a2b8; font-weight: 700; }
        .score-fair { color: #ffc107; font-weight: 700; }
        .score-poor { color: #dc3545; font-weight: 700; }
        </style>
        """,
        unsafe_allow_html=True,
    )

def set_header(title, subtitle=None):
    """Set page header with title and subtitle."""
    apply_custom_css()
    st.markdown(f"<div class='big-title'>{title}</div>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(f"<div class='sub-title'>{subtitle}</div>", unsafe_allow_html=True)

def get_score_color(score):
    """Get color class based on score."""
    if score >= 80:
        return "score-excellent"
    elif score >= 60:
        return "score-good"
    elif score >= 40:
        return "score-fair"
    else:
        return "score-poor"

def format_score(score):
    """Format score with color."""
    color_class = get_score_color(score)
    return f'<span class="{color_class}">{score}/100</span>'
