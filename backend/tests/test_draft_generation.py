#!/usr/bin/env python3
"""Test draft generation with correct DraftType"""
import requests
import time
import json

BASE_URL = "http://localhost:8000/api/v1"

print("=" * 70)
print("TEST DRAFT GENERATION")
print("=" * 70)

# Register user
timestamp = int(time.time())
email = f'drafttest{timestamp}@example.com'

reg = requests.post(f'{BASE_URL}/auth/register', json={
    'name': 'DraftTest',
    'email': email,
    'password': 'test12345',
    'role': 'Staff'
})

if reg.status_code not in [200, 201]:
    print(f"❌ Registration failed: {reg.status_code}")
    exit(1)

token = reg.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

print("✅ Registered user")

# Test all draft types
draft_types = [
    "Speech",
    "Official Response",
    "Press Release",
    "Policy Brief",
    "Meeting Agenda",
    "Public Notice",
    "Formal Letter",
    "RTI Response",
    "Government Circular"
]

print("\nTesting all draft types:")
print("-" * 70)

for dtype in draft_types:
    payload = {
        "draft_type": dtype,
        "topic": "Test topic for draft generation",
        "tone": "Formal",
        "audience": "Citizens",
        "department": "General Department",
        "additional_context": "Test context"
    }
    
    r = requests.post(f'{BASE_URL}/drafts/generate', 
        headers=headers,
        json=payload
    )
    
    if r.status_code == 201:
        data = r.json()
        print(f"✅ {dtype}: Draft generated (ID: {data['id'][:8]}...)")
    else:
        print(f"❌ {dtype}: Status {r.status_code}")
        try:
            errors = r.json()
            if isinstance(errors.get('detail'), list):
                for err in errors['detail']:
                    print(f"   Error: {err.get('msg', 'Unknown')}")
            else:
                print(f"   Error: {errors.get('detail', 'Unknown')}")
        except:
            print(f"   Response: {r.text[:100]}")

print("\n" + "=" * 70)
print("✅ TEST COMPLETE")
print("=" * 70)
