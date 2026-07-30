import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.111.187', username='eramba', password='eramba')
stdin, stdout, stderr = ssh.exec_command("echo eramba | sudo -S docker logs attackchain_celery --tail 50")
print('STDOUT:', stdout.read().decode())
print('STDERR:', stderr.read().decode())
ssh.close()
