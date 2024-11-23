"""
Vehicle Faults data structure extending Pandas DataFrame.
Provides specialized methods for vehicle fault analysis and processing.
Author: Chris Yeo
"""

import pandas as pd
from typing import Optional, Union, List
import numpy as np
from datetime import datetime

class VehicleFault(pd.DataFrame):
    """
    A specialized DataFrame for handling vehicle fault data.
    Inherits from pandas DataFrame and adds vehicle-specific functionality.
    """
    
    # Define valid columns for the vehicle fault data based on Kardex Excel format
    _required_columns = [
        'WO No',
        'Loc',
        'ST',
        'Mileage',
        'Open Date',
        'Done Date',
        'Actual Finish Date',
        'Nature of Complaint',
        'Fault Codes',
        'Job Description',
        'SRR No.',
        'Mechanic Name',
        'Customer',
        'Customer Name',
        'Recommendation 4 next',
        'Cat',
        'Lead Tech',
        'Bill No.',
        'Intercoamt',
        'Custamt',
        'FaultCategory'  # New column for categorizing faults
    ]

    def __init__(self, *args, **kwargs):
        """Initialize the VehicleFault DataFrame with required columns."""
        super().__init__(*args, **kwargs)
        self._validate_columns()
        if 'FaultCategory' not in self.columns:
            self['FaultCategory'] = self._categorize_faults()

    @property
    def _constructor(self):
        """Return the class constructor for pandas operations."""
        return VehicleFault

    def _validate_columns(self) -> None:
        """Validate that all required columns are present."""
        missing_cols = [col for col in self._required_columns if col not in self.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

    @classmethod
    def from_excel(cls, filepath: str) -> 'VehicleFault':
        """
        Create a VehicleFault object from an Excel file.
        
        Args:
            filepath (str): Path to the Excel file
            
        Returns:
            VehicleFault: New VehicleFault object with data from Excel
        """
        # Skip the first 3 rows which contain header information
        df = pd.read_excel(filepath, skiprows=3)
        return cls(df)

    def add_fault(self, vehicle_id: str, fault_description: str, 
                 severity: str, status: str = 'open') -> None:
        """
        Add a new fault entry to the DataFrame.
        
        Args:
            vehicle_id (str): ID of the vehicle
            fault_description (str): Description of the fault
            severity (str): Severity level of the fault
            status (str, optional): Current status of the fault. Defaults to 'open'
        """
        new_fault = {
            'fault_id': self._generate_fault_id(),
            'vehicle_id': vehicle_id,
            'fault_description': fault_description,
            'severity': severity,
            'timestamp': datetime.now(),
            'status': status
        }
        self.loc[len(self)] = new_fault

    def _generate_fault_id(self) -> str:
        """Generate a unique fault ID."""
        if len(self) == 0:
            return 'F001'
        last_id = self['fault_id'].iloc[-1]
        num = int(last_id[1:]) + 1
        return f'F{num:03d}'

    def get_active_faults(self) -> 'VehicleFault':
        """Get all active (unfinished) faults."""
        return self[self['Done Date'].isna()]

    def get_vehicle_history(self, vehicle_id: str) -> 'VehicleFault':
        """
        Get fault history for a specific vehicle.
        
        Args:
            vehicle_id (str): Vehicle ID to get history for
            
        Returns:
            VehicleFault: Filtered fault data for the specified vehicle
        """
        # Extract vehicle ID from the first row (title)
        return self[self.iloc[0, 0].startswith(vehicle_id)]

    def get_faults_by_category(self, category: str) -> 'VehicleFault':
        """
        Filter faults by category.
        
        Args:
            category (str): Category to filter by
            
        Returns:
            VehicleFault: Filtered fault data for the specified category
        """
        return self[self['Cat'] == category]

    def _categorize_faults(self) -> pd.Series:
        """
        Automatically categorize faults based on Nature of Complaint and Job Description.
        Returns a pandas Series with fault categories.
        
        Categories include:
        - Engine
        - Transmission
        - Electrical
        - Brakes
        - Suspension
        - Body
        - Maintenance
        - Other
        """
        categories = pd.Series(index=self.index, data='Other')  # Default category
        
        # Define keywords for each category
        category_keywords = {
            'Engine': ['engine', 'motor', 'cylinder', 'piston', 'fuel', 'oil leak', 'coolant'],
            'Transmission': ['transmission', 'gear', 'clutch', 'differential'],
            'Electrical': ['battery', 'electrical', 'wire', 'fuse', 'light', 'sensor'],
            'Brakes': ['brake', 'abs', 'rotor', 'pad'],
            'Suspension': ['suspension', 'shock', 'strut', 'spring', 'steering', 'wheel', 'tire'],
            'Body': ['body', 'door', 'window', 'paint', 'dent', 'scratch'],
            'Maintenance': ['service', 'maintenance', 'inspection', 'oil change', 'filter']
        }
        
        # Combine Nature of Complaint and Job Description for better categorization
        combined_text = (self['Nature of Complaint'].str.lower().fillna('') + ' ' + 
                        self['Job Description'].str.lower().fillna(''))
        
        # Categorize based on keywords
        for category, keywords in category_keywords.items():
            mask = combined_text.str.contains('|'.join(keywords), na=False)
            categories[mask] = category
            
        return categories

    def get_fault_statistics(self) -> dict:
        """Get statistics about vehicle faults including the new FaultCategory."""
        stats = {
            'total_records': len(self),
            'active_faults': len(self.get_active_faults()),
            'unique_locations': self['Loc'].nunique(),
            'avg_mileage': self['Mileage'].mean(),
            'categories': self['Cat'].value_counts().to_dict(),
            'complaints_by_type': self['Nature of Complaint'].value_counts().to_dict(),
            'total_intercost': self['Intercoamt'].sum(),
            'total_custcost': self['Custamt'].sum(),
            'fault_categories': self['FaultCategory'].value_counts().to_dict()
        }
        return stats

    def to_excel(self, filepath: str) -> None:
        """
        Save the fault data to an Excel file.
        
        Args:
            filepath (str): Path to save the Excel file
        """
        # Add vehicle information as header
        writer = pd.ExcelWriter(filepath, engine='openpyxl')
        self.to_excel(writer, index=False, startrow=3)
        writer.save()

    def close_fault(self, fault_id: str) -> None:
        """
        Mark a fault as closed.
        
        Args:
            fault_id (str): ID of the fault to close
        """
        if fault_id in self['fault_id'].values:
            self.loc[self['fault_id'] == fault_id, 'status'] = 'closed'
        else:
            raise ValueError(f"Fault ID {fault_id} not found")
