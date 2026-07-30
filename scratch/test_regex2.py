import re

def escape_backslashes_in_quotes(match: re.Match) -> str:
    inner = match.group(1)
    inner = re.sub(r'(?<!\\)\\(?!\\)', r'\\\\', inner)
    return f'"{inner}"'

text = r'''
playbook:
  process_path: "C:\Windows\System32"
  unquoted: C:\Windows\System32
  already_escaped: "C:\\Windows\\System32"
  mixed: "C:\temp\file.txt"
'''

new_text = re.sub(r'"([^"\\]*(?:\\.[^"\\]*)*)"', escape_backslashes_in_quotes, text)
print("ORIGINAL:")
print(text)
print("FIXED:")
print(new_text)

import yaml
try:
    data = yaml.safe_load(new_text)
    print("YAML LOADED SUCCESSFULLY:")
    print(data)
except Exception as e:
    print("YAML ERROR:", e)
