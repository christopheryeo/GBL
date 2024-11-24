"""
Test script to verify Excel reading functionality.
"""
import os
import pandas as pd
from src.LogManager import LogManager

def test_kardex_reading():
    log_manager = LogManager()
    
    # Clear application.log before starting
    open('application.log', 'w').close()
    
    log_manager.log("\n=== Starting Kardex Excel Reading Test ===")
    
    # Get the Excel file path
    excel_file = os.path.join('uploads', 'Kardex_for_vehicle_6_years_old.xlsx')
    if not os.path.exists(excel_file):
        log_manager.log(f"Error: Excel file not found at {excel_file}")
        return
        
    try:
        # Read all sheets
        excel = pd.ExcelFile(excel_file)
        log_manager.log(f"\nFound {len(excel.sheet_names)} sheets: {excel.sheet_names}")
        
        for sheet_name in excel.sheet_names:
            log_manager.log(f"\n=== Sheet: {sheet_name} ===")
            
            # Read without headers first to see raw data
            df_raw = pd.read_excel(excel, sheet_name=sheet_name, header=None)
            log_manager.log("\nFirst 3 rows (raw):")
            log_manager.log(df_raw.head(3).to_string())
            
            # Read with header at row 4 (0-based index 3)
            df = pd.read_excel(excel, sheet_name=sheet_name, header=3)
            
            # Log specific columns and first 4 rows to application.log
            with open('application.log', 'a') as f:
                f.write(f"\n=== DataFrame Contents for Sheet: {sheet_name} ===\n")
                selected_columns = ['WO No', 'Nature of Complaint', 'Job Description']
                f.write(f"\nSelected Columns: {selected_columns}\n")
                f.write("\nFirst 4 rows of data:\n")
                f.write(df[selected_columns].head(4).to_string())
                f.write("\n" + "="*80 + "\n")
            
            log_manager.log("\nColumns after reading with header=3:")
            log_manager.log(str(list(df.columns)))
            log_manager.log("\nFirst 4 rows of data:")
            log_manager.log(df.head(4).to_string())
            
    except Exception as e:
        log_manager.log(f"Error reading Excel file: {str(e)}")
        
if __name__ == '__main__':
    test_kardex_reading()
