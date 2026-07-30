import paramiko
import sys

sys.stdout.reconfigure(encoding='utf-8')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.111.187', username='eramba', password='eramba')

query = "SELECT id, playbook_name, status, error_message, created_at FROM simulation_runs WHERE status = 'FAILED' ORDER BY created_at DESC LIMIT 5;"
stdin, stdout, stderr = ssh.exec_command(f'echo eramba | sudo -S docker exec attackchain_postgres psql -U attackchain -d attackchaindb -c "{query}"')
print(stdout.read().decode('utf-8', errors='replace'))
print(stderr.read().decode('utf-8', errors='replace'))
