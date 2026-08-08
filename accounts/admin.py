from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser, CandidateProfile, EmployerProfile


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
