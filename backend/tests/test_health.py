#!/usr/bin/env python3
import requests
import json

# Test health endpoint (no auth required)
health_resp = requests.get('http://localhost:8000/api/v1/health/deep')
print(f'Health Response Status: {health_resp.status_code}')
print(f'Health Response: {json.dumps(health_resp.json(), indent=2)}')
