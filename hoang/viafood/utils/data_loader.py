import pandas as pd
from typing import List, Optional
from models.data_models import VietnameseDish
from config.settings import settings
import os

class DataLoader:
    """Đọc và xử lý dữ liệu món ăn từ CSV"""
    
    def __init__(self, file_path: Optional[str] = None):
        self.file_path = file_path or settings.DATA_FILE_PATH
        self.dishes: List[VietnameseDish] = []
    
    def load_excel_data(self) -> bool:
        """Đọc dữ liệu từ file Excel (.xlsx)"""
        try:
            if not os.path.exists(self.file_path):
                print(f"File không tồn tại: {self.file_path}")
                return False
            
            # Đọc file Excel 
            df = pd.read_excel(self.file_path, engine='openpyxl')  

            # Chuẩn hóa tên cột
            df.columns = df.columns.str.strip()
            
            # Mapping cột Excel với model
            column_mapping = {
                'Món ăn': 'name',
                'Vùng miền': 'region', 
                'Mô tả': 'description',
                'Nguyên liệu': 'ingredients',
                'Cách làm/công thức': 'recipe',
                'Link món ăn': 'link',
                'Hình ảnh': 'image',
                'Chay/mặn': 'dish_type',
                'Tâm trạng, cảm xúc': 'mood',
                'Chính/vặt': 'meal_category',
                'Khô/nước': 'texture',
                'Người điền': 'contributor'
            }
            
            dishes_data = []
            for _, row in df.iterrows():
                dish_data = {}
                for excel_col, model_field in column_mapping.items():
                    value = row.get(excel_col, "")
                    if pd.isna(value):
                        dish_data[model_field] = ""
                    else:
                        dish_data[model_field] = str(value).strip()
                dish = VietnameseDish(**dish_data)
                dishes_data.append(dish)

            self.dishes = dishes_data
            print(f"✅ Đã tải {len(self.dishes)} món ăn từ file Excel")
            return True

        except Exception as e:
            print(f"❌ Lỗi khi đọc file Excel: {e}")
            return False

    
    def get_dishes(self) -> List[VietnameseDish]:
        """Lấy danh sách món ăn"""
        return self.dishes
    
    def get_dishes_by_region(self, region: str) -> List[VietnameseDish]:
        """Lấy món ăn theo vùng miền"""
        return [dish for dish in self.dishes if region.lower() in dish.region.lower()]
    
    def get_dishes_by_type(self, dish_type: str) -> List[VietnameseDish]:
        """Lấy món ăn theo loại (chay/mặn)"""
        return [dish for dish in self.dishes if dish_type.lower() in dish.dish_type.lower()]
    
    def get_dishes_by_mood(self, mood: str) -> List[VietnameseDish]:
        """Lấy món ăn theo tâm trạng"""
        return [dish for dish in self.dishes if mood.lower() in dish.mood.lower()]
    
    def search_dishes(self, keyword: str) -> List[VietnameseDish]:
        """Tìm kiếm món ăn theo từ khóa"""
        keyword = keyword.lower()
        results = []
        
        for dish in self.dishes:
            # Tìm trong tên món
            if keyword in dish.name.lower():
                results.append(dish)
            # Tìm trong mô tả
            elif keyword in dish.description.lower():
                results.append(dish)
            # Tìm trong nguyên liệu
            elif keyword in dish.ingredients.lower():
                results.append(dish)
        
        return results
    
    def get_statistics(self) -> dict:
        """Thống kê dữ liệu"""
        if not self.dishes:
            return {}
        
        stats = {
            'total_dishes': len(self.dishes),
            'regions': {},
            'dish_types': {},
            'meal_categories': {},
            'textures': {}
        }
        
        for dish in self.dishes:
            # Thống kê theo vùng miền
            region = dish.region or "Không xác định"
            stats['regions'][region] = stats['regions'].get(region, 0) + 1
            
            # Thống kê theo loại món
            dish_type = dish.dish_type or "Không xác định"
            stats['dish_types'][dish_type] = stats['dish_types'].get(dish_type, 0) + 1
            
            # Thống kê theo phân loại
            meal_cat = dish.meal_category or "Không xác định"
            stats['meal_categories'][meal_cat] = stats['meal_categories'].get(meal_cat, 0) + 1
            
            # Thống kê theo tính chất
            texture = dish.texture or "Không xác định"
            stats['textures'][texture] = stats['textures'].get(texture, 0) + 1
        
        return stats

# Global instance
data_loader = DataLoader()