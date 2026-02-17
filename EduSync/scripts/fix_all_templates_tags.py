import re
import os
import glob

directories = [
    r'c:\Users\Krish Patel\Desktop\Project\EduSync-1\EduSync\student\templates\student',
    r'c:\Users\Krish Patel\Desktop\Project\EduSync-1\EduSync\teacher\templates\teacher',
    r'c:\Users\Krish Patel\Desktop\Project\EduSync-1\EduSync\institution\templates\institution',
    r'c:\Users\Krish Patel\Desktop\Project\EduSync-1\EduSync\generator\templates',
    r'c:\Users\Krish Patel\Desktop\Project\EduSync-1\EduSync\templates'
]

def clean_tags(match):
    tag_content = match.group(0)
    cleaned = re.sub(r'\s+', ' ', tag_content)
    return cleaned

for directory in directories:
    if not os.path.exists(directory):
        continue
    files = glob.glob(os.path.join(directory, '*.html'))
    for file_path in files:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        result = re.sub(r'\{\{.*?\}\}', clean_tags, content, flags=re.DOTALL)
        result = re.sub(r'\{%.*?%\}', clean_tags, result, flags=re.DOTALL)

        if content != result:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(result)
            print(f"Cleaned multi-line tags in {file_path}")
