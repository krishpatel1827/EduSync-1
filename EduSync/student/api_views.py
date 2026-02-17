from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import IsStudent, IsTeacher, IsTeacherOrAdmin, IsSameInstitution
from .models import Student
from .serializers import StudentSerializer, StudentListSerializer


class StudentProfileAPIView(APIView):
    """
    Get the current student's own profile.
    
    GET /api/student/profile/
    
    Headers:
        Authorization: Bearer <access_token>
    
    Returns the student's full profile data.
    """
    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request):
        try:
            student = Student.objects.select_related(
                'user', 'institution', 'course', 'branch', 'department'
            ).get(user=request.user)
            serializer = StudentSerializer(student)
            return Response(serializer.data)
        except Student.DoesNotExist:
            return Response(
                {'detail': 'Student profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

    def patch(self, request):
        """Update student's own profile (limited fields)."""
        try:
            student = Student.objects.get(user=request.user)
            
            # Only allow updating certain fields
            allowed_fields = ['phone', 'address', 'blood_group']
            update_data = {k: v for k, v in request.data.items() if k in allowed_fields}
            
            serializer = StudentSerializer(student, data=update_data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Student.DoesNotExist:
            return Response(
                {'detail': 'Student profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )


class StudentListAPIView(APIView):
    """
    List all students in the same institution.
    Only accessible by teachers and institution admins.
    
    GET /api/student/list/
    
    Query params:
        - course: Filter by course ID
        - semester: Filter by semester
        - status: Filter by status (active/inactive)
    """
    permission_classes = [IsAuthenticated, IsTeacherOrAdmin]

    def get(self, request):
        user_institution = request.user.userprofile.institution
        
        students = Student.objects.select_related(
            'user', 'course'
        ).filter(
            institution__name__iexact=user_institution
        )
        
        # Apply filters
        course_id = request.query_params.get('course')
        if course_id:
            students = students.filter(course_id=course_id)
        
        semester = request.query_params.get('semester')
        if semester:
            students = students.filter(semester=semester)
        
        status_filter = request.query_params.get('status')
        if status_filter:
            students = students.filter(status=status_filter)
        
        serializer = StudentListSerializer(students, many=True)
        return Response({
            'count': len(serializer.data),
            'students': serializer.data
        })


class StudentDetailAPIView(APIView):
    """
    Get a specific student's details.
    Only accessible by teachers and institution admins from the same institution.
    
    GET /api/student/<student_id>/
    """
    permission_classes = [IsAuthenticated, IsTeacherOrAdmin]

    def get(self, request, student_id):
        user_institution = request.user.userprofile.institution
        
        try:
            student = Student.objects.select_related(
                'user', 'institution', 'course', 'branch', 'department'
            ).get(
                student_id=student_id,
                institution__name__iexact=user_institution
            )
            serializer = StudentSerializer(student)
            return Response(serializer.data)
        except Student.DoesNotExist:
            return Response(
                {'detail': 'Student not found or not in your institution.'},
                status=status.HTTP_404_NOT_FOUND
            )
