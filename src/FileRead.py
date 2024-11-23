"""
Utility module for file operations, providing functions for secure file reading and validation.
Ensures safe handling of uploaded files.
Author: Chris Yeo
"""

import os
from werkzeug.utils import secure_filename
from VehicleFaults import VehicleFault
import pandas as pd

ALLOWED_EXTENSIONS = {'pdf', 'xlsx', 'xls'}
UPLOAD_FOLDER = 'uploads'

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def setup_upload_folder():
    upload_path = os.path.join(os.getcwd(), UPLOAD_FOLDER)
    if not os.path.exists(upload_path):
        os.makedirs(upload_path)
    return upload_path

def handle_file_upload(file):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        upload_path = setup_upload_folder()
        filepath = os.path.join(upload_path, filename)
        file.save(filepath)
        
        # Check if the file is an Excel file containing fault data
        if filename.endswith(('.xlsx', '.xls')):
            try:
                # Attempt to load as vehicle fault data
                df = pd.read_excel(filepath)
                if all(col in df.columns for col in VehicleFault._required_columns):
                    fault_data = VehicleFault(df)
                    return {
                        'success': True,
                        'filename': filename,
                        'message': f'File {filename} uploaded successfully as vehicle fault data',
                        'is_fault_data': True
                    }
            except Exception as e:
                pass  # Not a fault data file, proceed with normal upload
        
        return {
            'success': True,
            'filename': filename,
            'message': f'File {filename} uploaded successfully',
            'is_fault_data': False
        }
    return {
        'success': False,
        'message': 'Invalid file type. Only PDF and Excel files are allowed.'
    }

def load_fault_data(filepath):
    """
    Load vehicle fault data from an Excel file.
    
    Args:
        filepath (str): Path to the Excel file
        
    Returns:
        tuple: (VehicleFault object, dict with success status and message)
    """
    try:
        fault_data = VehicleFault.from_excel(filepath)
        return fault_data, {
            'success': True,
            'message': 'Fault data loaded successfully'
        }
    except ValueError as ve:
        return None, {
            'success': False,
            'message': f'Invalid fault data format: {str(ve)}'
        }
    except Exception as e:
        return None, {
            'success': False,
            'message': f'Error loading fault data: {str(e)}'
        }
