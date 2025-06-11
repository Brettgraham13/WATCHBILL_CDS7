    """
Module for managing watchstanders and their assignments for a specific month.
"""
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from src.watchstander import Watchstander
from src.month_vector_generator import generate_month_vector
from src.constants import VALUE_KEY

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
        self.watchstanders: List[Watchstander] = []
        self.month_vector = generate_month_vector(year, month)
        self.actual_watch_points: Dict[str, float] = {}  # Track actual watch points for each watchstander
        
    def add_watchstander(self, watchstander: Watchstander) -> None:
        """Add a watchstander to the month's roster."""
        if watchstander not in self.watchstanders:
            self.watchstanders.append(watchstander)
            self.actual_watch_points[watchstander.name] = 0.0
            
    def remove_watchstander(self, watchstander: Watchstander) -> None:
        """Remove a watchstander from the month's roster."""
        if watchstander in self.watchstanders:
            self.watchstanders.remove(watchstander)
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
        if watchstander_name not in self.actual_watch_points:
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
        for ws in self.watchstanders:
            if ws.name == name:
                return ws
        return None
    
    def get_all_watchstanders(self) -> List[Watchstander]:
        """Get all watchstanders in the month's roster."""
        return self.watchstanders
    
    def get_n_heads(self) -> List[Watchstander]:
        """Get all N-heads in the month's roster."""
        return [ws for ws in self.watchstanders if ws.is_n_head]
    
    def get_regular_watchstanders(self) -> List[Watchstander]:
        """Get all regular watchstanders (non-N-heads) in the month's roster."""
        return [ws for ws in self.watchstanders if not ws.is_n_head]
    
    def calculate_total_availability(self) -> Dict[str, int]:
        """
        Calculate total available days for all watchstanders in the month.
        Returns a dictionary mapping watchstander names to their available days.
        """
        total_available = 0
        individual_available = {}
        
        for ws in self.watchstanders:
            available_days, _, _ = ws.calculate_monthly_availability(self.year, self.month)
            individual_available[ws.name] = available_days
            total_available += available_days
            
        return individual_available
    
    def calculate_expected_watch_points(self) -> Dict[str, float]:
        """
        Calculate expected watch points for all watchstanders in the month.
        Returns a dictionary mapping watchstander names to their expected watch points.
        """
        expected_points = {}
        for ws in self.watchstanders:
            points = ws.calculate_expected_watch_points(self.year, self.month, self.month_vector)
            expected_points[ws.name] = points
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