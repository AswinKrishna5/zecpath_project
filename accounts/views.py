from django.shortcuts import render
from rest_framework import generics,status
from rest_framework.permissions import AllowAny
from .serializers import SignupSerializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from rest_framework_simplejwt.tokens import RefreshToken

from .permissions import IsAdmin,IsEmployer,IsCandidate

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