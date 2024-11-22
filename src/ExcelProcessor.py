import pandas as pd
import os
from io import StringIO

class ExcelProcessor:
    def __init__(self, file_path):
        self.file_path = file_path
        self.df = None
        self.sheet_name = None
        self.data_info = None

    def read_excel(self):
        """Read the Excel file into a pandas DataFrame"""
        try:
            # Get the Excel file's sheet names
            xl = pd.ExcelFile(self.file_path)
            self.sheet_name = xl.sheet_names[0]  # Get the first sheet name
            
            # Read the first sheet
            self.df = pd.read_excel(self.file_path, sheet_name=self.sheet_name)
            return True
        except Exception as e:
            print(f"Error reading Excel file: {str(e)}")
            return False

    def get_data_info(self):
        """Get detailed information about the DataFrame"""
        if self.df is None:
            return None

        # Get basic file info
        file_info = f"""Filename: {os.path.basename(self.file_path)}
Sheet Name: {self.sheet_name}
Number of Records: {len(self.df)}
Number of Columns: {len(self.df.columns)}"""

        # Get column information
        buffer = StringIO()
        self.df.info(buf=buffer)
        column_info = buffer.getvalue()

        # Get sample data (first 5 rows)
        sample_data = self.df.head().to_string()

        # Get summary statistics
        summary_stats = self.df.describe().to_string()

        return {
            'file_info': file_info,
            'column_info': column_info,
            'sample_data': sample_data,
            'summary_stats': summary_stats
        }

    def process_file(self):
        """Process the Excel file and store the data information"""
        if self.read_excel():
            self.data_info = self.get_data_info()
            return f"Sheet Name: {self.sheet_name}, Number of Records: {len(self.df)}"
        return "Error processing Excel file"
