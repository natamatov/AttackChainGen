from jinja2 import Environment, Undefined

class SafeUndefined(Undefined):
    def __str__(self):
        return ""
    def __repr__(self):
        return ""
    def __add__(self, other):
        return other
    def __radd__(self, other):
        return other

env = Environment(undefined=SafeUndefined)
t2 = env.from_string('{{ "Hello " + x }}')
try:
    print("Output2:", t2.render())
except Exception as e:
    print("ERROR2:", e)
