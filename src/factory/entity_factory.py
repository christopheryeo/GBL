"""
Factory for creating domain-specific entities.
"""
from typing import Any, Dict, Optional, Type
from ..domain.base.base_entity import BaseEntity
from ..domain.vehicle_leasing.vehicle_fault import VehicleFault

class EntityFactory:
    """Factory for creating domain entities."""
    
    _entity_classes = {
        'vehicle_leasing': VehicleFault
    }
    
    @classmethod
    def create_entity(cls, domain: str, domain_config: Dict[str, Any]) -> Optional[BaseEntity]:
        """
        Create an entity for the specified domain.
        
        Args:
            domain: Domain name
            domain_config: Domain configuration dictionary
            
        Returns:
            Domain-specific entity instance or None if domain not found
        """
        entity_class = cls._entity_classes.get(domain)
        if entity_class:
            return entity_class(domain_config)
        return None
    
    @classmethod
    def register_entity(cls, domain: str, entity_class: Type[BaseEntity]) -> None:
        """
        Register a new entity class for a domain.
        
        Args:
            domain: Domain name
            entity_class: Entity class to register
        """
        cls._entity_classes[domain] = entity_class
