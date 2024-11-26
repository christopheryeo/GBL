import os
import sys
import pandas as pd
from datetime import datetime
import logging

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from PandasChat import PandasChat
from LogManager import LogManager
from VehicleFaults import VehicleFault

# Configure logging
logging.basicConfig(
    filename='application.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_specific_query')

class TracingLogManager(LogManager):
    """Extended LogManager that prints logs immediately for tracing."""
    def log(self, message, level=None):
        logger.info(f"[TRACE] {message}")
        if level:
            logger.info(f"[LEVEL] {level}")
        super().log(message)

def analyze_vehicle_types(df):
    """Analyze vehicle types and their fault counts."""
    logger.info("Starting vehicle type analysis")
    
    if 'Vehicle Type' in df.columns:
        vehicle_counts = df['Vehicle Type'].value_counts()
        logger.info("Vehicle type counts calculated")
        
        print("\nFault Count by Vehicle Type:")
        print("-" * 40)
        for vehicle_type, count in vehicle_counts.items():
            print(f"{vehicle_type}: {count} faults")
            logger.info(f"Vehicle type {vehicle_type}: {count} faults")
        
        # Calculate percentages
        percentages = (vehicle_counts / len(df) * 100).round(2)
        logger.info("Percentage distribution calculated")
        
        print("\nPercentage Distribution:")
        print("-" * 40)
        for vehicle_type, percentage in percentages.items():
            print(f"{vehicle_type}: {percentage}%")
            logger.info(f"Vehicle type {vehicle_type}: {percentage}%")
    else:
        logger.warning("No Vehicle Type column found in the data")
        print("No Vehicle Type column found in the data")

def format_user_response(df):
    """Format a clear response for end users."""
    if 'Vehicle Type' not in df.columns:
        return "No vehicle type information available in the data."
    
    vehicle_counts = df['Vehicle Type'].value_counts()
    total_faults = len(df)
    percentages = (vehicle_counts / total_faults * 100).round(2)
    
    response = [
        "Here's the breakdown of faults by vehicle type:",
        "\nTotal Faults: " + str(total_faults),
        "\nDistribution by Vehicle Type:",
        "-" * 40
    ]
    
    for vehicle_type in vehicle_counts.index:
        count = vehicle_counts[vehicle_type]
        percentage = percentages[vehicle_type]
        response.append(f"{vehicle_type}:")
        response.append(f"  • Number of faults: {count}")
        response.append(f"  • Percentage: {percentage}%")
    
    response.append("\nKey Observations:")
    response.append(f"• {vehicle_counts.index[0]} vehicles have the highest number of faults ({vehicle_counts.iloc[0]} faults, {percentages.iloc[0]}% of total)")
    if len(vehicle_counts) > 1:
        response.append(f"• The remaining {len(vehicle_counts)-1} vehicle types account for {100-percentages.iloc[0]:.2f}% of faults")
    
    formatted_response = "\n".join(response)
    
    # Log the formatted response
    logger.info("\nUSER RESPONSE:")
    logger.info("=" * 40)
    for line in formatted_response.split('\n'):
        logger.info(line)
    logger.info("=" * 40)
    
    return formatted_response

def load_kardex_data():
    """Load and prepare the Kardex data."""
    logger.info("Starting data loading process")
    
    data_path = os.path.join(os.path.dirname(__file__), '..', 'uploads', 'Kardex_for_vehicle_6_years_old.xlsx')
    logger.info(f"Loading data from: {data_path}")
    
    # Get all sheets
    excel_file = pd.ExcelFile(data_path)
    sheet_names = excel_file.sheet_names
    logger.info(f"Found sheets: {sheet_names}")
    
    # Initialize an empty list to store DataFrames
    dfs = []
    
    # Read each sheet and add vehicle type
    for sheet_name in sheet_names:
        # Read Excel file with header on row 3 (0-based index)
        df = pd.read_excel(data_path, sheet_name=sheet_name, header=3)
        # Add vehicle type from sheet name
        df['Vehicle Type'] = sheet_name.split(' (')[0]  # Remove the '(6yrs)' part
        dfs.append(df)
    
    # Combine all DataFrames
    combined_df = pd.concat(dfs, ignore_index=True)
    logger.info("Combined data from all sheets")
    
    print("\nDataFrame Info after loading:")
    print("-" * 40)
    print("Columns:", combined_df.columns.tolist())
    print("Shape:", combined_df.shape)
    print("\nFirst few rows of data:")
    print(combined_df.head(2))
    
    logger.info(f"DataFrame loaded with shape: {combined_df.shape}")
    logger.info(f"Columns: {combined_df.columns.tolist()}")
    
    # Analyze vehicle types
    analyze_vehicle_types(combined_df)
    
    return combined_df

def trace_query_processing(query):
    """Trace the processing of a specific query through the system."""
    logger.info(f"{'='*80}")
    logger.info(f"TRACING QUERY: {query}")
    logger.info(f"{'='*80}")
    
    print(f"\n{'='*80}")
    print(f"TRACING QUERY: {query}")
    print(f"{'='*80}")
    
    # Initialize components with tracing
    log_manager = TracingLogManager()
    logger.info("Initialized TracingLogManager")
    
    # Load and prepare Kardex data
    try:
        df = load_kardex_data()
        chat = PandasChat(df_data=df, log_manager=log_manager)
        logger.info("Successfully initialized PandasChat with Kardex data")
        print("\nSuccessfully initialized PandasChat with Kardex data")
    except Exception as e:
        error_msg = f"Error loading Kardex data: {str(e)}"
        logger.error(error_msg)
        print(f"\n{error_msg}")
        return None
    
    try:
        # Step 1: Query Preprocessing
        logger.info("\nSTEP 1: Query Preprocessing")
        print("\n[STEP 1] Query Preprocessing")
        print("-" * 40)
        print(f"Original Query: {query}")
        logger.info(f"Original Query: {query}")
        
        # Step 2: Data Analysis
        logger.info("\nSTEP 2: Data Analysis")
        print("\n[STEP 2] Data Analysis")
        print("-" * 40)
        analyze_vehicle_types(df)
        
        # Step 3: Response Generation
        logger.info("\nSTEP 3: Response Generation")
        print("\n[STEP 3] Response Generation")
        print("-" * 40)
        response = format_user_response(df)
        print("\nUSER RESPONSE:")
        print("=" * 40)
        print(response)
        print("=" * 40)
        
        return response
        
    except Exception as e:
        error_msg = f"An error occurred: {str(e)}"
        logger.error(error_msg)
        print(f"\n[ERROR] {error_msg}")
        return None

def main():
    """Test specific query for fault count by vehicle type."""
    logger.info("Starting test execution")
    query = "What is the number of faults per vehicle type?"
    trace_query_processing(query)
    logger.info("Test execution completed")

if __name__ == "__main__":
    main()
