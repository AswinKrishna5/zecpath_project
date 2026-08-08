from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        EMPLOYER = "EMPLOYER", "Employer"
        CANDIDATE = "CANDIDATE", "Candidate"

    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True)

    role = models.CharField(max_length=20,choices=Role.choices,default=Role.CANDIDATE)

    is_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class CandidateProfile(models.Model):

    user = models.OneToOneField(CustomUser,on_delete=models.CASCADE,related_name="candidate_profile")

    full_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=15, blank=True)
    skills = models.TextField(blank=True)

    def __str__(self):
        return self.full_name


class EmployerProfile(models.Model):

    user = models.OneToOneField(CustomUser,on_delete=models.CASCADE,related_name="employer_profile")

    company_name = models.CharField(max_length=50)
    location = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return self.company_name