from langchain_core.prompts import PromptTemplate
import re
import json  # Add this import
from langchain_core.output_parsers import JsonOutputParser
from langchain_groq import ChatGroq
import os


def get_llm():
    """Create LLM instance with JSON output format"""
    if "GROQ_API_KEY" not in os.environ:
        return None
    
    return ChatGroq(
        model="deepseek-r1-distill-llama-70b",
        temperature=0,
        max_tokens=None,
        response_format={"type": "json_object"},
        timeout=None,
        
        max_retries=2
    )
    

def extract_job_and_contact_info(job_paragraph: str) -> dict:  # Changed return type to dict
    llm = get_llm()
    if llm is None:
        raise ValueError("LLM not configured. Please set up your environment variables.")
        
    prompt_extract = PromptTemplate.from_template("""
### JOB POSTING ANALYSIS TASK
Analyze this job posting and extract structured information:

{job_paragraph}

### OUTPUT REQUIREMENTS:
- Return JSON with two root keys: "employer_info" and "position_details"
- Output ONLY valid JSON - no commentary
- Include fields ONLY when explicitly mentioned
- Maintain original wording for values
- Handle all job types (medical, tech, education, etc.)
if 2 or more email are provided thn use the first one 

1. EMPLOYER_INFO (hiring organization/individual):
{{
    "full_name": "(if individual)",
    "organization": "(company/institution name)",
    "department": "(specific division/team)",
    "industry": "(medical, tech, education, etc.)",
    "contact": {{
        "email": "(preferred,if 2 or more email are provided thn use the first one )",
        "phone": "(if provided)",
        "website": "(career portal/LinkedIn)"
    }},
    "location": {{
        "city": "(primary workplace)",
        "country": "(if mentioned)",
        "remote_options": "(hybrid/remote flags)"
    }},
    "organization_type": "(hospital, startup, university, etc.)",
    "key_attributes": ["list", "of", "notable", "features"]
}}

2. POSITION_DETAILS (job characteristics):
{{
    "title": "(official job name)",
    "type": "(full-time, contract, internship)",
    "category": "(clinical, engineering, research, etc.)",
    "level": "(junior, senior, principal)",
    "salary": {{
        "range": "(numbers or description)",
        "currency": "(if specified)",
        "bonuses": "(signing/performance bonuses)"
    }},
    "requirements": {{
        "education": "(degrees/certifications)",
        "experience": "(years/type)",
        "skills": ["technical", "and", "soft", "skills"],
        "licenses": "(industry-specific certifications)"
    }},
    "responsibilities": ["list", "of", "core", "duties"],
    "benefits": ["healthcare", "retirement", "perks"],
    "deadlines": {{
        "application": "(DD/MM/YYYY or relative)",
        "start_date": "(if specified)"
    }},
    "travel_requirements": "(percentage or description)",
    "reporting_structure": "(supervisory relationships)",
    "performance_metrics": "(KPIs/success measures)"
}}

### OUTPUT ONLY VALID JSON WITH NO MARKDOWN FORMATTING
""")
    chain_extract = prompt_extract | llm
    response = chain_extract.invoke({'job_paragraph': job_paragraph})
    
    # Clean Markdown formatting from response
    content = response.content.strip()
    
    # Handle Markdown code blocks
    if content.startswith('```json'):
        content = content[7:].strip()  # Remove starting ```json
    elif content.startswith('```'):
        content = content[3:].strip()  # Remove starting ```
    
    # Remove trailing ```
    if content.endswith('```'):
        content = content[:-3].strip()
    
    # Parse JSON and return as dictionary
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON: {e}\nContent: {content}")


def validate_or_ask_email(extracted_json: dict) -> str:
    # Check nested contact info first, then fallback to manual input
    email = extracted_json.get("employer_info", {}).get("contact", {}).get("email")
    
    if email and re.match(r"^[\w\.-]+@[a-zA-Z\d\.-]+\.[a-zA-Z]{2,}$", email):
        return email
    
    # If no valid email found, prompt user
    print("\n✉️ No valid email found in job posting. Please provide one:")
    while True:
        manual_email = input("Contact email: ").strip()
        if re.match(r"^[\w\.-]+@[a-zA-Z\d\.-]+\.[a-zA-Z]{2,}$", manual_email):
            return manual_email
        print("Invalid format. Please enter a valid email address (e.g. name@company.com)")