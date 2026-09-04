from django.urls import path
from .views import(SignupView,LogoutView,ProfileView,AdminTestView,EmployerTestView,CandidateTestView,EmployerJobAnalyticsView,
                   CandidateProfileView,EmployerProfileView,CandidateListView,EmployerJobView,PublicJobListView,SaveJobView,
                   LatestJobListView,ApplyJobView,MyApplicationListView,EmployerApplicationStatusView,EmployerApplicationListView,
                   SavedJobListView,RecommendedJobListView,ApplicationTimelineView,ApplicationStatusNotificationView)

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
    path("jobs/<int:job_id>/apply/",ApplyJobView.as_view(),name="apply_job"),
    path("applications/",MyApplicationListView.as_view(),name="my_application"),
    path("employer/applications/<int:application_id>/status/",EmployerApplicationStatusView.as_view(),name="employer_application_status"),
    path("employer/jobs/<int:job_id>/applications/",EmployerApplicationListView.as_view(),name="employer_application_list"),
    path("employer/jobs/<int:job_id>/analytics/",EmployerJobAnalyticsView.as_view(),name="employer_job_analytics"),
    path("jobs/<int:job_id>/save/",SaveJobView.as_view(),name="save_job"),
    path("saved-jobs/",SavedJobListView.as_view(),name="saved_job_list"),
    path("recommended-jobs/",RecommendedJobListView.as_view(),name="recommended_jobs"),
    path("applications/<int:application_id>/timeline/",ApplicationTimelineView.as_view(),name="application_timeline"),
    path(
    "application-notifications/",ApplicationStatusNotificationView.as_view(),name="application_notifications"),
]