import re
import os

files_to_fix = [
    r'c:/Users/Krish Patel/Desktop/New folder/EduSync_Final/EduSync-1/EduSync/marksheet/templates/marksheet/marks_entry_sheet.html',
    r'c:/Users/Krish Patel/Desktop/New folder/EduSync_Final/EduSync-1/EduSync/teacher/templates/teacher/dashboard.html',
    r'c:/Users/Krish Patel/Desktop/New folder/EduSync_Final/EduSync-1/EduSync/student/templates/student/dashboard.html'
]

def fix_file(filepath):
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # This regex matches {{ ... }} and captures the inside
    # We want to catch instances where there is a newline inside
    def replacer(match):
        inner = match.group(1)
        if '\n' in inner:
            # Clean it up: convert multiple whitespace/newlines to single space
            cleaned = re.sub(r'\s+', ' ', inner).strip()
            return f"{{{{ {cleaned} }}}}"
        return match.group(0) # No change if no newline
    
    new_content = re.sub(r'\{\{([\s\S]*?)\}\}', replacer, content)
    
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Fixed template tags in: {filepath}")
    else:
        print(f"No changes needed for: {filepath}")

for f in files_to_fix:
    fix_file(f)

print("Template fix complete.")
