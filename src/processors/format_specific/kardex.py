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
                    sheet_df['Vehicle Type'] = sheet_name.split(' (')[0].strip()
                    print(f"Sheet {sheet_name} has {len(sheet_df)} rows before validation")
                    break
            
            if sheet_df is not None:
                all_dfs.append(sheet_df)
                
        if not all_dfs:
            raise ValueError("No valid Kardex data found in Excel file")
            
        # Combine all sheets
        df = pd.concat(all_dfs, ignore_index=True)
        print(f"Total rows before validation: {len(df)}")
            
        print(f"Found columns: {df.columns.tolist()}")
        required_cols = [col['name'] for col in self.format_config['columns'] if col['required']]
        
        # Ensure all required columns are present
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
            
        return df
    
    def validate(self, data: pd.DataFrame) -> pd.DataFrame:
        """Validate the extracted data."""
        print(f"Starting validation with {len(data)} rows")
        
        # Remove rows where all required columns are empty
        required_cols = self.format_config['validations']['required_columns']
        data_before_drop = data.copy()
        data = data.dropna(subset=required_cols, how='all')
        print(f"Dropped {len(data_before_drop) - len(data)} rows with empty required columns")
        print(f"After dropping empty required columns: {len(data)} rows")
        
        # Convert WO No to string to preserve leading zeros
        data['WO No'] = data['WO No'].astype(str)
        
        # Validate dates
        data_before_drop = data.copy()
        data['Open Date'] = pd.to_datetime(data['Open Date'], errors='coerce')
        print(f"Rows with invalid dates: {data['Open Date'].isna().sum()}")
        data = data.dropna(subset=['Open Date'])
        print(f"Dropped {len(data_before_drop) - len(data)} rows with invalid dates")
        print(f"After dropping invalid dates: {len(data)} rows")
        
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
