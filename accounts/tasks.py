from celery import shared_task
from .services import send_application_submitted_email,make_twilio_call
from django.utils import timezone
from .speech_to_text import transcribe_audio
from .models import AIInterviewSession
from django.conf import settings

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

@shared_task(bind=True,max_retries=3,default_retry_delay=60)
def send_interview_reminder_task(self,reminder_id):
    from .models import InterviewReminder
    from .services import send_interview_reminder_email
    reminder=InterviewReminder.objects.filter(id=reminder_id).first()
    if reminder is None:
        return f"reminder {reminder_id} is not found"
    if reminder.status==InterviewReminder.Status.SENT:
        return "email already sent"
    if reminder.status==InterviewReminder.Status.FAILED:
            return "email remainder failed permenently"
    try:
        reminder.status=InterviewReminder.Status.PROCESSING
        reminder.attempts+=1
        reminder.save(update_fields=["attempts","status"])
        recipient=send_interview_reminder_email(reminder)
        reminder.status=InterviewReminder.Status.SENT
        reminder.sent_at=timezone.now()
        reminder.last_error=""
        reminder.save(update_fields=["status","sent_at","last_error"])
        return f"reminder sent successfully to{recipient}"
    except Exception as exc:
        reminder.last_error=str(exc)
        if self.request.retries>=self.max_retries:
            reminder.status=InterviewReminder.Status.FAILED
            reminder.save(update_fields=["status","last_error"])
            return f"Email reminder failed: {exc}"
        reminder.save(update_fields=["last_error"])
        raise self.retry(exc=exc)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_interview_voice_reminder_task(self, reminder_id):
    from .models import InterviewReminder
    from .services import make_twilio_call
    reminder = InterviewReminder.objects.filter(id=reminder_id).first()
    if reminder is None:
        return f"Reminder {reminder_id} not found"
    if reminder.voice_status in [InterviewReminder.VoiceStatus.QUEUED,InterviewReminder.VoiceStatus.IN_PROGRESS,
        InterviewReminder.VoiceStatus.COMPLETED,]:
        return "Voice reminder is already queued or completed"
    if reminder.voice_status == InterviewReminder.VoiceStatus.FAILED:
        return "Voice reminder has failed permanently"
    try:
        reminder.voice_status = InterviewReminder.VoiceStatus.PROCESSING
        reminder.voice_attempts += 1
        reminder.save(update_fields=["voice_status", "voice_attempts"])
        session = reminder.session
        application = session.ai_call.application
        candidate = application.candidate
        job = application.job
        candidate_phone = candidate.phone
        candidate_name = candidate.full_name
        if not candidate_phone:
            raise ValueError("Candidate phone number is missing")
        if not session.scheduled_start:
            raise ValueError("Interview scheduled time is missing")
        interview_time = timezone.localtime(session.scheduled_start).strftime("%d %B %Y at %I:%M %p")
        if reminder.reminder_type == InterviewReminder.ReminderType.ONE_DAY:
            reminder_text = "in 24 hours"
        elif reminder.reminder_type == InterviewReminder.ReminderType.ONE_HOUR:
            reminder_text = "in 1 hour"
        else:
            raise ValueError("Unsupported reminder type")
        message = (
            f"Hello {candidate_name}. This is an automated interview "
            f"reminder from {job.title}. Your interview is scheduled "
            f"for {interview_time}. Your interview is {reminder_text} "
            "from now. Please be prepared. Thank you.")
        call_result = make_twilio_call(to_number=candidate_phone,message=message,voice="alice",language="en-US",
            status_callback=settings.TWILIO_STATUS_CALLBACK_URL,)
        if call_result.get("success"):
            reminder.voice_call_sid = call_result["call_sid"]
            reminder.voice_status = InterviewReminder.VoiceStatus.QUEUED
            reminder.voice_sent_at = timezone.now()
            reminder.voice_last_error = ""
            reminder.save(update_fields=["voice_call_sid","voice_status","voice_sent_at","voice_last_error",])
        return {"success": True,"message": "Voice call queued with Twilio",
            "call_sid": call_result["call_sid"],
            "provider_status": call_result["status"],}

    except Exception as exc:
        reminder.voice_last_error = str(exc)

        if self.request.retries >= self.max_retries:
            reminder.voice_status = InterviewReminder.VoiceStatus.FAILED
            reminder.save(
                update_fields=["voice_status", "voice_last_error"]
            )
            return {
                "success": False,
                "message": "Voice reminder failed",
                "error": str(exc),
            }
        reminder.voice_status = InterviewReminder.VoiceStatus.PROCESSING
        reminder.save(update_fields=["voice_status", "voice_last_error"])
        raise self.retry(exc=exc)

@shared_task
def scan_due_interview_reminders():
    from .models import InterviewReminder
    now=timezone.now()
    email_queued=0
    voice_queued=0
    due_email_ids=InterviewReminder.objects.filter(status=InterviewReminder.Status.PENDING,scheduled_for__lte=now).values_list("id",flat=True)
    for reminder_id in due_email_ids.iterator():
        claimed=InterviewReminder.objects.filter(id=reminder_id,status=InterviewReminder.Status.PENDING).update(status=InterviewReminder.Status.PROCESSING)
        if claimed:
            try:
                send_interview_reminder_task.delay(reminder_id)
                email_queued+=1
            except Exception:
                InterviewReminder.objects.filter(id=reminder_id,status=InterviewReminder.Status.PROCESSING).update(status=InterviewReminder.Status.PENDING)
    due_voice_ids=InterviewReminder.objects.filter(voice_status=InterviewReminder.VoiceStatus.PENDING,scheduled_for__lte=now).values_list("id",flat=True)
    for reminder_id in due_voice_ids.iterator():
        claimed=InterviewReminder.objects.filter(id=reminder_id,voice_status=InterviewReminder.VoiceStatus.PENDING).update(voice_status=InterviewReminder.VoiceStatus.PROCESSING)
        if claimed:
            try:
                send_interview_voice_reminder_task.delay(reminder_id)
                voice_queued+=1
            except Exception:
                InterviewReminder.objects.filter(id=reminder_id,voice_status=InterviewReminder.VoiceStatus.PROCESSING).update(voice_status=InterviewReminder.VoiceStatus.PENDING)

    return {"email_queued":email_queued,"voice_queued":voice_queued}






