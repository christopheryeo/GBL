#!/usr/bin/env python3
"""
Response Processor for Goldbell Leasing ChatGPT integration.
Enhances raw responses from PandasAI using ChatGPT.
Author: Chris Yeo
"""

import os
import pandas as pd
from openai import OpenAI
from config.prompt_manager import PromptManager

class ResponseProcessor:
    """Process and enhance responses from PandasAI using ChatGPT."""
    
    def __init__(self, logger):
        """Initialize the ResponseProcessor with a logger."""
        self.logger = logger
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.prompt_manager = PromptManager()
        
    def _format_vehicle_type_response(self, query, response):
        """Format response for vehicle type related queries."""
        try:
            if isinstance(response, str) and 'Vehicle Type' in response and 'Number of Faults' in response:
                # Parse the response into a DataFrame
                lines = response.strip().split('\n')
                data = []
                for line in lines[1:]:  # Skip header
                    parts = line.split()
                    if len(parts) >= 2:
                        vehicle_type = ' '.join(parts[:-1])
                        faults = int(parts[-1])
                        data.append((vehicle_type.strip(), faults))
                
                # Calculate total faults and percentages
                total_faults = sum(faults for _, faults in data)
                
                # Format response
                formatted_response = f"Here's the breakdown of faults by vehicle type:\n\n"
                formatted_response += f"Total Faults: {total_faults}\n\n"
                formatted_response += "Distribution by Vehicle Type:\n"
                formatted_response += "----------------------------------------\n"
                
                for vehicle_type, faults in data:
                    percentage = (faults / total_faults) * 100
                    formatted_response += f"{vehicle_type}:\n"
                    formatted_response += f"  • Number of faults: {faults}\n"
                    formatted_response += f"  • Percentage: {percentage:.2f}%\n"
                
                if self.logger:
                    self.logger.info(f"Formatted vehicle type response: {formatted_response}")
                return formatted_response
            
            return response
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error formatting vehicle type response: {str(e)}")
            return response

    def _format_time_based_response(self, query, response):
        """Format response for time-based queries."""
        try:
            # Check if response contains time-based information
            time_indicators = ['year', 'month', 'week', 'quarter']
            if any(indicator in response.lower() for indicator in time_indicators):
                # Add time period context
                formatted_response = "Time Period Analysis:\n"
                formatted_response += "----------------------------------------\n"
                formatted_response += response
                
                if self.logger:
                    self.logger.info(f"Formatted time-based response: {formatted_response}")
                return formatted_response
            
            return response
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error formatting time-based response: {str(e)}")
            return response

    def enhance_response(self, query, raw_response):
        """Enhance the raw response using GPT-4."""
        try:
            if self.logger:
                self.logger.info(f"Processing response for query: {query}")
            
            # Handle empty or None responses
            if raw_response is None:
                return "No data available for analysis."
                
            # Handle DataFrame responses
            if isinstance(raw_response, pd.DataFrame):
                if raw_response.empty:
                    return "No data available for analysis."
                # Convert DataFrame to string representation
                raw_response = raw_response.to_string()
            elif isinstance(raw_response, pd.Series):
                if raw_response.empty:
                    return "No data available for analysis."
                # Convert Series to string representation
                raw_response = raw_response.to_string()
                
            # Handle string responses
            if isinstance(raw_response, str) and raw_response.strip() == "":
                return "No data available for analysis."
            
            # Convert query to lowercase for easier matching
            query_lower = query.lower()
            
            # Check for vehicle type related queries
            if 'vehicle type' in query_lower and ('faults' in query_lower or 'maintenance' in query_lower):
                raw_response = self._format_vehicle_type_response(query, raw_response)
            
            # Get system prompt from prompt manager
            system_prompt = self.prompt_manager.get_system_prompt("response_processor")
            
            # Create user prompt using response format
            user_prompt = self.prompt_manager.get_response_format("enhance_response", 
                query=query,
                raw_response=raw_response
            )
            
            # Get enhanced response from GPT
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            # Extract the enhanced response
            enhanced_response = response.choices[0].message.content
            
            if self.logger:
                self.logger.info("Response successfully enhanced")
            
            return enhanced_response
            
        except Exception as e:
            error_msg = f"Error enhancing response: {str(e)}"
            if self.logger:
                self.logger.error(error_msg)
            return raw_response  # Fall back to raw response on error
            
    def format_maintenance_insights(self, response):
        """Format maintenance-specific insights in a structured way."""
        # TODO: Implement maintenance insights formatting
        return response
