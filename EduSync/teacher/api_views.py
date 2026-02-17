from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import IsTeacher, IsInstitutionAdmin, IsTeacherOrAdmin
from .models import Teacher
from .serializers import TeacherSerializer, TeacherListSerializer


class TeacherProfileAPIView(APIView):
    """
    Get the current teacher's own profile.
    
    GET /api/teacher/profile/
    
    Headers:
        Authorization: Bearer <access_token>
    
    Returns the teacher's full profile data.
    """
    permission_classes = [IsAuthenticated, IsTeacher]

    def get(self, request):
        try:
            teacher = Teacher.objects.select_related(
                'user', 'institution', 'department', 'branch'
            ).get(user=request.user)
            serializer = TeacherSerializer(teacher)
            return Response(serializer.data)
        except Teacher.DoesNotExist:
            return Response(
                {'detail': 'Teacher profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

    def patch(self, request):
        """Update teacher's own profile (limited fields)."""
        try:
            teacher = Teacher.objects.get(user=request.user)
            
            # Only allow updating certain fields
            allowed_fields = ['phone', 'address', 'qualification']
            update_data = {k: v for k, v in request.data.items() if k in allowed_fields}
            
            serializer = TeacherSerializer(teacher, data=update_data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Teacher.DoesNotExist:
            return Response(
                {'detail': 'Teacher profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )


class TeacherListAPIView(APIView):
    """
    List all teachers in the same institution.
    Only accessible by institution admins.
    
    GET /api/teacher/list/
    
    Query params:
        - department: Filter by department ID
        - contract_type: Filter by contract type
    """
    permission_classes = [IsAuthenticated, IsInstitutionAdmin]

    def get(self, request):
        user_institution = request.user.userprofile.institution
        
        teachers = Teacher.objects.select_related(
            'user', 'department'
        ).filter(
            institution__name__iexact=user_institution
        )
        
        # Apply filters
        department_id = request.query_params.get('department')
        if department_id:
            teachers = teachers.filter(department_id=department_id)
        
        contract_type = request.query_params.get('contract_type')
        if contract_type:
            teachers = teachers.filter(contract_type=contract_type)
        
        serializer = TeacherListSerializer(teachers, many=True)
        return Response({
            'count': len(serializer.data),
            'teachers': serializer.data
        })


class TeacherDetailAPIView(APIView):
    """
    Get a specific teacher's details.
    Only accessible by institution admins from the same institution.
    
    GET /api/teacher/<employee_id>/
    """
    permission_classes = [IsAuthenticated, IsInstitutionAdmin]

    def get(self, request, employee_id):
        user_institution = request.user.userprofile.institution
        
        try:
            teacher = Teacher.objects.select_related(
                'user', 'institution', 'department', 'branch'
            ).get(
                employee_id=employee_id,
                institution__name__iexact=user_institution
            )
            serializer = TeacherSerializer(teacher)
            return Response(serializer.data)
        except Teacher.DoesNotExist:
            return Response(
                {'detail': 'Teacher not found or not in your institution.'},
                status=status.HTTP_404_NOT_FOUND
            )
