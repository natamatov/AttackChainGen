import psycopg2
from app.workers.playbook_parser import PlaybookParser

conn = psycopg2.connect(
    dbname="attackchaindb",
    user="attackchain",
    password="strongpassword",
    host="postgres",
    port="5432"
)
cur = conn.cursor()
cur.execute("SELECT id, yaml_content FROM playbooks WHERE name = 'Phishing Attack with Lateral Movement';")
row = cur.fetchone()

pb_id, yaml_text = row
print("Got playbook!")
try:
    pb = PlaybookParser.from_yaml(yaml_text)
    print("SUCCESS!")
except Exception as e:
    print("FAILED TO PARSE:")
    import traceback
    traceback.print_exc()

cur.close()
conn.close()
