import pandas as pd
from models.data_models import VietnameseDish

def load_dishes_from_excel(excel_path: str) -> list:
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
