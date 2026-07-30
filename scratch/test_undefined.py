from jinja2 import Environment, Undefined
import json

env = Environment(undefined=Undefined)
env.filters['tojson'] = json.dumps

t = env.from_string('{"name": "{{ x }}", "obj": {{ x | tojson }}, "num": {{ y | default(123) }} }')
try:
    print(t.render())
except Exception as e:
    print("ERROR:", e)
