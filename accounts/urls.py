from django.urls import path
from .views import SignupView,LogoutView,ProfileView,AdminTestView,EmployerTestView,CandidateTestView

from rest_framework_simplejwt.views import TokenObtainPairView,TokenRefreshView


urlpatterns =[
    path("signup/",SignupView.as_view(),name="signup"),
    path("login/",TokenObtainPairView.as_view(),name="login"),
    path("token/refresh/",TokenRefreshView.as_view(),name="token_refresh"),
    path("logout/",LogoutView.as_view(),name="logout"),
    path("profile/",ProfileView.as_view(),name="profile"),
    path("admin-test/",AdminTestView.as_view(),name="admin_test"),
    path("employer-test/",EmployerTestView.as_view(),name="employer_test"),
    path("candidate-test/",CandidateTestView.as_view(),name="candidate_test")
]