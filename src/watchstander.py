"""
Module for defining the Watchstander class.
"""
from datetime import datetime

class Watchstander:
    def __init__(self, name: str, check_in_date: datetime, qualification_date: datetime, is_n_head: bool):
        self.name = name
        self.check_in_date = check_in_date
        self.qualification_date = qualification_date
        self.is_n_head = is_n_head

    def __str__(self) -> str:
        return f"{self.name} (Check-in: {self.check_in_date}, Qualified: {self.qualification_date}, N-Head: {self.is_n_head})"

if __name__ == "__main__":
    # Example usage
    watchstander = Watchstander("John Doe", datetime(2023, 1, 1), datetime(2023, 2, 1), True)
    print(watchstander) 