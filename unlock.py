import re

# Step 1: Clean up script.js
with open('static/script.js', 'r', encoding='utf-8') as f:
    js_code = f.read()

# Remove the specific event listener block
js_code = re.sub(
    r'document\.addEventListener\(\s*[\'"]DOMContentLoaded[\'"]\s*,\s*\(event\)\s*=>\s*{.*?fetchButton\.click\(\);\s*.*?}\s*\);',
    '',
    js_code,
    flags=re.DOTALL
)

with open('static/script.js', 'w', encoding='utf-8') as f:
    f.write(js_code)


# Step 2: Modify index.html
with open('static/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Remove `disabled` from the <input id="fileInput">
def remove_disabled_attr(match):
    tag = match.group(0)
    tag = re.sub(r'\sdisabled\b', '', tag)
    return tag

html = re.sub(
    r'<input[^>]*id=["\']fileInput["\'][^>]*>',
    remove_disabled_attr,
    html
)

with open('static/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
