from typing import List, Dict, Any, Optional
from models.data_models import VietnameseDish
import uuid
from datetime import datetime

class OrderItem:
    def __init__(self, dish: VietnameseDish, quantity: int = 1, note: str = ""):
        self.dish = dish
        self.quantity = quantity
        self.note = note

class Order:
    def __init__(self, user_id: str, table_id: str = None):
        self.order_id = str(uuid.uuid4())
        self.user_id = user_id
        self.table_id = table_id  # Lưu thông tin bàn
        self.items: List[OrderItem] = []
        self.status = "pending"  # pending, confirmed, sent_to_kitchen, completed
        self.note = ""
        self.created_at = datetime.now()

    def add_item(self, dish: VietnameseDish, quantity: int = 1, note: str = ""):
        for item in self.items:
            if item.dish.name == dish.name:
                item.quantity += quantity
                if note:
                    item.note = note
                return
        self.items.append(OrderItem(dish, quantity, note))

    def remove_item(self, dish_name: str):
        self.items = [item for item in self.items if item.dish.name != dish_name]

    def clear(self):
        self.items.clear()

    def get_summary(self) -> List[Dict[str, Any]]:
        return [
            {
                "dish": item.dish.name,
                "quantity": item.quantity,
                "note": item.note
            } for item in self.items
        ]

class OrderManager:
    def __init__(self):
        # user_id -> List[Order]
        self.orders: Dict[str, List[Order]] = {}

    def get_orders(self, user_id: str) -> List[Order]:
        return self.orders.get(user_id, [])

    def get_current_order(self, user_id: str) -> Order:
        """Lấy order có trạng thái 'pending' gần nhất, nếu không có thì tạo mới."""
        user_orders = self.orders.get(user_id, [])
        for order in user_orders:
            if order.status == "pending":
                return order
        # Nếu không có order pending, tạo mới
        # Tìm table_id từ session hoặc table context
        table_id = None
        try:
            from core.table_manager import table_manager
            # Thử tìm table theo user context
            table = table_manager.find_table_by_user_context(user_id)
            if table:
                table_id = table.id
            else:
                # Nếu user_id có thể là table_id (UUID), kiểm tra trực tiếp
                if table_manager.get_table(user_id):
                    table_id = user_id
                else:
                    # Tìm session active nào đó (fallback cho test)
                    for s in table_manager.sessions.values():
                        if s.status == 'active':
                            table_id = s.table_id
                            break
        except Exception as e:
            table_id = None
        new_order = Order(user_id, table_id=table_id)
        self.orders.setdefault(user_id, []).append(new_order)
        return new_order

    def add_dish(self, user_id: str, dish: VietnameseDish, quantity: int = 1, note: str = ""):
        print(f"[DEBUG][add_dish] user_id={user_id} | dish={dish.name} | quantity={quantity}")
        # Nếu user_id là table_id (UUID), truyền vào get_current_order để tạo order đúng bàn
        order = self.get_current_order(user_id)
        # Nếu order chưa có table_id, gán lại
        if not getattr(order, 'table_id', None):
            order.table_id = user_id
        order.add_item(dish, quantity, note)

    def remove_dish(self, user_id: str, dish_name: str):
        order = self.get_current_order(user_id)
        order.remove_item(dish_name)

    def clear_order(self, user_id: str):
        order = self.get_current_order(user_id)
        order.clear()

    def get_order_summary(self, user_id: str) -> List[Dict[str, Any]]:
        order = self.get_current_order(user_id)
        return order.get_summary()

    def confirm_order(self, user_id: str):
        order = self.get_current_order(user_id)
        order.status = "confirmed"

    def get_bill(self, user_id: str, order_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        user_orders = self.orders.get(user_id, [])
        order = None
        if order_id:
            for o in user_orders:
                if o.order_id == order_id:
                    order = o
                    break
        else:
            # Nếu không truyền order_id, lấy order mới nhất (ưu tiên pending, nếu không có lấy gần nhất)
            order = None
            for o in user_orders:
                if o.status == "pending":
                    order = o
                    break
            if not order and user_orders:
                order = user_orders[-1]
        if not order:
            print(f"[DEBUG][get_bill] user_id={user_id} | bill=None")
            return None
        bill_items = []
        total = 0
        for item in order.items:
            price = getattr(item.dish, 'price', 0)
            amount = price * item.quantity
            bill_items.append({
                'dish': item.dish.name,
                'quantity': item.quantity,
                'unit_price': price,
                'amount': amount,
                'note': item.note
            })
            total += amount
        created_at_str = order.created_at.strftime('%d/%m/%Y %H:%M:%S') if hasattr(order, 'created_at') else ''
        # Luôn lấy tên bàn từ table_manager theo table_id
        table_name = None
        table_id = getattr(order, 'table_id', None)
        if table_id:
            try:
                from core.table_manager import table_manager
                # Tìm theo ID trước
                table = table_manager.get_table(table_id)
                if table:
                    table_name = table.name
                else:
                    # Nếu không tìm thấy theo ID, dùng phương thức tìm theo context
                    table = table_manager.find_table_by_user_context(user_id)
                    if table:
                        table_name = table.name
            except Exception as e:
                table_name = None
        else:
            # Nếu không có table_id, thử tìm theo user context
            try:
                from core.table_manager import table_manager
                table = table_manager.find_table_by_user_context(user_id)
                if table:
                    table_name = table.name
            except Exception as e:
                table_name = None
                
        if not table_name:
            # Thử extract tên bàn từ user_id nếu có pattern
            if "192.168" in str(user_id):
                table_name = "Bàn 1"  # Default cho IP local
            else:
                table_name = str(table_id) if table_id else user_id
        print(f"[DEBUG][get_bill] user_id={user_id} | bill={{'order_id': order.order_id, 'user_id': user_id, 'table_name': table_name, 'items': bill_items, 'total': total, 'status': order.status}}")
        return {
            'order_id': order.order_id,
            'user_id': user_id,
            'table_name': table_name,
            'items': bill_items,
            'total': total,
            'status': order.status,
            'created_at': created_at_str
        }

    def has_dish_in_order(self, user_id: str, dish_name: str) -> bool:
        order = self.get_current_order(user_id)
        for item in order.items:
            if item.dish.name == dish_name:
                return True
        return False

    def update_note(self, user_id: str, dish_name: str, note: str):
        order = self.get_current_order(user_id)
        for item in order.items:
            if item.dish.name == dish_name:
                if item.note:
                    if note.lower() not in item.note.lower():
                        item.note = f"{item.note}, {note}"
                else:
                    item.note = note
                return True
        return False

    def get_dish_note(self, user_id: str, dish_name: str) -> str:
        order = self.get_current_order(user_id)
        for item in order.items:
            if item.dish.name == dish_name:
                return item.note
        return ""

    def get_all_bills(self, user_id: Optional[str] = None):
        if user_id:
            return self.orders.get(user_id, [])
        return self.orders

    def update_bill_status(self, user_id: str, status: str, order_id: Optional[str] = None):
        user_orders = self.orders.get(user_id, [])
        target_order = None
        if order_id:
            for o in user_orders:
                if o.order_id == order_id:
                    target_order = o
                    break
        else:
            # Nếu không truyền order_id, lấy order pending gần nhất
            for o in user_orders:
                if o.status == "pending":
                    target_order = o
                    break
            if not target_order and user_orders:
                target_order = user_orders[-1]
        if target_order:
            print(f"[DEBUG][update_bill_status] user_id={user_id} | status={status} | order_id={target_order.order_id}")
            # Nếu admin chọn 'paid' hoặc 'Đã thanh toán', lưu là 'paid'
            if status.lower() in ["paid", "đã thanh toán"]:
                target_order.status = "paid"
            else:
                target_order.status = status

order_manager = OrderManager()
