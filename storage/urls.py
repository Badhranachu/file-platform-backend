from rest_framework.routers import DefaultRouter
from .views import (
    FileCommentViewSet,
    FileViewSet,
    FolderCommentViewSet,
    FolderViewSet,
)

router = DefaultRouter()
router.register(r'folders', FolderViewSet, basename='folders')
router.register(r'files', FileViewSet, basename='files')
router.register(r'folder-comments', FolderCommentViewSet, basename='folder-comments')
router.register(r'file-comments', FileCommentViewSet, basename='file-comments')

urlpatterns = router.urls
