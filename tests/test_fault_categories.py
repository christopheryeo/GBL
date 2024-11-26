import sys
import os
from pathlib import Path
from collections import Counter, defaultdict
import pandas as pd
import pytest
from datetime import datetime

# Add the src directory to the Python path
src_dir = str(Path(__file__).parent.parent / 'src')
if src_dir not in sys.path:
    sys.path.append(src_dir)

from VehicleFaults import VehicleFault
from FileRead import FileReader
from config.TestConfig import test_config

def clear_log_file(log_file_path: str):
    """Clear the log file and write a header."""
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
    with open(log_file_path, 'w') as f:
        f.write(f"=== Log Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")

def test_analyze_fault_categories():
    """Test the fault categorization functionality."""
    try:
        # Get log file path from config
        log_config = test_config._config.get('logging', {}).get('test_fault_categories', {})
        log_file = log_config.get('log_file')
        
        # Clear log file if it exists
        if log_file:
            clear_log_file(log_file)
        
        # Initialize logger
        logger = test_config.get_logger('test_fault_categories')
        logger.info("\n=== Starting Fault Categories Analysis Test ===")
        
        # Initialize FileReader with logger
        file_reader = FileReader(logger)
        
        # Load the default Kardex file
        kardex_path = test_config.get_kardex_path()  # Uses default from test_config.yaml
        assert os.path.exists(kardex_path), f"Kardex file not found at {kardex_path}"
        logger.info(f"Testing default Kardex file: {kardex_path}")
            
        # Load data using FileReader
        df, vehicle_type, status = file_reader.load_kardex_data(kardex_path)
        assert status['success'], f"Failed to load Kardex file: {status['message']}"
        
        logger.info(f"Successfully loaded {len(df)} records")
        logger.info(f"Vehicle Type: {vehicle_type}")
        
        # Validate required columns from format configuration
        default_key = test_config.get_default_kardex()
        format_config = test_config.get_excel_format(default_key)
        
        required_columns = [col['name'] for col in format_config['format']['columns'] 
                          if col['required']]
        for col in required_columns:
            assert col in df.columns, f"Required column {col} missing"
        
        # Create VehicleFault instance
        vehicle_faults = VehicleFault(data=df)
        
        # Get fault statistics
        fault_analysis = vehicle_faults.get_fault_statistics()
        
        # Validate analysis results
        assert fault_analysis is not None, "Fault analysis returned None"
        assert isinstance(fault_analysis, dict), "Analysis result should be a dictionary"
        
        # Log analysis results
        logger.info("\nFault Category Analysis Results:")
        logger.info("-" * 50)
        
        # Log main categories
        if 'main_categories' in fault_analysis:
            logger.info("\nMain Categories Distribution:")
            total_faults = sum(fault_analysis['main_categories'].values())
            for category, count in fault_analysis['main_categories'].items():
                percentage = (count / total_faults) * 100
                logger.info(f"{category}: {count} occurrences ({percentage:.2f}%)")
        
        # Log subcategories for each main category
        if 'sub_categories' in fault_analysis:
            logger.info("\nSub-Categories Distribution:")
            for main_cat, sub_cats in fault_analysis['sub_categories'].items():
                logger.info(f"\n{main_cat}:")
                total_sub = sum(sub_cats.values())
                for sub_cat, count in sub_cats.items():
                    percentage = (count / total_sub) * 100
                    logger.info(f"  - {sub_cat}: {count} occurrences ({percentage:.2f}%)")
        
        # Log vehicle type distribution
        if 'vehicle_types' in fault_analysis:
            logger.info("\nVehicle Type Distribution:")
            total_by_type = sum(fault_analysis['vehicle_types'].values())
            for vehicle_type, count in fault_analysis['vehicle_types'].items():
                percentage = (count / total_by_type) * 100
                logger.info(f"{vehicle_type}: {count} occurrences ({percentage:.2f}%)")
        
        # Get top faults
        top_main = vehicle_faults.get_top_faults(limit=5, by_subcategory=False)
        top_sub = vehicle_faults.get_top_faults(limit=5, by_subcategory=True)
        
        # Log top faults
        logger.info("\nTop 5 Main Categories:")
        logger.info("-" * 50)
        if isinstance(top_main, dict) and 'value' in top_main:
            for category in top_main['value']:
                logger.info(f"- {category}")
        
        logger.info("\nTop 5 Sub-Categories:")
        logger.info("-" * 50)
        if isinstance(top_sub, dict) and 'value' in top_sub:
            for category in top_sub['value']:
                logger.info(f"- {category}")
        
        # Log summary statistics
        total_main_categories = len(fault_analysis.get('main_categories', {}))
        total_sub_categories = sum(len(sub_cats) for sub_cats in fault_analysis.get('sub_categories', {}).values())
        total_faults = sum(fault_analysis.get('main_categories', {}).values())
        
        logger.info("\nSummary Statistics:")
        logger.info("-" * 50)
        logger.info(f"Total Main Categories: {total_main_categories}")
        logger.info(f"Total Sub-Categories: {total_sub_categories}")
        logger.info(f"Total Faults: {total_faults}")
        if total_main_categories > 0:
            logger.info(f"Average Faults per Main Category: {total_faults/total_main_categories:.2f}")
        if total_sub_categories > 0:
            logger.info(f"Average Faults per Sub-Category: {total_faults/total_sub_categories:.2f}")
        
        logger.info("\n=== Fault Categories Analysis Test Completed Successfully ===")
        
    except Exception as e:
        logger.error(f"Error during fault categories analysis: {str(e)}")
        raise

if __name__ == "__main__":
    pytest.main([__file__])
