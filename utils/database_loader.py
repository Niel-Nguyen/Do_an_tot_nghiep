import sqlite3
from models.data_models import VietnameseDish

def load_dishes_from_database(db_path: str = 'restaurant.db') -> list:
    """Load dữ liệu món ăn từ database thay vì Excel"""
    dishes = []
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Để truy cập cột bằng tên
        cursor = conn.cursor()
        
        # Lấy tất cả món ăn từ database
        cursor.execute("""
            SELECT 
                name, region, ingredients, description, recipe, price, unit,
                mood, main_or_side, dry_or_soup, image_url, vegetarian_or_meat,
                cooking_time, calories, fat, fiber, sugar, protein, nutrient_content
            FROM dishes 
            WHERE is_available = 1
            ORDER BY name
        """)
        
        rows = cursor.fetchall()
        print(f"[DEBUG] Loaded {len(rows)} dishes from database")
        
        for row in rows:
            # Chuyển đổi từ database row sang VietnameseDish object
            dish = VietnameseDish(
                name=str(row['name']).strip() if row['name'] else '',
                region=str(row['region']).strip() if row['region'] else '',
                ingredients=str(row['ingredients']).strip() if row['ingredients'] else '',
                description=str(row['description']).strip() if row['description'] else '',
                recipe=str(row['recipe']).strip() if row['recipe'] else '',
                price=row['price'],
                unit=str(row['unit']).strip() if row['unit'] else None,
                mood=str(row['mood']).strip() if row['mood'] else '',
                dish_type=str(row['main_or_side']).strip() if row['main_or_side'] else '',
                texture=str(row['dry_or_soup']).strip() if row['dry_or_soup'] else '',
                image=str(row['image_url']).strip() if row['image_url'] else None,  # Quan trọng: map image_url -> image
                meal_category=str(row['vegetarian_or_meat']).strip() if row['vegetarian_or_meat'] else '',
                cook_time=str(row['cooking_time']).strip() if row['cooking_time'] else None,
                calories=row['calories'],
                fat=row['fat'],
                fiber=row['fiber'],
                sugar=row['sugar'],
                protein=row['protein'],
                nutrient_content=str(row['nutrient_content']).strip() if row['nutrient_content'] else None,
                contributor=None,
                link=None
            )
            dishes.append(dish)
            
            # Debug thông tin hình ảnh
            if dish.image:
                print(f"[DEBUG] Dish '{dish.name}' has image: {dish.image[:50]}...")
        
        conn.close()
        print(f"[INFO] Successfully loaded {len(dishes)} dishes from database")
        
        # Thống kê
        dishes_with_images = sum(1 for dish in dishes if dish.image)
        print(f"[INFO] Dishes with images: {dishes_with_images}/{len(dishes)} ({dishes_with_images/len(dishes)*100:.1f}%)")
        
        return dishes
        
    except Exception as e:
        print(f"[ERROR] Failed to load dishes from database: {e}")
        print(f"[INFO] Falling back to Excel...")
        # Fallback to Excel if database fails
        from utils.excel_loader import load_dishes_from_excel
        return load_dishes_from_excel('144mon.xlsx')

def load_dishes_from_excel(excel_path: str) -> list:
    """Load dữ liệu món ăn từ Excel (giữ lại để backup)"""
    import pandas as pd
    
    df = pd.read_excel(excel_path)
    dishes = []
    for _, row in df.iterrows():
        dish = VietnameseDish(
            name=str(row.get('Món ăn', '')).strip(),
            region=str(row.get('Vùng miền', '')).strip(),
            ingredients=str(row.get('Nguyên liệu', '')).strip(),
            description=str(row.get('Mô tả', '')).strip(),
            recipe=str(row.get('Cách làm/công thức', '')).strip(),
            price=row.get('Giá', None),
            unit=row.get('Đơn vị tính', None),
            mood=str(row.get('Tâm trạng, cảm xúc', '')).strip(),
            dish_type=str(row.get('Chính/vặt', '')).strip(),
            texture=str(row.get('Khô/nước', '')).strip(),
            image=row.get('Hình ảnh', None),
            meal_category=str(row.get('Chay/Mặn', '')).strip(),
            cook_time=row.get('Thời gian nấu', None),
            calories=row.get('calories', None),
            fat=row.get('fat', None),
            fiber=row.get('fiber', None),
            sugar=row.get('sugar', None),
            protein=row.get('protein', None),
            nutrient_content=row.get('nutrient_content', None),
            contributor=None,
            link=None
        )
        dishes.append(dish)
    return dishes
