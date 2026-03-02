"""Quick test for notifications with upcoming events."""
import requests

r = requests.post("http://localhost:8000/api/v1/auth/login", json={"email": "admin@nayam.gov.in", "password": "admin12345"})
token = r.json()["access_token"]
h = {"Authorization": f"Bearer {token}"}

r = requests.get("http://localhost:8000/api/v1/notifications", headers=h)
data = r.json()
print(f"Status: {r.status_code}, Total notifications: {data['total']}")
for item in data["items"][:10]:
    print(f"  [{item['severity']:8s}] {item['type']:20s} | {item['title']}")
    print(f"           {item['detail'][:80]}")
    print()
