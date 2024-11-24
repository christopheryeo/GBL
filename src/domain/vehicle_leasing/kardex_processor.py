"""
Kardex Excel file processor for the vehicle leasing domain.
"""
from typing import Any, Dict, List
import pandas as pd
from ..base.base_processor import BaseProcessor
from .vehicle_fault import VehicleFault

class KardexProcessor(BaseProcessor):
    """Processor for Kardex Excel files in the vehicle leasing domain."""
    
    def __init__(self):
        """Initialize Kardex processor with vehicle leasing domain configuration."""
        super().__init__('vehicle_leasing', 'kardex')
        self.log_manager.log("Initialized KardexProcessor")
        
    def process(self, excel_file: str) -> List[Dict[str, Any]]:
        """
        Process Kardex Excel file and create vehicle fault entities.
        
        Args:
            excel_file: Path to the Kardex Excel file
            
        Returns:
            List of processed vehicle faults as dictionaries
        """
        self.log_manager.log(f"Processing Kardex Excel file: {excel_file}")
        
        # Read Excel file
        try:
            df = pd.read_excel(excel_file, sheet_name=self.config['format_config'].get('sheet_name', 'Sheet1'))
            self.log_manager.log(f"Successfully read Excel file with {len(df)} rows")
        except Exception as e:
            self.log_manager.log(f"Error reading Excel file: {str(e)}")
            raise
        
        # Validate format
        self.validate_format(df)
        
        # Process each row
        faults = []
        for idx, row in df.iterrows():
            self.log_manager.log(f"Processing row {idx + 1}")
            fault = VehicleFault(self.config['domain_config'])
            
            # Map Excel columns to fault attributes
            for column in self.config['format_config']['columns']:
                excel_name = column['name']
                internal_key = column['key']
                if excel_name in row:
                    fault.set_attribute(internal_key, row[excel_name])
            
            # Apply transformations
            self._apply_transformations(fault)
            
            # Validate fault
            if fault.validate():
                faults.append(fault.to_dict())
                self.log_manager.log(f"Successfully processed fault from row {idx + 1}")
            else:
                self.log_manager.log(f"Warning: Skipped invalid fault from row {idx + 1}")
                
        self.log_manager.log(f"Completed processing {len(faults)} valid faults from {len(df)} rows")
        return faults
    
    def _apply_transformations(self, fault: VehicleFault) -> None:
        """
        Apply configured transformations to the fault entity.
        
        Args:
            fault: VehicleFault entity to transform
        """
        transformations = self.config['format_config'].get('transformations', [])
        self.log_manager.log(f"Applying transformations: {transformations}")
        
        for transform in transformations:
            self.log_manager.log(f"Applying transformation: {transform}")
            if transform == 'clean_work_order':
                self._clean_work_order(fault)
            elif transform == 'format_dates':
                self._format_dates(fault)
            elif transform == 'clean_description':
                self._clean_description(fault)
    
    def _clean_work_order(self, fault: VehicleFault) -> None:
        """Clean work order number."""
        wo = fault.get_attribute('work_order')
        if wo:
            # Remove any whitespace and special characters
            original = wo
            wo = ''.join(c for c in wo if c.isalnum())
            if wo != original:
                self.log_manager.log(f"Cleaned work order from '{original}' to '{wo}'")
            fault.set_attribute('work_order', wo)
    
    def _format_dates(self, fault: VehicleFault) -> None:
        """Format dates to standard format."""
        date = fault.get_attribute('date')
        if isinstance(date, pd.Timestamp):
            original = str(date)
            formatted = date.strftime('%Y-%m-%d')
            self.log_manager.log(f"Formatted date from '{original}' to '{formatted}'")
            fault.set_attribute('date', formatted)
    
    def _clean_description(self, fault: VehicleFault) -> None:
        """Clean and standardize fault description."""
        desc = fault.get_attribute('description')
        if desc:
            # Remove extra whitespace and standardize
            original = desc
            desc = ' '.join(desc.split())
            if desc != original:
                self.log_manager.log(f"Cleaned description from '{original}' to '{desc}'")
            fault.set_attribute('description', desc)
            
            # Try to determine component and severity from description
            desc_lower = desc.lower()
            
            # Simple component detection (can be enhanced)
            components = ['engine', 'brake', 'transmission', 'tire', 'battery']
            for component in components:
                if component in desc_lower:
                    self.log_manager.log(f"Detected component '{component}' from description")
                    fault.set_component(component)
                    break
            
            # Simple severity detection (can be enhanced)
            if any(word in desc_lower for word in ['urgent', 'emergency', 'critical']):
                severity = 'high'
            elif any(word in desc_lower for word in ['routine', 'regular', 'normal']):
                severity = 'low'
            else:
                severity = 'medium'
            self.log_manager.log(f"Set severity to '{severity}' based on description")
            fault.set_severity(severity)
