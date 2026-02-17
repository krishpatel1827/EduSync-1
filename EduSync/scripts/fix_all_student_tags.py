import re
import os
import glob

directory = r'c:\Users\Krish Patel\Desktop\Project\EduSync-1\EduSync\student\templates\student'
files = glob.glob(os.path.join(directory, '*.html'))

def clean_tags(match):
    tag_content = match.group(0)
    cleaned = re.sub(r'\s+', ' ', tag_content)
    return cleaned

for file_path in files:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    result = re.sub(r'\{\{.*?\}\}', clean_tags, content, flags=re.DOTALL)
    result = re.sub(r'\{%.*?%\}', clean_tags, result, flags=re.DOTALL)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(result)

    print(f"Cleaned all multi-line tags in {file_path}")
