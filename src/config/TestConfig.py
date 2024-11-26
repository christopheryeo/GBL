"""
Test Configuration Manager.
Handles loading and providing test configuration from YAML.
Author: Chris Yeo
"""

import os
import yaml
import logging
import time
from typing import Dict, Any, Optional, List, Set
from datetime import datetime

class TestConfig:
    """Manages test configuration and logging."""
    
    _instance = None
    _config = None
    _kardex_config = None
    _loggers = {}
    
    def __new__(cls):
        """Create singleton instance."""
        if cls._instance is None:
            cls._instance = super(TestConfig, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize configuration if not already loaded."""
        if self._config is None:
            self._config = self._load_config()
            
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML files."""
        config_dir = os.path.dirname(os.path.abspath(__file__))
        test_config_path = os.path.join(config_dir, 'test_config.yaml')
        
        try:
            # Load main test config
            with open(test_config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Load Kardex config if specified
            kardex_config_rel = config.get('kardex_config')
            if kardex_config_rel:
                kardex_config_path = os.path.join(config_dir, '..', kardex_config_rel)
                with open(kardex_config_path, 'r') as f:
                    self._kardex_config = yaml.safe_load(f)
            
            return config
        except Exception as e:
            print(f"Error loading configuration: {str(e)}")
            return {}
    
    def get_test_files(self) -> Dict[str, str]:
        """Get dictionary of test files."""
        return self._config.get('test_files', {})
    
    def get_test_question_config(self, test_name: str) -> Dict[str, Any]:
        """Get test question configuration for a specific test.
        
        Args:
            test_name (str): Name of the test to get configuration for
            
        Returns:
            Dict[str, Any]: Test question configuration including default query if specified
        """
        test_questions = self._config.get('test_questions', {})
        return test_questions.get(test_name, {})
    
    def get_kardex_path(self, file_key: str = None) -> str:
        """Get path to Kardex Excel file.
        
        Args:
            file_key (str): Key of Excel file to get path for.
                          If None, uses default_kardex from config.
        
        Returns:
            str: Absolute path to Excel file
        """
        if file_key is None:
            file_key = self._config.get('default_kardex')
            
        if not self._kardex_config:
            raise ValueError("No Kardex configuration loaded")
            
        excel_files = self._kardex_config.get('excel_files', {})
        file_config = excel_files.get(file_key, {})
        rel_path = file_config.get('path')
        
        if not rel_path:
            raise ValueError(f"No path found for Excel file key: {file_key}")
            
        # Convert to absolute path
        return os.path.abspath(rel_path)
    
    def get_format_path(self, file_key: str) -> str:
        """Get path to format configuration file.
        
        Args:
            file_key (str): Key of Excel file to get format for
            
        Returns:
            str: Absolute path to format configuration file
        """
        if not self._kardex_config:
            raise ValueError("No Kardex configuration loaded")
            
        excel_files = self._kardex_config.get('excel_files', {})
        file_config = excel_files.get(file_key, {})
        rel_path = file_config.get('format')
        
        if not rel_path:
            raise ValueError(f"No format configuration found for Excel file key: {file_key}")
            
        # Format files are in format_specific directory
        format_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'processors', 'format_specific')
        return os.path.join(format_dir, rel_path)
    
    def get_excel_format(self, file_key: str) -> Dict[str, Any]:
        """Get format configuration for Excel file.
        
        Args:
            file_key (str): Key of Excel file to get format for
            
        Returns:
            Dict containing format configuration
        """
        format_path = self.get_format_path(file_key)
        try:
            with open(format_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading format configuration: {str(e)}")
            return {}
    
    def get_default_kardex(self) -> str:
        """Get the default Kardex file key from config.
        
        Returns:
            str: Default Kardex file key
        """
        default_kardex = self._config.get('default_kardex')
        if not default_kardex:
            raise ValueError("No default Kardex file specified in config")
        return default_kardex
    
    def get_logger(self, logger_name: str) -> logging.Logger:
        """Get or create logger with configuration from YAML.
        
        Args:
            logger_name (str): Name of the logger to get/create
            
        Returns:
            logging.Logger: Configured logger instance
        """
        # Return existing logger if already created
        if logger_name in self._loggers:
            return self._loggers[logger_name]
            
        # Get logging config
        log_config = self._config.get('logging', {}).get(logger_name, {})
        if not log_config:
            raise ValueError(f"No logging configuration found for: {logger_name}")
            
        # Create logger
        logger = logging.getLogger(logger_name)
        logger.setLevel(getattr(logging, log_config.get('level', 'INFO')))
        
        # Create log directory if needed
        log_dir = log_config.get('log_dir', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Create formatter
        formatter = logging.Formatter(
            fmt=log_config.get('format', '%(message)s'),
            datefmt=log_config.get('date_format', '%Y-%m-%d %H:%M:%S')
        )
        
        # Create and add file handler
        log_file = log_config.get('log_file')
        if log_file:
            fh = logging.FileHandler(log_file)
            fh.setLevel(logger.level)
            fh.setFormatter(formatter)
            logger.addHandler(fh)
        
        # Create and add console handler
        ch = logging.StreamHandler()
        ch.setLevel(logger.level)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
        # Store and return logger
        self._loggers[logger_name] = logger
        return logger

    def get_test_sequence(self) -> List[str]:
        """Get the ordered sequence of tests to run."""
        return self._config.get('test_execution', {}).get('sequence', [])

    def get_test_dependencies(self, test_name: str) -> List[str]:
        """Get dependencies for a specific test."""
        deps = self._config.get('test_execution', {}).get('dependencies', {})
        return deps.get(test_name, {}).get('requires', [])

    def get_execution_settings(self) -> Dict[str, Any]:
        """Get test execution settings."""
        return self._config.get('test_execution', {}).get('settings', {
            'stop_on_failure': True,
            'retry_count': 1,
            'retry_delay': 2,
            'parallel_allowed': False
        })

    def get_test_timeout(self, test_name: str) -> int:
        """Get timeout for a specific test."""
        timeouts = self._config.get('test_execution', {}).get('timeouts', {})
        return timeouts.get(test_name, timeouts.get('default', 30))

    def get_test_file(self, test_name: str) -> str:
        """Get the file path for a specific test."""
        test_files = self._config.get('test_files', {})
        return test_files.get(test_name, '')

    def validate_test_dependencies(self) -> bool:
        """Validate that test dependencies form a valid DAG without cycles."""
        def get_all_dependencies(test: str, visited: Set[str] = None) -> Set[str]:
            if visited is None:
                visited = set()
            if test in visited:
                return visited
            visited.add(test)
            for dep in self.get_test_dependencies(test):
                get_all_dependencies(dep, visited)
            return visited

        sequence = self.get_test_sequence()
        for test in sequence:
            deps = get_all_dependencies(test)
            if test in deps - {test}:
                return False
        return True


# Create singleton instance
test_config = TestConfig()
