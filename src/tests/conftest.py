"""
Pytest configuration file for shared fixtures.
"""
import pytest
import tempfile
import os
from pathlib import Path

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname

@pytest.fixture
def test_data_dir():
    """Return the path to test data directory."""
    return Path(__file__).parent / 'data'

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment before each test."""
    # Store original environment
    original_env = dict(os.environ)
    
    # Setup test environment variables
    os.environ['TEST_MODE'] = 'true'
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)
