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

class VehicleFault:
    """
    A wrapper around pandas DataFrame for handling vehicle fault data.
    Uses composition instead of inheritance to avoid recursion issues.
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

    def __init__(self, data=None, validate_columns=True):
        """Initialize with a pandas DataFrame."""
        # Create or copy the DataFrame
        if data is None:
            self._df = pd.DataFrame()
        elif isinstance(data, pd.DataFrame):
            self._df = data.copy()
        else:
            self._df = pd.DataFrame(data)
        
        # Add empty columns for any missing optional columns
        for col in self._optional_columns:
            if col not in self._df.columns:
                self._df[col] = pd.NA
        
        # Add empty fault categories if not present
        if 'FaultMainCategory' not in self._df.columns:
            self._df['FaultMainCategory'] = pd.Series(dtype='object')
        if 'FaultSubCategory' not in self._df.columns:
            self._df['FaultSubCategory'] = pd.Series(dtype='object')
        
        # Only validate required columns if validation is enabled
        if validate_columns:
            self._validate_columns()
            
        # Generate both main category and sub-category if possible
        try:
            categories = self.categorize_faults()
            if categories:
                self._df['FaultMainCategory'] = categories['main']
                self._df['FaultSubCategory'] = categories['sub']
        except Exception as e:
            print(f"Warning: Failed to categorize faults: {str(e)}")

    def _validate_columns(self):
        """Validate that all required columns are present."""
        if not self._df.empty:
            missing_cols = [col for col in self._required_columns if col not in self._df.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")

    def _safe_get_column(self, column_name, default_value=''):
        """Safely get a column value, returning a default if not found."""
        try:
            if column_name in self._df.columns:
                return self._df[column_name]
            return pd.Series([default_value] * len(self._df))
        except Exception as e:
            print(f"Warning: Error accessing column {column_name}: {str(e)}")
            return pd.Series([default_value] * len(self._df))

    @classmethod
    def from_excel(cls, filepath: str) -> 'VehicleFault':
        """Create a VehicleFault object from an Excel file."""
        # Skip the first 3 rows which contain header information
        df = pd.read_excel(filepath, skiprows=3)
        return cls(df)

    def categorize_faults(self):
        """Categorize faults based on job description and nature of complaint."""
        try:
            # Load categorization rules from fault_categories.yaml first
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

            # Get fault descriptions from both columns
            job_desc = self._df['Job Description'] if 'Job Description' in self._df.columns else pd.Series([''] * len(self._df))
            complaint = self._df['Nature of Complaint'] if 'Nature of Complaint' in self._df.columns else pd.Series([''] * len(self._df))
            
            # Combine descriptions, handling NaN values
            combined_desc = job_desc.fillna('') + ' ' + complaint.fillna('')
            
            # Initialize result lists
            main_categories = []
            sub_categories = []
            confidence_scores = []
            
            # Process each row
            for desc in combined_desc:
                main_cat, sub_cat, confidence = self._categorize_faults(str(desc))
                main_categories.append(main_cat)
                sub_categories.append(sub_cat if sub_cat else '')
                confidence_scores.append(confidence)
            
            # Create Series with proper index alignment
            main_series = pd.Series(main_categories, index=self._df.index)
            sub_series = pd.Series(sub_categories, index=self._df.index)
            confidence_series = pd.Series(confidence_scores, index=self._df.index)
            
            return {
                'main': main_series,
                'sub': sub_series,
                'confidence': confidence_series
            }
            
        except Exception as e:
            print(f"Error categorizing faults: {str(e)}")
            # Return empty categories on error
            empty_series = pd.Series([''] * len(self._df), index=self._df.index)
            return {
                'main': empty_series,
                'sub': empty_series,
                'confidence': pd.Series([0.0] * len(self._df), index=self._df.index)
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
        match_density = 0
        
        try:
            for category, details in self.fault_categories['fault_categories'].items():
                # Check main category keywords
                score = 0
                keyword_matches = 0
                
                # Process main category keywords
                if 'keywords' in details:
                    for keyword in details['keywords']:
                        if keyword.lower() in fault_description:
                            score += 1
                            keyword_matches += 1
                
                # Process subcategories without recursion
                best_sub = None
                sub_score = 0
                sub_keyword_matches = 0
                
                if 'subcategories' in details:
                    for subcategory, sub_details in details['subcategories'].items():
                        current_sub_score = 0
                        current_sub_matches = 0
                        
                        if 'keywords' in sub_details:
                            for keyword in sub_details['keywords']:
                                if keyword.lower() in fault_description:
                                    current_sub_score += 1
                                    current_sub_matches += 1
                                    
                        if current_sub_score > sub_score:
                            sub_score = current_sub_score
                            sub_keyword_matches = current_sub_matches
                            best_sub = subcategory
                
                # Calculate total keywords for match density
                total_keywords = len(details.get('keywords', []))
                if 'subcategories' in details:
                    for sub in details['subcategories'].values():
                        total_keywords += len(sub.get('keywords', []))
                
                # Calculate match density and total score
                current_match_density = (keyword_matches + sub_keyword_matches) / max(1, total_keywords)
                total_score = score + (sub_score * 0.5) + (current_match_density * 2)
                
                if total_score > highest_score:
                    highest_score = total_score
                    best_match = category
                    best_subcategory = best_sub
                    match_density = current_match_density
        
        except Exception as e:
            print(f"Error in categorization: {str(e)}")
            return "Uncategorized", None, 0
            
        if best_match is None:
            return "Uncategorized", None, 0
        
        # Normalize confidence score
        confidence = min((highest_score / 4) + (match_density * 0.5), 1.0)
        return best_match, best_subcategory, confidence

    def __len__(self):
        """Return the length of the underlying DataFrame."""
        return len(self._df)

    def __getitem__(self, key):
        """Get a column from the DataFrame."""
        return self._df[key]

    def __setitem__(self, key, value):
        """Set a column in the DataFrame."""
        self._df[key] = value

    @property
    def columns(self):
        """Get DataFrame columns."""
        return self._df.columns

    @property
    def index(self):
        """Get DataFrame index."""
        return self._df.index

    @property
    def empty(self):
        """Check if DataFrame is empty."""
        return self._df.empty

    def copy(self):
        """Create a copy of the VehicleFault object."""
        return VehicleFault(self._df.copy())

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
        self._df.loc[len(self._df)] = new_fault

    def _generate_fault_id(self) -> str:
        """Generate a unique fault ID."""
        if len(self._df) == 0:
            return 'F001'
        last_id = self._df['fault_id'].iloc[-1]
        num = int(last_id[1:]) + 1
        return f'F{num:03d}'

    def get_active_faults(self):
        """Get currently active faults."""
        try:
            # Filter for faults without a completion date
            active = self._df[pd.isna(self._df['Done Date'])]
            
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
            df = self._df.copy()  # Create a copy to prevent modifying original
            
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
            stats = {}
            
            # Get categories
            main_cats = self._safe_get_column('FaultMainCategory')
            sub_cats = self._safe_get_column('FaultSubCategory')
            vehicle_types = self._safe_get_column('Vehicle Type')
            
            # Count faults by main category
            main_counts = main_cats.value_counts().to_dict()
            stats['main_categories'] = main_counts
            
            # Count faults by subcategory within each main category
            sub_counts = {}
            for main_cat in main_counts.keys():
                mask = main_cats == main_cat
                sub_cats_in_main = sub_cats[mask].value_counts().to_dict()
                sub_counts[main_cat] = sub_cats_in_main
            stats['sub_categories'] = sub_counts
            
            # Count faults by vehicle type
            vehicle_counts = {}
            for vehicle_type in vehicle_types.unique():
                if pd.isna(vehicle_type):
                    continue
                    
                # First try to count records with fault categories
                mask = (vehicle_types == vehicle_type) & (~main_cats.isna())
                count = mask.sum()
                
                # If no categorized faults, count all records for this vehicle type
                if count == 0:
                    count = (vehicle_types == vehicle_type).sum()
                    
                vehicle_counts[vehicle_type] = count
                
            stats['vehicle_types'] = vehicle_counts
            
            return stats
            
        except Exception as e:
            print(f"Error getting fault statistics: {str(e)}")
            return {}

    def get_faults_by_category(self, main_category: str = None, sub_category: str = None) -> 'VehicleFault':
        """
        Filter faults by main category and/or sub-category.
        
        Args:
            main_category (str, optional): Main category to filter by
            sub_category (str, optional): Sub-category to filter by
            
        Returns:
            VehicleFault: Filtered fault data for the specified category/categories
        """
        try:
            df = self._df.copy()
            
            if main_category:
                mask = df['FaultMainCategory'].str.contains(main_category, case=False, na=False)
                df = df[mask]
                
                if sub_category:
                    mask = df['FaultSubCategory'].str.contains(sub_category, case=False, na=False)
                    df = df[mask]
                    
            return VehicleFault(df)
            
        except Exception as e:
            print(f"Error filtering faults by category: {str(e)}")
            return VehicleFault()

    def get_fault_count(self, vehicle_type: str = None, fault_type: str = None) -> int:
        """
        Get the count of faults, optionally filtered by vehicle type and/or fault type.
        First tries to count records with fault categories, then falls back to all records if no categories found.
        
        Args:
            vehicle_type (str, optional): Vehicle type to filter by
            fault_type (str, optional): Fault type to filter by
            
        Returns:
            int: Count of faults matching the criteria
        """
        try:
            # Start with all records
            mask = pd.Series(True, index=self._df.index)
            
            # Apply vehicle type filter if specified
            if vehicle_type:
                vehicle_mask = self._df['Vehicle Type'].str.contains(str(vehicle_type), case=False, na=False)
                if not vehicle_mask.any():  # No matches found for vehicle type
                    return 0
                mask &= vehicle_mask
            
            # Try to count records with specific fault type first
            if fault_type:
                # Create combined fault mask
                fault_mask = (
                    self._df['FaultMainCategory'].str.contains(str(fault_type), case=False, na=False) |
                    self._df['FaultSubCategory'].str.contains(str(fault_type), case=False, na=False) |
                    self._df['Job Description'].str.contains(str(fault_type), case=False, na=False) |
                    self._df['Nature of Complaint'].str.contains(str(fault_type), case=False, na=False)
                )
                
                if not fault_mask.any():  # No matches found for fault type
                    return 0
                
                mask &= fault_mask
                return mask.sum()
            else:
                # Try to count records with any fault category first
                categorized_mask = ~self._df['FaultMainCategory'].isna()
                if categorized_mask.any():  # If we have any categorized faults
                    mask &= categorized_mask
                    return mask.sum()
                else:
                    # If no categorized faults found, count all records
                    return mask.sum()
            
        except Exception as e:
            print(f"Error getting fault count: {str(e)}")
            return 0
            
    def get_fault_count_by_vehicle_type(self) -> pd.DataFrame:
        """
        Get the count of faults for each vehicle type.
        First tries to count records with fault categories, then falls back to all records if no categories found.
        
        Returns:
            pd.DataFrame: DataFrame with vehicle types and their fault counts
        """
        try:
            result = []
            vehicle_types = self._df['Vehicle Type'].unique()
            
            for vehicle_type in vehicle_types:
                if pd.isna(vehicle_type):
                    continue
                    
                count = self.get_fault_count(vehicle_type=vehicle_type)
                result.append({
                    'Vehicle Type': vehicle_type,
                    'Number of Faults': count
                })
                
            return pd.DataFrame(result)
            
        except Exception as e:
            print(f"Error getting fault count by vehicle type: {str(e)}")
            return pd.DataFrame(columns=['Vehicle Type', 'Number of Faults'])

    def to_excel(self, filepath: str) -> None:
        """
        Save the fault data to an Excel file.
        
        Args:
            filepath (str): Path to save the Excel file
        """
        # Add vehicle information as header
        writer = pd.ExcelWriter(filepath, engine='openpyxl')
        self._df.to_excel(writer, index=False, startrow=3)
        writer.save()

    def close_fault(self, fault_id: str) -> None:
        """
        Close a fault by setting its status to 'closed'.
        
        Args:
            fault_id (str): ID of the fault to close
        """
        idx = self._df[self._df['fault_id'] == fault_id].index
        if len(idx) > 0:
            self._df.loc[idx[0], 'status'] = 'closed'
            self._df.loc[idx[0], 'Done Date'] = datetime.now()

    def get_faults_by_category(self, main_category: str = None, sub_category: str = None) -> 'VehicleFault':
        """
        Filter faults by main category and/or sub-category.
        
        Args:
            main_category (str, optional): Main category to filter by
            sub_category (str, optional): Sub-category to filter by
            
        Returns:
            VehicleFault: Filtered fault data for the specified category/categories
        """
        try:
            df = self._df.copy()  # Create a copy to prevent modifying original
            
            if main_category:
                mask = df['FaultMainCategory'].str.contains(main_category, case=False, na=False)
                df = df[mask]
                
                if sub_category:
                    mask = df['FaultSubCategory'].str.contains(sub_category, case=False, na=False)
                    df = df[mask]
                    
            return VehicleFault(df)
            
        except Exception as e:
            print(f"Error filtering faults by category: {str(e)}")
            return VehicleFault()

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
                total = len(self._df)
                
                # Get top subcategories
                top_subcats = []
                for subcat, count in counts.head(limit).items():
                    percentage = (count / total) * 100
                    main_cat = self._df[sub_cats == subcat]['FaultMainCategory'].iloc[0]
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
                total = len(self._df)
                
                # Get top categories with their subcategories
                top_cats = []
                for cat, count in counts.head(limit).items():
                    percentage = (count / total) * 100
                    
                    # Get subcategory breakdown for this category
                    cat_mask = main_cats == cat
                    sub_counts = self._df[cat_mask]['FaultSubCategory'].value_counts()
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
            
            for _, row in self._df.iterrows():
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
            return pd.Series(['Unknown'] * len(self._df))
