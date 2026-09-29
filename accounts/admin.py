from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser, CandidateProfile, EmployerProfile,Job,Application,SavedJob,ApplicationAuditLog,AccountFlag,EmailLog,AIInterviewSession,AICall,AIQuestion,AIAnswer,CallLog


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):

    list_display = (
        "username","email", "role", "is_active", "is_verified",
    )

    list_filter = (
        "role","is_active","is_verified",
    )

    fieldsets = (
        (None, {
            "fields": (
                "username",
                "password",
            ),
        }),

        ("Personal info", {
            "fields": (
                "first_name","last_name", "email","phone","role",
            ),
        }),

        ("Verification", {
            "fields": (
                "is_verified",
            ),
        }),

        ("Permissions", {
            "fields": ( "is_active","is_staff","is_superuser","groups","user_permissions",
            ),
        }),

        ("Important dates", {
            "fields": (
                "last_login","date_joined", 
            ),
        }),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ( "username",  "email",  "password1","password2","phone", "role",  "is_verified",
            ),
        }),
    )

@admin.register(CandidateProfile)
class CandidateProfileAdmin(admin.ModelAdmin):

    list_display = ( "full_name", "user", "phone",
    )


@admin.register(EmployerProfile)
class EmployerProfileAdmin(admin.ModelAdmin):

    list_display = (
        "company_name","user","location",  
    )


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):

    list_display = (
        "employer","title","description","location", "skills","experience","salary_min","salary_max",
        "status","job_type","created_at","updated_at"
    )

@admin.register(Application)
class ApplictionAdmin(admin.ModelAdmin):

    list_display = (
        "candidate","job","status","resume_snapshot","applied_at"
    )

@admin.register(SavedJob)
class SavedJobAdmin(admin.ModelAdmin):
    list_display=("id","candidate","job","saved_at")
    list_filter=("saved_at",)

@admin.register(ApplicationAuditLog)
class ApplicationAuditLogAdmin(admin.ModelAdmin):
    list_display=("id","application","actor","old_status","new_status","created_at",)

@admin.register(AccountFlag)
class AccountFlagAdmin(admin.ModelAdmin):
    list_display=("id","user","reason","created_at",)

@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display=("id","application","recipient","subject","status","created_at",)
    list_filter=("status","created_at")
    search_fields=("recipient","subject")

@admin.register(AIInterviewSession)
class AIInterviewSessionAdmin(admin.ModelAdmin):
    list_display = ( "id","ai_call","status","started_at","ended_at","created_at",
    )

    list_filter = ("status", "created_at")
    search_fields = ("ai_call__application__id",)
    readonly_fields = ("created_at",)


@admin.register(AIQuestion)
class AIQuestionAdmin(admin.ModelAdmin):
    list_display = ("id","session","question_order","created_at",
    )

    list_filter = ("created_at",)
    search_fields = ("question_text",)
    ordering = ("session", "question_order")
    readonly_fields = ("created_at",)


@admin.register(AIAnswer)
class AIAnswerAdmin(admin.ModelAdmin):
    list_display = ("id","question","answered_at","created_at",
    )

    search_fields = ("answer_text",)
    readonly_fields = ("created_at",)


@admin.register(CallLog)
class CallLogAdmin(admin.ModelAdmin):
    list_display = ("id","ai_call","event","triggered_by","created_at",
    )

    list_filter = ("event", "created_at")
    search_fields = ("event", "details", "reason","triggered_by__username")
    readonly_fields = ("created_at",)

@admin.register(AICall)
class AICallAdmin(admin.ModelAdmin):
    list_display = ("id","application","status","created_at","started_at")

    list_filter = ("status", "created_at")
    search_fields = ("status","started_at")
    readonly_fields = ("created_at",)