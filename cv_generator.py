from langchain.prompts import PromptTemplate
from fpdf import FPDF
from pathlib import Path
import json
from typing import Dict, Literal, List, Optional
import re
import os
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_groq import ChatGroq

# Define Pydantic model for structured CV output
class StructuredCV(BaseModel):
    name: str = Field(..., description="Full name of the candidate")
    contact: Dict[str, str] = Field(..., description="Contact information including email, phone, etc.")
    summary: Optional[str] = Field(None, description="Professional summary/profile")
    experience: List[Dict] = Field(..., description="List of work experiences")
    education: List[Dict] = Field(..., description="List of education entries")
    skills: Dict[str, List[str]] = Field(..., description="Categorized skills dictionary")
    projects: List[Dict] = Field(..., description="List of projects")
    certifications: List[Dict] = Field([], description="List of certifications")
    industry_preferences: List[str] = Field([], description="Industry preferences")

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

def clean_unicode(text: str) -> str:
    """Clean problematic unicode characters without altering text structure"""
    replacements = {
        '\u2013': '-',  # en dash
        '\u2014': '-',  # em dash
        '\u2018': "'",  # left single quote
        '\u2019': "'",  # right single quote
        '\u201c': '"',  # left double quote
        '\u201d': '"',  # right double quote
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    return text

class FormattedCVPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        self.set_margins(20, 20, 20)
        self.link_color = (0, 0, 255)  # Blue color for hyperlinks
    
    def header(self):
        pass
    
    def footer(self):
        pass
    
    def add_name_header(self, name: str):
        self.set_font('Arial', 'B', 22)
        clean_name = clean_unicode(name)
        self.cell(0, 12, clean_name, ln=True, align='L')
        self.ln(3)
    
    def add_contact_info(self, email: str, phone: str, linkedin: str = "", github: str = ""):
        self.set_font('Arial', '', 10)
        self.set_text_color(0)  # Start with black color
        current_x = 20  # Start at left margin
        
        # Build the contact info string
        contact_parts = []
        if email:
            contact_parts.append(f"Email: {clean_unicode(email)}")
        if phone:
            contact_parts.append(f"Phone: {clean_unicode(phone)}")
        
        # Create the text part first
        if contact_parts:
            text_part = " | ".join(contact_parts)
            self.set_x(current_x)
            self.cell(self.get_string_width(text_part), 6, text_part, ln=0)
            current_x += self.get_string_width(text_part)
        
        # Add LinkedIn with separator if needed
        if linkedin:
            if contact_parts:
                self.set_x(current_x)
                self.cell(self.get_string_width(" | "), 6, " | ", ln=0)
                current_x += self.get_string_width(" | ")
            
            self.set_text_color(*self.link_color)  # Blue for hyperlink
            self.set_x(current_x)
            self.cell(self.get_string_width("LinkedIn"), 6, "LinkedIn", link=linkedin, ln=0)
            current_x += self.get_string_width("LinkedIn")
            self.set_text_color(0)  # Reset to black
        
        # Add GitHub with separator if needed
        if github:
            if linkedin or contact_parts:
                self.set_x(current_x)
                self.cell(self.get_string_width(" | "), 6, " | ", ln=0)
                current_x += self.get_string_width(" | ")
            
            self.set_text_color(*self.link_color)  # Blue for hyperlink
            self.set_x(current_x)
            self.cell(self.get_string_width("GitHub"), 6, "GitHub", link=github, ln=0)
            self.set_text_color(0)  # Reset to black
        
        # Move to next line
        self.ln(8)
    def add_section_header(self, title: str):
        self.ln(3)
        self.set_font('Arial', 'B', 14)
        clean_title = clean_unicode(title.upper())
        self.cell(0, 8, clean_title, ln=True)
        self.set_draw_color(68, 68, 68)
        self.set_line_width(0.5)
        self.line(20, self.get_y(), 190, self.get_y())
        self.ln(5)
    
    def add_job_entry(self, title: str, company: str, date: str, description: str, technologies: List[str] = None):
        self.set_font('Arial', 'B', 11)
        clean_title = clean_unicode(title)
        clean_company = clean_unicode(company)
        clean_date = clean_unicode(date)
        
        job_line = f"{clean_title} - {clean_company}"
        self.cell(130, 7, job_line, ln=False)
        self.set_font('Arial', 'I', 10)
        self.cell(0, 7, clean_date, ln=True, align='R')
        self.ln(2)
        
        # Add job description as bullet points
        self.set_font('Arial', '', 10)
        for line in description.split('\n'):
            if line.strip():
                self.add_bullet_point(line.strip())
        
        # Add technologies if available
        if technologies:
            self.set_font('Arial', 'I', 9)
            tech_text = "Technologies: " + ", ".join(technologies)
            self.set_x(28)
            self.cell(0, 5, clean_unicode(tech_text), ln=True)
            self.ln(1)
    
    def add_education_entry(self, degree: str, institution: str, date: str, specialization: Optional[str] = None):
        self.set_font('Arial', 'B', 11)
        clean_degree = clean_unicode(degree)
        clean_institution = clean_unicode(institution)
        clean_date = clean_unicode(date)
        
        education_line = f"{clean_degree} - {clean_institution}"
        self.cell(130, 7, education_line, ln=False)
        self.set_font('Arial', 'I', 10)
        self.cell(0, 7, clean_date, ln=True, align='R')
        self.ln(2)
        
        # Add specialization if available
        if specialization:
            self.set_font('Arial', '', 10)
            self.set_x(28)
            self.cell(0, 5, f"Specialization: {clean_unicode(specialization)}", ln=True)
            self.ln(1)
    
    def add_bullet_point(self, text: str):
        self.set_font('Arial', '', 10)
        clean_text = clean_unicode(text)
        self.cell(8, 5, '-', ln=False)
        self.set_x(28)
        self.multi_cell(0, 5, clean_text)
        self.ln(1)
    
    def add_project_entry(self, title: str, description: str):
        self.set_font('Arial', 'B', 11)
        clean_title = clean_unicode(title)
        self.cell(0, 7, clean_title, ln=True)
        self.ln(1)
        
        self.set_font('Arial', '', 10)
        clean_description = clean_unicode(description)
        self.multi_cell(0, 5, clean_description)
        self.ln(3)
    
    def add_categorized_skills(self, skills: Dict[str, List[str]]):
        """Add categorized skills section"""
        for category, skill_list in skills.items():
            self.set_font('Arial', 'B', 10)
            self.cell(50, 6, f"{category}:", ln=False)
            self.set_font('Arial', '', 10)
            skills_text = clean_unicode(', '.join(skill_list))
            self.multi_cell(0, 6, skills_text)
            self.ln(3)
    
    def add_regular_text(self, text: str):
        self.set_font('Arial', '', 10)
        clean_text = clean_unicode(text)
        self.multi_cell(0, 6, clean_text)
        self.ln(2)
    
    def add_certifications(self, certifications: List[Dict]):
        """Add certifications section with name and issuer on one line"""
        for cert in certifications:
            name = clean_unicode(cert.get('name', ''))
            issuer = clean_unicode(cert.get('issuer', ''))
            url = cert.get('url', '')
            
            # Create combined text with name and issuer
            combined_text = name
            if issuer:
                combined_text += f" ({issuer})"
            
            # Add hyperlink if URL exists
            if url:
                self.set_text_color(*self.link_color)  # Set blue color
                self.set_font('Arial', 'B', 10)
                self.cell(0, 6, combined_text, link=url, ln=True)
                self.set_text_color(0)  # Reset to black
            else:
                self.set_font('Arial', 'B', 10)
                self.cell(0, 6, combined_text, ln=True)
            
            self.ln(2)
def generate_structured_cv(user_data: dict, job_posting_info: dict, llm) -> dict:
    """Generate structured CV using LLM with JSON output"""
    parser = JsonOutputParser(pydantic_object=StructuredCV)
    
    prompt = PromptTemplate(
        template="""
Create a professional ATS-friendly CV in JSON format using the candidate's information tailored to this job. 
Follow this structure exactly:

{format_instructions}

Candidate Information:
{user_data}

Job Posting Details:
{job_posting_info}
note:8 strictly dont add redundant experiences ai intern or ai enginieer intern will be graded as same as ai engineer if the institution name is same  
also mern stack and full stack stack will be graded as same if the institution name is same so add one of each only
Rules:
1. Only include sections with  relevat content
2. Keep descriptions concise and job-relevant
3. Use reverse chronological order
4. Focus on quantifiable achievements
5. Include job-relevant keywords
6. Format dates as "YYYY-YYYY" or "YYYY-MM"
7. For experience entries only relevant experiences max 3:
   - Include "title", "company", "dates", "description", and "technologies"
   - The "description" must be a list of bullet point strings
   - Each bullet point should be a complete sentence ending with a period
   - Example: ["Developed machine learning models using PyTorch.", "Optimized algorithms for 30% faster inference."]
8. For education:
   - Include "degree", "institution", "dates", and "specialization" if available
9. For projects include 3 projects at max always use one project in detail only other project as supporing if relevant :
   - Include "title" and "in project description make sure u hihlight what you did and needed in the job  posting"
   - The "description" must be a list of bullet point strings
   - Each bullet point should be a complete sentence ending with a period
   - Example: ["Built a RAG pipeline using LangChain and ChromaDB.", "Integrated IBM Watsonx.ai for summarization tasks."]
10. For certifications only relevant:
   - Include "name" and "issuer" and  most importantly "url" (if available)
11. For skills:
   - Categorize skills into relevant groups (e.g., "AI & Data Science", "Full Stack Development", "Tools/Platforms")
   - Use job-relevant categories based on the position
""",
        input_variables=["user_data", "job_posting_info"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    
    chain = prompt | llm | parser
    return chain.invoke({
        "user_data": json.dumps(user_data, indent=2),
        "job_posting_info": json.dumps(job_posting_info, indent=2)
    })

def structured_cv_to_text(structured_cv: dict) -> str:
    """Convert structured CV to ATS-friendly text format"""
    sections = []
    
    # Header
    name = structured_cv.get('name', '')
    contact_info = structured_cv.get('contact', {})
    
    header = f"{name}\n\n"
    contact_parts = []
    if contact_info.get('email'): 
        contact_parts.append(f"Email: {contact_info['email']}")
    if contact_info.get('phone'): 
        contact_parts.append(f"Phone: {contact_info['phone']}")
    if contact_info.get('linkedin'): 
        contact_parts.append(f"LinkedIn: {contact_info['linkedin']}")
    if contact_info.get('github'): 
        contact_parts.append(f"GitHub: {contact_info['github']}")
    
    if contact_parts:
        header += " | ".join(contact_parts) + "\n\n"
    
    sections.append(header.strip())
    
    # Professional Summary
    if structured_cv.get('summary'):
        sections.append(f"ABOUT ME\n{structured_cv['summary']}\n")
    
    # Experience
    if structured_cv.get('experience'):
        exp_section = "EXPERIENCE\n"
        for job in structured_cv['experience']:
            exp_section += f"{job.get('title', '')} - {job.get('company', '')} ({job.get('dates', '')})\n"
            
            # Process description as bullet points with proper sentence structure
            description = job.get('description', '')
            if isinstance(description, list):
                for line in description:
                    # Ensure proper sentence structure
                    line = line.strip()
                    if line and not line.endswith('.'):
                        line += '.'
                    exp_section += f"- {line}\n"
            elif isinstance(description, str):
                # Split into sentences and format as bullet points
                for line in description.split('\n'):
                    line = line.strip()
                    if line:
                        if not line.endswith('.'):
                            line += '.'
                        exp_section += f"- {line}\n"
            
            # Add technologies if available
            if job.get('technologies'):
                techs = ", ".join(job['technologies'])
                exp_section += f"Technologies: {techs}\n"
            
            exp_section += "\n"
        sections.append(exp_section.strip())
    
    # Education
    if structured_cv.get('education'):
        edu_section = "EDUCATION\n"
        for edu in structured_cv['education']:
            edu_line = f"{edu.get('degree', '')} - {edu.get('institution', '')} ({edu.get('dates', '')})"
            if edu.get('specialization'):
                edu_line += f" | Specialization: {edu['specialization']}"
            edu_section += edu_line + "\n\n"
        sections.append(edu_section.strip())
    
    # Skills - categorized
    if structured_cv.get('skills'):
        skills_section = "SKILLS\n"
        for category, skill_list in structured_cv['skills'].items():
            skills_section += f"{category}: {', '.join(skill_list)}\n"
        sections.append(skills_section.strip())
    
    # Projects
    if structured_cv.get('projects'):
        proj_section = "PROJECTS\n"
        for project in structured_cv['projects']:
            proj_section += f"{project.get('title', '')}\n"
            
            # Process description with proper sentence structure
            description = project.get('description', '')
            if isinstance(description, list):
                for line in description:
                    # Ensure proper sentence structure
                    line = line.strip()
                    if line and not line.endswith('.'):
                        line += '.'
                    proj_section += f"- {line}\n"
            elif isinstance(description, str):
                # Split into sentences and format as bullet points
                for line in description.split('\n'):
                    line = line.strip()
                    if line:
                        if not line.endswith('.'):
                            line += '.'
                        proj_section += f"- {line}\n"
            
            proj_section += "\n"
        sections.append(proj_section.strip())
    
    # Certifications
    if structured_cv.get('certifications'):
        cert_section = "CERTIFICATIONS\n"
        for cert in structured_cv['certifications']:
            cert_text = f"{cert.get('name', '')}"
            if cert.get('date'):
                cert_text += f" ({cert.get('date')})"
            if not cert_text.endswith('.'):
                cert_text += '.'
            cert_section += f"- {cert_text}\n"
        sections.append(cert_section.strip())
    
    # Industry Preferences
    if structured_cv.get('industry_preferences'):
        industry_section = "INDUSTRY PREFERENCES\n"
        preferences = structured_cv['industry_preferences']
        # Add period at the end of each preference
        preferences = [pref + '.' if not pref.endswith('.') else pref for pref in preferences]
        industry_section += "\n".join([f"- {pref}" for pref in preferences])
        sections.append(industry_section)
    
    return "\n\n".join(sections)
def create_pdf_from_structured_cv(structured_cv: dict, output_path: str):
    """Create PDF directly from structured CV data with hyperlinks and section cohesion"""
    pdf = FormattedCVPDF()
    pdf.add_page()
    
    # Add name header
    name = structured_cv.get('name', '') or "CV"
    pdf.add_name_header(name)
    
    # Add contact info
    contact_info = structured_cv.get('contact', {})
    email = contact_info.get('email', '')
    phone = contact_info.get('phone', '')
    linkedin = contact_info.get('linkedin', '')
    github = contact_info.get('github', '')
    pdf.add_contact_info(email, phone, linkedin, github)
    
    # Keep track of section heights to prevent splitting
    section_heights = {}
    
    # Professional Summary
    if structured_cv.get('summary'):
        # Add page break if needed
        if pdf.get_y() > 250:  # 250mm from top (A4 height is 297mm)
            pdf.add_page()
        pdf.add_section_header("Professional Profile")
        pdf.add_regular_text(structured_cv['summary'])
    
    # Experience
    if structured_cv.get('experience'):
        # Add page break if needed
        if pdf.get_y() > 220:  # More space needed for experience section
            pdf.add_page()
        pdf.add_section_header("Experience")
        for job in structured_cv['experience']:
            description = job.get('description', '')
            if isinstance(description, list):
                description = "\n".join(description)
            
            pdf.add_job_entry(
                title=job.get('title', ''),
                company=job.get('company', ''),
                date=job.get('dates', ''),
                description=description,
                technologies=job.get('technologies', [])
            )
    
    # Skills - categorized
    if structured_cv.get('skills'):
        # Add page break if needed
        if pdf.get_y() > 250:
            pdf.add_page()
        pdf.add_section_header("Skills")
        pdf.add_categorized_skills(structured_cv['skills'])
    
    # Education
    if structured_cv.get('education'):
        # Add page break if needed
        if pdf.get_y() > 240:
            pdf.add_page()
        pdf.add_section_header("Education")
        for edu in structured_cv['education']:
            pdf.add_education_entry(
                degree=edu.get('degree', ''),
                institution=edu.get('institution', ''),
                date=edu.get('dates', ''),
                specialization=edu.get('specialization', '')
            )
    
    # Certifications with hyperlinks
    if structured_cv.get('certifications'):
        # Add page break if needed
        if pdf.get_y() > 250:
            pdf.add_page()
        pdf.add_section_header("Certifications")
        pdf.add_certifications(structured_cv['certifications'])
    
    # Projects
    if structured_cv.get('projects'):
        # Add page break if needed
        if pdf.get_y() > 220:  # More space needed for projects section
            pdf.add_page()
        pdf.add_section_header("Projects")
        for project in structured_cv['projects']:
            description = project.get('description', '')
            if isinstance(description, list):
                description = "\n".join(description)
            
            pdf.add_project_entry(
                title=project.get('title', ''),
                description=description
            )
    
    # Industry Preferences
    if structured_cv.get('industry_preferences'):
        # Add page break if needed
        if pdf.get_y() > 260:
            pdf.add_page()
        pdf.add_section_header("Industry Preferences")
        pdf.add_regular_text(", ".join(structured_cv['industry_preferences']))
    
    # Save PDF
    try:
        pdf.output(output_path)
        return f"PDF successfully saved to: {output_path}"
    except Exception as e:
        return f"Error saving PDF: {str(e)}"
def generate_custom_cv(
    user_dir: str,
    job_posting_info: Dict,
    action: Literal["preview", "save", "edit"] = "preview",
    edit_instructions: str = ""
) -> str:
    # Load user profile
    profile_path = Path(user_dir) / "profile_data.json"
    if not profile_path.exists():
        raise FileNotFoundError("User profile_data.json not found.")
    
    with open(profile_path, "r") as f:
        user_data = json.load(f)
    
    generated_cv_path = Path(user_dir) / "latest_cv.txt"
    structured_cv_path = Path(user_dir) / "structured_cv.json"
    
    # Get LLM instance
    llm = get_llm()
    if not llm:
        return "GROQ_API_KEY not set. LLM functionality disabled."
    
    if action == "preview":
        # Generate structured CV using LLM
        try:
            structured_cv = generate_structured_cv(user_data, job_posting_info, llm)
            
            # Save structured CV for later use
            with open(structured_cv_path, 'w', encoding='utf-8') as f:
                json.dump(structured_cv, f, indent=2)
            
            # Convert to text format
            cv_text = structured_cv_to_text(structured_cv)
            cv_text = clean_unicode(cv_text)
            
            # Save text CV
            with open(generated_cv_path, 'w', encoding='utf-8') as f:
                f.write(cv_text)
            
            return cv_text
        except Exception as e:
            return f"Error generating CV: {str(e)}"
    
    elif action == "edit":
        if not generated_cv_path.exists() or not structured_cv_path.exists():
            raise FileNotFoundError("Preview the CV first before editing.")
        
        try:
            # Load existing structured CV
            with open(structured_cv_path, 'r', encoding='utf-8') as f:
                structured_cv = json.load(f)
            
            # Edit prompt
            parser = JsonOutputParser(pydantic_object=StructuredCV)
            edit_prompt = PromptTemplate(
                template="""
Edit the following structured CV according to the instructions:

Current CV (JSON):
{structured_cv}

Edit Instructions:
{edit_instructions}

Candidate Info:
{user_data}

Job Posting:
{job_posting_info}

Revise the CV while maintaining:
1. Professional structure
2. ATS-friendly formatting
3. Concise bullet points
4. Reverse chronological order
5. Job-relevant keywords
6. Categorized skills format

Output ONLY the revised JSON without any additional text.
{format_instructions}
""",
                input_variables=["structured_cv", "edit_instructions", "user_data", "job_posting_info"],
                partial_variables={"format_instructions": parser.get_format_instructions()}
            )
            
            chain = edit_prompt | llm | parser
            edited_cv = chain.invoke({
                "structured_cv": json.dumps(structured_cv, indent=2),
                "edit_instructions": edit_instructions,
                "user_data": json.dumps(user_data, indent=2),
                "job_posting_info": json.dumps(job_posting_info, indent=2),
            })
            
            # Save updated structured CV
            with open(structured_cv_path, 'w', encoding='utf-8') as f:
                json.dump(edited_cv, f, indent=2)
            
            # Convert to text format
            cv_text = structured_cv_to_text(edited_cv)
            cv_text = clean_unicode(cv_text)
            
            # Save text CV (overwrite existing)
            with open(generated_cv_path, 'w', encoding='utf-8') as f:
                f.write(cv_text)
            
            return cv_text
        except Exception as e:
            return f"Error editing CV: {str(e)}"
    
    elif action == "save":
        if not structured_cv_path.exists():
            raise FileNotFoundError("Preview the CV first before saving.")
        
        try:
            # Load structured CV
            with open(structured_cv_path, 'r', encoding='utf-8') as f:
                structured_cv = json.load(f)
            
            # Generate PDF
            output_path = Path(user_dir) / "generated_cv.pdf"
            return create_pdf_from_structured_cv(structured_cv, str(output_path))
        except Exception as e:
            return f"Error saving PDF: {str(e)}"
    
    else:
        raise ValueError("Invalid action. Use 'preview', 'edit', or 'save'.")