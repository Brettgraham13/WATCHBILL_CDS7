"""
Module for defining the Watchstander class.
"""
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from src.database import WatchstanderDB, get_db_session, calculate_total_availability
from src.constants import VALUE_KEY, MONTH_KEY

class Watchstander:
    def __init__(self, name: str, check_in_date: datetime, qualification_date: datetime, is_n_head: bool):
        self.name = name
        self.check_in_date = check_in_date
        self.qualification_date = qualification_date
        self.is_n_head = is_n_head
        self.availability_vectors: Dict[str, List[int]] = {}  # Key: "YYYY-MM", Value: List[int]

    def set_monthly_availability(self, year: int, month: int, availability_vector: List[int]) -> None:
        """Set the availability vector for a specific month."""
        month_key = f"{year:04d}-{month:02d}"
        self.availability_vectors[month_key] = availability_vector
        self._save_to_db()

    def get_monthly_availability(self, year: int, month: int) -> Optional[List[int]]:
        """Get the availability vector for a specific month."""
        month_key = f"{year:04d}-{month:02d}"
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

    def calculate_expected_watch_points(self, year: int, month: int, month_vector: List[int]) -> float:
        """
        Calculate the expected watch points this person should stand based on their availability percentage
        and the daily watch points from VALUE_KEY.
        
        Args:
            year: The year
            month: The month
            month_vector: List of integers representing the type of each day (0: workday, 1: leading into weekend, 2: weekend, 3: final weekend day)
            
        Returns:
            float: The expected number of watch points this person should stand
        """
        # Calculate availability percentage
        available_days, total_days, availability_percentage = self.calculate_monthly_availability(year, month)
        
        if self.is_n_head:
            # For N-heads, use their availability percentage of the expected N-head watch value
            expected_points = (availability_percentage / 100) * VALUE_KEY["Expected N-Head watch monthly (one weekday and one weekend)"]
        else:
            # For regular watchstanders, calculate based on total monthly points
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

            # Calculate this person's percentage of watches
            watch_percentage = self.calculate_watch_percentage(year, month)

            # Calculate expected points
            expected_points = (watch_percentage / 100) * total_monthly_points

        return expected_points

    def _save_to_db(self) -> None:
        """Save the watchstander to the database."""
        session = get_db_session()
        try:
            # Check if watchstander already exists
            db_watchstander = session.query(WatchstanderDB).filter_by(name=self.name).first()
            
            if db_watchstander:
                # Update existing record
                db_watchstander.check_in_date = self.check_in_date
                db_watchstander.qualification_date = self.qualification_date
                db_watchstander.is_n_head = self.is_n_head
                db_watchstander.availability_vectors = self.availability_vectors
            else:
                # Create new record
                db_watchstander = WatchstanderDB(
                    name=self.name,
                    check_in_date=self.check_in_date,
                    qualification_date=self.qualification_date,
                    is_n_head=self.is_n_head,
                    availability_vectors=self.availability_vectors
                )
                session.add(db_watchstander)
            
            session.commit()
        except Exception as e:
            session.rollback()
            raise Exception(f"Error saving watchstander to database: {str(e)}")
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
                    check_in_date=db_watchstander.check_in_date,
                    qualification_date=db_watchstander.qualification_date,
                    is_n_head=db_watchstander.is_n_head
                )
                watchstander.availability_vectors = db_watchstander.availability_vectors
                return watchstander
            return None
        finally:
            session.close()

    def __str__(self) -> str:
        return f"{self.name} (Check-in: {self.check_in_date}, Qualified: {self.qualification_date}, N-Head: {self.is_n_head})"

if __name__ == "__main__":
    # Example usage
    watchstander1 = Watchstander("John Doe", datetime(2023, 1, 1), datetime(2023, 2, 1), True)  # N-head
    watchstander2 = Watchstander("Jane Smith", datetime(2023, 1, 1), datetime(2023, 2, 1), False)  # Regular watchstander
    
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
    points1 = watchstander1.calculate_expected_watch_points(2023, 1, jan_month_vector)
    points2 = watchstander2.calculate_expected_watch_points(2023, 1, jan_month_vector)
    
    print(f"John Doe (N-head) expected watch points: {points1:.1f}")
    print(f"Jane Smith (Regular) expected watch points: {points2:.1f}") 