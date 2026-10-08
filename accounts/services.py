from .models import CandidateProfile,EmployerProfile,Application,EmailLog,JobQuestionMapping,QuestionTemplate,AIQuestion
import re
import os
import pdfplumber
from docx import Document

from .workflow import is_valid_transition

from django.core.mail import send_mail
from django.template.loader import render_to_string
from datetime import time,timedelta
from django.utils import timezone

from django.db import transaction
import logging
from html import escape

from django.conf import settings
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from urllib.parse import urlencode
from twilio.http.http_client import TwilioHttpClient


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

def check_eligibility(application,threshold):
    if application.ats_score is None:
        return False
    return application.ats_score >= threshold

ROLE_THRESHOLDS={"python developer": 80,"django developer": 80,"backend developer": 80,"software developer": 75,
                "software engineer": 80,"full stack developer": 75,"frontend developer": 70,"web developer": 70,}

def get_job_threshold(job):
    job_title=job.title.strip().lower()
    for role,threshold in ROLE_THRESHOLDS.items():
        if role in job_title:
            return threshold
    return 75

def check_job_eligibility(application):
    threshold=get_job_threshold(application.job)
    return check_eligibility(application,threshold)

def auto_shortlist_application(application):
    if application.status!=application.Status.APPLIED:
        return False
    if check_job_eligibility(application):
        application.status=application.Status.SHORTLISTED
        application.save(update_fields=["status"])
        send_shortlisted_email(application=application,candidate_email=application.candidate.user.email,candidate_name=application.candidate.full_name,job_title=application.job.title,)
        trigger_ai_call_if_eligible(application)
        return True
    return False

def auto_reject_application(application):
    if application.status!=application.Status.APPLIED:
        return False
    if not check_job_eligibility(application):
        application.status=application.Status.REJECTED
        application.save(update_fields=["status"])
        send_rejected_email(application=application,candidate_email=application.candidate.user.email,candidate_name=application.candidate.full_name,job_title=application.job.title,)
        
        return True
    return False

def create_status_notification(application):
    if application.status==application.Status.SHORTLISTED:
        message="your application has been shortlisted"
    elif application.status==application.Status.REJECTED:
        message="your application has been rejected"
    else :
        return None
    return {"application_id": application.id,"job_title": application.job.title,"status": application.status,"message": message,}

def process_job_applications(job):
    applications=Application.objects.filter(job=job,status=Application.Status.APPLIED)
    results=[]
    for application in applications:
        if auto_shortlist_application(application):
            action="SHORTLISTED"
        elif auto_reject_application(application):
            action="REJECTED"
        else:
            action="NO MATCH"
        results.append({ "application_id": application.id,"status": application.status,"action": action,})
    return results

def override_application_status(application,new_status):
    if not is_valid_transition(application.status,new_status):
        return False
    application.status=new_status
    application.save(update_fields=["status"])
    return True

def send_application_submitted_email(application,candidate_email,candidate_name,job_title):
    message=render_to_string("emails/application_submitted.txt",{"candidate_name":candidate_name,"job_title":job_title})
    send_email_with_retry(application=application,subject="application submitted succesfully",message=message,recipient_email=candidate_email)

def send_shortlisted_email(application,candidate_email,candidate_name,job_title):
    message=render_to_string("emails/shortlisted.txt",{"candidate_name":candidate_name,"job_title":job_title})
    send_email_with_retry(application=application,subject="application shortlisted succesfully",message=message,recipient_email=candidate_email)

def send_rejected_email(application,candidate_email,candidate_name,job_title):
    message=render_to_string("emails/rejected.txt",{"candidate_name":candidate_name,"job_title":job_title})
    send_email_with_retry(application=application,subject="application rejected",message=message,recipient_email=candidate_email)

def send_email_with_retry(application,subject,message,recipient_email,max_retries=3):
    for attempt in range(max_retries):
        try:
            send_mail(subject,message,None,[recipient_email],fail_silently=False)
            EmailLog.objects.create(application=application,recipient=recipient_email,subject=subject,status="SENT")
            return True
        except Exception as e:
            if attempt==max_retries-1:
                EmailLog.objects.create(application=application,recipient=recipient_email,subject=subject,status="FAILED",error_message=str(e))
                return False
    return False

def is_ai_call_eligible(application,threshold=80):
    if application.ats_score is None:
        return False
    if application.job.status != "ACTIVE":
        return False
    if not application.candidate.is_available_for_ai_call :
        return False
    return application.ats_score>=threshold

def trigger_ai_call_if_eligible(application):
    from .models import AICall,CallLog
    if application.status!=application.Status.SHORTLISTED:
        return False
    if not is_ai_call_eligible(application):
        return False
    with transaction.atomic():
        ai_call,created=AICall.objects.get_or_create(application=application,defaults={"status":AICall.Status.QUEUED})
        if not created:
           return False 
        if is_within_ai_call_window():
            CallLog.objects.create(ai_call=ai_call,event="AI_CALL_TRIGGERED",details="AI interview call triggered automatically",triggered_by=None,reason=(
                "application was shortlisted and met ai eligible criteria "
            ))
            from .tasks import trigger_ai_call_task
            transaction.on_commit(lambda:trigger_ai_call_task.delay(application.id))
        else:
            CallLog.objects.create(ai_call=ai_call,event="AI_CALL_SCHEDULED",details=(
                    "AI interview call queued for the next "
                    "permitted call window."),triggered_by=None,reason=(
                    "Application was eligible, but the current "
                    "time was outside the permitted call window."))
            
            transaction.on_commit(lambda:schedule_ai_call_for_next_window(application.id))
    return True

def is_within_ai_call_window():
    current_time=timezone.localtime().time()
    start_time=time(9,0)
    end_time=time(18,0)
    return start_time<=current_time<=end_time

def schedule_ai_call_for_next_window(applicatoin_id):
    from .tasks import trigger_ai_call_task
    now=timezone.localtime()
    today_start=now.replace(hour=9,minute=0,second=0,microsecond=0)
    today_end=now.replace(hour=18,minute=0,second=0,microsecond=0)
    if now<today_start:
        target_time=today_start
    elif now>=today_end:
        target_time=today_start+timedelta(days=1)
    else:
        trigger_ai_call_task.delay(applicatoin_id)
        return True
    countdown=max(0,int((target_time-now).total_seconds()))
    trigger_ai_call_task.apply_sync(args=[applicatoin_id],countdown=countdown)
    return True

#day35#....................................

logger = logging.getLogger(__name__)
def make_twilio_call(to_number,message,voice="alice",language="en-US",):
    if not settings.TWILIO_ACCOUNT_SID:
        raise ValueError("twilio account sid is not configured")
    if not settings.TWILIO_AUTH_TOKEN:
        raise ValueError("twilio auth token is not configured")
    if not settings.TWILIO_PHONE_NUMBER:
        raise ValueError("twilio trial phone number is not configured")
    if not settings.TWILIO_TWIML_BIN_URL:
        raise ValueError("twilio twiml bin url is not configured")
    if not to_number or not to_number.startswith("+"):
        raise ValueError("the noumber should in internation format, eg +91")
    if not message or not message.strip():
        raise ValueError("the message cannot be empty")
    http_client=TwilioHttpClient(timeout=10)
    client=Client(settings.TWILIO_ACCOUNT_SID,settings.TWILIO_AUTH_TOKEN,http_client=http_client)
    
    try:
        params = urlencode({"message": message,"voice": voice,"language": language,})
        voice_url = f"{settings.TWILIO_TWIML_BIN_URL}?{params}"
        call=client.calls.create(to=to_number,from_=settings.TWILIO_PHONE_NUMBER,url=voice_url)
        logger.info("twilo call created succesfully.call sid:%s",call.sid)
        return {"success":True,"call_sid":call.sid,"status":call.status}
    except TwilioRestException as exc:
        logger.exception("Twilio rejected the outbound call.code:%s status:%s message:%s",exc.code,exc.status,exc.msg)
        raise

#day36.............................

def get_next_question(job,current_question_index=0):
    mappings=JobQuestionMapping.objects.filter(job=job,is_active=True,question_template__is_active=True).select_related("question_template").order_by("question_order")
    for mapping in mappings:
        if mapping.question_order>current_question_index:
            return mapping.question_template
    return None

def get_current_question(session):
    question=session.questions.filter(answer__isnull=True).order_by("question_order").first()
    return question

def should_ask_follow_up(answer_text):
    if not answer_text:
        return False
    answer=answer_text.lower().strip()
    positive_answers=[ "yes","yeah","yep","sure","i have","absolutly","i do",]
    return any(phrase in answer
               for phrase in positive_answers
    )

def get_follow_up_question(session,answer_text):
    answered_question=AIQuestion.objects.filter(session=session,answer__answer_text=answer_text).select_related("question_mapping").first()

    if not answered_question:
        return None
    answer = answer_text.lower().strip()
    next_question=session.questions.filter(question_order__gt=answered_question.question_order,answer__isnull=True).order_by("question_order").first()
    if not next_question:
        return None
    mapping=next_question.question_mapping
    if not mapping:
        None
    if mapping.depends_on_id==answered_question.question_mapping_id:
            if mapping.trigger_answer.lower() in answer:
                return next_question
    return None
    # if not should_ask_follow_up(answer_text):
    #     return None
    # current_question = get_current_question(session)
    # if not current_question:
    #     return None
    # next_question = session.questions.filter(question_order__gt=current_question.question_order,answer__isnull=True
    # ).order_by("question_order").first()
    # return next_question

def create_interview_questions(session):
    existing_questions=session.questions.all().order_by("question_order")
    if existing_questions.exists():
        return list(existing_questions)
    job=session.ai_call.application.job
    mappings=JobQuestionMapping.objects.filter(job=job,is_active=True,question_template__is_active=True).select_related("question_template").order_by("question_order")
    questions=[]
    for mapping in mappings:
        question=AIQuestion.objects.create(session=session,question_mapping=mapping,question_text=mapping.question_template.question_text,question_order=mapping.question_order)
        questions.append(question)
    return questions



def get_next_interview_question(session,answer_text=None):
    if answer_text:
        answered_question=AIQuestion.objects.filter(session=session,answer__answer_text=answer_text).select_related("question_mapping").first()

        if not answered_question:
            return None
        follow_up=get_follow_up_question(session,answer_text)    
        if follow_up:
            return follow_up
        next_questions=session.questions.filter(question_order__gt=answered_question.question_order,answer__isnull=True).select_related("question_mapping").order_by("question_order")
        for question in next_questions:
            mapping = question.question_mapping
            if mapping and mapping.depends_on_id:
                continue
            return question
        return None
    return get_current_question(session)