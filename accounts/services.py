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

def calculate_skill_match(candidate_skills,job_skills):
    candidate_skills=[skill.strip().lower()for skill in candidate_skills]
    job_skills=[skill.strip().lower()for skill in job_skills.split(",")]
    if not job_skills:
        return 0
    matched_skills=[
        skill for skill in job_skills
        if skill in candidate_skills]
    return (len(matched_skills)/len(job_skills))*100

def calculate_experience_match(candidate_experience,job_experience):
    pattern=r"(\d+)\+?\s*(?:years|yrs?)"
    match=re.search(pattern,job_experience,re.IGNORECASE)
    if not match:
        return 0
    required_experience=int(match.group(1))
    if candidate_experience>=required_experience:
        return 100
    if required_experience==0:
        return 100
    return (candidate_experience/required_experience)*100

def calculate_education_match(candiate_education,job_description):
    candiate_education=[education.strip().lower() for education in candiate_education]
    education_keywords=["bca","b.tech","be","mca","m.tech","me","bsc","msc",
        "bachelor of computer applications","master of computer applications","bachelor of technology","master of technology",]
    required_education=[]
    for education in education_keywords:
        pattern=rf"\b{re.escape(education)}\b"
        if re.search(pattern,job_description,re.IGNORECASE):
            required_education.append(education)
    if not required_education:
        return 100
    for education in required_education:
        if education in candiate_education:
            return 100
    return 0


def normalize_score(score):
    return max(0,min(score,100))


def calculate_ats_score(candidate,job):
    resume_data=candidate.resume_data or {}
    candidate_skills=resume_data.get("skills",[])
    candidate_experience=resume_data.get("experience_years",0)
    candidate_education=resume_data.get("education",[])
    skill_match=calculate_skill_match(candidate_skills,job.skills)
    experience_match=calculate_experience_match(candidate_experience,job.experience)
    education_match=calculate_education_match(candidate_education,job.description)
    skill_match=normalize_score(skill_match)
    experience_match=normalize_score(experience_match)
    education_match=normalize_score(education_match)
    ats_score=((skill_match * 0.60)+(experience_match * 0.25)+(education_match * 0.15))
    ats_score=normalize_score(ats_score)

    return {"skill_match": round(skill_match, 2),"experience_match": round(experience_match, 2),
        "education_match": round(education_match, 2),"ats_score": round(ats_score, 2),}

def rank_candidates(job,candidates):
    ranked_candidates=[]
    for candidate in candidates:
        score_data=calculate_ats_score(candidate,job)
        ranked_candidates.append({"candidate": candidate,"score": score_data["ats_score"],"skill_match": score_data["skill_match"],
                                "experience_match": score_data["experience_match"],"education_match": score_data["education_match"],})
    ranked_candidates.sort(key=lambda item:item["score"],reverse=True)
    return ranked_candidates