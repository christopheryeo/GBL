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
from FileRead import FileReader
from config.TestConfig import TestConfig
import pandas as pd
import re

def clear_log_file(log_file_path: str):
    """Clear the log file and write a header."""
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
    with open(log_file_path, 'w') as f:
        f.write(f"=== Log Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")

def load_kardex_data():
    """Load the Kardex Excel file and process it."""
    try:
        # Initialize logger with test-specific configuration
        logger = TestConfig().get_logger('test_chat_queries')
        logger.info("\n=== Starting Chat Queries Test Data Loading ===")
        
        # Initialize FileReader
        file_reader = FileReader(logger)
        
        # Use the default Kardex file from configuration
        kardex_file = TestConfig().get_kardex_path()  # Uses default from test_config.yaml
        if not os.path.exists(kardex_file):
            raise FileNotFoundError(f"Kardex Excel file not found at {kardex_file}")
        
        logger.info(f"Loading default Kardex file: {kardex_file}")
        
        # Load data using FileReader
        df, vehicle_type, status = file_reader.load_kardex_data(kardex_file)
        
        if not status['success']:
            raise ValueError(f"Failed to load Kardex data: {status['message']}")
        
        # Validate required columns from format configuration
        default_key = TestConfig().get_default_kardex()
        format_config = TestConfig().get_excel_format(default_key)
        required_columns = [col['name'] for col in format_config['format']['columns'] 
                          if col['required']]
        
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Required column {col} missing from Kardex data")
        
        logger.info(f"Successfully loaded {len(df)} records")
        logger.info(f"Vehicle Type: {vehicle_type}")
        logger.info(f"Columns: {df.columns.tolist()}")
        
        # Create VehicleFault object with validated data
        vehicle_faults = VehicleFault(data=df)
        
        # Verify fault categorization
        stats = vehicle_faults.get_fault_statistics()
        if stats:
            main_categories = len(stats.get('main_categories', {}))
            sub_categories = sum(len(sub_cats) for sub_cats in stats.get('sub_categories', {}).values())
            logger.info(f"Detected {main_categories} main categories and {sub_categories} sub-categories")
        
        logger.info("=== Chat Queries Test Data Loading Completed Successfully ===\n")
        return vehicle_faults
        
    except Exception as e:
        logger.error(f"Error loading Kardex data: {str(e)}")
        raise

def preprocess_complex_query(query):
    """
    Preprocess complex queries to make them more specific to our dataset.
    
    Args:
        query (str): The original query
        
    Returns:
        str: The preprocessed query
    """
    # Convert to lowercase for consistent processing
    query = query.lower()
    
    # Replace common terms with more specific ones
    replacements = {
        'problems': 'faults',
        'issues': 'faults',
        'vehicles': 'lifestyle vans',
        'cars': 'lifestyle vans',
        'vans': 'lifestyle vans',
        'common': 'frequent',
        'often': 'frequent',
        'usually': 'frequent',
        'typically': 'frequent',
        'mostly': 'frequent',
        'mainly': 'frequent',
        'generally': 'frequent',
        'primarily': 'frequent',
        'predominantly': 'frequent',
        'regularly': 'frequent'
    }
    
    for old, new in replacements.items():
        # Use word boundaries to avoid partial replacements
        query = re.sub(rf'\b{old}\b', new, query)
    
    # Add specific context if query is too general
    if 'fault' in query and 'category' not in query and 'type' not in query:
        query += ' by category'
    
    if 'frequent' in query and 'most' not in query:
        query = 'most ' + query
    
    return query

def load_test_questions():
    """
    Load test questions from file based on configuration.
    
    Returns:
        list: List of test questions from configured section
    """
    # Get configuration
    test_config = TestConfig()
    test_questions_config = test_config._config['test_questions']
    test_specific_config = test_questions_config.get('test_chat_queries', {})
    
    # Get file path - use test-specific file if specified, otherwise use default
    questions_file = Path(test_specific_config.get('file', test_questions_config['default_file']))
    target_section = test_specific_config.get('section')
    
    if not questions_file.exists():
        raise FileNotFoundError(f"Test questions file not found at {questions_file}")
    
    if not target_section:
        raise ValueError("No target section specified in configuration")
    
    questions = []
    current_section = None
    
    with open(questions_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
                
            # Check if line is a section header
            if line.startswith('#'):
                current_section = line[1:].strip()
                continue
            
            # Add question if it's in the target section
            if current_section == target_section:
                questions.append(line)
    
    if not questions:
        raise ValueError(f"No questions found in section '{target_section}'")
    
    return questions

def enhance_response(response):
    """
    Enhance the response format for better readability.
    
    Args:
        response: The raw response from PandasChat
        
    Returns:
        str: Enhanced response string
    """
    if isinstance(response, dict):
        if 'value' in response:
            value = response['value']
            if isinstance(value, dict):
                # Handle fault statistics
                if 'main_categories' in value:
                    result = "Fault Category Distribution:\n"
                    total = sum(value['main_categories'].values())
                    for category, count in value['main_categories'].items():
                        percentage = (count / total) * 100
                        result += f"- {category}: {count} occurrences ({percentage:.2f}%)\n"
                    return result
                
                # Handle top faults
                if 'top_items' in value:
                    result = "Top Faults:\n"
                    for i, item in enumerate(value['top_items'], 1):
                        if isinstance(item, dict):
                            if 'category' in item:
                                result += f"{i}. {item['category']}: {item['count']} occurrences ({item['percentage']}%)\n"
                            else:
                                result += f"{i}. {item['subcategory']}: {item['count']} occurrences ({item['percentage']}%)\n"
                        else:
                            result += f"{i}. {item}\n"
                    return result
            
            # Handle simple value types
            return str(value)
        
        # Handle other dictionary responses
        return "\n".join(f"{k}: {v}" for k, v in response.items())
    
    return str(response)

def test_chat_queries():
    """Test chat queries with improved preprocessing and response enhancement."""
    try:
        # Get log file path from config
        log_config = TestConfig()._config.get('logging', {}).get('test_chat_queries', {})
        log_file = log_config.get('log_file')
        
        # Clear log file if it exists
        if log_file:
            clear_log_file(log_file)
        
        # Initialize components
        test_config = TestConfig()
        logger = test_config.get_logger('test_chat_queries')  # Use the logging config key directly
        logger.info("\n=== Starting Chat Queries Test ===")
        
        # Load Kardex data
        vehicle_faults = load_kardex_data()
        
        # Initialize PandasChat with the loaded data
        chat = PandasChat(vehicle_faults)
        chat.log_manager = logger
        
        # Load test questions
        test_questions = load_test_questions()
        logger.info(f"Loaded {len(test_questions)} test questions")
        
        # Process each test question
        for i, question in enumerate(test_questions, 1):
            logger.info(f"\n[Question {i}]: {question}")
            
            # Preprocess the question
            processed_question = preprocess_complex_query(question)
            if processed_question != question:
                logger.info(f"Preprocessed to: {processed_question}")
            
            try:
                # Use chat_query method instead of get_response
                response = chat.chat_query(processed_question, vehicle_faults)
                if response:
                    logger.info(f"Response to question {i}: {response}")
                else:
                    logger.info(f"No response for question {i}")
            except Exception as e:
                logger.error(f"Error processing question {i}: {str(e)}")
                continue
        
        logger.info("\n=== Chat Queries Test Completed Successfully ===")
        
    except Exception as e:
        logger.error(f"Error during chat queries test: {str(e)}")
        raise

if __name__ == '__main__':
    test_chat_queries()
