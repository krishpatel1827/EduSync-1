from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.models import User
from .models import UserProfile, SignupTable


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT token serializer that includes additional user info in the token.
    """
    institution_name = serializers.CharField(write_only=True, required=True)
    role = serializers.CharField(write_only=True, required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make username and password required
        self.fields['username'] = serializers.CharField()
        self.fields['password'] = serializers.CharField(write_only=True)

    def validate(self, attrs):
        institution_name = attrs.pop('institution_name', None)
        role = attrs.pop('role', None)

        # First validate institution exists
        try:
            SignupTable.objects.get(institution_name__iexact=institution_name)
        except SignupTable.DoesNotExist:
            raise serializers.ValidationError({
                'institution_name': f"Institution '{institution_name}' not found."
            })

        # Call parent validation (authenticates user)
        data = super().validate(attrs)

        # Verify user profile and role match
        try:
            profile = UserProfile.objects.get(user=self.user)
            
            if profile.institution.lower() != institution_name.lower():
                raise serializers.ValidationError({
                    'institution_name': f"This account is not registered under {institution_name}."
                })
            
            if profile.role != role:
                raise serializers.ValidationError({
                    'role': f"Account found, but it is not a {role} account."
                })
                
        except UserProfile.DoesNotExist:
            raise serializers.ValidationError({
                'detail': "User profile not found."
            })

        # Add custom claims to the token
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'role': profile.role,
            'institution': profile.institution,
        }

        return data

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims to the token payload
        try:
            profile = user.userprofile
            token['role'] = profile.role
            token['institution'] = profile.institution
        except UserProfile.DoesNotExist:
            pass

        token['username'] = user.username
        token['email'] = user.email

        return token


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    role = serializers.CharField(source='userprofile.role', read_only=True)
    institution = serializers.CharField(source='userprofile.institution', read_only=True)
    phone = serializers.CharField(source='userprofile.phone', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'institution', 'phone']
        read_only_fields = ['id', 'username']


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model."""
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)

    class Meta:
        model = UserProfile
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'phone', 'institution']
        read_only_fields = ['role', 'institution']
        