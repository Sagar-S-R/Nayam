"""Quick test for schedule and drafts APIs."""
import requests

r = requests.post("http://localhost:8000/api/v1/auth/login", json={"email": "admin@nayam.gov.in", "password": "admin12345"})
token = r.json()["access_token"]
h = {"Authorization": f"Bearer {token}"}

print("=== SCHEDULE ===")
r = requests.get("http://localhost:8000/api/v1/schedule/", headers=h)
data = r.json()
print(f"Status: {r.status_code}, Total events: {data['total']}")
for e in data["events"][:3]:
    print(f"  - {e['title']} ({e['event_type']}, {e['status']})")

print()
r = requests.get("http://localhost:8000/api/v1/schedule/upcoming/list", headers=h)
data = r.json()
print(f"Upcoming: {data['total']} events")

print()
print("=== DRAFTS ===")
r = requests.get("http://localhost:8000/api/v1/drafts/", headers=h)
data = r.json()
print(f"Status: {r.status_code}, Total drafts: {data['total']}")
for d in data["drafts"]:
    print(f"  - {d['title']} ({d['draft_type']}, {d['status']}, v{d['version']})")
print()
print("ALL APIs OK!")
