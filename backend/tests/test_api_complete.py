#!/usr/bin/env python3
import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"

# Register user with unique email
timestamp = int(time.time())
email = f"test{timestamp}@example.com"
print(f"Registering user: {email}")
reg = requests.post(f"{BASE_URL}/auth/register", json={
    "name": "APITest",
    "email": email,
    "password": "test12345",
    "role": "Staff"
})

if reg.status_code not in [200, 201]:
    print(f"Registration error: {reg.status_code}")
    print(reg.text)
    exit(1)

token = reg.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Test citizens
print("\n1. CITIZENS ENDPOINT:")
r = requests.get(f"{BASE_URL}/citizens?limit=10", headers=headers)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"Total citizens in DB: {data.get('total', 0)}")
    print(f"Citizens returned: {len(data.get('citizens', []))}")
    if data.get('citizens'):
        c = data['citizens'][0]
        print(f"Sample: {c.get('name')} - Ward {c.get('ward')}")

# Test issues
print("\n2. ISSUES ENDPOINT:")
r = requests.get(f"{BASE_URL}/issues?limit=10", headers=headers)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"Total issues in DB: {data.get('total', 0)}")
    print(f"Issues returned: {len(data.get('issues', []))}")
    if data.get('issues'):
        i = data['issues'][0]
        print(f"Sample: {i.get('title')} - {i.get('status')}")

# Test dashboard
print("\n3. DASHBOARD ENDPOINT:")
r = requests.get(f"{BASE_URL}/dashboard", headers=headers)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"Total issues: {data.get('total_issues', 0)}")
    print(f"Open issues: {data.get('open_issues', 0)}")
    print(f"Total citizens: {data.get('total_citizens', 0)}")
    print(f"Total documents: {data.get('total_documents', 0)}")
