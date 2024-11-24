import pandas as pd
import sys
import os
from datetime import datetime

# Add the src directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from LogManager import LogManager

# Initialize the log manager
log_manager = LogManager()

def read_and_log_kardex():
    excel_path = '/Users/chrisyeo/Library/CloudStorage/OneDrive-Personal/Dev/windsurf/GBL/uploads/Kardex_for_vehicle_6_years_old.xlsx'
    sheets = [
        'Lifestyle (6yrs)',
        '10 ft (6yrs)',
        '14 ft (6yrs)',
        '16 ft (6yrs)',
        '24 ft (6yrs)'
    ]

    log_manager.log("Starting Kardex spreadsheet analysis - First 5 columns from row 5 onwards")

    for sheet_name in sheets:
        try:
            log_manager.log(f"\n{'='*50}")
            log_manager.log(f"Reading sheet: {sheet_name}")
            log_manager.log(f"{'='*50}")

            # Read the Excel file with headers at row 4 (index 3)
            df = pd.read_excel(excel_path, sheet_name=sheet_name, header=3)
            
            # Get only the first 5 columns
            first_five_cols = ['WO No', 'Loc', 'ST', 'Mileage', 'Open Date']
            df = df[first_five_cols]
            
            # Skip to row 5 (index 4) and get the first 3 rows from there
            first_three = df.iloc[0:3]
            
            # Log each row
            for idx, row in first_three.iterrows():
                log_manager.log(f"Excel Row {idx + 5}:")  # Show actual Excel row number
                for col in first_five_cols:
                    value = row[col]
                    if pd.notnull(value):
                        if col == 'Open Date':
                            value = value.strftime('%Y-%m-%d %H:%M:%S')
                        log_manager.log(f"  {col}: {value}")
                log_manager.log("-" * 50)

        except Exception as e:
            log_manager.log(f"Error processing sheet {sheet_name}: {str(e)}")

if __name__ == "__main__":
    read_and_log_kardex()
