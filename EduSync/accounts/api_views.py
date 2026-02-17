from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .serializers import CustomTokenObtainPairSerializer, UserSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom JWT token obtain view that validates institution and role.
    
    POST /api/auth/token/
    
    Request body:
    {
        "username": "user123",
        "password": "password123",
        "institution_name": "Sample Institution",
        "role": "student"  // student, teacher, or institution_admin
    }
    
    Response:
    {
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "user": {
            "id": 1,
            "username": "user123",
            "email": "user@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "role": "student",
            "institution": "Sample Institution"
        }
    }
    """
    permission_classes = [AllowAny]
    serializer_class = CustomTokenObtainPairSerializer


class CustomTokenRefreshView(TokenRefreshView):
    """
    Refresh JWT access token.
    
    POST /api/auth/token/refresh/
    
    Request body:
    {
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    }
    
    Response:
    {
        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."  // New refresh token if rotation is enabled
    }
    """
    permission_classes = [AllowAny]


class LogoutView(APIView):
    """
    Logout by blacklisting the refresh token.
    
    POST /api/auth/logout/
    
    Request body:
    {
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    }
    
    Response:
    {
        "detail": "Successfully logged out."
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response(
                    {'detail': 'Refresh token is required.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response(
                {'detail': 'Successfully logged out.'},
                status=status.HTTP_200_OK
            )
        except TokenError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class UserProfileView(APIView):
    """
    Get current authenticated user's profile.
    
    GET /api/auth/profile/
    
    Headers:
    Authorization: Bearer <access_token>
    
    Response:
    {
        "id": 1,
        "username": "user123",
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "role": "student",
        "institution": "Sample Institution",
        "phone": "1234567890"
    }
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class VerifyTokenView(APIView):
    """
    Verify if the current access token is valid.
    
    GET /api/auth/verify/
    
    Headers:
    Authorization: Bearer <access_token>
    
    Response:
    {
        "valid": true,
        "user_id": 1,
        "username": "user123"
    }
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            'valid': True,
            'user_id': request.user.id,
            'username': request.user.username
        })
