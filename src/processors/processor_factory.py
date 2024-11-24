import pandas as pd
from .format_specific.kardex import KardexProcessor
import logging

class ProcessorFactory:
    _processors = {
        'kardex': KardexProcessor
    }
    
    @classmethod
    def create(cls, format_type: str):
        """Create and return appropriate processor instance."""
        processor_class = cls._processors.get(format_type.lower())
        if not processor_class:
            raise ValueError(f"Unsupported format type: {format_type}")
        return processor_class()
    
    @classmethod
    def detect_format(cls, file_path: str) -> str:
        """Detect the format of the Excel file."""
        print(f"Attempting to detect format for file: {file_path}")
        try:
            xl = pd.ExcelFile(file_path)
            print(f"Found sheets: {xl.sheet_names}")
            
            for sheet_name in xl.sheet_names:
                print(f"Checking sheet: {sheet_name}")
                # Read without headers first
                df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
                
                # Look for the row containing "WO No" or similar
                for idx, row in df.iterrows():
                    if any('WO No' in str(val) for val in row):
                        print(f"Found 'WO No' in sheet {sheet_name} at row {idx} - identified as Kardex format")
                        return 'kardex'
                    
        except Exception as e:
            print(f"Error during format detection: {str(e)}")
            raise ValueError(f"Error detecting Excel format: {str(e)}")
            
        raise ValueError("Unable to detect Excel format - no matching format found")
