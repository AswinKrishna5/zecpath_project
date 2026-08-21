from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser, CandidateProfile, EmployerProfile,Job,Application


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):

    list_display = (
        "username",
        "email",
        "role",
        "is_active",
        "is_verified",
    )

    list_filter = (
        "role",
        "is_active",
        "is_verified",
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
                "first_name",
                "last_name",
                "email",
                "phone",
                "role",
            ),
        }),

        ("Verification", {
            "fields": (
                "is_verified",
            ),
        }),

        ("Permissions", {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            ),
        }),

        ("Important dates", {
            "fields": (
                "last_login",
                "date_joined",
                
            ),
        }),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "username",
                "email",
                "password1",
                "password2",
                "phone",
                "role",
                "is_verified",
            ),
        }),
    )

@admin.register(CandidateProfile)
class CandidateProfileAdmin(admin.ModelAdmin):

    list_display = (
        "full_name",
        "user",
        "phone",
    )


@admin.register(EmployerProfile)
class EmployerProfileAdmin(admin.ModelAdmin):

    list_display = (
        "company_name",
        "user",
        "location",
        
    )


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):

    list_display = (
        "employer",
        "title",
        "description",
        "location",
        "skills",
        "experience",
        "salary_min",
        "salary_max",
        "status",
        "job_type",
        "created_at",
        "updated_at"
    )

@admin.register(Application)
class ApplictionAdmin(admin.ModelAdmin):

    list_display = (
        "candidate",
        "job",
        "status",
        "resume_snapshot",
        "applied_at"
      
    )