from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password

User = get_user_model()


# ✅ Registration Serializer
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    public_password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "is_public",
            "public_password",
        ]

    def create(self, validated_data):
        if validated_data.get("public_password"):
            validated_data["public_password"] = make_password(
                validated_data["public_password"]
            )

        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email"),
            password=validated_data["password"],
        )

        user.is_public = validated_data.get("is_public", True)
        user.public_password = validated_data.get("public_password")
        user.save()

        return user


# ✅ Profile Serializer
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "is_public",
            "profile_photo",
        ]