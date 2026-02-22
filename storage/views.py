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
from rest_framework.filters import SearchFilter

class FolderViewSet(ModelViewSet):
    queryset = Folder.objects.all()
    serializer_class = FolderSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [SearchFilter]
    search_fields = ['name']

    # ======================
    # LIST + FILTER
    # ======================
    def get_queryset(self):
        queryset = super().get_queryset()

        parent_id = self.request.query_params.get("parent")
        password = self.request.query_params.get("password")

        if parent_id:
            parent_folder = Folder.objects.get(id=parent_id)

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

    # ======================
    # CREATE
    # ======================
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    # ======================
    # FEED
    # ======================
    @action(detail=False, methods=["get"])
    def feed(self, request):
        folders = Folder.objects.filter(is_listed_in_feed=True)

        if not request.user.is_authenticated:
            folders = folders.filter(is_public=True)

        serializer = self.get_serializer(folders, many=True)
        return Response(serializer.data)

    # ======================
    # RETRIEVE (Password)
    # ======================
    def retrieve(self, request, *args, **kwargs):
        folder = self.get_object()

        if folder.is_public:
            return super().retrieve(request, *args, **kwargs)

        if request.user == folder.owner:
            return super().retrieve(request, *args, **kwargs)

        password = request.query_params.get("password")

        if password and folder.password and check_password(password, folder.password):
            return super().retrieve(request, *args, **kwargs)

        return Response(
            {"error": "This folder is private. Password required or incorrect."},
            status=403
        )

    # ======================
    # MY FOLDERS
    # ======================
    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def my_folders(self, request):
        folders = Folder.objects.filter(owner=request.user)
        serializer = self.get_serializer(folders, many=True)
        return Response(serializer.data)
    
# =========================
# File ViewSet
# =========================
from django.contrib.auth.hashers import check_password

class FileViewSet(ModelViewSet):
    serializer_class = FileSerializer
    permission_classes = [IsOwnerOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        queryset = File.objects.all()
        folder_id = self.request.query_params.get("folder")
        password = self.request.query_params.get("password")

        if folder_id:
            queryset = queryset.filter(folder_id=folder_id)
            folder = Folder.objects.get(id=folder_id)

            # Public → allow
            if folder.is_public:
                return queryset

            # Owner → allow
            if self.request.user == folder.owner:
                return queryset

            # Password check
            if password and folder.password and check_password(password, folder.password):
                return queryset

            # ❌ deny
            return File.objects.none()

        return queryset

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)



# from rest_framework.filters import SearchFilter

# class FolderViewSet(ModelViewSet):
#     queryset = Folder.objects.all()   # 🔥 REQUIRED
#     serializer_class = FolderSerializer
#     filter_backends = [SearchFilter]
#     search_fields = ['name']

#     def get_queryset(self):
#         queryset = super().get_queryset()

#         # Example security filtering
#         if not self.request.user.is_authenticated:
#             queryset = queryset.filter(is_public=True)

#         return queryset