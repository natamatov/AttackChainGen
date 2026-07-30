import requests
import time
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

run_ids = list(range(132, 152))
print(f"Monitoring runs: {run_ids}\n")

completed = set()
failed = {}

while len(completed) + len(failed) < len(run_ids):
    time.sleep(5)
    r = requests.get(f"{BASE_URL}/simulations/?limit=100", headers=headers)
    data = r.json()
    sims = data.get("items", data) if isinstance(data, dict) else data
    
    for sim in sims:
        sim_id = sim["id"]
        if sim_id in run_ids:
            status = sim["status"].lower()
            if status == "completed" and sim_id not in completed:
                completed.add(sim_id)
                print(f"[{sim_id}] COMPLETED: {sim.get('playbook_name', 'Unknown')}")
            elif status == "failed" and sim_id not in failed:
                failed[sim_id] = {
                    "name": sim.get("playbook_name", "Unknown"),
                    "error": sim.get("error_message", "No error message")
                }
                print(f"[{sim_id}] FAILED: {sim.get('playbook_name', 'Unknown')} - {sim.get('error_message')}")

print("\n=== SUMMARY ===")
print(f"Total: {len(run_ids)}")
print(f"Completed: {len(completed)}")
print(f"Failed: {len(failed)}")
for run_id, info in failed.items():
    print(f" - [{run_id}] {info['name']}: {info['error']}")
