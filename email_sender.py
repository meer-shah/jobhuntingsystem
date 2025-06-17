# def send_email_with_cv(user_dir: str, job_data: dict):
#     from pathlib import Path
#     import json
#     from email.message import EmailMessage
#     import smtplib, ssl
#     import logging
#     import re

#     # Set up logging
#     logging.basicConfig(level=logging.INFO)
#     logger = logging.getLogger(__name__)

#     try:
#         user_dir = Path(user_dir)
        
#         # Get recipient email from job data
#         recipient_email = job_data.get("employer_info", {}).get("contact", {}).get("email", "")
#         if not recipient_email:
#             raise ValueError("No email found in job data. Please process a job posting first.")
        
#         # Validate email format
#         if not re.match(r"^[\w\.-]+@[a-zA-Z\d\.-]+\.[a-zA-Z]{2,}$", recipient_email):
#             raise ValueError(f"Invalid email format: {recipient_email}")
        
#         # Load user credentials
#         creds_path = user_dir / "credentials.json"
#         if not creds_path.exists():
#             raise FileNotFoundError("User credentials not found")
            
#         with open(creds_path) as f:
#             creds = json.load(f)
        
#         sender_email = creds["USER_EMAIL"]
#         app_password = creds["GMAIL_APP_PASSWORD"]
        
#         # Get sender's name from profile_data.json if available
#         profile_path = user_dir / "profile_data.json"
#         if profile_path.exists():
#             with open(profile_path) as f:
#                 profile = json.load(f)
#             # Use full name if available, else fallback to email prefix
#             sender_name = profile.get("full_name") or sender_email.split('@')[0].title()
#         else:
#             sender_name = sender_email.split('@')[0].title()  # Fallback to email prefix
        
#         # Get cover letter
#         cover_letter_path = user_dir / "latest_cover_letter.txt"
#         if not cover_letter_path.exists():
#             logger.warning("Cover letter not found, sending without cover letter")
#             cover_letter_text = "Please find my CV attached for your consideration."
#         else:
#             cover_letter_text = cover_letter_path.read_text()
        
#         # Get generated CV
#         pdf_path = user_dir / "generated_cv.pdf"
#         if not pdf_path.exists():
#             raise FileNotFoundError("Generated CV not found. Please generate a CV first.")
        
#         # Compose professional email subject
#         job_title = job_data.get("position_details", {}).get("title", "Position")
#         company = job_data.get("employer_info", {}).get("organization", "")
        
#         # Format subject using sender_name from profile
#         subject = f"Application for {job_title} - {sender_name}"
#         if company:
#             subject = f"Application for {job_title} at {company} - {sender_name}"
        
#         # Compose email
#         msg = EmailMessage()
#         msg["Subject"] = subject
#         msg["From"] = f"{sender_name} <{sender_email}>"  # Optional: Format as "Name <email>"
#         msg["To"] = recipient_email
#         msg.set_content(cover_letter_text)
        
#         # Attach CV with professional filename
#         filename = f"{sender_name.replace(' ', '_')}_CV_{job_title.replace(' ', '_')}.pdf"
#         with open(pdf_path, "rb") as f:
#             pdf_data = f.read()
#         msg.add_attachment(
#             pdf_data, 
#             maintype='application', 
#             subtype='pdf', 
#             filename=filename
#         )
        
#         # Send via Gmail SMTP
#         context = ssl.create_default_context()
#         with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
#             smtp.login(sender_email, app_password)
#             smtp.send_message(msg)
#             logger.info(f"Email sent successfully to {recipient_email}")
            
#     except Exception as e:
#         logger.error(f"Email sending failed: {str(e)}")
#         raise  # Re-raise the exception for Streamlit to handle

# email_sender.py
import re
import json
import logging
import smtplib
import ssl
from pathlib import Path
from email.message import EmailMessage

def send_email_with_cv(user_dir: str, job_data: dict, cv_path: str = None):
    from pathlib import Path
    import json
    from email.message import EmailMessage
    import smtplib, ssl
    import logging
    import re

    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    try:
        user_dir = Path(user_dir)
        
        # Get recipient email from job data
        recipient_email = job_data.get("employer_info", {}).get("contact", {}).get("email", "")
        if not recipient_email:
            raise ValueError("No email found in job data. Please process a job posting first.")
        
        # Validate email format
        if not re.match(r"^[\w\.-]+@[a-zA-Z\d\.-]+\.[a-zA-Z]{2,}$", recipient_email):
            raise ValueError(f"Invalid email format: {recipient_email}")
        
        # Load user credentials
        creds_path = user_dir / "credentials.json"
        if not creds_path.exists():
            raise FileNotFoundError("User credentials not found")
            
        with open(creds_path) as f:
            creds = json.load(f)
        
        sender_email = creds["USER_EMAIL"]
        app_password = creds["GMAIL_APP_PASSWORD"]
        
        # Get sender's name
        sender_name = "Applicant"
        profile_path = user_dir / "profile_data.json"
        if profile_path.exists():
            with open(profile_path) as f:
                profile = json.load(f)
            sender_name = profile.get("full_name", sender_name)
        
        # Get cover letter
        cover_letter_path = user_dir / "latest_cover_letter.txt"
        if not cover_letter_path.exists():
            logger.warning("Cover letter not found, sending without cover letter")
            cover_letter_text = "Please find my CV attached for your consideration."
        else:
            cover_letter_text = cover_letter_path.read_text()
        
        # Get CV path
        if cv_path:
            pdf_path = Path(cv_path)
        else:
            pdf_path = user_dir / "generated_cv.pdf"
        
        if not pdf_path.exists():
            raise FileNotFoundError("Selected CV not found")
        
        # Compose professional email subject
        job_title = job_data.get("position_details", {}).get("title", "Position")
        company = job_data.get("employer_info", {}).get("organization", "")
        
        # Format subject
        subject = f"Application for {job_title} - {sender_name}"
        if company:
            subject = f"Application for {job_title} at {company} - {sender_name}"
        
        # Compose email
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = f"{sender_name} <{sender_email}>"
        msg["To"] = recipient_email
        msg.set_content(cover_letter_text)
        
        # Attach CV with professional filename
        filename = f"{sender_name.replace(' ', '_')}_CV_{job_title.replace(' ', '_')}.pdf"
        with open(pdf_path, "rb") as f:
            pdf_data = f.read()
        msg.add_attachment(
            pdf_data, 
            maintype='application', 
            subtype='pdf', 
            filename=filename
        )
        
        # Send via Gmail SMTP
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
            smtp.login(sender_email, app_password)
            smtp.send_message(msg)
            logger.info(f"Email sent successfully to {recipient_email}")
            
    except Exception as e:
        logger.error(f"Email sending failed: {str(e)}")
        raise