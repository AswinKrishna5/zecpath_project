from celery import shared_task
from .services import send_application_submitted_email,make_twilio_call
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
        ai_call,created=AICall.objects.get_or_create(application=application,defaults={"status":AICall.Status.QUEUED},)
        if ai_call.call_logs.filter(event="CALL_REQUESTED").exists():
            return "Twilio call was already requested"
        if ai_call.status == AICall.Status.COMPLETED:
            return "AI call already completed"
        candidate_phone = application.candidate.phone
        candidate_name = application.candidate.full_name
        if not candidate_phone:
            raise ValueError("Candidate phone number is missing")
        now = timezone.now()
        session, created = AIInterviewSession.objects.get_or_create(
            ai_call=ai_call,
            defaults={"status": AIInterviewSession.Status.IN_PROGRESS,"started_at": now, },)
        if not created:
            session.status = AIInterviewSession.Status.IN_PROGRESS
            if session.started_at is None:
                session.started_at = now
            session.save(update_fields=["status", "started_at"])
        if ai_call.started_at is None:
            ai_call.started_at = now
        ai_call.status = AICall.Status.IN_PROGRESS
        ai_call.save(update_fields=["status", "started_at"])
        if not ai_call.call_logs.filter(event="CALL_STARTED").exists():
            CallLog.objects.create(ai_call=ai_call,event="CALL_STARTED",details="AI interview call started.",triggered_by=None,
            reason="Automatically initiated by the ATS.",)
            
        call_result = make_twilio_call(to_number=candidate_phone,message=(f"Hello {candidate_name}. "
        "This is an automated interview call "
        "regarding your job application."),voice="alice",language="en-US",)
        CallLog.objects.create(ai_call=ai_call,event="CALL_REQUESTED",details=(
        "Twilio accepted the outbound call request. "
        f"Call SID: {call_result['call_sid']}; "
        f"provider status: {call_result['status']}."),triggered_by=None,reason="Outbound call initiated by Twilio.",)
        return {"success": True,"message": "Twilio call request accepted","call_sid": call_result["call_sid"],
        "provider_status": call_result["status"],}
    except Exception as exc:
        if ai_call is None:
            ai_call = AICall.objects.filter(application_id=application_id).first()
        if isinstance(exc, (ValueError, AICall.DoesNotExist)):
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
            raise 
        if ai_call is not None:
            ai_call.status = AICall.Status.FAILED
            ai_call.save(update_fields=["status"])
            session = AIInterviewSession.objects.filter(ai_call=ai_call).first()
            if session:
                session.status = AIInterviewSession.Status.FAILED
                session.save(update_fields=["status"])
            if not ai_call.call_logs.filter(event="CALL_FAILED").exists():
                CallLog.objects.create(ai_call=ai_call,event="CALL_FAILED",details=str(exc),triggered_by=None,
                    reason="The automated AI call task encountered an error.",)
        raise

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













