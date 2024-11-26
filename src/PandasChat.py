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
from pandasai.smart_dataframe import SmartDataframe
from VehicleFaults import VehicleFault
from pathlib import Path
from ResponseProcessor import ResponseProcessor
from QueryPreProcessor import QueryPreProcessor
import calendar

class PandasChat:
    """A class to handle chat-based interactions with pandas DataFrames."""
    
    def __init__(self, df_data=None, log_manager=None):
        """Initialize PandasChat with optional DataFrame."""
        self.log_manager = log_manager
        
        # Handle the case where df_data is actually a log_manager
        if hasattr(df_data, 'log') and callable(df_data.log):
            self.log_manager = df_data
            df_data = None
            
        self.df = self.prepare_dataframe(df_data)
        self.llm = OpenAI(api_token=os.getenv('OPENAI_API_KEY'))
        self.response_processor = ResponseProcessor(self.log_manager)
        self.query_preprocessor = QueryPreProcessor()
        
        # Configure SmartDataframe with custom settings
        if self.df is not None:
            self.smart_df = SmartDataframe(
                self.df,
                config={
                    "llm": self.llm,
                    "enable_cache": True,
                    "custom_whitelisted_dependencies": ["dateutil"],
                    "custom_prompts": {
                        "system": """You are a vehicle maintenance analyst. Analyze the maintenance records and provide insights about:
                        1. Fault patterns and trends
                        2. Maintenance frequencies
                        3. Vehicle type specific issues
                        4. Seasonal patterns if applicable
                        
                        The data contains vehicle maintenance records with columns for dates, fault categories, vehicle types, and other relevant information.
                        
                        When analyzing the data:
                        1. Always group by relevant categories (Vehicle Type, Fault Category, etc.)
                        2. Provide specific numbers and percentages
                        3. Consider temporal patterns if relevant
                        4. Highlight any significant findings or anomalies
                        5. Format responses clearly with proper units and context"""
                    }
                }
            )

    def prepare_dataframe(self, df_data):
        """Prepare the DataFrame for analysis."""
        try:
            if isinstance(df_data, pd.DataFrame):
                # Convert date columns to datetime if they exist
                date_columns = ['Open Date', 'Completion Date', 'Last Update']
                for col in date_columns:
                    if col in df_data.columns:
                        df_data[col] = pd.to_datetime(df_data[col], errors='coerce')
                
                # Ensure Vehicle Type column exists
                if 'Vehicle Type' not in df_data.columns:
                    self.log_manager.log("Warning: Vehicle Type column not found in data")
                
                return df_data
            elif isinstance(df_data, VehicleFault):
                return df_data._df if hasattr(df_data, '_df') else df_data
            elif df_data is None:
                self.log_manager.log("No DataFrame provided")
                return pd.DataFrame()  # Return empty DataFrame instead of None
            else:
                self.log_manager.log(f"Invalid data type for DataFrame preparation: {type(df_data)}")
                return pd.DataFrame()  # Return empty DataFrame instead of None
        except Exception as e:
            self.log_manager.log(f"Error preparing DataFrame: {str(e)}")
            return pd.DataFrame()  # Return empty DataFrame instead of None

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

    def process_dataframe_response(self, raw_response, query):
        """Process DataFrame responses into meaningful text."""
        try:
            if isinstance(raw_response, str):
                return raw_response
                
            # Handle NaN responses
            if pd.isna(raw_response) or (isinstance(raw_response, dict) and raw_response.get('type') == 'number' and pd.isna(raw_response.get('value'))):
                # Calculate average faults directly
                if "average" in query.lower() and "fault" in query.lower():
                    df = self.df
                    if df is None or df.empty or 'Vehicle Type' not in df.columns:
                        return "Vehicle Type information is not available in the data."
                    
                    fault_counts = df.groupby('Vehicle Type').size().reset_index(name='count')
                    avg_faults = fault_counts['count'].mean()
                    result = f"The average number of faults per vehicle type is {avg_faults:.1f}.\n\nBreakdown by vehicle type:\n"
                    for _, row in fault_counts.iterrows():
                        result += f"- {row['Vehicle Type']}: {row['count']} faults\n"
                    return result
                return "No data available for this query."
                
            # Handle DataFrame responses
            df = None
            if isinstance(raw_response, pd.DataFrame):
                df = raw_response
            elif isinstance(raw_response, dict) and raw_response.get('type') == 'dataframe':
                df = raw_response['value']
            elif hasattr(raw_response, 'to_string'):
                df = raw_response
                
            if df is None:
                return str(raw_response)
                
            # Special handling for month-based queries
            if "month" in query.lower() and "highest" in query.lower():
                if isinstance(df, pd.DataFrame) and 'Fault Count' in df.columns and 'Month' in df.columns:
                    max_count = df['Fault Count'].max()
                    highest_months = df[df['Fault Count'] == max_count].copy()
                    month_counts = []
                    
                    for _, row in highest_months.iterrows():
                        try:
                            month_val = row['Month']
                            if isinstance(month_val, pd._libs.tslibs.period.Period):
                                month_str = f"{calendar.month_name[month_val.month]} {month_val.year}"
                            elif pd.isna(month_val):
                                continue
                            elif isinstance(month_val, str) and '-' in month_val:
                                year, month = month_val.split('-')
                                month_name = calendar.month_name[int(month)]
                                month_str = f"{month_name} {year}"
                            else:
                                month_str = str(month_val)
                            month_counts.append(month_str)
                        except (ValueError, AttributeError) as e:
                            self.log_manager.log(f"Error processing month value: {str(e)}")
                            continue
                    
                    if month_counts:
                        result = f"The months with the highest number of faults ({max_count} faults each) are:\n"
                        for month in sorted(month_counts):
                            result += f"- {month}\n"
                        return result
                    
            # Handle battery breakdown query
            if "battery" in query.lower() and "breakdown" in query.lower():
                if isinstance(df, pd.DataFrame) and 'Description' in df.columns:
                    battery_count = len(df[df['Description'].str.contains('battery', case=False, na=False)])
                    return f"There are {battery_count} battery-related breakdowns recorded."
            
            # Default handling
            if isinstance(df, pd.DataFrame):
                if len(df.columns) == 2 and 'Month' in df.columns and 'Fault Count' in df.columns:
                    result = "Monthly fault distribution:\n"
                    for _, row in df.sort_values('Month').iterrows():
                        result += f"- {row['Month']}: {row['Fault Count']} faults\n"
                    return result
                return df.to_string(index=False)
            return str(df)
            
        except Exception as e:
            self.log_manager.log(f"Error processing DataFrame response: {str(e)}")
            return str(raw_response)

    def chat_query(self, query, df_data):
        """Process a chat query and return the response."""
        try:
            # Log the query
            self.log_manager.log(f"Processed Query: {query}")
            self.log_manager.log(f"CHAT_QUERY: {query}")
            
            # Prepare the DataFrame
            vehicle_faults = self.prepare_dataframe(df_data)
            if vehicle_faults is None:
                return "No data available for analysis."
            
            # Get the underlying pandas DataFrame
            self.df = vehicle_faults._df if isinstance(vehicle_faults, VehicleFault) else vehicle_faults
            if self.df.empty:
                return "No data available for analysis."
            
            # Create SmartDataframe with the pandas DataFrame
            smart_df = SmartDataframe(self.df, config={
                "llm": self.llm,
                "enable_cache": True,
                "custom_whitelisted_dependencies": ["dateutil"],
                "custom_prompts": {
                    "system": """You are a vehicle maintenance analyst. Analyze the maintenance records and provide insights about:
                    1. Fault patterns and trends
                    2. Maintenance frequencies
                    3. Vehicle type specific issues
                    4. Seasonal patterns if applicable
                    
                    The data contains vehicle maintenance records with columns for dates, fault categories, vehicle types, and other relevant information.
                    
                    When analyzing the data:
                    1. Always group by relevant categories (Vehicle Type, Fault Category, etc.)
                    2. Provide specific numbers and percentages
                    3. Consider temporal patterns if relevant
                    4. Highlight any significant findings or anomalies
                    5. Format responses clearly with proper units and context"""
                }
            })
            
            # Get raw response from PandasAI
            raw_response = smart_df.chat(query)
            
            # Process the response
            processed_response = self.process_dataframe_response(raw_response, query)
            
            # Log raw response
            self.log_manager.log(f"CHAT_QUERY: {query} | RAW_RESPONSE: {processed_response}")
            
            # Enhance response using ResponseProcessor
            enhanced_response = self.response_processor.enhance_response(query, processed_response)
            
            # Log enhanced response
            self.log_manager.log(f"CHAT_QUERY: {query} | ENHANCED_RESPONSE: {enhanced_response}")
            
            return enhanced_response
            
        except Exception as e:
            error_msg = f"Error processing query: {str(e)}"
            self.log_manager.log(error_msg)
            return error_msg

    def chat(self, query: str) -> str:
        """Process a chat query and return a response."""
        try:
            if self.df is None or self.df.empty:
                return "No data available for analysis."
            
            # Preprocess the query for better results
            processed_query = self.query_preprocessor.preprocess(query)
            if self.log_manager:
                self.log_manager.log(f"Processed query: {processed_query}")
            
            # Configure SmartDataframe with appropriate prompts
            self.smart_df.config.update({
                "custom_prompts": {
                    "system": """You are a vehicle maintenance analyst. Analyze the maintenance records and provide insights about:
                    1. Fault patterns and trends
                    2. Maintenance frequencies
                    3. Vehicle type specific issues
                    4. Seasonal patterns if applicable
                    
                    The data contains vehicle maintenance records with columns for dates, fault categories, vehicle types, and other relevant information.
                    
                    When analyzing the data:
                    1. Always group by relevant categories (Vehicle Type, Fault Category, etc.)
                    2. Provide specific numbers and percentages
                    3. Consider temporal patterns if relevant
                    4. Highlight any significant findings or anomalies
                    5. Format responses clearly with proper units and context"""
                }
            })
            
            # Get response from PandasAI
            response = self.smart_df.chat(processed_query)
            
            # Process and format the response
            formatted_response = self.response_processor.process_response(response, query)
            
            return formatted_response
            
        except Exception as e:
            error_msg = f"Error processing query: {str(e)}"
            if self.log_manager:
                self.log_manager.log(error_msg, level="ERROR")
            return error_msg
