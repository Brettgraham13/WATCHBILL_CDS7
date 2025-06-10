"""
Module to hold all constants used in the project.
"""

from datetime import date

# Federal Holidays
FEDERAL_HOLIDAYS = {
    "New Year's Day": (1, 1),
    "Martin Luther King Jr. Day": (1, 3, 0),  # 3rd Monday in January
    "Presidents' Day": (2, 3, 0),  # 3rd Monday in February
    "Memorial Day": (5, -1, 0),  # Last Monday in May
    "Juneteenth": (6, 19),
    "Independence Day": (7, 4),
    "Labor Day": (9, 1, 0),  # First Monday in September
    "Columbus Day": (10, 2, 0),  # Second Monday in October
    "Veterans Day": (11, 11),
    "Thanksgiving Day": (11, 4, 3),  # 4th Thursday in November
    "Christmas Day": (12, 25)
}

# Holiday Codes
HOLIDAY_CODES = {
    "Thursday": {"before": 1, "holiday": 2, "after": 2},
    "Friday": {"before": 1, "holiday": 2, "after": 2},
    "Monday": {"before": 1, "holiday": 2, "after": 2},
    "Tuesday": {"before": 1, "holiday": 2, "after": 2}
}

# Month Key
MONTH_KEY = {
    0: "Normal work days",
    1: "Days leading into a weekend",
    2: "Weekend/Holiday",
    3: "Final day of a weekend"
}

# Body Key
BODY_KEY = {
    0: "Available for duty, no restrictions",
    1: "First day of leave or travel day heading to a TDY",
    2: "On leave or TDY",
    3: "Final day of leave or travel day from a TDY trip",
    4: "First day of special liberty",
    5: "Special liberty. Unable to stand duty but no charge to leave",
    6: "Last day of special lib (next day can only stand night watch)",
    7: "Local event. Cannot stand watch and day before is restricted",
    8: "STWO Day Watch",
    9: "STWO Night Watch"
}

# Value Key
VALUE_KEY = {
    "Working hour": 0.75,
    "Off duty hour": 1,
    "Weekend/Holiday Hour": 3,
    "Weekday QH": 22,
    "Friday QH": 54,
    "Saturday QH": 72,
    "Sunday QH": 56,
    "Weekday day watch": 10,
    "Weekday night watch": 12,
    "Friday day watch": 18,
    "Friday night/Saturday/Sunday day": 36,
    "Sunday night": 20,
    "Expected N-Head watch monthly (one weekday and one weekend)": 28,
    "Expected SWO watch": 18
}

# Rules
RULES = {
    1: "N3, N4, N5, N7 can only stand weekday day watches",
    2: "No watch can be scheduled the day before leave/TDY/special liberty",
    3: "Two days before leave/TDY/special liberty, only night watch can be scheduled",
    4: "No watch can be scheduled the day after leave/TDY/special liberty",
    5: "Only night watch can be scheduled the day after leave/TDY/special liberty",
    6: "Personnel are expected to stand an equivalent number of watches per month",
    7: "Working day defined as 0800-1600. Off duty hour defined as all other times",
    8: "Weekend/holiday hour defined from 1600 Friday to 0800 Monday",
    9: "All personnel stand at least one watch per month"
}

# Other constants can be added here as needed 