"""
Base class for all domain-specific Excel processors.
"""
from typing import Any, Dict, List
from abc import ABC, abstractmethod
import pandas as pd
import yaml
import os
from ...LogManager import LogManager

class BaseProcessor(ABC):
    """Base class for all domain-specific Excel processors."""
    
    def __init__(self, domain: str, format_name: str):
        """
        Initialize base processor with domain and format configuration.
        
        Args:
            domain: Domain name (e.g., 'vehicle_leasing')
            format_name: Format name within the domain (e.g., 'kardex')
        """
        self.domain = domain
        self.format_name = format_name
        self.log_manager = LogManager()
        self.log_manager.log(f"Initializing {self.__class__.__name__} for domain '{domain}', format '{format_name}'")
        self.config = self._load_domain_config()
        
    def _load_domain_config(self) -> Dict[str, Any]:
        """
        Load domain configuration from excel_formats.yaml.
        
        Returns:
            Configuration dictionary for the specified domain and format
        """
        config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'excel_formats.yaml')
        self.log_manager.log(f"Loading configuration from {config_path}")
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                
            domain_config = config.get('domains', {}).get(self.domain)
            if not domain_config:
                error_msg = f"Domain '{self.domain}' not found in configuration"
                self.log_manager.log(f"Error: {error_msg}")
                raise ValueError(error_msg)
                
            format_config = domain_config.get('formats', {}).get(self.format_name)
            if not format_config:
                error_msg = f"Format '{self.format_name}' not found in domain '{self.domain}'"
                self.log_manager.log(f"Error: {error_msg}")
                raise ValueError(error_msg)
            
            self.log_manager.log(f"Successfully loaded configuration for {self.domain}/{self.format_name}")
            return {
                'domain_config': domain_config,
                'format_config': format_config
            }
        except Exception as e:
            error_msg = f"Failed to load configuration: {str(e)}"
            self.log_manager.log(f"Error: {error_msg}")
            raise
    
    def validate_format(self, df: pd.DataFrame) -> bool:
        """
        Validate Excel format against domain configuration.
        
        Args:
            df: Pandas DataFrame containing the Excel data
            
        Returns:
            bool: True if valid, False otherwise
        """
        format_config = self.config['format_config']
        required_columns = [col['name'] for col in format_config['columns'] if col.get('required', False)]
        
        self.log_manager.log(f"Validating DataFrame columns. Required: {required_columns}")
        
        # Check if all required columns are present
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            error_msg = f"Missing required columns: {missing_columns}"
            self.log_manager.log(f"Error: {error_msg}")
            raise ValueError(error_msg)
        
        self.log_manager.log("DataFrame validation successful")
        return True
    
    @abstractmethod
    def process(self, excel_file: str) -> List[Dict[str, Any]]:
        """
        Process Excel file based on domain configuration.
        Must be implemented by concrete classes.
        
        Args:
            excel_file: Path to the Excel file
            
        Returns:
            List of processed entities as dictionaries
        """
        pass
    
    def get_column_key(self, column_name: str) -> str:
        """
        Get the internal key for a column name from configuration.
        
        Args:
            column_name: Excel column name
            
        Returns:
            Internal key for the column
        """
        for col in self.config['format_config']['columns']:
            if col['name'] == column_name:
                key = col.get('key', column_name)
                self.log_manager.log(f"Mapped column '{column_name}' to key '{key}'")
                return key
        self.log_manager.log(f"Warning: No mapping found for column '{column_name}'")
        return column_name
