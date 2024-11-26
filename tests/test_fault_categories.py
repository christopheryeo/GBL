import sys
import os
from pathlib import Path
from collections import Counter, defaultdict
import pandas as pd
import pytest

# Add the src directory to the Python path
src_dir = str(Path(__file__).parent.parent / 'src')
if src_dir not in sys.path:
    sys.path.append(src_dir)

from VehicleFaults import VehicleFault
from ExcelProcessor import ExcelProcessor
from LogManager import LogManager

def test_analyze_fault_categories():
    """Test the fault categorization functionality."""
    try:
        # Initialize components
        log_manager = LogManager()
        processor = ExcelProcessor(log_manager)
        
        # Load the Kardex file
        kardex_path = str(Path(__file__).parent.parent / 'uploads' / 'Kardex_for_vehicle_6_years_old.xlsx')
        assert os.path.exists(kardex_path), f"Kardex file not found at {kardex_path}"
            
        # Process the Excel file using the project's ExcelProcessor
        result = processor.process_excel(kardex_path, os.path.basename(kardex_path))
        assert result is not None and 'data' in result, "Failed to process Kardex file"
            
        # Create DataFrame and initialize VehicleFault
        df = pd.DataFrame(result['data'])
        faults = VehicleFault(df)
        
        # Process each fault description individually
        fault_descriptions = df['Description'].fillna('').astype(str).tolist()
        main_cats = []
        sub_cats = []
        confidences = []
        
        # Categorize all faults
        categories = faults.categorize_faults()
        assert categories is not None, "Failed to categorize any faults"
        
        main_cats = categories['main'].tolist()
        sub_cats = categories['sub'].tolist()
        confidences = categories['confidence'].tolist()
        
        # Count occurrences of each category
        main_counter = Counter(main_cats)
        sub_counter = Counter(sub_cats)
        
        # Calculate percentages
        total_faults = len(main_cats)
        main_percentages = {cat: (count / total_faults * 100) for cat, count in main_counter.items()}
        sub_percentages = {cat: (count / total_faults * 100) for cat, count in sub_counter.items()}
        
        # Group subcategories by main category
        sub_by_main = defaultdict(list)
        for main, sub in zip(main_cats, sub_cats):
            if pd.notna(sub) and sub:  # Only include non-empty subcategories
                sub_by_main[main].append(sub)
                
        # Calculate subcategory distributions within each main category
        sub_distributions = {}
        for main_cat, subs in sub_by_main.items():
            sub_count = Counter(subs)
            total = len(subs)
            sub_distributions[main_cat] = {sub: (count / total * 100) 
                                         for sub, count in sub_count.items()}
        
        # Calculate average confidence per category
        confidence_by_cat = defaultdict(list)
        for main, conf in zip(main_cats, confidences):
            confidence_by_cat[main].append(conf)
        avg_confidence = {cat: sum(scores)/len(scores) 
                         for cat, scores in confidence_by_cat.items()}

        # Log detailed results
        log_manager.log("\n=== Fault Category Distribution Analysis ===\n")
        
        # Main categories
        log_manager.log("Main Categories (with confidence):")
        log_manager.log("-" * 50)
        for category, count in main_counter.most_common():
            percentage = (count / total_faults) * 100
            conf = avg_confidence[category]
            log_manager.log(f"{category:25} {count:5d} ({percentage:5.2f}%) [conf: {conf:.2f}]")
        
        # Subcategories
        log_manager.log("\nSubcategory Distribution:")
        log_manager.log("-" * 50)
        for main_cat, sub_counts in sub_by_main.items():
            if sub_counts:  # Only show categories that have subcategories
                log_manager.log(f"\n{main_cat}:")
                main_total = main_counter[main_cat]
                for sub_cat, count in Counter(sub_counts).most_common():
                    percentage = (count / main_total) * 100
                    log_manager.log(f"  {sub_cat:20} {count:5d} ({percentage:5.2f}%)")
        
        # Show uncategorized faults
        log_manager.log("\nUncategorized Faults:")
        log_manager.log("-" * 50)
        for i in range(len(df)):
            if main_cats[i] == 'Uncategorized':
                desc = str(df['Job Description'].iloc[i]).strip()
                complaint = str(df['Nature of Complaint'].iloc[i]).strip()
                combined = f"{desc} | {complaint}" if desc and complaint else desc or complaint
                log_manager.log(f"- {combined}")

        # Low confidence categories
        low_conf_threshold = 0.5
        low_conf_cats = {cat: conf for cat, conf in avg_confidence.items() 
                        if conf < low_conf_threshold}
        
        if low_conf_cats:
            log_manager.log("\nCategories with Low Confidence (<0.5):")
            log_manager.log("-" * 50)
            for cat, conf in sorted(low_conf_cats.items(), key=lambda x: x[1]):
                log_manager.log(f"{cat:25} [confidence: {conf:.2f}]")
        
        # Verify expected categories are present
        expected_main_categories = {'Wheels', 'Maintenance', 'HVAC'}
        expected_sub_categories = {'Tires', 'Inspection', 'Cooling'}
        
        assert all(cat in main_counter for cat in expected_main_categories), \
            "Missing expected main categories"
        assert all(cat in sub_counter for cat in expected_sub_categories), \
            "Missing expected sub categories"
        
        # Verify category percentages
        assert main_percentages['Wheels'] > 20, "Wheels category percentage too low"
        assert main_percentages['Maintenance'] > 15, "Maintenance category percentage too low"
        assert main_percentages['HVAC'] > 10, "HVAC category percentage too low"
        
        # Verify subcategory distributions
        assert sub_distributions['Wheels']['Tires'] > 90, "Tires subcategory percentage too low"
        assert sub_distributions['Maintenance']['Inspection'] > 75, "Inspection subcategory percentage too low"
        assert sub_distributions['HVAC']['Cooling'] > 90, "Cooling subcategory percentage too low"
        
    except Exception as e:
        raise AssertionError(f"Test failed: {str(e)}")

if __name__ == "__main__":
    pytest.main([__file__])
