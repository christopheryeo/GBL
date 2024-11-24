"""
Tests for the VehicleFault entity.
"""
import unittest
from datetime import datetime
from src.domain.vehicle_leasing.vehicle_fault import VehicleFault

class TestVehicleFault(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test."""
        self.domain_config = {
            'name': 'Vehicle Leasing',
            'description': 'Test domain config'
        }
        self.fault = VehicleFault(self.domain_config)
        
    def test_basic_attributes(self):
        """Test setting and getting basic attributes."""
        test_data = {
            'work_order': 'W001',
            'date': '2024-01-01 09:00:00',
            'description': 'Test fault',
            'fault_codes': 'F001',
            'status': 'Open',
            'category': 'A',
            'mileage': 50000
        }
        
        for key, value in test_data.items():
            self.fault.set_attribute(key, value)
            self.assertEqual(self.fault.get_attribute(key), value)
            
    def test_date_validation(self):
        """Test date format validation."""
        # Valid date
        self.fault.set_attribute('date', '2024-01-01 09:00:00')
        self.assertTrue(self.fault.validate())
        
        # Invalid date
        self.fault.set_attribute('date', 'invalid-date')
        self.assertFalse(self.fault.validate())
        
    def test_required_attributes(self):
        """Test validation of required attributes."""
        # Missing required attributes
        self.assertFalse(self.fault.validate())
        
        # Set required attributes
        self.fault.set_attribute('work_order', 'W001')
        self.fault.set_attribute('date', '2024-01-01 09:00:00')
        self.fault.set_attribute('description', 'Test fault')
        self.assertTrue(self.fault.validate())
        
    def test_cost_validation(self):
        """Test cost value validation."""
        # Valid cost
        self.fault.set_attribute('cost', '100.50')
        self.assertEqual(self.fault.get_cost(), 100.50)
        
        # Invalid cost
        self.fault.set_attribute('cost', 'invalid')
        self.assertEqual(self.fault.get_cost(), 0.0)
        
    def test_mileage_validation(self):
        """Test mileage value validation."""
        # Valid mileage
        self.fault.set_attribute('mileage', '50000')
        self.assertEqual(self.fault.get_mileage(), 50000)
        
        # Invalid mileage
        self.fault.set_attribute('mileage', 'invalid')
        self.assertIsNone(self.fault.get_mileage())
        
    def test_to_dict(self):
        """Test conversion to dictionary."""
        test_data = {
            'work_order': 'W001',
            'date': '2024-01-01 09:00:00',
            'description': 'Test fault',
            'fault_codes': 'F001',
            'status': 'Open'
        }
        
        for key, value in test_data.items():
            self.fault.set_attribute(key, value)
            
        result = self.fault.to_dict()
        for key, value in test_data.items():
            self.assertEqual(result.get(key), value)

if __name__ == '__main__':
    unittest.main()
