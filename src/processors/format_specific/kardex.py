import pandas as pd
import numpy as np
from datetime import datetime
from ..base_processor import BaseProcessor

class KardexProcessor(BaseProcessor):
    def __init__(self, file_key: str):
        """Initialize the Kardex processor.
        
        Args:
            file_key (str): Key of the Excel file to process, must match a key in test_config.yaml
        """
        super().__init__(file_key)
        self.format_config = self.config['format']
        
    def extract_data(self, file_path: str) -> pd.DataFrame:
        """Extract data from Kardex Excel file."""
        # Read all sheets to find the one with data
        xl = pd.ExcelFile(file_path)
        all_dfs = []
        
        for sheet_name in xl.sheet_names:
            print(f"Processing sheet: {sheet_name}")
            # Skip header rows to find actual column names
            temp_df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
            sheet_df = None
            
            # Look for the row containing "WO No" or similar
            for idx, row in temp_df.iterrows():
                if any('WO No' in str(val) for val in row):
                    print(f"Found header row at index {idx}")
                    # Read the Excel file again with the correct header row
                    sheet_df = pd.read_excel(file_path, sheet_name=sheet_name, header=idx)
                    # Clean column names
                    sheet_df.columns = [str(col).strip() for col in sheet_df.columns]
                    # Add sheet name as vehicle type
                    sheet_df['Vehicle Type'] = sheet_name
                    break
            
            if sheet_df is not None:
                all_dfs.append(sheet_df)
        
        if not all_dfs:
            raise ValueError("No valid data found in Excel file")
        
        # Combine all sheets
        df = pd.concat(all_dfs, ignore_index=True)
        
        # Get required columns from format config
        required_columns = [col['name'] for col in self.format_config['columns'] if col.get('required', False)]
        
        # Verify required columns exist
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        return df
    
    def validate(self, data: pd.DataFrame) -> pd.DataFrame:
        """Validate the extracted data."""
        # Remove rows where all required fields are empty
        required_columns = [col['name'] for col in self.format_config['columns'] if col.get('required', False)]
        data = data.dropna(subset=required_columns, how='all')
        
        # Convert date columns
        date_columns = [col['name'] for col in self.format_config['columns'] if col.get('type') == 'date']
        for col in date_columns:
            if col in data.columns:
                data[col] = pd.to_datetime(data[col], errors='coerce')
        
        # Convert numeric columns
        numeric_columns = [col['name'] for col in self.format_config['columns'] if col.get('type') == 'float']
        for col in numeric_columns:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce')
        
        return data
    
    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """Transform the validated data."""
        # Sort by date if available
        date_columns = [col['name'] for col in self.format_config['columns'] if col.get('type') == 'date']
        if date_columns and date_columns[0] in data.columns:
            data = data.sort_values(date_columns[0])
        
        return data
