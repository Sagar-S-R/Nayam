#!/usr/bin/env python3
"""
Comprehensive test of Add Citizen flow from start to finish
"""
import requests
import time
import json

BASE_URL = "http://localhost:8000/api/v1"

print("=" * 70)
print("COMPREHENSIVE ADD CITIZEN TEST")
print("=" * 70)

# Step 1: Register user
print("\n1️⃣ REGISTER USER")
print("-" * 70)
timestamp = int(time.time())
email = f'fulltest{timestamp}@example.com'
print(f"Email: {email}")

reg = requests.post(f'{BASE_URL}/auth/register', json={
    'name': 'FullTest',
    'email': email,
    'password': 'test12345',
    'role': 'Staff'
})

if reg.status_code not in [200, 201]:
    print(f"❌ Registration failed: {reg.status_code}")
    print(reg.text)
    exit(1)

user_data = reg.json()
token = user_data['access_token']
print(f"✅ Registered successfully")
print(f"   Token: {token[:40]}...")
headers = {'Authorization': f'Bearer {token}'}

# Step 2: Fetch wards
print("\n2️⃣ FETCH WARD LIST")
print("-" * 70)
r = requests.get(f'{BASE_URL}/citizens/wards', headers=headers)
if r.status_code != 200:
    print(f"❌ Failed to fetch wards: {r.status_code}")
    print(r.text)
    exit(1)

wards = r.json().get('wards', [])
print(f"✅ Wards retrieved: {len(wards)}")
print(f"   Wards: {wards}")

# Step 3: Create citizen with valid data
print("\n3️⃣ CREATE CITIZEN")
print("-" * 70)

test_data = {
    'name': 'John Doe Smith',
    'contact_number': '+919876543210',
    'ward': wards[0] if wards else 'Ward-1'
}

print(f"Creating citizen with:")
print(f"   Name: {test_data['name']}")
print(f"   Phone: {test_data['contact_number']}")
print(f"   Ward: {test_data['ward']}")

r = requests.post(f'{BASE_URL}/citizens', 
    headers=headers,
    json=test_data
)

print(f"Response Status: {r.status_code}")

if r.status_code == 201:
    citizen = r.json()
    print(f"✅ CITIZEN CREATED SUCCESSFULLY!")
    print(f"   ID: {citizen['id']}")
    print(f"   Name: {citizen['name']}")
    print(f"   Contact: {citizen['contact_number']}")
    print(f"   Masked: {citizen['masked_contact']}")
    print(f"   Ward: {citizen['ward']}")
    print(f"   Created: {citizen['created_at']}")
else:
    print(f"❌ Failed to create citizen: {r.status_code}")
    print(f"Response: {r.text}")
    exit(1)

# Step 4: Verify citizen appears in list
print("\n4️⃣ VERIFY CITIZEN IN LIST")
print("-" * 70)
r = requests.get(f'{BASE_URL}/citizens?limit=5', headers=headers)
if r.status_code != 200:
    print(f"❌ Failed to fetch citizens: {r.status_code}")
    exit(1)

data = r.json()
total = data.get('total', 0)
citizens = data.get('citizens', [])

# Find our newly created citizen
found = None
for c in citizens:
    if c['id'] == citizen['id']:
        found = c
        break

if found:
    print(f"✅ Citizen found in list!")
    print(f"   Name: {found['name']}")
    print(f"   Ward: {found['ward']}")
    print(f"   Masked Contact: {found.get('masked_contact', 'N/A')}")
else:
    print(f"⚠️  Citizen not found in top 5 (might be paginated)")

print(f"\nTotal citizens in DB: {total}")
print(f"Citizens in response: {len(citizens)}")

# Step 5: Test validation errors
print("\n5️⃣ TEST VALIDATION ERRORS")
print("-" * 70)

invalid_tests = [
    {
        'name': 'Short Name',
        'data': {'name': 'J', 'contact_number': '9876543210', 'ward': wards[0] if wards else 'Ward-1'},
        'expect_error': True
    },
    {
        'name': 'Invalid Phone',
        'data': {'name': 'Valid Name', 'contact_number': '12345', 'ward': wards[0] if wards else 'Ward-1'},
        'expect_error': True
    },
    {
        'name': 'Invalid Ward',
        'data': {'name': 'Valid Name', 'contact_number': '9876543210', 'ward': 'InvalidWard'},
        'expect_error': True
    },
]

for test in invalid_tests:
    r = requests.post(f'{BASE_URL}/citizens', headers=headers, json=test['data'])
    if r.status_code != 201:
        print(f"✅ {test['name']}: Correctly rejected ({r.status_code})")
    else:
        print(f"⚠️  {test['name']}: Should have failed but succeeded!")

print("\n" + "=" * 70)
print("✅ COMPREHENSIVE TEST COMPLETE")
print("=" * 70)
