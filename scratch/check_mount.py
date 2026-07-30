import paramiko
import sys
import json

sys.stdout.reconfigure(encoding='utf-8')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.111.187', username='eramba', password='eramba')

stdin, stdout, stderr = ssh.exec_command('echo eramba | sudo -S docker inspect attackchain_postgres --format="{{json .Mounts}}"')
output = stdout.read().decode('utf-8', errors='replace')
try:
    mounts = json.loads(output)
    for m in mounts:
        print(f"Mount Name: {m.get('Name')}")
        print(f"Mount Source: {m.get('Source')}")
except Exception as e:
    print(output)
