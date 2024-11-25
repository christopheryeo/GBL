"""
Base class for all domain-specific entities.
"""
from typing import Any, Dict
from abc import ABC, abstractmethod
from ...LogManager import LogManager

class BaseEntity(ABC):
    """Base class for all domain entities."""
    
    def __init__(self, domain_config: Dict[str, Any]):
        """
        Initialize base entity with domain configuration.
        
        Args:
            domain_config: Configuration dictionary containing domain-specific settings
        """
        self.attributes = {}
        self.domain_config = domain_config
        self.log_manager = LogManager()
        self.log_manager.log(f"Initialized {self.__class__.__name__} with domain config: {domain_config.get('name', 'Unknown')}")
        
    def set_attribute(self, key: str, value: Any) -> None:
        """
        Set an attribute if it's defined in the domain configuration.
        
        Args:
            key: Attribute key
            value: Attribute value
        """
        if key in self.domain_config.get('fault_attributes', []):
            self.attributes[key] = value
            self.log_manager.log(f"Set attribute {key}={value} for {self.__class__.__name__}")
        else:
            # Initialize attribute if not already defined
            if key not in self.attributes:
                self.attributes[key] = None
                self.log_manager.log(f"Initialized undefined attribute {key} for {self.__class__.__name__}")
            self.attributes[key] = value
            self.log_manager.log(f"Updated attribute {key}={value} for {self.__class__.__name__}")
            
    def get_attribute(self, key: str) -> Any:
        """
        Get an attribute value.
        
        Args:
            key: Attribute key
            
        Returns:
            The attribute value if it exists, None otherwise
        """
        if key not in self.attributes:
            self.log_manager.log(f"Warning: Attempted to get undefined attribute {key} for {self.__class__.__name__}")
            self.attributes[key] = None
        return self.attributes.get(key)
    
    @abstractmethod
    def validate(self) -> bool:
        """
        Validate the entity based on domain rules.
        Must be implemented by concrete classes.
        
        Returns:
            bool: True if valid, False otherwise
        """
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert entity to dictionary representation.
        
        Returns:
            Dictionary containing all entity attributes
        """
        self.log_manager.log(f"Converting {self.__class__.__name__} to dictionary with {len(self.attributes)} attributes")
        return self.attributes.copy()
