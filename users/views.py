from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

from .models import User
from .serializers import RegisterSerializer, UserProfileSerializer, InternalUserSerializer
from .events import user_registered_event, user_logged_in_event, user_updated_event


class RegisterView(APIView):
    """
    POST /api/users/register/
    Anyone can register. After registering, publishes
    'user.registered' event to Redis so notification-service
    can send a welcome email.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)

            # Publish event to Redis ← other services listen here
            user_registered_event(user)

            return Response({
                "message": "Account created successfully.",
                "user": UserProfileSerializer(user).data,
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                },
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """
    POST /api/users/login/
    Returns JWT access + refresh tokens.
    Publishes 'user.logged_in' event to Redis.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        user = authenticate(request, username=email, password=password)
        if not user:
            return Response(
                {"error": "Invalid email or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        refresh = RefreshToken.for_user(user)

        # Publish login event to Redis
        user_logged_in_event(user)

        return Response({
            "tokens": {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            "user": UserProfileSerializer(user).data,
        })


class ProfileView(generics.RetrieveUpdateAPIView):
    """
    GET  /api/users/profile/   → get my profile
    PUT  /api/users/profile/   → update my profile
    Requires JWT token in Authorization header.
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def perform_update(self, serializer):
        user = serializer.save()
        # Publish update event to Redis
        user_updated_event(user)


class LogoutView(APIView):
    """
    POST /api/users/logout/
    Blacklists the refresh token (invalidates it).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Logged out successfully."})
        except Exception:
            return Response({"error": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)


class InternalUserDetailView(APIView):
    """
    GET /api/users/internal/<user_id>/

    INTERNAL USE ONLY — called by other services
    (reservation-service, etc.) to verify a user exists.

    In production, protect this with a secret header or
    put it on a private network not exposed to the internet.
    """
    permission_classes = [AllowAny]  # secured by private network in prod

    def get(self, request, user_id):
        # Check internal secret header
        secret = request.headers.get("X-Internal-Secret")
        if secret != "internal-secret-change-in-prod":
            return Response({"error": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)

        try:
            user = User.objects.get(id=user_id)
            return Response(InternalUserSerializer(user).data)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
