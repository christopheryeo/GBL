from abc import ABC, abstractmethod
import pandas as pd
import yaml
import os

class BaseProcessor(ABC):
    def __init__(self):
        self.config = self._load_config()
        
    def _load_config(self):
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'excel_formats.yaml')
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
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
