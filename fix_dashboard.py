import re

# Fix student dashboard - timeslot times
sd_path = r'c:/Users/Krish Patel/Desktop/New folder/EduSync_Final/EduSync-1/EduSync/student/templates/student/dashboard.html'
with open(sd_path, 'r', encoding='utf-8') as f:
    content = f.read()

content = re.sub(
    r'<div style="font-weight: 707; font-size: 0\.9rem;">\{\{\s+entry\.timeslot\.start_time\|time:"G:i" \}\}</div>',
    '<div style="font-weight: 700; font-size: 0.9rem;">{{ entry.timeslot.start_time|time:"G:i" }}</div>',
    content
)

# Match the actual multi-line pattern in student dashboard
content = re.sub(
    r'(<div style="font-weight: 700; font-size: 0\.9rem;">)\{\{\s*[\r\n]+\s*(entry\.timeslot\.start_time\|time:"G:i") \}\}(</div>)',
    r'\1{{ \2 }}\3',
    content
)
content = re.sub(
    r'(<div class="text-muted" style="font-size: 0\.75rem;">)\{\{\s*[\r\n]+\s*(entry\.timeslot\.end_time\|time:"G:i") \}\}(</div>)',
    r'\1{{ \2 }}\3',
    content
)

with open(sd_path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Fixed student dashboard timeslots')

# Fix teacher dashboard - event.type and remaining timeslot
td_path = r'c:/Users/Krish Patel/Desktop/New folder/EduSync_Final/EduSync-1/EduSync/teacher/templates/teacher/dashboard.html'
with open(td_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix remaining multi-line timeslot tags
content = re.sub(
    r'(<div style="font-weight: 700; font-size: 0\.9rem;">)\{\{\s*[\r\n]+\s*(entry\.timeslot\.start_time\|time:"G:i") \}\}(</div>)',
    r'\1{{ \2 }}\3',
    content
)
content = re.sub(
    r'(<div class="text-muted" style="font-size: 0\.75rem;">)\{\{\s*[\r\n]+\s*(entry\.timeslot\.end_time\|time:"G:i") \}\}(</div>)',
    r'\1{{ \2 }}\3',
    content
)

# Fix event.type span across multiple lines
content = re.sub(
    r'<span\s*\n\s*style="display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 0\.7rem;\s*\n\s*font-weight: 600; text-transform: uppercase; background: \{\{ event\.color_code \}\}22; color: \{\{ event\.color_code \}\};">\{\{\s*\n\s*event\.type \}\}</span>',
    '<span style="display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 0.7rem; font-weight: 600; text-transform: uppercase; background: {{ event.color_code }}22; color: {{ event.color_code }};">{{ event.type }}</span>',
    content
)

# Also try with \r\n
content = re.sub(
    r'<span\s*\r\n\s*style="display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 0\.7rem;\s*\r\n\s*font-weight: 600; text-transform: uppercase; background: \{\{ event\.color_code \}\}22; color: \{\{ event\.color_code \}\};">\{\{\s*\r\n\s*event\.type \}\}</span>',
    '<span style="display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 0.7rem; font-weight: 600; text-transform: uppercase; background: {{ event.color_code }}22; color: {{ event.color_code }};">{{ event.type }}</span>',
    content
)

with open(td_path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Fixed teacher dashboard')
print('Done!')
