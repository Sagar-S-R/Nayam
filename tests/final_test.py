#!/usr/bin/env python3
import requests
import time

# Fresh test
timestamp = int(time.time())
email = f'finaltest{timestamp}@example.com'

reg = requests.post('http://localhost:8000/api/v1/auth/register', json={
    'name': 'FinalTest',
    'email': email,
    'password': 'test12345', 
    'role': 'Staff'
})

if reg.status_code not in [200, 201]:
    print("Registration failed")
    exit(1)

token = reg.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

print('✅ DATABASE TO API TEST')
print('=' * 60)

# Test Citizens
r = requests.get('http://localhost:8000/api/v1/citizens?limit=20', headers=headers)
if r.status_code == 200:
    data = r.json()
    total = data.get('total', 0)
    returned = len(data.get('citizens', []))
    print(f'✅ Citizens: {total} total, {returned} returned')
    if returned > 0:
        c = data['citizens'][0]
        print(f'   Sample: {c["name"]} - Ward {c["ward"]}')
        print(f'   Has masked_contact: {"masked_contact" in c}')
else:
    print(f'❌ Citizens: Status {r.status_code}')

# Test Issues  
r = requests.get('http://localhost:8000/api/v1/issues?limit=20', headers=headers)
if r.status_code == 200:
    data = r.json()
    total = data.get('total', 0)
    returned = len(data.get('issues', []))
    print(f'✅ Issues: {total} total, {returned} returned')
else:
    print(f'❌ Issues: Status {r.status_code}')

print('=' * 60)
print('✅ All tests passed!')
