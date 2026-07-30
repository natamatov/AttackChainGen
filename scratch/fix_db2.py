import psycopg2

conn = psycopg2.connect(
    dbname="attackchaindb",
    user="attackchain",
    password="strongpassword",
    host="postgres",
    port="5432"
)
cur = conn.cursor()

cur.execute("SELECT id, yaml_content FROM playbooks;")
rows = cur.fetchall()

updated = 0
for row in rows:
    pb_id, yaml_text = row
    if not yaml_text:
        continue
        
    original = yaml_text
    
    # \\" is \ \ "
    # We want to replace it with \" which is \ "
    if '\\\\"' in yaml_text:
        yaml_text = yaml_text.replace('\\\\"', '\\"')
        
    if yaml_text != original:
        cur.execute("UPDATE playbooks SET yaml_content = %s WHERE id = %s;", (yaml_text, pb_id))
        updated += 1

conn.commit()
cur.close()
conn.close()

print(f"Updated {updated} playbooks in the database.")
