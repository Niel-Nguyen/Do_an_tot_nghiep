from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime

from models.database import SessionLocal, init_db, Dish as DishModel, Bill as BillModel, BillItem as BillItemModel, ChatHistory as ChatHistoryModel
from models.data_models import VietnameseDish


def get_session() -> Session:
    init_db()
    return SessionLocal()


def _parse_datetime(dt_str: str) -> datetime | None:
    if not dt_str:
        return None
    for fmt in ("%d/%m/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%d-%m-%Y %H:%M:%S"):
        try:
            return datetime.strptime(dt_str, fmt)
        except Exception:
            continue
    return None


def get_dishes_for_chatbot() -> List[VietnameseDish]:
    session = get_session()
    try:
        dishes: List[VietnameseDish] = []
        for row in session.query(DishModel).all():
            vd = VietnameseDish(
                name=row.name or "",
                region=row.region or "",
                ingredients=row.ingredients or "",
                description=row.description or "",
                recipe=row.recipe or "",
                price=row.price,
                unit=row.unit,
                mood=row.mood or "",
                dish_type=(row.main_or_side or ""),
                texture=(row.dry_or_soup or ""),
                image=row.image_url,
                meal_category=(row.veg_or_meat or ""),
                cook_time=str(row.cook_time) if row.cook_time is not None else None,
                calories=str(row.calories) if row.calories is not None else None,
                fat=str(row.fat) if row.fat is not None else None,
                fiber=str(row.fiber) if row.fiber is not None else None,
                sugar=str(row.sugar) if row.sugar is not None else None,
                protein=str(row.protein) if row.protein is not None else None,
                nutrient_content=row.nutrient_content,
                contributor=None,
                link=None,
            )
            dishes.append(vd)
        return dishes
    finally:
        session.close()


def upsert_bill_with_items(order: Dict[str, Any], status: str | None = None) -> None:
    """Create or update a bill and its items from an order dict.
    order keys: order_id, user_id, items[{dish, quantity, unit_price, amount, note}], total, status, created_at
    """
    session = get_session()
    try:
        order_id = order.get('order_id')
        if not order_id:
            return
        user_id = order.get('user_id')
        created_at = _parse_datetime(order.get('created_at')) or datetime.utcnow()
        bill: BillModel | None = session.query(BillModel).filter(BillModel.order_id == order_id).one_or_none()
        if bill is None:
            bill = BillModel(
                order_id=order_id,
                user_id=user_id,
                created_at=created_at,
                status=status or order.get('status'),
                total_amount=order.get('total') or 0,
                note=order.get('note')
            )
            session.add(bill)
            session.flush()
            # Insert items
            for it in order.get('items', []):
                dish_name = it.get('dish') if isinstance(it.get('dish'), str) else (it.get('dish', {}) or {}).get('name')
                quantity = it.get('quantity', 1)
                unit_price = it.get('unit_price', 0)
                amount = it.get('amount', unit_price * quantity)
                note = it.get('note')
                session.add(BillItemModel(
                    bill_id=bill.id,
                    dish_name=dish_name,
                    quantity=quantity,
                    price=unit_price,
                    total=amount,
                    note=note
                ))
        else:
            # Update status/total if provided
            bill.status = status or order.get('status') or bill.status
            bill.total_amount = order.get('total') or bill.total_amount
            # Don't duplicate items; assume items inserted at first creation
        if (status or order.get('status')) and (status or order.get('status')).lower() in ["paid", "đã thanh toán"]:
            bill.status = "paid"
            bill.paid_at = datetime.utcnow()
        session.commit()
    finally:
        session.close()


def update_bill_status(order_id: str, status: str) -> None:
    session = get_session()
    try:
        bill = session.query(BillModel).filter(BillModel.order_id == order_id).one_or_none()
        if bill is None:
            return
        bill.status = status
        if status.lower() in ["paid", "đã thanh toán"]:
            bill.status = "paid"
            bill.paid_at = datetime.utcnow()
        session.commit()
    finally:
        session.close()


def get_paid_dishes(user_id: str) -> List[str]:
    session = get_session()
    try:
        q = (
            session.query(BillItemModel.dish_name)
            .join(BillModel, BillItemModel.bill_id == BillModel.id)
            .filter(BillModel.user_id == user_id)
        )
        # Consider dishes from all bills, or only paid ones; here prefer paid
        q = q.filter((BillModel.status == 'paid'))
        names = sorted({name for (name,) in q.all() if name})
        return names
    finally:
        session.close()


def get_paid_bills(user_id: str) -> List[Dict[str, Any]]:
    session = get_session()
    try:
        bills = session.query(BillModel).filter(BillModel.user_id == user_id).order_by(BillModel.created_at.asc()).all()
        results: List[Dict[str, Any]] = []
        for b in bills:
            items_rows = session.query(BillItemModel).filter(BillItemModel.bill_id == b.id).all()
            items = [
                {
                    'dish': it.dish_name,
                    'quantity': it.quantity,
                    'unit_price': it.price,
                    'amount': it.total,
                    'note': it.note or ''
                }
                for it in items_rows
            ]
            results.append({
                'order_id': b.order_id,
                'user_id': b.user_id,
                'items': items,
                'total': b.total_amount or sum((it.total or 0) for it in items_rows),
                'status': b.status,
                'created_at': b.created_at.strftime('%d/%m/%Y %H:%M:%S') if b.created_at else None,
                'paid_at': b.paid_at.strftime('%d/%m/%Y %H:%M:%S') if b.paid_at else None,
            })
        return results
    finally:
        session.close()


def get_bill_by_order_id(order_id: str) -> Dict[str, Any] | None:
    session = get_session()
    try:
        b = session.query(BillModel).filter(BillModel.order_id == order_id).one_or_none()
        if not b:
            return None
        items_rows = session.query(BillItemModel).filter(BillItemModel.bill_id == b.id).all()
        items = [
            {
                'dish': it.dish_name,
                'quantity': it.quantity,
                'unit_price': it.price,
                'amount': it.total,
                'note': it.note or ''
            }
            for it in items_rows
        ]
        return {
            'order_id': b.order_id,
            'user_id': b.user_id,
            'items': items,
            'total': b.total_amount or sum((it.total or 0) for it in items_rows),
            'status': b.status,
            'created_at': b.created_at.strftime('%d/%m/%Y %H:%M:%S') if b.created_at else None,
            'paid_at': b.paid_at.strftime('%d/%m/%Y %H:%M:%S') if b.paid_at else None,
        }
    finally:
        session.close()


def get_used_dishes_history(user_id: str) -> Dict[str, Dict[str, Any]]:
    """Return dict of dish_name -> {count: int, times: [str]} based on bills."""
    session = get_session()
    try:
        rows = (
            session.query(BillItemModel.dish_name, BillItemModel.quantity, BillModel.paid_at, BillModel.created_at)
            .join(BillModel, BillItemModel.bill_id == BillModel.id)
            .filter(BillModel.user_id == user_id)
            .all()
        )
        used: Dict[str, Dict[str, Any]] = {}
        for dish_name, qty, paid_at, created_at in rows:
            if not dish_name:
                continue
            ts = paid_at or created_at
            ts_str = ts.strftime('%Y-%m-%d %H:%M:%S') if ts else None
            if dish_name in used:
                used[dish_name]['count'] += qty or 0
                if ts_str:
                    used[dish_name]['times'].append(ts_str)
            else:
                used[dish_name] = {
                    'count': qty or 0,
                    'times': [ts_str] if ts_str else []
                }
        return used
    finally:
        session.close()


def get_chat_history(user_id: str, limit: int = 50) -> List[Dict[str, str]]:
    session = get_session()
    try:
        rows = (
            session.query(ChatHistoryModel)
            .filter(ChatHistoryModel.user_id == user_id)
            .order_by(ChatHistoryModel.timestamp.asc())
            .all()
        )
        history: List[Dict[str, str]] = []
        for r in rows[-limit:]:
            if r.message:
                history.append({'role': 'user', 'content': r.message})
            if r.response:
                history.append({'role': 'assistant', 'content': r.response})
        return history
    finally:
        session.close()
