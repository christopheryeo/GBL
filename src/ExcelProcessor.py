"""
Core Excel processing module that handles Excel file parsing, data extraction, and analytics generation.
Provides structured data output for visualization and analysis.
Author: Chris Yeo
"""

import pandas as pd
import time
from datetime import datetime
from collections import Counter
from VehicleFaults import VehicleFault

class ExcelProcessor:
    def __init__(self, log_manager=None):
        """Initialize the ExcelProcessor with an optional log manager."""
        self.data = None
        self.fault_data = None
        self.file_info = None
        self.processing_info = None
        self.sheet_counts = {}
        self.log_manager = log_manager

    def log(self, message):
        """Log a message using the log manager if available."""
        if self.log_manager:
            self.log_manager.log(message)

    def _extract_vehicle_type(self, sheet_name):
        """Extract vehicle type from sheet name."""
        try:
            # Remove the '(6yrs)' suffix and trim
            vehicle_type = sheet_name.split('(')[0].strip()
            if not vehicle_type:
                return "Unknown"
            return vehicle_type
        except Exception as e:
            self.log(f"Error extracting vehicle type: {str(e)}")
            return "Unknown"

    def _find_header_row(self, sheet):
        """Find the header row containing 'WO No' and return its index."""
        for idx, row in sheet.iterrows():
            if any('WO No' in str(val) for val in row):
                return idx
        return None

    def process_excel(self, file_path, filename):
        start_time = time.time()
        self.log(f"Starting Excel processing for file: {filename}")
        
        try:
            # Read all sheets from the Excel file
            excel_file = pd.ExcelFile(file_path)
            processed_sheets = []
            sheet_count = len(excel_file.sheet_names)
            self.log(f"Found {sheet_count} sheets in the Excel file: {', '.join(excel_file.sheet_names)}")
            sheet_data_counts = Counter()
            
            for sheet_name in excel_file.sheet_names:
                vehicle_type = self._extract_vehicle_type(sheet_name)
                self.log(f"Processing sheet: {sheet_name} (Vehicle Type: {vehicle_type})")
                
                # First read without headers to find the correct header row
                temp_df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
                header_idx = self._find_header_row(temp_df)
                
                if header_idx is not None:
                    # Read the sheet again with the correct header row
                    df = pd.read_excel(file_path, sheet_name=sheet_name, header=header_idx)
                    # Clean column names
                    df.columns = [str(col).strip() for col in df.columns]
                    
                    # Process the sheet data
                    processed_df = self._process_sheet(df, vehicle_type)
                    if not processed_df.empty:
                        processed_sheets.append(processed_df)
                        sheet_data_counts[sheet_name] = len(processed_df)
                        self.log(f"Successfully processed {len(processed_df)} records from sheet {sheet_name}")
                else:
                    self.log(f"No valid header row found in sheet {sheet_name}")
                    sheet_data_counts[sheet_name] = 0
            
            # Combine all processed sheets
            if processed_sheets:
                self.data = pd.concat(processed_sheets, ignore_index=True)
                total_rows = len(self.data)
            else:
                self.data = pd.DataFrame()
                total_rows = 0
            
            # Calculate processing time
            end_time = time.time()
            processing_time = round(end_time - start_time, 2)
            
            # Update file info
            self.file_info = {
                'filename': filename,
                'processing_info': {
                    'total_sheets': sheet_count,
                    'total_rows': total_rows,
                    'time_taken': f"{processing_time} seconds"
                },
                'sheet_data': dict(sheet_data_counts)
            }
            
            self.log(f"Processing completed. Total rows: {total_rows}")
            
            # Return both file info and data
            return {
                'file_info': self.file_info,
                'data': self.data.to_dict('records') if not self.data.empty else []
            }

        except Exception as e:
            self.log(f"Critical error during Excel processing: {str(e)}")
            self.data = None
            self.file_info = {
                'error': f"Failed to process file: {str(e)}",
                'file_info': {'filename': filename},
                'processing_info': {'total_sheets': 0, 'total_rows': 0, 'time_taken': '0 seconds'},
                'sheet_data': {}
            }
            return None

    def _process_sheet(self, sheet, vehicle_type):
        try:
            self.log(f"Starting sheet processing for vehicle type: {vehicle_type}")
            
            # Get the actual number of columns in the sheet
            num_cols = len(sheet.columns)
            self.log(f"Found {num_cols} columns in sheet")
            
            # Create DataFrame from the sheet (headers are already set from read_excel)
            df = sheet.copy()
            
            # Reset the index to make sure we have clean row numbers
            df = df.reset_index(drop=True)
            
            # Basic data cleaning
            self.log("Performing basic data cleaning...")
            df = df.replace({pd.NA: None, pd.NaT: None})
            df = df.dropna(how='all')
            
            if df.empty:
                self.log("No valid data found after cleaning")
                return pd.DataFrame()
            
            self.log(f"Processing {len(df)} records...")
            
            # Add vehicle type from sheet name (remove the ' (6yrs)' suffix)
            sheet_vehicle_type = vehicle_type.split(' (')[0] if ' (' in vehicle_type else vehicle_type
            df['Vehicle Category'] = sheet_vehicle_type
            
            # Process dates - assuming standard Kardex format
            try:
                date_columns = ['Open Date', 'Completion Date', 'Last Update']
                for col in date_columns:
                    if col in df.columns:
                        df[col] = pd.to_datetime(df[col], errors='coerce')
                        self.log(f"Processed {col} column")
            except Exception as e:
                self.log(f"Error processing date columns: {str(e)}")
            
            # Ensure all required columns exist
            required_columns = [
                'WO No', 'Status', 'Vehicle Type', 'Vehicle No',
                'Open Date', 'Completion Date', 'Last Update',
                'Nature of Complaint', 'Job Description', 'Description',
                'Customer No', 'Customer Name', 'Category'
            ]
            
            # Add any missing columns with None values
            for col in required_columns:
                if col not in df.columns:
                    df[col] = None
                    self.log(f"Added missing column: {col}")
            
            self.log(f"Successfully processed sheet with {len(df)} records")
            return df
            
        except Exception as e:
            self.log(f"Error in _process_sheet: {str(e)}")
            return pd.DataFrame()

    def get_data(self):
        return self.data

    def get_file_info(self):
        return self.file_info

    def process_fault_data(self, file_path, filename):
        """
        Process Excel file specifically for vehicle fault data.
        
        Args:
            file_path (str): Path to the Excel file
            filename (str): Name of the file
            
        Returns:
            bool: True if processing was successful, False otherwise
        """
        start_time = time.time()
        self.log(f"Starting fault data processing for file: {filename}")
        
        try:
            # Create VehicleFault object from Excel file
            self.fault_data = VehicleFault.from_excel(file_path)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Store file information
            self.file_info = {
                'file_info': {
                    'filename': filename,
                    'processed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'data_type': 'vehicle_faults'
                },
                'processing_info': {
                    'total_faults': len(self.fault_data),
                    'active_faults': len(self.fault_data.get_active_faults()),
                    'time_taken': f"{processing_time:.2f} seconds"
                },
                'fault_statistics': self.fault_data.get_fault_statistics()
            }
            
            self.log(f"Fault data processing completed in {processing_time:.2f} seconds")
            
            return True
            
        except Exception as e:
            self.log(f"Critical error during fault data processing: {str(e)}")
            self.fault_data = None
            self.file_info = {
                'error': f"Failed to process fault data: {str(e)}",
                'file_info': {'filename': filename},
                'processing_info': {'total_faults': 0, 'active_faults': 0, 'time_taken': '0 seconds'},
                'fault_statistics': {}
            }
            return False

    def get_fault_data(self):
        """
        Get the processed fault data.
        
        Returns:
            VehicleFault: The processed fault data or None if no fault data has been processed
        """
        return self.fault_data

    def get_fault_summary(self):
        """
        Get a summary of the fault data including statistics and active faults.
        
        Returns:
            dict: Summary of fault data or None if no fault data has been processed
        """
        if self.fault_data is None:
            return None
            
        active_faults = self.fault_data.get_active_faults()
        high_severity = self.fault_data.get_faults_by_severity('high')
        
        return {
            'total_faults': len(self.fault_data),
            'active_faults': len(active_faults),
            'high_severity_faults': len(high_severity),
            'statistics': self.fault_data.get_fault_statistics()
        }
