from rest_framework import serializers
from .models import CustomUser,CandidateProfile,EmployerProfile,Job,Application,SavedJob,ApplicationAuditLog

class SignupSerializers(serializers.ModelSerializer):
    class Meta:
        model=CustomUser
        fields=("username","email","password","phone","role",)
        extra_kwargs={
            "password":{
                "write_only":True
            }
        }

    def create(self, validated_data):
        user=CustomUser.objects.create_user(username=validated_data["username"],email=validated_data["email"],password=validated_data["password"],phone=validated_data.get('phone', ""),role=validated_data.get("role",CustomUser.Role.CANDIDATE),)

        return user

class CandidateProfileSerializer(serializers.ModelSerializer):
    def validate_phone(self,value):
        if value and not value.isdigit():
            raise serializers.ValidationError("phine must contain only digits")

        if value and len(value) !=10:
            raise serializers.ValidationError("must contain 10 digits")

        return value
    
    def validate_expected_salary(self,value):
        if value is not None and value<=0:
            raise serializers.ValidationError("cannot be minus")

        return value

    def validate_full_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Full name cannot be empty.")

        return value

    def validate_resume(self,value):
        allowed_extensions=[".pdf",".doc",".docx"]
        file_name=value.name.lower()
        if not any(file_name.endswith(ext) for ext in allowed_extensions):
            raise serializers.ValidationError("only pdf,doc,docx files are allowed")

        max_size=5*1024*1024
        if value.size>max_size:
            raise serializers.ValidationError("size should below 5 mb")

        return value
    
    class Meta:
        model=CandidateProfile
        fields="id","full_name","phone","skills","education","experience","expected_salary","resume","is_deleted",
        read_only_fields="id","is_deleted"


class EmployerProfileSerializer(serializers.ModelSerializer):
    def validate_company_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Company name cannot be empty.")

        return value

    def validate_company_size(self, value):
        allowed_sizes = ["1-10","11-50","51-200","201-500","501-1000","1000+",]

        if value and value not in allowed_sizes:
            raise serializers.ValidationError("Invalid company size." )

        return value
    
    class Meta:
        model=EmployerProfile
        fields="id","company_name","location","domain","company_size","is_verified","is_deleted",
        read_only_fields="id","is_verified","is_deleted"

class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model=Job
        fields="id","title","description","skills","experience","salary_min","salary_max","location","job_type","status","created_at","updated_at"
        read_only_fields="id","status","created_at","updated_at"

class ApplicationSerializer(serializers.ModelSerializer):
    job_title=serializers.CharField(source="job.title",read_only=True)
    company=serializers.CharField(source="job.employer.company_name",read_only=True)
    class Meta:
        model=Application
        fields= "id","job","job_title","company","status","applied_at"
        read_only_fields="id","job_title","company","status","applied_at"

class EmployerApplicationSerializer(serializers.ModelSerializer):
    candidate_name=serializers.CharField(source="candidate.full_name",read_only=True)
    candidate_skills=serializers.CharField(source="candidate.skills",read_only=True)
    candidate_education=serializers.CharField(source="candidate.eduacation",read_only=True)
    candidate_experience=serializers.CharField(source="candidate.experience",read_only=True)
    expected_salary=serializers.DecimalField(source="candidate.expected_salary",max_digits=10,decimal_places=2,read_only=True)
    resume=serializers.FileField(source="resume_snapshot",read_only=True)
    class Meta:
        model=Application
        fields= "id","candidate_name","candidate_skills","candidate_education","candidate_experience","expected_salary","resume","status","applied_at"
        read_only_fields=fields

class SavedJobSerializer(serializers.ModelSerializer):
    title=serializers.CharField(source="job.title",read_only=True)
    company=serializers.CharField(source="job.employer.company_name",read_only=True)
    location=serializers.CharField(source="job.location",read_only=True)
    job_type=serializers.CharField(source="job.job_type",read_only=True)
    class Meta:
        model=SavedJob
        fields=("id","job","title","company","location","job_type","saved_at")
        read_only_fields=fields

class ApplicationTimelineSerializer(serializers.ModelSerializer):
    class Meta:
        model=ApplicationAuditLog
        fields=("old_status","new_status","created_at")
        read_only_fields=fields


class ApplicationStatusNotificationSerializer(serializers.ModelSerializer):
    job_title=serializers.CharField(source="application.job.title",read_only=True)
    class Meta:
        model=ApplicationAuditLog
        fields=("id","application","job_title","old_status","new_status","created_at")
        read_only_fields=fields
        