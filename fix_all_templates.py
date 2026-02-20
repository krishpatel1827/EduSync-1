import re
import os

def fix_all_templates(directory):
    for root, dirs, files in os.walk(directory):
        if any(x in root for x in ['node_modules', '.git', '__pycache__', '.gemini']):
            continue
        for file in files:
            if file.endswith('.html'):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Fix {{ ... }} and {% ... %} tags split across lines
                    # We want to catch instances where there is a newline inside
                    def replacer_val(match):
                        inner = match.group(1)
                        if '\n' in inner or '\r' in inner:
                            cleaned = re.sub(r'\s+', ' ', inner).strip()
                            return f"{{{{ {cleaned} }}}}"
                        return match.group(0)

                    def replacer_tag(match):
                        inner = match.group(1)
                        if '\n' in inner or '\r' in inner:
                            # For tags like {% block %}, we might want to keep newlines if it's a multi-line tag?
                            # Usually, logic tags {% if %} etc should be on one line for the start tag.
                            # But some tags like {% block %} might have content? No, the START tag is what we fix.
                            cleaned = re.sub(r'\s+', ' ', inner).strip()
                            return f"{{% {cleaned} %}}"
                        return match.group(0)

                    temp_content = re.sub(r'\{\{([\s\S]*?)\}\}', replacer_val, content)
                    new_content = re.sub(r'\{%([\s\S]*?)%\}', replacer_tag, temp_content)
                    
                    if new_content != content:
                        with open(path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        print(f"Fixed template tags in: {path}")
                except Exception as e:
                    print(f"Error processing {path}: {e}")

fix_all_templates('EduSync')
print("Global template fix complete.")
