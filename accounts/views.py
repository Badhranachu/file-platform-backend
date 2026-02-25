from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import serializers
from storage.models import Folder
from storage.serializers import FolderSerializer
from .models import DirectMessage
from .serializers import DirectMessageSerializer, RegisterSerializer, UserSerializer

User = get_user_model()


# ✅ Register New User
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


# ✅ Get / Update Logged-in User Profile
class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=400)


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = "email"
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get("email", "").strip()
        password = attrs.get("password")

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist as exc:
            raise AuthenticationFailed("No active account found with this email.") from exc

        authenticated_user = authenticate(
            request=self.context.get("request"),
            username=user.username,
            password=password,
        )
        if not authenticated_user:
            raise AuthenticationFailed("Invalid email or password.")

        refresh = self.get_token(authenticated_user)
        return {"refresh": str(refresh), "access": str(refresh.access_token)}


class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer


class UserListView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = User.objects.all().order_by("username")
        q = self.request.query_params.get("q", "").strip()
        if q:
            queryset = queryset.filter(Q(username__icontains=q) | Q(email__icontains=q))
        return queryset


class UserDetailView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = User.objects.all()


class UserFoldersView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, user_id):
        folders = Folder.objects.filter(owner_id=user_id)
        if request.user.id != int(user_id):
            folders = folders.filter(is_public=True)
        serializer = FolderSerializer(folders, many=True, context={"request": request})
        return Response(serializer.data)


class ToggleFollowView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, user_id):
        if request.user.id == int(user_id):
            return Response({"error": "You cannot follow yourself."}, status=400)

        try:
            target = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=404)

        if request.user.follows.filter(id=target.id).exists():
            request.user.follows.remove(target)
            following = False
        else:
            request.user.follows.add(target)
            following = True

        return Response(
            {
                "following": following,
                "followers_count": target.followers.count(),
            }
        )


class ChatListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        messages = DirectMessage.objects.filter(
            Q(sender=request.user) | Q(receiver=request.user)
        ).order_by("-created_at")

        seen = set()
        partners = []
        for msg in messages:
            partner = msg.receiver if msg.sender_id == request.user.id else msg.sender
            if partner.id in seen:
                continue
            seen.add(partner.id)
            partners.append(
                {
                    "user": UserSerializer(partner, context={"request": request}).data,
                    "last_message": msg.text,
                    "last_message_at": msg.created_at,
                }
            )
        return Response(partners)


class ChatWithUserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, user_id):
        if request.user.id == int(user_id):
            return Response({"error": "Cannot open chat with yourself."}, status=400)

        messages = DirectMessage.objects.filter(
            (Q(sender=request.user, receiver_id=user_id) | Q(sender_id=user_id, receiver=request.user))
        ).order_by("created_at")
        serializer = DirectMessageSerializer(messages, many=True)
        return Response(serializer.data)

    def post(self, request, user_id):
        if request.user.id == int(user_id):
            return Response({"error": "Cannot message yourself."}, status=400)

        try:
            receiver = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=404)

        text = request.data.get("text", "").strip()
        if not text:
            return Response({"error": "Message text is required."}, status=400)

        message = DirectMessage.objects.create(
            sender=request.user,
            receiver=receiver,
            text=text,
        )
        serializer = DirectMessageSerializer(message)
        return Response(serializer.data, status=201)


class UsernameSuggestionsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        raw = request.query_params.get("username", "").strip().lower()
        if not raw:
            return Response({"suggestions": []})

        base = "".join(ch for ch in raw if ch.isalnum() or ch == "_")
        if not base:
            base = "user"

        suggestions = []
        suffix = 1
        while len(suggestions) < 5 and suffix < 1000:
            candidate = f"{base}{suffix}" if suffix > 1 else base
            if not User.objects.filter(username__iexact=candidate).exists():
                suggestions.append(candidate)
            suffix += 1

        return Response({"suggestions": suggestions})
