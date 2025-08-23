import sys
import os
sys.path.append('.')

from utils.excel_loader import load_dishes_from_excel

# Test loading dishes from Excel
data_path = os.path.join(os.path.dirname(__file__), 'data100mon.xlsx')
print(f"Loading from: {data_path}")
print(f"File exists: {os.path.exists(data_path)}")

if os.path.exists(data_path):
    dishes = load_dishes_from_excel(data_path)
    print(f"Loaded {len(dishes)} dishes")
    
    if dishes:
        print(f"First dish: {dishes[0].name}")
        print(f"Sample dishes:")
        for i, dish in enumerate(dishes[:5]):
            print(f"  {i+1}. {dish.name}")
        
        # Check for "Gỏi ngó sen tôm thịt"
        found_dish = None
        for dish in dishes:
            if "ngó sen" in dish.name.lower():
                found_dish = dish
                break
        
        if found_dish:
            print(f"\n✅ Found dish: {found_dish.name}")
        else:
            print("\n❌ 'Gỏi ngó sen tôm thịt' not found in loaded dishes")
    else:
        print("❌ No dishes loaded")
else:
    print("❌ Excel file not found")
