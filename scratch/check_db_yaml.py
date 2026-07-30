import psycopg2

conn = psycopg2.connect(
    dbname="attackchaindb",
    user="attackchain",
    password="strongpassword",
    host="postgres",
    port="5432"
)
cur = conn.cursor()

cur.execute("SELECT id, yaml_content FROM playbooks WHERE name = 'Phishing Attack with Lateral Movement';")
rows = cur.fetchall()

for row in rows:
    pb_id, yaml_text = row
    print("-------")
    print(pb_id)
    print(yaml_text[:500])
    lines = yaml_text.split("\n")
    for idx, line in enumerate(lines):
        if "process_command_line" in line or "ntdsutil" in line:
            print(f"Line {idx}: {line}")
            print(repr(line))

cur.close()
conn.close()
