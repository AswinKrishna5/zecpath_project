from rest_framework import serializers
from .models import CustomUser

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