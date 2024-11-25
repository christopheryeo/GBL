"""
PandasChat module for handling chat-based queries on DataFrame using PandasAI.
Provides functionality for querying data using natural language and specialized fault analysis.
Author: Chris Yeo
"""

import os
import pandas as pd
import numpy as np
import re
from datetime import datetime
from pandasai.llm.openai import OpenAI
from pandasai import SmartDataframe
from VehicleFaults import VehicleFault

class PandasChat:
    def __init__(self, log_manager):
        """Initialize PandasChat with a log manager."""
        self.log_manager = log_manager
        self.llm = OpenAI(api_token=os.getenv('OPENAI_API_KEY'))

    def prepare_dataframe(self, df_data):
        """Prepare the DataFrame by converting date columns and handling data types."""
        # Convert list to DataFrame if necessary
        if isinstance(df_data, list):
            df_data = pd.DataFrame(df_data)
            
        # Convert date columns to datetime
        date_columns = ['Open Date', 'Done Date', 'Actual Finish Date']
        for col in date_columns:
            if col in df_data.columns:
                try:
                    df_data[col] = pd.to_datetime(df_data[col], errors='coerce')
                except Exception as e:
                    self.log_manager.log(f"Error converting {col} to datetime: {str(e)}")
                    df_data[col] = pd.NaT
        
        # Handle numeric columns safely
        numeric_columns = ['Mileage', 'Intercoamt', 'Custamt']
        for col in numeric_columns:
            if col in df_data.columns:
                try:
                    df_data[col] = pd.to_numeric(df_data[col].astype(str).str.replace(',', ''), errors='coerce')
                except Exception as e:
                    self.log_manager.log(f"Error converting {col} to numeric: {str(e)}")
                    df_data[col] = np.nan
        
        # Create VehicleFault DataFrame with validation disabled for flexibility
        return VehicleFault(df_data, validate_columns=False)

    def _preprocess_query(self, query):
        """Preprocess query to standardize terminology."""
        replacements = {
            "Faults": "Fault Categories",
            "faults": "fault categories",
            "Fault Details": "Fault Sub-Categories",
            "fault details": "fault sub-categories"
        }
        
        processed_query = query
        for old, new in replacements.items():
            processed_query = processed_query.replace(old, new)
        return processed_query

    def handle_year_query(self, df, year):
        """Handle queries about work orders in a specific year."""
        try:
            # Convert year to string for comparison
            year_str = str(year)
            
            # List of possible date columns
            date_columns = ['Open Date', 'Done Date', 'Actual Finish Date']
            
            # Initialize result DataFrame
            result = pd.DataFrame()
            
            for col in date_columns:
                if col in df.columns:
                    try:
                        # Convert column to datetime if not already
                        if not pd.api.types.is_datetime64_any_dtype(df[col]):
                            df[col] = pd.to_datetime(df[col], errors='coerce')
                        
                        # Filter by year
                        mask = df[col].dt.year == int(year_str)
                        if result.empty:
                            result = df[mask].copy()
                        else:
                            result = pd.concat([result, df[mask]]).drop_duplicates()
                    except Exception as e:
                        self.log_manager.log(f"Error processing date column {col}: {str(e)}")
                        continue
            
            if result.empty:
                return f"No work orders found for the year {year_str}"
            
            # Sort by date
            if 'Open Date' in result.columns:
                result = result.sort_values('Open Date')
            
            return result
            
        except Exception as e:
            error_msg = f"Error processing year query: {str(e)}"
            self.log_manager.log(error_msg)
            return error_msg

    def _extract_year(self, query):
        """Extract year from query text."""
        try:
            # Look for 4-digit year
            match = re.search(r'\b(19|20)\d{2}\b', query)
            if match:
                return match.group(0)
            
            # Look for year keywords
            year_words = {
                'this year': datetime.now().year,
                'last year': datetime.now().year - 1,
                'previous year': datetime.now().year - 1,
                'next year': datetime.now().year + 1
            }
            
            for phrase, year in year_words.items():
                if phrase in query.lower():
                    return str(year)
            
            return None
            
        except Exception as e:
            self.log_manager.log(f"Error extracting year: {str(e)}")
            return None

    def _extract_top_n(self, query):
        """Extract the number X from 'top X' queries."""
        try:
            # Look for patterns like "top 5", "top five", etc.
            number_words = {
                'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
                'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
            }
            
            # Try to match "top X" where X is a number
            match = re.search(r'top\s+(\d+)', query.lower())
            if match:
                return int(match.group(1))
            
            # Try to match "top X" where X is a word
            for word, num in number_words.items():
                if f'top {word}' in query.lower():
                    return num
            
            # Default to 3 if no number found
            return 3
            
        except Exception as e:
            self.log_manager.log(f"Error extracting top N: {str(e)}")
            return 3

    def handle_category_query(self, df, query):
        """Handle queries related to fault categories."""
        try:
            # Preprocess query to standardize terminology
            query = self._preprocess_query(query)
            
            if 'FaultMainCategory' not in df.columns or 'FaultSubCategory' not in df.columns:
                return "Fault categories are not available in the data."
            
            # Create a copy to prevent modifying original
            df = df.copy()
            
            # Determine if we're looking for main or sub categories
            is_sub_category = 'sub' in query.lower()
            category_col = 'FaultSubCategory' if is_sub_category else 'FaultMainCategory'
            category_type = "sub-categories" if is_sub_category else "main categories"
            
            # Get category counts and sort by frequency
            category_counts = df[category_col].value_counts()
            total = len(df)
            
            # Format the response
            response_lines = [f'Distribution of fault {category_type}:']
            
            # Add total count
            response_lines.append(f"\nTotal faults: {total}\n")
            
            # Add category breakdown
            for category, count in category_counts.items():
                if pd.notna(category) and category != '':  # Skip empty categories
                    percentage = (count / total) * 100
                    response_lines.append(f"- {category}: {count} faults ({percentage:.1f}%)")
                    
                    # For main categories, add sample faults
                    if not is_sub_category and len(response_lines) < 20:  # Limit to prevent too much output
                        samples = df[df[category_col] == category].head(2)
                        if not samples.empty:
                            response_lines.append("  Sample issues:")
                            for _, row in samples.iterrows():
                                complaint = str(row.get('Nature of Complaint', 'N/A'))[:100]  # Truncate long descriptions
                                response_lines.append(f"  * {complaint}")
            
            return '\n'.join(response_lines)
            
        except Exception as e:
            self.log_manager.log(f"Error processing category query: {str(e)}")
            return f"Error processing category query: {str(e)}"

    def handle_top_query(self, df, query):
        """Handle queries about top fault categories."""
        try:
            # Extract the number of top items to return
            limit = self._extract_top_n(query)
            
            # Determine if we should look at subcategories
            by_subcategory = any(term in query.lower() for term in 
                               ['sub', 'subcategory', 'subcategories', 'specific', 'detail'])
            
            # Get top faults
            results = df.get_top_faults(limit=limit, by_subcategory=by_subcategory)
            
            # Format the response
            if by_subcategory and 'top_subcategories' in results:
                response = [f"Here are the top {limit} fault sub-categories:"]
                for item in results['top_subcategories']:
                    response.append(
                        f"- {item['subcategory']} (under {item['main_category']}): "
                        f"{item['count']} occurrences ({item['percentage']}%)"
                    )
            elif 'top_categories' in results:
                response = [f"Here are the top {limit} fault categories:"]
                for item in results['top_categories']:
                    response.append(
                        f"- {item['category']}: {item['count']} occurrences ({item['percentage']}%)"
                    )
                    if item['subcategories']:
                        response.append("  Breakdown:")
                        for sub in item['subcategories']:
                            response.append(
                                f"  * {sub['name']}: {sub['count']} ({sub['percentage']}%)"
                            )
            
            return '\n'.join(response)
            
        except Exception as e:
            error_msg = f"Error processing top faults query: {str(e)}"
            self.log_manager.log(error_msg)
            return error_msg

    def handle_list_query(self, df, query):
        """Handle queries about listing fault categories or subcategories."""
        try:
            # Determine if we want categories or subcategories
            want_subcategories = any(term in query.lower() for term in 
                                   ['sub', 'subcategory', 'subcategories', 'specific', 'detail'])
            
            if want_subcategories:
                # Get subcategories
                results = df.get_top_faults(by_subcategory=True)
                if 'top_subcategories' in results:
                    response = ["Here are all fault sub-categories:"]
                    for item in results['top_subcategories']:
                        response.append(
                            f"- {item['subcategory']} (under {item['main_category']}): "
                            f"{item['count']} occurrences ({item['percentage']}%)"
                        )
                    return '\n'.join(response)
            else:
                # Get main categories
                results = df.get_top_faults()
                if 'top_categories' in results:
                    response = ["Here are all fault categories:"]
                    for item in results['top_categories']:
                        response.append(
                            f"- {item['category']}: {item['count']} occurrences ({item['percentage']}%)"
                        )
                        if item['subcategories']:
                            response.append("  Breakdown:")
                            for sub in item['subcategories']:
                                response.append(
                                    f"  * {sub['name']}: {sub['count']} ({sub['percentage']}%)"
                                )
                    return '\n'.join(response)
            
            return "No fault categories found"
            
        except Exception as e:
            error_msg = f"Error processing list query: {str(e)}"
            self.log_manager.log(error_msg)
            return error_msg

    def query(self, data, query):
        """Query the data using natural language."""
        try:
            # Preprocess query to standardize terminology
            query = self._preprocess_query(query)
            
            # Check for specific query types
            if any(term in query.lower() for term in ['top', 'most common', 'highest']):
                return self.handle_top_query(data, query)
            elif any(term in query.lower() for term in ['list', 'show all', 'what are the']):
                return self.handle_list_query(data, query)
            elif 'year' in query.lower() or any(str(year) in query for year in range(2000, 2025)):
                year = self._extract_year(query)
                if year:
                    return self.handle_year_query(data, year)
            
            # Prepare the data for querying
            prepared_data = self.prepare_dataframe(data)
            
            # Create a new PandasAI instance with error handling
            try:
                pandas_ai = SmartDataframe(prepared_data, config={
                    'llm': self.llm,
                    'custom_methods': [
                        prepared_data.filter_records,
                        prepared_data.get_filtered_count,
                        prepared_data.get_active_faults,
                        prepared_data.get_vehicle_history,
                        prepared_data.get_faults_by_category,
                        prepared_data._categorize_faults,
                        prepared_data.get_fault_statistics
                    ],
                    'enable_cache': True,
                    'max_retries': 3,
                    'enforce_privacy': False,
                    'save_charts': False,
                    'save_charts_path': None
                })
            except Exception as e:
                self.log_manager.log(f"Error creating SmartDataframe: {str(e)}")
                return f"Error initializing query engine: {str(e)}"

            # Log the query
            self.log_manager.log(f"CHAT_QUERY: {query}")
            
            try:
                # Run the query
                response = str(pandas_ai.chat(query))
                
                # Log the response
                self.log_manager.log(f"CHAT_QUERY: {query} | RESPONSE: {response}")
                
                # If response is empty or just whitespace, return a helpful message
                if not response or response.isspace():
                    return "I apologize, but I couldn't find any relevant information for your query."
                
                return response
                
            except Exception as e:
                error_msg = f"I apologize, but I couldn't process your query: {str(e)}"
                self.log_manager.log(f"CHAT_QUERY: {query} | ERROR: {error_msg}")
                return error_msg
                
        except Exception as e:
            error_msg = f"Error preparing data for query: {str(e)}"
            self.log_manager.log(error_msg)
            return error_msg
