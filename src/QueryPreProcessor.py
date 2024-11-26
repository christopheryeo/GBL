"""
QueryPreProcessor module for enhancing user queries before they are sent to PandasAI.
Focuses on query standardization and enrichment for vehicle maintenance analysis.
Author: Chris Yeo
"""

import re
from datetime import datetime
import calendar
import yaml
from pathlib import Path
from typing import Dict, Optional

class QueryPreProcessor:
    """A class to preprocess and enhance user queries for better PandasAI responses."""
    
    def __init__(self):
        """Initialize QueryPreProcessor with common patterns and replacements."""
        self.common_patterns = {
            r'\b(?:show|tell|give|list)\b\s+(?:me|us)?\s*': '',  # Remove unnecessary words
            r'\b(?:the|a|an)\b\s+': ' ',  # Remove articles
            r'\s+': ' ',  # Normalize whitespace
        }
        
        # Load only query templates from prompts.yaml and fault categories
        config_path = Path(__file__).parent / 'config'
        self.query_templates = self._load_query_templates(config_path / 'prompts.yaml')
        self.fault_categories = self._load_fault_categories(config_path / 'fault_categories.yaml')
            
        # Extract fault category mappings
        self.entity_mappings = self._build_entity_mappings()
        
        self.time_patterns = {
            'this year': str(datetime.now().year),
            'last year': str(datetime.now().year - 1),
            'next year': str(datetime.now().year + 1),
        }
        
        # Vehicle type mappings
        self.vehicle_types = {
            'lifestyle': 'Lifestyle',
            '10ft': '10 ft',
            '14ft': '14 ft',
            '16ft': '16 ft',
            '24ft': '24 ft',
        }
        
    def _load_query_templates(self, path: Path) -> Dict:
        """Load only the query_templates section from prompts.yaml."""
        try:
            with open(path, 'r') as f:
                prompts = yaml.safe_load(f)
                return prompts.get('query_templates', {})
        except Exception as e:
            print(f"Error loading query templates: {e}")
            return {}
            
    def _load_fault_categories(self, path: Path) -> Dict:
        """Load fault categories from fault_categories.yaml."""
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading fault categories: {e}")
            return {'fault_categories': {}}
        
    def _build_entity_mappings(self) -> dict:
        """Build entity mappings from fault categories and common terms."""
        mappings = {
            'vehicle': ['car', 'truck', 'van', 'vehicle'],
            'fault': ['issue', 'problem', 'breakdown', 'failure'],
            'maintenance': ['repair', 'service', 'fix', 'maintenance'],
        }
        
        # Add mappings from fault categories
        for category, data in self.fault_categories['fault_categories'].items():
            # Add main category keywords
            category_key = category.lower().replace(' ', '_')
            mappings[category_key] = data.get('keywords', [])
            
            # Add subcategory keywords
            for subcategory, subdata in data.get('subcategories', {}).items():
                subcategory_key = f"{category_key}_{subcategory.lower()}"
                mappings[subcategory_key] = subdata.get('keywords', [])
        
        return mappings
        
    def _extract_vehicle_info(self, query: str) -> tuple[Optional[str], Optional[str]]:
        """Extract vehicle type and specific vehicle info from query."""
        # First check for specific vehicle types
        vehicle_type = None
        vehicle_id = None
        
        # Check for specific vehicle types
        for key, value in self.vehicle_types.items():
            if key in query.lower() or value.lower() in query.lower():
                vehicle_type = value
                break
                
        # Check for specific vehicle identifiers
        vehicle_patterns = [
            r'(?:vehicle|car)\s+(\w+\s*\w*)',  # e.g. "vehicle ABC123" or "car Fiat Doblo"
            r'(?:truck|van)\s+(\w+\s*\w*)',    # e.g. "truck XYZ" or "van Mercedes"
        ]
        
        for pattern in vehicle_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                vehicle_id = match.group(1)
                break
                
        return vehicle_type, vehicle_id

    def _is_fault_related(self, query: str) -> bool:
        """Check if the query is related to faults or issues."""
        fault_terms = ['fault', 'issue', 'problem', 'breakdown', 'failure', 'repair', 'maintenance']
        return any(term in query.lower() for term in fault_terms)
        
    def preprocess(self, query: str) -> str:
        """
        Preprocess the user query to make it more effective for PandasAI.
        
        Args:
            query: The original user query
            
        Returns:
            Enhanced query optimized for PandasAI
        """
        # Convert to lowercase and strip whitespace
        processed_query = query.lower().strip()
        
        # Extract specific entities before standardization
        vehicle_type, vehicle_id = self._extract_vehicle_info(processed_query)
        fault_type = self._extract_fault_type(processed_query)
        
        # Apply common pattern replacements
        for pattern, replacement in self.common_patterns.items():
            processed_query = re.sub(pattern, replacement, processed_query)
        
        # Standardize entity references
        processed_query = self._standardize_entities(processed_query)
        
        # Standardize time references
        processed_query = self._standardize_time_references(processed_query)
        
        # Add analysis context if needed
        processed_query = self._add_analysis_context(processed_query)
        
        # Apply appropriate query template if available
        processed_query = self._apply_query_template(processed_query, vehicle_type, fault_type, vehicle_id)
        
        return processed_query.strip()
        
    def _standardize_entities(self, query: str) -> str:
        """Standardize entity references in the query."""
        for standard_term, variants in self.entity_mappings.items():
            if variants:  # Only process if there are variants
                pattern = r'\b(' + '|'.join(map(re.escape, variants)) + r')\b'
                query = re.sub(pattern, standard_term, query)
        return query
    
    def _standardize_time_references(self, query: str) -> str:
        """Standardize time references in the query."""
        # Replace year references
        for time_ref, year in self.time_patterns.items():
            query = query.replace(time_ref, year)
        
        # Standardize month names
        for month_num, month_name in enumerate(calendar.month_name[1:], 1):
            pattern = f"\\b{month_name[:3].lower()}\\w*\\b"
            query = re.sub(pattern, month_name, query, flags=re.IGNORECASE)
        
        return query
    
    def _add_analysis_context(self, query: str) -> str:
        """Add relevant analysis context to the query if needed."""
        analysis_keywords = {
            'trend': 'analyze the trend and pattern of',
            'compare': 'perform a comparative analysis of',
            'average': 'calculate the average and distribution of',
            'common': 'identify the most frequent occurrences of',
            'pattern': 'analyze the temporal patterns in',
            'count': 'count the occurrences of',
            'number': 'count the number of',
            'breakdown': 'analyze the breakdown of',
        }
        
        # Check if query already has analysis context
        has_context = any(keyword in query for keyword in analysis_keywords)
        if not has_context:
            # Add appropriate context based on query content
            for keyword, context in analysis_keywords.items():
                if keyword in query:
                    query = f"{context} {query}"
                    break
        
        return query
    
    def _apply_query_template(self, query: str, vehicle_type: Optional[str] = None, fault_type: Optional[str] = None, vehicle_id: Optional[str] = None) -> str:
        """Apply appropriate query template if available."""
        # Handle vehicle type fault count queries first
        if any(phrase in query for phrase in ['per vehicle type', 'by vehicle type', 'each vehicle type']):
            if self._is_fault_related(query):
                return "use get_fault_count_by_vehicle_type to show fault distribution across vehicle types"
            return query
            
        # Check if query matches any template patterns
        if 'history' in query or 'maintenance record' in query:
            template = self.query_templates.get('vehicle_history', '')
            if template:
                vehicle_ref = vehicle_id or vehicle_type or "all vehicles"
                return template.format(vehicle_id=vehicle_ref, history_data=query)
                
        elif 'pattern' in query or 'recurring' in query:
            template = self.query_templates.get('fault_pattern', '')
            if template:
                if fault_type:
                    return template.format(fault_data=f"{fault_type} faults: {query}")
                return template.format(fault_data=query)
            
        elif 'repair' in query or 'fix' in query:
            template = self.query_templates.get('repair_validation', '')
            if template:
                if fault_type:
                    return template.format(repair_details=f"{fault_type} repair: {query}")
                return template.format(repair_details=query)
            
        # Handle highest/most queries
        if any(word in query for word in ['highest', 'most', 'top']):
            if 'month' in query:
                return "analyze work order numbers by month and identify the months with highest fault counts"
            elif fault_type:
                return f"identify the most common {fault_type} faults based on work order numbers"
            return "identify the most common faults based on work order numbers"
            
        # Add specific context for count queries
        if any(word in query for word in ['how many', 'count', 'number of']):
            # Only use work order counts for fault-related queries
            if self._is_fault_related(query):
                if fault_type:
                    query = f"use get_fault_count to count {fault_type} faults"
                    if vehicle_id:
                        query += f" for vehicle {vehicle_id}"
                    elif vehicle_type:
                        query += f" for {vehicle_type} vehicles"
                    else:
                        query += " across all vehicles"
                elif vehicle_id:
                    query = f"use get_fault_count to count faults for vehicle {vehicle_id}"
                elif vehicle_type:
                    query = f"use get_fault_count to count faults for {vehicle_type} vehicles"
                else:
                    query = "use get_fault_count to count faults across all vehicles"
            else:
                # For non-fault queries, use regular counting
                if vehicle_id:
                    query = f"count the number of {query} for vehicle {vehicle_id}"
                elif vehicle_type:
                    query = f"count the number of {query} for {vehicle_type} vehicles"
                else:
                    query = f"count the number of {query} for all vehicles"
                
        return query

    def _extract_fault_type(self, query: str) -> Optional[str]:
        """Extract specific fault type from query."""
        for category, data in self.fault_categories['fault_categories'].items():
            # Check main category keywords
            if any(keyword.lower() in query.lower() for keyword in data.get('keywords', [])):
                return category
                
            # Check subcategory keywords
            for subcategory, subdata in data.get('subcategories', {}).items():
                if any(keyword.lower() in query.lower() for keyword in subdata.get('keywords', [])):
                    return f"{category} - {subcategory}"
        return None
