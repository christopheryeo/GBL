"""
Tests for the processor factory functionality.
"""
import unittest
import tempfile
import pandas as pd
from pathlib import Path
from src.processors import ProcessorFactory
from src.domain.vehicle_leasing.kardex_processor import KardexProcessor

class TestProcessorFactory(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test."""
        self.test_data = {
            'WO No': ['W001'],
            'Open Date': ['2024-01-01'],
            'Job Description': ['Test']
        }
        
    def create_test_excel(self, data=None):
        """Create a temporary Excel file for testing."""
        if data is None:
            data = self.test_data
            
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            df = pd.DataFrame(data)
            df.to_excel(tmp.name, index=False)
            return tmp.name
            
    def test_detect_format(self):
        """Test format detection."""
        excel_file = self.create_test_excel()
        try:
            format_type = ProcessorFactory.detect_format(excel_file)
            self.assertEqual(format_type, 'kardex')  # Assuming 'kardex' is the expected format
        finally:
            Path(excel_file).unlink()
            
    def test_create_processor(self):
        """Test processor creation."""
        processor = ProcessorFactory.create('kardex')
        self.assertIsInstance(processor, KardexProcessor)
        
    def test_invalid_format(self):
        """Test handling of invalid format."""
        with self.assertRaises(ValueError):
            ProcessorFactory.create('invalid_format')
            
    def test_detect_format_invalid_file(self):
        """Test format detection with invalid file."""
        with tempfile.NamedTemporaryFile(suffix='.txt') as tmp:
            with self.assertRaises(ValueError):
                ProcessorFactory.detect_format(tmp.name)

if __name__ == '__main__':
    unittest.main()
