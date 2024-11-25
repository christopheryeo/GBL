import sys
import os
from pathlib import Path
from collections import Counter, defaultdict
import pandas as pd

# Add the src directory to the Python path
src_dir = str(Path(__file__).parent.parent / 'src')
if src_dir not in sys.path:
    sys.path.append(src_dir)

from VehicleFaults import VehicleFault
from ExcelProcessor import ExcelProcessor
from LogManager import LogManager

def analyze_fault_categories():
    """Analyze the distribution of fault categories in the Kardex data."""
    try:
        # Initialize components
        log_manager = LogManager()
        processor = ExcelProcessor(log_manager)
        
        # Load the Kardex file
        kardex_path = str(Path(__file__).parent.parent / 'uploads' / 'Kardex_for_vehicle_6_years_old.xlsx')
        if not os.path.exists(kardex_path):
            log_manager.log(f"Kardex file not found at {kardex_path}")
            return
            
        # Process the Excel file using the project's ExcelProcessor
        result = processor.process_excel(kardex_path, os.path.basename(kardex_path))
        if result is None or 'data' not in result:
            log_manager.log("Failed to process Kardex file")
            return
            
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
        if categories is None:
            log_manager.log("Failed to categorize any faults")
            return
            
        main_cats = categories['main'].tolist()
        sub_cats = categories['sub'].tolist()
        confidences = categories['confidence'].tolist()
        
        if not main_cats:
            log_manager.log("Failed to categorize any faults")
            return
        
        # Count main categories
        main_counter = Counter(main_cats)
        total_faults = len(main_cats)
        
        # Count subcategories per main category
        sub_counter = defaultdict(Counter)
        for main, sub, conf in zip(main_cats, sub_cats, confidences):
            if sub:  # Only count if subcategory exists
                sub_counter[main][sub] += 1
        
        # Calculate average confidence per category
        confidence_by_cat = defaultdict(list)
        for main, conf in zip(main_cats, confidences):
            confidence_by_cat[main].append(conf)
        avg_confidence = {cat: sum(scores)/len(scores) 
                         for cat, scores in confidence_by_cat.items()}
        
        # Log results using the project's logging system
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
        for main_cat, sub_counts in sub_counter.items():
            if sub_counts:  # Only show categories that have subcategories
                log_manager.log(f"\n{main_cat}:")
                main_total = main_counter[main_cat]
                for sub_cat, count in sub_counts.most_common():
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
        
    except Exception as e:
        log_manager.log(f"Error analyzing fault categories: {str(e)}")
        import traceback
        log_manager.log(traceback.format_exc())

if __name__ == "__main__":
    analyze_fault_categories()
