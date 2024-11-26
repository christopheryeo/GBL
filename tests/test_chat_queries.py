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
from ExcelProcessor import ExcelProcessor
import pandas as pd

def load_kardex_data():
    """Load the Kardex Excel file and process it."""
    logger = LogManager(log_file='chat_queries.log')
    excel_processor = ExcelProcessor(logger)
    
    # Use the specific Kardex file
    kardex_file = Path(__file__).parent.parent / 'uploads' / 'Kardex for Lifestyle Van v2.xlsx'
    
    if not kardex_file.exists():
        raise FileNotFoundError(f"Kardex Excel file not found at {kardex_file}")
    
    # Process the Excel file
    kardex_path = str(kardex_file)
    kardex_name = kardex_file.name
    result = excel_processor.process_excel(kardex_path, kardex_name)
    
    # Convert the processed data to DataFrame
    if isinstance(result, dict) and 'data' in result:
        df = result['data']
        if not isinstance(df, pd.DataFrame):
            df = pd.DataFrame(df)
    else:
        df = pd.DataFrame(result)
    
    # Create VehicleFault object with the processed data
    vehicle_faults = VehicleFault(df)
    return vehicle_faults

def preprocess_complex_query(query):
    """Preprocess complex queries to make them more specific to our dataset."""
    # Normalize query
    query = query.lower().strip()
    
    # Handle vehicle-specific queries
    if "fiat doblo" in query:
        return query.replace("fiat doblo", "all vehicles")
    
    # Handle time-based queries
    time_patterns = {
        r"\d+(?:st|nd|rd|th)\s+year": lambda x: f"year {x.split()[0][0]}",
        "last year": "year 6",
        "first year": "year 1",
        "this year": "year 6",
        "current year": "year 6"
    }
    
    for pattern, replacement in time_patterns.items():
        if isinstance(replacement, str) and pattern in query:
            query = query.replace(pattern, replacement)
        elif callable(replacement) and any(p in query for p in [pattern]):
            import re
            match = re.search(pattern, query)
            if match:
                query = query.replace(match.group(), replacement(match.group()))
    
    # Handle comparative queries
    if "compare" in query:
        if "vehicle" in query or "type" in query:
            return "What are the fault distributions across different vehicle types?"
        if "year" in query:
            return "What are the fault trends across different years?"
    
    # Handle trend analysis queries
    if "trend" in query or "pattern" in query:
        if "maintenance" in query:
            return "What are the maintenance patterns over time?"
        if "fault" in query or "breakdown" in query:
            return "What are the fault occurrence patterns over time?"
    
    # Handle statistical queries
    if "average" in query or "mean" in query:
        if "visit" in query:
            return "What is the average number of maintenance visits per year?"
        if "fault" in query or "breakdown" in query:
            return "What is the average number of faults per vehicle type?"
    
    # Handle vehicle type queries
    if "vehicle type" in query or "which type" in query:
        if "maintenance" in query or "issue" in query:
            return "Which vehicle category has the highest number of maintenance records?"
        if "reliable" in query or "best" in query:
            return "Which vehicle type has the lowest fault rate?"
    
    return query

def test_chat_queries():
    """Test chat queries with improved preprocessing and response enhancement."""
    try:
        # Load the Kardex data
        vehicle_faults = load_kardex_data()
        
        # Initialize logger and PandasChat
        logger = LogManager(log_file='chat_queries.log')
        pandas_chat = PandasChat(vehicle_faults._df, logger)
        
        # Load test questions from file
        questions_file = Path(__file__).parent / 'test_questions.txt'
        if not questions_file.exists():
            raise FileNotFoundError(f"Test questions file not found at {questions_file}")
        
        # Read questions and track sections
        client_questions = []
        current_section = None
        
        with open(questions_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                    
                if line.startswith('#'):
                    current_section = line[1:].strip().lower()
                    continue
                    
                if current_section == 'client questions':
                    client_questions.append(line)
        
        logger.log(f"Found {len(client_questions)} client questions")
        
        # Process each client question
        for question in client_questions:
            try:
                logger.log(f"\nProcessing question: {question}")
                
                # Preprocess the question
                processed_question = preprocess_complex_query(question)
                logger.log(f"Preprocessed question: {processed_question}")
                
                # Get response using chat method
                response = pandas_chat.chat(processed_question)
                
                # Print results
                print(f"\nOriginal Question: {question}")
                print(f"Processed Question: {processed_question}")
                print(f"Response: {response}")
                print("-" * 80)
                
            except Exception as e:
                error_msg = f"Error processing question '{question}': {str(e)}"
                logger.log(error_msg, level="ERROR")
                print(error_msg)
                
    except Exception as e:
        print(f"Error in test_chat_queries: {str(e)}")
        raise

if __name__ == '__main__':
    test_chat_queries()
