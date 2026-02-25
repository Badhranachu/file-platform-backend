from django.urls import path
from .views import (
    ChatListView,
    ChatWithUserView,
    RegisterView,
    ToggleFollowView,
    UsernameSuggestionsView,
    UserDetailView,
    UserFoldersView,
    UserListView,
    UserProfileView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('users/<int:user_id>/folders/', UserFoldersView.as_view(), name='user-folders'),
    path('users/<int:user_id>/follow/', ToggleFollowView.as_view(), name='toggle-follow'),
    path('chats/', ChatListView.as_view(), name='chat-list'),
    path('chats/<int:user_id>/', ChatWithUserView.as_view(), name='chat-with-user'),
    path('username-suggestions/', UsernameSuggestionsView.as_view(), name='username-suggestions'),
]
