import streamlit as st
from utils.api import reset_db
from utils.auth import require_login, require_role, render_session_sidebar
from utils.ui import set_header

require_login()
render_session_sidebar()
require_role("admin")

set_header("⚠️ Admin – Reset Database", "Danger zone. This action cannot be undone.")

st.warning("""
⚠️ **This will permanently delete:**
- All resume database records (scores, buckets, mistakes)
- All uploaded PDF files from the uploads folder

**This action cannot be undone!**
""")

confirm = st.checkbox("I understand this will permanently delete all data AND uploaded files.")

if st.button("🔥 Reset Database", type="primary"):
    if not confirm:
        st.error("Please confirm before resetting the database.")
    else:
        with st.spinner("Resetting database..."):
            res = reset_db()

        if res.get("status") == "success":
            message = res.get("message", "Database reset successfully!")
            st.success(f"✅ {message}")
            st.balloons()
        else:
            st.error(f"❌ Reset failed: {res.get('message')}")
