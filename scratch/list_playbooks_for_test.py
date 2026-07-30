import paramiko
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.111.187', username='eramba', password='eramba')

query = "SELECT id, name FROM playbooks ORDER BY id;"
stdin, stdout, stderr = ssh.exec_command(f'echo eramba | sudo -S docker exec attackchain_postgres psql -U attackchain -d attackchaindb -t -A -c "{query}"')
playbooks = stdout.read().decode('utf-8').strip().split('\n')

query2 = "SELECT id, name FROM stands WHERE is_active = true ORDER BY id LIMIT 1;"
stdin, stdout, stderr = ssh.exec_command(f'echo eramba | sudo -S docker exec attackchain_postgres psql -U attackchain -d attackchaindb -t -A -c "{query2}"')
stand = stdout.read().decode('utf-8').strip()

print(f"Stand: {stand}")
print("Playbooks:")
for pb in playbooks:
    print(pb)
