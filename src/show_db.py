"""
Script to display the contents of the watchbill database.
"""
from src.database import get_db_session, WatchstanderDB
from src.month import Month
from src.watchstander import Watchstander
from src.month_vector_generator import generate_month_vector
import json
from datetime import datetime
import pandas as pd
from collections import Counter
from src.constants import VALUE_KEY, MONTH_KEY
import argparse

def format_datetime(dt):
    """Format datetime for display."""
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def format_availability_vectors(vectors):
    """Format availability vectors for display."""
    if not vectors:
        return "No availability data"
    
    formatted = {}
    for month_key, vector in vectors.items():
        # Convert vector to more readable format using BODY_KEY
        readable_vector = []
        for day in vector:
            if day == 0:
                readable_vector.append("Available")
            elif day == 1:
                readable_vector.append("Leave Start")
            elif day == 2:
                readable_vector.append("On Leave")
            elif day == 3:
                readable_vector.append("Leave End")
            elif day == 4:
                readable_vector.append("Special Lib Start")
            elif day == 5:
                readable_vector.append("Special Lib")
            elif day == 6:
                readable_vector.append("Special Lib End")
            elif day == 7:
                readable_vector.append("Local Event")
            elif day == 8:
                readable_vector.append("Day Watch")
            elif day == 9:
                readable_vector.append("Night Watch")
            else:
                readable_vector.append(f"Unknown({day})")
        formatted[month_key] = readable_vector
    return json.dumps(formatted, indent=2)

def show_database_contents():
    """Display all watchstanders in the database."""
    session = get_db_session()
    try:
        watchstanders = session.query(WatchstanderDB).all()
        
        print("\n=== Watchbill Database Contents ===\n")
        
        for ws in watchstanders:
            print(f"Watchstander: {ws.name}")
            print(f"  ID: {ws.id}")
            print("  Availability Vectors:")
            print(format_availability_vectors(ws.availability_vectors))
            print("\n" + "-"*50 + "\n")
            
        print(f"Total Watchstanders: {len(watchstanders)}")
        
    finally:
        session.close()

def show_database_table():
    """Display the watchstander database in a table format."""
    session = get_db_session()
    try:
        parser = argparse.ArgumentParser(description='Display the contents of the watchbill database.')
        parser.add_argument('--year', type=int, required=True, help='Year to display data for.')
        parser.add_argument('--month', type=int, required=True, help='Month to display data for.')
        args = parser.parse_args()

        # Create a Month instance for the specified year and month
        month = Month(args.year, args.month)
        
        # Store watchstanders in original order
        watchstanders_in_order = []
        
        # Add each watchstander to the month
        for ws in session.query(WatchstanderDB).all():
            # Convert WatchstanderDB to Watchstander
            watchstander = Watchstander(
                name=ws.name,
                is_n_head=ws.is_n_head
            )
            # Set availability
            month_key = (args.year, args.month)
            month_vector = ws.availability_vectors.get(month_key, [])
            watchstander.set_monthly_availability(args.year, args.month, month_vector)
            month.add_watchstander(watchstander)
            watchstanders_in_order.append(watchstander)
        
        # Get month summary
        summary = month.get_month_summary()
        
        # Print month vector summary
        print(f"\n=== {args.year}-{args.month:02d} Month Vector Summary ===")
        print(f"Total days in month: {len(month.month_vector)}")
        print("\nDay type distribution:")
        day_type_counts = Counter(month.month_vector)
        for day_type, count in sorted(day_type_counts.items()):
            print(f"{day_type} ({MONTH_KEY[day_type]}): {count} days")
        
        # Print detailed watchstander summary
        print("\n=== Watchstander Summary Table ===")
        
        # Prepare data for DataFrame
        data = []
        for ws in watchstanders_in_order:
            expected_points = summary['expected_points'][ws.name]
            
            # Calculate actual points from availability vector
            actual_points = 0.0
            month_vector = ws.availability_vectors.get(month_key, [])
            print(f"Watchstander: {ws.name}, Availability Vector: {month_vector}")
            for day_idx, val in enumerate(month_vector):
                day_type = month.month_vector[day_idx]
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
            print(f"Watchstander: {ws.name}, Actual Points: {actual_points}")
            
            # Get points deviation
            deviation = ws.get_points_deviation(args.year, args.month)
            
            row = {
                'Name': ws.name,
                'Expected Points': f"{expected_points:.1f}",
                'Actual Points': f"{actual_points:.1f}",
                'Points Deviation': f"{deviation:+.1f}"
            }
            data.append(row)
        
        # Create DataFrame and display
        df = pd.DataFrame(data)
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        print(df.to_string(index=False))
        
        # Calculate total actual points
        total_actual = sum(float(row['Actual Points']) for row in data)
        
        # Print total points
        total_expected = sum(summary['expected_points'].values())
        print(f"\nTotal Expected Points for {args.year}-{args.month:02d}: {total_expected:.1f}")
        print(f"Total Actual Points for {args.year}-{args.month:02d}: {total_actual:.1f}")
        print(f"Difference: {total_actual - total_expected:+.1f} points")
        
    finally:
        session.close()

if __name__ == "__main__":
    show_database_table() 