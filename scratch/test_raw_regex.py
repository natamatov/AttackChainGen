import re
import yaml

yaml_text = r'''
steps:
  - id: step_1
    process_command_line: @"ntdsutil.exe ""ac i ntds"" ""ifm"" ""create full c:\temp"" q q"
    process_path: @"C:\Windows\System32\cmd.exe"
'''

def raw_string_replace(match: re.Match) -> str:
    inner = match.group(1)
    inner = inner.replace('""', '"')
    escaped = inner.replace('\\', '\\\\').replace('"', '\\"')
    return f'"{escaped}"'

new_text = re.sub(r'@"((?:[^"]|"")*)"', raw_string_replace, yaml_text)

print("NEW TEXT:")
print(new_text)

try:
    data = yaml.safe_load(new_text)
    print("YAML LOADED:")
    print(data)
except Exception as e:
    print("ERROR:", e)
