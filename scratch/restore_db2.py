import paramiko
import sys

sys.stdout.reconfigure(encoding='utf-8')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.111.187', username='eramba', password='eramba')

# 1. Take down unified_soc just in case they are running there
ssh.exec_command('cd unified_soc && echo eramba | sudo -S docker compose down')

# 3. Upload modified docker-compose.yml
local_compose_path = r"D:\AttackChainGen\docker-compose.yml"
sftp = ssh.open_sftp()
sftp.put(local_compose_path, '/home/eramba/AttackChainGen/docker-compose.yml')
sftp.close()

# 4. Restart containers in AttackChainGen (with explicit project name to be safe)
stdin, stdout, stderr = ssh.exec_command('cd AttackChainGen && echo eramba | sudo -S docker compose down && echo eramba | sudo -S docker compose --project-name attackchaingen up -d')
print("STDOUT:", stdout.read().decode('utf-8', errors='replace'))
print("STDERR:", stderr.read().decode('utf-8', errors='replace'))
