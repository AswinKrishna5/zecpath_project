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