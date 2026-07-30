import psycopg2
conn = psycopg2.connect(dbname="attackchaindb", user="attackchain", password="strongpassword", host="192.168.111.187", port="5432")
cur = conn.cursor()
cur.execute("SELECT name FROM playbooks;")
rows = cur.fetchall()
for r in rows:
    print("-", r[0])
cur.close()
conn.close()
