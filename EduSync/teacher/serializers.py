from rest_framework import serializers
from .models import Teacher


class TeacherSerializer(serializers.ModelSerializer):
    """Serializer for Teacher model."""
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    full_name = serializers.SerializerMethodField()
    institution_name = serializers.CharField(source='institution.name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)

    class Meta:
        model = Teacher
        fields = [
            'id', 'employee_id', 'username', 'email', 'first_name', 'last_name',
            'full_name', 'phone', 'gender', 'date_of_birth', 'address',
            'institution_name', 'department_name', 'branch_name',
            'qualification', 'contract_type', 'hire_date', 'initials'
        ]
        read_only_fields = ['id', 'employee_id', 'hire_date', 'initials']

    def get_full_name(self, obj):
        return obj.user.get_full_name()


class TeacherListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing teachers."""
    full_name = serializers.SerializerMethodField()
    department_name = serializers.CharField(source='department.name', read_only=True)

    class Meta:
        model = Teacher
        fields = ['id', 'employee_id', 'full_name', 'department_name', 'contract_type', 'initials']

    def get_full_name(self, obj):
        return obj.user.get_full_name()
