import streamlit as st
from credentials import get_user_email, create_user_profile
from llm_config import get_llm
from job_extractor import extract_job_and_contact_info
from cv_extractor import run_cv_pipeline_streamlit
from cv_generator import generate_custom_cv
from cover_letter import generate_cover_letter
from email_sender import send_email_with_cv
import json
import os
import re
from pathlib import Path
import base64
import pandas as pd
import tempfile
from io import BytesIO
import time

# Initialize session state
if 'user_dir' not in st.session_state:
    st.session_state.user_dir = None
if 'user_email' not in st.session_state:
    st.session_state.user_email = None
if 'job_text' not in st.session_state:
    st.session_state.job_text = ""
if 'llm' not in st.session_state:
    st.session_state.llm = None
if 'profile_data' not in st.session_state:
    st.session_state.profile_data = None
if 'selected_cv_path' not in st.session_state:
    st.session_state.selected_cv_path = None
if 'cover_letter_text' not in st.session_state:
    st.session_state.cover_letter_text = ""
if 'cv_option' not in st.session_state:
    st.session_state.cv_option = "Select from Uploaded CVs"
if 'cv_preview' not in st.session_state:
    st.session_state.cv_preview = ""
if 'edit_instructions_cv' not in st.session_state:
    st.session_state.edit_instructions_cv = ""
if 'edit_instructions_letter' not in st.session_state:
    st.session_state.edit_instructions_letter = ""
if 'workflow_mode' not in st.session_state:
    st.session_state.workflow_mode = None  # 'quick_send' or 'step_by_step'
if 'extracted_job_data' not in st.session_state:
    st.session_state.extracted_job_data = None
if 'excel_jobs' not in st.session_state:
    st.session_state.excel_jobs = []
if 'current_job_index' not in st.session_state:
    st.session_state.current_job_index = 0
if 'batch_results' not in st.session_state:
    st.session_state.batch_results = []
if 'batch_in_progress' not in st.session_state:
    st.session_state.batch_in_progress = False

def display_pdf(file_path):
    """Display PDF in Streamlit app"""
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

def quick_send_application():
    """Handle the quick send application process for a single job"""
    try:
        # Extract job data
        st.session_state.extracted_job_data = extract_job_and_contact_info(
            st.session_state.job_text, 
            # st.session_state.llm
        )
        
        # Handle CV based on selection
        if st.session_state.cv_option == "Generate New CV":
            # Generate CV without showing to user
            generate_custom_cv(
                st.session_state.user_dir,
                st.session_state.extracted_job_data,
                action="preview"
            )
            generate_custom_cv(
                st.session_state.user_dir,
                st.session_state.extracted_job_data,
                action="save"
            )
            cv_path = Path(st.session_state.user_dir) / "generated_cv.pdf"
        else:
            # Use selected CV
            cv_path = st.session_state.selected_cv_path
        
        # Generate cover letter without showing to user
        cover_letter_text = generate_cover_letter(
            st.session_state.user_dir,
            st.session_state.extracted_job_data,
            st.session_state.llm,
            action="preview"
        )
        
        # Save cover letter to file
        cover_letter_path = Path(st.session_state.user_dir) / "latest_cover_letter.txt"
        with open(cover_letter_path, "w") as f:
            f.write(cover_letter_text)
        
        # Send application
        send_email_with_cv(
            st.session_state.user_dir,
            st.session_state.extracted_job_data,
            cv_path=str(cv_path))
        
        return True
    except Exception as e:
        st.error(f"Quick send failed: {str(e)}")
        return False

def process_excel_job(job_text, job_index, total_jobs):
    """Process a single job from Excel batch"""
    try:
        # Extract job data
        extracted_job_data = extract_job_and_contact_info(job_text)
        
        # Handle CV based on selection
        if st.session_state.cv_option == "Generate New CV":
            # Generate CV without showing to user
            generate_custom_cv(
                st.session_state.user_dir,
                extracted_job_data,
                action="preview"
            )
            generate_custom_cv(
                st.session_state.user_dir,
                extracted_job_data,
                action="save"
            )
            cv_path = Path(st.session_state.user_dir) / "generated_cv.pdf"
        else:
            # Use selected CV
            cv_path = st.session_state.selected_cv_path
        
        # Generate cover letter without showing to user
        cover_letter_text = generate_cover_letter(
            st.session_state.user_dir,
            extracted_job_data,
            st.session_state.llm,
            action="preview"
        )
        
        # Save cover letter to file
        cover_letter_path = Path(st.session_state.user_dir) / f"cover_letter_job_{job_index}.txt"
        with open(cover_letter_path, "w", encoding='utf-8') as f:
            f.write(cover_letter_text)
        
        # Send application
        send_email_with_cv(
            st.session_state.user_dir,
            extracted_job_data,
            cv_path=str(cv_path))
        
        return True, None
    except Exception as e:
        error_msg = f"Job {job_index+1}/{total_jobs} failed: {str(e)}"
        # Return failure status without creating cover letter file
        return False, error_msg

def process_excel_batch():
    """Process all jobs from the uploaded Excel file"""
    st.session_state.batch_in_progress = True
    st.session_state.batch_results = []
    total_jobs = len(st.session_state.excel_jobs)
    success_count = 0
    failure_count = 0
    
    # Create progress bar and status container
    progress_bar = st.progress(0)
    status_container = st.empty()
    
    for idx, job_text in enumerate(st.session_state.excel_jobs):
        st.session_state.current_job_index = idx
        status_container.write(f"Processing job {idx+1}/{total_jobs}...")
        
        success, error = process_excel_job(job_text, idx, total_jobs)
        
        if success:
            st.session_state.batch_results.append({
                "job_index": idx,
                "status": "Success",
                "error": None
            })
            success_count += 1
        else:
            st.session_state.batch_results.append({
                "job_index": idx,
                "status": "Failed",
                "error": error
            })
            failure_count += 1
        
        # Update progress
        progress_bar.progress((idx + 1) / total_jobs)
        time.sleep(0.5)  # Add slight delay to avoid rate limiting
    
    # Final summary
    progress_bar.empty()
    status_container.empty()
    st.session_state.batch_in_progress = False
    
    return success_count, failure_count

def main():
    st.title("AI Job Application Assistant")
    
    # Handle GROQ API key
    if st.session_state.llm is None:
        if "GROQ_API_KEY" in os.environ:
            st.session_state.llm = get_llm()
        else:
            with st.expander("🔑 Groq API Key Setup", expanded=True):
                st.warning("Please enter your Groq API key to continue")
                api_key = st.text_input("Enter your Groq API key:", type="password", key="api_key_input")
                if st.button("Save API Key", key="save_api_key"):
                    if api_key:
                        os.environ["GROQ_API_KEY"] = api_key
                        st.session_state.llm = get_llm()
                        st.success("API key saved!")
                        st.rerun()
                    else:
                        st.error("Please enter a valid API key")
            return
    
    # Setup environment - User Profile
    if st.session_state.user_dir is None:
        try:
            # Try to get existing user profile
            st.session_state.user_email, st.session_state.user_dir = get_user_email()
            st.success(f"Using existing profile: {st.session_state.user_email}")
        except RuntimeError:
            # Show profile creation form
            with st.expander("👤 Create User Profile", expanded=True):
                st.subheader("Create Your Profile")
                user_email = st.text_input("Your email (for CV storage and sending):", key="user_email_input")
                gmail_app_pwd = st.text_input("Gmail App Password (for sending emails):", type="password", key="gmail_pwd_input")
                
                if st.button("Save Profile", key="save_profile"):
                    if not re.match(r"^[\w\.-]+@[a-zA-Z\d\.-]+\.[a-zA-Z]{2,}$", user_email):
                        st.error("Invalid email format. Use name@domain.com")
                    elif not gmail_app_pwd:
                        st.error("Password cannot be empty")
                    else:
                        try:
                            st.session_state.user_dir = create_user_profile(user_email, gmail_app_pwd)
                            st.session_state.user_email = user_email
                            st.success(f"Profile created for {user_email}!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error creating profile: {str(e)}")
            return
    
    # CV Management
    with st.expander("📝 Manage Your CV", expanded=True):
        try:
            run_cv_pipeline_streamlit(st.session_state.user_dir, st.session_state.llm)
        except Exception as e:
            st.error(f"CV processing error: {str(e)}")
    
    # Combined Job Processing & Application Block
    with st.expander("🚀 Job Application Center", expanded=True):
        # Section 1: Job Source Selection
        st.subheader("1. Job Source")
        job_source = st.radio("Select job source:", 
                             ["Paste Job Text", "Upload Excel File"], 
                             key="job_source_radio")
        
        if job_source == "Paste Job Text":
            # Section 1a: Job Posting Text
            st.session_state.job_text = st.text_area(
                "Paste job posting:", 
                height=300, 
                value=st.session_state.job_text,
                key="job_posting_text",
                placeholder="Copy-paste the full job description here..."
            )
            has_jobs = bool(st.session_state.job_text)
        else:
            # Section 1b: Excel Upload
            uploaded_file = st.file_uploader(
                "Upload Excel file with job postings (each row = one job)", 
                type=["xlsx", "xls"],
                key="excel_uploader"
            )
            
            if uploaded_file is not None:
                try:
                    # Read Excel file
                    df = pd.read_excel(uploaded_file)
                    
                    # Get all non-empty rows from first column
                    job_descriptions = df.iloc[:, 0].dropna().tolist()
                    
                    if job_descriptions:
                        st.session_state.excel_jobs = job_descriptions
                        st.success(f"Loaded {len(job_descriptions)} jobs from Excel file")
                    else:
                        st.warning("Excel file contains no job descriptions in the first column")
                except Exception as e:
                    st.error(f"Error reading Excel file: {str(e)}")
            
            has_jobs = bool(st.session_state.excel_jobs)
        
        # Only show application options if jobs exist
        if has_jobs:
            # Section 2: CV Selection
            st.subheader("2. CV Selection")
            cv_options = ["Generate New CV", "Select from Uploaded CVs"]
            st.session_state.cv_option = st.radio(
                "Choose CV source:", 
                cv_options, 
                key="cv_option_radio"
            )
            
            # Handle CV selection based on choice
            if st.session_state.cv_option == "Select from Uploaded CVs":
                user_path = Path(st.session_state.user_dir)
                pdf_files = list(user_path.glob("*.pdf"))
                
                if pdf_files:
                    file_names = [f.name for f in pdf_files]
                    selected_file = st.selectbox("Choose a CV file:", file_names, key="cv_selectbox")
                    st.session_state.selected_cv_path = user_path / selected_file
                    
                    if st.button("👁️ Preview CV", key="preview_selected_cv", use_container_width=True):
                        try:
                            display_pdf(st.session_state.selected_cv_path)
                        except Exception as e:
                            st.error(f"Error displaying PDF: {str(e)}")
                else:
                    st.warning("No PDF files found. Please upload CVs in the 'Manage Your CV' section.")
                    st.session_state.selected_cv_path = None
            
            # Section 3: Application Options
            st.subheader("3. Application Options")
            
            if job_source == "Paste Job Text":
                # Single job application
                if st.session_state.cv_option == "Generate New CV":
                    # Workflow selection for generated CV
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("🚀 Quick Send", key="quick_send_generated", 
                                    help="Generate and send application without review",
                                    use_container_width=True):
                            with st.spinner("Processing quick send..."):
                                if quick_send_application():
                                    st.success("Application sent successfully!")
                    
                    with col2:
                        if st.button("🔍 Step-by-Step Review", key="step_by_step", 
                                    help="Review and edit application before sending",
                                    use_container_width=True):
                            st.session_state.workflow_mode = "step_by_step"
                            st.session_state.extracted_job_data = extract_job_and_contact_info(
                                st.session_state.job_text, 
                                # st.session_state.llm
                            )
                            st.rerun()
                    
                    # Step-by-step workflow
                    if st.session_state.workflow_mode == "step_by_step" and st.session_state.extracted_job_data:
                        st.divider()
                        st.subheader("Step-by-Step Application Review")
                        
                        # CV Generation
                        st.markdown("#### Customize Your CV")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Generate CV Preview", key="gen_cv_preview"):
                                try:
                                    with st.spinner("Generating CV preview..."):
                                        preview = generate_custom_cv(
                                            st.session_state.user_dir,
                                            st.session_state.extracted_job_data,
                                            action="preview"
                                        )
                                        st.session_state.cv_preview = preview
                                        st.rerun()
                                except Exception as e:
                                    st.error(f"CV generation error: {str(e)}")
                        
                        with col2:
                            if st.button("Save CV as PDF", key="save_cv_pdf"):
                                try:
                                    with st.spinner("Saving CV..."):
                                        result = generate_custom_cv(
                                            st.session_state.user_dir,
                                            st.session_state.extracted_job_data,
                                            action="save"
                                        )
                                        st.session_state.selected_cv_path = Path(st.session_state.user_dir) / "generated_cv.pdf"
                                        st.success(result)
                                except Exception as e:
                                    st.error(f"Error saving PDF: {str(e)}")
                        
                        # CV Preview and Editing
                        if st.session_state.cv_preview:
                            st.text_area("CV Preview:", 
                                         value=st.session_state.cv_preview, 
                                         height=400,
                                         key="cv_preview_area")
                            
                            st.text_area(
                                "Edit instructions:", 
                                value=st.session_state.edit_instructions_cv,
                                height=100,
                                key="edit_instructions_cv_area",
                                placeholder="How would you like to modify your CV? (e.g., 'Make more concise', 'Highlight Python skills')"
                            )
                            
                            col_edit1, col_edit2 = st.columns(2)
                            with col_edit1:
                                if st.button("Apply Edits", key="apply_cv_edits"):
                                    try:
                                        with st.spinner("Applying edits..."):
                                            edited_cv = generate_custom_cv(
                                                st.session_state.user_dir,
                                                st.session_state.extracted_job_data,
                                                action="edit",
                                                edit_instructions=st.session_state.edit_instructions_cv
                                            )
                                            st.session_state.cv_preview = edited_cv
                                            st.rerun()
                                    except Exception as e:
                                        st.error(f"Error editing CV: {str(e)}")
                            
                            with col_edit2:
                                if st.button("Clear Edits", key="clear_cv_edits"):
                                    st.session_state.edit_instructions_cv = ""
                                    st.success("Edit instructions cleared")
                        
                        # Cover Letter Generation
                        st.divider()
                        st.markdown("#### Customize Cover Letter")
                        
                        if st.button("Generate Cover Letter", key="gen_cover_letter"):
                            try:
                                with st.spinner("Generating cover letter..."):
                                    cover_letter_text = generate_cover_letter(
                                        st.session_state.user_dir,
                                        st.session_state.extracted_job_data,
                                        st.session_state.llm,
                                        action="preview"
                                    )
                                    st.session_state.cover_letter_text = cover_letter_text
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Cover letter error: {str(e)}")
                        
                        # Cover Letter Editing
                        if st.session_state.cover_letter_text:
                            st.text_area(
                                "Cover Letter:", 
                                value=st.session_state.cover_letter_text, 
                                height=300,
                                key="cover_letter_content_area"
                            )
                            
                            st.text_area(
                                "Edit instructions:", 
                                value=st.session_state.edit_instructions_letter,
                                height=100,
                                key="cover_letter_instructions_area",
                                placeholder="How would you like to modify your cover letter?"
                            )
                            
                            col_edit1, col_edit2 = st.columns(2)
                            with col_edit1:
                                if st.button("Apply AI Edits", key="apply_ai_edits_letter"):
                                    try:
                                        with st.spinner("Applying edits..."):
                                            edited_letter = generate_cover_letter(
                                                st.session_state.user_dir,
                                                st.session_state.extracted_job_data,
                                                st.session_state.llm,
                                                action="edit",
                                                edit_instructions=st.session_state.edit_instructions_letter
                                            )
                                            st.session_state.cover_letter_text = edited_letter
                                            st.rerun()
                                    except Exception as e:
                                        st.error(f"AI editing error: {str(e)}")
                            
                            with col_edit2:
                                if st.button("Clear Instructions", key="clear_letter_instructions"):
                                    st.session_state.edit_instructions_letter = ""
                                    st.success("Edit instructions cleared")
                        
                        # Final Send
                        st.divider()
                        st.subheader("Ready to Send")
                        if st.button("📤 Send Application", key="send_application", use_container_width=True):
                            try:
                                # Save cover letter to file
                                cover_letter_path = Path(st.session_state.user_dir) / "latest_cover_letter.txt"
                                with open(cover_letter_path, "w") as f:
                                    f.write(st.session_state.cover_letter_text)
                                
                                # Send email
                                send_email_with_cv(
                                    st.session_state.user_dir,
                                    st.session_state.extracted_job_data,
                                    cv_path=str(st.session_state.selected_cv_path)
                                )
                                
                                st.success("Application sent successfully!")
                            except Exception as e:
                                st.error(f"Email sending error: {str(e)}")
                else:
                    # CV selected from uploaded CVs
                    if st.button("🚀 Quick Send Application", key="quick_send_existing", 
                                help="Send application without review",
                                use_container_width=True):
                        with st.spinner("Processing quick send..."):
                            if quick_send_application():
                                st.success("Application sent successfully!")
            else:
                # Excel batch processing
                if st.session_state.excel_jobs:
                    st.info(f"Ready to process {len(st.session_state.excel_jobs)} jobs")
                    
                    if st.button("🚀 Send All Applications", key="send_all_jobs", 
                                help="Send applications for all jobs in Excel",
                                use_container_width=True):
                        with st.spinner(f"Processing {len(st.session_state.excel_jobs)} applications..."):
                            success_count, failure_count = process_excel_batch()
                            
                            if failure_count == 0:
                                st.success(f"All {success_count} applications sent successfully!")
                            else:
                                st.warning(f"Completed with {success_count} successes and {failure_count} failures")
                                
                                # Show detailed results without expander
                                st.subheader("Application Results")
                                for result in st.session_state.batch_results:
                                    if result["status"] == "Success":
                                        st.success(f"Job {result['job_index']+1}: ✅ Success")
                                    else:
                                        st.error(f"Job {result['job_index']+1}: ❌ Failed - {result['error']}")
        else:
            st.info("Please enter a job posting or upload an Excel file to proceed")

if __name__ == "__main__":
    main()