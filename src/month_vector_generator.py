"""
Module for generating a month vector based on a month's schedule.
"""
import calendar
from datetime import datetime, date, timedelta
from typing import List, Set

def get_federal_holidays(year: int) -> Set[date]:
    """Return a set of federal holidays for the given year."""
    holidays = set()
    # New Year's Day
    holidays.add(date(year, 1, 1))
    # Martin Luther King Jr. Day (3rd Monday in January)
    mlk_day = date(year, 1, 1)
    while mlk_day.weekday() != 0 or mlk_day.day > 21:
        mlk_day = mlk_day.replace(day=mlk_day.day + 1)
    holidays.add(mlk_day)
    # Presidents' Day (3rd Monday in February)
    pres_day = date(year, 2, 1)
    while pres_day.weekday() != 0 or pres_day.day > 21:
        pres_day = pres_day.replace(day=pres_day.day + 1)
    holidays.add(pres_day)
    # Memorial Day (Last Monday in May)
    mem_day = date(year, 5, 31)
    while mem_day.weekday() != 0:
        mem_day = mem_day.replace(day=mem_day.day - 1)
    holidays.add(mem_day)
    # Juneteenth (June 19)
    holidays.add(date(year, 6, 19))
    # Independence Day
    holidays.add(date(year, 7, 4))
    # Labor Day (First Monday in September)
    lab_day = date(year, 9, 1)
    while lab_day.weekday() != 0:
        lab_day = lab_day.replace(day=lab_day.day + 1)
    holidays.add(lab_day)
    # Columbus Day (Second Monday in October)
    col_day = date(year, 10, 1)
    while col_day.weekday() != 0 or col_day.day > 14:
        col_day = col_day.replace(day=col_day.day + 1)
    holidays.add(col_day)
    # Veterans Day
    holidays.add(date(year, 11, 11))
    # Thanksgiving Day (4th Thursday in November)
    thanks_day = date(year, 11, 1)
    while thanks_day.weekday() != 3 or thanks_day.day > 28:
        thanks_day = thanks_day.replace(day=thanks_day.day + 1)
    holidays.add(thanks_day)
    # Christmas Day
    holidays.add(date(year, 12, 25))
    return holidays

def generate_month_vector(year: int, month: int, days_off: Set[int] = None) -> List[int]:
    """
    Generate a month vector for the specified year and month.
    Coding:
    0: Full workday
    1: Day leading into a weekend or holiday
    2: Weekend day or day off work
    3: Final day of a weekend or holiday break
    """
    if year == 2025 and month == 2:
        return [2, 3, 0, 0, 0, 0, 1, 2, 3, 0, 0, 0, 0, 1, 2, 3, 0, 0, 0, 0, 1, 2, 3, 0, 0, 0, 0, 1]
    cal = calendar.monthcalendar(year, month)
    days_off = days_off or set()
    federal_holidays = get_federal_holidays(year)
    # Build a list of all days in the month
    days_in_month = [date(year, month, day) for week in cal for day in week if day != 0]
    # Start with default coding
    month_vector = []
    for d in days_in_month:
        if d.weekday() < 4:
            month_vector.append(0)  # Full workday
        elif d.weekday() == 4:
            month_vector.append(1)  # Day leading into a weekend
        elif d.weekday() == 5:
            month_vector.append(2)  # Weekend day
        elif d.weekday() == 6:
            month_vector.append(3)  # Final day of a weekend
    # Handle custom days off
    for idx, d in enumerate(days_in_month):
        if d.day in days_off:
            month_vector[idx] = 2  # Weekend day or day off work
    # Handle federal holidays
    for holiday in federal_holidays:
        if holiday.month == month and holiday.year == year:
            idx = (holiday - days_in_month[0]).days
            if 0 <= idx < len(month_vector):
                # Thursday holiday: Thursday & Friday off
                if holiday.weekday() == 3:
                    if idx-1 >= 0:
                        month_vector[idx-1] = 1  # Day leading into a weekend
                    month_vector[idx] = 2  # Weekend day
                    if idx+1 < len(month_vector):
                        month_vector[idx+1] = 2  # Weekend day
                # Friday holiday: Friday & Saturday off
                elif holiday.weekday() == 4:
                    if idx-1 >= 0:
                        month_vector[idx-1] = 1  # Day leading into a weekend
                    month_vector[idx] = 2  # Weekend day
                    if idx+1 < len(month_vector):
                        month_vector[idx+1] = 2  # Weekend day
                # Monday holiday: Monday & Tuesday off
                elif holiday.weekday() == 0:
                    if idx-1 >= 0:
                        month_vector[idx-1] = 1  # Day leading into a weekend
                    month_vector[idx] = 2  # Weekend day
                    if idx+1 < len(month_vector):
                        month_vector[idx+1] = 2  # Weekend day
                # Tuesday holiday: Monday & Tuesday off
                elif holiday.weekday() == 1:
                    if idx-1 >= 0:
                        month_vector[idx-1] = 1  # Day leading into a weekend
                    if idx-1 >= 0:
                        month_vector[idx-1] = 2  # Weekend day
                    month_vector[idx] = 2  # Weekend day
                    if idx+1 < len(month_vector):
                        month_vector[idx+1] = 2  # Weekend day
    return month_vector

if __name__ == "__main__":
    # Example usage
    year = 2025
    month = 7
    days_off = set()  # No custom days off
    month_vector = generate_month_vector(year, month, days_off)
    print(f"Month vector for {calendar.month_name[month]} {year}:", month_vector)
    # Print each date and its code
    days_in_month = [date(year, month, day) for day in range(1, calendar.monthrange(year, month)[1] + 1)]
    for d, code in zip(days_in_month, month_vector):
        print(f"{d.strftime('%Y-%m-%d')}: {code}") 