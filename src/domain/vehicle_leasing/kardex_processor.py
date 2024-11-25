"""
Kardex Excel file processor for the vehicle leasing domain.
"""
from typing import Any, Dict, List
import pandas as pd
from datetime import datetime
from ..base.base_processor import BaseProcessor
from .vehicle_fault import VehicleFault
from ...ChatGPT import ChatGPT
from ...config.prompt_manager import PromptManager

class KardexProcessor(BaseProcessor):
    """Processor for Kardex Excel files in the vehicle leasing domain."""
    
    def __init__(self):
        """Initialize Kardex processor with vehicle leasing domain configuration."""
        super().__init__('vehicle_leasing', 'kardex')
        self.gpt = ChatGPT()
        self.prompt_manager = PromptManager()
        self._category_cache = {}
        self.log_manager.log("Initialized KardexProcessor")
        
    def process(self, excel_file: str, sheet_name: str = None) -> List[Dict[str, Any]]:
        """
        Process Kardex Excel file and create vehicle fault entities.
        
        Args:
            excel_file: Path to the Kardex Excel file
            sheet_name: Name of the sheet to process. If None, uses the sheet name from config.
            
        Returns:
            List of processed vehicle faults as dictionaries
        """
        self.log_manager.log(f"Processing Kardex Excel file: {excel_file}")
        
        # Get Excel reading parameters from config
        format_config = self.config['format_config']
        config_sheet_name = format_config.get('sheet_name', 'Sheet1')
        header_row = format_config.get('header_row', 0)
        
        # Use provided sheet_name if available, otherwise use config
        sheet_name = sheet_name or config_sheet_name
        
        self.log_manager.log(f"Reading Excel with sheet_name='{sheet_name}', header_row={header_row}")
        
        try:
            # Read Excel file
            df = pd.read_excel(
                excel_file,
                sheet_name=sheet_name,
                header=header_row
            )
            
            # Check if DataFrame is empty or has no data rows
            if df.empty or len(df) == 0:
                self.log_manager.log("No data found in sheet")
                return []
                
            self.log_manager.log(f"Successfully read Excel file with {len(df)} rows")
            self.log_manager.log(f"Columns found: {list(df.columns)}")
            
            # Validate required columns
            required_columns = ['WO No', 'Open Date', 'Nature of Complaint', 'Job Description']
            self.log_manager.log(f"Validating DataFrame columns. Required: {required_columns}")
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
                
            self.log_manager.log("DataFrame validation successful")
            
            # Process each row into a VehicleFault
            results = []
            for idx, row in df.iterrows():
                try:
                    self.log_manager.log(f"Processing row {idx + 1}")
                    
                    # Create VehicleFault instance with domain config
                    fault = VehicleFault(self.config)
                    
                    # Map Excel columns to VehicleFault attributes
                    fault.set_attribute('work_order', str(row['WO No']))
                    fault.set_attribute('date', row['Open Date'])
                    fault.set_attribute('nature_of_complaint', str(row['Nature of Complaint']))
                    fault.set_attribute('description', str(row['Job Description']))
                    
                    # Set vehicle type
                    fault.set_attribute('vehicle_type', sheet_name)
                    
                    # Set optional attributes if present
                    optional_attrs = {
                        'location': 'Loc',
                        'status': 'ST',
                        'mileage': 'Mileage',
                        'completion_date': 'Done Date',
                        'actual_finish_date': 'Actual Finish Date',
                        'fault_codes': 'Fault Codes',
                        'srr_number': 'SRR No.',
                        'mechanic': 'Mechanic Name',
                        'customer_id': 'Customer',
                        'customer_name': 'Customer Name',
                        'next_recommendation': 'Recommendation 4 next',
                        'category': 'Cat',
                        'lead_technician': 'Lead Tech',
                        'bill_number': 'Bill No.',
                        'interco_amount': 'Intercoamt',
                        'cost': 'Custamt'
                    }
                    
                    for attr, col in optional_attrs.items():
                        if col in row and pd.notna(row[col]):
                            fault.set_attribute(attr, str(row[col]))
                    
                    # Apply transformations
                    self._apply_transformations(fault)
                    
                    # Validate and convert to dictionary
                    fault.validate()
                    result = fault.to_dict()
                    results.append(result)
                    
                    self.log_manager.log(f"Successfully processed fault from row {idx + 1}")
                    
                except Exception as e:
                    self.log_manager.log(f"Error processing row {idx + 1}: {str(e)}")
                    continue
                    
            return results
            
        except Exception as e:
            self.log_manager.log(f"Error reading Excel file: {str(e)}")
            raise
    
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
            elif transform == 'classify_fault_category':
                self._classify_fault_category(fault)
    
    def _clean_work_order(self, fault: VehicleFault) -> None:
        """Clean work order number by removing non-alphanumeric characters."""
        wo = str(fault.get_attribute('work_order'))  # Convert to string first
        
        # Handle special cases first
        if ' ' in wo:
            wo = wo.replace(' ', '')
            
        if '-' in wo:
            wo = wo.replace('-', '')
            
        # Keep only alphanumeric characters
        wo = ''.join(c for c in wo if c.isalnum())
        
        fault.set_attribute('work_order', wo)
    
    def _format_dates(self, fault: VehicleFault) -> None:
        """Format dates to standard format."""
        date = fault.get_attribute('date')
        
        # Handle various date formats
        try:
            if isinstance(date, str):
                date = pd.to_datetime(date)
            elif isinstance(date, (pd.Timestamp, datetime)):
                pass  # Already in correct format
            else:
                raise ValueError(f"Unsupported date type: {type(date)}")
                
            # Format date to string
            formatted_date = date.strftime('%Y-%m-%d %H:%M:%S')
            self.log_manager.log(f"Formatted date from '{date}' to '{formatted_date}'")
            fault.set_attribute('date', formatted_date)
        except Exception as e:
            self.log_manager.log(f"Error formatting date: {str(e)}")
            raise ValueError("Invalid date format")
    
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
            
            # Enhanced component detection
            self._extract_component_from_description(fault)
            
            # Enhanced severity detection
            self._extract_severity_from_description(fault)
            
    def _extract_component_from_description(self, fault: VehicleFault) -> None:
        """
        Extract affected component from fault description using keyword matching.
        
        Args:
            fault: VehicleFault instance to process
        """
        try:
            # Get description and nature of complaint if available
            description = fault.get_attribute('description').lower()
            try:
                nature = fault.get_attribute('nature_of_complaint', '').lower()
                description = description + ' ' + nature
            except:
                pass
            
            # Define component keywords with expanded terms
            component_keywords = {
                'engine': ['engine', 'dpf', 'timing belt', 'pulley', 'water pump', 'oil', 'coolant', 'motor', 'cylinder', 'piston', 'crankshaft', 'valve', 'head gasket', 'turbo'],
                'transmission': ['transmission', 'gear', 'clutch', 'trans', 'drive shaft', 'gearbox', 'differential', 'flywheel', 'synchro'],
                'brake': ['brake', 'abs', 'rotor', 'caliper', 'brake pad', 'brake fluid', 'brake disc', 'brake drum', 'brake line'],
                'electrical': ['electrical', 'battery', 'light', 'cigar lighter', 'cigarette lighter', 'aircon', 'wiring', 'fuse', 'relay', 'switch', 'sensor', 'starter', 'alternator', 'ecu'],
                'suspension': ['suspension', 'shock', 'absorber', 'mounting', 'link rod', 'strut', 'spring', 'bushing', 'ball joint', 'control arm', 'stabilizer'],
                'tire': ['tyre', 'tire', 'wheel', 'rim', 'alignment', 'balancing', 'puncture', 'flat'],
                'exhaust': ['exhaust', 'dpf', 'regen', 'muffler', 'catalytic', 'emission', 'silencer'],
                'fuel': ['fuel', 'diesel', 'petrol', 'gas', 'injector', 'carburetor', 'tank', 'pump', 'filter'],
                'cooling': ['coolant', 'radiator', 'water pump', 'thermostat', 'fan', 'hose', 'temperature', 'overheat'],
                'steering': ['steering', 'power steering', 'rack', 'tie rod', 'steering wheel', 'steering column', 'steering pump']
            }
            
            # Find matching components with improved handling
            components = []
            for component, keywords in component_keywords.items():
                # Check each keyword
                matches = [keyword for keyword in keywords if keyword in description]
                if matches:
                    components.append(component)
                    self.log_manager.log(f"Detected component '{component}' from keywords: {', '.join(matches)}")
                    
            # Set components if found
            if components:
                component_str = ', '.join(sorted(set(components)))  # Remove duplicates and sort
                self.log_manager.log(f"Setting affected component to: {component_str}")
                fault.set_attribute('component', component_str)
                
        except Exception as e:
            self.log_manager.log(f"Error extracting component: {str(e)}")
            
    def _extract_severity_from_description(self, fault: VehicleFault) -> None:
        """
        Extract severity from fault description using keyword matching.
        
        Args:
            fault: VehicleFault instance to process
        """
        try:
            # Get description and nature of complaint if available
            description = fault.get_attribute('description').lower()
            try:
                nature = fault.get_attribute('nature_of_complaint', '').lower()
                description = description + ' ' + nature
            except:
                pass
            
            # Define severity indicators with expanded terms
            severity_indicators = {
                'high': [
                    'urgent', 'emergency', 'critical', 'severe', 'dangerous', 'immediate', 'safety',
                    'broken', 'failed', 'not working', 'breakdown', 'accident', 'collision',
                    'smoke', 'fire', 'overheat', 'stall', 'stuck', 'dead', 'major', 'serious'
                ],
                'medium': [
                    'repair', 'replace', 'fix', 'check', 'inspect', 'warning', 'attention',
                    'maintenance', 'service', 'worn', 'noise', 'vibration', 'leak', 'loose',
                    'adjustment', 'alignment', 'update'
                ],
                'low': [
                    'monitor', 'observe', 'note', 'clean', 'minor', 'cosmetic', 'scratch',
                    'polish', 'touch up', 'routine', 'normal', 'regular', 'standard'
                ]
            }
            
            # Count severity indicators with weighted scoring
            severity_scores = {'high': 0, 'medium': 0, 'low': 0}
            
            for level, keywords in severity_indicators.items():
                # Weight multipliers for different severity levels
                weight = 3 if level == 'high' else 2 if level == 'medium' else 1
                
                # Count matches with weighting
                matches = sum(1 for keyword in keywords if keyword in description)
                severity_scores[level] = matches * weight
            
            # Determine severity based on highest weighted score
            max_score = max(severity_scores.values())
            if max_score > 0:
                severity = max(severity_scores.items(), key=lambda x: x[1])[0]
            else:
                severity = 'medium'  # Default to medium if no indicators found
                
            self.log_manager.log(f"Set severity to '{severity}' based on description (scores: {severity_scores})")
            fault.set_severity(severity)
            
        except Exception as e:
            self.log_manager.log(f"Error extracting severity: {str(e)}")
            fault.set_severity('medium')  # Default to medium on error

    def _classify_fault_category(self, fault: VehicleFault) -> None:
        """
        Classify the fault category based on description and other attributes.
        
        Args:
            fault: VehicleFault instance to classify
        """
        try:
            # Get description and component
            description = fault.get_attribute('description')
            component = fault.get_attribute('component')
            severity = fault.get_attribute('severity')
            
            # Default to maintenance if it's a service
            if 'service' in description.lower() or fault.get_attribute('category') == 'SERVICE':
                fault.set_attribute('fault_category', 'Maintenance')
                return
                
            # Check for breakdown
            if 'breakdown' in description.lower() or fault.get_attribute('category') == 'TYREBD':
                fault.set_attribute('fault_category', 'Breakdown')
                return
                
            # Check for inspection
            if 'inspect' in description.lower() or 'check' in description.lower():
                fault.set_attribute('fault_category', 'Inspection')
                return
                
            # Check for repair
            if 'repair' in description.lower() or 'replace' in description.lower() or fault.get_attribute('category') == 'REPAIR':
                fault.set_attribute('fault_category', 'Repair')
                return
                
            # Default to Other if no match
            fault.set_attribute('fault_category', 'Other')
            
        except Exception as e:
            self.log_manager.log(f"Error classifying fault: {str(e)}. Using 'Other'")
            fault.set_attribute('fault_category', 'Other')
