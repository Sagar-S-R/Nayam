"""
NAYAM (नयम्) — MCD Ward Constants.

Delhi MCD has 12 zones with multiple wards. For Phase 4, we support
the primary ward list: Ward-1 through Ward-8.
"""

# MCD Delhi Ward List (Phase 4 - 8 primary wards)
MCD_WARDS = [
    "Ward-1",
    "Ward-2",
    "Ward-3",
    "Ward-4",
    "Ward-5",
    "Ward-6",
    "Ward-7",
    "Ward-8",
]

# Ward -> Zone mapping (for future expansion)
WARD_TO_ZONE = {
    "Ward-1": "North-1",
    "Ward-2": "North-2",
    "Ward-3": "South-1",
    "Ward-4": "South-2",
    "Ward-5": "Central-1",
    "Ward-6": "Central-2",
    "Ward-7": "East-1",
    "Ward-8": "East-2",
}

def get_valid_wards() -> list[str]:
    """Get list of valid MCD wards."""
    return MCD_WARDS

def is_valid_ward(ward: str) -> bool:
    """Check if a ward is valid."""
    return ward in MCD_WARDS

def get_ward_zone(ward: str) -> str:
    """Get zone for a ward."""
    return WARD_TO_ZONE.get(ward, "Unknown")
