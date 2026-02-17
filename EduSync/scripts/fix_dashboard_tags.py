import re
import os

file_path = r'c:\Users\Krish Patel\Desktop\Project\EduSync-1\EduSync\student\templates\student\dashboard.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern to find Django tags {{ ... }} and {% ... %} that are spread across lines
# and replace them with single-line versions.
def clean_tags(match):
    tag_content = match.group(0)
    # Remove newlines and consolidate whitespace
    cleaned = re.sub(r'\s+', ' ', tag_content)
    return cleaned

# Match {{ ... }} across lines
result = re.sub(r'\{\{.*?\}\}', clean_tags, content, flags=re.DOTALL)
# Match {% ... %} across lines 
result = re.sub(r'\{%.*?%\}', clean_tags, result, flags=re.DOTALL)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(result)

print(f"Cleaned all multi-line tags in {file_path}")
