"""
Script to add timeout parameter to all EFRIS requests
Run this once to update efris_client.py
"""
import re

# Read the file
with open('d:/EfrisAPI/efris_client.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern to find self.session.post() or self.session.get() without timeout
pattern1 = r'(self\.session\.post\([^)]+)\)(?!\s*,\s*timeout)'
pattern2 = r'(self\.session\.get\([^)]+)\)(?!\s*,\s*timeout)'

# Replace pattern 1 (post)
def replace_post(match):
    return match.group(1) + ', timeout=self.request_timeout)'

# Replace pattern 2 (get)
def replace_get(match):
    return match.group(1) + ', timeout=self.request_timeout)'

# Count matches
post_matches = len(re.findall(pattern1, content))
get_matches = len(re.findall(pattern2, content))

print(f"Found {post_matches} POST requests and {get_matches} GET requests without timeout")

# Apply replacements
new_content = re.sub(pattern1, replace_post, content)
new_content = re.sub(pattern2, replace_get, new_content)

# Write back
with open('d:/EfrisAPI/efris_client.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"✅ Added timeout to {post_matches + get_matches} EFRIS requests")
