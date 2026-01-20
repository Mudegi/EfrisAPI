#!/usr/bin/env python3
"""
T104 Response Analysis - Inspect full response structure
"""

import json
from efris_client import EfrisManager

print("="*100)
print("T104 RESPONSE STRUCTURE ANALYSIS")
print("="*100)

manager = EfrisManager(tin='1014409555', test_mode=True)

# Build T104 payload
t104_payload = manager._build_handshake_payload("T104", "")

# Send request
response = manager.session.post(
    manager.base_url,
    json=t104_payload,
    headers=manager._get_headers()
)

response_data = response.json()

print("\nFull Response Structure:")
print(json.dumps(response_data, indent=2))

print("\n" + "="*100)
print("DETAILED ANALYSIS:")
print("="*100)

# Check top level
print("\nTop-level keys:")
for key in response_data.keys():
    print(f"  - {key}: {type(response_data[key]).__name__}")

# Check data section
data_section = response_data.get('data', {})
print(f"\nData section type: {type(data_section).__name__}")
print("\nData section keys:")
if isinstance(data_section, dict):
    for key in data_section.keys():
        value = data_section[key]
        if isinstance(value, dict):
            print(f"  - {key}: (dict with keys: {list(value.keys())})")
        elif isinstance(value, str):
            print(f"  - {key}: (str, length={len(value)})")
        else:
            print(f"  - {key}: ({type(value).__name__})")

# Look for key-related fields
print("\n" + "-"*100)
print("SEARCHING FOR KEY MATERIAL:")
print("-"*100)

def search_for_key_material(obj, path=""):
    """Recursively search for fields that might contain key material"""
    if isinstance(obj, dict):
        for key, value in obj.items():
            new_path = f"{path}.{key}" if path else key
            if any(keyword in key.lower() for keyword in ["key", "pass", "encrypt", "des", "aes", "pwd", "secret"]):
                if isinstance(value, str) and value:
                    print(f"  Found at '{new_path}': {value[:100]}...")
                elif isinstance(value, (dict, list)):
                    print(f"  Found at '{new_path}': {type(value).__name__}")
            if isinstance(value, (dict, list)):
                search_for_key_material(value, new_path)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            new_path = f"{path}[{i}]"
            search_for_key_material(item, new_path)

search_for_key_material(response_data)

# Print the actual data section
print("\n" + "-"*100)
print("ACTUAL DATA SECTION:")
print("-"*100)
print(json.dumps(data_section, indent=2))
