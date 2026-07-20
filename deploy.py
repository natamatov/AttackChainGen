import paramiko
import time
import sys

def deploy():
    host = "192.168.111.187"
    user = "eramba"
    password = "eramba"

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"Connecting to {host}...")
    try:
        ssh.connect(host, username=user, password=password, timeout=10, auth_timeout=10, look_for_keys=False, allow_agent=False)
    except Exception as e:
        print(f"Failed to connect: {e}")
        sys.exit(1)

    print("Connected. Running deployment commands...")
    commands = [
        "if [ ! -d 'AttackChainGen' ]; then git clone https://github.com/natamatov/AttackChainGen.git; fi",
        "cd AttackChainGen && git pull origin master",
        "cd AttackChainGen && touch .env",
        "cd AttackChainGen && echo 'eramba' | sudo -S docker compose up -d --force-recreate"
    ]

    for cmd in commands:
        print(f"Executing: {cmd}")
        stdin, stdout, stderr = ssh.exec_command(cmd)
        
        # Read output fully before waiting for exit status to prevent buffer deadlock
        out = stdout.read().decode('utf-8', errors='replace').strip()
        err = stderr.read().decode('utf-8', errors='replace').strip()
        exit_status = stdout.channel.recv_exit_status()
        
        if out:
            print(f"STDOUT:\n{out}".encode('cp1251', errors='replace').decode('cp1251'))
        if err:
            print(f"STDERR:\n{err}".encode('cp1251', errors='replace').decode('cp1251'))
        
        if exit_status != 0:
            print(f"Command failed with exit status {exit_status}")
            sys.exit(exit_status)

    print("Deployment completed successfully!")
    ssh.close()

if __name__ == '__main__':
    deploy()
