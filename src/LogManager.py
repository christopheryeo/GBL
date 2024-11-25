"""
Log Manager for capturing and storing application logs.
Author: Chris Yeo
"""

import sys
import io
import threading
import time
import subprocess
import os
from datetime import datetime
from queue import Queue, Empty
from typing import List, Dict

class LogManager:
    """
    Manages application logs with a circular buffer and stdout capturing.
    """
    
    def __init__(self, max_logs: int = 1000):
        """
        Initialize the log manager.
        
        Args:
            max_logs (int): Maximum number of logs to keep in memory
        """
        self.logs = []
        self.max_logs = max_logs
        self.log_id = 0
        self.log_lock = threading.Lock()
        
        # Set up log file path
        self.log_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.log_file = os.path.join(self.log_dir, "application.log")
        
        # Create log directory if it doesn't exist
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
        # Create or append to the log file
        try:
            with open(self.log_file, 'a') as f:
                f.write(f"\n=== Log Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
        except Exception as e:
            print(f"Error creating log file: {str(e)}")
        
        # Log git version information
        self._log_git_info()
    
    def _log_git_info(self):
        """Log git version and latest commit information."""
        try:
            # Get git commit hash
            git_hash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], 
                                            stderr=subprocess.DEVNULL).decode().strip()
            
            # Get git commit description
            git_desc = subprocess.check_output(['git', 'log', '-1', '--pretty=%B'], 
                                            stderr=subprocess.DEVNULL).decode().strip()
            
            # Get branch name
            git_branch = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], 
                                              stderr=subprocess.DEVNULL).decode().strip()
            
            # Get author and date
            git_author = subprocess.check_output(['git', 'log', '-1', '--pretty=%an'], 
                                              stderr=subprocess.DEVNULL).decode().strip()
            git_date = subprocess.check_output(['git', 'log', '-1', '--pretty=%ad', '--date=format:%Y-%m-%d %H:%M:%S'], 
                                            stderr=subprocess.DEVNULL).decode().strip()
            
            # Format the startup message
            startup_message = (
                "\n=== Application Started ===\n"
                f"Version: {git_hash} on {git_branch}\n"
                f"Last Commit: {git_desc}\n"
                f"Author: {git_author}\n"
                f"Date: {git_date}\n"
                "=========================="
            )
            self.log(startup_message)
        except subprocess.CalledProcessError:
            self.log("\n=== Application Started === (Git information unavailable) ===")
    
    def _write_to_file(self, timestamp: str, message: str):
        """Write log entry to file."""
        try:
            with open(self.log_file, 'a') as f:
                f.write(f"[{timestamp}] {message}\n")
        except Exception as e:
            print(f"Error writing to log file: {str(e)}")
    
    def log(self, message: str):
        """
        Add a log entry with timestamp.
        
        Args:
            message (str): The log message
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        with self.log_lock:
            log_entry = {
                'id': self.log_id,
                'timestamp': timestamp,
                'message': message
            }
            self.logs.append(log_entry)
            if len(self.logs) > self.max_logs:
                self.logs.pop(0)
            self.log_id += 1
            print(f"[{timestamp}] {message}")  # Print to console
            self._write_to_file(timestamp, message)  # Write to file
    
    def get_logs(self, after_id: int = -1) -> List[Dict]:
        """
        Get logs after the specified ID.
        
        Args:
            after_id (int): Return logs after this ID
        
        Returns:
            List[Dict]: List of log entries
        """
        with self.log_lock:
            if after_id == -1:
                return self.logs[-100:]  # Return last 100 logs for initial load
            return [log for log in self.logs if log['id'] > after_id]
    
    def cleanup(self):
        """Cleanup resources."""
        pass  # No cleanup needed in simplified version
