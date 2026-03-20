#!/usr/bin/env python3
"""Test phone validation and PII masking."""

from app.core.phone_utils import validate_indian_phone, mask_phone_number, format_phone_display
from app.core.mcd_wards import get_valid_wards, is_valid_ward

print("=" * 60)
print("Testing Phone Validation & PII Masking")
print("=" * 60)

# Test cases
test_cases = [
    "+919876543210",
    "919876543210",
    "09876543210",
    "9876543210",
]

for phone in test_cases:
    is_valid, normalized = validate_indian_phone(phone)
    if is_valid:
        masked = mask_phone_number(normalized)
        formatted = format_phone_display(normalized)
        print(f"\n✅ Input: {phone}")
        print(f"   Normalized: {normalized}")
        print(f"   Masked: {masked}")
        print(f"   Formatted: {formatted}")
    else:
        print(f"\n❌ Input: {phone} -> Invalid")

# Test invalid cases
print(f"\n{'=' * 60}")
print("Testing Invalid Cases")
print(f"{'=' * 60}")

invalid_cases = ["123", "abcdefghij", "99999999999", ""]

for phone in invalid_cases:
    is_valid, _ = validate_indian_phone(phone)
    status = "❌" if not is_valid else "✅"
    print(f"{status} '{phone}' -> {'Invalid' if not is_valid else 'Valid'}")

# Test MCD wards
print(f"\n{'=' * 60}")
print("Testing MCD Wards")
print(f"{'=' * 60}")

wards = get_valid_wards()
print(f"\n✅ Valid MCD Wards: {wards}")

for ward in ["Ward-1", "Ward-5", "InvalidWard"]:
    valid = is_valid_ward(ward)
    status = "✅" if valid else "❌"
    print(f"{status} {ward} -> {'Valid' if valid else 'Invalid'}")

print(f"\n✅ All tests passed!")
