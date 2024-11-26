import os
import sys
import pandas as pd
from datetime import datetime
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from VehicleFaults import VehicleFault
from FileRead import FileReader
from config.TestConfig import test_config
from PandasChat import PandasChat

def clear_log_file(log_file_path: str):
    """Clear the log file and write a header."""
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
    with open(log_file_path, 'w') as f:
        f.write(f"=== Log Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")

def test_specific_query():
    """Test specific query for vehicle faults using configured default query."""
    # Get log file path from config
    log_config = test_config._config.get('logging', {}).get('test_specific_query', {})
    log_file = log_config.get('log_file')
    
    # Clear log file if it exists
    if log_file:
        clear_log_file(log_file)
    
    # Initialize logging
    logger = test_config.get_logger('test_specific_query')
    logger.info("\n=== Application Started ===")
    
    try:
        # Initialize FileReader with logger
        file_reader = FileReader(logger)
        
        # Load Kardex data with vehicle type
        kardex_file = test_config.get_kardex_path('kardex_lifestyle')
        df, vehicle_type, status = file_reader.load_kardex_data(kardex_file)
        
        if not status['success']:
            logger.error(f"Failed to load data: {status['message']}")
            assert False, f"Failed to load data: {status['message']}"
        
        logger.info(f"Successfully loaded {len(df)} records")
        logger.info(f"Vehicle Type: {vehicle_type}")
        
        # Create VehicleFault instance
        vehicle_faults = VehicleFault(data=df)
        
        # Initialize PandasChat for natural language querying
        pandas_chat = PandasChat(logger)
        
        # Get the default query from config
        default_query = test_config.get_test_question_config('test_specific_query').get('default_query')
        logger.info(f"\nExecuting query: {default_query}")
        
        # Process the query
        response = pandas_chat.query(vehicle_faults, default_query)
        
        # Log and verify results
        logger.info("\nQuery Results:")
        logger.info("-" * 50)
        
        assert response is not None, "Query response should not be None"
        
        if isinstance(response, dict) and 'type' in response and 'value' in response:
            if response['type'] == 'number':
                logger.info(f"Found {response['value']} battery breakdowns for the Fiat Doblo")
                assert isinstance(response['value'], (int, float)), "Response value should be a number"
            else:
                logger.info(response['value'])
                assert isinstance(response['value'], str), "Response value should be a string"
        else:
            logger.info(response)
            assert isinstance(response, (str, dict)), "Response should be either a string or a dictionary"
        
        logger.info("\n=== Application Completed Successfully ===")
        
    except Exception as e:
        logger.error(f"Error during execution: {str(e)}")
        raise
