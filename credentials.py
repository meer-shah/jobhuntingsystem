import os
import re
import json
import streamlit as st
import shutil
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
        raise RuntimeError(f"Directory creation failed: {str(e)}") from e
    
    credentials_path = user_dir / "credentials.json"
    credentials = {
        "USER_EMAIL": email,
        "GMAIL_APP_PASSWORD": app_password
    }
    
    try:
        with open(credentials_path, "w") as f:
            json.dump(credentials, f, indent=2)
    except IOError as e:
        raise RuntimeError(f"File writing failed: {str(e)}") from e
    
    return str(user_dir)

def update_user_credentials(old_user_dir: str, new_email: str, new_password: str) -> str:
    """
    Update user credentials and move directory if email changed
    Returns the new user directory path
    """
    if not re.match(EMAIL_REGEX, new_email):
        raise ValueError("Invalid email format")
    
    old_dir_path = Path(old_user_dir)
    if not old_dir_path.exists():
        raise RuntimeError("Current user directory not found")
    
    # Get old credentials to compare
    old_creds_path = old_dir_path / "credentials.json"
    if not old_creds_path.exists():
        raise RuntimeError("Current credentials file not found")
    
    try:
        with open(old_creds_path) as f:
            old_credentials = json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        raise RuntimeError(f"Error reading old credentials: {str(e)}")
    
    old_email = old_credentials.get("USER_EMAIL", "")
    
    # Check if email is changing
    email_changed = old_email.lower() != new_email.lower()
    
    if email_changed:
        # Create new directory path
        new_safe_email = sanitize_email(new_email)
        new_dir_path = Path(STORAGE_DIR) / new_safe_email
        
        # Check if new directory already exists
        if new_dir_path.exists():
            raise RuntimeError(f"A profile with email {new_email} already exists")
        
        try:
            # Move the entire directory to new location
            shutil.move(str(old_dir_path), str(new_dir_path))
            user_dir_path = new_dir_path
        except (OSError, shutil.Error) as e:
            raise RuntimeError(f"Failed to move user directory: {str(e)}")
    else:
        # Email not changed, keep same directory
        user_dir_path = old_dir_path
    
    # Update credentials file with new information
    new_credentials = {
        "USER_EMAIL": new_email,
        "GMAIL_APP_PASSWORD": new_password
    }
    
    credentials_path = user_dir_path / "credentials.json"
    try:
        with open(credentials_path, "w") as f:
            json.dump(new_credentials, f, indent=2)
    except IOError as e:
        # If we moved the directory but failed to update credentials, try to move back
        if email_changed:
            try:
                shutil.move(str(user_dir_path), str(old_dir_path))
            except:
                pass  # Best effort to restore
        raise RuntimeError(f"Failed to update credentials: {str(e)}")
    
    return str(user_dir_path)

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