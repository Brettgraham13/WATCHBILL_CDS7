"""
Module for managing watchstanders and their assignments for a specific month.
"""
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from src.watchstander import Watchstander
from src.month_vector_generator import generate_month_vector
from src.constants import VALUE_KEY
import pandas as pd
import matplotlib.pyplot as plt
import re
import calendar

class Month:
    def __init__(self, year: int, month: int):
        """
        Initialize a Month object.
        
        Args:
            year: The year
            month: The month (1-12)
        """
        self.year = year
        self.month = month
        self.watchstanders: Dict[str, Watchstander] = {}
        self.month_vector = generate_month_vector(year, month)
        self.actual_watch_points: Dict[str, float] = {}  # Track actual watch points for each watchstander
        # Calculate the number of days in the month
        self.days_in_month = calendar.monthrange(year, month)[1]
        
    def add_watchstander(self, watchstander: Watchstander) -> None:
        """Add a watchstander to the month."""
        if watchstander.name in self.watchstanders:
            raise ValueError(f"Watchstander {watchstander.name} already exists in the month.")
        # Ensure availability vector is filled and has the correct length
        if not watchstander.availability_vectors.get((self.year, self.month), []):
            raise ValueError(f"Watchstander {watchstander.name} must have a filled availability vector.")
        if len(watchstander.availability_vectors.get((self.year, self.month), [])) != self.days_in_month:
            raise ValueError(f"Watchstander {watchstander.name} must have an availability vector of length {self.days_in_month}.")
        self.watchstanders[watchstander.name] = watchstander
        self.actual_watch_points[watchstander.name] = 0.0  # Initialize actual watch points
            
    def remove_watchstander(self, watchstander: Watchstander) -> None:
        """Remove a watchstander from the month's roster."""
        if watchstander.name in self.watchstanders:
            del self.watchstanders[watchstander.name]
            if watchstander.name in self.actual_watch_points:
                del self.actual_watch_points[watchstander.name]
    
    def add_watch(self, watchstander_name: str, day: int, watch_type: str) -> None:
        """
        Add a watch to a watchstander's actual points.
        
        Args:
            watchstander_name: Name of the watchstander
            day: Day of the month (1-31)
            watch_type: Type of watch ('D' for day, 'N' for night)
        """
        if watchstander_name not in self.watchstanders:
            raise ValueError(f"Watchstander {watchstander_name} not found in month's roster")
            
        if day < 1 or day > len(self.month_vector):
            raise ValueError(f"Invalid day: {day}")
            
        # Get the day type from month vector (0-based index)
        day_type = self.month_vector[day - 1]
        
        # Calculate points based on watch type and day type
        points = 0
        if watch_type == 'D':  # Day watch
            if day_type == 0:  # Workday
                points = VALUE_KEY["Weekday day watch"]
            elif day_type == 1:  # Leading into weekend
                points = VALUE_KEY["Friday day watch"]
            elif day_type in [2, 3]:  # Weekend or final weekend day
                points = VALUE_KEY["Friday night/Saturday/Sunday day"]
        elif watch_type == 'N':  # Night watch
            if day_type == 0:  # Workday
                points = VALUE_KEY["Weekday night watch"]
            elif day_type == 1:  # Leading into weekend
                points = VALUE_KEY["Friday night/Saturday/Sunday day"]
            elif day_type == 2:  # Weekend day
                points = VALUE_KEY["Friday night/Saturday/Sunday day"]
            elif day_type == 3:  # Final weekend day
                points = VALUE_KEY["Sunday night"]
        else:
            raise ValueError(f"Invalid watch type: {watch_type}")
            
        self.actual_watch_points[watchstander_name] += points
    
    def evaluate_watch_deviations(self) -> Dict[str, Dict[str, float]]:
        """
        Evaluate the deviation between expected and actual watch points for each watchstander.
        Returns a dictionary with watchstander names as keys and dictionaries containing:
        - expected_points: Expected watch points
        - actual_points: Actual watch points stood
        - deviation: Difference between expected and actual (positive means stood too little, negative means stood too much)
        - deviation_percentage: Deviation as a percentage of expected points
        """
        expected_points = self.calculate_expected_watch_points()
        deviations = {}
        
        for ws in self.watchstanders:
            name = ws.name
            expected = expected_points[name]
            actual = self.actual_watch_points.get(name, 0.0)
            # Invert the deviation calculation so positive means stood too little
            deviation = expected - actual
            deviation_percentage = (deviation / expected * 100) if expected > 0 else 0.0
            
            deviations[name] = {
                "expected_points": expected,
                "actual_points": actual,
                "deviation": deviation,
                "deviation_percentage": deviation_percentage
            }
            
        return deviations
    
    def get_watchstander(self, name: str) -> Optional[Watchstander]:
        """Get a watchstander by name."""
        return self.watchstanders.get(name)
    
    def get_all_watchstanders(self) -> List[Watchstander]:
        """Get all watchstanders in the month's roster."""
        return list(self.watchstanders.values())
    
    def get_n_heads(self) -> List[Watchstander]:
        """Get all N-heads in the month's roster."""
        return [ws for ws in self.watchstanders.values() if ws.is_n_head]
    
    def get_regular_watchstanders(self) -> List[Watchstander]:
        """Get all regular watchstanders (non-N-heads) in the month's roster."""
        return [ws for ws in self.watchstanders.values() if not ws.is_n_head]
    
    def calculate_total_availability(self) -> Dict[str, int]:
        """
        Calculate total available days for all watchstanders in the month.
        Returns a dictionary mapping watchstander names to their available days.
        """
        total_available = 0
        individual_available = {}
        
        for ws in self.watchstanders.values():
            available_days, _, _ = ws.calculate_monthly_availability(self.year, self.month)
            individual_available[ws.name] = available_days
            total_available += available_days
            
        return individual_available
    
    def calculate_expected_watch_points(self):
        """Calculate expected watch points for each watchstander."""
        # Calculate total monthly points
        total_monthly_points = 0
        for day_type in self.month_vector:
            if day_type == 0:  # Full workday
                total_monthly_points += VALUE_KEY["Weekday day watch"] + VALUE_KEY["Weekday night watch"]
            elif day_type == 1:  # Leading into weekend
                total_monthly_points += VALUE_KEY["Friday day watch"] + VALUE_KEY["Friday night/Saturday/Sunday day"]
            elif day_type == 2:  # Weekend day
                total_monthly_points += VALUE_KEY["Friday night/Saturday/Sunday day"]
            elif day_type == 3:  # Final day of weekend
                total_monthly_points += VALUE_KEY["Friday night/Saturday/Sunday day"] + VALUE_KEY["Sunday night"]
        
        # Calculate N-head points first
        n_head_points = 0
        for ws in self.watchstanders.values():
            if ws.is_n_head:
                # Calculate N-head points based on availability percentage
                availability_vector = ws.availability_vectors.get((self.year, self.month), [])
                if availability_vector:
                    total_days = len(availability_vector)
                    available_days = sum(1 for day in availability_vector if day > 0)
                    availability_percentage = available_days / total_days if total_days > 0 else 0.0
                    n_head_points += availability_percentage * 28.0
        
        # Calculate remaining points for regular watchstanders
        remaining_points = total_monthly_points - n_head_points
        
        # Calculate total watch percentage for regular watchstanders
        total_watch_percentage = 0
        for ws in self.watchstanders.values():
            if not ws.is_n_head:
                availability_vector = ws.availability_vectors.get((self.year, self.month), [])
                if availability_vector:
                    total_days = len(availability_vector)
                    available_days = sum(1 for day in availability_vector if day > 0)
                    availability_percentage = available_days / total_days if total_days > 0 else 0.0
                    total_watch_percentage += availability_percentage * ws.watch_percentage
        
        # Calculate expected points for each watchstander
        expected_points = {}
        for ws in self.watchstanders.values():
            if ws.is_n_head:
                # N-heads get points based on their availability percentage
                availability_vector = ws.availability_vectors.get((self.year, self.month), [])
                if availability_vector:
                    total_days = len(availability_vector)
                    available_days = sum(1 for day in availability_vector if day > 0)
                    availability_percentage = available_days / total_days if total_days > 0 else 0.0
                    expected_points[ws.name] = availability_percentage * 28.0
                else:
                    expected_points[ws.name] = 0.0
            else:
                # Regular watchstanders get points based on their availability and watch percentage
                availability_vector = ws.availability_vectors.get((self.year, self.month), [])
                if availability_vector and total_watch_percentage > 0:
                    total_days = len(availability_vector)
                    available_days = sum(1 for day in availability_vector if day > 0)
                    availability_percentage = available_days / total_days if total_days > 0 else 0.0
                    watch_share = (availability_percentage * ws.watch_percentage) / total_watch_percentage
                    expected_points[ws.name] = watch_share * remaining_points
                else:
                    expected_points[ws.name] = 0.0
            
            # Calculate actual points
            actual_points = 0.0
            availability_vector = ws.availability_vectors.get((self.year, self.month), [])
            for day_idx, val in enumerate(availability_vector):
                day_type = self.month_vector[day_idx]
                if val == 8:  # Day watch
                    if day_type == 0:  # Workday
                        actual_points += VALUE_KEY["Weekday day watch"]
                    elif day_type == 1:  # Leading into weekend
                        actual_points += VALUE_KEY["Friday day watch"]
                    elif day_type in [2, 3]:  # Weekend or final weekend day
                        actual_points += VALUE_KEY["Friday night/Saturday/Sunday day"]
                elif val == 9:  # Night watch
                    if day_type == 0:  # Workday
                        actual_points += VALUE_KEY["Weekday night watch"]
                    elif day_type == 1:  # Leading into weekend
                        actual_points += VALUE_KEY["Friday night/Saturday/Sunday day"]
                    elif day_type == 2:  # Weekend day
                        actual_points += VALUE_KEY["Friday night/Saturday/Sunday day"]
                    elif day_type == 3:  # Final weekend day
                        actual_points += VALUE_KEY["Sunday night"]
            
            # Update points deviation
            ws.update_points_deviation(self.year, self.month, expected_points[ws.name], actual_points)
        
        return expected_points
    
    def get_month_summary(self) -> Dict:
        """
        Get a summary of the month including:
        - Total watchstanders
        - Number of N-heads
        - Total available days
        - Expected watch points for each watchstander
        - Actual watch points and deviations
        """
        deviations = self.evaluate_watch_deviations()
        return {
            "year": self.year,
            "month": self.month,
            "total_watchstanders": len(self.watchstanders),
            "n_heads": len(self.get_n_heads()),
            "regular_watchstanders": len(self.get_regular_watchstanders()),
            "availability": self.calculate_total_availability(),
            "expected_points": self.calculate_expected_watch_points(),
            "actual_points": self.actual_watch_points,
            "deviations": deviations
        }
    
    def __str__(self) -> str:
        """String representation of the month."""
        return f"Month: {self.year}-{self.month:02d} with {len(self.watchstanders)} watchstanders"

    def print_watchstander_points(self):
        """
        Print the expected and actual watch points for each watchstander.
        """
        summary = self.get_month_summary()
        print('\nWatchstander Breakdown:')
        for name in summary['expected_points']:
            print(f'{name:20}  Expected: {summary["expected_points"][name]:6.1f}  Actual: {summary["actual_points"][name]:6.1f}  Deviation: {summary["actual_points"][name] - summary["expected_points"][name]:+6.1f}')

    @staticmethod
    def normalize_name(name):
        """Collapse multiple spaces, strip, and lowercase a name for robust matching."""
        return re.sub(r'\s+', ' ', str(name)).strip().lower()

    @staticmethod
    def build_month_from_excel(filepath: str, year: int, month: int) -> 'Month':
        """
        Build a Month object for the specified year and month from the given Excel file.
        Assumes first row is header, first column is name, rest are availability vector (BODY_KEY values).
        Uses default values for check-in/qualification dates.
        Skips rows where the name is missing or NaN.
        Adds actual watches for days marked 8 (day watch) and 9 (night watch).
        Sets is_n_head=True for CDR IVEY, LCDR KIM, LCDR HUNTLEY, LCDR DESORMIER, LCDR DESPOTA (case-insensitive).
        """
        n_heads = {Month.normalize_name(n) for n in [
            'CDR IVEY', 'LCDR KIM', 'LCDR HUNTLEY', 'LCDR DESORMIER', 'LCDR DESPOTA']}
        df = pd.read_excel(filepath)
        month_obj = Month(year, month)
        for _, row in df.iterrows():
            name = row.iloc[0]
            if pd.isna(name) or not str(name).strip():
                continue  # Skip rows with missing or empty name
            # N-head logic with normalized name
            is_n_head = Month.normalize_name(name) in n_heads
            # Replace NaN with 0 in the availability vector
            availability_vector = [int(x) if pd.notna(x) else 0 for x in row.iloc[1:].tolist()]
            # Ensure the availability vector is filled and has the correct length
            if not availability_vector or len(availability_vector) != month_obj.days_in_month:
                raise ValueError(f"Watchstander {name} must have a filled availability vector of length {month_obj.days_in_month}.")
            ws = Watchstander(name, is_n_head)
            ws.set_monthly_availability(year, month, availability_vector)
            month_obj.add_watchstander(ws)
            # Add actual watches for days marked 8 or 9
            for day_idx, val in enumerate(availability_vector):
                if val == 8:
                    month_obj.add_watch(name, day_idx + 1, 'D')  # Day is 1-indexed
                elif val == 9:
                    month_obj.add_watch(name, day_idx + 1, 'N')
        return month_obj

    def print_month_summary(self):
        """
        Print a summary of the month using Month.get_month_summary().
        """
        summary = self.get_month_summary()
        print(f"\nMonth Summary for {summary['year']}-{summary['month']:02d}:")
        print(f"Total Watchstanders: {summary['total_watchstanders']}")
        print(f"N-Heads: {summary['n_heads']}")
        print(f"Regular Watchstanders: {summary['regular_watchstanders']}")
        print("\nAvailability:")
        for name, avail in summary['availability'].items():
            print(f"  {name}: {avail} days available")
        print("\nExpected Watch Points:")
        for name, points in summary['expected_points'].items():
            print(f"  {name}: {points:.1f}")
        print("\nActual Watch Points:")
        for name, points in summary['actual_points'].items():
            print(f"  {name}: {points:.1f}")
        print("\nWatch Point Deviations:")
        for name, data in summary['deviations'].items():
            print(f"\n{name}:")
            print(f"  Expected Points: {data['expected_points']:.1f}")
            print(f"  Actual Points: {data['actual_points']:.1f}")
            print(f"  Deviation: {data['deviation']:+.1f} points ({data['deviation_percentage']:+.1f}%)")
            if data['deviation'] > 0:
                print(f"  Status: Needs {data['deviation']:.1f} more points to reach expected watch")
            elif data['deviation'] < 0:
                print(f"  Status: Has stood {abs(data['deviation']):.1f} more points than expected")
            else:
                print("  Status: Perfectly balanced")

    def visualize_month_summary(self):
        summary = self.get_month_summary()
        names = list(summary['expected_points'].keys())
        expected = [summary['expected_points'][n] for n in names]
        actual = [summary['actual_points'][n] for n in names]
        deviations = [summary['deviations'][n]['deviation'] for n in names]
        n_heads = set(ws.name for ws in self.get_n_heads())
        is_n_head = [n in n_heads for n in names]

        # 1. Bar chart: Expected vs. Actual Watch Points
        plt.figure(figsize=(14, 6))
        x = range(len(names))
        plt.bar(x, expected, width=0.4, label='Expected', align='center')
        plt.bar(x, actual, width=0.4, label='Actual', align='edge')
        plt.xticks(x, names, rotation=90)
        plt.ylabel('Watch Points')
        plt.title('Expected vs. Actual Watch Points per Watchstander')
        plt.legend()
        plt.tight_layout()
        plt.show()

        # 2. Bar chart: Deviation per Watchstander
        plt.figure(figsize=(14, 6))
        plt.bar(x, deviations, color=['green' if d < 0 else 'red' for d in deviations])
        plt.xticks(x, names, rotation=90)
        plt.ylabel('Deviation (Expected - Actual)')
        plt.title('Deviation in Watch Points per Watchstander')
        plt.axhline(0, color='black', linewidth=0.8)
        plt.tight_layout()
        plt.show()

        # 3. Pie chart: N-heads vs. Regular
        n_n_heads = sum(is_n_head)
        n_regular = len(names) - n_n_heads
        plt.figure(figsize=(6, 6))
        plt.pie([n_n_heads, n_regular], labels=['N-heads', 'Regular'], autopct='%1.1f%%', startangle=90)
        plt.title('Proportion of N-heads vs. Regular Watchstanders')
        plt.axis('equal')
        plt.show()

        # 4. Histogram: Distribution of deviations
        plt.figure(figsize=(8, 6))
        plt.hist(deviations, bins=10, color='skyblue', edgecolor='black')
        plt.xlabel('Deviation (Expected - Actual)')
        plt.ylabel('Number of Watchstanders')
        plt.title('Distribution of Watch Point Deviations')
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    # Example usage
    month = Month(2023, 1)
    
    # Create some watchstanders
    watchstander1 = Watchstander("John Doe", datetime(2023, 1, 1), datetime(2023, 2, 1), True)  # N-head
    watchstander2 = Watchstander("Jane Smith", datetime(2023, 1, 1), datetime(2023, 2, 1), False)  # Regular watchstander
    
    # Set their availability
    jan_availability1 = [0] * 31  # 31 days of January
    jan_availability1[14:20] = [1, 2, 2, 2, 2, 3]  # Leave from 15th to 20th
    watchstander1.set_monthly_availability(2023, 1, jan_availability1)
    
    jan_availability2 = [0] * 31  # 31 days of January
    jan_availability2[10:15] = [1, 2, 2, 2, 3]  # Leave from 11th to 15th
    watchstander2.set_monthly_availability(2023, 1, jan_availability2)
    
    # Add watchstanders to the month
    month.add_watchstander(watchstander1)
    month.add_watchstander(watchstander2)
    
    # Add some watches
    month.add_watch("John Doe", 1, 'D')  # Day watch on workday
    month.add_watch("John Doe", 2, 'N')  # Night watch on workday
    month.add_watch("Jane Smith", 3, 'D')  # Day watch on workday
    month.add_watch("Jane Smith", 4, 'N')  # Night watch on workday
    
    # Get month summary
    summary = month.get_month_summary()
    print(f"\nMonth Summary for {summary['year']}-{summary['month']:02d}:")
    print(f"Total Watchstanders: {summary['total_watchstanders']}")
    print(f"N-Heads: {summary['n_heads']}")
    print(f"Regular Watchstanders: {summary['regular_watchstanders']}")
    
    print("\nWatch Point Analysis:")
    for name, data in summary['deviations'].items():
        print(f"\n{name}:")
        print(f"  Expected Points: {data['expected_points']:.1f}")
        print(f"  Actual Points: {data['actual_points']:.1f}")
        print(f"  Deviation: {data['deviation']:+.1f} points ({data['deviation_percentage']:+.1f}%)")
        if data['deviation'] > 0:
            print(f"  Status: Needs {data['deviation']:.1f} more points to reach expected watch")
        elif data['deviation'] < 0:
            print(f"  Status: Has stood {abs(data['deviation']):.1f} more points than expected")
        else:
            print("  Status: Perfectly balanced")

    # Print watchstander points
    month.print_watchstander_points() 