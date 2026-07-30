import paramiko
import sys

sys.stdout.reconfigure(encoding='utf-8')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.111.187', username='eramba', password='eramba')

stdin, stdout, stderr = ssh.exec_command('echo eramba | sudo -S docker rm -f attackchain_frontend attackchain_backend attackchain_flower attackchain_celery attackchain_postgres attackchain_redis')
print(stdout.read().decode('utf-8', errors='replace'))

stdin, stdout, stderr = ssh.exec_command('cd AttackChainGen && echo eramba | sudo -S docker compose --project-name attackchaingen up -d')
print(stdout.read().decode('utf-8', errors='replace'))
print(stderr.read().decode('utf-8', errors='replace'))
