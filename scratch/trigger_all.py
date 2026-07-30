import requests
import time
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
BASE_URL = "http://192.168.111.187/api"

# 1. Login
login_data = {
    "username": "admin@attackchain.local",
    "password": "Admin1234!"
}
r = requests.post(f"{BASE_URL}/auth/login", data=login_data)
if r.status_code != 200:
    print(f"Login failed: {r.text}")
    sys.exit(1)

token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 2. Get playbooks and stand
r = requests.get(f"{BASE_URL}/playbooks/", headers=headers)
playbooks = r.json()

r = requests.get(f"{BASE_URL}/stands/", headers=headers)
stands = r.json()
if not stands:
    print("No active stands found.")
    sys.exit(1)

stand_id = stands[0]["id"]
print(f"Using Stand ID: {stand_id} ({stands[0]['name']})")

# 3. Trigger all
run_ids = []
for pb in playbooks:
    payload = {
        "playbook_id": pb["id"],
        "stand_id": stand_id,
        "mode": "realtime"
    }
    r = requests.post(f"{BASE_URL}/simulations/run", json=payload, headers=headers)
    if r.status_code == 200:
        run_info = r.json()
        run_ids.append(run_info["id"])
        print(f"Started run {run_info['id']} for Playbook '{pb['name']}'")
    else:
        print(f"Failed to start playbook {pb['name']}: {r.text}")

print(f"\nMonitoring {len(run_ids)} runs...\n")

# 4. Monitor
completed = set()
failed = {}
while len(completed) + len(failed) < len(run_ids):
    time.sleep(5)
    r = requests.get(f"{BASE_URL}/simulations/?limit=100", headers=headers)
    sims = r.json()["items"]
    
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
