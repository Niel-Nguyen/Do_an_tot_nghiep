import sqlite3
import pandas as pd
from datetime import datetime

def clear_and_import_dishes(excel_file: str = '144mon.xlsx', db_file: str = 'restaurant.db'):
    """
    Clear dữ liệu bảng dishes hiện tại và import dữ liệu mới từ Excel
    """
    print(f"[INFO] Starting dishes data update at {datetime.now()}")
    
    try:
        # Đọc dữ liệu từ Excel
        print(f"[INFO] Reading data from {excel_file}...")
        df = pd.read_excel(excel_file)
        print(f"[INFO] Found {len(df)} dishes in Excel file")
        
        # Kết nối database
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Backup dữ liệu cũ (optional)
        print("[INFO] Creating backup of current dishes data...")
        cursor.execute("CREATE TABLE IF NOT EXISTS dishes_backup AS SELECT * FROM dishes WHERE 1=0")
        cursor.execute("INSERT INTO dishes_backup SELECT * FROM dishes")
        backup_count = cursor.rowcount
        print(f"[INFO] Backed up {backup_count} existing dishes")
        
        # Clear dữ liệu hiện tại
        print("[INFO] Clearing current dishes data...")
        cursor.execute("DELETE FROM dishes")
        deleted_count = cursor.rowcount
        print(f"[INFO] Deleted {deleted_count} existing dishes")
        
        # Import dữ liệu mới
        print("[INFO] Importing new dishes data...")
        success_count = 0
        error_count = 0
        
        for index, row in df.iterrows():
            try:
                # Chuẩn bị dữ liệu
                dish_data = {
                    'name': str(row.get('Món ăn', '')).strip() if pd.notna(row.get('Món ăn')) else '',
                    'region': str(row.get('Vùng miền', '')).strip() if pd.notna(row.get('Vùng miền')) else '',
                    'ingredients': str(row.get('Nguyên liệu', '')).strip() if pd.notna(row.get('Nguyên liệu')) else '',
                    'description': str(row.get('Mô tả', '')).strip() if pd.notna(row.get('Mô tả')) else '',
                    'recipe': str(row.get('Cách làm/công thức', '')).strip() if pd.notna(row.get('Cách làm/công thức')) else '',
                    'price': row.get('Giá') if pd.notna(row.get('Giá')) else None,
                    'unit': str(row.get('Đơn vị tính', '')).strip() if pd.notna(row.get('Đơn vị tính')) else None,
                    'mood': str(row.get('Tâm trạng, cảm xúc', '')).strip() if pd.notna(row.get('Tâm trạng, cảm xúc')) else '',
                    'main_or_side': str(row.get('Chính/vặt', '')).strip() if pd.notna(row.get('Chính/vặt')) else '',
                    'dry_or_soup': str(row.get('Khô/nước', '')).strip() if pd.notna(row.get('Khô/nước')) else '',
                    'image_url': str(row.get('Hình ảnh', '')).strip() if pd.notna(row.get('Hình ảnh')) else None,
                    'vegetarian_or_meat': str(row.get('Chay/Mặn', '')).strip() if pd.notna(row.get('Chay/Mặn')) else '',
                    'cooking_time': str(row.get('Thời gian nấu', '')).strip() if pd.notna(row.get('Thời gian nấu')) else None,
                    'calories': row.get('calories') if pd.notna(row.get('calories')) else None,
                    'fat': row.get('fat') if pd.notna(row.get('fat')) else None,
                    'fiber': row.get('fiber') if pd.notna(row.get('fiber')) else None,
                    'sugar': row.get('sugar') if pd.notna(row.get('sugar')) else None,
                    'protein': row.get('protein') if pd.notna(row.get('protein')) else None,
                    'nutrient_content': str(row.get('nutrient_content', '')).strip() if pd.notna(row.get('nutrient_content')) else None,
                    'is_available': 1  # Mặc định là available
                }
                
                # Insert vào database
                cursor.execute("""
                    INSERT INTO dishes (
                        name, region, ingredients, description, recipe, price, unit,
                        mood, main_or_side, dry_or_soup, image_url, vegetarian_or_meat,
                        cooking_time, calories, fat, fiber, sugar, protein, nutrient_content,
                        is_available
                    ) VALUES (
                        :name, :region, :ingredients, :description, :recipe, :price, :unit,
                        :mood, :main_or_side, :dry_or_soup, :image_url, :vegetarian_or_meat,
                        :cooking_time, :calories, :fat, :fiber, :sugar, :protein, :nutrient_content,
                        :is_available
                    )
                """, dish_data)
                
                success_count += 1
                
                # In progress mỗi 10 món
                if success_count % 10 == 0:
                    print(f"[PROGRESS] Imported {success_count} dishes...")
                    
            except Exception as e:
                error_count += 1
                print(f"[ERROR] Failed to import dish at row {index + 2}: {e}")
                continue
        
        # Commit changes
        conn.commit()
        print(f"[SUCCESS] Import completed!")
        print(f"  - Successfully imported: {success_count} dishes")
        print(f"  - Errors: {error_count} dishes")
        print(f"  - Total in database: {success_count} dishes")
        
        # Verify data
        cursor.execute("SELECT COUNT(*) FROM dishes WHERE is_available = 1")
        final_count = cursor.fetchone()[0]
        print(f"[VERIFY] Final count in database: {final_count} available dishes")
        
        # Show some sample data
        cursor.execute("SELECT name, region, price FROM dishes LIMIT 5")
        sample_dishes = cursor.fetchall()
        print("\n[SAMPLE] First 5 dishes:")
        for dish in sample_dishes:
            print(f"  - {dish[0]} ({dish[1]}) - {dish[2]} VND")
        
        conn.close()
        
    except Exception as e:
        print(f"[ERROR] Failed to update dishes data: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        raise

if __name__ == "__main__":
    # Chạy update
    clear_and_import_dishes()
    print("\n[INFO] Dishes data update completed!")