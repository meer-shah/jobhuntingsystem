# llm_config.py
from langchain_groq import ChatGroq
import os

def get_llm():
    if "GROQ_API_KEY" not in os.environ:
        return None
    
    return ChatGroq(
        model="llama3-70b-8192",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2
    )