from celery import shared_task
from .services import send_application_submitted_email

@shared_task
def send_application_email_task(application_id,candidate_name,candidate_email,job_title):
    from .models import Application
    application=Application.objects.get(id=application_id)  
    send_application_submitted_email(application=application,candidate_email=candidate_email,candidate_name=candidate_name,job_title=job_title)
    return "application email send succesfully"

@shared_task
def parse_resume_task(profile_id):
    from .models import CandidateProfile
    from .services import parse_resume_structured
    profile=CandidateProfile.objects.get(id=profile_id)
    if not profile.resume:
        return "profile not found"
    parsed_data=parse_resume_structured(profile.resume)
    profile.resume_text=parsed_data["text"]
    profile.resume_data=parsed_data
    profile.save(update_fields=["resume_text","resume_data"])
    return "resume parsed succesfully"

@shared_task
def trigger_ai_call_task(application_id):
    from .models import Application
    application=Application.objects.get(id=application_id)
    if application.status!=Application.Status.SHORTLISTED:
        return "application is not shortlisted"
