from abc import ABC, abstractmethod
import pandas as pd
import yaml
import os
from config.TestConfig import test_config

class BaseProcessor(ABC):
    def __init__(self, file_key: str):
        """Initialize the processor.
        
        Args:
            file_key (str): Key of the Excel file to process, must match a key in test_config.yaml
        """
        self.file_key = file_key
        self.config = self._load_config()
        
    def _load_config(self):
        """Load format configuration for this Excel file."""
        return test_config.get_excel_format(self.file_key)
    
    @abstractmethod
    def extract_data(self, file_path: str) -> pd.DataFrame:
        """Extract data from Excel file into DataFrame."""
        pass
    
    @abstractmethod
    def validate(self, data: pd.DataFrame) -> pd.DataFrame:
        """Validate the extracted data."""
        pass
    
    @abstractmethod
    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """Transform the validated data."""
        pass
    
    def process(self, file_path: str) -> pd.DataFrame:
        """Main processing pipeline."""
        data = self.extract_data(file_path)
        validated_data = self.validate(data)
        transformed_data = self.transform(validated_data)
        return transformed_data
