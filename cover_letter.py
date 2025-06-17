# cover_letter.py
from langchain.prompts import PromptTemplate
from utils import clean_unicode
from pathlib import Path
import json
from typing import Dict, Literal
import streamlit as st

def generate_cover_letter(
    user_dir: str,
    job_posting_info: Dict,
    llm,
    action: Literal["preview", "edit"] = "preview",
    edit_instructions: str = ""
) -> str:
    profile_path = Path(user_dir) / "profile_data.json"
    if not profile_path.exists():
        raise FileNotFoundError("User profile_data.json not found.")
    
    with open(profile_path, "r") as f:
        user_data = json.load(f)
    
    generated_letter_path = Path(user_dir) / "latest_cover_letter.txt"
    
    if action == "preview":
        prompt = PromptTemplate(
            input_variables=["user_data", "job_posting_info"],
            template="""
You are an expert in writing tailored, concise, and professional cover letters for job applications.

Use the following data to generate a compelling, personalized cover letter.

---

👤 **Candidate Profile**
{user_data}

🧾 **Job Posting**
{job_posting_info}

---

✍️ **Instructions**:
- Use standard business letter format: Address, Greeting, 1-2 short paragraphs, and Signature.
- Keep it under 350 words.
- Address the hiring manager if possible ("Dear Hiring Manager" if not known).
- Mention 2–3 core skills or experiences that match the job.
- End with a polite call to action.
- Use clear, professional language.
always use clients credentials such as name email and phone number in the cover letter.
 strictly donot include any details  which is not provided to u  such as address or city e.t.c unless provided
 also donot need to include job posting source if not provided 
 dont include any information thats not provided in the user profile or job posting.
- Avoid generic phrases like "I am writing to apply for the position of...".
- Focus on how your skills can benefit the company.
- Use a friendly yet professional tone.
- Ensure the letter is well-structured and easy to read.
if date is not provided in the user profile, use today's date.
- If the job posting mentions a specific project or goal, reference it in your letter.

Now generate the cover letter with no preamble or note strictly .
"""
        )
        
        chain = prompt | llm
        result = chain.invoke({
            "user_data": json.dumps(user_data, indent=2),
            "job_posting_info": json.dumps(job_posting_info, indent=2),
        })
        
        letter_text = clean_unicode(result.content.strip())
        generated_letter_path.write_text(letter_text, encoding="utf-8")
        return letter_text
    
    elif action == "edit":
        if not generated_letter_path.exists():
            raise FileNotFoundError("Preview the letter first before editing.")
        
        previous_letter = generated_letter_path.read_text(encoding="utf-8")
        
        edit_prompt = PromptTemplate(
            input_variables=["previous_letter", "edit_instructions"],
            template="""
You are a professional writing assistant.

Here's the current cover letter:
---
{previous_letter}
---

Apply the following editing instructions:
---
{edit_instructions}
---

Return the updated cover letter.but make sure there is no premable or note included in the response.
"""
        )
        chain = edit_prompt | llm
        result = chain.invoke({
            "previous_letter": previous_letter,
            "edit_instructions": edit_instructions,
        })
        
        letter_text = clean_unicode(result.content.strip())
        generated_letter_path.write_text(letter_text, encoding="utf-8")
        return letter_text
    
    else:
        raise ValueError("Invalid action. Use 'preview' or 'edit'.")