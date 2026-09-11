from .models import CandidateProfile,EmployerProfile
import re
import os
import pdfplumber
from docx import Document

def get_candidate_profile(user,user_id=None):

    if user.role=="ADMIN":
        if not user_id:
            return None,"user id required for admin"

        try:
            profile=CandidateProfile.objects.get(user_id=user_id,is_deleted=False)
            return profile,None
        except CandidateProfile.DoesNotExist:
            return None,"candidate profile not found"

    try:
        profile=CandidateProfile.objects.get(user=user,is_deleted=False)
        return profile,None
    except CandidateProfile.DoesNotExist:
        return None,"profile not found"

def get_employer_profile(user,user_id=None):

    if user.role=="ADMIN":
        if not user_id:
            return None,"user id required for admin"

        try:
            profile=EmployerProfile.objects.get(user_id=user_id,is_deleted=False)
            return profile,None
        except EmployerProfile.DoesNotExist:
            return None,"employer profile not found"

    try:
        profile=EmployerProfile.objects.get(user=user,is_deleted=False)
        return profile,None
    except EmployerProfile.DoesNotExist:
        return None,"profile not found"

def clean_resume_text(text):
    lines=text.splitlines()
    cleaned_lines=[]
    for line in lines:
        line=re.sub(r"\s+", " ",line).strip()
        if line:
            cleaned_lines.append(line)
    return "\n".join(cleaned_lines)

def extract_text_from_pdf(file):
    text=""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text+=page.extract_text() or ""
            text+="\n"
    return text

def extract_text_from_docx(file):
    document=Document(file)
    text="" 
    for paragraph in document.paragraphs:
        text+=paragraph.text+"\n"
    return text

def extract_resume_text(file):
    extension=os.path.splitext(file.name)[1].lower()
    if extension==".pdf":
        return extract_text_from_pdf(file)
    if extension==".docx":
        return extract_text_from_docx(file)
    raise ValueError("unsupported resume format.")

def parse_resume(file):
    raw_text=extract_resume_text(file)
    cleaned_text=clean_resume_text(raw_text)
    return cleaned_text   

SKILLS_LIBRARY=["python","mongodb","django","django rest framework","sql","mysql","postgresql","javascript","react","html","css","git","github","docker","aws",]

def extract_skills(text):
    extracted_skills=[]
    for skills in SKILLS_LIBRARY:
        pattern=rf"\b{re.escape(skills)}\b"
        if re.search(pattern,text,re.IGNORECASE):
            extracted_skills.append(skills)
    return extracted_skills

def parse_resume_data(file):
    raw_text=extract_resume_text(file)
    cleaned_text=clean_resume_text(raw_text)
    skills=extract_skills(cleaned_text)
    return{"text":cleaned_text,"skills":skills}

def extract_experience_years(text):
    pattern=r"(\d+)\+?\s*(?:years?|yrs?)"
    mataches=re.findall(pattern,text,re.IGNORECASE)
    if mataches:
        return max(int(year)for year in mataches)
    return 0

ROLE_LIBRARY=["python developer","django developer","backend developer","software developer","software engineer","full stack developer","frontend developer","web developer",]

def extract_roles(text):
    extracted_roles=[]
    for role in ROLE_LIBRARY:
        pattern=rf"\b{re.escape(role)}\b"
        if re.search(pattern,text,re.IGNORECASE):
            extracted_roles.append(role)
    return extracted_roles

EDUCATION_LIBRARY=["bca","b.tech","be","mca","m.tech","me","bsc","msc","bachelor of computer applications","master of computer applications","bachelor of technology","master of technology",]

def extract_education(text):
    extracted_education=[]
    for education in EDUCATION_LIBRARY:
        pattern=rf"\b{re.escape(education)}\b"
        if re.search(pattern,text,re.IGNORECASE):
            extracted_education.append(education)
    return extracted_education

def parse_resume_structured(file):
    raw_text=extract_resume_text(file)
    cleaned_text=clean_resume_text(raw_text)
    skills=extract_skills(cleaned_text)
    role=extract_roles(cleaned_text)
    experience_years=extract_experience_years(cleaned_text)
    education=extract_education(cleaned_text)
    return{"text":cleaned_text,"skills":skills,"role":role,"experience_years":experience_years,"education":education}