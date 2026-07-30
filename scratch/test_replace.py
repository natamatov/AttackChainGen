import re

text = '      process_command_line: "cmd.exe /c ntdsutil.exe \\"ac i ntds\\" \\"ifm\\" \\"create full c:\\\\temp\\" q q"'
print("Original:")
print(repr(text))

new_text = text.replace('\\\\"', '\\"')
print("Replaced:")
print(repr(new_text))
