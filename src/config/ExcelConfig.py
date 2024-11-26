"""
Excel Configuration Manager.
Handles loading and providing Excel file structure configuration from YAML.
Author: Chris Yeo
"""

import os
import yaml
from typing import Dict, Any, Optional
from .TestConfig import test_config

class ExcelConfig:
    """Manages Excel file structure configuration."""
    
    def __init__(self, file_key: str):
        """Initialize the Excel Configuration manager.
        
        Args:
            file_key (str): Key of the Excel file to get configuration for.
                          Must match a key in test_config.yaml's excel_files section.
        """
        self.file_key = file_key
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            return test_config.get_excel_format(self.file_key)
        except Exception as e:
            print(f"Error loading Excel configuration: {str(e)}")
            return {}
    
    def get_format_config(self) -> Dict[str, Any]:
        """Get configuration for this Excel format.
            
        Returns:
            Dict containing the format configuration
        """
        return self.config.get("format", {})
    
    def get_row_indices(self) -> Dict[str, int]:
        """Get row indices for this format.
        
        Returns:
            Dict containing row indices:
            - vehicle_type_row: Row containing vehicle type
            - header_row: Row containing column headers
            - data_start_row: First row of data
        """
        format_config = self.get_format_config()
        return {
            'vehicle_type_row': format_config.get('vehicle_type_row', 1),
            'header_row': format_config.get('header_row', 3),
            'data_start_row': format_config.get('data_start_row', 4)
        }
    
    def get_column_config(self) -> Dict[str, Dict[str, Any]]:
        """Get column configuration for this format.
        
        Returns:
            Dict mapping column names to their configuration:
            - type: Data type of the column
            - required: Whether the column is required
        """
        format_config = self.get_format_config()
        columns = format_config.get('columns', [])
        return {
            col['name']: {
                'type': col.get('type', 'string'),
                'required': col.get('required', False)
            }
            for col in columns
        }
    
    def get_required_columns(self) -> list:
        """Get list of required column names.
        
        Returns:
            List of column names that are marked as required
        """
        column_config = self.get_column_config()
        return [
            name for name, config in column_config.items()
            if config.get('required', False)
        ]
