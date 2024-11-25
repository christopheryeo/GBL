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

    log_manager.log("\nStarting Kardex spreadsheet analysis")
    
    for sheet_name in sheets:
        try:
            log_manager.log(f"\n{'='*50}")
            log_manager.log(f"Reading sheet: {sheet_name}")
            log_manager.log(f"{'='*50}")

            # Read the Excel file with headers at row 4 (index 3)
            df = pd.read_excel(excel_path, sheet_name=sheet_name, header=3)
            
            # Add vehicle_type column based on sheet name
            df['vehicle_type'] = sheet_name
            
            # Log the first 4 rows of data with all columns
            log_manager.log("\nFirst 4 rows of vehicle type DataFrame:")
            log_manager.log("-" * 50)
            
            for idx, row in df.head(4).iterrows():
                log_manager.log(f"\nRow {idx + 5}:")  # Adding 5 because we skipped 4 rows and idx is 0-based
                for col in df.columns:
                    value = row[col]
                    if pd.notnull(value):
                        if isinstance(value, pd.Timestamp):
                            value = value.strftime('%Y-%m-%d %H:%M:%S')
                        log_manager.log(f"  {col}: {value}")
                log_manager.log("-" * 50)

        except Exception as e:
            log_manager.log(f"Error processing sheet {sheet_name}: {str(e)}")

if __name__ == "__main__":
    read_and_log_kardex()
