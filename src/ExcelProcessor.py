"""
Core Excel processing module that handles Excel file parsing, data extraction, and analytics generation.
Provides structured data output for visualization and analysis.
"""

import pandas as pd
import time
from datetime import datetime
from collections import Counter

class ExcelProcessor:
    def __init__(self):
        self.data = None
        self.file_info = None
        self.processing_info = None
        self.sheet_counts = {}

    def _extract_vehicle_type(self, sheet):
        try:
            # Get the vehicle type from the third row (index 2)
            vehicle_type = sheet.iloc[2, 0]  # Assuming it's in the first column
            if pd.isna(vehicle_type) or not isinstance(vehicle_type, str):
                return "Unknown"
            return vehicle_type.strip()
        except Exception as e:
            print(f"Error extracting vehicle type: {str(e)}")
            return "Unknown"

    def process_excel(self, file_path, filename):
        start_time = time.time()
        
        try:
            # Read all sheets from the Excel file
            excel_file = pd.ExcelFile(file_path)
            all_data = []
            sheet_count = len(excel_file.sheet_names)
            sheet_data_counts = Counter()

            for sheet_name in excel_file.sheet_names:
                print(f"Processing sheet: {sheet_name}")
                # Read the sheet
                sheet = pd.read_excel(excel_file, sheet_name=sheet_name)
                
                if sheet.empty:
                    sheet_data_counts[sheet_name] = 0
                    continue

                # Extract vehicle type from the third row
                vehicle_type = self._extract_vehicle_type(sheet)
                
                # Skip the first 4 rows (headers and vehicle type)
                data = sheet.iloc[4:].copy()
                
                if not data.empty:
                    # Add vehicle_type and sheet_name columns
                    data['vehicle_type'] = vehicle_type
                    data['sheet_name'] = sheet_name
                    all_data.append(data)
                    sheet_data_counts[sheet_name] = len(data)
                else:
                    sheet_data_counts[sheet_name] = 0

            # Combine all data into a single DataFrame
            if all_data:
                self.data = pd.concat(all_data, ignore_index=True)
            else:
                self.data = pd.DataFrame()

            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Store file information
            self.file_info = {
                'file_info': {
                    'filename': filename,
                    'processed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                },
                'processing_info': {
                    'total_sheets': sheet_count,
                    'total_rows': len(self.data),
                    'time_taken': f"{processing_time:.2f} seconds"
                },
                'sheet_data': dict(sheet_data_counts)  # Changed from vehicle_types to sheet_data
            }

            return True

        except Exception as e:
            print(f"Error processing Excel file: {str(e)}")
            self.data = None
            self.file_info = {
                'error': f"Failed to process file: {str(e)}",
                'file_info': {'filename': filename},
                'processing_info': {'total_sheets': 0, 'total_rows': 0, 'time_taken': '0 seconds'},
                'sheet_data': {}  # Changed from vehicle_types to sheet_data
            }
            return False

    def get_data(self):
        return self.data

    def get_file_info(self):
        return self.file_info
