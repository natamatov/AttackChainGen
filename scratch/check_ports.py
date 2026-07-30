import paramiko
import sys

sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.111.187', username='eramba', password='eramba')

stdin, stdout, stderr = ssh.exec_command('echo eramba | sudo -S ss -tulpn')
ss_output = stdout.read().decode('utf-8', errors='replace')

stdin, stdout, stderr = ssh.exec_command('echo eramba | sudo -S docker ps --format "table {{.Names}}\\t{{.Ports}}"')
docker_output = stdout.read().decode('utf-8', errors='replace')

print('=== Listening Ports (ss -tulpn) ===')
print(ss_output)
print('\n=== Docker Ports ===')
print(docker_output)
