import re
import yaml

text = '''
steps:
  - id: step_1
    process_command_line: "cmd.exe /c ntdsutil.exe \\"ac i ntds\\" \\"ifm\\" \\"create full c:\\\\temp\\" q q"
'''

def escape_backslashes_in_quotes(match: re.Match) -> str:
    inner = match.group(1)
    inner = re.sub(r'(?<!\\)\\(?![\\"])', r'\\\\', inner)
    return f'"{inner}"'

new_text = re.sub(r'"([^"\\]*(?:\\.[^"\\]*)*)"', escape_backslashes_in_quotes, text)

print("NEW TEXT:")
print(repr(new_text))

try:
    print(yaml.safe_load(new_text))
except Exception as e:
    print("ERROR:")
    print(e)
