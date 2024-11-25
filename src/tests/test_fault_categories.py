"""
Test script for fault categorization system.
Analyzes fault categories from consolidated Kardex Excel file.
"""

import os
import sys
import logging
from pathlib import Path
import yaml

# Add src directory to Python path for imports
src_path = str(Path(__file__).parent.parent)
sys.path.append(src_path)

def setup_logging():
    """Configure logging to write to application.log"""
    logging.basicConfig(
        filename='application.log',
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def get_fault_categories():
    """Load fault categories from YAML file"""
    config_dir = os.path.join(src_path, 'config')
    categories_file = os.path.join(config_dir, 'fault_categories.yaml')
    
    with open(categories_file, 'r') as f:
        data = yaml.safe_load(f)
    return data.get('fault_categories', {})

def main():
    # Setup logging
    logger = setup_logging()
    
    # Load fault categories
    categories = get_fault_categories()
    
    # Log category counts
    logger.info("\n=== Fault Categories Analysis ===")
    logger.info(f"Total major categories: {len(categories)}")
    
    # Log each category and its subcategory count
    for category, subcategories in sorted(categories.items()):
        logger.info(f"{category}: {len(subcategories)} subcategories")

if __name__ == "__main__":
    main()
