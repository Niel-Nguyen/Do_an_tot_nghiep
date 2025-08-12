import json
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from models.database import Bill, BillItem, SessionLocal, init_db

def parse_datetime(dt_str):
    # Hỗ trợ nhiều định dạng ngày giờ
    if not dt_str:
        return None
    for fmt in (
        "%d/%m/%Y %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%d-%m-%Y %H:%M:%S",
    ):
        try:
            return datetime.strptime(dt_str, fmt)
        except Exception:
            continue
    return None

def migrate_paid_bill_histories(json_path):
    init_db()
    session = SessionLocal()
    with open(json_path, 'r', encoding='utf-8') as f:
        bills = json.load(f)

    # Lấy các order_id đã có trong DB để tránh lỗi UNIQUE
    existing = {oid for (oid,) in session.query(Bill.order_id).all() if oid}
    seen_order_ids = set()
    inserted = skipped = 0

    try:
        for bill in bills:
            order_id = bill.get('order_id')
            if not order_id:
                skipped += 1
                continue
            if order_id in seen_order_ids or order_id in existing:
                skipped += 1
                continue  # Bỏ qua bản ghi trùng order_id (trong file hoặc DB)

            seen_order_ids.add(order_id)
            created_at = parse_datetime(bill.get('created_at'))
            paid_at = parse_datetime(bill.get('paid_at'))
            status = 'paid' if paid_at else (bill.get('status') or 'done')

            bill_obj = Bill(
                order_id=order_id,
                user_id=bill.get('user_id'),
                created_at=created_at,
                status=status,
                total_amount=bill.get('total', 0),
                note=bill.get('note') or ''
            )
            # paid_at có thể không tồn tại ở DB cũ; init_db đã thêm cột nếu thiếu
            bill_obj.paid_at = paid_at

            session.add(bill_obj)
            session.flush()  # Để lấy bill_obj.id

            for item in bill.get('items', []):
                # dish có thể là string hoặc object
                dish_field = item.get('dish')
                dish_name = (
                    dish_field if isinstance(dish_field, str)
                    else (dish_field or {}).get('name', '')
                )
                item_obj = BillItem(
                    bill_id=bill_obj.id,
                    dish_name=dish_name,
                    quantity=item.get('quantity', 1),
                    price=item.get('unit_price', 0),
                    total=item.get('amount', 0),
                    note=item.get('note', '')
                )
                session.add(item_obj)
            inserted += 1

        session.commit()
        print(f'Dã migrate xong: chèn {inserted}, bỏ qua {skipped}.')
    except IntegrityError:
        session.rollback()
        print('Có lỗi UNIQUE hoặc ràng buộc. Đã rollback. Hãy chạy lại sau khi kiểm tra dữ liệu.')
        raise
    finally:
        session.close()

if __name__ == '__main__':
    migrate_paid_bill_histories('paid_bill_histories/Vuong_history.json')
