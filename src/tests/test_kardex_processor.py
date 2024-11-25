"""
Tests for the Kardex processor functionality.
"""
import unittest
import pandas as pd
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import os
from datetime import datetime
import logging

from src.domain.vehicle_leasing.kardex_processor import KardexProcessor
from src.domain.vehicle_leasing.vehicle_fault import VehicleFault
from src.LogManager import LogManager

class TestKardexProcessor(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test."""
        self.processor = KardexProcessor()
        self.log_manager = LogManager()
        self.excel_path = '/Users/chrisyeo/Library/CloudStorage/OneDrive-Personal/Dev/windsurf/GBL/uploads/Kardex_for_vehicle_6_years_old.xlsx'
        self.sheets = [
            'Lifestyle (6yrs)',
            '10 ft (6yrs)',
            '14 ft (6yrs)',
            '16 ft (6yrs)',
            '24 ft (6yrs)'
        ]
        
        # Get domain config for VehicleFault creation
        self.domain_config = {
            'domains': {
                'vehicle_leasing': {
                    'name': 'vehicle_leasing',
                    'fault_attributes': [
                        'work_order', 'date', 'description', 'component', 'severity',
                        'nature_of_complaint', 'vehicle_type', 'location', 'status',
                        'mileage', 'completion_date', 'actual_finish_date', 'fault_codes',
                        'srr_number', 'customer_id', 'customer_name', 'next_recommendation',
                        'category', 'bill_number', 'cost', 'fault_category'
                    ]
                }
            }
        }
        
        # Ensure test file exists
        if not os.path.exists(self.excel_path):
            raise FileNotFoundError(f"Test Kardex file not found at {self.excel_path}")

    def create_test_excel(self, df, filename):
        """Helper to create test Excel files with proper header row."""
        writer = pd.ExcelWriter(filename, engine='openpyxl')
        # Create empty rows before header
        empty_df = pd.DataFrame(columns=df.columns)
        empty_df.to_excel(writer, sheet_name='Sheet1', index=False)
        empty_df.to_excel(writer, sheet_name='Sheet1', startrow=1, index=False)
        empty_df.to_excel(writer, sheet_name='Sheet1', startrow=2, index=False)
        # Write actual data with header at row 3
        df.to_excel(writer, sheet_name='Sheet1', startrow=3, index=False)
        writer.close()

    def test_read_kardex_file(self):
        """Test reading the actual Kardex Excel file."""
        self.log_manager.log("\nTesting Kardex file reading")
        
        # Test file existence
        self.assertTrue(os.path.exists(self.excel_path), 
                       f"Kardex file not found at {self.excel_path}")
        
        all_data = []
        for sheet_name in self.sheets:
            self.log_manager.log(f"\nReading sheet: {sheet_name}")
            
            # Read Excel sheet
            df = pd.read_excel(self.excel_path, sheet_name=sheet_name, header=3)
            
            # Verify DataFrame
            self.assertIsInstance(df, pd.DataFrame, 
                                f"Failed to create DataFrame for sheet {sheet_name}")
            self.assertFalse(df.empty, 
                            f"DataFrame is empty for sheet {sheet_name}")
            
            # Add vehicle_type
            df['vehicle_type'] = sheet_name
            
            # Verify required columns
            required_columns = ['WO No', 'Loc', 'ST', 'Mileage', 'Open Date', 
                              'Done Date', 'Actual Finish Date', 'Nature of Complaint', 
                              'Fault Codes', 'Job Description', 'vehicle_type']
            
            for col in required_columns:
                self.assertIn(col, df.columns, 
                            f"Required column {col} missing in sheet {sheet_name}")
            
            # Format DataFrame output with clear separators
            df_str = "\n" + "="*80 + "\n"
            df_str += "DataFrame Sample for sheet: " + sheet_name + "\n"
            df_str += "="*80 + "\n\n"
            
            # Get first 3 rows with all columns
            sample_df = df.head(3)
            
            # Configure pandas display options for better readability
            pd.set_option('display.max_colwidth', None)
            pd.set_option('display.max_columns', None)
            pd.set_option('display.width', None)
            pd.set_option('display.max_rows', None)
            
            # Add column info
            df_str += f"Total Rows: {len(df)}\n"
            df_str += f"Columns: {', '.join(df.columns)}\n\n"
            
            # Add sample data with all columns
            df_str += "First 3 rows with all columns:\n"
            print(sample_df.to_string())
            df_str += "\n" + "="*80 + "\n"
            
            # Log using LogManager
            self.log_manager.log(df_str)
            
            # Verify data types
            self.assertTrue(pd.api.types.is_numeric_dtype(df['Mileage']), 
                          f"Mileage column should be numeric in sheet {sheet_name}")
            self.assertTrue(pd.api.types.is_datetime64_any_dtype(df['Open Date']), 
                          f"Open Date should be datetime in sheet {sheet_name}")
            
            all_data.append(df)
        
        # Combine all sheets
        combined_df = pd.concat(all_data, ignore_index=True)
        self.assertGreater(len(combined_df), 0, 
                          "Combined DataFrame should not be empty")
        self.log_manager.log(f"\nTotal records in combined DataFrame: {len(combined_df)}")
        
        return combined_df

    def test_process_valid_excel(self):
        """Test processing the actual Kardex Excel file."""
        # Process each sheet and combine results
        all_results = []
        sheets = ['Lifestyle (6yrs)', '10 ft (6yrs)', '14 ft (6yrs)', '16 ft (6yrs)', '24 ft (6yrs)']
        
        for sheet_name in sheets:
            results = self.processor.process(self.excel_path, sheet_name=sheet_name)
            self.assertIsInstance(results, list)
            self.assertGreater(len(results), 0)
            
            # Verify each result has expected fields
            for result in results:
                self.assertIsInstance(result, dict)
                self.assertIn('work_order', result)
                self.assertIn('fault_codes', result)
                self.assertIn('nature_of_complaint', result)
                self.assertIn('job_description', result)
                self.assertIn('vehicle_type', result)
                self.assertEqual(result['vehicle_type'], sheet_name)
            
            all_results.extend(results)
        
        # Verify combined results
        self.assertGreater(len(all_results), 0)
        self.log_manager.log(f"Total records in combined DataFrame: {len(all_results)}")

    def test_empty_sheet(self):
        """Test processing a sheet with no data rows."""
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            # Create empty Excel file with header row at index 3
            writer = pd.ExcelWriter(tmp.name, engine='openpyxl')
            df = pd.DataFrame(columns=['WO No', 'Open Date', 'Nature of Complaint', 'Job Description'])
            df.to_excel(writer, sheet_name='Sheet1', startrow=3, index=False)
            writer.close()
            
            # Process empty sheet
            results = self.processor.process(tmp.name, sheet_name='Sheet1')
            
            # Verify empty results
            self.assertIsInstance(results, list)
            self.assertEqual(len(results), 0)
            
        os.unlink(tmp.name)

    def test_invalid_date_format(self):
        """Test processing with invalid date format."""
        df = pd.DataFrame({
            'Work Order': ['123'],
            'Date': ['invalid_date'],
            'Description': ['Test description'],
            'Classification': ['Test class']
        })
        
        excel_file = 'test_invalid_date.xlsx'
        df.to_excel(excel_file, index=False)
        
        processor = KardexProcessor()
        with self.assertRaises(ValueError) as context:
            processor.process(excel_file)
        
        self.assertEqual(str(context.exception), "Invalid date format")
        os.remove(excel_file)

    def test_work_order_formats(self):
        """Test handling of different work order formats."""
        test_cases = [
            ('123', '123'),           # String number
            (456, '456'),            # Integer
            ('ABC123', 'ABC123'),    # Alphanumeric
            ('123-456', '123456'),   # With hyphen
            ('WO 789', 'WO789')      # With space
        ]
        
        processor = KardexProcessor()
        for input_wo, expected_wo in test_cases:
            fault = VehicleFault(self.domain_config)
            fault.set_attribute('work_order', input_wo)
            processor._clean_work_order(fault)
            self.assertEqual(
                fault.get_attribute('work_order'),
                expected_wo,
                f"Work order cleaning failed for input: {input_wo}"
            )

    def test_description_cleaning(self):
        """Test description cleaning and component/severity detection."""
        processor = KardexProcessor()
        
        # Test case 1: Multiple spaces and component detection
        fault = VehicleFault(self.domain_config)
        fault.set_attribute('description', '  Engine   making  loud  noise   ')
        processor._clean_description(fault)
        self.assertEqual(fault.get_attribute('description'), 'Engine making loud noise')
        self.assertEqual(fault.get_attribute('component'), 'engine')
        
        # Test case 2: Severity detection - high
        fault = VehicleFault(self.domain_config)
        fault.set_attribute('description', 'Urgent brake failure needs immediate attention')
        processor._clean_description(fault)
        self.assertEqual(fault.get_attribute('severity'), 'high')
        self.assertEqual(fault.get_attribute('component'), 'brake')
        
        # Test case 3: Severity detection - low
        fault = VehicleFault(self.domain_config)
        fault.set_attribute('description', 'Routine tire inspection and rotation')
        processor._clean_description(fault)
        self.assertEqual(fault.get_attribute('severity'), 'low')
        self.assertEqual(fault.get_attribute('component'), 'tire')
        
        # Test case 4: Empty description
        fault = VehicleFault(self.domain_config)
        fault.set_attribute('description', '')
        processor._clean_description(fault)
        self.assertEqual(fault.get_attribute('description'), '')

    @patch('src.ChatGPT.ChatGPT')
    def test_fault_classification(self, mock_gpt):
        """Test fault classification with ChatGPT integration."""
        processor = KardexProcessor()
        
        # Mock ChatGPT response
        mock_gpt.return_value.get_completion.return_value = 'Mechanical'
        
        # Test case 1: New classification
        fault = VehicleFault(self.domain_config)
        fault.set_attribute('nature_of_complaint', 'Engine noise')
        fault.set_attribute('description', 'Loud knocking sound from engine')
        processor._classify_fault_category(fault)
        self.assertEqual(fault.get_attribute('fault_category'), 'Mechanical')
        
        # Test case 2: Cached classification
        fault2 = VehicleFault(self.domain_config)
        fault2.set_attribute('nature_of_complaint', 'Engine noise')
        fault2.set_attribute('description', 'Loud knocking sound from engine')
        processor._classify_fault_category(fault2)
        # Should use cached value without calling ChatGPT again
        self.assertEqual(mock_gpt.return_value.get_completion.call_count, 1)
        
        # Test case 3: Invalid category from GPT
        mock_gpt.return_value.get_completion.return_value = 'InvalidCategory'
        fault3 = VehicleFault(self.domain_config)
        fault3.set_attribute('nature_of_complaint', 'New issue')
        fault3.set_attribute('description', 'Some new problem')
        processor._classify_fault_category(fault3)
        self.assertEqual(fault3.get_attribute('fault_category'), 'Other')
        
        # Test case 4: GPT error handling
        mock_gpt.return_value.get_completion.side_effect = Exception('API Error')
        fault4 = VehicleFault(self.domain_config)
        fault4.set_attribute('nature_of_complaint', 'Another issue')
        fault4.set_attribute('description', 'Another problem')
        processor._classify_fault_category(fault4)
        self.assertEqual(fault4.get_attribute('fault_category'), 'Other')

    def test_date_formats(self):
        """Test handling of different date formats."""
        processor = KardexProcessor()
        
        # Test case 1: pandas Timestamp
        fault = VehicleFault(self.domain_config)
        date = pd.Timestamp('2023-01-01 10:30:00')
        fault.set_attribute('date', date)
        processor._format_dates(fault)
        self.assertEqual(fault.get_attribute('date'), '2023-01-01 10:30:00')
        
        # Test case 2: datetime object
        fault = VehicleFault(self.domain_config)
        date = datetime(2023, 1, 1, 10, 30, 0)
        fault.set_attribute('date', date)
        processor._format_dates(fault)
        self.assertEqual(fault.get_attribute('date'), '2023-01-01 10:30:00')
        
        # Test case 3: Invalid date type
        fault = VehicleFault(self.domain_config)
        fault.set_attribute('date', '2023-01-01')  # String date
        with self.assertRaises(ValueError) as context:
            processor._format_dates(fault)
        self.assertEqual(str(context.exception), "Invalid date format")

    def test_transformations_error_handling(self):
        """Test error handling in transformation pipeline."""
        processor = KardexProcessor()
        
        # Test processing with actual data
        results = processor.process(self.excel_path, sheet_name='Lifestyle (6yrs)')
        
        # Verify results
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        
        # Verify each result has expected fields
        for result in results:
            self.assertIsInstance(result, dict)
            self.assertIn('work_order', result)
            self.assertIn('fault_codes', result)
            self.assertIn('nature_of_complaint', result)
            self.assertIn('job_description', result)
            self.assertIn('vehicle_type', result)
            self.assertEqual(result['vehicle_type'], 'Lifestyle (6yrs)')

    def test_dataframe_handling(self):
        """Test comprehensive DataFrame handling scenarios."""
        processor = KardexProcessor()
        
        # Test case 1: DataFrame with missing columns
        df_missing_cols = pd.DataFrame({
            'WO No': ['123'],
            # Missing 'Open Date'
            'Nature of Complaint': ['Test complaint'],
            'Job Description': ['Test description']
        })
        excel_file = 'test_missing_cols.xlsx'
        self.create_test_excel(df_missing_cols, excel_file)
        with self.assertRaises(ValueError) as context:
            processor.process(excel_file)
        self.assertIn("Missing required columns", str(context.exception))
        os.remove(excel_file)
        
        # Test case 2: DataFrame with null values
        df_null_values = pd.DataFrame({
            'WO No': ['123', None, '456'],
            'Open Date': [pd.Timestamp('2023-01-01'), pd.Timestamp('2023-01-02'), None],
            'Nature of Complaint': ['Test complaint', None, 'Another complaint'],
            'Job Description': ['Test description', 'Another description', None]
        })
        excel_file = 'test_null_values.xlsx'
        self.create_test_excel(df_null_values, excel_file)
        results = processor.process(excel_file)
        self.assertEqual(len(results), 3)  # Should process all rows, handling nulls
        os.remove(excel_file)
        
        # Test case 3: DataFrame with different data types
        df_mixed_types = pd.DataFrame({
            'WO No': [123, '456', 'ABC-789'],  # Mixed numeric and string
            'Open Date': [
                pd.Timestamp('2023-01-01'),
                datetime(2023, 1, 2),
                pd.Timestamp('2023-01-03')
            ],
            'Nature of Complaint': ['Test', 123, 'Another'],  # Mixed string and numeric
            'Job Description': ['Test', 'Test2', 'Test3']
        })
        excel_file = 'test_mixed_types.xlsx'
        self.create_test_excel(df_mixed_types, excel_file)
        results = processor.process(excel_file)
        self.assertEqual(len(results), 3)
        # Verify work order formatting for different types
        self.assertEqual(results[0]['work_order'], '123')
        self.assertEqual(results[1]['work_order'], '456')
        self.assertEqual(results[2]['work_order'], 'ABC789')
        os.remove(excel_file)
        
        # Test case 4: DataFrame with duplicate rows
        df_duplicates = pd.DataFrame({
            'WO No': ['123', '123', '456'],
            'Open Date': [
                pd.Timestamp('2023-01-01'),
                pd.Timestamp('2023-01-01'),
                pd.Timestamp('2023-01-02')
            ],
            'Nature of Complaint': ['Test', 'Test', 'Another'],
            'Job Description': ['Test', 'Test', 'Test2']
        })
        excel_file = 'test_duplicates.xlsx'
        self.create_test_excel(df_duplicates, excel_file)
        results = processor.process(excel_file)
        self.assertEqual(len(results), 3)  # Should process all rows, including duplicates
        os.remove(excel_file)
        
        # Test case 5: DataFrame with special characters
        df_special_chars = pd.DataFrame({
            'WO No': ['123-ABC', '456/DEF', '789\nGHI'],
            'Open Date': [
                pd.Timestamp('2023-01-01'),
                pd.Timestamp('2023-01-02'),
                pd.Timestamp('2023-01-03')
            ],
            'Nature of Complaint': ['Test\nwith\nnewlines', 'Test,with,commas', 'Test with spaces'],
            'Job Description': ['Test#1', 'Test@2', 'Test&3']
        })
        excel_file = 'test_special_chars.xlsx'
        self.create_test_excel(df_special_chars, excel_file)
        results = processor.process(excel_file)
        self.assertEqual(len(results), 3)
        # Verify special character handling
        self.assertEqual(results[0]['work_order'], '123ABC')
        self.assertEqual(results[1]['work_order'], '456DEF')
        self.assertEqual(results[2]['work_order'], '789GHI')
        os.remove(excel_file)

if __name__ == '__main__':
    unittest.main()
