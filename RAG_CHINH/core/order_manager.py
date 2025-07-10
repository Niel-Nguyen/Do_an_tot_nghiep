from typing import List, Dict, Any, Optional
from models.data_models import VietnameseDish
import uuid

class OrderItem:
    def __init__(self, dish: VietnameseDish, quantity: int = 1, note: str = ""):
        self.dish = dish
        self.quantity = quantity
        self.note = note

class Order:
    def __init__(self, user_id: str):
        self.order_id = str(uuid.uuid4())
        self.user_id = user_id
        self.items: List[OrderItem] = []
        self.status = "pending"  # pending, confirmed, sent_to_kitchen, completed
        self.note = ""

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
        self.orders: Dict[str, Order] = {}  # user_id -> Order

    def get_order(self, user_id: str) -> Order:
        if user_id not in self.orders:
            self.orders[user_id] = Order(user_id)
        return self.orders[user_id]

    def add_dish(self, user_id: str, dish: VietnameseDish, quantity: int = 1, note: str = ""):
        print(f"[DEBUG][add_dish] user_id={user_id} | dish={dish.name} | quantity={quantity}")
        order = self.get_order(user_id)
        order.add_item(dish, quantity, note)

    def remove_dish(self, user_id: str, dish_name: str):
        order = self.get_order(user_id)
        order.remove_item(dish_name)

    def clear_order(self, user_id: str):
        order = self.get_order(user_id)
        order.clear()

    def get_order_summary(self, user_id: str) -> List[Dict[str, Any]]:
        order = self.get_order(user_id)
        return order.get_summary()

    def confirm_order(self, user_id: str):
        order = self.get_order(user_id)
        order.status = "confirmed"

    def get_bill(self, user_id: str) -> Dict[str, Any]:
        if user_id not in self.orders:
            print(f"[DEBUG][get_bill] user_id={user_id} | bill=None")
            return None
        order = self.orders[user_id]
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
        print(f"[DEBUG][get_bill] user_id={user_id} | bill={{'order_id': order.order_id, 'user_id': user_id, 'items': bill_items, 'total': total, 'status': order.status}}")
        return {
            'order_id': order.order_id,
            'user_id': user_id,
            'items': bill_items,
            'total': total,
            'status': order.status
        }

    def has_dish_in_order(self, user_id: str, dish_name: str) -> bool:
        order = self.get_order(user_id)
        for item in order.items:
            if item.dish.name == dish_name:
                return True
        return False

    def update_note(self, user_id: str, dish_name: str, note: str):
        """Cập nhật ghi chú cho món ăn mà không thay đổi số lượng.
        Nếu đã có ghi chú trước đó, thêm ghi chú mới vào sau."""
        order = self.get_order(user_id)
        for item in order.items:
            if item.dish.name == dish_name:
                if item.note:
                    # Nếu ghi chú mới chưa có trong ghi chú cũ
                    if note.lower() not in item.note.lower():
                        item.note = f"{item.note}, {note}"
                else:
                    item.note = note
                return True
        return False

    def get_dish_note(self, user_id: str, dish_name: str) -> str:
        """Lấy ghi chú hiện tại của món ăn"""
        order = self.get_order(user_id)
        for item in order.items:
            if item.dish.name == dish_name:
                return item.note
        return ""

    def get_all_bills(self):
        print(f"[DEBUG][get_all_bills] orders={self.orders}")
        # Giả sử self.orders là dict {user_id: bill_dict}
        return list(self.orders.values())

    def update_bill_status(self, user_id: str, status: str):
        print(f"[DEBUG][update_bill_status] user_id={user_id} | status={status}")
        if user_id in self.orders:
            self.orders[user_id].status = status

order_manager = OrderManager()
