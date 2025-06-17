# # cv_extractor.py
# import json
# import os
# import re
# import datetime
# from pathlib import Path
# from typing import Dict, List, Optional
# import streamlit as st
# from langchain_core.output_parsers import JsonOutputParser
# from langchain.prompts import PromptTemplate
# from langchain_groq import ChatGroq
# from langchain_community.document_loaders import PyPDFLoader, UnstructuredWordDocumentLoader
# from pydantic import BaseModel, Field

# # Define ProfessionalProfile model
# class ProfessionalProfile(BaseModel):
#     full_name: str = Field(..., description="Full legal name")
#     contact_email: str = Field(..., description="Primary contact email")
#     phone: Optional[str] = Field(None, description="Contact phone number")
#     summary: Optional[str] = Field(None, description="Professional summary")
#     education: List[Dict] = Field(default_factory=list, description="List of educational achievements")
#     experience: List[Dict] = Field(default_factory=list, description="Work history")
#     technical_skills: List[str] = Field(default_factory=list, description="Technical skills")
#     certifications: List[str] = Field(default_factory=list, description="Professional certifications")
#     projects: List[Dict] = Field(default_factory=list, description="Notable projects")
#     industry_preferences: List[str] = Field(default_factory=list, description="Preferred industries")

# def create_parser():
#     return JsonOutputParser(pydantic_object=ProfessionalProfile)

# def create_prompt(parser):
#     return PromptTemplate(
#         template="""**Professional Profile Analysis Task**
# Act as an expert career analyst with deep knowledge across industries (tech, healthcare, finance, engineering). 
# Extract structured information while identifying transferable skills and cross-domain competencies.
# "Please extract the following fields from the CV and return them in JSON format without any preamble: ..."

# **Fields to Extract:**
# - full_name
# - contact_email
# - phone
# - summary
# - education (list)
# - experience (list)
# - technical_skills (list)
# - certifications (list)
# - projects (list)
# - industry_preferences (list)

# **Analysis Guidelines:**
# 1. Core Identification:
# - Extract full legal name from header/contact section
# - Verify email format (name@domain.tld)
# - Identify phone numbers in international format (+XXX...)
# - Extract summary

# 2. Education Analysis:
# - Parse degrees with majors/specializations
# - Flag accreditation status for institutions
# - Convert dates to MM/YYYY format  if provided
# - Highlight research projects/theses

# 3. Experience Processing: 
# - Separate employment history from internships
# - Identify technical/soft skill development
# - Quantify achievements ("Increased X by Y%")
# - Map technologies to industry standards

# 4. Skill Extraction:
# - Categorize skills:
#   • Technical (tools/platforms)
#   • Methodologies (Agile, Six Sigma)
#   • Domain Knowledge (HIPAA, GAAP)
# - Identify skill maturity levels:
#   (Beginner < 1yr, Intermediate 1-3yr, Expert 3+yr)

# 5. Cross-Industry Transfer Analysis:
# - Identify portable competencies between industries
# - Highlight leadership/management patterns
# - Extract crisis management evidence
# - Flag multilingual capabilities

# **Structured Output Requirements:**
# {format_instructions}

# **Content Processing Rules:**
# - Preserve original wording unless ambiguous
# - only if starting date is provided Convert relative dates ("current" → {today})
# - Expand acronyms first occurrence (WHO → World Health Organization)
# - Handle conflicting info (prioritize most recent)

# **Input Profile:**
# {text}""",
#         input_variables=["text"],
#         partial_variables={
#             "format_instructions": parser.get_format_instructions(),
#             "today": datetime.date.today().strftime("%m/%Y")
#         },
#     )

# def parse_cv(text: str, llm) -> dict:
#     """Process CV text through LLM parsing chain"""
#     try:
#         parser = create_parser()
#         prompt = create_prompt(parser)
#         chain = prompt | llm | parser
#         result = chain.invoke({"text": text})
#         return dict(result)
#     except Exception as e:
#         st.error(f"Error parsing CV: {str(e)}")
#         return {}

# def save_parsed_data(data: dict, user_dir: str) -> None:
#     """Save structured profile data"""
#     save_path = Path(user_dir) / "profile_data.json"
#     with open(save_path, "w") as f:
#         json.dump(data, f, indent=2)
#     st.success(f"📄 Profile data saved!")

# def merge_with_llm(existing: dict, new: dict, llm) -> dict:
#     """Use LLM to intelligently merge two structured profile dicts."""
#     if not existing:
#         return new
#     if not new:
#         return existing

#     try:
#         prompt_text = f"""
# You are a helpful assistant tasked with merging two structured professional profiles extracted from CVs. 
# Your goal is to intelligently combine the data from both profiles, avoiding redundancy, preserving the most complete and informative entries, and resolving conflicts sensibly.

# Act as an expert career analyst with deep cross-industry knowledge (tech, healthcare, finance, engineering). 
# You must identify transferable skills, merge overlapping entries, and preserve all unique information, especially for certifications.

# Please extract and return the following fields in raw JSON format **only**, without preamble or commentary.

# ---
# **Fields to Extract:**
# - full_name
# - contact_email
# - phone
# - summary
# - education (list)
# - experience (list)
# - technical_skills (list)
# - certifications (list)
# - projects (list)
# - industry_preferences (list)
# ---

# **Guidelines for Merging and Extraction:**

# 1. **Core Info:**
#    - Extract full legal name from the header or contact block.
#    - Emails must be valid (e.g., name@domain.com).
#    - Phone numbers must be in international format (+XXX...).

# 2. **Education:**
#    - List all degrees and specializations.
#    - Include institution name, degree, field, start and end date (MM/YYYY).
#    - Highlight research projects or thesis titles if available.
#    - Avoid duplication; if same degree exists with more details, keep the more complete version.

# 3. **Experience:**
#    - Distinguish jobs, internships, freelance, and volunteering.
#    - Include job title, company, duration, technologies used, and quantifiable outcomes.
#    - Keep the most recent or complete version of similar roles.
#    - Use consistent date format (MM/YYYY).

# 4. **Skills:**
#    - Group technical skills (tools, platforms, libraries)
#    - Include experience levels if stated (e.g., Expert, Intermediate).

# 5. **Certifications (✅ Important):**
#    - Extract each certification with full name, issuing organization, and date (if available).
#    - Only merge certifications if the **exact full name and issuer match**.
#    - If titles are slightly different or have extra info (e.g., "AWS Certified Developer – Associate" vs "AWS Developer Cert"), treat them as separate and preserve both.
    
# 6. **Projects:**
#    - Include title, description, technologies used, role (if specified), and duration.
#    - Projects may come from personal work, hackathons, university, or freelance.
#    - Merge only if titles and descriptions are identical or nearly identical.
#    - Preserve all distinct projects — no limit.

# 7. **Industry Preferences:**
#    - Merge the lists, removing duplicates.

# 8. **General Rules:**
#    - Avoid redundancy and merge smartly.
#    - Prioritize clarity, structure, and richness of information.
#    - Do not add placeholder or fabricated data.
#    - Output should be a valid JSON object.

# ---

# **Input Profiles:**

# Profile A (existing):
# {json.dumps(existing, indent=2)}

# Profile B (newly parsed):
# {json.dumps(new, indent=2)}

# Return ONLY the merged profile in raw JSON format.
# Do NOT include explanations or commentary. Just output the final merged JSON.
# """
#         response = llm.invoke(prompt_text)
#         raw_output = response.content.strip()

#         # Safely extract the JSON part from the output
#         json_start = raw_output.find('{')
#         json_end = raw_output.rfind('}')
#         if json_start == -1 or json_end == -1:
#             raise ValueError("No JSON object found in LLM output")

#         clean_json = raw_output[json_start:json_end+1]
#         return json.loads(clean_json)

#     except Exception as e:
#         st.error(f"LLM merge failed: {e}")
#         st.error(f"Raw LLM output:\n{response.content if 'response' in locals() else 'No response'}")
#         return {**existing, **new}  # fallback to simple merge

# def run_cv_pipeline_streamlit(user_dir: str, llm) -> None:
#     """Streamlit-based CV processing pipeline"""
#     st.subheader("Upload and Process Your CV")
    
#     # Display existing profile if available
#     profile_path = Path(user_dir) / "profile_data.json"
#     if profile_path.exists():
#         with open(profile_path) as f:
#             profile_data = json.load(f)
#         st.session_state.profile_data = profile_data
#         st.subheader("Current Profile")
#         st.json(profile_data)
    
#     # File uploader
#     uploaded_file = st.file_uploader("Upload CV (PDF or DOCX)", type=["pdf", "docx"])
    
#     if uploaded_file is not None:
#         with st.spinner("Processing CV..."):
#             # Save the uploaded file
#             safe_filename = re.sub(r"[^\w\.-]", "_", uploaded_file.name)
#             save_path = Path(user_dir) / safe_filename
#             with open(save_path, "wb") as f:
#                 f.write(uploaded_file.getbuffer())
            
#             # Load and parse the file
#             try:
#                 if uploaded_file.name.lower().endswith(".pdf"):
#                     loader = PyPDFLoader(str(save_path))
#                 else:  # .docx
#                     loader = UnstructuredWordDocumentLoader(str(save_path))
                
#                 documents = loader.load()
#                 text = "\n".join([doc.page_content for doc in documents])
                
#                 # Parse CV
#                 new_parsed = parse_cv(text, llm)
                
#                 # Load existing data if it exists
#                 existing_parsed = {}
#                 if profile_path.exists():
#                     with open(profile_path) as f:
#                         existing_parsed = json.load(f)
                
#                 # Merge profiles
#                 merged_data = merge_with_llm(existing_parsed, new_parsed, llm)
#                 save_parsed_data(merged_data, user_dir)
#                 st.session_state.profile_data = merged_data
#                 st.success("Profile updated successfully!")
#             except Exception as e:
#                 st.error(f"Error processing CV: {str(e)}")
    
#     # Delete profile button
#     if st.button("Delete Profile Data"):
#         if profile_path.exists():
#             profile_path.unlink()
#             st.session_state.profile_data = None
#             st.success("Profile data deleted")
# cv_extractor.py (fixed)
import json
import os
import re
import datetime
import fitz  # PyMuPDF for advanced PDF handling
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import streamlit as st
from langchain_core.output_parsers import JsonOutputParser
from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq
from langchain_community.document_loaders import UnstructuredWordDocumentLoader
from pydantic import BaseModel, Field

# Define ProfessionalProfile model with enhanced certificate extraction
class ProfessionalProfile(BaseModel):
    full_name: str = Field(..., description="Full legal name")
    contact_email: str = Field(..., description="Primary contact email")
    phone: Optional[str] = Field(None, description="Contact phone number")
    linkedin: Optional[str] = Field(None, description="LinkedIn profile URL")
    github: Optional[str] = Field(None, description="GitHub profile URL")
    portfolio: Optional[str] = Field(None, description="Personal portfolio/website URL")
    summary: Optional[str] = Field(None, description="Professional summary")
    education: List[Dict] = Field(default_factory=list, description="List of educational achievements")
    experience: List[Dict] = Field(default_factory=list, description="Work history")
    technical_skills: List[str] = Field(default_factory=list, description="Technical skills")
    certifications: List[Dict] = Field(
        default_factory=list, 
        description="List of certifications with name, issuer and verification URL"
    )
    projects: List[Dict] = Field(default_factory=list, description="Notable projects")
    industry_preferences: List[str] = Field(default_factory=list, description="Preferred industries")

def extract_pdf_content(pdf_path: str) -> Tuple[str, List[str]]:
    """Extract both text and hidden links from PDF using PyMuPDF"""
    text = ""
    links = []
    
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            # Extract visible text
            text += page.get_text()
            
            # Extract all links (including hidden ones)
            for link in page.get_links():
                if link['kind'] == fitz.LINK_URI and link.get('uri'):
                    links.append(link['uri'])
        
        # Deduplicate links
        links = list(set(links))
        return text, links
    except Exception as e:
        st.error(f"PDF extraction error: {str(e)}")
        return "", []

def extract_docx_content(docx_path: str) -> Tuple[str, List[str]]:
    """Extract text and links from DOCX using python-docx and unstructured"""
    text = ""
    links = []
    
    try:
        # First get text with Unstructured
        loader = UnstructuredWordDocumentLoader(str(docx_path))
        documents = loader.load()
        text = "\n".join([doc.page_content for doc in documents])
        
        # Additional link extraction for DOCX
        from docx import Document
        doc = Document(docx_path)
        
        # Extract hyperlinks from document relationships
        for rel in doc.part.rels.values():
            if "hyperlink" in rel.reltype:
                links.append(rel._target)
        
        # Extract hyperlinks from text runs
        for para in doc.paragraphs:
            for run in para.runs:
                if run.hyperlink and run.hyperlink.address:
                    links.append(run.hyperlink.address)
        
        # Deduplicate links
        links = list(set(links))
        return text, links
    except Exception as e:
        st.error(f"DOCX extraction error: {str(e)}")
        return text, []

def create_parser():
    return JsonOutputParser(pydantic_object=ProfessionalProfile)

def create_prompt(parser):
    return PromptTemplate(
        template="""**Professional Profile Analysis Task**
Act as an expert career analyst with deep knowledge across industries (tech, healthcare, finance, engineering). 
Extract structured information while identifying transferable skills and cross-domain competencies.

**Fields to Extract:**
- full_name
- contact_email
- phone
- linkedin
- github
- portfolio
- summary
- education (list)
- experience (list)
- technical_skills (list)
- certifications (list of dicts with name, issuer, url)
- projects (list)
- industry_preferences (list)

**Analysis Guidelines:**
1. Core Identification:
- Extract full legal name from header/contact section
- Verify email format (name@domain.tld)
- Identify phone numbers in international format (+XXX...)
- Extract LinkedIn/GitHub/profile URLs from both text and extracted links
- Extract summary

2. Education Analysis:
- Parse degrees with majors/specializations
- Flag accreditation status for institutions
- Convert dates to MM/YYYY format if provided
- Highlight research projects/theses

3. Experience Processing: 
- Separate employment history from internships
- Identify technical/soft skill development
- Quantify achievements ("Increased X by Y%")
- Map technologies to industry standards

4. Link Extraction:
- LinkedIn: Extract full profile URLs (https://www.linkedin.com/in/username)
- GitHub: Extract full profile URLs (https://github.com/username)
- Portfolio: Identify personal websites/blogs
- Social Media: Only include professional networks (ignore personal social media)
- Verify URL formats and discard malformed links

5. Certificate Extraction (CRITICAL):
- Extract ALL certifications with:
  • Full name (e.g., "AWS Certified Solutions Architect - Associate")
  • Issuing organization (e.g., "Amazon Web Services")
  
  • Verification URL (if available in text or extracted links)
- Match verification URLs to certificates:
  • Look for credential IDs in text (e.g., "Credential ID XYZ-123")
  • Find matching verification URLs in extracted links
  • Prioritize URLs from known credential platforms:
    - credly.com
    - acm.org
    - youracclaim.com
    - aws.amazon.com/certification
    - learn.microsoft.com/certifications
    - google.com/certification
    - coursera.org/professional-certificates
- For certificates without explicit URLs:
  • Search extracted links for possible matches
  • Only include verifiable URLs (no generic organization sites)

6. Skill Extraction:
- Categorize skills:
  • Technical (tools/platforms)
  • Methodologies (Agile, Six Sigma)
  • Domain Knowledge (HIPAA, GAAP)
- Identify skill maturity levels:
  (Beginner < 1yr, Intermediate 1-3yr, Expert 3+yr)

7. Cross-Industry Transfer Analysis:
- Identify portable competencies between industries
- Highlight leadership/management patterns
- Extract crisis management evidence
- Flag multilingual capabilities

**Structured Output Requirements:**
{format_instructions}

**Content Processing Rules:**
- Preserve original wording unless ambiguous
- Convert relative dates ("current" → {today})
- Expand acronyms first occurrence (WHO → World Health Organization)
- Handle conflicting info (prioritize most recent)
- Use extracted links to supplement missing profile URLs and certificate verification links

**Input Profile:**
{text}

**Extracted Links:**
{links}""",
        input_variables=["text"],
        partial_variables={
            "format_instructions": parser.get_format_instructions(),
            "today": datetime.date.today().strftime("%m/%Y")
        },
    )

def parse_cv(text: str, links: List[str], llm) -> dict:
    """Process CV text and links through LLM parsing chain"""
    try:
        parser = create_parser()
        prompt = create_prompt(parser)
        
        # Format links for inclusion in prompt
        links_str = "\n".join(links) if links else "No links found"
        
        chain = prompt | llm | parser
        result = chain.invoke({"text": text, "links": links_str})
        return dict(result)
    except Exception as e:
        st.error(f"Error parsing CV: {str(e)}")
        return {}

def save_parsed_data(data: dict, user_dir: str) -> None:
    """Save structured profile data"""
    save_path = Path(user_dir) / "profile_data.json"
    with open(save_path, "w") as f:
        json.dump(data, f, indent=2)
    st.success(f"📄 Profile data saved!")

def merge_with_llm(existing: dict, new: dict, llm) -> dict:
    """Use LLM to intelligently merge two structured profile dicts."""
    if not existing:
        return new
    if not new:
        return existing

    try:
        prompt_text = f"""
You are a helpful assistant tasked with merging two structured professional profiles extracted from CVs. 
Your goal is to intelligently combine the data from both profiles, avoiding redundancy, preserving the most complete and informative entries, and resolving conflicts sensibly.

Act as an expert career analyst with deep cross-industry knowledge (tech, healthcare, finance, engineering). 
You must identify transferable skills, merge overlapping entries, and preserve all unique information, especially for certifications.

Please extract and return the following fields in raw JSON format **only**, without preamble or commentary.

---
**Fields to Extract:**
- full_name
- contact_email
- phone
- linkedin
- github
- portfolio
- summary
- education (list)
- experience (list)
- technical_skills (list)
- certifications (list of dicts with name, issuer, url)
- projects (list)
- industry_preferences (list)
---

**Guidelines for Merging and Extraction:**

1. **Core Info:**
   - Extract full legal name from the header or contact block.
   - Emails must be valid (e.g., name@domain.com).
   - Phone numbers must be in international format (+XXX...).
   - Preserve all profile links (LinkedIn, GitHub, portfolio).

2. **Education:**
   - List all degrees and specializations.
   - Include institution name, degree, field, start and end date (MM/YYYY).
   - Highlight research projects or thesis titles if available.
   - Avoid duplication; if same degree exists with more details, keep the more complete version.

3. **Experience:**
   - Distinguish jobs, internships, freelance, and volunteering.
   - Include job title, company, duration, technologies used, and quantifiable outcomes.
   - Keep the most recent or complete version of similar roles.
   - Use consistent date format (MM/YYYY).

4. **Skills:**
   - Group technical skills (tools, platforms, libraries)
   - Include experience levels if stated (e.g., Expert, Intermediate).

5. **Certifications (✅ Critical):**
   - Extract each certification with:
     • name (full certification title)
     • issuer (certifying organization)
    
     • url (verification link if available)
   - Merge certifications only when ALL of these match:
     • Certification name (exact match)
     • Issuing organization (exact match)
     • Verification URL (if both have URLs, they must match)
   - If any element differs, treat as separate certifications
   - Preserve all verification URLs
   - If a certification appears without URL in one source and with URL in another, merge and keep the URL

6. **Projects:**
   - Include title, description, technologies used, role (if specified), and duration.
   - Projects may come from personal work, hackathons, university, or freelance.
   - Merge only if titles and descriptions are identical or nearly identical.
   - Preserve all distinct projects — no limit.

7. **Industry Preferences:**
   - Merge the lists, removing duplicates.

8. **General Rules:**
   - Avoid redundancy and merge smartly.
   - Prioritize clarity, structure, and richness of information.
   - Do not add placeholder or fabricated data.
   - Output should be a valid JSON object.

---

**Input Profiles:**

Profile A (existing):
{json.dumps(existing, indent=2)}

Profile B (newly parsed):
{json.dumps(new, indent=2)}

Return ONLY the merged profile in raw JSON format.
Do NOT include explanations or commentary. Just output the final merged JSON.
"""
        response = llm.invoke(prompt_text)
        raw_output = response.content.strip()

        # Safely extract the JSON part from the output
        json_start = raw_output.find('{')
        json_end = raw_output.rfind('}')
        if json_start == -1 or json_end == -1:
            raise ValueError("No JSON object found in LLM output")

        clean_json = raw_output[json_start:json_end+1]
        return json.loads(clean_json)

    except Exception as e:
        st.error(f"LLM merge failed: {e}")
        st.error(f"Raw LLM output:\n{response.content if 'response' in locals() else 'No response'}")
        return {**existing, **new}  # fallback to simple merge

def run_cv_pipeline_streamlit(user_dir: str, llm) -> None:
    """Streamlit-based CV processing pipeline with enhanced link extraction"""
    st.subheader("Upload and Process Your CV")
    
    # Display existing profile if available
    profile_path = Path(user_dir) / "profile_data.json"
    if profile_path.exists():
        with open(profile_path) as f:
            profile_data = json.load(f)
        st.session_state.profile_data = profile_data
        st.subheader("Profile exists")
        
        
        
        
    
    # File uploader
    uploaded_file = st.file_uploader("Upload CV (PDF or DOCX)", type=["pdf", "docx"])
    
    if uploaded_file is not None:
        with st.spinner("Processing CV..."):
            # Save the uploaded file
            safe_filename = re.sub(r"[^\w\.-]", "_", uploaded_file.name)
            save_path = Path(user_dir) / safe_filename
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Process based on file type
            text = ""
            links = []
            
            if uploaded_file.type == "application/pdf":
                text, links = extract_pdf_content(save_path)
            elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                text, links = extract_docx_content(save_path)
            
            # Display extraction info
            st.info(f"📊 Extracted {len(text.split())} words and {len(links)} links")
            
            # Show links in a scrollable container instead of expander
            # if links:
            #     st.subheader("🔗 Extracted Links")
            #     links_container = st.container(height=200)
            #     with links_container:
            #         for link in links:
            #             st.markdown(f"- [{link}]({link})")
            
            # Parse CV with both text and links
            new_parsed = parse_cv(text, links, llm)
            
            # Show raw parsed data in a scrollable container
            # st.subheader("🔄 Raw Parsed Data")
            # raw_data_container = st.container(height=300)
            # with raw_data_container:
            #     st.json(new_parsed)
            
            # Load existing data if it exists
            existing_parsed = {}
            if profile_path.exists():
                with open(profile_path) as f:
                    existing_parsed = json.load(f)
            
            # Merge profiles
            merged_data = merge_with_llm(existing_parsed, new_parsed, llm)
            
            # Save merged profile
            save_parsed_data(merged_data, user_dir)
            st.session_state.profile_data = merged_data
            
            # Display certificate verification status
            # if merged_data.get("certifications"):
            #     st.subheader("✅ Certificates with Verification Links")
            #     cert_container = st.container()
            #     with cert_container:
            #         for cert in merged_data["certifications"]:
            #             name = cert.get("name", "Unnamed Certificate")
            #             issuer = cert.get("issuer", "Unknown Issuer")
                        
            #             url = cert.get("url", "")
                        
            #             if url:
            #                 st.markdown(f"- **{name}** ({issuer}): [Verify]({url})")
            #             else:
            #                 st.markdown(f"- **{name}** ({issuer}) - *Verification link not found*")
            
            st.success("🎉 Profile updated successfully!")

    if st.button("🗑️ Delete Profile Data"):
        # Get user directory from session state
        user_dir = st.session_state.get("user_dir")
        
        if user_dir:
            user_path = Path(user_dir)
            
            # Delete profile_data.json
            profile_path = user_path / "profile_data.json"
            if profile_path.exists():
                profile_path.unlink()
            
            # Delete all PDF files
            for pdf_file in user_path.glob("*.pdf"):
                pdf_file.unlink()
            
            # Delete all Word files (.doc and .docx)
            for doc_file in user_path.glob("*.doc"):
                doc_file.unlink()
            for docx_file in user_path.glob("*.docx"):
                docx_file.unlink()
            
            # Delete cover letter if exists
            cover_letter_path = user_path / "latest_cover_letter.txt"
            if cover_letter_path.exists():
                cover_letter_path.unlink()
            
            # Reset session state
            st.session_state.profile_data = None
            st.session_state.generated_cv = None
            st.session_state.cover_letter = None
            
            st.success("Profile data and all generated files (PDF/DOCX) deleted")
        else:
            st.warning("No user directory found. Cannot delete files.")