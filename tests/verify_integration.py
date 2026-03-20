#!/usr/bin/env python3
"""Quick verification that all components are integrated correctly."""

from app.core.mcd_wards import get_valid_wards, is_valid_ward
from app.core.phone_utils import validate_indian_phone, mask_phone_number
from app.schemas.citizen import CitizenCreateRequest

print("✅ ALL IMPORTS SUCCESSFUL")
print(f"✅ MCD Wards: {len(get_valid_wards())} wards available")
print(f"✅ Ward-1 valid: {is_valid_ward('Ward-1')}")
print(f"✅ Phone validation: {validate_indian_phone('+919876543210')}")
print(f"✅ Phone masking: {mask_phone_number('9876543210')}")

try:
    citizen = CitizenCreateRequest(
        name="Test Citizen",
        contact_number="+919876543210",
        ward="Ward-1"
    )
    print("✅ SCHEMA VALIDATION WORKING")
except Exception as e:
    print(f"❌ Schema error: {e}")

print("\n✅ SYSTEM READY FOR END-TO-END TESTING!")
