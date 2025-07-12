import pandas as pd
from models.data_models import VietnameseDish

def load_dishes_from_excel(excel_path: str) -> list:
    df = pd.read_excel(excel_path)
    dishes = []
    for _, row in df.iterrows():
        dish = VietnameseDish(
            name=row.get('Món ăn', ''),
            region=row.get('Vùng miền', ''),
            ingredients=row.get('Nguyên liệu', ''),
            description=row.get('Mô tả', ''),
            recipe=row.get('Cách làm/công thức', ''),
            price=row.get('Giá', None),
            unit=row.get('Đơn vị tính', None),
            mood=row.get('Tâm trạng, cảm xúc', ''),
            dish_type=row.get('Chính/vặt', ''),
            texture=row.get('Khô/nước', ''),
            image=row.get('Hình ảnh', None),
            meal_category=row.get('Chay/Mặn', ''),
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
