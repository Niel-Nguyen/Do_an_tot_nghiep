from core.rag_system import rag_system
from paid_bill_histories_manager import get_used_dishes_history

def handle_history_query(query, user_id=None):
    if not user_id:
        return "Xin lỗi, tôi không thể xác định được thông tin người dùng để tra cứu lịch sử."
    
    used_dishes = get_used_dishes_history(user_id)
    if not used_dishes:
        return "Bạn chưa có lịch sử gọi món nào được ghi nhận."
    
    # Sắp xếp các món theo số lần gọi
    sorted_dishes = sorted(used_dishes.items(), key=lambda x: x[1]['count'], reverse=True)
    
    response = "Dựa trên lịch sử, bạn đã từng gọi các món sau:\n\n"
    for dish_name, stats in sorted_dishes:
        dish = rag_system.dishes_lookup.get(dish_name)
        if dish:
            last_time = max(stats['times']) if stats['times'] else "không rõ"
            response += f"- {dish_name} ({stats['count']} lần, lần cuối: {last_time})\n"
    
    response += "\nBạn có muốn biết thêm chi tiết về món nào không?"
    return response

def check_history_intent(text):
    """Kiểm tra xem câu hỏi có phải về lịch sử món ăn không"""
    keywords = [
        "lịch sử", "đã gọi", "đã ăn", "đã dùng", "từng gọi", "từng ăn",
        "từng dùng", "món nào rồi", "những món nào", "món gì rồi",
        "món đã đặt", "đã đặt món", "món đã thanh toán"
    ]
    text = text.lower()
    return any(keyword in text for keyword in keywords)
