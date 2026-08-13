from django.shortcuts import render
from rest_framework import generics,status
from rest_framework.permissions import AllowAny
from .serializers import SignupSerializers,CandidateProfileSerializer,EmployerProfileSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import CandidateProfile,EmployerProfile

from rest_framework_simplejwt.tokens import RefreshToken

from .permissions import IsAdmin,IsEmployer,IsCandidate,IsCandidateOrAdmin,IsEmployerOrAdmin

# Create your views here.

class SignupView(generics.CreateAPIView):

    serializer_class=SignupSerializers
    permission_classes=[AllowAny]

class LogoutView(APIView):
    permission_classes=[AllowAny]

    def post(self,request):
        refresh_token=request.data.get("refresh")

        if not refresh_token:
            return Response({
                "error":"refresh token is requiered"
            },status=status.HTTP_400_BAD_REQUEST)

        try:
            token=RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                {"message":"logout succusfull"},status=status.HTTP_200_OK
            )

        except Exception:
            return Response(
                {"error":"invalid or already blacklisted token"},status=status.HTTP_400_BAD_REQUEST
            )

class ProfileView(APIView):
    permission_classes=[IsAuthenticated]

    def get(self,request):
        user=request.user
        return Response({ "username": user.username,
            "email": user.email,
            "phone": user.phone,
            "role": user.role,
            "is_verified": user.is_verified,})

class AdminTestView(APIView):
    permission_classes=[IsAdmin]

    def get(self,request):
        return Response({
            "message":"welcome admin","username":request.user.username,"role":request.user.role,
        })

class EmployerTestView(APIView):
    permission_classes=[IsEmployer]

    def get(self,request):
        return Response(
            {"message":"welcome employer","username":request.user.username,"role":request.user.role,}
        )

class CandidateTestView(APIView):
    permission_classes=[IsCandidate] 

    def get(self,request):
        return Response({
            "message":"welcome candidate","username":request.user.username,"role":request.user.role,
            })

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
                profile = CandidateProfile.objects.get(user=request.user,is_deleted=False
                                                       )
            except CandidateProfile.DoesNotExist:
                return Response({"detail": "Candidate profile not found."},status=status.HTTP_404_NOT_FOUND)

        serializer = CandidateProfileSerializer(profile)

        return Response(serializer.data,status=status.HTTP_200_OK)

    def put(self, request):

        if request.user.role == "ADMIN":
            user_id = request.query_params.get("user_id")

            if not user_id:
                return Response(
                {"detail": "user_id is required for admin."},
                status=status.HTTP_400_BAD_REQUEST
            )

            try:
                profile = CandidateProfile.objects.get(
                user_id=user_id,
                is_deleted=False
            )

            except CandidateProfile.DoesNotExist:
                return Response(
                {"detail": "Candidate profile not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        else:
            try:
                profile = CandidateProfile.objects.get(
                user=request.user,
                is_deleted=False
            )

            except CandidateProfile.DoesNotExist:
                 return Response(
                {"detail": "Candidate profile not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        old_resume_name = profile.resume.name if profile.resume else None

        serializer = CandidateProfileSerializer(
        profile,
        data=request.data
    )

        if serializer.is_valid():
            updated_profile = serializer.save()

        
            if "resume" in request.FILES and old_resume_name:
                if old_resume_name != updated_profile.resume.name:
                    old_resume_path = profile.resume.storage.path(
                    old_resume_name
                )

                    if old_resume_path:
                        import os

                        if os.path.exists(old_resume_path):
                            os.remove(old_resume_path)

            response_serializer = CandidateProfileSerializer(
            updated_profile
        )

            return Response(
            response_serializer.data,
            status=status.HTTP_200_OK
        )

        return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )

    def delete(self,request):
        try:
            profile=CandidateProfile.objects.get(user=request.user,is_deleted=False)
        except CandidateProfile.DoesNotExist:
            return Response({"details":"candidate profile not found"},status=status.HTTP_404_NOT_FOUND)
        
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

        if request.user.role == "ADMIN":
            user_id = request.query_params.get("user_id")

            if not user_id:
                return Response(
                {"detail": "user_id is required for admin."},
                status=status.HTTP_400_BAD_REQUEST
            )

            try:
                profile = EmployerProfile.objects.get(
                user_id=user_id,
                is_deleted=False
            )
            except EmployerProfile.DoesNotExist:
                return Response(
                {"detail": "Employer profile not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        else:
            try:
                profile = EmployerProfile.objects.get(
                user=request.user,
                is_deleted=False
            )
            except EmployerProfile.DoesNotExist:
                return Response(
                {"detail": "Employer profile not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = EmployerProfileSerializer(profile)

        return Response(
        serializer.data,
        status=status.HTTP_200_OK
    )

    def put(self, request):

        if request.user.role == "ADMIN":
            user_id = request.query_params.get("user_id")

            if not user_id:
                return Response(
                {"detail": "user_id is required for admin."},
                status=status.HTTP_400_BAD_REQUEST
            )

            try:
                 profile = EmployerProfile.objects.get(
                user_id=user_id,
                is_deleted=False
            )
            except EmployerProfile.DoesNotExist:
                return Response(
                {"detail": "Employer profile not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        else:
            try:
                profile = EmployerProfile.objects.get(
                user=request.user,
                is_deleted=False
            )
            except EmployerProfile.DoesNotExist:
                return Response(
                {"detail": "Employer profile not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = EmployerProfileSerializer(
            profile,
        data=request.data
    )

        if serializer.is_valid():
            serializer.save()

            return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

        return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )