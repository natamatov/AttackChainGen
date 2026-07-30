import sys
from app.workers.template_engine import TemplateEngine, TemplateRenderError

engine = TemplateEngine()

print("Testing known template (win_security_4624):")
try:
    doc = engine.render("win_security_4624", {"user_name": "hacker"})
    print("SUCCESS: Event generated with @timestamp =", doc.get("@timestamp"))
except Exception as e:
    print("ERROR:", e)

print("\nTesting missing template (should fallback to generic_event):")
try:
    doc = engine.render("this_template_does_not_exist", {"some_weird_field": "hacked"})
    print("SUCCESS: Event generated with @timestamp =", doc.get("@timestamp"))
    print("Labels:", doc.get("labels"))
    print("Message:", doc.get("message"))
except Exception as e:
    print("ERROR:", e)

print("\nTesting undefined variables:")
try:
    # generic_event has {{ user_name }} which is not provided here
    doc = engine.render("generic_event", {"some_field": "abc"})
    print("SUCCESS! User name was:", doc.get("user", {}).get("name"))
except Exception as e:
    print("ERROR:", e)
