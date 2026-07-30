import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.111.187', username='eramba', password='eramba')
stdin, stdout, stderr = ssh.exec_command('curl -s -w "\n%{http_code}" http://localhost/api/environments/')
print(stdout.read().decode(errors='replace'))
print(stderr.read().decode(errors='replace'))
