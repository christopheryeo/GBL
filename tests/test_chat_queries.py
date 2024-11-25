#!/usr/bin/env python3
"""
Test script for PandasChat functionality focusing on fault categories.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).parent.parent / 'src'
sys.path.append(str(src_dir))

from PandasChat import PandasChat
from LogManager import LogManager
from VehicleFaults import VehicleFault
import pandas as pd

class MockLogger(LogManager):
    """Custom logger for testing that writes to console only."""
    def log(self, message):
        """Override log method to print to console."""
        timestamp = datetime.now().strftime('[%Y-%m-%d %H:%M:%S.%f]')
        log_entry = f"{timestamp} {message}"
        print(log_entry)  # Print to console

def create_test_data():
    """Create sample data for testing."""
    data = {
        'WO No': ['WO001', 'WO002', 'WO003', 'WO004'],
        'Nature of Complaint': [
            'Engine overheating and coolant leak',
            'Transmission making noise when shifting',
            'Battery not charging, alternator issue',
            'Brake pedal feels soft, possible fluid leak'
        ],
        'Job Description': [
            'Replace radiator and thermostat',
            'Repair transmission gear selector',
            'Replace alternator and battery',
            'Replace brake master cylinder'
        ],
        'Open Date': ['2023-01-01', '2023-02-01', '2023-03-01', '2023-04-01'],
        'Done Date': ['2023-01-02', '2023-02-03', '2023-03-02', '2023-04-03']
    }
    return VehicleFault(pd.DataFrame(data))

def test_fault_categories():
    """Test fault category queries."""
    logger = MockLogger('test.log')
    chat = PandasChat(logger)
    data = create_test_data()
    
    print("\n=== Testing Fault Categories ===")
    
    # Test main categories
    print("\nTesting main categories query...")
    query = "What is the list of fault categories?"
    response = chat.query(data, query)
    print(f"Query: {query}")
    print(f"Response: {response}")
    
    # Test subcategories
    print("\nTesting subcategories query...")
    query = "What is the list of fault sub-categories?"
    response = chat.query(data, query)
    print(f"Query: {query}")
    print(f"Response: {response}")
    
    # Test categorization
    print("\nVerifying fault categorization...")
    categories = {
        'Engine': 'Engine overheating and coolant leak',
        'Transmission': 'Transmission making noise when shifting',
        'Electrical': 'Battery not charging, alternator issue',
        'Brakes': 'Brake pedal feels soft, possible fluid leak'
    }
    
    for category, complaint in categories.items():
        faults = data[data['Nature of Complaint'] == complaint]
        if not faults.empty:
            print(f"\nFound {category} fault:")
            print(f"Complaint: {complaint}")
            print(f"Main Category: {faults['FaultMainCategory'].iloc[0]}")
            print(f"Sub Category: {faults['FaultSubCategory'].iloc[0]}")
        else:
            print(f"\nWarning: Could not find fault with complaint: {complaint}")

if __name__ == '__main__':
    test_fault_categories()
