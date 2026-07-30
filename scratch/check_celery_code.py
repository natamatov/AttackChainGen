import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.111.187', username='eramba', password='eramba')
stdin, stdout, stderr = ssh.exec_command('echo eramba | sudo -S docker exec attackchain_celery cat /app/app/workers/playbook_parser.py')
code = stdout.read().decode('utf-8')
lines = code.split('\n')
for i, line in enumerate(lines):
    if 'escape_backslashes_in_quotes' in line:
        for j in range(max(0, i-2), min(len(lines), i+8)):
            print(f"{j}: {lines[j]}")
        break
