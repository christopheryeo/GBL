"""
Vehicle Faults data structure extending Pandas DataFrame.
Provides specialized methods for vehicle fault analysis and processing.
Author: Chris Yeo
"""

import pandas as pd
from typing import Optional, Union, List
import numpy as np
from datetime import datetime
import yaml
import os

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
        'Custamt'
    ]

    def __init__(self, *args, **kwargs):
        """Initialize the VehicleFault DataFrame with required columns."""
        super().__init__(*args, **kwargs)
        self._validate_columns()
        # Always generate FaultCategory regardless of whether it exists
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
        
        Categories are loaded from config/fault_categories.yaml and include:
        - Engine: Engine and related components
        - Transmission: Transmission and drivetrain
        - Electrical: Electrical systems and electronics
        - Brakes: Brake system components
        - Suspension: Suspension, steering, and wheels
        - Body: Vehicle body and cosmetic issues
        - HVAC: Heating, ventilation, and air conditioning
        - Maintenance: Regular maintenance and service
        - Exhaust: Exhaust system and emissions
        - Fuel: Fuel system components
        - Other: Uncategorized issues
        """
        categories = pd.Series(index=self.index, data='Other')  # Default category
        
        # Load category keywords from configuration file
        config_path = os.path.join(os.path.dirname(__file__), 'config', 'fault_categories.yaml')
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            category_keywords = config['fault_categories']
        
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
        Close a fault by setting its status to 'closed'.
        
        Args:
            fault_id (str): ID of the fault to close
        """
        idx = self[self['fault_id'] == fault_id].index
        if len(idx) > 0:
            self.loc[idx[0], 'status'] = 'closed'
            self.loc[idx[0], 'Done Date'] = datetime.now()

    def filter_records(self, criteria: dict = None, start_date: Union[str, datetime] = None, 
                      end_date: Union[str, datetime] = None, date_column: str = 'Open Date') -> 'VehicleFault':
        """
        Filter records based on multiple criteria and date range.
        
        Args:
            criteria (dict): Dictionary of column-value pairs to filter by
                Example: {'FaultCategory': 'Engine', 'Loc': 'Workshop A'}
            start_date (str or datetime): Start date for filtering (inclusive)
            end_date (str or datetime): End date for filtering (inclusive)
            date_column (str): Column to use for date filtering (default: 'Open Date')
                             Can be 'Open Date', 'Done Date', or 'Actual Finish Date'
        
        Returns:
            VehicleFault: Filtered DataFrame with matching records
            
        Example:
            # Filter engine faults from Workshop A between Jan 1 and Mar 31, 2023
            filtered_df = df.filter_records(
                criteria={'FaultCategory': 'Engine', 'Loc': 'Workshop A'},
                start_date='2023-01-01',
                end_date='2023-03-31'
            )
            print(f"Found {len(filtered_df)} matching records")
        """
        # Start with all records
        mask = pd.Series(True, index=self.index)
        
        # Apply criteria filters
        if criteria:
            for column, value in criteria.items():
                if column in self.columns:
                    if isinstance(value, (list, tuple)):
                        # Handle multiple values for a column
                        mask &= self[column].isin(value)
                    else:
                        # Handle single value
                        mask &= (self[column] == value)
        
        # Apply date range filter
        if date_column in self.columns and (start_date is not None or end_date is not None):
            # Convert string dates to datetime if necessary
            if isinstance(start_date, str):
                start_date = pd.to_datetime(start_date)
            if isinstance(end_date, str):
                end_date = pd.to_datetime(end_date)
            
            # Convert column to datetime if it's not already
            date_series = pd.to_datetime(self[date_column])
            
            # Apply date filters
            if start_date is not None:
                mask &= (date_series >= start_date)
            if end_date is not None:
                mask &= (date_series <= end_date)
        
        # Return filtered DataFrame
        return self[mask]

    def get_filtered_count(self, criteria: dict = None, start_date: Union[str, datetime] = None, 
                         end_date: Union[str, datetime] = None, date_column: str = 'Open Date') -> int:
        """
        Get the count of records matching the specified criteria and date range.
        
        Args:
            Same as filter_records method
        
        Returns:
            int: Number of matching records
            
        Example:
            # Count engine faults from Workshop A between Jan 1 and Mar 31, 2023
            count = df.get_filtered_count(
                criteria={'FaultCategory': 'Engine', 'Loc': 'Workshop A'},
                start_date='2023-01-01',
                end_date='2023-03-31'
            )
            print(f"Found {count} matching records")
        """
        filtered_df = self.filter_records(criteria, start_date, end_date, date_column)
        return len(filtered_df)
