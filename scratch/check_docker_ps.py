import paramiko
import sys

# Ensure stdout uses utf-8
sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.111.187', username='eramba', password='eramba')

stdin, stdout, stderr = ssh.exec_command('cd AttackChainGen && echo eramba | sudo -S docker compose ps')
print(stdout.read().decode('utf-8', errors='replace'))
