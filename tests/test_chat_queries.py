#!/usr/bin/env python3
"""
Test script for PandasChat functionality.
This script reads test questions from a file and runs them through the PandasChat system,
logging both queries and responses for analysis.
"""

import os
import sys
import pandas as pd
from datetime import datetime
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).parent.parent / 'src'
sys.path.append(str(src_dir))

from PandasChat import PandasChat
from LogManager import LogManager
from VehicleFaults import VehicleFault

class TestLogger(LogManager):
    """Custom logger for testing that writes to both console and file."""
    def __init__(self, log_file):
        super().__init__(log_file)
        
    def log(self, message):
        """Override log method to also print to console."""
        timestamp = datetime.now().strftime('[%Y-%m-%d %H:%M:%S.%f]')
        log_entry = f"{timestamp} {message}"
        print(log_entry)  # Print to console
        with open(self.log_file, 'a') as f:
            f.write(log_entry + '\n')

def load_test_questions(file_path):
    """Load test questions from file, skipping comments and empty lines."""
    questions = []
    current_category = "Uncategorized"
    
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:  # Skip empty lines
                continue
            if line.startswith('#'):  # Category marker
                current_category = line[1:].strip()
                continue
            questions.append({
                'category': current_category,
                'query': line
            })
    return questions

def load_sample_data(excel_file):
    """Load sample Excel data for testing."""
    if not os.path.exists(excel_file):
        raise FileNotFoundError(f"Sample data file not found: {excel_file}")
    
    # Read the Excel file with all sheets
    all_data = []
    xlsx = pd.ExcelFile(excel_file)
    
    for sheet_name in xlsx.sheet_names:
        # Extract vehicle type from sheet name (e.g., "14 ft (6yrs)" -> "14 ft")
        vehicle_type = sheet_name.split('(')[0].strip()
        
        # Read the sheet
        df = pd.read_excel(xlsx, sheet_name)
        
        # Rename unnamed columns to match expected format
        column_mapping = {
            'Unnamed: 0': 'WO No',
            'Unnamed: 1': 'Loc',
            'Unnamed: 2': 'ST',
            'Unnamed: 3': 'Mileage',
            'Unnamed: 4': 'Open Date',
            'Unnamed: 5': 'Done Date',
            'Unnamed: 6': 'Actual Finish Date',
            'Unnamed: 7': 'Nature of Complaint',
            'Unnamed: 8': 'Fault Codes',
            'Unnamed: 9': 'Job Description',
            'Unnamed: 10': 'SRR No.',
            'Unnamed: 11': 'Mechanic Name',
            'Unnamed: 12': 'Customer',
            'Unnamed: 13': 'Customer Name',
            'Unnamed: 14': 'Recommendation 4 next',
            'Unnamed: 15': 'Cat',
            'Unnamed: 16': 'Lead Tech',
            'Unnamed: 17': 'Bill No.',
            'Unnamed: 18': 'Intercoamt',
            'Unnamed: 19': 'Custamt'
        }
        df = df.rename(columns=column_mapping)
        
        # Add vehicle type column
        df['Vehicle Type'] = vehicle_type
        
        # Convert to records and add to all_data
        sheet_data = df.to_dict('records')
        all_data.extend(sheet_data)
    
    return all_data

def run_tests(questions, data, logger):
    """Run all test questions through PandasChat."""
    chat = PandasChat(logger)
    
    logger.log("=== Starting Chat Query Tests ===")
    logger.log(f"Total questions to test: {len(questions)}")
    
    for i, q in enumerate(questions, 1):
        category = q['category']
        query = q['query']
        
        logger.log(f"\n=== Test {i} ({category}) ===")
        logger.log(f"Query: {query}")
        
        try:
            response = chat.query(data, query)
            logger.log(f"Response: {response}")
        except Exception as e:
            logger.log(f"Error: {str(e)}")
    
    logger.log("\n=== Test Run Completed ===")

def main():
    # Setup paths
    base_dir = Path(__file__).parent.parent
    questions_file = base_dir / 'tests' / 'test_questions.txt'
    sample_data_file = base_dir / 'uploads' / 'Kardex_for_vehicle_6_years_old.xlsx'
    test_log_file = base_dir / 'tests' / 'test_results.log'
    
    # Initialize logger
    logger = TestLogger(str(test_log_file))
    
    try:
        # Load test questions
        logger.log("Loading test questions...")
        questions = load_test_questions(questions_file)
        
        # Load sample data
        logger.log("Loading sample data...")
        data = load_sample_data(sample_data_file)
        
        # Run tests
        run_tests(questions, data, logger)
        
    except Exception as e:
        logger.log(f"Test setup failed: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
