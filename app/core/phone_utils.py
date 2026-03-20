"""
NAYAM (नयम्) — Contact Number Validation & PII Masking (Phase 4).

Validates Indian phone formats and provides PII masking for display.
"""

import re
from typing import Tuple


def validate_indian_phone(phone: str) -> Tuple[bool, str]:
    """
    Validate Indian phone number format.
    
    Accepts:
    - +91XXXXXXXXXX (international format)
    - 91XXXXXXXXXX (country code without +)
    - 0XXXXXXXXXX (national format)
    - XXXXXXXXXX (10 digits only)
    
    Args:
        phone: Phone number string.
        
    Returns:
        Tuple of (is_valid, normalized_phone).
        Normalized format: 10-digit string without formatting.
    """
    # Remove all whitespace and dashes
    cleaned = re.sub(r"[\s\-\.]", "", phone.strip())
    
    # Remove leading +91
    if cleaned.startswith("+91"):
        cleaned = cleaned[3:]
    # Remove leading 91
    elif cleaned.startswith("91") and len(cleaned) > 10:
        cleaned = cleaned[2:]
    # Remove leading 0
    elif cleaned.startswith("0"):
        cleaned = cleaned[1:]
    
    # Now cleaned should be 10 digits
    if not re.match(r"^\d{10}$", cleaned):
        return False, ""
    
    # Valid if 10 digits - no need to check 2nd digit as some numbers might not follow mobile pattern
    return True, cleaned


def normalize_phone(phone: str) -> str:
    """
    Normalize phone to standard format (10 digits).
    
    Args:
        phone: Raw phone input.
        
    Returns:
        Normalized 10-digit phone number, or empty string if invalid.
    """
    is_valid, normalized = validate_indian_phone(phone)
    return normalized if is_valid else ""


def mask_phone_number(phone: str, format_type: str = "partial") -> str:
    """
    Mask phone number for display (PII protection).
    
    Formats:
    - "partial": XXXXXX9876 (last 4 visible)
    - "full": XXXXXXXXXX (fully masked)
    - "minimal": XX...XX (first 2 and last 2 visible)
    
    Args:
        phone: 10-digit phone number.
        format_type: Masking strategy.
        
    Returns:
        Masked phone number string.
    """
    if not phone or len(phone) != 10:
        return "***INVALID***"
    
    if format_type == "partial":
        # Show last 4 digits
        return f"{'X' * 6}{phone[-4:]}"
    elif format_type == "full":
        # Fully masked
        return "X" * 10
    elif format_type == "minimal":
        # Show first 2 and last 2
        return f"{phone[:2]}...{phone[-2:]}"
    else:
        # Default to partial
        return f"{'X' * 6}{phone[-4:]}"


def format_phone_display(phone: str, masked: bool = True) -> str:
    """
    Format phone number for display with optional masking.
    
    Args:
        phone: 10-digit phone number.
        masked: Whether to apply PII masking.
        
    Returns:
        Formatted phone string.
    """
    if masked:
        # Return masked format with visual grouping
        masked_num = mask_phone_number(phone, "partial")
        return f"+91-{masked_num[:6]}-{masked_num[6:]}"
    else:
        # Return formatted unmasked (for admin view, if needed)
        return f"+91-{phone[:5]}-{phone[5:]}"
