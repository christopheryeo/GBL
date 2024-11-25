import os
import sys
import pandas as pd
from datetime import datetime

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from LogManager import LogManager
from FileRead import load_kardex_data
from ExcelProcessor import ExcelProcessor

def test_kardex_file():
    # Initialize logging
    log_manager = LogManager()
    log_manager.log("\n=== Starting Kardex File Read Test ===")
    
    # Get the path to the test file
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    kardex_file = os.path.join(current_dir, 'uploads', 'Kardex_for_vehicle_6_years_old.xlsx')
    
    log_manager.log(f"Testing file: {kardex_file}")
    
    try:
        # Test direct Excel reading (first 3 rows)
        log_manager.log("\n=== Testing Direct Excel Reading ===")
        raw_df = pd.read_excel(kardex_file)
        for i in range(3):
            log_manager.log(f"Row {i + 1}: {raw_df.iloc[i].tolist()}")
        
        # Test FileRead module
        log_manager.log("\n=== Testing FileRead Module ===")
        df, result = load_kardex_data(kardex_file)
        if result['success']:
            log_manager.log("FileRead: Successfully loaded Kardex data")
            log_manager.log(f"Number of columns: {len(df.columns)}")
            log_manager.log(f"Column names: {', '.join(df.columns.tolist())}")
            log_manager.log("\nFirst 3 rows of processed data:")
            for i in range(min(3, len(df))):
                log_manager.log(f"Row {i + 1}: {df.iloc[i].to_dict()}")
        else:
            log_manager.log(f"FileRead Error: {result['message']}")
        
        # Test ExcelProcessor
        log_manager.log("\n=== Testing ExcelProcessor ===")
        processor = ExcelProcessor(log_manager)
        result = processor.process_excel(file_path=kardex_file, filename=os.path.basename(kardex_file))
        if result:
            log_manager.log("\nFile Info:")
            log_manager.log(result['file_info'])
            
            log_manager.log("\nProcessed Data:")
            data = result['data']
            if data:
                log_manager.log(f"Number of records: {len(data)}")
                if len(data) > 0:
                    log_manager.log("First 3 records:")
                    for i in range(min(3, len(data))):
                        log_manager.log(f"Record {i + 1}: {data[i]}")
            else:
                log_manager.log("No data processed")
        
        log_manager.log("\n=== Kardex File Read Test Completed Successfully ===")
        
    except Exception as e:
        log_manager.log(f"Error during testing: {str(e)}")
        raise

if __name__ == '__main__':
    test_kardex_file()
