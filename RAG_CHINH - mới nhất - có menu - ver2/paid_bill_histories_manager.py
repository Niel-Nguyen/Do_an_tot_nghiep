import json
import os
from datetime import datetime

class PaidBillHistory:
    def __init__(self, user_id, bill_data):
        self.user_id = user_id
        self.order_id = bill_data.get('order_id')
        self.items = bill_data.get('items', [])
        self.total = bill_data.get('total', 0)
        self.created_at = bill_data.get('created_at')
        self.paid_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.table_id = bill_data.get('table_id')

def get_histories_file_path(user_id):
    directory = 'paid_bill_histories'
    if not os.path.exists(directory):
        os.makedirs(directory)
    return os.path.join(directory, f'{user_id}_history.json')

def save_paid_bill_history(user_id, bill_data):
    """Lưu lịch sử hóa đơn đã thanh toán"""
    file_path = get_histories_file_path(user_id)
    history = PaidBillHistory(user_id, bill_data)
    
    # Đọc lịch sử cũ nếu có
    existing_data = []
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except:
            existing_data = []
    
    # Thêm lịch sử mới
    existing_data.append({
        'user_id': history.user_id,
        'order_id': history.order_id,
        'items': history.items,
        'total': history.total,
        'created_at': history.created_at,
        'paid_at': history.paid_at,
        'table_id': history.table_id
    })
    
    # Lưu vào file
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=2)

def load_paid_bill_histories(user_id):
    """Lấy lịch sử hóa đơn đã thanh toán của user"""
    file_path = get_histories_file_path(user_id)
    if not os.path.exists(file_path):
        return []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            histories = json.load(f)
        return histories
    except:
        return []

def get_used_dishes_history(user_id):
    """Lấy danh sách các món đã từng dùng của user"""
    histories = load_paid_bill_histories(user_id)
    used_dishes = {}  # dict để track số lần dùng mỗi món
    
    for history in histories:
        for item in history.get('items', []):
            dish_name = item.get('dish', {}).get('name', '') if isinstance(item.get('dish'), dict) else item.get('dish', '')
            if dish_name:
                if dish_name in used_dishes:
                    used_dishes[dish_name]['count'] += item.get('quantity', 1)
                    used_dishes[dish_name]['times'].append(history.get('paid_at'))
                else:
                    used_dishes[dish_name] = {
                        'count': item.get('quantity', 1),
                        'times': [history.get('paid_at')]
                    }
    
    return used_dishes
