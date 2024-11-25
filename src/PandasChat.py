"""
PandasChat module for handling chat-based queries on DataFrame using PandasAI.
Provides functionality for querying data using natural language and specialized fault analysis.
Author: Chris Yeo
"""

import os
import pandas as pd
from pandasai.llm.openai import OpenAI
from pandasai import SmartDataframe
from VehicleFaults import VehicleFault

class PandasChat:
    def __init__(self, log_manager):
        """Initialize PandasChat with a log manager."""
        self.log_manager = log_manager
        self.llm = OpenAI(api_token=os.getenv('OPENAI_API_KEY'))

    def prepare_dataframe(self, df_data):
        """Prepare the DataFrame by converting date columns."""
        # Convert list to DataFrame if necessary
        if isinstance(df_data, list):
            df_data = pd.DataFrame(df_data)
            
        # Convert date columns to datetime
        date_columns = ['Open Date', 'Done Date', 'Actual Finish Date']
        for col in date_columns:
            if col in df_data.columns:
                df_data[col] = pd.to_datetime(df_data[col], errors='coerce')
        
        return VehicleFault(df_data)

    def handle_year_query(self, df, query):
        """Handle queries related to specific years."""
        if 'Open Date' not in df.columns:
            return None

        # Extract years from the query using a simple number check
        query_years = [int(year) for year in query.split() if year.isdigit() and len(year) == 4]
        
        if query_years:
            response_lines = ['Work orders for the requested years:']
            for year in sorted(query_years):
                count = len(df[df['Open Date'].dt.year == year])
                response_lines.append(f"- {year}: {count} work orders")
            
            self.log_manager.log(f"Generated work orders count for specific years: {query_years}")
            return '\n'.join(response_lines)
        else:
            # If no specific years requested, show all years
            years = df['Open Date'].dt.year.unique()
            years = sorted([year for year in years if not pd.isna(year)])
            
            response_lines = ['Work orders by year:']
            for year in years:
                count = len(df[df['Open Date'].dt.year == year])
                response_lines.append(f"- {int(year)}: {count} work orders")
            
            self.log_manager.log(f"Generated work orders count for all years")
            return '\n'.join(response_lines)

    def handle_category_query(self, df, query):
        """Handle queries related to fault categories."""
        stats = df.get_fault_statistics()
        
        # Determine if we're looking for main or sub categories
        if 'sub' in query.lower():
            categories = stats['sub_categories']
            category_type = "sub-categories"
        else:
            categories = stats['main_categories']
            category_type = "main categories"
        
        total = sum(categories.values())
        
        # Format the response
        response_lines = [f'Distribution of fault {category_type}:']
        for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total) * 100
            response_lines.append(f"- {category}: {count} faults ({percentage:.1f}%)")
        
        self.log_manager.log(f"Generated fault {category_type} distribution response")
        return '\n'.join(response_lines)

    def query(self, df_data, query):
        """Process a chat query and return the response."""
        try:
            if not query:
                return 'Please provide a query.'

            # Prepare the DataFrame
            df = self.prepare_dataframe(df_data)
            
            # Handle year-related queries
            if any(keyword in query.lower() for keyword in ['year', 'when', 'date']):
                response = self.handle_year_query(df, query)
                if response:
                    self.log_manager.log(f"CHAT_QUERY: {query} | RESPONSE: {response}")
                    return response

            # Handle category distribution queries
            if any(keyword in query.lower() for keyword in ['distribution', 'breakdown', 'categories']):
                response = self.handle_category_query(df, query)
                self.log_manager.log(f"CHAT_QUERY: {query} | RESPONSE: {response}")
                return response

            # For other queries, use PandasAI
            smart_df = SmartDataframe(df, config={
                'llm': self.llm,
                'custom_methods': [
                    df.filter_records,
                    df.get_filtered_count,
                    df.get_active_faults,
                    df.get_vehicle_history,
                    df.get_faults_by_category,
                    df._categorize_faults,
                    df.get_fault_statistics
                ]
            })

            # Query the DataFrame
            response = str(smart_df.chat(query))
            self.log_manager.log(f"CHAT_QUERY: {query} | RESPONSE: {response}")
            return response

        except Exception as e:
            error_msg = f'Sorry, there was an error processing your request: {str(e)}'
            self.log_manager.log(f"CHAT_QUERY: {query} | ERROR: {error_msg}")
            return error_msg
