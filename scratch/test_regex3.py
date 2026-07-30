import re
import yaml

def escape_backslashes_in_quotes(match: re.Match) -> str:
    inner = match.group(1)
    inner = re.sub(r'(?<!\\)\\(?![\\"])', r'\\\\', inner)
    return f'"{inner}"'

text = r'''
playbook:
  process_path: "C:\Windows\System32"
  unquoted: C:\Windows\System32
  already_escaped: "C:\\Windows\\System32"
  mixed: "C:\temp\file.txt"
  with_quotes: "cmd.exe /c ntdsutil.exe \"ac i ntds\" \"ifm\""
'''

new_text = re.sub(r'"([^"\\]*(?:\\.[^"\\]*)*)"', escape_backslashes_in_quotes, text)
print("FIXED:")
print(new_text)

try:
    data = yaml.safe_load(new_text)
    print("YAML LOADED SUCCESSFULLY:")
    print(data)
except Exception as e:
    print("YAML ERROR:", e)
