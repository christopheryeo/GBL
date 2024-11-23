"""
ChatGPT API integration for Goldbell Leasing application.
Provides functions to interact with OpenAI's GPT-4 model.
Author: Chris Yeo

Improvements made:
1. Automatic Connection Testing:
   - Tests the connection during initialization
   - Makes a minimal test API call to verify everything works
   - Stores connection status and any error messages

2. Better Error Handling:
   - No more exceptions thrown to the user
   - All errors are captured and returned in a structured format
   - Connection status is tracked and updated automatically

3. New Features:
   - get_connection_status() method to check connection state
   - More informative error messages
   - Automatic detection of authentication issues
   - Visual indicators in test output

4. Improved Testing:
   - Two-stage testing (connection check, then API call)
   - More detailed test output
   - Graceful handling of all error cases
"""

import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import Dict, List, Optional, Union

# Load environment variables from .env file
load_dotenv()

class ChatGPT:
    """
    A class to handle interactions with OpenAI's GPT-4 model.
    Includes automatic connection testing and graceful error handling.
    
    Key Features:
    - Automatic connection testing during initialization
    - Graceful error handling without exceptions
    - Connection status tracking
    - Detailed error messages
    """
    
    def __init__(self):
        """
        Initialize the ChatGPT class with API key and test the connection.
        If the connection test fails, the instance will still be created but
        will return error messages instead of making API calls.
        
        Improvements:
        - Stores connection status
        - Captures initialization errors
        - No exceptions thrown
        """
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.client = None
        self.is_connected = False
        self.error_message = None
        
        # Initialize and test connection
        self._initialize_connection()
    
    def _initialize_connection(self) -> None:
        """
        Initialize the OpenAI client and test the connection.
        Sets is_connected flag and error_message based on results.
        
        Improvements:
        - Makes minimal test API call
        - Verifies actual API functionality
        - Stores detailed error messages
        - Updates connection status automatically
        """
        if not self.api_key:
            self.error_message = "OpenAI API key not found in environment variables"
            return
        
        try:
            self.client = OpenAI(api_key=self.api_key)
            
            # Make a minimal test call to verify connection
            test_response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5,
                temperature=0.1
            )
            
            if test_response.choices[0].message.content:
                self.is_connected = True
                self.error_message = None
            else:
                self.error_message = "API test call returned empty response"
                
        except Exception as e:
            self.error_message = f"API Connection Error: {str(e)}"
            self.is_connected = False

    def ask_gpt(self, 
                prompt: str, 
                model: str = "gpt-4",
                temperature: float = 0.7,
                max_tokens: int = 1000) -> Dict[str, Union[str, List[Dict]]]:
        """
        Send a prompt to GPT-4 and get a response.
        If the connection is not available, returns an error message.
        
        Improvements:
        - Checks connection status before making calls
        - Returns structured error responses
        - Updates connection status on authentication errors
        - Maintains message history even on errors
        
        Args:
            prompt (str): The question or prompt to send to GPT-4
            model (str): The OpenAI model to use (default: "gpt-4")
            temperature (float): Controls randomness (0-1, default: 0.7)
            max_tokens (int): Maximum length of response (default: 1000)
            
        Returns:
            Dict containing either the response and message history,
            or an error message if the connection is not available
        """
        # Check connection status first
        if not self.is_connected:
            return {
                "error": self.error_message or "Connection to OpenAI API not available",
                "messages": [{"role": "user", "content": prompt}]
            }
        
        try:
            # Create the chat completion
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Extract the response text
            response_text = response.choices[0].message.content
            
            return {
                "response": response_text,
                "messages": [
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": response_text}
                ]
            }
            
        except Exception as e:
            error_msg = f"Error during API call: {str(e)}"
            # Update connection status if we get an authentication error
            if "authentication" in str(e).lower() or "api key" in str(e).lower():
                self.is_connected = False
                self.error_message = error_msg
            
            return {
                "error": error_msg,
                "messages": [{"role": "user", "content": prompt}]
            }

    def get_connection_status(self) -> Dict[str, Union[bool, str]]:
        """
        Get the current connection status and any error message.
        
        Improvements:
        - Provides easy way to check connection state
        - Returns both status and error message
        - Helps with debugging and user feedback
        
        Returns:
            Dict containing connection status and error message if any
        """
        return {
            "connected": self.is_connected,
            "error": self.error_message if not self.is_connected else None
        }

# Test function to verify the API connection
def test_gpt():
    """
    Test the ChatGPT integration with a simple prompt.
    
    Improvements:
    - Two-stage testing (connection, then API call)
    - Visual status indicators (✓/✗)
    - Detailed error reporting
    - Graceful failure handling
    """
    chat = ChatGPT()
    status = chat.get_connection_status()
    
    print("Connection Status:", "✓ Connected" if status["connected"] else "✗ Not Connected")
    if status["error"]:
        print("Connection Error:", status["error"])
        return False
    
    print("Testing API call...")
    result = chat.ask_gpt(
        prompt="Please respond with 'Connection successful!' if you can read this message.",
        temperature=0.3,
        max_tokens=50
    )
    
    if "error" in result:
        print("API Call Error:", result["error"])
        return False
        
    print("Response:", result["response"])
    return True

if __name__ == "__main__":
    # Run the test when the file is executed directly
    test_gpt()
