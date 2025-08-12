import pandas as pd
from models.database import Dish, SessionLocal, init_db

def migrate_dishes_from_excel(excel_path):
    init_db()
    session = SessionLocal()
    df = pd.read_excel(excel_path)
    for _, row in df.iterrows():
        dish = Dish(
            name=row.get('Món ăn', ''),
            region=row.get('Vùng miền', ''),
            ingredients=row.get('Nguyên liệu', ''),
            description=row.get('Mô tả', ''),
            recipe=row.get('Cách làm/công thức', ''),
            price=row.get('Giá', 0),
            unit=row.get('Đơn vị tính', ''),
            mood=row.get('Tâm trạng, cảm xúc', ''),
            main_or_side=row.get('Chính/vặt', ''),
            dry_or_soup=row.get('Khô/nước', ''),
            image_url=row.get('Hình ảnh', ''),
            veg_or_meat=row.get('Chay/Mặn', ''),
            cook_time=row.get('Thời gian nấu', 0),
            calories=row.get('calories', 0),
            fat=row.get('fat', 0),
            fiber=row.get('fiber', 0),
            sugar=row.get('sugar', 0),
            protein=row.get('protein', 0),
            nutrient_content=row.get('nutrient_content', '')
        )
        session.add(dish)
    session.commit()
    session.close()
    print('Đã migrate dữ liệu món ăn sang database.')

if __name__ == '__main__':
    migrate_dishes_from_excel('data100mon.xlsx')
