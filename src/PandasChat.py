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
        
    def prepare_dataframe(self, df_data):
        """Prepare the DataFrame for analysis."""
        try:
            if df_data is None:
                if self.log_manager:
                    self.log_manager.info("No data provided to prepare_dataframe")
                return None
                
            if isinstance(df_data, pd.DataFrame):
                if self.log_manager:
                    self.log_manager.info(f"Using provided DataFrame with shape: {df_data.shape}")
                return df_data
            elif hasattr(df_data, '_df') and isinstance(df_data._df, pd.DataFrame):
                if self.log_manager:
                    self.log_manager.info(f"Using DataFrame from VehicleFault object with shape: {df_data._df.shape}")
                return df_data._df
            else:
                if self.log_manager:
                    self.log_manager.info(f"Unsupported data type in prepare_dataframe: {type(df_data)}")
                return None
                
        except Exception as e:
            if self.log_manager:
                self.log_manager.error(f"Error in prepare_dataframe: {str(e)}")
            return None

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
                        if self.log_manager:
                            self.log_manager.error(f"Error processing date column {col}: {str(e)}")
                        continue
            
            if result.empty:
                return f"No work orders found for the year {year_str}"
            
            # Sort by date
            if 'Open Date' in result.columns:
                result = result.sort_values('Open Date')
            
            return result
            
        except Exception as e:
            error_msg = f"Error processing year query: {str(e)}"
            if self.log_manager:
                self.log_manager.error(error_msg)
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
            if self.log_manager:
                self.log_manager.error(f"Error extracting year: {str(e)}")
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
            if self.log_manager:
                self.log_manager.error(f"Error extracting top N: {str(e)}")
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
            if self.log_manager:
                self.log_manager.error(f"Error processing category query: {str(e)}")
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
            if self.log_manager:
                self.log_manager.error(error_msg)
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
            if self.log_manager:
                self.log_manager.error(error_msg)
            return error_msg

    def process_dataframe_response(self, raw_response, query):
        """Process DataFrame responses into meaningful text."""
        try:
            # Handle empty or None responses
            if raw_response is None:
                return "No data available for this query."
                
            # Handle DataFrame responses
            df = None
            if isinstance(raw_response, pd.DataFrame):
                if raw_response.empty:  # Use .empty for checking empty DataFrame
                    return "No data available for analysis."
                df = raw_response
            elif isinstance(raw_response, dict) and raw_response.get('type') == 'dataframe':
                df = raw_response['value']
                if df.empty:  # Check if the DataFrame is empty
                    return "No data available for analysis."
            elif hasattr(raw_response, 'to_string'):
                df = raw_response
                if hasattr(df, 'empty') and df.empty:  # Check empty for DataFrame-like objects
                    return "No data available for analysis."
                
            if df is None:
                return str(raw_response)
                
            # Special handling for month-based queries
            if "month" in query.lower() and "highest" in query.lower():
                if isinstance(df, pd.DataFrame) and 'Fault Count' in df.columns and 'Month' in df.columns:
                    max_count = df['Fault Count'].max()
                    matching_mask = (df['Fault Count'] == max_count)
                    
                    if not matching_mask.any():  # Check if we have any matching records
                        return "No fault count data available."
                        
                    highest_months = df[matching_mask].copy()
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
                            if self.log_manager:
                                self.log_manager.error(f"Error processing month value: {str(e)}")
                            continue
                    
                    if month_counts:
                        result = f"The months with the highest number of faults ({max_count} faults each) are:\n"
                        for month in sorted(month_counts):
                            result += f"- {month}\n"
                        return result
                    
            # Handle battery breakdown query
            if "battery" in query.lower() and "breakdown" in query.lower():
                if isinstance(df, pd.DataFrame) and 'Description' in df.columns:
                    battery_mask = df['Description'].str.contains('battery', case=False, na=False)
                    if not battery_mask.any():  # Check if we have any battery-related entries
                        return "No battery-related breakdowns found."
                    battery_count = battery_mask.sum()  # More efficient than len()
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
            if self.log_manager:
                self.log_manager.error(f"Error processing DataFrame response: {str(e)}")
            return str(raw_response)

    def chat_query(self, query, df_data):
        """Process a chat query and return the response."""
        try:
            if self.df is None:
                self.df = self.prepare_dataframe(df_data)
                
            if self.df is None:
                return "No data available for analysis."
                
            # Log the original query
            if self.log_manager:
                self.log_manager.info(f"CHAT_QUERY: {query}")
                self.log_manager.info(f"Using DataFrame from VehicleFault object with shape: {self.df.shape}")
            
            # Special handling for battery queries
            if 'battery' in query.lower() and ('breakdown' in query.lower() or 'how many' in query.lower()):
                if 'FaultMainCategory' in self.df.columns:
                    battery_faults = self.df[self.df['FaultMainCategory'] == 'Battery System']
                    count = len(battery_faults)
                    raw_response = str(count)
                    enhanced_response = f"The vehicle has experienced {count} battery-related issues throughout its lifespan."
                    
                    if self.log_manager:
                        self.log_manager.info(f"CHAT_QUERY: {query} | RAW_RESPONSE: {raw_response}")
                        self.log_manager.info(f"CHAT_QUERY: {query} | ENHANCED_RESPONSE: {enhanced_response}")
                        
                    return enhanced_response
            
            # Process other queries as normal
            df_ai = SmartDataframe(self.df, config={"llm": self.llm})
            raw_response = df_ai.chat(query)
            
            if self.log_manager:
                self.log_manager.info(f"CHAT_QUERY: {query} | RAW_RESPONSE: {raw_response}")
            
            # Process the response using the process_dataframe_response method
            processed_response = self.process_dataframe_response(raw_response, query)
            
            if self.log_manager:
                self.log_manager.info(f"CHAT_QUERY: {query} | ENHANCED_RESPONSE: {processed_response}")
            
            return processed_response
            
        except Exception as e:
            error_msg = f"Error processing chat query: {str(e)}"
            if self.log_manager:
                self.log_manager.error(error_msg)
            return error_msg

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
                        if self.log_manager:
                            self.log_manager.error(f"Error processing date column {col}: {str(e)}")
                        continue
            
            if result.empty:
                return f"No work orders found for the year {year_str}"
            
            # Sort by date
            if 'Open Date' in result.columns:
                result = result.sort_values('Open Date')
            
            return result
            
        except Exception as e:
            error_msg = f"Error processing year query: {str(e)}"
            if self.log_manager:
                self.log_manager.error(error_msg)
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
            if self.log_manager:
                self.log_manager.error(f"Error extracting year: {str(e)}")
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
            if self.log_manager:
                self.log_manager.error(f"Error extracting top N: {str(e)}")
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
            if self.log_manager:
                self.log_manager.error(f"Error processing category query: {str(e)}")
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
            if self.log_manager:
                self.log_manager.error(error_msg)
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
            if self.log_manager:
                self.log_manager.error(error_msg)
            return error_msg

    def process_dataframe_response(self, raw_response, query):
        """Process DataFrame responses into meaningful text."""
        try:
            # Handle empty or None responses
            if raw_response is None:
                return "No data available for this query."
                
            # Handle DataFrame responses
            df = None
            if isinstance(raw_response, pd.DataFrame):
                if raw_response.empty:  # Use .empty for checking empty DataFrame
                    return "No data available for analysis."
                df = raw_response
            elif isinstance(raw_response, dict) and raw_response.get('type') == 'dataframe':
                df = raw_response['value']
                if df.empty:  # Check if the DataFrame is empty
                    return "No data available for analysis."
            elif hasattr(raw_response, 'to_string'):
                df = raw_response
                if hasattr(df, 'empty') and df.empty:  # Check empty for DataFrame-like objects
                    return "No data available for analysis."
                
            if df is None:
                return str(raw_response)
                
            # Special handling for month-based queries
            if "month" in query.lower() and "highest" in query.lower():
                if isinstance(df, pd.DataFrame) and 'Fault Count' in df.columns and 'Month' in df.columns:
                    max_count = df['Fault Count'].max()
                    matching_mask = (df['Fault Count'] == max_count)
                    
                    if not matching_mask.any():  # Check if we have any matching records
                        return "No fault count data available."
                        
                    highest_months = df[matching_mask].copy()
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
                            if self.log_manager:
                                self.log_manager.error(f"Error processing month value: {str(e)}")
                            continue
                    
                    if month_counts:
                        result = f"The months with the highest number of faults ({max_count} faults each) are:\n"
                        for month in sorted(month_counts):
                            result += f"- {month}\n"
                        return result
                    
            # Handle battery breakdown query
            if "battery" in query.lower() and "breakdown" in query.lower():
                if isinstance(df, pd.DataFrame) and 'Description' in df.columns:
                    battery_mask = df['Description'].str.contains('battery', case=False, na=False)
                    if not battery_mask.any():  # Check if we have any battery-related entries
                        return "No battery-related breakdowns found."
                    battery_count = battery_mask.sum()  # More efficient than len()
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
            if self.log_manager:
                self.log_manager.error(f"Error processing DataFrame response: {str(e)}")
            return str(raw_response)

    def chat(self, query: str) -> str:
        """Process a chat query and return a response."""
        try:
            if self.df is None or self.df.empty:
                if self.log_manager:
                    self.log_manager.error("No data available for analysis")
                return "No data available for analysis."
            
            # Log the incoming query
            if self.log_manager:
                self.log_manager.info(f"Processing query: {query}")
            
            # Check if it's a time-based query
            is_time_query = any(word in query.lower() for word in ['year', 'month', 'week', 'annual', 'monthly', 'weekly'])
            
            # Preprocess the query
            processed_query = self.query_preprocessor.preprocess(query)
            if self.log_manager:
                self.log_manager.info(f"Preprocessed query: {processed_query}")
            
            try:
                # Create SmartDataframe with custom configuration
                smart_df = SmartDataframe(
                    self.df,
                    config={
                        "llm": self.llm,
                        "enable_cache": True,
                        "custom_whitelisted_dependencies": ["dateutil"],
                        "custom_prompts": {
                            "system": """You are a vehicle maintenance analyst. When analyzing the data:
                            1. Focus on specific vehicle types and fault categories
                            2. Provide clear numerical insights (counts, percentages)
                            3. Consider maintenance patterns over time
                            4. Highlight key findings and trends
                            5. Format responses with proper units and context
                            6. For time-based analysis:
                               - Use date comparisons instead of Timedelta
                               - Group by maintenance periods
                               - Consider service intervals"""
                        }
                    }
                )
                
                if is_time_query:
                    # Try alternative query approach for time-based analysis
                    try:
                        modified_query = self._modify_time_query(processed_query)
                        raw_response = smart_df.chat(modified_query)
                        if self.log_manager:
                            self.log_manager.info(f"Time-based query modified to: {modified_query}")
                    except Exception as e:
                        if self.log_manager:
                            self.log_manager.error(f"Time-based query failed: {str(e)}")
                        return "Unable to process time-based query. Please try rephrasing your question to focus on specific date ranges or maintenance periods."
                else:
                    # Get response for non-time-based query
                    raw_response = smart_df.chat(processed_query)
                
                if self.log_manager:
                    self.log_manager.info(f"Raw response: {raw_response}")
                
            except AttributeError as e:
                if "Timedelta" in str(e):
                    if self.log_manager:
                        self.log_manager.warning("Time-based analysis requires alternative approach")
                    return "Unable to process time-based query. Please try rephrasing your question to focus on specific date ranges or maintenance periods."
                else:
                    raise
            except Exception as e:
                if self.log_manager:
                    self.log_manager.error(f"Error in SmartDataframe processing: {str(e)}")
                return f"Unable to process query due to error: {str(e)}"
            
            # Process and enhance the response
            try:
                enhanced_response = self.response_processor.enhance_response(query, raw_response)
                if self.log_manager:
                    self.log_manager.info(f"Enhanced response: {enhanced_response}")
                return enhanced_response
                
            except Exception as e:
                if self.log_manager:
                    self.log_manager.error(f"Error enhancing response: {str(e)}")
                return str(raw_response)  # Return raw response if enhancement fails
            
        except Exception as e:
            error_msg = f"Error in chat: {str(e)}"
            if self.log_manager:
                self.log_manager.error(error_msg)
            return error_msg

    def _modify_time_query(self, query: str) -> str:
        """Modify time-based queries to use alternative approaches."""
        query = query.lower()
        
        # Replace time-based references with maintenance period terminology
        replacements = {
            'year': 'annual maintenance period',
            'monthly': '30-day maintenance period',
            'week': '7-day maintenance period',
            'annual': 'yearly maintenance cycle',
            '1st year': 'initial maintenance period',
            '2nd year': 'second maintenance period',
            '3rd year': 'third maintenance period',
            '4th year': 'fourth maintenance period',
            '5th year': 'fifth maintenance period'
        }
        
        for old, new in replacements.items():
            if old in query:
                query = query.replace(old, new)
                
        # Add maintenance context if not present
        if 'maintenance' not in query and 'servicing' not in query:
            query = f"maintenance analysis for {query}"
            
        return query

    def query(self, df_data, query_text):
        """Process a query with provided data and return the response."""
        try:
            self.df = self.prepare_dataframe(df_data)
            if self.df is not None and not self.df.empty:
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
            return self.chat(query_text)
        except Exception as e:
            error_msg = f"Error processing query: {str(e)}"
            if self.log_manager:
                self.log_manager.error(error_msg)
            return error_msg
