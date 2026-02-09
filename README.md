# EduSync 2.0 - Campus Management & Timetable System

EduSync is a comprehensive campus management system designed for institutions to manage students, teachers, courses, and most importantly, automated timetable generation.

## 🚀 Getting Started

### Prerequisites
- Python 3.10 or higher
- Pip (Python Package Installer)

### Installation
1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd EduSync_2.0/EduSync-1/EduSync
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup Database:**
   ```bash
   python manage.py migrate
   ```

4. **Seed Initial Data (Recommended for Testing):**
   A seeding script is provided to populate the database with a sample institution, teachers, and courses.
   ```bash
   python manage.py shell < scripts/seed_wrapper.py
   # OR move seed.py into the root and run:
   python seed.py
   ```

5. **Run the Server:**
   ```bash
   python manage.py runserver
   ```
   Access the app at [http://127.0.0.1:8000](http://127.0.0.1:8000)

## 📂 Project Structure

- **`academics/`**: Manages Courses, Grades, and Departments.
- **`accounts/`**: Handles Authentication, User Roles (Admin, Teacher, Student).
- **`generator/`**: The core Timetable Generation engine.
- **`institution/`**: Institution-level settings and announcements.
- **`student/`**: Student portal and records.
- **`teacher/`**: Teacher portal and faculty management.

## 🛠️ Key Features
- **Automated Timetable Generation**: Generate non-conflicting schedules with a single click.
- **Role-Based Access**: Specialized portals for Admins, Teachers, and Students.
- **Export Options**: Download timetables as PDF or Excel.
- **Dynamic Theming**: Customizable UI themes for different institutions.

## 🤝 Support
For any issues or feature requests, please contact the development team at info@edusync.com.
