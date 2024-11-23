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
    
    # Define valid columns for the vehicle fault data
    _required_columns = [
        'fault_id',
        'vehicle_id',
        'fault_description',
        'severity',
        'timestamp',
        'status'
    ]

    def __init__(self, *args, **kwargs):
        """Initialize the VehicleFault DataFrame with required columns."""
        super().__init__(*args, **kwargs)
        self._validate_columns()

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
    def from_excel(cls, excel_path: str, sheet_name: Optional[str] = None) -> 'VehicleFault':
        """
        Create a VehicleFault DataFrame from an Excel file.
        
        Args:
            excel_path (str): Path to the Excel file
            sheet_name (str, optional): Name of the sheet to read. Defaults to None (first sheet)
        
        Returns:
            VehicleFault: A new VehicleFault DataFrame
        """
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
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
        """Return all active (open) faults."""
        return self[self['status'] == 'open']

    def get_vehicle_history(self, vehicle_id: str) -> 'VehicleFault':
        """
        Get the fault history for a specific vehicle.
        
        Args:
            vehicle_id (str): ID of the vehicle
        
        Returns:
            VehicleFault: DataFrame containing fault history for the vehicle
        """
        return self[self['vehicle_id'] == vehicle_id].sort_values('timestamp')

    def get_faults_by_severity(self, severity: Union[str, List[str]]) -> 'VehicleFault':
        """
        Get faults filtered by severity level(s).
        
        Args:
            severity (str or list): Severity level(s) to filter by
        
        Returns:
            VehicleFault: DataFrame containing faults of specified severity
        """
        if isinstance(severity, str):
            severity = [severity]
        return self[self['severity'].isin(severity)]

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

    def get_fault_statistics(self) -> pd.DataFrame:
        """
        Generate statistics about faults.
        
        Returns:
            DataFrame: Statistics about faults including counts by severity and status
        """
        stats = pd.DataFrame({
            'total_faults': [len(self)],
            'active_faults': [len(self.get_active_faults())],
            'high_severity': [len(self.get_faults_by_severity('high'))],
            'medium_severity': [len(self.get_faults_by_severity('medium'))],
            'low_severity': [len(self.get_faults_by_severity('low'))]
        })
        return stats

    def to_excel(self, excel_path: str, sheet_name: str = 'Vehicle Faults') -> None:
        """
        Save the fault data to an Excel file.
        
        Args:
            excel_path (str): Path to save the Excel file
            sheet_name (str, optional): Name of the sheet. Defaults to 'Vehicle Faults'
        """
        super().to_excel(excel_path, sheet_name=sheet_name, index=False)
