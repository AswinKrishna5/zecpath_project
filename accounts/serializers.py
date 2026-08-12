from rest_framework import serializers
from .models import CustomUser,CandidateProfile,EmployerProfile

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
    
    class Meta:
        model=CandidateProfile
        fields="id","full_name","phone","skills","education","experience","expected_salary","is_deleted",
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