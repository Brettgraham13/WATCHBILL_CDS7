"""
Module for defining the Watchstander class.
"""
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from src.database import WatchstanderDB, get_db_session, calculate_total_availability
from src.constants import VALUE_KEY, MONTH_KEY

class Watchstander:
    """Class representing a watchstander."""
    
    def __init__(self, name, is_n_head=False):
        """Initialize a watchstander.
        
        Args:
            name (str): Name of the watchstander
            is_n_head (bool, optional): Whether the watchstander is an N-head
        """
        self.name = name
        self.is_n_head = is_n_head
        self.availability_vectors = {}  # year-month -> vector
        self.watch_percentage = 1.0  # Default to 100%
        self.points_deviation = {}  # year-month -> deviation

    def set_monthly_availability(self, year: int, month: int, availability_vector: List[int]) -> None:
        """Set the availability vector for a specific month."""
        month_key = (year, month)
        self.availability_vectors[month_key] = availability_vector
        self._save_to_db()

    def get_monthly_availability(self, year: int, month: int) -> Optional[List[int]]:
        """Get the availability vector for a specific month."""
        month_key = (year, month)
        return self.availability_vectors.get(month_key)

    def calculate_monthly_availability(self, year: int, month: int) -> Tuple[int, int, float]:
        """
        Calculate the availability statistics for a given month.
        Returns a tuple of (available_days, total_days, availability_percentage)
        """
        month_key = f"{year:04d}-{month:02d}"
        if month_key not in self.availability_vectors:
            return 0, 0, 0.0

        vector = self.availability_vectors[month_key]
        total_days = len(vector)
        available_days = sum(1 for day in vector if day in [0, 4, 5, 6, 7, 8, 9])
        availability_percentage = (available_days / total_days) * 100 if total_days > 0 else 0.0

        return available_days, total_days, availability_percentage

    def calculate_watch_percentage(self, year: int, month: int) -> float:
        """
        Calculate the percentage of watches this person should stand based on their availability
        relative to the total availability of all watchstanders.
        Returns a float representing the percentage (0-100).
        """
        # Get this watchstander's available days
        available_days, _, _ = self.calculate_monthly_availability(year, month)
        
        # Get total available days across all watchstanders
        total_available, individual_available = calculate_total_availability(year, month)
        
        if total_available == 0:
            return 0.0
            
        # Calculate percentage
        return (available_days / total_available) * 100

    def calculate_expected_watch_points(self, year: int, month: int, month_vector: List[int], n_head_count: int = 0) -> float:
        """
        Calculate the expected watch points this person should stand based on their availability percentage
        and the daily watch points from VALUE_KEY.
        
        Args:
            year: The year
            month: The month
            month_vector: List of integers representing the type of each day (0: workday, 1: leading into weekend, 2: weekend, 3: final weekend day)
            n_head_count: Number of N-heads in the month (used to calculate total N-head points)
            
        Returns:
            float: The expected number of watch points this person should stand
        """
        # Calculate total monthly points
        total_monthly_points = 0
        for day_type in month_vector:
            if day_type == 0:  # Full workday
                total_monthly_points += VALUE_KEY["Weekday day watch"] + VALUE_KEY["Weekday night watch"]
            elif day_type == 1:  # Leading into weekend
                total_monthly_points += VALUE_KEY["Friday day watch"] + VALUE_KEY["Friday night/Saturday/Sunday day"]  # 18 + 36
            elif day_type == 2:  # Weekend day
                total_monthly_points += VALUE_KEY["Friday night/Saturday/Sunday day"] + VALUE_KEY["Friday night/Saturday/Sunday day"]  # 36 + 36
            elif day_type == 3:  # Final day of a weekend
                total_monthly_points += VALUE_KEY["Friday night/Saturday/Sunday day"] + VALUE_KEY["Sunday night"]  # 36 + 20

        if self.is_n_head:
            # For N-heads, calculate their availability percentage and multiply by 28 points
            available_days, total_days, availability_percentage = self.calculate_monthly_availability(year, month)
            print(f"N-head {self.name} - Available Days: {available_days}, Total Days: {total_days}, Availability Percentage: {availability_percentage:.2f}%")
            expected_points = (availability_percentage / 100) * VALUE_KEY["Expected N-Head watch monthly (one weekday and one weekend)"]
            print(f"N-head {self.name} - Expected Points: {expected_points:.2f}")
        else:
            # Calculate total N-head points based on their availability percentages
            n_head_points = 0
            for ws in self.watchstanders:
                if ws.is_n_head:
                    available_days, total_days, availability_percentage = ws.calculate_monthly_availability(year, month)
                    n_head_points += (availability_percentage / 100) * VALUE_KEY["Expected N-Head watch monthly (one weekday and one weekend)"]
            
            # Calculate remaining points for regular watchstanders
            remaining_points = total_monthly_points - n_head_points
            
            # Calculate this person's percentage of watches among regular watchstanders
            watch_percentage = self.calculate_watch_percentage(year, month)
            
            # Calculate expected points from remaining points
            expected_points = (watch_percentage / 100) * remaining_points

        return expected_points

    def _save_to_db(self) -> None:
        """Save the watchstander's data to the database."""
        session = get_db_session()
        try:
            # Convert tuple keys to strings for JSON serialization
            serializable_vectors = {f"{year}-{month:02d}": vector for (year, month), vector in self.availability_vectors.items()}
            # Check if watchstander already exists
            existing = session.query(WatchstanderDB).filter_by(name=self.name).first()
            
            if existing:
                # Update existing record
                existing.is_n_head = self.is_n_head
                existing.availability_vectors = serializable_vectors
            else:
                # Create new record
                new_ws = WatchstanderDB(
                    name=self.name,
                    is_n_head=self.is_n_head,
                    availability_vectors=serializable_vectors
                )
                session.add(new_ws)
            
            session.commit()
        finally:
            session.close()

    @classmethod
    def load_from_db(cls, name: str) -> Optional['Watchstander']:
        """Load a watchstander from the database by name."""
        session = get_db_session()
        try:
            db_watchstander = session.query(WatchstanderDB).filter_by(name=name).first()
            if db_watchstander:
                watchstander = cls(
                    name=db_watchstander.name,
                    is_n_head=db_watchstander.is_n_head
                )
                watchstander.availability_vectors = db_watchstander.availability_vectors
                return watchstander
            return None
        finally:
            session.close()

    def __str__(self) -> str:
        return f"{self.name} (N-Head: {self.is_n_head})"

    def set_watch_percentage(self, percentage: float) -> None:
        """Set the watch percentage for the watchstander.
        
        Args:
            percentage (float): Watch percentage (0.0 to 1.0)
        """
        self.watch_percentage = percentage

    def update_points_deviation(self, year: int, month: int, expected_points: float, actual_points: float) -> None:
        """Update the points deviation for a specific month.
        
        Args:
            year (int): Year
            month (int): Month (1-12)
            expected_points (float): Expected points for the month
            actual_points (float): Actual points for the month
        """
        key = f"{year}-{month:02d}"
        self.points_deviation[key] = actual_points - expected_points

    def get_points_deviation(self, year: int, month: int) -> float:
        """Get the points deviation for a specific month.
        
        Args:
            year (int): Year
            month (int): Month (1-12)
            
        Returns:
            float: Points deviation (actual - expected)
        """
        key = f"{year}-{month:02d}"
        return self.points_deviation.get(key, 0.0)

if __name__ == "__main__":
    # Example usage
    watchstander1 = Watchstander("John Doe", True)  # N-head
    watchstander2 = Watchstander("Jane Smith", False)  # Regular watchstander
    
    # Example availability vectors for January 2023
    jan_availability1 = [0] * 31  # 31 days of January
    jan_availability1[14:20] = [1, 2, 2, 2, 2, 3]  # Leave from 15th to 20th
    watchstander1.set_monthly_availability(2023, 1, jan_availability1)
    
    jan_availability2 = [0] * 31  # 31 days of January
    jan_availability2[10:15] = [1, 2, 2, 2, 3]  # Leave from 11th to 15th
    watchstander2.set_monthly_availability(2023, 1, jan_availability2)
    
    # Example month vector for January 2023 (simplified)
    jan_month_vector = [0] * 31  # All workdays for simplicity
    jan_month_vector[6:8] = [1, 2, 2, 3]  # Weekend
    jan_month_vector[13:15] = [1, 2, 2, 3]  # Weekend
    jan_month_vector[20:22] = [1, 2, 2, 3]  # Weekend
    jan_month_vector[27:29] = [1, 2, 2, 3]  # Weekend
    
    # Calculate expected watch points
    points1 = watchstander1.calculate_expected_watch_points(2023, 1, jan_month_vector, n_head_count=1)
    points2 = watchstander2.calculate_expected_watch_points(2023, 1, jan_month_vector, n_head_count=1)
    
    print(f"John Doe (N-head) expected watch points: {points1:.1f}")
    print(f"Jane Smith (Regular) expected watch points: {points2:.1f}") 