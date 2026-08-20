from django.urls import path
from .views import SignupView,LogoutView,ProfileView,AdminTestView,EmployerTestView,CandidateTestView,CandidateProfileView,EmployerProfileView,CandidateListView,EmployerJobView,PublicJobListView,LatestJobListView

from rest_framework_simplejwt.views import TokenObtainPairView,TokenRefreshView


urlpatterns =[
    path("signup/",SignupView.as_view(),name="signup"),
    path("login/",TokenObtainPairView.as_view(),name="login"),
    path("token/refresh/",TokenRefreshView.as_view(),name="token_refresh"),
    path("logout/",LogoutView.as_view(),name="logout"),
    path("profile/",ProfileView.as_view(),name="profile"),
    path("admin-test/",AdminTestView.as_view(),name="admin_test"),
    path("employer-test/",EmployerTestView.as_view(),name="employer_test"),
    path("candidate-test/",CandidateTestView.as_view(),name="candidate_test"),
    path("candidate-profile/",CandidateProfileView.as_view(),name="candidate_profile"),
    path("employer-profile/",EmployerProfileView.as_view(),name="employer_profile"),
    path("candidates/",CandidateListView.as_view(),name="candidate_list"),
    path("employer-jobs/",EmployerJobView.as_view(),name="employer_jobsl"),
    path("employer-jobs/<int:job_id>/",EmployerJobView.as_view(),name="employer_jobs_deatail"),
    path("jobs/",PublicJobListView.as_view(),name="public_job_list"),
    path("jobs/latest/",LatestJobListView.as_view(),name="latest_jobs"),
]