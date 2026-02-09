# EduSync Authentication Flow - Summary

## Current Implementation

### Flow Overview:
1. **Main Login** (3-field form)
   - Institution Name
   - Username  
   - Password
   - URL: `/login/`

2. **Institution Dashboard** (After successful login)
   - Shows 3 portal options:
     * Admin Portal Login
     * Teacher Portal Login
     * Student Portal Login
   - URL: `/institution/dashboard/`

3. **Portal-Specific Access:**
   - **Teacher Portal**: Click "Teacher Portal" → Enter Name + Employee ID → Teacher Dashboard
   - **Student Portal**: Click "Student Portal" → Enter Name + Student ID → Student Dashboard
   - **Admin Portal**: Click "Admin Portal" → Direct access to admin features

### Key Features:

#### Institution-Based Data Filtering:
- **Timetable Generator "Add Entry"** form automatically filters:
  - Teachers (only from the logged-in user's institution)
  - Students (only from the logged-in user's institution)
  - Subjects/Courses (only from the logged-in user's institution)
  - Rooms (only from the logged-in user's institution)

- This is implemented in `generator/forms.py` (lines 19-22):
  ```python
  if institution:
      self.fields['subject'].queryset = Course.objects.filter(institution=institution)
      self.fields['faculty'].queryset = Teacher.objects.filter(institution=institution)
      self.fields['room'].queryset = Room.objects.filter(institution=institution)
  ```

#### Test Credentials:
**KP_Academy:**
- Admin: `KP_Academy` / `kp_admin` / `pass123`
- Teacher: `KP_Academy` / `kp_academy_jd` / `pass123` (then use "John Doe" + "JD")
- Student: `KP_Academy` / `student_kp_st_01` / `pass123` (then use "Alice Wong" + "KP_ST_01")

**DNI_Institute:**
- Admin: `DNI_Institute` / `dni_admin` / `pass123`
- Teacher: `DNI_Institute` / `dni_academy_rb` / `pass123` (then use "Robert Brown" + "RB")

### File Changes Made:
1. `accounts/views.py` - Modified `_redirect_by_role()` to always redirect to institution dashboard
2. `generator/forms.py` - Already has institution-based filtering (no changes needed)
3. `generator/views.py` - Already passes institution context (no changes needed)

### Verification:
✓ Main login redirects to Institution Dashboard
✓ Institution Dashboard shows 3 portal options
✓ Teacher Portal access works correctly
✓ Timetable "Add Entry" filters by institution
