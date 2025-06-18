import streamlit as st
from credentials import sanitize_email, create_user_profile, update_user_credentials, STORAGE_DIR, EMAIL_REGEX
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
    st.session_state.workflow_mode = None
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
if 'credentials_error' not in st.session_state:
    st.session_state.credentials_error = None
if 'reset_api_key' not in st.session_state:
    st.session_state.reset_api_key = False
if 'logout_requested' not in st.session_state:
    st.session_state.logout_requested = False
if 'show_credential_update' not in st.session_state:
    st.session_state.show_credential_update = False
if 'credential_update_success' not in st.session_state:
    st.session_state.credential_update_success = None

def display_pdf(file_path):
    """Display PDF in Streamlit app"""
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

def reset_session():
    """Reset session state on logout"""
    keys = [
        'user_dir', 'user_email', 'job_text', 'profile_data', 'selected_cv_path',
        'cover_letter_text', 'cv_option', 'cv_preview', 'edit_instructions_cv',
        'edit_instructions_letter', 'workflow_mode', 'extracted_job_data',
        'excel_jobs', 'current_job_index', 'batch_results', 'batch_in_progress',
        'credentials_error', 'reset_api_key', 'show_credential_update', 'credential_update_success'
    ]
    
    for key in keys:
        if key in st.session_state:
            del st.session_state[key]
    
    # Reinitialize necessary states
    st.session_state.user_dir = None
    st.session_state.user_email = None
    st.session_state.job_text = ""
    st.session_state.llm = None
    st.session_state.logout_requested = True

def quick_send_application():
    """Handle the quick send application process for a single job"""
    try:
        # Extract job data
        st.session_state.extracted_job_data = extract_job_and_contact_info(
            st.session_state.job_text
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

def validate_credentials(email, password):
    """Validate user credentials against stored profile"""
    try:
        sanitized = sanitize_email(email)
        user_dir = Path(STORAGE_DIR) / sanitized
        
        if not user_dir.exists():
            return False, "Profile not found"
            
        cred_path = user_dir / "credentials.json"
        if not cred_path.exists():
            return False, "Credentials not found"
            
        with open(cred_path, "r") as f:
            creds = json.load(f)
            
        if creds["USER_EMAIL"] == email and creds["GMAIL_APP_PASSWORD"] == password:
            return True, str(user_dir)
        else:
            return False, "Incorrect password"
            
    except Exception as e:
        return False, f"Validation error: {str(e)}"

def handle_credential_update():
    """Handle the credential update process"""
    st.subheader("🔧 Change Credentials")
    
    # Get current credentials
    current_creds_path = Path(st.session_state.user_dir) / "credentials.json"
    try:
        with open(current_creds_path) as f:
            current_creds = json.load(f)
        current_email = current_creds.get("USER_EMAIL", "")
    except:
        current_email = ""
    
    st.info(f"Current email: {current_email}")
    
    with st.form("credential_update_form"):
        new_email = st.text_input("New email:", value=current_email, key="new_email_input")
        new_password = st.text_input("New email app password:", type="password", key="new_password_input")
        confirm_password = st.text_input("Confirm new password:", type="password", key="confirm_password_input")
        
        col1, col2 = st.columns(2)
        with col1:
            submit_update = st.form_submit_button("Update Credentials", use_container_width=True)
        with col2:
            cancel_update = st.form_submit_button("Cancel", use_container_width=True)
    
    if cancel_update:
        st.session_state.show_credential_update = False
        st.session_state.credential_update_success = None
        st.rerun()
    
    if submit_update:
        # Validation
        if not re.match(EMAIL_REGEX, new_email):
            st.error("Invalid email format. Please use name@domain.com")
            return
        
        if not new_password:
            st.error("Password cannot be empty")
            return
        
        if new_password != confirm_password:
            st.error("Passwords do not match")
            return
        
        # Update credentials
        try:
            with st.spinner("Updating credentials..."):
                new_user_dir = update_user_credentials(
                    st.session_state.user_dir,
                    new_email,
                    new_password
                )
                
                # Update session state
                st.session_state.user_dir = new_user_dir
                st.session_state.user_email = new_email
                st.session_state.show_credential_update = False
                st.session_state.credential_update_success = "Credentials updated successfully!"
                
                st.success("Credentials updated successfully!")
                time.sleep(1)
                st.rerun()
                
        except Exception as e:
            st.error(f"Failed to update credentials: {str(e)}")

def main():
    st.title("AI Job Application Assistant")
    
    # Handle logout if requested - FIXED VERSION
    if st.session_state.logout_requested:
        reset_session()
        st.success("Logged out successfully!")
        time.sleep(1)
        # Don't rerun here, let it fall through to show login page
        st.session_state.logout_requested = False  # Reset the flag
    
    # Handle GROQ API key - MOVE THIS AFTER LOGIN CHECK
    # Only show API key setup if user is logged in
    if st.session_state.user_dir is not None and (st.session_state.llm is None or st.session_state.reset_api_key):
        with st.expander("🔑 Groq API Key Setup", expanded=True):
            if st.session_state.reset_api_key:
                st.warning("Please enter a new Groq API key")
            else:
                st.warning("Please enter your Groq API key to continue")
            
            api_key = st.text_input("Enter your Groq API key:", 
                                   type="password", 
                                   key="api_key_input",
                                   value="")
            
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("Save API Key", key="save_api_key"):
                    if api_key:
                        os.environ["GROQ_API_KEY"] = api_key
                        st.session_state.llm = get_llm()
                        st.session_state.reset_api_key = False
                        st.success("API key saved!")
                        st.rerun()
                    else:
                        st.error("Please enter a valid API key")
            with col2:
                if st.session_state.llm and st.button("Reset API Key", key="reset_api_key"):
                    st.session_state.reset_api_key = True
                    st.session_state.llm = None
                    if "GROQ_API_KEY" in os.environ:
                        del os.environ["GROQ_API_KEY"]
                    st.rerun()
            
            if st.session_state.credentials_error:
                st.error(st.session_state.credentials_error)
            
            return  # Stop here until API key is set
    
    # User authentication and profile management
    if st.session_state.user_dir is None:
        with st.expander("👤 User Authentication", expanded=True):
            st.subheader("Login or Create Profile")
            email = st.text_input("Your email:", key="user_email_input")
            password = st.text_input("Your password:", type="password", key="user_pwd_input")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Login", key="login_button"):
                    if not re.match(EMAIL_REGEX, email):
                        st.session_state.credentials_error = "Invalid email format. Use name@domain.com"
                        st.rerun()
                    elif not password:
                        st.session_state.credentials_error = "Password cannot be empty"
                        st.rerun()
                    else:
                        valid, message = validate_credentials(email, password)
                        if valid:
                            st.session_state.user_email = email
                            st.session_state.user_dir = message
                            st.session_state.credentials_error = None
                            st.success(f"Welcome back, {email}!")
                            st.rerun()
                        else:
                            st.session_state.credentials_error = message
                            st.rerun()
            
            with col2:
                if st.button("Create Profile", key="create_profile_button"):
                    if not re.match(EMAIL_REGEX, email):
                        st.session_state.credentials_error = "Invalid email format. Use name@domain.com"
                        st.rerun()
                    elif not password:
                        st.session_state.credentials_error = "Password cannot be empty"
                        st.rerun()
                    else:
                        try:
                            sanitized = sanitize_email(email)
                            user_dir = Path(STORAGE_DIR) / sanitized
                            
                            if user_dir.exists():
                                st.session_state.credentials_error = "Profile already exists. Please login instead."
                                st.rerun()
                            
                            st.session_state.user_dir = create_user_profile(email, password)
                            st.session_state.user_email = email
                            st.session_state.credentials_error = None
                            st.success(f"Profile created for {email}!")
                            st.rerun()
                        except Exception as e:
                            st.session_state.credentials_error = f"Error creating profile: {str(e)}"
                            st.rerun()
            
            if st.session_state.credentials_error:
                st.error(st.session_state.credentials_error)
            
            st.info("Don't have an account? Click 'Create Profile'. Forgot password? You'll need to create a new profile.")
        return  # Stop here - user needs to login first
    
    # Add header buttons if user is logged in
    if st.session_state.user_email:
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.write(f"👤 Logged in as: **{st.session_state.user_email}**")
        with col2:
            if st.button("🔧 Change Credentials", key="change_credentials_button"):
                st.session_state.show_credential_update = True
                st.session_state.credential_update_success = None
                st.rerun()
        with col3:
            if st.button("Logout", key="logout_button"):
                st.session_state.logout_requested = True
                st.rerun()
        
        # Show success message if credentials were updated
        if st.session_state.credential_update_success:
            st.success(st.session_state.credential_update_success)
            st.session_state.credential_update_success = None
    
    # Handle credential update
    if st.session_state.show_credential_update:
        handle_credential_update()
        return
    
    # Check if API key is needed before showing main content
    if st.session_state.llm is None:
        st.warning("Please set up your Groq API key in the section above to continue.")
        return
    
    # CV Management
    with st.expander("📝 Manage Your CV", expanded=True):
        try:
            run_cv_pipeline_streamlit(st.session_state.user_dir)
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
                                st.session_state.job_text
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
                        
                        # CV Preview and Editing - FIXED VERSION
                        if st.session_state.cv_preview:
                            st.text_area("CV Preview:", 
                                         value=st.session_state.cv_preview, 
                                         height=400,
                                         key="cv_preview_area",
                                         disabled=True)  # Make read-only
                            
                            # Get current edit instructions from input
                            current_edit_cv = st.text_area(
                                "Edit instructions:", 
                                value=st.session_state.edit_instructions_cv,
                                height=100,
                                key="edit_instructions_cv_input",
                                placeholder="How would you like to modify your CV? (e.g., 'Make more concise', 'Highlight Python skills')"
                            )
                            
                            col_edit1, col_edit2 = st.columns(2)
                            with col_edit1:
                                if st.button("Apply Edits", key="apply_cv_edits"):
                                    if not current_edit_cv.strip():
                                        st.warning("Please provide edit instructions first.")
                                    else:
                                        try:
                                            with st.spinner("Applying edits..."):
                                                edited_cv = generate_custom_cv(
                                                    st.session_state.user_dir,
                                                    st.session_state.extracted_job_data,
                                                    action="edit",
                                                    edit_instructions=current_edit_cv
                                                )
                                                st.session_state.cv_preview = edited_cv
                                                st.session_state.edit_instructions_cv = current_edit_cv
                                                st.success("CV updated successfully!")
                                                st.rerun()
                                        except Exception as e:
                                            st.error(f"Error editing CV: {str(e)}")
                            
                            with col_edit2:
                                if st.button("Clear Edits", key="clear_cv_edits"):
                                    st.session_state.edit_instructions_cv = ""
                                    st.success("Edit instructions cleared")
                                    st.rerun()
                        
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
                        
                        # Cover Letter Editing - FIXED VERSION
                        if st.session_state.cover_letter_text:
                            # Editable cover letter text area
                            current_cover_letter = st.text_area(
                                "Cover Letter:", 
                                value=st.session_state.cover_letter_text, 
                                height=300,
                                key="cover_letter_content_input"
                            )
                            
                            # Update session state with manual edits
                            st.session_state.cover_letter_text = current_cover_letter
                            
                            # Edit instructions
                            current_edit_letter = st.text_area(
                                "AI Edit instructions:", 
                                value=st.session_state.edit_instructions_letter,
                                height=100,
                                key="cover_letter_instructions_input",
                                placeholder="How would you like to modify your cover letter? (e.g., 'Make it more enthusiastic', 'Add technical details')"
                            )
                            
                            col_edit1, col_edit2 = st.columns(2)
                            with col_edit1:
                                if st.button("Apply AI Edits", key="apply_ai_edits_letter"):
                                    if not current_edit_letter.strip():
                                        st.warning("Please provide edit instructions first.")
                                    else:
                                        try:
                                            with st.spinner("Applying AI edits..."):
                                                edited_letter = generate_cover_letter(
                                                    st.session_state.user_dir,
                                                    st.session_state.extracted_job_data,
                                                    st.session_state.llm,
                                                    action="edit",
                                                    edit_instructions=current_edit_letter
                                                )
                                                st.session_state.cover_letter_text = edited_letter
                                                st.session_state.edit_instructions_letter = current_edit_letter
                                                st.success("Cover letter updated successfully!")
                                                st.rerun()
                                        except Exception as e:
                                            st.error(f"AI editing error: {str(e)}")
                            
                            with col_edit2:
                                if st.button("Clear Instructions", key="clear_letter_instructions"):
                                    st.session_state.edit_instructions_letter = ""
                                    st.success("Edit instructions cleared")
                                    st.rerun()
                        
                        # Final Send
                        st.divider()
                        st.subheader("Ready to Send")
                        if st.button("📤 Send Application", key="send_application", use_container_width=True):
                            try:
                                # Save cover letter to file
                                cover_letter_path = Path(st.session_state.user_dir) / "latest_cover_letter.txt"
                                with open(cover_letter_path, "w", encoding='utf-8') as f:
                                    f.write(st.session_state.cover_letter_text)
                                
                                # Send email
                                send_email_with_cv(
                                    st.session_state.user_dir,
                                    st.session_state.extracted_job_data,
                                    cv_path=str(st.session_state.selected_cv_path))
                                
                                st.success("Application sent successfully!")
                            except Exception as e:
                                st.error(f"Email sending error: {str(e)}")
                else:
                    # CV selected from uploaded CVs
                    if st.session_state.selected_cv_path:
                        if st.button("🚀 Quick Send Application", key="quick_send_existing", 
                                    help="Send application without review",
                                    use_container_width=True):
                            with st.spinner("Processing quick send..."):
                                if quick_send_application():
                                    st.success("Application sent successfully!")
                    else:
                        st.warning("Please select a CV file first.")
            else:
                # Excel batch processing
                if st.session_state.excel_jobs:
                    st.info(f"Ready to process {len(st.session_state.excel_jobs)} jobs")
                    
                    # Validate CV selection for batch processing
                    cv_ready = False
                    if st.session_state.cv_option == "Generate New CV":
                        cv_ready = True
                    elif st.session_state.cv_option == "Select from Uploaded CVs" and st.session_state.selected_cv_path:
                        cv_ready = True
                    
                    if cv_ready:
                        if st.button("🚀 Send All Applications", key="send_all_jobs", 
                                    help="Send applications for all jobs in Excel",
                                    use_container_width=True):
                            with st.spinner(f"Processing {len(st.session_state.excel_jobs)} applications..."):
                                success_count, failure_count = process_excel_batch()
                                
                                if failure_count == 0:
                                    st.success(f"All {success_count} applications sent successfully!")
                                else:
                                    st.warning(f"Completed with {success_count} successes and {failure_count} failures")
                                    
                                    # Show detailed results
                                    st.subheader("Application Results")
                                    for result in st.session_state.batch_results:
                                        if result["status"] == "Success":
                                            st.success(f"Job {result['job_index']+1}: ✅ Success")
                                        else:
                                            st.error(f"Job {result['job_index']+1}: ❌ Failed - {result['error']}")
                    else:
                        st.warning("Please select a CV file for batch processing.")
        else:
            st.info("Please enter a job posting or upload an Excel file to proceed")
if __name__ == "__main__":
    main()