import requests
import sys

sys.stdout.reconfigure(encoding='utf-8')
BASE_URL = "http://192.168.111.187/api"

login_data = {
    "username": "admin@attackchain.local",
    "password": "Admin1234!"
}
r = requests.post(f"{BASE_URL}/auth/login", data=login_data)
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

payload = {
    "playbook_id": 24,
    "stand_id": 2,
    "mode": "realtime"
}
r = requests.post(f"{BASE_URL}/simulations/run", json=payload, headers=headers)
print(r.text)
