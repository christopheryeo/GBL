"""
Factory for creating domain-specific processors.
"""
from typing import Optional, Type
from ..domain.base.base_processor import BaseProcessor
from ..domain.vehicle_leasing.kardex_processor import KardexProcessor

class ProcessorFactory:
    """Factory for creating Excel processors."""
    
    _processor_classes = {
        'vehicle_leasing': {
            'kardex': KardexProcessor
        }
    }
    
    @classmethod
    def create_processor(cls, domain: str, format_name: str) -> Optional[BaseProcessor]:
        """
        Create a processor for the specified domain and format.
        
        Args:
            domain: Domain name
            format_name: Format name within the domain
            
        Returns:
            Domain-specific processor instance or None if not found
        """
        domain_processors = cls._processor_classes.get(domain, {})
        processor_class = domain_processors.get(format_name)
        if processor_class:
            return processor_class()
        return None
    
    @classmethod
    def register_processor(cls, domain: str, format_name: str, processor_class: Type[BaseProcessor]) -> None:
        """
        Register a new processor class for a domain and format.
        
        Args:
            domain: Domain name
            format_name: Format name within the domain
            processor_class: Processor class to register
        """
        if domain not in cls._processor_classes:
            cls._processor_classes[domain] = {}
        cls._processor_classes[domain][format_name] = processor_class
