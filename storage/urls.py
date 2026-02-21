from rest_framework.routers import DefaultRouter
from .views import FolderViewSet, FileViewSet

router = DefaultRouter()
router.register(r'folders', FolderViewSet, basename='folders')
router.register(r'files', FileViewSet, basename='files')

urlpatterns = router.urls