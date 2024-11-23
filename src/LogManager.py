"""
Log Manager for capturing and storing application logs.
Author: Chris Yeo
"""

import sys
import io
import threading
import time
import subprocess
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
            
            self.log(f"Application started. Git version: {git_hash} ({git_branch}) - {git_desc}")
        except subprocess.CalledProcessError:
            self.log("Application started. Unable to retrieve git version information.")
    
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
            print(f"[{timestamp}] {message}")  # Print to console as well
    
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
