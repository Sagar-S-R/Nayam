#!/usr/bin/env python3
"""Test phone validation with various formats"""

from app.core.phone_utils import validate_indian_phone

test_cases = [
    ("+919876543210", True, "International with +"),
    ("919876543210", True, "International without +"),
    ("09876543210", True, "National format with 0"),
    ("9876543210", True, "10 digits only"),
    ("+91 9876543210", True, "With spaces"),
    ("+91-9876543210", True, "With dashes"),
    ("1234567890", True, "Any 10 digits (removed 2nd digit check)"),
    ("0000000000", True, "All zeros (10 digits)"),
    ("123456789", False, "9 digits"),
    ("12345678901", False, "11 digits"),
    ("ABC123456789", False, "Non-numeric"),
]

print("Phone Validation Tests")
print("=" * 70)

for phone, expected, description in test_cases:
    is_valid, normalized = validate_indian_phone(phone)
    status = "✅" if is_valid == expected else "❌"
    print(f"{status} {description:40} | Input: {phone:15} | Valid: {is_valid} | Normalized: {normalized}")

print("=" * 70)
