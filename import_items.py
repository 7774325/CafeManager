import os
import django
import pandas as pd
import sys

# 1. FIX PATHING
# This gets the absolute path of the folder containing THIS script
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(CURRENT_DIR)

# 2. SETUP DJANGO
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CafeManager.settings')
try:
    django.setup()
except Exception as e:
    print(f"DJANGO SETUP ERROR: {e}")
    sys.exit(1)

from core.models import Product, Outlet

def run_import():
    # Define the CSV name precisely
    FILENAME = 'export_items.csv'
    csv_path = os.path.join(CURRENT_DIR, FILENAME)
    
    print(f"--- DIAGNOSTICS ---")
    print(f"Script Location: {CURRENT_DIR}")
    print(f"Looking for CSV at: {csv_path}")
    
    if not os.path.exists(csv_path):
        print(f"ERROR: File '{FILENAME}' not found in the script directory.")
        print(f"Files actually in this folder: {os.listdir(CURRENT_DIR)}")
        return

    # 3. LOAD DATA
    try:
        # We use low_memory=False to handle mixed types in Loyverse exports
        df = pd.read_csv(csv_path, low_memory=False)
    except Exception as e:
        print(f"CSV READ ERROR: {e}")
        return
    
    # 4. OUTLET INITIALIZATION
    outlet, _ = Outlet.objects.get_or_create(
        name='Chillo', 
        defaults={'location': 'Main'}
    )

    print(f"--- STARTING IMPORT ({len(df)} rows found) ---")

    success_count = 0
    for index, row in df.iterrows():
        try:
            # Clean data using column names from your uploaded CSV
            name = row.get('Name')
            if pd.isna(name): continue

            raw_cat = row.get('Category')
            category = str(raw_cat) if pd.notna(raw_cat) else "General"
            
            # Map prices - Note: Loyverse uses 'Price [StoreName]'
            price = float(row.get('Price [Chillo]', 0)) if pd.notna(row.get('Price [Chillo]')) else 0.0
            cost = float(row.get('Cost', 0)) if pd.notna(row.get('Cost')) else 0.0
            stock = int(float(row.get('In stock [Chillo]', 0))) if pd.notna(row.get('In stock [Chillo]')) else 0

            Product.objects.update_or_create(
                name=name,
                outlet=outlet,
                defaults={
                    'sku': row.get('SKU'),
                    'category': category,
                    'cost_price': cost,
                    'selling_price': price,
                    'current_stock_level': stock
                }
            )
            success_count += 1
            if success_count % 50 == 0:
                print(f"Imported {success_count} items...")

        except Exception as e:
            print(f"Row {index} Skip Error: {e}")

    print(f"--- SUCCESS: {success_count} items imported into {outlet.name} ---")

if __name__ == "__main__":
    run_import()