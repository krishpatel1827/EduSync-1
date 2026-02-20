from rest_framework import serializers
from .models import Student
from academics.models import Course, Branch


class StudentSerializer(serializers.ModelSerializer):
    """Serializer for Student model."""
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    full_name = serializers.SerializerMethodField()
    institution_name = serializers.CharField(source='institution.name', read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)

    class Meta:
        model = Student
        fields = [
            'id', 'student_id', 'username', 'email', 'first_name', 'last_name',
            'full_name', 'phone', 'gender', 'date_of_birth', 'address',
            'institution_name', 'course_name', 'branch_name', 'department_name',
            'academic_year', 'semester', 'gpa', 'status', 'enrollment_date',
            'parent_name', 'parent_phone', 'blood_group'
        ]
        read_only_fields = ['id', 'student_id', 'enrollment_date']

    def get_full_name(self, obj):
        return obj.user.get_full_name()


class StudentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing students.""" 
    full_name = serializers.SerializerMethodField()
    course_name = serializers.CharField(source='course.name', read_only=True)

    class Meta:
        model = Student
        fields = ['id', 'student_id', 'full_name', 'course_name', 'semester', 'status']

    def get_full_name(self, obj):
        return obj.user.get_full_name()
