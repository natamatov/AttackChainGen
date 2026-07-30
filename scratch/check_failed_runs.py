import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.111.187', username='eramba', password='eramba')
query = "SELECT id, playbook_name, error_message FROM simulation_runs WHERE id >= 132 AND status = 'FAILED';"
stdin, stdout, stderr = ssh.exec_command(f'echo eramba | sudo -S docker exec attackchain_postgres psql -U attackchain -d attackchaindb -c "{query}"')
print(stdout.read().decode('utf-8', errors='replace'))
