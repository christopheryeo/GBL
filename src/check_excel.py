import pandas as pd
import os

excel_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads', 'Kardex_for_vehicle_6_years_old.xlsx')

# Read without headers
df = pd.read_excel(excel_file, header=None)

print("First 10 rows of data:")
print("-" * 50)
for idx, row in df.head(10).iterrows():
    print(f"\nRow {idx}:")
    for col, value in row.items():
        if pd.notna(value):  # Only show non-null values
            print(f"Column {col}: {value}")
