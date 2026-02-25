from django.contrib.auth.hashers import make_password
from rest_framework import serializers

from .models import File, FileComment, Folder, FolderComment, FolderMessage


class FolderSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source="owner.username", read_only=True)
    owner_profile_photo = serializers.ImageField(source="owner.profile_photo", read_only=True)
    owner_id = serializers.IntegerField(source="owner.id", read_only=True)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    subfolder_count = serializers.SerializerMethodField()
    file_count = serializers.SerializerMethodField()
    folder_code = serializers.CharField(read_only=True)
    view_count = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()

    class Meta:
        model = Folder
        fields = [
            "id",
            "name",
            "description",
            "owner_username",
            "owner_id",
            "owner_profile_photo",
            "subfolder_count",
            "file_count",
            "view_count",
            "like_count",
            "comment_count",
            "is_liked",
            "is_public",
            "is_listed_in_feed",
            "created_at",
            "parent",
            "password",
            "folder_code",
        ]

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        if password:
            validated_data["password"] = make_password(password)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        if password is not None:
            if password == "":
                instance.password = None
            else:
                instance.password = make_password(password)
        return super().update(instance, validated_data)

    def get_subfolder_count(self, obj):
        if not self._can_show_counts(obj):
            return None
        return self._count_subfolders(obj)

    def _count_subfolders(self, folder):
        total = folder.subfolders.count()
        for sub in folder.subfolders.all():
            total += self._count_subfolders(sub)
        return total

    def get_file_count(self, obj):
        if not self._can_show_counts(obj):
            return None
        return self._count_files(obj)

    def _count_files(self, folder):
        total = folder.file_set.count()
        for sub in folder.subfolders.all():
            total += self._count_files(sub)
        return total

    def get_view_count(self, obj):
        return obj.views.count()

    def get_like_count(self, obj):
        return obj.liked_by.count()

    def get_is_liked(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.liked_by.filter(id=request.user.id).exists()

    def get_comment_count(self, obj):
        return obj.comments.count()

    def _can_show_counts(self, obj):
        request = self.context.get("request")
        if obj.is_public:
            return True
        if not request or not request.user.is_authenticated:
            return False
        return request.user.id == obj.owner_id


class FileSerializer(serializers.ModelSerializer):
    comment_count = serializers.SerializerMethodField()

    class Meta:
        model = File
        fields = "__all__"
        read_only_fields = ["owner", "uploaded_at"]

    def validate_file(self, value):
        max_size = 100 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError("File size must be under 100MB.")
        return value

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["file"] = instance.file.url
        return data

    def get_comment_count(self, obj):
        return obj.comments.count()


class FolderCommentSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source="owner.username", read_only=True)

    class Meta:
        model = FolderComment
        fields = ["id", "folder", "owner", "owner_username", "text", "created_at"]
        read_only_fields = ["owner", "created_at", "owner_username"]


class FileCommentSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source="owner.username", read_only=True)

    class Meta:
        model = FileComment
        fields = ["id", "file", "owner", "owner_username", "text", "created_at"]
        read_only_fields = ["owner", "created_at", "owner_username"]


class FolderMessageSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source="owner.username", read_only=True)

    class Meta:
        model = FolderMessage
        fields = ["id", "folder", "owner", "owner_username", "text", "created_at"]
        read_only_fields = ["owner", "created_at", "owner_username"]
