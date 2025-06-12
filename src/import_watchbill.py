import sys
import pandas as pd
from src.month import Month
from src.watchstander import Watchstander
from src.constants import BODY_KEY
from typing import List
import argparse

def build_month_from_excel(filepath, year, month, n_heads=None):
    """
    Build a Month object from an Excel file for the given year and month.
    Args:
        filepath (str): Path to the Excel file
        year (int): Year (e.g., 2025)
        month (int): Month (1-12)
        n_heads (set or list): Names of N-heads (optional)
    Returns:
        Month: Populated Month object
    """
    df = pd.read_excel(filepath)
    if df.empty:
        raise ValueError("Excel file is empty or not found.")
    
    # Assume first row is header, first column is name, rest are availability
    month_obj = Month(year, month)
    n_heads = set(n_heads) if n_heads else set()
    for _, row in df.iterrows():
        name = row.iloc[0]
        if pd.isna(name):
            continue
        is_n_head = name in n_heads
        # Fill NaN with 0 in the availability vector
        availability_vector = [int(x) if not pd.isna(x) else 0 for x in row.iloc[1:]]
        print(f"Watchstander: {name}, Availability Vector: {availability_vector}")  # Debug print
        # Check if the watchstander already exists
        existing_watchstander = next((w for w in month_obj.watchstanders if w.name == name), None)
        if existing_watchstander:
            existing_watchstander.set_monthly_availability(year, month, availability_vector)
        else:
            ws = Watchstander(name=name, is_n_head=is_n_head)
            ws.set_monthly_availability(year, month, availability_vector)
            month_obj.add_watchstander(ws)
    return month_obj

def build_month_from_table(table_text: str, year: int, month: int, n_heads: List[str]) -> Month:
    """
    Build a Month object from a pasted table.
    
    Args:
        table_text (str): The pasted table text.
        year (int): The year.
        month (int): The month.
        n_heads (List[str]): List of N-head names.
        
    Returns:
        Month: The constructed Month object.
    """
    month_obj = Month(year, month)
    lines = table_text.strip().split('\n')
    for line in lines:
        parts = line.strip().split('\t')
        if len(parts) >= 2:
            name = parts[0].strip()
            availability_vector = [int(part.strip()) for part in parts[1:]]
            # Check if the watchstander already exists
            existing_watchstander = next((w for w in month_obj.watchstanders if w.name == name), None)
            if existing_watchstander:
                existing_watchstander.set_monthly_availability(year, month, availability_vector)
            else:
                watchstander = Watchstander(name, name in n_heads)
                watchstander.set_monthly_availability(year, month, availability_vector)
                month_obj.add_watchstander(watchstander)
    return month_obj

def print_month_summary(month_obj):
    """
    Print a summary of the month.
    Args:
        month_obj (Month): The Month object
    """
    summary = month_obj.get_month_summary()
    print(f"\n=== {month_obj.year}-{month_obj.month:02d} Watchbill Summary ===")
    print(f"Total Watchstanders: {len(month_obj.watchstanders)}")
    print(f"Total Expected Points: {sum(summary['expected_points'].values()):.1f}")
    print(f"Total Actual Points: {sum(summary['actual_points'].values()):.1f}")
    print("\nWatchstander Breakdown:")
    for name in summary['expected_points']:
        print(f"{name:20}  Expected: {summary['expected_points'][name]:6.1f}  Actual: {summary['actual_points'][name]:6.1f}  Deviation: {summary['actual_points'][name] - summary['expected_points'][name]:+6.1f}")

def print_watchstander_points(month_obj):
    """
    Print the expected and actual watch points for each watchstander.
    Args:
        month_obj (Month): The Month object
    """
    summary = month_obj.get_month_summary()
    print('\nWatchstander Breakdown:')
    for name in summary['expected_points']:
        print(f'{name:20}  Expected: {summary["expected_points"][name]:6.1f}  Actual: {summary["actual_points"][name]:6.1f}  Deviation: {summary["actual_points"][name] - summary["expected_points"][name]:+6.1f}')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Import watchbill data from a file.')
    parser.add_argument('filepath', type=str, help='Path to the file containing watchbill data.')
    parser.add_argument('year', type=int, help='Year of the watchbill data.')
    parser.add_argument('month', type=int, help='Month of the watchbill data.')
    parser.add_argument('--n-heads', nargs='*', help='List of N-head names.')
    args = parser.parse_args()

    # Example usage of build_month_from_table
    table_text = """
    LTJG Bailey	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	0	0	0	8	0	0	0	0
    CTTC Thompson	2	3	0	8	0	0	1	2	2	3	0	0	0	0	0	0	8	0	0	0	9	0	0	0	0	0	0	0
    ISC Alumia	0	0	0	0	0	0	0	9	0	1	2	2	2	2	3	0	0	0	8	0	0	0	0	0	0	0	0	9
    LT Maligsa	8	0	1	2	2	2	2	2	2	2	2	2	2	2	3	0	0	0	0	9	0	0	0	0	0	0	0	8
    LT Hespen	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2
    OS1 Tillman	0	0	0	9	0	0	0	0	0	0	0	9	0	0	0	8	0	0	0	0	0	0	0	0	0	0	0	0
    LCDR  Despota	0	0	0	0	0	0	8	0	0	0	0	0	8	0	4	5	5	6	0	1	2	2	3	0	0	0	0	0
    ENC Tran	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2
    EMC Daves	0	0	0	0	0	0	0	0	8	0	0	0	9	0	0	0	0	0	0	0	0	0	0	0	0	0	8	0
    GSMC Mckeown	2	3	2	2	2	2	2	2	2	2	2	2	2	3	0	0	0	0	0	0	0	0	0	0	0	0	0	0
    ETC Pearson	2	2	2	3	0	0	1	2	2	2	2	2	2	2	2	2	3	0	0	0	0	9	0	0	0	8	0	0
    LSC Smith	0	9	0	0	0	0	0	0	0	0	0	0	0	8	1	2	2	2	2	2	2	2	3	0	0	0	0	0
    FC1 Fernandez	0	1	2	2	2	2	3	0	0	0	0	0	0	0	0	9	0	0	0	0	0	0	0	0	0	0	9	0
    GMC Ogle	0	0	0	0	0	0	9	0	9	0	0	0	0	0	0	0	0	9	0	0	0	0	0	0	0	0	0	0
    DCC Allen	0	0	0	0	0	9	0	0	0	8	0	0	0	0	0	0	0	0	0	0	0	0	0	0	9	0	0	0
    LT Graham	1	2	2	2	2	2	3	0	1	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2
    LT Decker	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2
    LT Garcia	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2
    STGC Placencia	3	0	0	0	8	0	1	2	2	2	2	2	2	2	3	0	0	0	9	0	0	0	8	0	0	0	0	0
    ITC Antero	0	0	9	0	0	0	0	8	0	0	0	0	0	0	1	2	2	2	2	2	2	2	2	2	2	2	2	3
    ITC  Valencia	2	2	2	2	2	2	2	2	3	0	0	0	0	0	8	0	0	0	0	0	0	0	0	0	0	9	0	0
    IT1 Lucas	0	8	0	0	9	0	1	2	2	3	0	8	0	0	0	0	0	0	0	0	0	0	0	9	0	0	0	0
    BMC Fuentes	0	0	0	0	0	8	0	0	0	0	9	0	0	4	5	5	6	0	0	0	0	0	9	0	0	0	0	0
    LTJG  Moore	0	0	1	2	2	3	0	0	1	2	2	2	2	3	0	0	9	0	0	0	0	8	0	1	2	2	2	3
    LT Parra	0	0	0	0	0	0	0	0	0	9	0	0	0	9	0	0	0	8	0	0	0	0	0	0	0	0	0	0
    GMC Bartelmey	9	0	0	0	1	2	2	2	2	2	2	3	0	0	9	0	0	0	0	0	0	0	0	0	0	0	0	0
    CDR Ivey	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2
    LCDR  Huntley	0	0	8	0	0	0	0	0	0	0	8	0	0	0	0	0	0	0	0	0	8	0	0	0	0	0	0	0
    LCDR  Kim	2	2	2	2	2	0	0	0	1	2	2	2	2	2	2	3	0	0	0	8	7	0	0	0	0	0	0	0
    LCDR  DeSormier	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	2	0	8	1	2	2
    """

    n_heads = ["CDR Ivey", "LCDR Kim", "LCDR Huntley", "LCDR DeSormier", "LCDR Despota"]
    february_month = build_month_from_table(table_text, args.year, args.month, n_heads)
    print_month_summary(february_month)
    print_watchstander_points(february_month) 