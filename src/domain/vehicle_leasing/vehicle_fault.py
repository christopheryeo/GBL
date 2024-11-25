"""
Vehicle fault entity for the vehicle leasing domain.
"""
from typing import Any, Dict, Optional
from datetime import datetime
from ..base.base_entity import BaseEntity

class VehicleFault(BaseEntity):
    """Entity representing a vehicle fault in the leasing system."""
    
    def __init__(self, domain_config: Dict[str, Any]):
        """
        Initialize vehicle fault with domain configuration.
        
        Args:
            domain_config: Configuration dictionary containing domain-specific settings
        """
        # Ensure domain_config has the required structure
        if not isinstance(domain_config, dict):
            domain_config = {'fault_attributes': []}
            
        if 'domains' in domain_config:
            # Extract vehicle_leasing domain config
            domain_config = domain_config.get('domains', {}).get('vehicle_leasing', {})
            
        super().__init__(domain_config)
        
        # Initialize required attributes
        required_attrs = ['work_order', 'date', 'description', 'nature_of_complaint']
        for attr in required_attrs:
            if attr not in self.attributes:
                self.attributes[attr] = None
                
        self.log_manager.log("Created new VehicleFault instance")
        
    def validate(self) -> bool:
        """Validate the fault entity.
        
        Returns:
            True if validation passes, False otherwise
            
        Raises:
            ValueError: If date format is invalid
        """
        # Required attributes
        required_attrs = ['work_order', 'date', 'description']
        self.log_manager.log(f"Validating VehicleFault with required attributes: {required_attrs}")
        
        for attr in required_attrs:
            if not self.get_attribute(attr):
                self.log_manager.log(f"Missing required attribute: {attr}")
                return False
        
        # Validate date format
        date = self.get_attribute('date')
        if date:
            if isinstance(date, str):
                try:
                    datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
                    self.log_manager.log("date validation successful")
                except ValueError:
                    self.log_manager.log(f"date validation failed for value: {date}")
                    raise ValueError(f"Invalid date format: {date}. Expected format: YYYY-MM-DD HH:MM:SS")
            elif not isinstance(date, datetime):
                self.log_manager.log(f"date validation failed for value: {date}")
                raise ValueError(f"Invalid date type: {type(date)}. Expected str or datetime")
        
        # Validate cost is numeric if present
        cost = self.get_attribute('cost')
        if cost is not None:
            try:
                float(cost)
                self.log_manager.log("Cost validation successful")
            except (ValueError, TypeError):
                self.log_manager.log(f"Cost validation failed for value: {cost}")
                return False
                
        # Validate mileage is numeric if present
        mileage = self.get_attribute('mileage')
        if mileage is not None:
            try:
                int(mileage)
                self.log_manager.log("Mileage validation successful")
            except (ValueError, TypeError):
                self.log_manager.log(f"Mileage validation failed for value: {mileage}")
                return False
                
        self.log_manager.log("VehicleFault validation successful")
        return True
    
    def set_severity(self, severity: str) -> None:
        """
        Set the fault severity.
        
        Args:
            severity: Fault severity level
        """
        self.log_manager.log(f"Setting fault severity to: {severity}")
        self.set_attribute('severity', severity)
        
    def set_component(self, component: str) -> None:
        """
        Set the affected vehicle component.
        
        Args:
            component: Affected vehicle component
        """
        self.log_manager.log(f"Setting affected component to: {component}")
        self.set_attribute('component', component)
        
    def get_cost(self) -> float:
        """
        Get the fault repair cost.
        
        Returns:
            float: Repair cost, 0 if not set
        """
        cost = self.get_attribute('cost')
        try:
            value = float(cost) if cost is not None else 0.0
            self.log_manager.log(f"Retrieved cost value: {value}")
            return value
        except ValueError:
            self.log_manager.log(f"Failed to convert cost to float: {cost}")
            return 0.0
            
    def get_mileage(self) -> Optional[int]:
        """
        Get the vehicle mileage at time of fault.
        
        Returns:
            Optional[int]: Mileage value, None if not set or invalid
        """
        mileage = self.get_attribute('mileage')
        try:
            value = int(mileage) if mileage is not None else None
            self.log_manager.log(f"Retrieved mileage value: {value}")
            return value
        except ValueError:
            self.log_manager.log(f"Failed to convert mileage to int: {mileage}")
            return None
            
    def get_mechanic(self) -> Optional[str]:
        """
        Get the mechanic who worked on the fault.
        
        Returns:
            Optional[str]: Mechanic name, None if not set
        """
        mechanic = self.get_attribute('mechanic')
        self.log_manager.log(f"Retrieved mechanic: {mechanic}")
        return mechanic
        
    def get_completion_date(self) -> Optional[datetime]:
        """
        Get the date when the work was completed.
        
        Returns:
            Optional[datetime]: Completion date, None if not set or invalid
        """
        date_str = self.get_attribute('completion_date')
        try:
            if date_str and isinstance(date_str, str):
                value = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                self.log_manager.log(f"Retrieved completion date: {value}")
                return value
        except ValueError:
            self.log_manager.log(f"Failed to parse completion date: {date_str}")
        return None
        
    def get_component(self) -> Optional[str]:
        """
        Get the affected vehicle component.
        
        Returns:
            Optional[str]: Component name, None if not set
        """
        component = self.get_attribute('component')
        self.log_manager.log(f"Retrieved component: {component}")
        return component
        
    def get_severity(self) -> Optional[str]:
        """
        Get the fault severity.
        
        Returns:
            Optional[str]: Severity level, None if not set
        """
        severity = self.get_attribute('severity')
        self.log_manager.log(f"Retrieved severity: {severity}")
        return severity
