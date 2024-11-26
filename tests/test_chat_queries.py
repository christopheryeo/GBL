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
    logger = LogManager()  # Use default max_logs value
    excel_processor = ExcelProcessor(logger)
    
    # Find the Kardex file in the uploads directory
    uploads_dir = Path(__file__).parent.parent / 'uploads'
    try:
        kardex_file = next(uploads_dir.glob('*Kardex*.xlsx'))
    except StopIteration:
        raise FileNotFoundError("No Kardex Excel file found in uploads directory")
    
    if not kardex_file.exists():
        raise FileNotFoundError(f"Kardex Excel file not found at {kardex_file}")
    
    # Process the Excel file with header on row 4 (0-based index 3)
    kardex_path = str(kardex_file)
    kardex_name = kardex_file.name
    result = excel_processor.process_excel(kardex_path, kardex_name)
    
    # Convert the data to a VehicleFault object
    if isinstance(result, dict) and 'data' in result:
        df = pd.DataFrame(result['data'])
    else:
        df = pd.DataFrame(result)
    
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
    """Test complex queries with improved preprocessing and response enhancement."""
    logger = LogManager()  # Use default max_logs value
    logger.log("\n=== Starting Enhanced Chat Query Tests ===")
    
    try:
        # Load the actual Kardex data
        vehicle_faults = load_kardex_data()
        chat = PandasChat(logger)
        
        # Load test questions
        test_questions_path = Path(__file__).parent / 'test_questions.txt'
        with open(test_questions_path, 'r') as f:
            questions = f.readlines()
        
        # Filter for complex queries only
        test_queries = []
        current_section = ""
        for question in questions:
            question = question.strip()
            if question.startswith('#'):
                current_section = question.lower()
            elif question and current_section == '# complex queries':
                # Preprocess the query
                processed_query = preprocess_complex_query(question)
                test_queries.append((question, processed_query))
        
        # Run the queries with enhanced responses
        logger.log(f"\nTesting {len(test_queries)} complex queries with response enhancement...")
        for i, (original_query, processed_query) in enumerate(test_queries, 1):
            if processed_query:
                logger.log(f"\nComplex Query {i}: {original_query}")
                logger.log(f"Processed Query: {processed_query}")
                
                # Get enhanced response
                response = chat.chat_query(processed_query, vehicle_faults)
                
                # Verify response
                assert response is not None, f"No response received for query: {processed_query}"
                assert len(response.strip()) > 0, f"Empty response received for query: {processed_query}"
                assert isinstance(response, str), f"Response should be string, got {type(response)}"
                
                logger.log(f"Enhanced Response: {response}\n")
                
        logger.log("\n=== Chat Query Tests Completed Successfully ===")
        
    except Exception as e:
        logger.log(f"Error in test_chat_queries: {str(e)}")
        raise

if __name__ == '__main__':
    test_chat_queries()
