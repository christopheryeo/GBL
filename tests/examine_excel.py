import pandas as pd
import os

def examine_excel():
    """Examine the Excel file structure."""
    file_path = os.path.join(os.path.dirname(__file__), '..', 'uploads', 'Kardex_for_vehicle_6_years_old.xlsx')
    
    # Get sheet names
    excel_file = pd.ExcelFile(file_path)
    print("Sheet Names:", excel_file.sheet_names)
    
    # Read the data
    df = pd.read_excel(file_path, header=3)
    
    print("\nColumns:")
    for col in df.columns:
        print(f"- {col}")
    
    print("\nFirst few rows:")
    print(df.head(2).to_string())

if __name__ == "__main__":
    examine_excel()
