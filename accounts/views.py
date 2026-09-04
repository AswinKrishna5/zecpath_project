from django.shortcuts import render
from rest_framework import generics,status
from rest_framework.permissions import AllowAny
from .serializers import SignupSerializers,CandidateProfileSerializer,EmployerProfileSerializer,JobSerializer,ApplicationSerializer,EmployerApplicationSerializer,SavedJobSerializer,ApplicationTimelineSerializer,ApplicationStatusNotificationSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import CandidateProfile,EmployerProfile,Job,Application,ApplicationAuditLog,SavedJob

from rest_framework_simplejwt.tokens import RefreshToken

from .permissions import IsAdmin,IsEmployer,IsCandidate,IsCandidateOrAdmin,IsEmployerOrAdmin

from .pagination import CandidatePagination,JobPagination

from django.db.models import Q

from .services import get_candidate_profile,get_employer_profile
from .workflow import is_valid_transition

# Create your views here.

class SignupView(generics.CreateAPIView):

    serializer_class=SignupSerializers
    permission_classes=[AllowAny]

class LogoutView(APIView):
    permission_classes=[AllowAny]

    def post(self,request):
        refresh_token=request.data.get("refresh")

        if not refresh_token:
            return Response({"error":"refresh token is requiered"},status=status.HTTP_400_BAD_REQUEST)

        try:
            token=RefreshToken(refresh_token)
            token.blacklist()

            return Response({"message":"logout succusfull"},status=status.HTTP_200_OK)

        except Exception:
            return Response({"error":"invalid or already blacklisted token"},status=status.HTTP_400_BAD_REQUEST)

class ProfileView(APIView):
    permission_classes=[IsAuthenticated]

    def get(self,request):
        user=request.user
        return Response({ "username": user.username,"email": user.email,"phone": user.phone,"role": user.role,"is_verified": user.is_verified,})

class AdminTestView(APIView):
    permission_classes=[IsAdmin]

    def get(self,request):
        return Response({"message":"welcome admin","username":request.user.username,"role":request.user.role, })

class EmployerTestView(APIView):
    permission_classes=[IsEmployer]

    def get(self,request):
        return Response({"message":"welcome employer","username":request.user.username,"role":request.user.role,})

class CandidateTestView(APIView):
    permission_classes=[IsCandidate] 

    def get(self,request):
        return Response({"message":"welcome candidate","username":request.user.username,"role":request.user.role,})

class CandidateProfileView(APIView):
    permission_classes=[IsCandidateOrAdmin]

    def post(self,request):
        if CandidateProfile.objects.filter(user=request.user,is_deleted=False).exists():
            return Response(
                {"detail":"profile already exist"},status=status.HTTP_400_BAD_REQUEST
            )
        serializer=CandidateProfileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data,status=status.HTTP_201_CREATED)

        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):

        user_id = request.query_params.get("user_id")
        profile,error=get_candidate_profile(request.user,user_id)
        if error:
            if error=="user id required for admin":
                return Response({"detail":error},status=status.HTTP_400_BAD_REQUEST)
            return Response({"detail":error},status=status.HTTP_404_NOT_FOUND)

        serializer=CandidateProfileSerializer(profile)
        return Response(serializer.data,status=status.HTTP_200_OK)
    

    def put(self, request):

        if request.user.role == "ADMIN":
            user_id = request.query_params.get("user_id")

            if not user_id:
                return Response({"detail": "user_id is required for admin."},status=status.HTTP_400_BAD_REQUEST)

            try:
                profile = CandidateProfile.objects.get(user_id=user_id,is_deleted=False)

            except CandidateProfile.DoesNotExist:
                return Response({"detail": "Candidate profile not found."},status=status.HTTP_404_NOT_FOUND)

        else:
            try:
                profile = CandidateProfile.objects.get(user=request.user,is_deleted=False)

            except CandidateProfile.DoesNotExist:
                 return Response({"detail": "Candidate profile not found."},status=status.HTTP_404_NOT_FOUND)

        old_resume_name = profile.resume.name if profile.resume else None

        serializer = CandidateProfileSerializer(profile,data=request.data)

        if serializer.is_valid():
            updated_profile = serializer.save()

        
            if "resume" in request.FILES and old_resume_name:
                if old_resume_name != updated_profile.resume.name:
                    old_resume_path = profile.resume.storage.path(old_resume_name)

                    if old_resume_path:
                        import os

                        if os.path.exists(old_resume_path):
                            os.remove(old_resume_path)

            response_serializer = CandidateProfileSerializer(updated_profile)

            return Response(response_serializer.data,status=status.HTTP_200_OK)

        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

    def delete(self,request):
        try:
            profile=CandidateProfile.objects.get(user=request.user,is_deleted=False)

        except CandidateProfile.DoesNotExist:
            return Response({"detail":"candidate profile not found"},status=status.HTTP_404_NOT_FOUND)
        
        profile.is_deleted=True
        profile.save()

        return Response({"detail": "Candidate profile deleted successfully."},status=status.HTTP_200_OK)

class EmployerProfileView(APIView):
    permission_classes=[IsEmployerOrAdmin]

    def post(self,request):
        if EmployerProfile.objects.filter(user=request.user,is_deleted=False).exists():
            return Response({"details":"employer profile already exist"},status=status.HTTP_400_BAD_REQUEST)

        serializer=EmployerProfileSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):

        user_id = request.query_params.get("user_id")
        profile,error=get_employer_profile(request.user,user_id)
        if error:
            if error=="user id required for admin":
                return Response({"detail":error},status=status.HTTP_400_BAD_REQUEST)
            return Response({"detail":error},status=status.HTTP_404_NOT_FOUND)
        
        serializer=EmployerProfileSerializer(profile)
        return Response(serializer.data,status=status.HTTP_200_OK)

    def put(self, request):

        if request.user.role == "ADMIN":
            user_id = request.query_params.get("user_id")

            if not user_id:
                return Response({"detail": "user_id is required for admin."},status=status.HTTP_400_BAD_REQUEST)

            try:
                 profile = EmployerProfile.objects.get(user_id=user_id,is_deleted=False)

            except EmployerProfile.DoesNotExist:
                return Response({"detail": "Employer profile not found."},status=status.HTTP_404_NOT_FOUND)

        else:
            try:
                profile = EmployerProfile.objects.get( user=request.user, is_deleted=False)
            
            except EmployerProfile.DoesNotExist:
                return Response({"detail": "Employer profile not found."},status=status.HTTP_404_NOT_FOUND)

        serializer = EmployerProfileSerializer(profile,data=request.data)

        if serializer.is_valid():
            serializer.save()

            return Response(serializer.data,status=status.HTTP_200_OK)

        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

class CandidateListView(APIView):
    permission_classes=[IsAdmin]

    def get(self,request):
        candidates=CandidateProfile.objects.select_related("user").all()

        role=request.query_params.get("role")
        if role:
            candidates=candidates.filter(user__role=role)

        created_after=request.query_params.get("created_after")
        if created_after:
            candidates=candidates.filter(user__created_at__date__gte=created_after)

        is_deleted=request.query_params.get("is_deleted")
        if is_deleted is not None:
                    candidates=candidates.filter(is_deleted=is_deleted.lower()=="true")
        else:
                    candidates=candidates.filter(is_deleted=False)

        search=request.query_params.get("search")
        if search:
            candidates=candidates.filter(Q(full_name__icontains=search)|Q(skills__icontains=search)|Q(experience__icontains=search)|
                                         Q(education__icontains=search))

        paginator=CandidatePagination()

        pagianted_candidates=paginator.paginate_queryset(candidates,request)
        serializer=CandidateProfileSerializer(pagianted_candidates,many=True)
        return paginator.get_paginated_response(serializer.data)

class EmployerJobView(APIView):
    permission_classes=[IsEmployer]

    def get(self,request):
        try:
            employer_profile=EmployerProfile.objects.get(user=request.user,is_deleted=False)
        except EmployerProfile.DoesNotExist:
            return Response({"detail":"employer is not exist"},status=status.HTTP_404_NOT_FOUND)
        jobs=Job.objects.filter(employer=employer_profile).order_by("-created_at")
        serializer=JobSerializer(jobs,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)
    
    def post(self,request):
        try:
            employer_profile=EmployerProfile.objects.get(user=request.user,is_deleted=False)
        except EmployerProfile.DoesNotExist:
            return Response({"detail":"employer profile does not found"},status=status.HTTP_404_NOT_FOUND)

        serializer=JobSerializer(data=request.data)
        if serializer.is_valid():
            job=serializer.save(employer=employer_profile)
            response_serializer=JobSerializer(job)
            return Response(response_serializer.data,status=status.HTTP_201_CREATED)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

    def put(self,request,job_id):
        try:
            employer_profile=EmployerProfile.objects.get(user=request.user,is_deleted=False)
        except EmployerProfile.DoesNotExist:
            return Response({"detail":"employer profile no found"},status=status.HTTP_404_NOT_FOUND)

        try:
            job=Job.objects.get(id=job_id,employer=employer_profile)
        except Job.DoesNotExist:
            return Response({"detail":"job not found or you do not own this job"},status=status.HTTP_404_NOT_FOUND)

        serializer=JobSerializer(job,data=request.data)
        if serializer.is_valid():
            updated_job=serializer.save()
            return Response(JobSerializer(updated_job).data,status=status.HTTP_200_OK)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

    def patch(self,request,job_id):
        try:
            employer_profile=EmployerProfile.objects.get(user=request.user,is_deleted=False)
        except EmployerProfile.DoesNotExist:
            return Response({"deatil":"employer is not found"},status=status.HTTP_404_NOT_FOUND)

        try:
            job=Job.objects.get(id=job_id,employer=employer_profile)
        except Job.DoesNotExist:
            return Response({"detail":"job is not found or you do not own this job"},status=status.HTTP_404_NOT_FOUND)

        new_status=request.data.get("status")
        if new_status not in ["ACTIVE","INACTIVE"]:
            return Response({"detail": "Status must be ACTIVE or INACTIVE."},status=status.HTTP_400_BAD_REQUEST)
        job.status=new_status
        job.save()

        return Response({"deatil":"job status updated sucessfully","status":job.status},status=status.HTTP_200_OK)
    

class PublicJobListView(APIView):
    def get(self,request):
        jobs=Job.objects.filter(status="ACTIVE").order_by("-created_at")
        skill=request.query_params.get("skill")
        if skill:
            jobs=jobs.filter(skills__icontains=skill)
        experience=request.query_params.get("experience")
        if experience:
            jobs=jobs.filter(experience__icontains=experience)
        salary_min=request.query_params.get("salary_min")
        if salary_min:
            jobs=jobs.filter(salary_max__gte=salary_min)
        location=request.query_params.get("location")
        if location:
            jobs=jobs.filter(location__icontains=location)
        job_type=request.query_params.get("job_type")
        if job_type:
            jobs=jobs.filter(job_type__icontains=job_type)
        search = request.query_params.get("search")
        if search:
            jobs = jobs.filter(Q(title__icontains=search) |Q(description__icontains=search) |Q(skills__icontains=search) |Q(location__icontains=search)
    )
        paginator=JobPagination()
        page=paginator.paginate_queryset(jobs,request)
        serializer=JobSerializer(page,many=True)
        return paginator.get_paginated_response(serializer.data)


class LatestJobListView(APIView):
    def get(self,request):
        jobs=Job.objects.filter(status="ACTIVE").order_by("-created_at")
        paginator=JobPagination()
        page=paginator.paginate_queryset(jobs,request)
        serializer=JobSerializer(page,many=True)
        return paginator.get_paginated_response(serializer.data)    
            
class ApplyJobView(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request,job_id):
        if request.user.role !="CANDIDATE":
            return Response({"detail":"only candidate can apply for jobs"},status=status.HTTP_403_FORBIDDEN)
        try:
            candidate=request.user.candidate_profile
        except CandidateProfile.DoesNotExist:
            return Response({"detail":"candidate profile not found"},status=status.HTTP_404_NOT_FOUND)
        try:
            job=Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            return Response({"detail":"job not found"},status=status.HTTP_404_NOT_FOUND)
        if job.status !=Job.Status.ACTIVE:
            return Response({"detail":"this job is not active"},status=status.HTTP_400_BAD_REQUEST)
        if not candidate.resume:
            return Response({"detail":"please upload a resume before applying"},status=status.HTTP_400_BAD_REQUEST)
        if Application.objects.filter(candidate=candidate,job=job).exists():
            return Response({"detail":"you have already applied for this job"},status=status.HTTP_400_BAD_REQUEST)
        application=Application.objects.create(candidate=candidate,job=job,resume_snapshot=candidate.resume,status=Application.Status.APPLIED)
        ApplicationAuditLog.objects.create(application=application,actor=request.user,old_status=None,new_status=Application.Status.APPLIED)
        return Response({"detail":"application submitted successfully"},status=status.HTTP_201_CREATED)

class MyApplicationListView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        if request.user.role != "CANDIDATE":
            return Response({"detail":"only candidates can view applications "},status=status.HTTP_403_FORBIDDEN)
        try :
            candidate=request.user.candidate_profile
        except CandidateProfile.DoesNotExist:
            return Response({"detail":"candidate profile does not find"},status=status.HTTP_404_NOT_FOUND)
        application=Application.objects.filter(candidate=candidate).select_related("job").order_by("-applied_at")
        serializer=ApplicationSerializer(application,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)


class EmployerApplicationStatusView(APIView):
    permission_classes=[IsAuthenticated]
    def patch(self,request,application_id):
        if request.user.role !="EMPLOYER":
            return Response({"detail":"only employer can update application status"},status=status.HTTP_403_FORBIDDEN)
        try:
            application=Application.objects.select_related("job","job__employer").get(id=application_id)
        except Application.DoesNotExist:
            return Response({"detail":"application not found"},status=status.HTTP_404_NOT_FOUND)
        if application.job.employer.user !=request.user:
            return Response({"detail":"you do not have permission to update this application "},status=status.HTTP_403_FORBIDDEN)
        new_status=request.data.get("status")
        if not new_status:
            return Response({"detail":"status is required"},status=status.HTTP_400_BAD_REQUEST)
        current_status=application.status
        if not is_valid_transition(current_status,new_status):
            return Response({"detail":"invalid staus transition "},status=status.HTTP_400_BAD_REQUEST)
        application.status=new_status
        application.save(update_fields=["status"])
        ApplicationAuditLog.objects.create(application=application,actor=request.user,old_status=current_status,new_status=new_status)
        return Response({"message":"application status updated succesfully","status":application.status},status=status.HTTP_200_OK) 
           
class EmployerApplicationListView(APIView):
    permission_classes=[IsEmployer]

    def get(self,request,job_id):
        try:
            employer_profile=EmployerProfile.objects.get(user=request.user,is_deleted=False)
        except EmployerProfile.DoesNotExist:
            return Response({"detail":"employer does not exist"},status=status.HTTP_404_NOT_FOUND)
        try:
            job=Job.objects.get(id=job_id,employer=employer_profile)
        except Job.DoesNotExist:
            return Response({"deatail":"job not found or you do not own this job"},status=status.HTTP_404_NOT_FOUND)
        application=Application.objects.filter(job=job).select_related("candidate").order_by("-applied_at")
        status_filter=request.query_params.get("status")
        if status_filter:
            if status_filter not in Application.Status.values:
                return Response({"detail": "Invalid application status."},status=status.HTTP_400_BAD_REQUEST)
            application=application.filter(status=status_filter)
        search=request.query_params.get("search")
        if search:
            application=application.filter(Q(candidate__full_name__icontains=search)|Q(candidate__skills__icontains=search)|Q(candidate__experience__icontains=search)|Q(candidate__education__icontains=search))
        serializer=EmployerApplicationSerializer(application,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)

class EmployerJobAnalyticsView(APIView):
    permission_classes=[IsEmployer]

    def get(self,request,job_id):
        try:
            employer_profile=EmployerProfile.objects.get(user=request.user,is_deleted=False)
        except EmployerProfile.DoesNotExist:
            return Response({"detail":"employer profile not found"},status=status.HTTP_404_NOT_FOUND)
        try:
            job=Job.objects.get(id=job_id,employer=employer_profile)
        except Job.DoesNotExist:
            return Response({"detail":"job not found or you do not own this job"},status=status.HTTP_404_NOT_FOUND)
        applications=Application.objects.filter(job=job)
        total_applications=applications.count()
        applied=applications.filter(status=Application.Status.APPLIED).count()
        shortlisted=applications.filter(status=Application.Status.SHORTLISTED).count()
        interview=applications.filter(status=Application.Status.INTERVIEW).count()
        selected=applications.filter(status=Application.Status.SELECTED).count()
        rejected=applications.filter(status=Application.Status.REJECTED).count()
        if total_applications > 0:
            shortlist_ratio=(shortlisted/total_applications)*100
        else:
            shortlist_ratio=0

        return Response({"total_applications":total_applications,"applied": applied,"shortlisted": shortlisted,"interview": interview,
        "selected": selected,"rejected": rejected,"shortlist_ratio": shortlist_ratio,},status=status.HTTP_200_OK)
    
class SaveJobView(APIView):
    permission_classes=[IsCandidate]
    
    def post(self,request,job_id):
        try :
            candidate_profile=CandidateProfile.objects.get(user=request.user,is_deleted=False)
        except CandidateProfile.DoesNotExist:
            return Response({"detail":"candidate not found"},status=status.HTTP_404_NOT_FOUND)
        try:
            job=Job.objects.get(id=job_id,status=Job.Status.ACTIVE)
        except Job.DoesNotExist:
            return Response({"detail":"job not found"},status=status.HTTP_404_NOT_FOUND)
        saved_job,created=SavedJob.objects.get_or_create(candidate=candidate_profile,job=job)
        if not created:
            return  Response({"detail":"job is already saved"},status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail":"job saved succesfully"},status=status.HTTP_201_CREATED)
    def delete(self,request,job_id):
        try :
            candidate_profile=CandidateProfile.objects.get(user=request.user,is_deleted=False)
        except CandidateProfile.DoesNotExist:
            return Response({"detail":"candidate profile not found"},status=status.HTTP_404_NOT_FOUND)
        deleted_count,_=SavedJob.objects.filter(candidate=candidate_profile,job_id=job_id).delete()
        if deleted_count==0:
            return Response({"detail":"saved job not found"},status=status.HTTP_404_NOT_FOUND)
        return Response({"detail":"job unsaved succesfully"},status=status.HTTP_200_OK)

class SavedJobListView(APIView):
    permission_classes=[IsCandidate]

    def get(self,request):
        try:
            candidate_profile=CandidateProfile.objects.get(user=request.user,is_deleted=False)
        except CandidateProfile.DoesNotExist:
            return Response({"detail":"candidate not found"},status=status.HTTP_404_NOT_FOUND)
        
        saved_jobs=SavedJob.objects.filter(candidate=candidate_profile).select_related("job","job__employer").order_by("-saved_at")
        serializer=SavedJobSerializer(saved_jobs,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)
    

class RecommendedJobListView(APIView):
    permission_classes=[IsCandidate]

    def get(self,request):
        try:
            candidate_profile=CandidateProfile.objects.get(user=request.user,is_deleted=False)
        except CandidateProfile.DoesNotExist:
            return Response({"detail":"candidate profile not found"},status=status.HTTP_404_NOT_FOUND)
        candidate_skills=[skill.strip().lower()
                          for skill in candidate_profile.skills.split(",")
                          if skill.strip()]
        if not candidate_skills:
            return Response([],status=status.HTTP_200_OK)
        jobs=Job.objects.filter(status=Job.Status.ACTIVE).select_related("employer")
        recommended_jobs=[]
        for job in jobs:
            job_skills=[skill.strip().lower()
            for skill in job.skills.split(",")
            if skill.strip()]

            matched_skills=set(candidate_skills) & set(job_skills)
            if matched_skills:
                match_score=(len(matched_skills)/len(candidate_skills))*100
                recommended_jobs.append({"id":job.id,"title":job.title,"company":job.employer.company_name,"location":job.location,"job_type":job.job_type,"matched_skill":list(matched_skills),"match_score":round(match_score,2)})
        recommended_jobs.sort(key=lambda job: job["match_score"],reverse=True)
        return Response(recommended_jobs,status=status.HTTP_200_OK)


class ApplicationTimelineView(APIView):
    permission_classes=[IsCandidate]

    def get(self,request,application_id):
        try:
            candidate_profile = CandidateProfile.objects.get(user=request.user,is_deleted=False)
        except CandidateProfile.DoesNotExist:
            return Response({"detail": "Candidate profile not found."},status=status.HTTP_404_NOT_FOUND)
        try:
            application=Application.objects.get(id=application_id,candidate=candidate_profile)
        except Application.DoesNotExist:
            return Response({"detail":"application not found"},status=status.HTTP_404_NOT_FOUND)
        audit_logs = application.audit_log.all().order_by("created_at")
        serializer=ApplicationTimelineSerializer(audit_logs,many=True)
        return Response({"application_id":application.id,"job_title":application.job.title,"current_status":application.status,"timeline":serializer.data},status=status.HTTP_200_OK)
        
class ApplicationStatusNotificationView(APIView):
    permission_classes=[IsCandidate]

    def get(self,request):
        try:
            candidate_profile = CandidateProfile.objects.get(user=request.user,is_deleted=False)
        except CandidateProfile.DoesNotExist:
            return Response({"detail": "Candidate profile not found."},status=status.HTTP_404_NOT_FOUND)
        notifications=ApplicationAuditLog.objects.filter(application__candidate=candidate_profile).select_related("application","application__job").order_by("-created_at")
        serializer=ApplicationStatusNotificationSerializer(notifications,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)
