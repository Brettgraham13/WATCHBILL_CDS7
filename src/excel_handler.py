"""
Module for handling Excel file operations.
"""
import pandas as pd
from pathlib import Path

class ExcelHandler:
    def __init__(self, file_path: str = "TROOP TO TASK - Watchbill Working Document.xlsx"):
        """Initialize the Excel handler with the file path."""
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"Excel file not found at {file_path}")
        
    def read_excel(self, sheet_name: str = None) -> pd.DataFrame:
        """Read the Excel file and return a pandas DataFrame."""
        try:
            if sheet_name:
                return pd.read_excel(self.file_path, sheet_name=sheet_name)
            return pd.read_excel(self.file_path)
        except Exception as e:
            raise Exception(f"Error reading Excel file: {str(e)}")
    
    def get_sheet_names(self) -> list:
        """Get all sheet names from the Excel file."""
        try:
            return pd.ExcelFile(self.file_path).sheet_names
        except Exception as e:
            raise Exception(f"Error getting sheet names: {str(e)}")

def read_excel_file(file_path):
    """Read the Excel file and return the available sheets."""
    try:
        xls = pd.ExcelFile(file_path)
        sheets = xls.sheet_names
        print("Available sheets:", sheets)
        # Read the 'Spreadsheet Key' sheet
        if 'Spreadsheet Key' in sheets:
            key_sheet = pd.read_excel(file_path, sheet_name='Spreadsheet Key')
            print("\nContents of 'Spreadsheet Key' sheet:")
            print(key_sheet)
        return sheets
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return []

def main():
    """Main function to test the Excel handler."""
    file_path = "TROOP TO TASK - Watchbill Working Document.xlsx"
    sheets = read_excel_file(file_path)
    if sheets:
        print("\nFirst few rows of the first sheet:")
        df = pd.read_excel(file_path, sheet_name=sheets[0])
        print(df.head())

if __name__ == "__main__":
    main() 