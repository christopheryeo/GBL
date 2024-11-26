"""
Utility module for file operations, providing functions for secure file reading and validation.
Ensures safe handling of uploaded files.
Author: Chris Yeo
"""

import os
from werkzeug.utils import secure_filename
from VehicleFaults import VehicleFault
import pandas as pd
from config.TestConfig import test_config
from processors.processor_factory import ProcessorFactory

ALLOWED_EXTENSIONS = {'pdf', 'xlsx', 'xls'}
UPLOAD_FOLDER = 'uploads'

class FileReader:
    """Class to handle file reading operations with configuration."""
    
    def __init__(self, log_manager=None):
        """Initialize FileReader with optional log manager."""
        self.log_manager = log_manager
        self.upload_path = self.setup_upload_folder()

    def log(self, message):
        """Log a message if log manager is available."""
        if self.log_manager:
            self.log_manager.info(message)

    @staticmethod
    def allowed_file(filename):
        """Check if the file extension is allowed."""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    @staticmethod
    def setup_upload_folder():
        """Create and return upload folder path."""
        upload_path = os.path.join(os.getcwd(), UPLOAD_FOLDER)
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)
        return upload_path

    def handle_file_upload(self, file):
        """Handle file upload with proper validation."""
        if file and self.allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(self.upload_path, filename)
            file.save(filepath)
            
            # Check if the file is an Excel file
            if filename.endswith(('.xlsx', '.xls')):
                try:
                    # Detect the format type
                    format_type = ProcessorFactory.detect_format(filepath)
                    return {
                        'success': True,
                        'filename': filename,
                        'message': f'File {filename} uploaded successfully',
                        'is_kardex_data': format_type == 'kardex'
                    }
                except Exception as e:
                    return {
                        'success': False,
                        'filename': filename,
                        'message': f'Error processing Excel file: {str(e)}'
                    }
            
            return {
                'success': True,
                'filename': filename,
                'message': f'File {filename} uploaded successfully',
                'is_kardex_data': False
            }
        return {
            'success': False,
            'message': 'Invalid file type. Only PDF and Excel files are allowed.'
        }

    def load_kardex_data(self, filepath, file_key=None):
        """
        Load Kardex data from an Excel file using configuration.
        
        Args:
            filepath (str): Path to the Excel file
            file_key (str, optional): Key of Excel file in configuration.
                                    If None, uses default from test_config
            
        Returns:
            tuple: (DataFrame, vehicle_type, dict with success status and message)
        """
        try:
            # Detect which Kardex format this is
            format_type = ProcessorFactory.detect_format(filepath)
            if format_type != 'kardex':
                raise ValueError("This file is not in Kardex format")
            
            # If no file_key provided, use default from test_config
            if file_key is None:
                file_key = test_config.get_default_kardex()
            
            # Create processor for this format
            processor = ProcessorFactory.create(format_type, file_key)
            
            # Process the data
            df = processor.process(filepath)
            
            # Get vehicle type from sheet name
            vehicle_type = df['Vehicle Type'].iloc[0] if 'Vehicle Type' in df.columns else 'Unknown'
            
            return df, vehicle_type, {
                'success': True,
                'message': 'Successfully loaded Kardex data'
            }
            
        except Exception as e:
            self.log(f"Error loading Kardex data: {str(e)}")
            return None, None, {
                'success': False,
                'message': f'Error loading Kardex data: {str(e)}'
            }

    def load_fault_data(self, filepath):
        """
        Load vehicle fault data from an Excel file.
        
        Args:
            filepath (str): Path to the Excel file
            
        Returns:
            tuple: (VehicleFault object, dict with success status and message)
        """
        try:
            vehicle_fault = VehicleFault(filepath)
            return vehicle_fault, {
                'success': True,
                'message': 'Successfully loaded fault data'
            }
        except Exception as e:
            self.log(f"Error loading fault data: {str(e)}")
            return None, {
                'success': False,
                'message': f'Error loading fault data: {str(e)}'
            }
