from models.database import SessionLocal, Bill, BillItem

session = SessionLocal()

# Lấy tất cả món đã thanh toán của user 'Vuong'
user_id = 'Vuong'
results = (
    session.query(BillItem)
    .join(Bill, BillItem.bill_id == Bill.id)
    .filter(Bill.user_id == user_id)
    .all()
)

for item in results:
    print(f"Món: {item.dish_name}, Số lượng: {item.quantity}, Giá: {item.price}, Tổng: {item.total}")

session.close()