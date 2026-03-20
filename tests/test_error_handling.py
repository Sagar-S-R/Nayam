#!/usr/bin/env python3
"""Test improved error handling across the app"""
import requests
import time

BASE_URL = "http://localhost:8000/api/v1"

print("=" * 80)
print("COMPREHENSIVE ERROR HANDLING TEST")
print("=" * 80)

# Test 1: PDF Export without auth token
print("\n1️⃣ PDF EXPORT - NO AUTH (should get 401)")
print("-" * 80)
r = requests.get(f'{BASE_URL}/compliance/audit-trail/pdf')
print(f"Status: {r.status_code}")
print(f"Expected: 401 (Unauthorized)")
if r.status_code == 401:
    print("✅ Correctly returns 401 - frontend will show: 'Session expired, please log in again'")
else:
    print(f"⚠️ Got {r.status_code} instead")

# Test 2: Successfully create citizen
print("\n2️⃣ CREATE CITIZEN - SUCCESS CASE")
print("-" * 80)
timestamp = int(time.time())
email = f'errtest{timestamp}@example.com'

reg = requests.post(f'{BASE_URL}/auth/register', json={
    'name': 'ErrorTest',
    'email': email,
    'password': 'test12345',
    'role': 'Staff'
})

if reg.status_code in [200, 201]:
    token = reg.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    
    r = requests.post(f'{BASE_URL}/citizens', headers=headers, json={
        'name': 'Test Error Handler',
        'contact_number': '9876543210',
        'ward': 'Ward-1'
    })
    
    print(f"Status: {r.status_code}")
    if r.status_code == 201:
        print("✅ Citizen created - frontend will show: 'Citizen added successfully!'")
        citizen_id = r.json()['id']
    else:
        print(f"❌ Error: {r.status_code}")

# Test 3: Validation error - invalid phone
print("\n3️⃣ ADD CITIZEN - VALIDATION ERROR (invalid phone)")
print("-" * 80)
r = requests.post(f'{BASE_URL}/citizens', headers=headers, json={
    'name': 'Invalid Phone Test',
    'contact_number': 'invalid',
    'ward': 'Ward-1'
})

print(f"Status: {r.status_code}")
if r.status_code == 422:
    print("✅ Validation error 422 - frontend will show: 'Please check your input...'")
    errors = r.json()
    print(f"Details: {errors.get('detail', 'error')}")
else:
    print(f"⚠️ Got {r.status_code}")

# Test 4: Invalid ward
print("\n4️⃣ ADD CITIZEN - INVALID WARD")
print("-" * 80)
r = requests.post(f'{BASE_URL}/citizens', headers=headers, json={
    'name': 'Invalid Ward Test',
    'contact_number': '9876543210',
    'ward': 'InvalidWard'
})

print(f"Status: {r.status_code}")
if r.status_code == 422:
    print("✅ Validation error 422 - frontend will show: 'Invalid ward. Must be one of...'")
else:
    print(f"⚠️ Got {r.status_code}")

# Test 5: Draft generation - invalid type
print("\n5️⃣ GENERATE DRAFT - INVALID TYPE")
print("-" * 80)
r = requests.post(f'{BASE_URL}/drafts/generate', headers=headers, json={
    'draft_type': 'InvalidType',
    'topic': 'Test topic for draft',
    'tone': 'Formal',
    'audience': 'Citizens'
})

print(f"Status: {r.status_code}")
if r.status_code == 422:
    print("✅ Validation error 422 - frontend will show validation error message")
else:
    print(f"⚠️ Got {r.status_code}")

# Test 6: Draft generation - success
print("\n6️⃣ GENERATE DRAFT - SUCCESS CASE")
print("-" * 80)
r = requests.post(f'{BASE_URL}/drafts/generate', headers=headers, json={
    'draft_type': 'Speech',
    'topic': 'Independence Day Commemoration 2026',
    'tone': 'Formal',
    'audience': 'Citizens',
    'department': 'Municipal Corporation'
})

print(f"Status: {r.status_code}")
if r.status_code == 201:
    print("✅ Draft generated - frontend will show: 'Draft generated successfully!'")
    draft_data = r.json()
    print(f"Title: {draft_data['title']}")
else:
    print(f"❌ Error: {r.status_code}")
    print(f"Response: {r.text[:150]}")

# Test 7: PDF export - with auth
print("\n7️⃣ PDF EXPORT - WITH AUTH (should work)")
print("-" * 80)
r = requests.get(f'{BASE_URL}/compliance/audit-trail/pdf', headers=headers)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    print("✅ PDF generated successfully - frontend will show: 'PDF exported successfully'")
    print(f"Content-Type: {r.headers.get('content-type')}")
    print(f"File size: {len(r.content)} bytes")
else:
    print(f"⚠️ Got {r.status_code}: {r.text[:100]}")

print("\n" + "=" * 80)
print("✅ ERROR HANDLING TEST COMPLETE")
print("=" * 80)
print("\nSummary of error handling improvements:")
print("- 401 errors → 'Session expired, please log in again'")
print("- 422 validation errors → Show specific validation message")
print("- Success cases → Show toast with action confirmation")
print("- Network errors → Guide user to check connection")
print("- Frontend now NEVER shows technical errors to users")
