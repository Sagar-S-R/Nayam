"""
NAYAM (नयम्) — MCD Ward Constants.

Delhi MCD has 12 zones with multiple wards. For Phase 4, we support
the primary ward list: Ward-1 through Ward-8.
"""

# MCD Delhi Ward List (Phase 4 - Real Delhi localities)
MCD_WARDS = [
    "Dwarka",
    "Rohini",
    "Karol Bagh",
    "Lajpat Nagar",
    "Saket",
    "Janakpuri",
    "Pitampura",
    "Mayur Vihar",
]

# Ward -> Zone mapping (for future expansion)
WARD_TO_ZONE = {
    "Dwarka": "South-West",
    "Rohini": "North-West",
    "Karol Bagh": "Central-North",
    "Lajpat Nagar": "Central-South",
    "Saket": "South",
    "Janakpuri": "West",
    "Pitampura": "North",
    "Mayur Vihar": "East",
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
