import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.111.187', username='eramba', password='eramba')
stdin, stdout, stderr = ssh.exec_command("echo eramba | sudo -S docker exec attackchain_backend cat /app/migrations/versions/f345a957dd06_rename_cidr_to_ip_range.py")
content = stdout.read().decode()
with open("backend/migrations/versions/f345a957dd06_rename_cidr_to_ip_range.py", "w", encoding="utf-8") as f:
    f.write(content)
ssh.close()
print("Saved!")
