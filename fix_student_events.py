import re
import os

filepath = r'EduSync/student/templates/student/dashboard.html'
if os.path.exists(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    pattern = re.compile(r'<span class="event-type-chip"[\s\S]*?</span>', re.MULTILINE)

    def replacer(match):
        s = match.group(0)
        collapsed = re.sub(r'\s+', ' ', s).strip()
        return collapsed

    new_content = pattern.sub(replacer, content)

    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print('Fixed event-type-chip in student dashboard')
    else:
        print('No changes made to student dashboard')
else:
    print('File not found')
