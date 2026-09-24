import streamlit as st
from utils.api import upload_pdfs, upload_csv, process_resume
from utils.auth import require_login, require_role, render_session_sidebar, current_role
from utils.ui import set_header
import time
import pandas as pd
import io
import requests

require_login()
render_session_sidebar()

set_header("📤 Upload Resumes", "Upload PDFs directly or via CSV with Google Drive links")

# Create tabs for different upload methods
tab1, tab2 = st.tabs(["📄 Upload PDF Files", "📊 Upload CSV (Google Drive Links)"])

# ===================================================================
# TAB 1: Direct PDF Upload
# ===================================================================
with tab1:
    st.info("""
    **Upload PDF files directly from your computer**
    - Select up to 50 PDF files at once
    - Files are uploaded and ready to process immediately
    """)
    
    uploaded_files = st.file_uploader(
        "Choose PDF files",
        type=["pdf"],
        accept_multiple_files=True,
        key="pdf_upload"
    )

    if uploaded_files:
        st.write(f"**{len(uploaded_files)} file(s) selected**")

        if st.button("🚀 Upload & Process Resumes", type="primary", key="upload_pdf"):
            # Prepare files for upload
            files = []
            for f in uploaded_files:
                files.append(("files", (f.name, f.getvalue(), "application/pdf")))
            
            with st.spinner("Uploading..."):
                upload_result = upload_pdfs(files)

            if upload_result and "upload_ids" in upload_result:
                upload_ids = upload_result["upload_ids"]
                st.success(f"✅ Uploaded {len(upload_ids)} resumes successfully")

                # Process resumes
                progress_bar = st.progress(0)
                status_text = st.empty()
                success_count = 0
                error_count = 0

                for idx, upload_id in enumerate(upload_ids):
                    status_text.text(f"Processing resume {idx + 1} of {len(upload_ids)}...")
                    progress_bar.progress((idx + 1) / len(upload_ids))

                    try:
                        result = process_resume(upload_id)
                        if result:
                            success_count += 1
                    except Exception as e:
                        st.error(f"Error processing resume {idx + 1}: {e}")
                        error_count += 1

                status_text.text("")
                st.balloons()
                
                st.success(f"""
                ✅ **Processing Complete!**
                - Successfully processed: {success_count}
                - Errors: {error_count}
                """)

                st.info("👉 Go to **Resume List** to view all processed resumes.")
            else:
                st.error("❌ Upload failed. Please try again.")

# ===================================================================
# TAB 2: CSV Upload with Google Drive Links
# ===================================================================
with tab2:
    if current_role() == "student":
        st.warning("🚫 Bulk CSV upload is available to Recruiters and Admins only.")
        st.stop()

    st.info("""
    **Upload CSV file containing Google Drive links to resumes**
    - CSV must have a column named `resume_link`
    - Links must be publicly accessible (Anyone with link can view)
    - Maximum 200 resumes per CSV file
    """)

    # CSV Template Download
    st.markdown("### 📥 Download CSV Template")
    st.caption("Use this template to create your CSV file")
    
    template_df = pd.DataFrame({
        'resume_link': [
            'https://drive.google.com/file/d/YOUR_FILE_ID_1/view',
            'https://drive.google.com/file/d/YOUR_FILE_ID_2/view',
            'https://drive.google.com/file/d/YOUR_FILE_ID_3/view',
        ]
    })
    
    csv_template = template_df.to_csv(index=False)
    st.download_button(
        "⬇️ Download Template CSV",
        csv_template,
        "resume_upload_template.csv",
        "text/csv",
        help="Download a template CSV file to fill in with your Google Drive links"
    )
    
    # Instructions expander
    with st.expander("📖 How to get Google Drive shareable links"):
        st.markdown("""
        **For each resume PDF in Google Drive:**
        
        1. Right-click the file → Click "Share"
        2. Change to "Anyone with the link"
        3. Set permission to "Viewer"
        4. Click "Copy link"
        5. Paste the link in your CSV file
        
        **Link format examples:**
        - `https://drive.google.com/file/d/FILE_ID/view`
        - `https://drive.google.com/open?id=FILE_ID`
        
        ⚠️ **Important**: Files MUST be publicly accessible (not private)
        """)
    
    # CSV File Upload
    st.markdown("### 📤 Upload Your CSV File")
    
    csv_file = st.file_uploader(
        "Choose CSV file with Google Drive links",
        type=['csv'],
        key='csv_upload'
    )
    
    if csv_file:
        try:
            # Preview CSV
            df = pd.read_csv(csv_file)
            st.write(f"**Preview** ({len(df)} resumes found)")
            st.dataframe(df.head(10), use_container_width=True)
            
            # Validate required column
            if 'resume_link' not in df.columns:
                st.error(f"❌ CSV must have 'resume_link' column. Found columns: {', '.join(df.columns)}")
            elif len(df) > 200:
                st.error(f"❌ Too many resumes. Maximum: 200, Found: {len(df)}")
            else:
                st.success(f"✅ Valid CSV with {len(df)} resume links")
                
                # Upload and process button
                if st.button("🚀 Download & Process All Resumes", type="primary", key="upload_csv_btn"):
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    status_text.text("Uploading CSV and downloading resumes from Google Drive...")
                    
                    # Upload CSV to backend
                    try:
                        result = upload_csv(csv_file.getvalue())

                        progress_bar.progress(0.5)
                        
                        # Display results
                        st.markdown("---")
                        st.markdown("### 📊 Download Results")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total", result['total'])
                        with col2:
                            st.metric("✅ Successful", result['successful'])
                        with col3:
                            st.metric("❌ Failed", result['failed'])
                        
                        # Show detailed results
                        if result['results']:
                            results_df = pd.DataFrame(result['results'])
                            
                            # Successful downloads
                            success_df = results_df[results_df['status'] == 'success']
                            if not success_df.empty:
                                st.success(f"**✅ Successfully Downloaded ({len(success_df)} resumes)**")
                                st.dataframe(success_df[['row', 'link', 'upload_id', 'size_kb']], use_container_width=True)
                                
                                # Now process them
                                if result['upload_ids']:
                                    st.markdown("### ⚙️ Processing Resumes")
                                    process_progress = st.progress(0)
                                    process_status = st.empty()
                                    
                                    processed = 0
                                    for idx, upload_id in enumerate(result['upload_ids']):
                                        process_status.text(f"Processing resume {idx + 1} of {len(result['upload_ids'])}...")
                                        try:
                                            process_result = process_resume(upload_id)
                                            if process_result:
                                                processed += 1
                                        except Exception as e:
                                            st.warning(f"Error processing resume {idx + 1}: {str(e)[:100]}")
                                        process_progress.progress((idx + 1) / len(result['upload_ids']))
                                    
                                    process_status.text("")
                                    st.balloons()
                                    st.success(f"🎉 Successfully processed {processed} out of {len(result['upload_ids'])} resumes!")
                            
                            # Failed downloads
                            failed_df = results_df[results_df['status'] == 'failed']
                            if not failed_df.empty:
                                st.error(f"**❌ Failed Downloads ({len(failed_df)} resumes)**")
                                st.dataframe(failed_df[['row', 'link', 'error']], use_container_width=True)
                                
                                with st.expander("💡 Common Issues & Solutions"):
                                    st.markdown("""
                                    **File is private or link is invalid**
                                    - Ensure file has "Anyone with the link" permission
                                    - Verify the link is copied correctly
                                    
                                    **Downloaded file is not a PDF**
                                    - Make sure link points to a PDF file
                                    - Don't link to Google Docs/Sheets (export as PDF first)
                                    
                                    **Download timeout**
                                    - File may be too large (max 10MB)
                                    - Try re-uploading or reducing file size
                                    """)
                        
                        st.info("👉 Go to **Resume List** to view all processed resumes.")
                        
                    except requests.exceptions.RequestException as e:
                        st.error(f"❌ Upload failed: {str(e)}")
                        st.error("Make sure the backend server is running on http://127.0.0.1:8000")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
        
        except Exception as e:
            st.error(f"❌ Failed to read CSV: {str(e)}")
