"""
Vehicle Faults data structure extending Pandas DataFrame.
Provides specialized methods for vehicle fault analysis and processing.
Author: Chris Yeo
"""

import pandas as pd
from typing import Optional, Union, List, Dict
import numpy as np
from datetime import datetime
import yaml
import os
import re
from pathlib import Path

class VehicleFault(pd.DataFrame):
    """
    A specialized DataFrame for handling vehicle fault data.
    Inherits from pandas DataFrame and adds vehicle-specific functionality.
    """
    
    # Define valid columns for the vehicle fault data based on Kardex Excel format
    _required_columns = [
        'WO No'  # Only require the Work Order number as mandatory
    ]
    
    _optional_columns = [
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

    def __init__(self, *args, validate_columns=True, **kwargs):
        """Initialize the VehicleFault DataFrame with required columns."""
        super().__init__(*args, **kwargs)
        
        # Add empty columns for any missing optional columns
        for col in self._optional_columns:
            if col not in self.columns:
                self[col] = pd.NA
        
        # Add empty fault categories if not present
        if 'FaultMainCategory' not in self.columns:
            self['FaultMainCategory'] = pd.Series(dtype='object')
        if 'FaultSubCategory' not in self.columns:
            self['FaultSubCategory'] = pd.Series(dtype='object')
        
        # Only validate required columns if validation is enabled
        if validate_columns:
            self._validate_columns()
            
        # Generate both main category and sub-category if possible
        try:
            categories = self._categorize_faults()
            self['FaultMainCategory'] = categories['main']
            self['FaultSubCategory'] = categories['sub']
        except Exception as e:
            # If categorization fails, keep existing categories or empty strings
            print(f"Warning: Failed to categorize faults: {str(e)}")
            pass

    @property
    def _constructor(self):
        """Return the class constructor for pandas operations."""
        return lambda *args, **kwargs: VehicleFault(*args, validate_columns=False, **kwargs)

    def _validate_columns(self) -> None:
        """Validate that all required columns are present."""
        if not self.empty:  # Only validate if DataFrame is not empty
            missing_cols = [col for col in self._required_columns if col not in self.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")

    def _safe_get_column(self, column_name, default_value=''):
        """Safely get a column value, returning a default if not found."""
        try:
            return self[column_name] if column_name in self.columns else pd.Series([default_value] * len(self))
        except Exception as e:
            print(f"Warning: Error accessing column {column_name}: {str(e)}")
            return pd.Series([default_value] * len(self))

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

    def get_active_faults(self):
        """Get currently active faults."""
        try:
            # Filter for faults without a completion date
            active = self[pd.isna(self['Done Date'])]
            
            # Select relevant columns
            columns = ['WO No', 'Nature of Complaint', 'Open Date', 'Vehicle Type']
            active_faults = active[columns].copy()
            
            return active_faults
            
        except Exception as e:
            print(f"Error getting active faults: {str(e)}")
            return pd.DataFrame()

    def get_vehicle_history(self, vehicle_type=None):
        """Get maintenance history for a specific vehicle type."""
        try:
            df = self.copy()  # Create a copy to prevent modifying original
            
            # Create vehicle type if not present
            if 'Vehicle Type' not in df.columns:
                df['Vehicle Type'] = self._determine_vehicle_type()
            
            if vehicle_type:
                # Handle multiple vehicle type patterns
                type_patterns = {
                    '14ft': [r'14\s*ft', r'14\s*feet', r'14foot'],
                    '16ft': [r'16\s*ft', r'16\s*feet', r'16foot'],
                    '24ft': [r'24\s*ft', r'24\s*feet', r'24foot'],
                    'Lifestyle': [r'lifestyle', r'life\s*style'],
                    'Prime': [r'prime\s*mover', r'prime']
                }
                
                # Try to match the query to a known vehicle type
                matched_type = None
                query = str(vehicle_type).lower()
                for type_name, patterns in type_patterns.items():
                    if any(re.search(pattern, query, re.IGNORECASE) for pattern in patterns):
                        matched_type = type_name
                        break
                
                if matched_type:
                    # Filter by matched vehicle type
                    mask = df['Vehicle Type'] == matched_type
                    vehicle_data = df[mask].copy()
                else:
                    # Try partial matching if no exact match found
                    mask = df['Vehicle Type'].str.contains(str(vehicle_type), case=False, na=False)
                    vehicle_data = df[mask].copy()
            else:
                vehicle_data = df
            
            # Sort by date
            if 'Open Date' in vehicle_data.columns:
                vehicle_data['Open Date'] = pd.to_datetime(vehicle_data['Open Date'], errors='coerce')
                vehicle_data = vehicle_data.sort_values('Open Date', na_position='last')
            
            # Select relevant columns
            relevant_columns = ['Open Date', 'Nature of Complaint', 'Job Description', 
                              'Vehicle Type', 'FaultMainCategory', 'FaultSubCategory']
            available_columns = [col for col in relevant_columns if col in vehicle_data.columns]
            
            # Create a new DataFrame with only the available columns
            history = vehicle_data[available_columns].copy()
            
            # Add summary statistics
            if not history.empty:
                total_records = len(history)
                date_range = None
                if 'Open Date' in history.columns:
                    valid_dates = history['Open Date'].dropna()
                    if not valid_dates.empty:
                        date_range = f"{valid_dates.min():%Y-%m-%d} to {valid_dates.max():%Y-%m-%d}"
                
                history.attrs['summary'] = {
                    'total_records': total_records,
                    'date_range': date_range,
                    'vehicle_type': vehicle_type or 'All'
                }
            
            return history
            
        except Exception as e:
            print(f"Error getting vehicle history: {str(e)}")
            return pd.DataFrame()

    def get_fault_statistics(self):
        """Get statistics about faults."""
        try:
            # Get categories
            main_cats = self._safe_get_column('FaultMainCategory')
            sub_cats = self._safe_get_column('FaultSubCategory')
            
            # Count faults by main category
            main_counts = main_cats.value_counts()
            
            # Count faults by subcategory within each main category
            sub_counts = {}
            for main_cat in main_counts.index:
                mask = main_cats == main_cat
                sub_counts[main_cat] = sub_cats[mask].value_counts()
            
            # Calculate percentages and prepare statistics
            total_faults = len(self)
            stats = {
                'total_faults': total_faults,
                'categories': []
            }
            
            for main_cat, count in main_counts.items():
                percentage = (count / total_faults) * 100
                subcategory_stats = []
                
                # Add subcategory statistics if available
                if main_cat in sub_counts:
                    for sub_cat, sub_count in sub_counts[main_cat].items():
                        sub_percentage = (sub_count / count) * 100
                        subcategory_stats.append({
                            'name': sub_cat,
                            'count': int(sub_count),
                            'percentage': round(sub_percentage, 2)
                        })
                
                stats['categories'].append({
                    'name': main_cat,
                    'count': int(count),
                    'percentage': round(percentage, 2),
                    'subcategories': subcategory_stats
                })
            
            return stats
            
        except Exception as e:
            print(f"Error getting fault statistics: {str(e)}")
            return {'total_faults': 0, 'categories': []}

    def get_filtered_count(self, column, value):
        """Get count of records matching a specific column value."""
        try:
            return len(self[self[column].str.contains(str(value), case=False, na=False)])
        except Exception as e:
            print(f"Error getting filtered count: {str(e)}")
            return 0

    def filter_records(self, column, value):
        """Filter records based on a column value."""
        try:
            return self[self[column].str.contains(str(value), case=False, na=False)]
        except Exception as e:
            print(f"Error filtering records: {str(e)}")
            return pd.DataFrame()

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

    def get_faults_by_category(self, main_category: str = None, sub_category: str = None) -> 'VehicleFault':
        """
        Filter faults by main category and/or sub-category.
        
        Args:
            main_category (str, optional): Main category to filter by
            sub_category (str, optional): Sub-category to filter by
            
        Returns:
            VehicleFault: Filtered fault data for the specified category/categories
        """
        if main_category and sub_category:
            return self[(self['FaultMainCategory'] == main_category) & 
                       (self['FaultSubCategory'] == sub_category)]
        elif main_category:
            return self[self['FaultMainCategory'] == main_category]
        elif sub_category:
            return self[self['FaultSubCategory'] == sub_category]
        else:
            return self

    def get_top_faults(self, limit=3, by_subcategory=False):
        """
        Get the top fault categories or subcategories by frequency.
        
        Args:
            limit (int): Number of top faults to return
            by_subcategory (bool): If True, return top subcategories instead of main categories
            
        Returns:
            dict: Dictionary containing the top faults with their counts and percentages
        """
        try:
            if by_subcategory:
                # Get subcategory counts
                sub_cats = self._safe_get_column('FaultSubCategory')
                counts = sub_cats.value_counts()
                total = len(self)
                
                # Get top subcategories
                top_subcats = []
                for subcat, count in counts.head(limit).items():
                    percentage = (count / total) * 100
                    main_cat = self[sub_cats == subcat]['FaultMainCategory'].iloc[0]
                    top_subcats.append({
                        'subcategory': subcat,
                        'main_category': main_cat,
                        'count': int(count),
                        'percentage': round(percentage, 2)
                    })
                
                return {
                    'total_faults': total,
                    'top_subcategories': top_subcats
                }
            else:
                # Get main category counts
                main_cats = self._safe_get_column('FaultMainCategory')
                counts = main_cats.value_counts()
                total = len(self)
                
                # Get top categories with their subcategories
                top_cats = []
                for cat, count in counts.head(limit).items():
                    percentage = (count / total) * 100
                    
                    # Get subcategory breakdown for this category
                    cat_mask = main_cats == cat
                    sub_counts = self[cat_mask]['FaultSubCategory'].value_counts()
                    subcats = []
                    for subcat, subcount in sub_counts.items():
                        sub_percentage = (subcount / count) * 100
                        subcats.append({
                            'name': subcat,
                            'count': int(subcount),
                            'percentage': round(sub_percentage, 2)
                        })
                    
                    top_cats.append({
                        'category': cat,
                        'count': int(count),
                        'percentage': round(percentage, 2),
                        'subcategories': subcats
                    })
                
                return {
                    'total_faults': total,
                    'top_categories': top_cats
                }
                
        except Exception as e:
            print(f"Error getting top faults: {str(e)}")
            return {'total_faults': 0, 'top_categories': []}

    def _determine_vehicle_type(self):
        """Determine vehicle type from available information."""
        try:
            # Try to extract vehicle type from various columns
            vehicle_types = []
            
            # Common vehicle type patterns
            type_patterns = {
                '14ft': [r'14\s*ft', r'14\s*feet', r'14foot'],
                '16ft': [r'16\s*ft', r'16\s*feet', r'16foot'],
                '24ft': [r'24\s*ft', r'24\s*feet', r'24foot'],
                'Lifestyle': [r'lifestyle', r'life\s*style'],
                'Prime': [r'prime\s*mover', r'prime']
            }
            
            for _, row in self.iterrows():
                vtype = None
                
                # Check Job Description and Nature of Complaint
                desc = str(row.get('Job Description', '')).lower()
                complaint = str(row.get('Nature of Complaint', '')).lower()
                text = f"{desc} {complaint}"
                
                # Try to match vehicle type patterns
                for type_name, patterns in type_patterns.items():
                    if any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns):
                        vtype = type_name
                        break
                
                # Default to 'Unknown' if no type found
                vehicle_types.append(vtype if vtype else 'Unknown')
            
            return pd.Series(vehicle_types)
            
        except Exception as e:
            print(f"Error determining vehicle types: {str(e)}")
            return pd.Series(['Unknown'] * len(self))

    def categorize_faults(self):
        """Categorize faults based on job description and nature of complaint."""
        try:
            # Get fault descriptions from both columns
            job_desc = self._safe_get_column('Job Description')
            complaint = self._safe_get_column('Nature of Complaint')
            
            # Combine descriptions, handling NaN values
            combined_desc = job_desc.fillna('') + ' ' + complaint.fillna('')
            
            # Initialize result lists
            main_categories = []
            sub_categories = []
            confidence_scores = []
            
            # Load categorization rules from fault_categories.yaml
            try:
                # Get the src directory path
                src_dir = Path(__file__).parent
                config_dir = src_dir / 'config'
                config_path = config_dir / 'fault_categories.yaml'
                
                if not config_path.exists():
                    raise FileNotFoundError(f"fault_categories.yaml not found at {config_path}")
                
                with open(config_path, 'r') as f:
                    self.fault_categories = yaml.safe_load(f)
                    
            except Exception as e:
                print(f"Warning: Could not load categories from fault_categories.yaml: {str(e)}")
                return None
            
            # Process each row
            for desc in combined_desc:
                main_cat, sub_cat, confidence = self._categorize_faults(str(desc))
                main_categories.append(main_cat)
                sub_categories.append(sub_cat if sub_cat else '')
                confidence_scores.append(confidence)
            
            # Create Series with proper index alignment
            main_series = pd.Series(main_categories, index=self.index)
            sub_series = pd.Series(sub_categories, index=self.index)
            confidence_series = pd.Series(confidence_scores, index=self.index)
            
            return {
                'main': main_series,
                'sub': sub_series,
                'confidence': confidence_series
            }
            
        except Exception as e:
            print(f"Error categorizing faults: {str(e)}")
            # Return empty categories on error
            empty_series = pd.Series([''] * len(self), index=self.index)
            return {
                'main': empty_series,
                'sub': empty_series,
                'confidence': pd.Series([0.0] * len(self), index=self.index)
            }

    def _categorize_faults(self, fault_description):
        """
        Categorize a fault description into a main category and subcategory.
        Returns a tuple of (main_category, subcategory, confidence_score)
        """
        if not fault_description or not isinstance(fault_description, str):
            return "Uncategorized", None, 0

        fault_description = fault_description.lower()
        best_match = None
        best_subcategory = None
        highest_score = 0
        
        for category, details in self.fault_categories['fault_categories'].items():
            # Check main category keywords
            score = 0
            keyword_matches = 0
            if 'keywords' in details:
                for keyword in details['keywords']:
                    if keyword.lower() in fault_description:
                        score += 1
                        keyword_matches += 1
            
            # Check subcategory keywords
            best_sub = None
            sub_score = 0
            sub_keyword_matches = 0
            if 'subcategories' in details:
                for subcategory, sub_details in details['subcategories'].items():
                    current_sub_score = 0
                    current_sub_matches = 0
                    for keyword in sub_details['keywords']:
                        if keyword.lower() in fault_description:
                            current_sub_score += 1
                            current_sub_matches += 1
                    if current_sub_score > sub_score:
                        sub_score = current_sub_score
                        sub_keyword_matches = current_sub_matches
                        best_sub = subcategory
            
            # Calculate weighted score based on both keyword matches and uniqueness
            total_keywords = len(details.get('keywords', [])) + sum(len(sub.get('keywords', [])) 
                           for sub in details.get('subcategories', {}).values())
            
            # Combine scores with emphasis on keyword match density
            match_density = (keyword_matches + sub_keyword_matches) / max(1, total_keywords)
            total_score = score + (sub_score * 0.5) + (match_density * 2)
            
            if total_score > highest_score:
                highest_score = total_score
                best_match = category
                best_subcategory = best_sub
        
        if best_match is None:
            return "Uncategorized", None, 0
        
        # Normalize confidence with emphasis on match density
        confidence = min((highest_score / 4) + (match_density * 0.5), 1.0)
        return best_match, best_subcategory, confidence
