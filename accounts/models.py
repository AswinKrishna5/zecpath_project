from django.contrib.auth.models import AbstractUser
from django.db import models
import os
import uuid

def resume_upload_path(instance,filename):
    extention=os.path.splitext(filename)[1].lower()
    return f"resumes/{instance.user.username}_{uuid.uuid4().hex}{extention}"

class CustomUser(AbstractUser):

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        EMPLOYER = "EMPLOYER", "Employer"
        CANDIDATE = "CANDIDATE", "Candidate"

    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True)

    role = models.CharField(max_length=20,choices=Role.choices,default=Role.CANDIDATE)

    is_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True,db_index=True)
    updated_at = models.DateTimeField(auto_now=True)


class CandidateProfile(models.Model):

    user = models.OneToOneField(CustomUser,on_delete=models.CASCADE,related_name="candidate_profile")

    full_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=15, blank=True)
    skills = models.TextField(blank=True)
    education=models.TextField(blank=True)
    experience=models.TextField(blank=True)
    resume=models.FileField(upload_to=resume_upload_path,blank=True,null=True)
    expected_salary=models.DecimalField(max_digits=10,decimal_places=2,null=True,blank=True)
    is_deleted=models.BooleanField(default=False)

    def __str__(self):
        return self.full_name


class EmployerProfile(models.Model):

    user = models.OneToOneField(CustomUser,on_delete=models.CASCADE,related_name="employer_profile")

    company_name = models.CharField(max_length=50)
    domain=models.CharField(max_length=100,blank=True)
    location = models.CharField(max_length=50, blank=True)
    company_size=models.CharField(max_length=50,blank=True)
    is_verified=models.BooleanField(default=False)
    is_deleted=models.BooleanField(default=False)

    def __str__(self):
        return self.company_name

class Job(models.Model):
    employer=models.ForeignKey(EmployerProfile,on_delete=models.CASCADE,related_name="jobs")
    title=models.CharField(max_length=200)
    description=models.TextField()
    skills=models.TextField()
    experience=models.CharField(max_length=100)
    salary_min=models.DecimalField(max_digits=10,decimal_places=2)
    salary_max=models.DecimalField(max_digits=10,decimal_places=2)
    location=models.CharField(max_length=200)

    class JobType(models.TextChoices):
        FULL_TIME="FULL_TIME","full time"
        PART_TIME = "PART_TIME", "Part Time"
        CONTRACT = "CONTRACT", "Contract"
        INTERNSHIP = "INTERNSHIP", "Internship"

    job_type=models.CharField(max_length=20,choices=JobType.choices)

    class Status(models.TextChoices):
        ACTIVE="ACTIVE","active"
        INACTIVE="INACTIVE","inactive"

    status=models.CharField(max_length=20,choices=Status.choices,default=Status.ACTIVE)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)

    class Meta:
        indexes=models.Index(fields=["status"]),models.Index(fields=["location"]),models.Index(fields=["job_type"]),models.Index(fields=["created_at"]),


class Application(models.Model):
    candidate=models.ForeignKey(CandidateProfile,on_delete=models.CASCADE,related_name="applications")
    job=models.ForeignKey(Job,on_delete=models.CASCADE,related_name="applications")
    resume_snapshot=models.FileField(upload_to="application_resumes/")
    class Status(models.TextChoices):
        APPLIED = "APPLIED", "Applied"
        SHORTLISTED = "SHORTLISTED", "Shortlisted"
        INTERVIEW = "INTERVIEW", "Interview"
        SELECTED = "SELECTED", "Selected"
        REJECTED = "REJECTED", "Rejected"
    status=models.CharField(max_length=20,choices=Status.choices,default=Status.APPLIED)
    applied_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.candidate.full_name}-{self.job.title}"
    

