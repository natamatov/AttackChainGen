import paramiko
import sys

sys.stdout.reconfigure(encoding='utf-8')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.111.187', username='eramba', password='eramba')

stdin, stdout, stderr = ssh.exec_command('echo eramba | sudo -S cat unified_soc/docker-compose.yml | tail -n 10')
print(stdout.read().decode('utf-8', errors='replace'))
