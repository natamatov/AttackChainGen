from jinja2 import Environment, Undefined

env = Environment(undefined=Undefined)
t = env.from_string('{{ "Hello " ~ x }}')
try:
    print("Output:", t.render())
except Exception as e:
    print("ERROR:", e)

# Test with + operator
t2 = env.from_string('{{ "Hello " + x }}')
try:
    print("Output2:", t2.render())
except Exception as e:
    print("ERROR2:", e)
