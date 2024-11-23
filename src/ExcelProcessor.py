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
    def __init__(self):
        self.data = None
        self.fault_data = None
        self.file_info = None
        self.processing_info = None
        self.sheet_counts = {}
        # Remove circular import
        self.log_manager = None

    def set_log_manager(self, log_manager):
        self.log_manager = log_manager

    def log(self, message):
        if self.log_manager:
            self.log_manager.log(message)

    def _extract_vehicle_type(self, sheet):
        try:
            # Get the vehicle type from the third row (index 2)
            vehicle_type = sheet.iloc[2, 0]  # Assuming it's in the first column
            if pd.isna(vehicle_type) or not isinstance(vehicle_type, str):
                return "Unknown"
            return vehicle_type.strip()
        except Exception as e:
            self.log(f"Error extracting vehicle type: {str(e)}")
            return "Unknown"

    def process_excel(self, file_path, filename):
        start_time = time.time()
        self.log(f"Starting Excel processing for file: {filename}")
        
        try:
            # Read all sheets from the Excel file
            excel_file = pd.ExcelFile(file_path)
            processed_sheets = []
            sheet_count = len(excel_file.sheet_names)
            self.log(f"Found {sheet_count} sheets in the Excel file")
            sheet_data_counts = Counter()

            for sheet_name in excel_file.sheet_names:
                self.log(f"Processing sheet: {sheet_name}")
                # Read the sheet
                sheet = pd.read_excel(excel_file, sheet_name=sheet_name)
                
                if sheet.empty:
                    self.log(f"Sheet '{sheet_name}' is empty")
                    sheet_data_counts[sheet_name] = 0
                    continue

                # Extract vehicle type from the third row
                vehicle_type = self._extract_vehicle_type(sheet)
                self.log(f"Vehicle type identified for sheet '{sheet_name}': {vehicle_type}")

                # Process the sheet data
                try:
                    self.log(f"Starting DataFrame creation for sheet '{sheet_name}'")
                    processed_data = self._process_sheet_data(sheet, vehicle_type, sheet_name)
                    if processed_data is not None:
                        processed_sheets.append(processed_data)
                        sheet_data_counts[sheet_name] = len(processed_data)
                        self.log(f"Successfully processed {len(processed_data)} records from sheet '{sheet_name}'")
                    else:
                        self.log(f"No valid data found in sheet '{sheet_name}'")
                except Exception as e:
                    self.log(f"Error processing sheet '{sheet_name}': {str(e)}")
                    continue

            # Combine all data into a single DataFrame
            if processed_sheets:
                self.log("Creating DataFrame from processed data")
                self.data = pd.concat(processed_sheets, ignore_index=True)
                self.log(f"Successfully created DataFrame with {len(self.data)} records")
            else:
                self.log("No valid data found in any sheets")
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
                'sheet_data': dict(sheet_data_counts)
            }

            self.log(f"Excel processing completed in {processing_time:.2f} seconds")
            
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

    def _process_sheet_data(self, sheet, vehicle_type, sheet_name):
        try:
            self.log("Starting DataFrame validation and cleaning")
            # Skip the first 4 rows (headers and vehicle type)
            data = sheet.iloc[4:].copy()
            
            if not data.empty:
                # Add vehicle_type and sheet_name columns
                data['vehicle_type'] = vehicle_type
                data['sheet_name'] = sheet_name
                self.log(f"DataFrame processing completed. Processed {len(data)} rows")
                return data
            else:
                self.log("No valid data found in the sheet")
                return None
        except Exception as e:
            self.log(f"Error in DataFrame processing: {str(e)}")
            return None

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
