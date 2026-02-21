from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Folder, File
from .serializers import FolderSerializer, FileSerializer
from .permissions import IsOwnerOrReadOnly


# =========================
# Folder ViewSet
# =========================
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

class FolderViewSet(ModelViewSet):
    serializer_class = FolderSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    # ✅ LIST + FILTER
    def get_queryset(self):
        queryset = Folder.objects.all()

        parent_id = self.request.query_params.get("parent")

        # Subfolder filtering
        if parent_id:
            queryset = queryset.filter(parent_id=parent_id)

        # If user not logged in → show only public folders
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(is_public=True)

        return queryset

    # ✅ CREATE
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    # ✅ PUBLIC FEED (Main folders only)
    @action(detail=False, methods=["get"])
    def feed(self, request):

        if request.user.is_authenticated:
            folders = Folder.objects.filter(
                Q(parent=None, is_public=True, is_listed_in_feed=True, owner__is_public=True)
                | Q(parent=None, owner=request.user)  # show own private
            )
        else:
            folders = Folder.objects.filter(
                parent=None,
                is_public=True,
                is_listed_in_feed=True,
                owner__is_public=True
            )

        serializer = self.get_serializer(folders, many=True)
        return Response(serializer.data)

    # ✅ RETRIEVE (Password Protected Access)
    def retrieve(self, request, *args, **kwargs):
        folder = self.get_object()

        # 1️⃣ Public folder → allow
        if folder.is_public:
            return super().retrieve(request, *args, **kwargs)

        # 2️⃣ Owner → allow
        if request.user == folder.owner:
            return super().retrieve(request, *args, **kwargs)

        # 3️⃣ Password check
        password = request.query_params.get("password")

        if password and folder.password and check_password(password, folder.password):
            return super().retrieve(request, *args, **kwargs)

        # ❌ Deny
        return Response(
            {"error": "This folder is private. Password required or incorrect."},
            status=403
        )

    # ✅ MY FOLDERS
    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def my_folders(self, request):
        folders = Folder.objects.filter(owner=request.user)
        serializer = self.get_serializer(folders, many=True)
        return Response(serializer.data)

# =========================
# File ViewSet
# =========================
class FileViewSet(ModelViewSet):
    serializer_class = FileSerializer
    permission_classes = [IsOwnerOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        queryset = File.objects.all()

        folder_id = self.request.query_params.get("folder")

        if folder_id:
            queryset = queryset.filter(folder_id=folder_id)

        if not self.request.user.is_authenticated:
            queryset = queryset.filter(
                folder__is_public=True,
                folder__owner__is_public=True
            )

        return queryset
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)