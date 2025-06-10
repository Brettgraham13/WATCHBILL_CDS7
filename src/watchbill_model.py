"""
Module for implementing a watchbill model similar to the pseudo code.
"""
from datetime import datetime
from typing import List, Dict, Tuple
from src.watchstander import Watchstander
from src.constants import VALUE_KEY, BODY_KEY, RULES

class WatchbillModel:
    def __init__(self, month_vector: List[int], watchstanders: List[Watchstander]):
        self.month_vector = month_vector  # 0: workday, 1: leading into weekend, 2: weekend, 3: final weekend day
        self.watchstanders = watchstanders
        self.wh = VALUE_KEY["Working hour"]  # Working hour weight
        self.wodh = VALUE_KEY["Off duty hour"]  # Weekday off-duty hour weight
        self.weh = VALUE_KEY["Weekend/Holiday Hour"]  # Weekend hour weight

    def monthly_total(self) -> List[int]:
        """Calculate total shift points for each day of the month."""
        monthly_total = []
        for day in self.month_vector:
            if day == 0:  # Full workday
                monthly_total.append(16 * self.wodh + 8 * self.wh)
            elif day == 1:  # Leading into weekend
                monthly_total.append(8 * self.wodh + 8 * self.wh + 8 * self.weh)
            elif day in [2, 3]:  # Weekend or final weekend day
                monthly_total.append(24 * self.weh)
            else:
                raise ValueError("Invalid input in month vector")
        return monthly_total

    def monthly_total_score(self) -> int:
        """Calculate total shift points for the month."""
        return sum(self.monthly_total())

    def personnel_availability_vector(self, availability: List[int]) -> List[int]:
        """Calculate availability vector for a person."""
        output_vector = []
        monthly_total = self.monthly_total()
        for i, avail in enumerate(availability):
            if avail in [0, 4, 5, 6]:  # Available or special cases
                output_vector.append(monthly_total[i])
            elif avail in [1, 2, 3, 7]:  # Unavailable
                output_vector.append(0)
            else:
                raise ValueError("Invalid input in availability vector")
        return output_vector

    def watchbill_availability(self, availability: List[int]) -> List[int]:
        """Determine which watches a person is available for."""
        watchbill_availability = []
        for i, avail in enumerate(availability):
            if avail in [1, 2, 3, 4, 5, 7]:  # Unavailable
                watchbill_availability.append(0)
            elif i > 0 and availability[i - 1] == 3 or i < len(availability) - 1 and availability[i + 1] == 1:
                watchbill_availability.append(0)  # Rule 2: No watch before leave/TDY/special liberty
            elif i > 0 and availability[i - 1] == 6 and avail == 0:
                watchbill_availability.append(2)  # Night watch only
            elif avail == 0 and i < len(availability) - 1 and availability[i + 1] == 4:
                watchbill_availability.append(1)  # Day watch only
            elif i > 0 and avail == 0 and i < len(availability) - 1 and availability[i - 1] == 0 and availability[i + 1] == 0:
                watchbill_availability.append(3)  # Available for either watch
            else:
                watchbill_availability.append(0)
        return watchbill_availability

    def expected_watch_vector(self, availability_matrix: List[List[int]]) -> List[float]:
        """Calculate expected watch points per person."""
        monthly_total = self.monthly_total()
        monthly_total_watch = self.monthly_total_score()
        watchstand_avail_vector = []
        command_availability = 0

        for person_availability in availability_matrix:
            output_vector = self.personnel_availability_vector(person_availability)
            watchstand_avail_vector.append(sum(output_vector))

        command_availability = sum(watchstand_avail_vector)
        expected_watch = [w / command_availability * monthly_total_watch for w in watchstand_avail_vector]
        return expected_watch

    def watchstander_availability(self, availability_matrix: List[List[int]]) -> List[List[int]]:
        """Convert availability matrix to watchbill availability matrix."""
        watchstander_availability = []
        for person_availability in availability_matrix:
            watchstander_availability.append(self.watchbill_availability(person_availability))
        return watchstander_availability

    def shift_evaluator(self, shift: str, date: int) -> int:
        """Evaluate points for a specific shift on a given date."""
        if shift == "D":
            if self.month_vector[date] == 0:
                return 4 * self.wodh + 8 * self.wh
            elif self.month_vector[date] == 1:
                return 8 * self.wodh + 4 * self.weh
            elif self.month_vector[date] in [2, 3]:
                return 12 * self.weh
        elif shift == "N":
            if self.month_vector[date] == 0:
                return 12 * self.wodh
            elif self.month_vector[date] in [1, 2]:
                return 12 * self.weh
            elif self.month_vector[date] == 3:
                return 4 * self.weh + 8 * self.wodh
        elif shift == "0":
            return 0
        raise ValueError("Invalid shift or date input")

    def evaluate_watchbill(self, watchbill: List[List[int]]) -> Dict[str, any]:
        """Evaluate a watchbill against the rules and return a score or feedback."""
        score = 0
        feedback = []

        # Rule 1: N3, N4, N5, N7 can only stand weekday day watches
        for i, person in enumerate(self.watchstanders):
            if person.is_n_head:
                for j, watch in enumerate(watchbill[i]):
                    if watch == 1 and self.month_vector[j] != 0:  # Day watch on non-workday
                        feedback.append(f"Rule 1 violation: {person.name} assigned day watch on non-workday.")

        # Rule 2: No watch before leave/TDY/special liberty
        for i, person in enumerate(watchbill):
            for j, watch in enumerate(person):
                if j > 0 and person[j - 1] in [1, 2, 3, 4, 5, 7]:  # Unavailable
                    if watch != 0:
                        feedback.append(f"Rule 2 violation: Watch scheduled before leave/TDY/special liberty.")

        # Rule 3: Two days before leave/TDY/special liberty, only night watch can be scheduled
        for i, person in enumerate(watchbill):
            for j, watch in enumerate(person):
                if j > 1 and person[j - 2] in [1, 2, 3, 4, 5, 7]:  # Unavailable
                    if watch == 1:  # Day watch
                        feedback.append(f"Rule 3 violation: Day watch scheduled two days before leave/TDY/special liberty.")

        # Rule 4: No watch after leave/TDY/special liberty
        for i, person in enumerate(watchbill):
            for j, watch in enumerate(person):
                if j < len(person) - 1 and person[j + 1] in [1, 2, 3, 4, 5, 7]:  # Unavailable
                    if watch != 0:
                        feedback.append(f"Rule 4 violation: Watch scheduled after leave/TDY/special liberty.")

        # Rule 5: Only night watch can be scheduled the day after leave/TDY/special liberty
        for i, person in enumerate(watchbill):
            for j, watch in enumerate(person):
                if j < len(person) - 1 and person[j + 1] in [1, 2, 3, 4, 5, 7]:  # Unavailable
                    if watch == 1:  # Day watch
                        feedback.append(f"Rule 5 violation: Day watch scheduled the day after leave/TDY/special liberty.")

        # Rule 6: Personnel are expected to stand an equivalent number of watches per month
        expected_watch = self.expected_watch_vector(watchbill)
        for i, person in enumerate(watchbill):
            total_watches = sum(1 for watch in person if watch != 0)
            if abs(total_watches - expected_watch[i]) > 1:
                feedback.append(f"Rule 6 violation: {self.watchstanders[i].name} has {total_watches} watches, expected {expected_watch[i]}.")

        # Rule 7: Working day defined as 0800-1600. Off duty hour defined as all other times
        # Rule 8: Weekend/holiday hour defined from 1600 Friday to 0800 Monday
        # Rule 9: All personnel stand at least one watch per month
        for i, person in enumerate(watchbill):
            if sum(1 for watch in person if watch != 0) == 0:
                feedback.append(f"Rule 9 violation: {self.watchstanders[i].name} has no watches assigned.")

        return {"score": score, "feedback": feedback}

    def calculate_total_watch_points(self) -> int:
        """Calculate the total watch points to be stood in the month."""
        total_points = 0
        for day in self.month_vector:
            if day == 0:  # Full workday
                total_points += VALUE_KEY["Weekday day watch"] + VALUE_KEY["Weekday night watch"]
            elif day == 1:  # Leading into weekend
                total_points += VALUE_KEY["Friday day watch"] + VALUE_KEY["Weekday night watch"]
            elif day == 2:  # Weekend day
                total_points += VALUE_KEY["Friday night/Saturday/Sunday day"] + VALUE_KEY["Sunday night"]
            elif day == 3:  # Final day of a weekend
                total_points += VALUE_KEY["Sunday night"] + VALUE_KEY["Weekday day watch"]
        return total_points

if __name__ == "__main__":
    # Example usage
    month_vector = [0, 0, 1, 2, 2, 3, 0, 0, 0, 0]  # Example month vector
    watchstanders = [
        Watchstander("John Doe", datetime(2023, 1, 1), datetime(2023, 2, 1), True),
        Watchstander("Jane Smith", datetime(2023, 1, 15), datetime(2023, 3, 1), False)
    ]
    model = WatchbillModel(month_vector, watchstanders)
    print("Monthly Total:", model.monthly_total())
    print("Monthly Total Score:", model.monthly_total_score()) 