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
        super().__init__(domain_config)
        self.log_manager.log("Created new VehicleFault instance")
        
    def validate(self) -> bool:
        """
        Validate the vehicle fault entity.
        
        Returns:
            bool: True if valid, False otherwise
        """
        required_attrs = ['work_order', 'date', 'description']
        self.log_manager.log(f"Validating VehicleFault with required attributes: {required_attrs}")
        
        # Check required attributes
        for attr in required_attrs:
            if not self.get_attribute(attr):
                self.log_manager.log(f"Validation failed: Missing required attribute '{attr}'")
                return False
        
        # Validate datetime fields
        datetime_fields = ['date', 'completion_date', 'actual_finish_date']
        for field in datetime_fields:
            date_str = self.get_attribute(field)
            if date_str:
                try:
                    if isinstance(date_str, str):
                        datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                        self.log_manager.log(f"{field} validation successful")
                except ValueError:
                    self.log_manager.log(f"{field} validation failed for value: {date_str}")
                    return False
        
        # Validate cost if present
        cost = self.get_attribute('cost')
        if cost is not None:
            try:
                float(cost)
                self.log_manager.log("Cost validation successful")
            except ValueError:
                self.log_manager.log(f"Cost validation failed for value: {cost}")
                return False
        
        # Validate mileage if present
        mileage = self.get_attribute('mileage')
        if mileage is not None:
            try:
                int(mileage)
                self.log_manager.log("Mileage validation successful")
            except ValueError:
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
