"""
Constants for Nexus HR application
"""

# Kenyan Public Holidays 2025
KENYAN_HOLIDAYS_2025 = [
    "2025-01-01",  # New Year
    "2025-04-18",  # Good Friday
    "2025-04-21",  # Easter Monday
    "2025-05-01",  # Labour Day
    "2025-06-01",  # Madaraka Day
    "2025-10-10",  # Huduma Day
    "2025-10-20",  # Mashujaa Day
    "2025-12-12",  # Jamhuri Day
    "2025-12-25",  # Christmas
    "2025-12-26",  # Boxing Day
]

# Kenyan Public Holidays 2026
KENYAN_HOLIDAYS_2026 = [
    "2026-01-01",  # New Year
    "2026-04-03",  # Good Friday
    "2026-04-06",  # Easter Monday
    "2026-05-01",  # Labour Day
    "2026-06-01",  # Madaraka Day
    "2026-10-10",  # Huduma Day
    "2026-10-20",  # Mashujaa Day
    "2026-12-12",  # Jamhuri Day
    "2026-12-25",  # Christmas
    "2026-12-26",  # Boxing Day
]

# Combined holidays
KENYAN_HOLIDAYS = KENYAN_HOLIDAYS_2025 + KENYAN_HOLIDAYS_2026

# Office Location for Geofencing (Nairobi CBD - example coordinates)
OFFICE_LOCATION = {
    "latitude": -1.286389,
    "longitude": 36.817223,
    "radius_meters": 200  # 200m radius
}
