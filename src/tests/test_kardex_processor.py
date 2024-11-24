"""
Tests for the Kardex processor functionality.
"""
import unittest
import pandas as pd
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.domain.vehicle_leasing.kardex_processor import KardexProcessor
from src.domain.vehicle_leasing.vehicle_fault import VehicleFault

class TestKardexProcessor(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test."""
        self.processor = KardexProcessor()
        self.test_data = {
            'WO No': ['W001', 'W002', 'W003'],
            'Loc': ['LOC1', 'LOC2', 'LOC3'],
            'ST': ['Open', 'Closed', 'In Progress'],
            'Mileage': [50000, 60000, 70000],
            'Open Date': ['2024-01-01 09:00:00', '2024-01-02 10:00:00', '2024-01-03 11:00:00'],
            'Done Date': ['2024-01-02 09:00:00', '2024-01-03 10:00:00', '2024-01-04 11:00:00'],
            'Actual Finish Date': ['2024-01-02 10:00:00', '2024-01-03 11:00:00', '2024-01-04 12:00:00'],
            'Nature of Complaint': ['Engine noise', 'Brake squeak', 'Transmission slip'],
            'Fault Codes': ['F001', 'F002', 'F003'],
            'Job Description': ['Engine repair', 'Brake service', 'Transmission fix'],
            'SRR No.': ['SRR1', 'SRR2', 'SRR3'],
            'Mechanic Name': ['John', 'Jane', 'Bob'],
            'Customer': ['CUST1', 'CUST2', 'CUST3'],
            'Customer Name': ['John Doe', 'Jane Smith', 'Bob Johnson'],
            'Recommendation 4 next': ['Check in 3 months', 'Replace pads', 'Monitor fluid'],
            'Cat': ['A', 'B', 'C'],
            'Lead Tech': ['Tech1', 'Tech2', 'Tech3'],
            'Bill No.': ['B001', 'B002', 'B003'],
            'Intercoamt': [100, 200, 300],
            'Custamt': [150.50, 250.75, 350.25]
        }
        
    def create_test_excel(self, data=None, include_header=True):
        """Create a temporary Excel file for testing."""
        if data is None:
            data = self.test_data
            
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            df = pd.DataFrame(data)
            if include_header:
                df.to_excel(tmp.name, index=False)
            else:
                df.to_excel(tmp.name, index=False, header=False)
            return tmp.name
            
    def test_process_valid_excel(self):
        """Test processing a valid Excel file."""
        excel_file = self.create_test_excel()
        try:
            results = self.processor.process(excel_file)
            self.assertEqual(len(results), 3)
            self.assertIsInstance(results[0], dict)
            
            # Check mapped fields
            first_result = results[0]
            self.assertEqual(first_result['work_order'], 'W001')
            self.assertEqual(first_result['date'], '2024-01-01 09:00:00')
            self.assertEqual(first_result['completion_date'], '2024-01-02 09:00:00')
            self.assertEqual(first_result['actual_finish_date'], '2024-01-02 10:00:00')
            self.assertEqual(first_result['description'], 'Engine repair')
            self.assertEqual(first_result['complaint'], 'Engine noise')
            self.assertEqual(first_result['fault_codes'], 'F001')
            self.assertEqual(first_result['cost'], 150.50)
            self.assertEqual(first_result['status'], 'Open')
            self.assertEqual(first_result['category'], 'A')
            self.assertEqual(first_result['mileage'], 50000)
            self.assertEqual(first_result['mechanic'], 'John')
            self.assertEqual(first_result['customer_name'], 'John Doe')
            self.assertEqual(first_result['next_recommendation'], 'Check in 3 months')
            
            # Check derived fields
            self.assertEqual(first_result['component'], 'engine')  # Derived from description
            self.assertIn(first_result['severity'], ['low', 'medium', 'high'])  # Derived from description
            
        finally:
            Path(excel_file).unlink()
            
    def test_empty_excel(self):
        """Test processing an empty Excel file."""
        empty_data = {col: [] for col in self.test_data.keys()}
        excel_file = self.create_test_excel(empty_data)
        try:
            results = self.processor.process(excel_file)
            self.assertEqual(len(results), 0)
        finally:
            Path(excel_file).unlink()
                
    def test_missing_required_columns(self):
        """Test processing Excel with missing required columns."""
        invalid_data = {
            'WO No': ['W001'],  # Missing Open Date and Job Description
            'ST': ['Open']
        }
        excel_file = self.create_test_excel(invalid_data)
        try:
            with self.assertRaises(ValueError):
                self.processor.process(excel_file)
        finally:
            Path(excel_file).unlink()
            
    def test_invalid_date_format(self):
        """Test processing Excel with invalid date format."""
        invalid_data = self.test_data.copy()
        invalid_data['Open Date'] = ['invalid-date', '2024-01-02 10:00:00', '2024-01-03 11:00:00']
        excel_file = self.create_test_excel(invalid_data)
        try:
            results = self.processor.process(excel_file)
            self.assertEqual(len(results), 2)  # Should skip the invalid row
        finally:
            Path(excel_file).unlink()

if __name__ == '__main__':
    unittest.main()
