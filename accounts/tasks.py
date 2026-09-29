from celery import shared_task
from .services import send_application_submitted_email
from django.utils import timezone
from .speech_to_text import transcribe_audio
from .models import AIInterviewSession

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

@shared_task(bind=True, max_retries=3)
def trigger_ai_call_task(self, application_id):
    from .models import (Application,AICall,AIInterviewSession, CallLog,)
    ai_call = None
    try:
        application = Application.objects.get(id=application_id)
        if application.status != Application.Status.SHORTLISTED:
            return "Application is not shortlisted"
        ai_call = AICall.objects.get(application=application)
        if ai_call.status == AICall.Status.COMPLETED:
            return "AI call already completed"
        now = timezone.now()
        if ai_call.started_at is None:
            ai_call.started_at = now
        ai_call.status = AICall.Status.IN_PROGRESS
        ai_call.save(update_fields=["status", "started_at"])
        session, created = AIInterviewSession.objects.get_or_create(
            ai_call=ai_call,
            defaults={"status": AIInterviewSession.Status.IN_PROGRESS,"started_at": now, },)
        if not created:
            session.status = AIInterviewSession.Status.IN_PROGRESS
            if session.started_at is None:
                session.started_at = now
            session.save(update_fields=["status", "started_at"])
        if not ai_call.call_logs.filter(event="CALL_STARTED").exists():
            CallLog.objects.create(ai_call=ai_call,event="CALL_STARTED",details="AI interview call started.",triggered_by=None,
                reason="Automatically initiated by the ATS.",)
        completed_at = timezone.now()
        ai_call.status = AICall.Status.COMPLETED
        ai_call.completed_at = completed_at
        ai_call.save(update_fields=["status", "completed_at"])
        session.status = AIInterviewSession.Status.COMPLETED
        session.ended_at = completed_at
        session.save(update_fields=["status", "ended_at"])
        if not ai_call.call_logs.filter(event="CALL_COMPLETED").exists():
            CallLog.objects.create(ai_call=ai_call,event="CALL_COMPLETED",details="AI interview task completed.",triggered_by=None,
                reason="The automated task completed successfully.",)
        return f"AI call completed for application {application.id}"
    except Exception as exc:
        if ai_call is None:
            ai_call = AICall.objects.filter(application_id=application_id).first()
        if ai_call is not None:
            ai_call.status = AICall.Status.FAILED
            ai_call.save(update_fields=["status"])
            session = AIInterviewSession.objects.filter(ai_call=ai_call).first()
            if session:
                session.status = AIInterviewSession.Status.FAILED
                session.save(update_fields=["status"])
            if not ai_call.call_logs.filter(event="CALL_FAILED").exists():
                CallLog.objects.create(ai_call=ai_call, event="CALL_FAILED", details=str(exc),triggered_by=None,
                    reason="The automated AI call task encountered an error.",)
        raise self.retry(exc=exc, countdown=10)

@shared_task
def transcribe_interview_audio_task(session_id,audio_file_path):
    try:
        session=AIInterviewSession.objects.get(id=session_id)
        transcript_text=transcribe_audio(audio_file_path)
        session.transcript=[{"speaker": "CANDIDATE","text": transcript_text,"timestamp": None}]
        session.save(update_fields=["transcript"])
        return {"session_id": session.id,"status": "TRANSCRIBED","transcript": transcript_text}
    except AIInterviewSession.DoesNotExist:
        return { "session_id": session_id,"status": "FAILED","error": "Interview session not found"}


session = AIInterviewSession.objects.get(id=2)

print(session.transcript)