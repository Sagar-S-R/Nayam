#!/usr/bin/env python3
"""Test Add Citizen API endpoints"""

import requests
import json
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import create_access_token

BASE_URL = "http://localhost:8000/api/v1"

# Get token
db = SessionLocal()
user = db.query(User).filter(User.role == "Leader").first()
token = create_access_token(data={"sub": str(user.id), "role": user.role})
headers = {"Authorization": f"Bearer {token}"}
db.close()

print("=" * 70)
print("API TEST RESULTS - ADD CITIZEN FLOW")
print("=" * 70)

# Test 1: Wards
print("\n[1] GET /citizens/wards")
resp = requests.get(f"{BASE_URL}/citizens/wards", headers=headers)
print(f"Status: {resp.status_code}")
print(f"Wards: {resp.json()['wards']}")

# Test 2: Valid citizen
print("\n[2] POST /citizens (Valid Data)")
resp = requests.post(f"{BASE_URL}/citizens/", json={
    "name": "John API Test",
    "contact_number": "+919876543210",
    "ward": "Ward-1"
}, headers=headers)
print(f"Status: {resp.status_code}")
if resp.status_code == 201:
    c = resp.json()
    print(f"✅ Citizen created:")
    print(f"   - Name: {c['name']}")
    print(f"   - Full: {c['contact_number']}")
    print(f"   - Masked: {c.get('masked_contact')}")
    print(f"   - Ward: {c['ward']}")

# Test 3: Invalid phone
print("\n[3] POST /citizens (Invalid Phone)")
resp = requests.post(f"{BASE_URL}/citizens/", json={
    "name": "Test",
    "contact_number": "invalid",
    "ward": "Ward-1"
}, headers=headers)
print(f"Status: {resp.status_code}")
if resp.status_code != 201:
    err = resp.json()['detail'][0]['msg']
    print(f"✅ Rejected: {err}")

# Test 4: Invalid ward
print("\n[4] POST /citizens (Invalid Ward)")
resp = requests.post(f"{BASE_URL}/citizens/", json={
    "name": "Test",
    "contact_number": "+919876543210",
    "ward": "InvalidWard"
}, headers=headers)
print(f"Status: {resp.status_code}")
if resp.status_code != 201:
    err = resp.json()['detail'][0]['msg']
    print(f"✅ Rejected: {err}")

print("\n" + "=" * 70)
print("✅ API TESTS COMPLETE")
print("=" * 70)
