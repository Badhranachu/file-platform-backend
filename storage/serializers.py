from rest_framework import serializers
from .models import Folder, File
from django.contrib.auth.hashers import make_password

class FolderSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(
        source="owner.username",
        read_only=True
    )

    owner_profile_photo = serializers.ImageField(
        source="owner.profile_photo",
        read_only=True
    )

    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True
    )

    subfolder_count = serializers.SerializerMethodField()
    file_count = serializers.SerializerMethodField()

    class Meta:
        model = Folder
        fields = [
            "id",
            "name",
            "description",
            "owner_username",
            "owner_profile_photo",
            "subfolder_count",
            "file_count",
            "is_public",
            "created_at",
            "parent",
            "password",  # 🔥 MUST INCLUDE THIS
        ]

    # ✅ CREATE (hash password)
    def create(self, validated_data):
        password = validated_data.pop("password", None)

        if password:
            validated_data["password"] = make_password(password)

        return super().create(validated_data)

    # ✅ UPDATE (important — handle password change)
    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)

        if password:
            instance.password = make_password(password)

        return super().update(instance, validated_data)

    # ✅ Recursive Folder Count
    def get_subfolder_count(self, obj):
        return self._count_subfolders(obj)

    def _count_subfolders(self, folder):
        total = folder.subfolders.count()
        for sub in folder.subfolders.all():
            total += self._count_subfolders(sub)
        return total

    # ✅ Recursive File Count
    def get_file_count(self, obj):
        return self._count_files(obj)

    def _count_files(self, folder):
        total = folder.file_set.count()
        for sub in folder.subfolders.all():
            total += self._count_files(sub)
        return total

class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = "__all__"

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["file"] = instance.file.url  # return relative path only
        return data