import paramiko
import sys

sys.stdout.reconfigure(encoding='utf-8')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.111.187', username='eramba', password='eramba')

stdin, stdout, stderr = ssh.exec_command('echo eramba | sudo -S cat AttackChainGen/.env | grep COMPOSE_PROJECT_NAME')
print("AttackChainGen/.env:", stdout.read().decode('utf-8', errors='replace'))

stdin, stdout, stderr = ssh.exec_command('echo eramba | sudo -S cat unified_soc/.env | grep COMPOSE_PROJECT_NAME')
print("unified_soc/.env:", stdout.read().decode('utf-8', errors='replace'))
