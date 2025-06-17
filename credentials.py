import os
import re
import json
import streamlit as st
from pathlib import Path

STORAGE_DIR = "cv_storage"
EMAIL_REGEX = r"^[\w\.-]+@[a-zA-Z\d\.-]+\.[a-zA-Z]{2,}$"

def sanitize_email(email: str) -> str:
    return re.sub(r"[^\w\.-]", "_", email.lower())

def create_user_profile(email: str, app_password: str) -> str:
    """Create user profile from Streamlit inputs"""
    if not re.match(EMAIL_REGEX, email):
        raise ValueError("Invalid email format")
    
    safe_email = sanitize_email(email)
    user_dir = Path(STORAGE_DIR) / safe_email
    
    # Create directory with robust error handling
    try:
        # Create parent directories if they don't exist
        user_dir.parent.mkdir(parents=True, exist_ok=True)
        # Create the specific user directory
        user_dir.mkdir(exist_ok=True)
    except OSError as e:
        st.error(f"Directory creation failed: {str(e)}")
        raise RuntimeError("Could not create user directory") from e
    
    credentials_path = user_dir / "credentials.json"
    credentials = {
        "USER_EMAIL": email,
        "GMAIL_APP_PASSWORD": app_password
    }
    
    try:
        with open(credentials_path, "w") as f:
            json.dump(credentials, f, indent=2)
    except IOError as e:
        st.error(f"File writing failed: {str(e)}")
        raise RuntimeError("Could not save credentials") from e
    
    return str(user_dir)

def get_user_email() -> tuple[str, str]:
    """
    Loads email from stored credentials.json
    Returns (email, user_dir)
    """
    # Ensure storage directory exists
    storage_path = Path(STORAGE_DIR)
    if not storage_path.exists():
        storage_path.mkdir(parents=True, exist_ok=True)
    
    for user_folder in storage_path.iterdir():
        if user_folder.is_dir():
            credentials_path = user_folder / "credentials.json"
            if credentials_path.exists():
                try:
                    with open(credentials_path) as f:
                        credentials = json.load(f)
                        user_email = credentials.get("USER_EMAIL")
                        if user_email:
                            return user_email, str(user_folder)
                except (IOError, json.JSONDecodeError):
                    continue  # Skip invalid credentials files
    
    raise RuntimeError("❌ No valid credentials found. Please create a profile.")