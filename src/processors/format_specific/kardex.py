import pandas as pd
import numpy as np
from datetime import datetime
from ..base_processor import BaseProcessor

class KardexProcessor(BaseProcessor):
    def __init__(self):
        super().__init__()
        self.format_config = self.config['formats']['kardex']
        
    def extract_data(self, file_path: str) -> pd.DataFrame:
        """Extract data from Kardex Excel file."""
        # Read all sheets to find the one with data
        xl = pd.ExcelFile(file_path)
        df = None
        
        for sheet_name in xl.sheet_names:
            print(f"Processing sheet: {sheet_name}")
            # Skip header rows to find actual column names
            temp_df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
            
            # Look for the row containing "WO No" or similar
            for idx, row in temp_df.iterrows():
                if any('WO No' in str(val) for val in row):
                    print(f"Found header row at index {idx}")
                    # Read the Excel file again with the correct header row
                    df = pd.read_excel(file_path, sheet_name=sheet_name, header=idx)
                    # Clean column names
                    df.columns = [str(col).strip() for col in df.columns]
                    # Skip the header row in the data
                    df = df.iloc[1:]
                    break
            
            if df is not None:
                break
        
        if df is None:
            raise ValueError("No valid Kardex data found in Excel file")
            
        print(f"Found columns: {df.columns.tolist()}")
        required_cols = [col['name'] for col in self.format_config['columns'] if col['required']]
        
        # Ensure all required columns are present
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
            
        return df
    
    def validate(self, data: pd.DataFrame) -> pd.DataFrame:
        """Validate the extracted data."""
        # Remove rows where all required columns are empty
        required_cols = self.format_config['validations']['required_columns']
        data = data.dropna(subset=required_cols, how='all')
        
        # Convert WO No to string to preserve leading zeros
        data['WO No'] = data['WO No'].astype(str)
        
        # Validate dates
        data['Open Date'] = pd.to_datetime(data['Open Date'], errors='coerce')
        data = data.dropna(subset=['Open Date'])
        
        return data
    
    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """Transform the validated data."""
        # Clean work order numbers
        data['WO No'] = data['WO No'].str.strip()
        
        # Format dates
        data['Open Date'] = data['Open Date'].dt.strftime(self.format_config['validations']['date_format'])
        
        # Clean description
        if 'Job Description' in data.columns:
            data['Job Description'] = data['Job Description'].fillna('').str.strip()
        
        # Clean amount
        if 'Custamt' in data.columns:
            data['Custamt'] = pd.to_numeric(data['Custamt'], errors='coerce')
            data['Custamt'] = data['Custamt'].fillna(0)
        
        # Clean ST and Cat columns
        for col in ['ST', 'Cat']:
            if col in data.columns:
                data[col] = data[col].fillna('').str.strip()
        
        return data
