from django.contrib.auth.hashers import check_password
from django.db.models import Count, Q
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import File, FileComment, Folder, FolderComment, FolderMessage, FolderView
from .permissions import IsOwnerOrReadOnly
from .serializers import (
    FileCommentSerializer,
    FileSerializer,
    FolderCommentSerializer,
    FolderMessageSerializer,
    FolderSerializer,
)


class FolderViewSet(ModelViewSet):
    queryset = Folder.objects.all()
    serializer_class = FolderSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [SearchFilter]
    search_fields = ["name", "folder_code"]

    def get_queryset(self):
        queryset = super().get_queryset()
        parent_id = self.request.query_params.get("parent")
        password = self.request.query_params.get("password")

        if parent_id:
            try:
                parent_folder = Folder.objects.get(id=parent_id)
            except Folder.DoesNotExist:
                return Folder.objects.none()

            if parent_folder.is_public:
                return queryset.filter(parent_id=parent_id)

            if self.request.user == parent_folder.owner:
                return queryset.filter(parent_id=parent_id)

            if password and parent_folder.password and check_password(password, parent_folder.password):
                return queryset.filter(parent_id=parent_id)

            return Folder.objects.none()

        if not self.request.user.is_authenticated:
            queryset = queryset.filter(is_public=True)

        return queryset

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=False, methods=["get"])
    def feed(self, request):
        folders = (
            Folder.objects.filter(is_listed_in_feed=True)
            .annotate(
                views_count=Count("views", distinct=True),
                likes_count=Count("liked_by", distinct=True),
                comments_count=Count("comments", distinct=True),
            )
            .order_by("-views_count", "-likes_count", "-comments_count", "-created_at")
        )
        if not request.user.is_authenticated:
            folders = folders.filter(is_public=True)
        serializer = self.get_serializer(folders, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def following_feed(self, request):
        followed_ids = request.user.follows.values_list("id", flat=True)
        folders = Folder.objects.filter(
            is_listed_in_feed=True,
            owner_id__in=followed_ids,
        ).filter(Q(is_public=True) | Q(owner=request.user)).order_by("-created_at")
        serializer = self.get_serializer(folders, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        folder = self.get_object()

        if folder.is_public or request.user == folder.owner:
            if request.user.is_authenticated:
                FolderView.objects.get_or_create(folder=folder, user=request.user)
            return super().retrieve(request, *args, **kwargs)

        password = request.query_params.get("password")

        if password and folder.password and check_password(password, folder.password):
            if request.user.is_authenticated:
                FolderView.objects.get_or_create(folder=folder, user=request.user)
            return super().retrieve(request, *args, **kwargs)

        return Response(
            {"error": "This folder is private. Password required or incorrect."},
            status=403,
        )

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def my_folders(self, request):
        folders = Folder.objects.filter(owner=request.user)
        serializer = self.get_serializer(folders, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def like(self, request, pk=None):
        folder = self.get_object()

        if folder.liked_by.filter(id=request.user.id).exists():
            folder.liked_by.remove(request.user)
            liked = False
        else:
            folder.liked_by.add(request.user)
            liked = True

        return Response({"liked": liked, "like_count": folder.liked_by.count()})

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def liked(self, request):
        folders = Folder.objects.filter(liked_by=request.user)
        serializer = self.get_serializer(folders, many=True)
        return Response(serializer.data)


class FileViewSet(ModelViewSet):
    serializer_class = FileSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        queryset = File.objects.all()
        folder_id = self.request.query_params.get("folder")
        password = self.request.query_params.get("password")

        if self.action == "retrieve":
            return queryset

        if not folder_id:
            if self.request.user.is_authenticated:
                return queryset.filter(owner=self.request.user)
            return File.objects.none()

        queryset = queryset.filter(folder_id=folder_id)

        try:
            folder = Folder.objects.get(id=folder_id)
        except Folder.DoesNotExist:
            return File.objects.none()

        if folder.is_public:
            return queryset

        if self.request.user == folder.owner:
            return queryset

        if password and folder.password and check_password(password, folder.password):
            return queryset

        return File.objects.none()

    def retrieve(self, request, *args, **kwargs):
        file_obj = self.get_object()
        folder = file_obj.folder

        if folder.is_public or request.user == folder.owner:
            return super().retrieve(request, *args, **kwargs)

        password = request.query_params.get("password")
        if password and folder.password and check_password(password, folder.password):
            return super().retrieve(request, *args, **kwargs)

        return Response({"error": "This file belongs to a private folder."}, status=403)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class FolderCommentViewSet(ModelViewSet):
    serializer_class = FolderCommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_queryset(self):
        queryset = FolderComment.objects.all().order_by("-created_at")
        folder_id = self.request.query_params.get("folder")
        if folder_id:
            queryset = queryset.filter(folder_id=folder_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class FileCommentViewSet(ModelViewSet):
    serializer_class = FileCommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_queryset(self):
        queryset = FileComment.objects.all().order_by("-created_at")
        file_id = self.request.query_params.get("file")
        if file_id:
            queryset = queryset.filter(file_id=file_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class FolderMessageViewSet(ModelViewSet):
    serializer_class = FolderMessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = FolderMessage.objects.all().order_by("created_at")
        folder_id = self.request.query_params.get("folder")
        if folder_id:
            queryset = queryset.filter(folder_id=folder_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
