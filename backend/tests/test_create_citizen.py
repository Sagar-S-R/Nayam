#!/usr/bin/env python3
import requests
import time

timestamp = int(time.time())
email = f'createtest{timestamp}@example.com'

# Register
reg = requests.post('http://localhost:8000/api/v1/auth/register', json={
    'name': 'CreateTest',
    'email': email,
    'password': 'test12345', 
    'role': 'Staff'
})

if reg.status_code not in [200, 201]:
    print(f"Registration failed: {reg.status_code}")
    print(reg.text)
    exit(1)

token = reg.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# Test create citizen
print("Creating citizen...")
r = requests.post('http://localhost:8000/api/v1/citizens', 
    headers=headers,
    json={
        'name': 'Test Citizen',
        'contact_number': '+919876543210',
        'ward': 'Ward-1'
    })

print(f'Status: {r.status_code}')
print(f'Response:\n{r.text}')

# Fetch to verify
print("\nFetching citizens to verify...")
r2 = requests.get('http://localhost:8000/api/v1/citizens?limit=5', headers=headers)
if r2.status_code == 200:
    data = r2.json()
    print(f"Total: {data.get('total')}")
    if data.get('citizens'):
        print(f"First citizen: {data['citizens'][0]}")
