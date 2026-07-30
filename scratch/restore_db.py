import paramiko
import sys
import yaml

sys.stdout.reconfigure(encoding='utf-8')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.111.187', username='eramba', password='eramba')

# 1. Take down unified_soc just in case they are running there
ssh.exec_command('cd unified_soc && echo eramba | sudo -S docker compose down')

# 2. Modify local AttackChainGen docker-compose.yml
local_compose_path = r"D:\AttackChainGen\docker-compose.yml"
with open(local_compose_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace volumes at the bottom
new_volumes = """volumes:
  postgres_data:
    name: attackchaingen_postgres_data
    external: true
  redis_data:
    name: attackchaingen_redis_data
    external: true"""

if "volumes:" in content:
    content = content[:content.find("volumes:")] + new_volumes
else:
    content += "\n" + new_volumes

with open(local_compose_path, 'w', encoding='utf-8') as f:
    f.write(content)

# 3. Upload modified docker-compose.yml
sftp = ssh.open_sftp()
sftp.put(local_compose_path, '/home/eramba/AttackChainGen/docker-compose.yml')
sftp.close()

# 4. Restart containers in AttackChainGen (with explicit project name to be safe)
stdin, stdout, stderr = ssh.exec_command('cd AttackChainGen && echo eramba | sudo -S docker compose down && echo eramba | sudo -S docker compose --project-name attackchaingen up -d')
print(stdout.read().decode('utf-8', errors='replace'))
print(stderr.read().decode('utf-8', errors='replace'))
