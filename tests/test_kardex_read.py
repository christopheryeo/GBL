import os
import sys
import pandas as pd
from datetime import datetime
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from FileRead import FileReader
from config.TestConfig import test_config

def clear_log_file(log_name: str):
    """Clear the log file and create a new one with a header."""
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f'{log_name}.log')
    
    with open(log_file, 'w') as f:
        f.write(f"=== {log_name.replace('_', ' ').title()} Log Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
        f.write("=" * 80 + "\n")

def test_kardex_file():
    """Test reading and processing of Kardex Excel files."""
    # Clear and initialize logging
    clear_log_file('kardex_read')
    logger = test_config.get_logger('test_kardex_read')
    logger.info("\n=== Starting Kardex File Read Test ===")
    
    try:
        # Initialize FileReader with logger
        file_reader = FileReader(logger)
        
        # Get the path to the default test file
        kardex_file = test_config.get_kardex_path()  # Uses default from test_config.yaml
        logger.info(f"Testing default Kardex file: {kardex_file}")
        
        # Load Kardex data using FileReader
        df, vehicle_type, status = file_reader.load_kardex_data(kardex_file)  # Will use default processor
        
        if status['success']:
            logger.info(f"Successfully loaded {len(df)} records")
            logger.info(f"Vehicle Type: {vehicle_type}")
            logger.info(f"Columns: {list(df.columns)}")
            
            # Basic data validation
            assert len(df) > 0, "DataFrame is empty"
            assert vehicle_type is not None, "Vehicle type not detected"
            assert 'Job Description' in df.columns, "Job Description column missing"
            
            # Get format configuration for the default Kardex
            default_key = test_config.get_default_kardex()
            format_config = test_config.get_excel_format(default_key)
            
            # Validate required columns from format configuration
            for col in format_config['format']['columns']:
                if col['required']:
                    assert col['name'] in df.columns, f"Required column {col['name']} missing"
                    if col['type'] == 'date':
                        assert pd.api.types.is_datetime64_any_dtype(df[col['name']]), f"{col['name']} not properly parsed as date"
            
            logger.info("All validation checks passed")
        else:
            logger.error(f"Failed to load data: {status['message']}")
            raise Exception(f"Failed to load data: {status['message']}")
        
        logger.info("=== Kardex File Read Test Completed Successfully ===\n")
        
    except Exception as e:
        logger.error(f"Error during Kardex file read test: {str(e)}")
        raise

if __name__ == '__main__':
    test_kardex_file()
