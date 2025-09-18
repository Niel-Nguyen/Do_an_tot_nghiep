from typing import List, Dict, Any
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from models.data_models import ChatMessage, VietnameseDish
from models.ai_models import ai_models
from core.rag_system import rag_system
from utils.text_processor import text_processor
from config.settings import settings
from core.order_manager import order_manager
import re
import random
import unicodedata
import difflib
import requests

# Function to get dish_status_map dynamically
def get_dish_status_map():
    try:
        # Try to get from Flask's current_app first if we're in app context
        try:
            from flask import current_app
            if hasattr(current_app, 'dish_status_map'):
                dish_status_map = current_app.dish_status_map
                print(f"[DEBUG] get_dish_status_map() from current_app: {dish_status_map}")
                return dish_status_map
        except Exception as e:
            print(f"[DEBUG] Flask current_app not available: {e}")
        
        # Fallback to importing app module
        import sys
        import os
        # Thêm đường dẫn root để import app
        root_path = os.path.dirname(os.path.dirname(__file__))
        if root_path not in sys.path:
            sys.path.insert(0, root_path)
        
        # Import app module và lấy dish_status_map
        import app
        dish_status_map = getattr(app, 'dish_status_map', {})
        print(f"[DEBUG] get_dish_status_map() from app module: {dish_status_map}")
        return dish_status_map
    except Exception as e:
        print(f"[DEBUG] Error getting dish_status_map: {e}")
        return {}

def normalize(text):
    import unicodedata
    import re
    text = text.lower()
    text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    text = re.sub(r'\s+', ' ', text)  # thay mọi loại whitespace thành 1 space
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return text.strip()

def parse_suggested_menu(text: str):
    """
    Parse text thuần từ LLM ➜ list các dict: [{dish, quantity, price}]
    Nhận diện format: Tên món: (60.000 VNĐ/dĩa) Mô tả...
    Có thể nhận diện số lượng ở đầu dòng, sau tên món, hoặc dạng 'x2'.
    """
    def clean_text(text):
        text = re.sub(r'\*\*', '', text)  # bỏ ** in đậm
        text = re.sub(r'^[\s\-*•]+', '', text, flags=re.MULTILINE)  # bỏ bullet đầu dòng
        text = re.sub(r'\*', '', text)    # bỏ * còn lại
        return text.strip()
    def normalize(s):
        s = s.strip()
        s = re.sub(r'<[^>]+>', '', s)  # Remove HTML tags
        s = unicodedata.normalize('NFC', s)
        return s
    text = re.sub(r'<[^>]+>', '', text)  # Remove HTML tags toàn văn
    text = clean_text(text)
    lines = [normalize(line) for line in text.split('\n') if line.strip()]
    dishes = []
    # Regex nhận diện số lượng ở đầu dòng, sau tên món, hoặc dạng x2
    # Ví dụ: '2 dĩa Gỏi rau mầm tôm: (60.000 VNĐ/dĩa)', 'Gỏi rau mầm tôm x2: (60.000 VNĐ/dĩa)', '2 Gỏi rau mầm tôm: (60.000 VNĐ/dĩa)'
    pattern = r"^(?:(\d+)\s*(?:dĩa|tô|phần|suất|bát|ly|cái|miếng)?\s*)?([A-Za-zÀ-ỹ0-9\s]+?)(?:\s*[xX](\d+))?:\s*\((\d{1,3}(?:[.,]\d{3})*)\s*VNĐ[^)]*\)"
    for line in lines:
        m = re.match(pattern, line, re.IGNORECASE)
        if m:
            qty1 = m.group(1)
            name = m.group(2).strip(' .-:')
            qty2 = m.group(3)
            price_str = m.group(4).replace('.', '').replace(',', '').strip()
            try:
                price = int(price_str)
            except Exception:
                price = None
            # Ưu tiên số lượng ở đầu dòng, nếu không có thì lấy số lượng sau tên món, nếu không có thì mặc định 1
            quantity = 1
            if qty1 and qty1.isdigit():
                quantity = int(qty1)
            elif qty2 and qty2.isdigit():
                quantity = int(qty2)
            if name and price and not any(d['dish'].lower() == name.lower() and d.get('price') == price for d in dishes):
                dish = {'dish': name, 'quantity': quantity, 'price': price}
                dishes.append(dish)
    print('[DEBUG] parse_suggested_menu input:', text)
    print('[DEBUG] parse_suggested_menu output:', dishes)
    return dishes

def clean_star_lines(text):
    text = re.sub(r'(^|[\r\n])\s*\*+\s*', r'\1', text)
    text = re.sub(r'\*+\s*', '', text)
    return text

# --- Thêm hàm chèn ảnh cho mọi tên món trong content ---
def insert_dish_images(content: str) -> str:
    import re
    lines = content.split('\n')
    dish_keys = list(rag_system.dishes_lookup.keys())
    def normalize(text):
        import unicodedata
        text = text.lower()
        text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
        text = re.sub(r'[^a-z0-9\s]', '', text)
        return text
    norm_dish_keys = [normalize(k) for k in dish_keys]
    for idx, line in enumerate(lines):
        # Nếu dòng đã có <img, bỏ qua (KHÔNG chèn thêm ảnh nữa)
        if '<img' in line:
            continue
        line_norm = normalize(line)
        found = False
        for i, dish_key in enumerate(dish_keys):
            dish_norm = norm_dish_keys[i]
            if dish_norm and dish_norm in line_norm:
                dish_obj = rag_system.dishes_lookup[dish_key]
                img_html = get_img_html(dish_key, dish_obj)
                lines[idx] = line + img_html
                found = True
                break
        if not found:
            for i, dish_key in enumerate(dish_keys):
                dish_norm = norm_dish_keys[i]
                import difflib
                matches = difflib.get_close_matches(dish_norm, [line_norm], n=1, cutoff=0.6)
                if matches:
                    dish_obj = rag_system.dishes_lookup[dish_key]
                    img_html = get_img_html(dish_key, dish_obj)
                    lines[idx] = line + img_html
                    break
    return '\n'.join(lines)

def get_img_html(dish_name, dish_obj):
    print(f"[DEBUG][get_img_html] {dish_name} | dish_obj: {dish_obj}")
    if dish_obj and hasattr(dish_obj, 'image'):
        print(f"[DEBUG][get_img_html] {dish_name} | image: {getattr(dish_obj, 'image', None)}")
    if dish_obj and getattr(dish_obj, 'image', None):
        return f"<br><img src='{dish_obj.image}' alt='{dish_name}' class='zoomable-img' style='max-width:180px;border-radius:8px;margin:8px 0;cursor:zoom-in;' title='Bấm vào để xem ảnh lớn hơn'>"
    else:
        print(f"[DEBUG][img_insert] Không có trường image cho {dish_name}")
        google_url = f"https://www.google.com/search?tbm=isch&q={dish_name.replace(' ', '+')}"
        return f"<br><span style='color:#888'>Chưa có ảnh món này.</span> <a href='{google_url}' target='_blank'>Tìm trên Google</a>"

class VietnameseFoodChatbot:
    def __init__(self):
        self.conversation_history: List[ChatMessage] = []
        self.system_prompt = self._create_system_prompt()
        self.is_ready = False
        self.last_dish: str = ""
        self.last_intent: Dict[str, Any] = {}
        self.last_filters: Dict[str, Any] = {}
        self.last_query: str = ""
        self.last_suggested_dishes: list = []
        self.pending_note: Dict[str, Any] = {}  # Lưu trữ thông tin về note đang chờ xử lý
        self.last_order_list: List[Dict[str, Any]] = []  # Lưu trữ danh sách order cuối cùng
        self.pending_menu: List[Dict[str, Any]] = []  # Lưu thực đơn gợi ý đang chờ xác nhận

    def initialize(self, dishes: List[VietnameseDish]) -> bool:
        try:
            if not rag_system.initialize(dishes):
                return False
            self.is_ready = True
            print("Chatbot đã sẵn sàng!")
            return True
        except Exception as e:
            print(f"Lỗi khi khởi tạo chatbot: {e}")
            return False
    
    def _is_dish_available(self, dish_name: str) -> bool:
        """Check if a dish is available (not disabled by admin)"""
        dish_status_map = get_dish_status_map()
        print(f"[DEBUG] Checking dish availability for: {dish_name}")
        print(f"[DEBUG] dish_status_map: {dish_status_map}")
        result = dish_status_map.get(dish_name, True)  # Default to True if not in map
        print(f"[DEBUG] Result for {dish_name}: {result}")
        return result

    def chat(self, user_message: str, user_id: str = "default", order_id: str = None) -> str:
        if not self.is_ready:
            return clean_star_lines("Chatbot chưa được khởi tạo. Vui lòng kiểm tra lại.")
        # Intent gọi nhân viên/phục vụ
        call_staff_phrases = [
            "gọi nhân viên", "cần phục vụ", "nhờ phục vụ", "nhờ nhân viên", "gọi phục vụ", "call staff", "gọi người phục vụ", "gọi phục vụ bàn", "gọi người giúp", "gọi người hỗ trợ"
        ]
        if any(phrase in user_message.lower() for phrase in call_staff_phrases):
            return self.handle_call_staff(user_id)
        # Ưu tiên nhận diện order trước note (ưu tiên intent cứng)
        # Kiểm tra xem có phải câu hỏi không trước khi xử lý order
        question_indicators = [
            "là gì", "như thế nào", "thế nào", "mô tả", "giới thiệu", "nói về", "có gì", "gồm gì", "làm sao", "ra sao"
        ]
        is_question = any(indicator in user_message.lower() for indicator in question_indicators)
        
        order_phrases = [
            "gọi", "order", "đặt", "cho", "cho tôi", "thêm", "thêm món", "lấy", "muốn ăn", "ăn", "mua", "add", "muốn order món...", "tôi muốn gọi món ..."
        ]
        
        # Nếu là câu hỏi (có question indicators) thì không xử lý như order
        has_order_phrase = any(phrase in user_message.lower() for phrase in order_phrases)
        
        if has_order_phrase and not is_question:
            dish_name = self._extract_dish_name(user_message)
            # Nếu không có tên món nhưng có last_dish, chỉ tự động thêm nếu user thực sự muốn tăng số lượng
            if not dish_name and self.last_dish:
                # Chỉ thêm nếu user thực sự muốn tăng số lượng (có số hoặc các từ khóa cụ thể)
                if re.search(r'(\d+|phần|suất|nữa)', user_message, re.IGNORECASE):
                    match = re.search(r'(\d+)', user_message)
                    quantity = int(match.group(1)) if match else 1
                    dish = rag_system.dishes_lookup.get(self.last_dish, None)
                    if dish:
                        # Check dish status before adding to order
                        if not self._is_dish_available(dish.name):
                            reply = f"Xin lỗi, món {self.last_dish} hiện tại tạm hết. Bạn có muốn chọn món khác không?"
                            self.conversation_history.append(
                                ChatMessage(role="assistant", content=reply)
                            )
                            return clean_star_lines(reply)
                        
                        order_manager.add_dish(user_id, dish, quantity=quantity)
                        reply = f"✅ Đã thêm {quantity} {self.last_dish}. Bạn muốn 'Thanh toán' hay 'Xem hóa đơn' hay 'Thêm ghi chú' hay muốn gọi thêm món nào hay cần gì nữa không?"
                        reply += "<br>Nếu bạn đã thống nhất hóa đơn rồi, vui lòng nhấn \"Xác nhận chốt món cho nhà hàng\" để gửi order cho bếp."
                        self.conversation_history.append(
                            ChatMessage(role="assistant", content=reply)
                        )
                        return clean_star_lines(reply)
                # Nếu không phải dạng tăng số lượng, không tự động thêm món
            if dish_name:
                match = re.search(r'(\d+)', user_message)
                quantity = int(match.group(1)) if match else 1
                dish = rag_system.dishes_lookup.get(dish_name, None)
                if dish:
                    # Check dish status before adding to order
                    if not self._is_dish_available(dish.name):
                        reply = f"Xin lỗi, món {dish_name} hiện tại tạm hết. Bạn có muốn chọn món khác không?"
                        self.conversation_history.append(
                            ChatMessage(role="assistant", content=reply)
                        )
                        return clean_star_lines(reply)
                    
                    order_manager.add_dish(user_id, dish, quantity=quantity)
                    reply = f"✅ Đã thêm {quantity} {dish_name}. Bạn muốn 'Thanh toán' hay 'Xem hóa đơn' hay 'Thêm ghi chú' hay muốn gọi thêm món nào hay cần gì nữa không?"
                    reply += "<br>Nếu bạn đã thống nhất hóa đơn rồi, vui lòng nhấn \"Xác nhận chốt món cho nhà hàng\" để gửi order cho bếp." + confirm_order_button
                    self.conversation_history.append(
                        ChatMessage(role="assistant", content=reply)
                    )
                    return clean_star_lines(reply)
        # Intent cứng: Tìm hiểu thông tin món ăn
        info_phrases = [
            "tìm hiểu món", "giới thiệu món", "món", "thông tin món", "món này là gì", "món này có gì đặc biệt", "món này ngon không", "món này có gì", "món ... là gì", "món ... có gì đặc biệt"
        ]
        lowered = user_message.lower()
        if any(phrase in lowered for phrase in info_phrases):
            dish_name = self._extract_dish_name(user_message)
            if dish_name:
                dish = rag_system.dishes_lookup.get(dish_name, None)
                if dish:
                    reply = f"🍽️ <b>{dish.name}</b>\n"
                    if dish.image:
                        reply += f"<br><img src='{dish.image}' alt='{dish.name}' style='max-width:180px;border-radius:8px;margin:8px 0;cursor:zoom-in;' title='Bấm vào để xem ảnh lớn hơn'>"
                    if dish.description:
                        reply += f"<br><b>Mô tả:</b> {dish.description}"
                    if dish.ingredients:
                        reply += f"<br><b>Nguyên liệu:</b> {dish.ingredients}"
                    if dish.recipe:
                        reply += f"<br><b>Cách làm:</b> {dish.recipe[:300]}{'...' if len(dish.recipe) > 300 else ''}"
                    if dish.price:
                        reply += f"<br><b>Giá:</b> {dish.price}"
                    if dish.region:
                        reply += f"<br><b>Vùng miền:</b> {dish.region}"
                    if dish.dish_type:
                        reply += f"<br><b>Loại món:</b> {dish.dish_type}"
                    if dish.meal_category:
                        reply += f"<br><b>Chay/Mặn:</b> {dish.meal_category}"
                    if dish.texture:
                        reply += f"<br><b>Tính chất:</b> {dish.texture}"
                    if dish.cook_time:
                        reply += f"<br><b>Thời gian nấu:</b> {dish.cook_time} phút"
                    if dish.calories:
                        reply += f"<br><b>Calories:</b> {dish.calories}"
                    self.conversation_history.append(ChatMessage(role="assistant", content=reply))
                    return clean_star_lines(reply)
                else:
                    reply = f"Xin lỗi, hiện tại nhà hàng chưa có thông tin chi tiết về món {dish_name}."
                    self.conversation_history.append(ChatMessage(role="assistant", content=reply))
                    return clean_star_lines(reply)
        # Nếu user chỉ nhập tên một món (không có từ khóa order/info khác), tự động trả về thông tin món
        if user_message.strip() and not any(phrase in user_message.lower() for phrase in order_phrases + info_phrases):
            dish_name = self._extract_dish_name(user_message)
            if dish_name:
                dish = rag_system.dishes_lookup.get(dish_name, None)
                if dish:
                    reply = f"🍽️ <b>{dish.name}</b>\n"
                    if dish.image:
                        reply += f"<br><img src='{dish.image}' alt='{dish.name}' style='max-width:180px;border-radius:8px;margin:8px 0;cursor:zoom-in;' title='Bấm vào để xem ảnh lớn hơn'>"
                    if dish.description:
                        reply += f"<br><b>Mô tả:</b> {dish.description}"
                    if dish.ingredients:
                        reply += f"<br><b>Nguyên liệu:</b> {dish.ingredients}"
                    if dish.recipe:
                        reply += f"<br><b>Cách làm:</b> {dish.recipe[:300]}{'...' if len(dish.recipe) > 300 else ''}"
                    if dish.price:
                        reply += f"<br><b>Giá:</b> {dish.price}"
                    if dish.region:
                        reply += f"<br><b>Vùng miền:</b> {dish.region}"
                    if dish.dish_type:
                        reply += f"<br><b>Loại món:</b> {dish.dish_type}"
                    if dish.meal_category:
                        reply += f"<br><b>Chay/Mặn:</b> {dish.meal_category}"
                    if dish.texture:
                        reply += f"<br><b>Tính chất:</b> {dish.texture}"
                    if dish.cook_time:
                        reply += f"<br><b>Thời gian nấu:</b> {dish.cook_time} phút"
                    if dish.calories:
                        reply += f"<br><b>Calories:</b> {dish.calories}"
                    self.conversation_history.append(ChatMessage(role="assistant", content=reply))
                    return clean_star_lines(reply)
        # Intent cứng: Xem trạng thái đơn hàng (ưu tiên kiểm tra trước)
        status_phrases = [
            "xem trạng thái đơn hàng", "trạng thái đơn hàng", "trạng thái hóa đơn", "đơn hàng đang ở đâu", "đơn hàng ở đâu", "hóa đơn đang ở đâu", "tình trạng đơn hàng", "tình trạng hóa đơn", "đơn hàng status", "bill status", "xem trạng thái đơn"
        ]
        if any(phrase in user_message.lower() for phrase in status_phrases):
            all_bills = order_manager.get_all_bills(user_id)
            if not all_bills or all(len(bill.items) == 0 for bill in all_bills):
                reply = "Bạn chưa có hóa đơn/giỏ hàng nào. Hãy chọn món trước nhé!"
            else:
                reply = f"\U0001F4DD Trạng thái các hóa đơn của bạn:\n"
                for idx, bill in enumerate(all_bills, 1):
                    if not bill.items:
                        continue
                    dish_names = ', '.join([item.dish.name for item in bill.items])
                    reply += f"- Hóa đơn #{idx} (Mã: {bill.order_id[:8]}): <b>{bill.status}</b>\n  Món: {dish_names}\n"
                reply += "\nCác trạng thái có thể: pending (chờ xác nhận), confirmed (đã gửi bếp), in_progress (đang làm), done (đã xong), paid (đã thanh toán)."
            self.conversation_history.append(
                ChatMessage(role="assistant", content=reply)
            )
            return clean_star_lines(reply)
        # Nhận diện yêu cầu xem hóa đơn/bill hoặc giỏ hàng hoặc thanh toán (ưu tiên intent cứng)
        bill_phrases = [
            "xem hóa đơn","in bill", "xem bill", "hóa đơn", "bill", "tổng tiền", "giỏ hàng", "đã có", "có trong giỏ", "đang có món gì", "liệt kê món đã chọn", "món đã chọn", "món đã gọi", "món trong giỏ", "món trong order", "món đã order", "món đã đặt", "xem thực đơn", "xem menu", "xem món đã chọn", "xem món đã gọi",
            "thanh toán"
        ]
        if any(phrase in user_message.lower() for phrase in bill_phrases):
            # Lấy tất cả hóa đơn của user
            all_bills = order_manager.get_all_bills(user_id)
            # Filter out empty bills (bills with no items)
            non_empty_bills = [bill for bill in all_bills if bill.items and len(bill.items) > 0]
            
            if not non_empty_bills:
                reply = "Bạn chưa có hóa đơn/giỏ hàng nào. Hãy chọn món trước nhé!"
            else:
                # Tạo HTML đẹp cho hiển thị hóa đơn
                in_progress_found = False
                total_all_bills = 0
                bills_html = ""
                
                for idx, bill in enumerate(non_empty_bills, 1):
                    # Tính tổng tiền cho bill này
                    total = sum(getattr(item.dish, 'price', 0) * item.quantity for item in bill.items)
                    total_all_bills += total
                    if bill.status == 'in_progress':
                        in_progress_found = True
                    
                    # Xác định icon và màu cho trạng thái
                    status_info = {
                        'pending': {'icon': 'fas fa-clock', 'color': '#ffc107', 'text': 'Chờ xử lý'},
                        'confirmed': {'icon': 'fas fa-check-circle', 'color': '#17a2b8', 'text': 'Đã xác nhận'},
                        'in_progress': {'icon': 'fas fa-utensils', 'color': '#fd7e14', 'text': 'Đang làm'},
                        'done': {'icon': 'fas fa-clipboard-check', 'color': '#28a745', 'text': 'Đã xong'},
                        'paid': {'icon': 'fas fa-money-check-alt', 'color': '#6c757d', 'text': 'Đã thanh toán'}
                    }
                    
                    status = status_info.get(bill.status, status_info['pending'])
                    
                    # Tạo HTML cho từng món - đơn giản
                    items_html = ""
                    for i, item in enumerate(bill.items, 1):
                        note_str = f"<div class='text-muted' style='font-size:0.7rem; margin-top:0.25rem;'>Ghi chú: {item.note}</div>" if item.note else ""
                        price = getattr(item.dish, 'price', 0)
                        amount = price * item.quantity
                        items_html += f"""
                        <div class="dish-item">
                            <div class="dish-name">{item.dish.name}</div>
                            <div class="dish-qty">x{item.quantity}</div>
                            <div class="dish-price">{amount:,}đ</div>
                        </div>
                        """
                    
                    # Xác định text trạng thái đơn giản
                    status_text_map = {
                        'pending': 'Chưa chốt',
                        'confirmed': 'Đã xác nhận', 
                        'in_progress': 'Đang làm',
                        'done': 'Đã xong',
                        'paid': 'Đã thanh toán'
                    }
                    
                    status_text = status_text_map.get(bill.status, 'Chưa chốt')
                    
                    # Tạo HTML cho từng hóa đơn - đơn giản như mobile browser
                    bills_html += f"""
                    <div class="bill-item">
                        <div class="bill-item-header">
                            <div class="bill-item-title">📋 Hóa đơn #{idx}</div>
                            <div class="bill-item-status">{status_text}</div>
                        </div>
                        <div class="bill-item-meta">
                            ID: {bill.order_id[:8]}... • {bill.created_at.strftime('%d/%m/%Y %H:%M')}
                        </div>
                        <div class="dish-list">
                            {items_html}
                        </div>
                        <div class="bill-total">
                            <div class="bill-total-label">💰 Tổng:</div>
                            <div class="bill-total-amount">{total:,}đ</div>
                        </div>
                    </div>
                    """
                
                # Tạo thông báo trạng thái
                status_message = ""
                if in_progress_found:
                    status_message = """
                    <div class="alert alert-info border-0 rounded-3 mb-3" style="background: linear-gradient(135deg, #e3f2fd, #bbdefb);">
                        <div class="d-flex align-items-center">
                            <i class="fas fa-info-circle text-info me-2"></i>
                            <span>👨‍🍳 Nhà hàng đang chuẩn bị món ăn cho bạn, vui lòng chờ trong giây lát.</span>
                        </div>
                    </div>
                    """
                
                # Tạo tổng kết đơn giản
                summary_html = f"""
                <div class="bill-summary">
                    <h5 style="margin: 0 0 15px 0; color: #333;">📋 Tổng quan hóa đơn</h5>
                    <div class="summary-stats">
                        <div class="stat-item">
                            <div class="stat-number">{len(non_empty_bills)}</div>
                            <div class="stat-label">Hóa đơn</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-number">{total_all_bills:,}đ</div>
                            <div class="stat-label">Tổng tiền</div>
                        </div>
                    </div>
                </div>
                """
                
                # CSS đơn giản, gọn gàng như mobile native
                css_styles = """
                <style>
                .bill-container {
                    max-width: 100%;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: #f5f5f5;
                    margin: 0;
                    padding: 0;
                }
                
                .bill-header {
                    background: white;
                    padding: 20px 15px;
                    text-align: center;
                    border-bottom: 1px solid #e0e0e0;
                }
                
                .bill-header h3 {
                    margin: 0;
                    font-size: 1.2rem;
                    font-weight: 600;
                    color: #333;
                }
                
                .bill-summary {
                    background: white;
                    padding: 20px;
                    margin: 10px 0;
                    border-radius: 8px;
                    text-align: center;
                }
                
                .summary-stats {
                    display: flex;
                    justify-content: space-around;
                    margin-top: 15px;
                }
                
                .stat-item {
                    text-align: center;
                }
                
                .stat-number {
                    font-size: 1.5rem;
                    font-weight: bold;
                    color: #2196F3;
                }
                
                .stat-label {
                    font-size: 0.85rem;
                    color: #666;
                    margin-top: 5px;
                }
                
                .bill-list {
                    margin: 10px 0;
                }
                
                .bill-item {
                    background: white;
                    margin-bottom: 8px;
                    border-radius: 8px;
                    border: 1px solid #e0e0e0;
                    overflow: hidden;
                }
                
                .bill-item-header {
                    background: #4CAF50;
                    color: white;
                    padding: 12px 15px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                
                .bill-item-title {
                    font-size: 0.9rem;
                    font-weight: 600;
                }
                
                .bill-item-status {
                    font-size: 0.75rem;
                    background: rgba(255,255,255,0.2);
                    padding: 2px 6px;
                    border-radius: 10px;
                }
                
                .bill-item-meta {
                    padding: 8px 15px;
                    font-size: 0.75rem;
                    color: #666;
                    background: #f8f9fa;
                    border-bottom: 1px solid #e0e0e0;
                }
                
                .dish-list {
                    padding: 15px;
                    margin: 0;
                }
                
                .dish-item {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 8px 0;
                    border-bottom: 1px solid #f0f0f0;
                }
                
                .dish-item:last-child {
                    border-bottom: none;
                }
                
                .dish-name {
                    flex: 1;
                    font-size: 0.9rem;
                    color: #333;
                }
                
                .dish-qty {
                    font-size: 0.8rem;
                    color: #666;
                    margin: 0 10px;
                }
                
                .dish-price {
                    font-size: 0.9rem;
                    font-weight: 600;
                    color: #4CAF50;
                }
                
                .bill-total {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 15px;
                    background: #f8f9fa;
                    border-top: 2px solid #4CAF50;
                    margin: 0;
                }
                
                .bill-total-label {
                    font-size: 1rem;
                    font-weight: 600;
                    color: #333;
                }
                
                .bill-total-amount {
                    font-size: 1.2rem;
                    font-weight: bold;
                    color: #4CAF50;
                }
                
                @media (max-width: 576px) {
                    .bill-summary {
                        margin: 5px;
                        padding: 15px;
                    }
                    
                    .bill-item {
                        margin: 5px;
                    }
                    
                    .bill-item-header {
                        flex-direction: column;
                        align-items: flex-start;
                        gap: 0.5rem;
                    }
                    
                    .dish-item {
                        flex-direction: column;
                        align-items: flex-start;
                        gap: 0.25rem;
                    }
                    
                    .dish-price {
                        align-self: flex-end;
                    }
                }
                </style>"""
                
                reply = f"""
                {css_styles}
                <div class="bill-container">
                    <div class="bill-header">
                        <h3>📋 Hóa đơn của bạn</h3>
                    </div>
                    {summary_html}
                    {status_message}
                    {bills_html}
                    <div class="text-center mt-2">
                        <p class="text-muted mb-0 small">
                            Bạn muốn thanh toán, xác nhận hóa đơn nào, hay gọi thêm món gì nữa không?
                        </p>
                    </div>
                </div>
                """
            self.conversation_history.append(
                ChatMessage(role="assistant", content=reply)
            )
            return clean_star_lines(reply)
        # Nhận diện yêu cầu kiểm tra/truy vấn giỏ hàng (order) (ưu tiên intent cứng)
        check_cart_phrases = [
            "kiểm tra", "giỏ hàng", "đã có", "có trong giỏ", "đang có món gì", "liệt kê món đã chọn", "món đã chọn", "món đã gọi", "món trong giỏ", "món trong order", "món đã order", "món đã đặt",
            "xem thực đơn", "xem menu", "xem món đã chọn", "xem món đã gọi"
        ]
        if any(phrase in user_message.lower() for phrase in check_cart_phrases):
            dish_name = self._extract_dish_name(user_message)
            if dish_name:
                has_dish = order_manager.has_dish_in_order(user_id, dish_name)
                if has_dish:
                    reply = f"✅ {dish_name} đã có trong giỏ hàng của bạn."
                else:
                    reply = f"❌ {dish_name} chưa có trong giỏ hàng của bạn."
                self.conversation_history.append(
                    ChatMessage(role="assistant", content=reply)
                )
                return clean_star_lines(reply)
            summary = order_manager.get_order_summary(user_id)
            if not summary:
                reply = "Giỏ hàng của bạn hiện đang trống. Bạn muốn gọi món nào không?"
            else:
                reply = "🛒 Các món bạn đã chọn trong giỏ hàng:\n"
                for idx, item in enumerate(summary, 1):
                    reply += f"{idx}. {item['dish']} x{item['quantity']}\n"
                reply += "Bạn muốn thực hiện 'Thanh toán' hay gọi thêm món nào nữa không?"
            self.conversation_history.append(
                ChatMessage(role="assistant", content=reply)
            )
            return clean_star_lines(reply)
        # Nhận diện yêu cầu xóa toàn bộ order (ưu tiên intent cứng)
        clear_order_phrases = ["xóa order", "xóa hết order", "xóa toàn bộ", "hủy order", "hủy đơn", "clear order", "xóa giỏ hàng", "hủy giỏ hàng"]
        if any(phrase in user_message.lower() for phrase in clear_order_phrases):
            order_manager.clear_order(user_id)
            reply = "✅ Đã xóa toàn bộ order của bạn. Bạn muốn bắt đầu order mới hay cần tôi tư vấn món gì không ạ?"
            self.conversation_history.append(
                ChatMessage(role="assistant", content=reply)
            )
            return clean_star_lines(reply)
        # Nhận diện yêu cầu thanh toán (ưu tiên intent cứng, không để LLM tổng hợp bill)
        payment_phrases = [
            "thanh toán", "tính tiền", "in bill", "xem bill", "bill", "tổng tiền", "xem hóa đơn", "hóa đơn"
        ]
        qr_phrases = [
            "chuyển khoản", "qr banking", "quét mã qr"
        ]
        if any(phrase in user_message.lower() for phrase in qr_phrases):
            # Lấy tất cả hóa đơn đã hoàn thành (trạng thái 'done')
            all_bills = order_manager.get_all_bills(user_id)
            done_bills = [bill for bill in all_bills if bill.status == 'done' and bill.items]
            print(f"[DEBUG] QR Payment - user_id: {user_id}")
            print(f"[DEBUG] QR Payment - all_bills count: {len(all_bills)}")
            print(f"[DEBUG] QR Payment - done_bills count: {len(done_bills)}")
            for i, bill in enumerate(all_bills):
                print(f"[DEBUG] Bill {i}: status={bill.status}, items_count={len(bill.items) if bill.items else 0}")
            
            if not done_bills:
                reply = "Bạn không có hóa đơn nào cần thanh toán. Khi món ăn đã hoàn thành, bạn sẽ nhận được mã QR để thanh toán."
            else:
                total_amount = sum(sum(getattr(item.dish, 'price', 0) * item.quantity for item in bill.items) for bill in done_bills)
                bill_ids = ', '.join([bill.order_id[:8] for bill in done_bills])
                qr_img_url = f"https://img.vietqr.io/image/bidv-5811471677-qr_only.png?amount={total_amount}&addInfo=Thanh%20toan%20cac%20hoa%20don%20{bill_ids}&accountName=NGUYEN%20NGOC%20PHUC"
                reply = (
                    f"💳 Vui lòng quét mã QR dưới đây để thanh toán chuyển khoản cho <b>tất cả hóa đơn đã hoàn thành</b>.<br>"
                    f"<img src='{qr_img_url}' alt='QR Banking' width='180'><br>"
                    f"Số tiền: <b>{total_amount:,}đ</b><br>"
                    f"Nội dung chuyển khoản: <b>Thanh toán các hóa đơn {bill_ids}</b><br>"
                    f"Sau khi chuyển khoản, vui lòng <b>chờ nhà hàng xác nhận</b>. Khi xác nhận xong, hệ thống sẽ tự động thông báo cho bạn!"
                )
            self.conversation_history.append(
                ChatMessage(role="assistant", content=reply)
            )
            return clean_star_lines(reply)
        if any(phrase in user_message.lower() for phrase in payment_phrases):
            bill = order_manager.get_bill(user_id)
            if not bill['items']:
                reply = "Bạn chưa có món nào trong hóa đơn. Hãy chọn món trước nhé!"
            else:
                reply = f"🧾 Hóa đơn của bạn (Order ID: {bill['order_id']}):\n"
                for idx, item in enumerate(bill['items'], 1):
                    note_str = f" (Ghi chú: {item['note']})" if item['note'] else ""
                    reply += f"{idx}. {item['dish']} x{item['quantity']}{note_str} - {item['unit_price']:,}đ = {item['amount']:,}đ\n"
                reply += f"Tổng cộng: {bill['total']:,}đ\n"
                reply += "Bạn muốn thanh toán bằng hình thức nào? Chọn 'Chuyển khoản' để nhận mã QR hoặc 'Tiền mặt' nhé!"
            self.conversation_history.append(
                ChatMessage(role="assistant", content=reply)
            )
            return clean_star_lines(reply)
        # Intent test QR code hiển thị
        if user_message.lower().strip() == "test qr":
            reply = "Test QR: <img src='https://img.vietqr.io/image/bidv-5811471677-qr_only.png?amount=100000&addInfo=Test' width='200'>"
            self.conversation_history.append(
                ChatMessage(role="assistant", content=reply)
            )
            return clean_star_lines(reply)
        # Không tự động thêm món khi chỉ nhắc tên món trong câu hỏi hoặc khi intent là recommendation, dinh dưỡng, nguyên liệu, ...
        # Các nhánh còn lại chỉ trả lời thông tin, không thêm vào order
        # Nếu user chỉ hỏi thông tin (giá, calo, dinh dưỡng, nguyên liệu, cách làm, v.v.), không tự động thêm món, để LLM trả lời tự nhiên
        # Nhận diện yêu cầu thêm ghi chú cho món ăn (ưu tiên intent cứng)
        note_phrases = ["note", "ghi chú", "yêu cầu","tôi muốn ghi chú","tôi cần ghi chú","tôi muốn note", "tôi muốn ghi chú","lưu ý"]
        if self.pending_note.get('waiting_for_selection', False):
            try:
                selection = int(user_message.strip())
                if 1 <= selection <= len(self.last_order_list):
                    selected_dish = self.last_order_list[selection - 1]
                    # Sau khi chọn món, hỏi lại nội dung ghi chú
                    self.pending_note = {
                        'waiting_for_note': True,
                        'dish': selected_dish['dish']
                    }
                    reply = f"Bạn muốn ghi chú gì cho món {selected_dish['dish']}?"
                    self.conversation_history.append(
                        ChatMessage(role="assistant", content=reply)
                    )
                    return clean_star_lines(reply)
            except ValueError:
                self.pending_note = {}
                pass
        # Nếu đang chờ nội dung ghi chú cho món đã chọn
        if self.pending_note.get('waiting_for_note', False):
            dish_name = self.pending_note.get('dish', '')
            note = user_message.strip()
            if dish_name and note:
                current_note = order_manager.get_dish_note(user_id, dish_name)
                if order_manager.update_note(user_id, dish_name, note):
                    if current_note:
                        reply = f"✅ Đã thêm ghi chú '{note}' cho món {dish_name}. Ghi chú hiện tại: '{order_manager.get_dish_note(user_id, dish_name)}'. Bạn cần ghi chú gì thêm hay 'Thanh toán' hay 'Xem hóa đơn' hay cần gì nữa không?"
                    else:
                        reply = f"✅ Đã thêm ghi chú '{note}' cho món {dish_name}. Bạn cần ghi chú gì thêm hay 'Thanh toán' hay 'Xem hóa đơn' hay cần gì nữa không?"
                    self.pending_note = {}
                    self.conversation_history.append(
                        ChatMessage(role="assistant", content=reply)
                    )
                    return clean_star_lines(reply)
        # Nếu user nhập note/ghi chú mà không kèm tên món, tự động note vào món duy nhất nếu chỉ có 1 món trong order
        if any(phrase in user_message.lower() for phrase in note_phrases):
            dish_name = self._extract_dish_name(user_message)
            if not dish_name:
                order_summary = order_manager.get_order_summary(user_id)
                if not order_summary:
                    reply = "Bạn chưa gọi món nào. Vui lòng gọi món trước khi thêm ghi chú!"
                    self.conversation_history.append(
                        ChatMessage(role="assistant", content=reply)
                    )
                    return clean_star_lines(reply)
                if len(order_summary) == 1:
                    # Nếu chỉ có 1 món, hỏi nội dung ghi chú và lưu luôn vào món đó
                    self.pending_note = {
                        'waiting_for_note': True,
                        'dish': order_summary[0]['dish']
                    }
                    reply = f"Bạn muốn ghi chú gì cho món {order_summary[0]['dish']}?"
                    self.conversation_history.append(
                        ChatMessage(role="assistant", content=reply)
                    )
                    return clean_star_lines(reply)
                else:
                    # Nếu có nhiều món, hỏi chọn món như cũ
                    self.last_order_list = order_summary
                    note = user_message.lower()
                    for phrase in note_phrases:
                        note = note.replace(phrase, "")
                    note = note.strip()
                    self.pending_note = {
                        'waiting_for_selection': True,
                        'note': note
                    }
                    reply = "Bạn muốn thêm ghi chú cho món nào? Đây là các món bạn đã gọi:\n"
                    for idx, item in enumerate(order_summary, 1):
                        note_str = f" (Ghi chú hiện tại: {item['note']})" if item['note'] else ""
                        reply += f"{idx}. {item['dish']} x{item['quantity']}{note_str}\n"
                    self.conversation_history.append(
                        ChatMessage(role="assistant", content=reply)
                    )
                    return clean_star_lines(reply)
            # Nếu không có tên món, fallback về logic cũ bên dưới
        # --- Xử lý xác nhận thực đơn từ last_suggested_dishes (ưu tiên intent cứng) ---
        confirm_menu_phrases = [
            "ok", "chốt thực đơn", "đồng ý", "lấy thực đơn này", "chốt menu", "chốt", 
            "xác nhận thực đơn", "xác nhận menu", "được rồi", "được", "yes", "take this menu", "confirm menu",
            "miền nào cũng được", "gì cũng được", "món nào cũng được", "tùy bạn", "tùy chef", 
            "tùy nhà hàng", "tùy ý", "tùy chọn", "tùy MC", "tùy gợi ý",
            "chốt các món này", "lấy các món này", "đồng ý các món này"
        ]
        # CHỈ xử lý xác nhận thực đơn khi có pending menu và không phải xác nhận cho nhà hàng
        is_restaurant_confirmation = any(phrase in user_message.lower() for phrase in [
            "cho nhà hàng", "gửi cho nhà hàng", "cho bếp", "gửi bếp", "hóa đơn", "order cho nhà hàng"
        ])
        
        if any(phrase in user_message.lower() for phrase in confirm_menu_phrases) and not is_restaurant_confirmation:
            # Nếu user nhắc tên món trong câu chốt
            dish_name = self._extract_dish_name(user_message)
            if dish_name:
                dish = rag_system.dishes_lookup.get(dish_name, None)
                if dish:
                    order_manager.add_dish(user_id, dish, quantity=1)
                    reply = f"✅ Đã chốt {dish_name} cho bạn. Bạn muốn 'Xem hóa đơn' hay 'Thanh toán' hay cần hỗ trợ gì thêm không ạ?"
                    self.conversation_history.append(
                        ChatMessage(role="assistant", content=reply)
                    )
                    return clean_star_lines(reply)
            # Nếu không có tên món và có pending menu, chốt toàn bộ pending menu
            if self.last_suggested_dishes:
                return clean_star_lines(insert_dish_images(self.auto_confirm_pending_order(user_id)))
        # Nhận diện yêu cầu xóa từng món khỏi order
        remove_phrases = ["xóa", "bỏ", "hủy", "remove", "delete"]
        if any(phrase in user_message.lower() for phrase in remove_phrases):
            dish_name = self._extract_dish_name(user_message)
            if not dish_name:
                reply = "Bạn muốn xóa món nào? Vui lòng nói rõ tên món cần xóa."
                self.conversation_history.append(ChatMessage(role="assistant", content=reply))
                return clean_star_lines(reply)
            order_summary = order_manager.get_order_summary(user_id)
            if not order_summary or not any(item['dish'] == dish_name for item in order_summary):
                reply = f"Không tìm thấy món {dish_name} trong hóa đơn của bạn."
                self.conversation_history.append(ChatMessage(role="assistant", content=reply))
                return clean_star_lines(reply)
            order_manager.remove_dish(user_id, dish_name)
            reply = f"✅ Đã xóa món {dish_name} khỏi hóa đơn của bạn."
            self.conversation_history.append(ChatMessage(role="assistant", content=reply))
            return clean_star_lines(reply)
        # Nhận diện xác nhận chốt món cho nhà hàng (chỉ update status, không thêm món)
        confirm_order_phrases = [
            "xác nhận chốt món cho nhà hàng", "chốt order cho nhà hàng", "gửi order cho nhà hàng", 
            "xác nhận đặt món cho nhà hàng", "gửi món cho nhà hàng", "xác nhận chốt thực đơn cho nhà hàng",
            "xác nhận hóa đơn", "xác nhận order", "gửi hóa đơn cho bếp", "chốt hóa đơn"
        ]
        if any(phrase in user_message.lower() for phrase in confirm_order_phrases):
            # Chỉ update status bill hiện tại, KHÔNG thêm món mới từ pending menu
            # Clear pending menu để tránh nhầm lẫn
            self.last_suggested_dishes = []
            order_manager.update_bill_status(user_id, "confirmed", order_id=order_id)
            
            # Lưu order vào database để admin có thể thấy
            try:
                from core.database_manager import db_manager
                
                bill_data = order_manager.get_bill(user_id, order_id=order_id)
                if bill_data and bill_data.get('items'):
                    # Chuẩn bị dữ liệu để lưu vào database
                    save_data = bill_data.copy()
                    save_data['user_id'] = user_id
                    save_data['order_id'] = bill_data['order_id']
                    save_data['total_amount'] = bill_data.get('total', 0)
                    save_data['status'] = "confirmed"
                    
                    # Tìm table thực tế từ table_manager nếu có
                    try:
                        from core.table_manager import table_manager
                        table = table_manager.find_table_by_user_context(user_id)
                        if table:
                            save_data['table_id'] = table.id
                        else:
                            save_data['table_id'] = user_id
                    except Exception as e:
                        print(f"Warning: Không thể tìm table, dùng user_id: {e}")
                        save_data['table_id'] = user_id
                    
                    # Lưu vào database SQLite
                    db_manager.save_order(save_data)
                    print(f"[CHATBOT] Đã lưu đơn hàng confirmed vào database: {save_data['order_id']}")
                    
            except Exception as e:
                print(f"[CHATBOT] Lỗi khi lưu order vào database: {e}")
                import traceback
                traceback.print_exc()
            
            reply = "✅ Đã xác nhận chốt món cho nhà hàng. Đơn hàng của bạn sẽ được nhà bếp chuẩn bị ngay!"
            self.conversation_history.append(ChatMessage(role="assistant", content=reply))
            return clean_star_lines(reply)
        # Các intent còn lại hoặc không khớp thì luôn để LLM trả lời tự nhiên
        try:
            self.conversation_history.append(
                ChatMessage(role="user", content=user_message)
            )
            # Nhận diện các câu xác nhận ngắn
            confirm_phrases = ["có", "ok", "đúng rồi", "vâng", "phải", "đúng", "chuẩn", "chính xác", "uh", "ừ", "dạ", "yeah", "yes"]
            user_message_norm = user_message.strip().lower()
            is_confirm = user_message_norm in confirm_phrases
            # Tự động nhớ món ăn đang focus
            dish_name = ""
            quantity = 1
            # Nếu user nhập câu có tên nhiều món và số lượng, thêm tất cả vào order
            # (LOẠI BỎ ĐOẠN NÀY, không tự động thêm món khi chỉ nhắc tên món)
            # if not is_confirm:
            #     # Lấy danh sách tên món (ưu tiên tên dài nhất trước)
            #     dish_names = sorted([dish.name for dish in rag_system.dishes_lookup.values()], key=len, reverse=True)
            #     added_dishes = []
            #     user_msg_norm = user_message.lower()
            #     used_spans = []
            #     for dish_name in dish_names:
            #         # Tìm tất cả vị trí xuất hiện tên món trong câu
            #         for m in re.finditer(re.escape(dish_name.lower()), user_msg_norm):
            #             start, end = m.start(), m.end()
            #             # Tránh trùng lặp span
            #             if any(us <= start < ue or us < end <= ue for us, ue in used_spans):
            #                 continue
            #             # Tìm số lượng trước tên món
            #             qty_match = re.search(r'(\d+)\s*(phần|chén|dĩa|bát|ly|cốc|miếng|cái|suất|phần ăn)?\s*' + re.escape(dish_name.lower()), user_msg_norm[max(0, start-10):end])
            #             if qty_match:
            #                 quantity = int(qty_match.group(1))
            #             else:
            #                 # Tìm số lượng sau tên món
            #                 qty_match2 = re.search(re.escape(dish_name.lower()) + r'\s*x?(\d+)', user_msg_norm[end:end+6])
            #                 quantity = int(qty_match2.group(1)) if qty_match2 else 1
            #             dish = rag_system.dishes_lookup.get(dish_name, None)
            #             if dish:
            #                 order_manager.add_dish(user_id, dish, quantity=quantity)
            #                 added_dishes.append(f"✅ Đã thêm {quantity} {dish_name}")
            #                 self.last_dish = dish_name
            #                 used_spans.append((start, end))
            #     if added_dishes:
            #         reply = ", ".join(added_dishes) + ". Bạn muốn 'Thanh toán' hay 'Xem hóa đơn' hay 'Thêm ghi chú' hay muốn gọi thêm món nào hay cần gì nữa không?"
            #         self.conversation_history.append(
            #             ChatMessage(role="assistant", content=reply)
            #         )
            #         return clean_star_lines(insert_dish_images(reply))
            # Phân tích intent hiện tại
            intent = text_processor.analyze_query_intent(user_message)
            # print('[DEBUG] intent sau khi phân tích:', intent)
            # Nếu intent là contact, ưu tiên gọi handle_intent_contact nếu có
            if intent['type'] == 'contact':
                try:
                    from intent.intent_contact import handle_intent_contact
                    contact_info = handle_intent_contact(user_message)
                    if contact_info:
                        reply = f"🏠 Thông tin liên hệ nhà hàng: {contact_info}"
                        self.conversation_history.append(
                            ChatMessage(role="assistant", content=reply)
                        )
                        return clean_star_lines(reply)
                    else:
                        # Fallback sang get_restaurant_contact nếu có
                        try:
                            from intent.intent_contact import get_restaurant_contact
                            contact_info = get_restaurant_contact()
                            reply = f"🏠 Thông tin liên hệ nhà hàng: {contact_info}"
                            self.conversation_history.append(
                                ChatMessage(role="assistant", content=reply)
                            )
                            return clean_star_lines(reply)
                        except Exception:
                            pass
                except Exception as e:
                    reply = "Xin lỗi, tôi không lấy được thông tin liên hệ nhà hàng lúc này."
                    self.conversation_history.append(
                        ChatMessage(role="assistant", content=reply)
                    )
                    return clean_star_lines(reply)
            
            # Nếu intent là hỏi về giá, ưu tiên trả lời trực tiếp về giá
            if intent['type'] == 'price':
                dish_name = self._extract_dish_name(user_message)
                if dish_name:
                    dish = rag_system.dishes_lookup.get(dish_name, None)
                    if dish and dish.price:
                        reply = f"💰 Giá món <span class=\"dish-name\">{dish.name}</span> là: <b>{dish.price}</b>. Bạn có muốn gọi món này không?"
                        self.last_dish = dish_name
                        self.conversation_history.append(
                            ChatMessage(role="assistant", content=reply)
                        )
                        return clean_star_lines(insert_dish_images(reply))
                    elif dish:
                        reply = f"Xin lỗi, hiện tại tôi chưa có thông tin giá cho món <span class=\"dish-name\">{dish.name}</span>. Bạn có thể liên hệ nhà hàng để hỏi giá nhé!"
                        self.conversation_history.append(
                            ChatMessage(role="assistant", content=reply)
                        )
                        return clean_star_lines(insert_dish_images(reply))
                elif self.last_dish:
                    # Nếu không tìm thấy tên món trong câu hỏi nhưng có last_dish
                    dish = rag_system.dishes_lookup.get(self.last_dish, None)
                    if dish and dish.price:
                        reply = f"💰 Giá món <span class=\"dish-name\">{dish.name}</span> là: <b>{dish.price}</b>. Bạn có muốn gọi món này không?"
                        self.conversation_history.append(
                            ChatMessage(role="assistant", content=reply)
                        )
                        return clean_star_lines(insert_dish_images(reply))
                    elif dish:
                        reply = f"Xin lỗi, hiện tại tôi chưa có thông tin giá cho món <span class=\"dish-name\">{dish.name}</span>. Bạn có thể liên hệ nhà hàng để hỏi giá nhé!"
                        self.conversation_history.append(
                            ChatMessage(role="assistant", content=reply)
                        )
                        return clean_star_lines(insert_dish_images(reply))
                else:
                    reply = "Bạn muốn hỏi giá món nào ạ? Vui lòng cho tôi biết tên món để tôi có thể tra cứu giá cho bạn."
                    self.conversation_history.append(
                        ChatMessage(role="assistant", content=reply)
                    )
                    return clean_star_lines(reply)
            
            # Nếu user xác nhận, và đã có last_dish, thì chỉ trả lời thông tin về món đó, KHÔNG tự động thêm vào order nữa
            if is_confirm and self.last_dish:
                dish = rag_system.dishes_lookup.get(self.last_dish, None)
                if dish:
                    context = rag_system.get_context_for_llm(self.last_dish)
                    full_prompt = self._create_full_prompt(user_message, context, intent)
                    llm = ai_models.get_llm()
                    response = llm.invoke(full_prompt)
                    bot_response = self._process_llm_response(response, intent, context, user_message, user_id=user_id, order_id=order_id)
                    self.conversation_history.append(
                        ChatMessage(role="assistant", content=bot_response)
                    )
                    return clean_star_lines(insert_dish_images(bot_response))
            # Nếu intent là recommendation và có tên món trong câu trả lời, tự động thêm vào order
            # (LOẠI BỎ ĐOẠN NÀY, chỉ trả lời thông tin, không thêm vào order)
            if intent['type'] == 'recommendation':
                # Thử extract tên món từ câu trả lời của LLM hoặc user_message
                dish_name = self._extract_dish_name(user_message)
                if dish_name:
                    dish = rag_system.dishes_lookup.get(dish_name, None)
                    if dish:
                        order_manager.add_dish(user_id, dish, quantity=1)
                        self.last_dish = dish_name
                        reply = f"✅ Đã thêm {dish_name} vào order. Bạn muốn 'Thanh toán' hay gọi thêm món nào hay cần gì nữa không?"
                        self.conversation_history.append(
                            ChatMessage(role="assistant", content=reply)
                        )
                        return clean_star_lines(insert_dish_images(reply))
            # Nhận diện các vị đặc trưng
            flavor_keywords = [
                ("ngọt", ["ngọt", "sweet"]),
                ("cay", ["cay", "spicy"]),
                ("chua", ["chua", "sour"]),
                ("mặn", ["mặn", "salty"]),
                ("béo", ["béo", "rich", "creamy"]),
                ("thanh", ["thanh", "fresh"]),
            ]
            found_flavor = None
            for flavor, keys in flavor_keywords:
                for k in keys:
                    if re.search(rf'\\b{k}\\b', user_message.lower()):
                        found_flavor = flavor
                        break
                if found_flavor:
                    break
            if found_flavor:
                # Gợi ý các món có vị tương ứng trong tên hoặc mô tả món, chỉ những món còn available
                suggested_dishes = [dish for dish in rag_system.dishes_lookup.values()
                                    if (found_flavor in dish.name.lower() or (hasattr(dish, 'description') and found_flavor in getattr(dish, 'description', '').lower()))
                                    and self._is_dish_available(dish.name)]
                if suggested_dishes:
                    self.last_suggested_dishes = [dish.name for dish in suggested_dishes[:20]]  # Lưu lại tên món vừa gợi ý
                    reply = f"🍜 Một số món có vị {found_flavor} mà nhà hàng gợi ý cho bạn:<br>"
                    for idx, dish in enumerate(suggested_dishes[:20], 1):
                        img_html = f"<br><img src='{dish.image}' alt='{dish.name}' width='120'>" if getattr(dish, 'image', None) else ""
                        reply += f"{idx}. {dish.name}{img_html}<br>"
                    reply += "Bạn muốn 'Thanh toán' hay biết thêm về món nào không ạ?"
                    self.conversation_history.append(
                        ChatMessage(role="assistant", content=reply)
                    )
                    return clean_star_lines(insert_dish_images(reply))
            # Nếu user hỏi về nguyên liệu chính (gà, bò, mực, tôm, cá, heo, v.v.)
            main_ingredients = ["gà", "bò", "mực", "tôm", "cá", "heo", "thịt", "vịt", "cua", "ghẹ", "sò", "ốc", "tép", "trứng", "rau", "chay"]
            found_ingredient = None
            for ing in main_ingredients:
                if re.search(rf'\\b{ing}\\b', user_message.lower()):
                    found_ingredient = ing
                    break
            if found_ingredient:
                # Sử dụng hàm normalize để so sánh không dấu, không phân biệt hoa thường
                def normalize(text):
                    text = text.lower()
                    text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
                    return text
                found_ingredient_norm = normalize(found_ingredient)
                matched_dishes = [dish for dish in rag_system.dishes_lookup.values()
                                  if found_ingredient_norm in normalize(dish.name)
                                  and self._is_dish_available(dish.name)]
                if matched_dishes:
                    self.last_suggested_dishes = [dish.name for dish in matched_dishes[:20]]  # Lưu lại tên món vừa gợi ý
                    reply = f"🍜 Chào bạn, dưới đây là các món có '{found_ingredient}' trong tên món của thực đơn nhà hàng:<br>"
                    for idx, dish in enumerate(matched_dishes[:20], 1):
                        img_html = f"<br><img src='{dish.image}' alt='{dish.name}' width='120'>" if getattr(dish, 'image', None) else ""
                        reply += f"{idx}. {dish.name}{img_html}<br>"
                    reply += "Bạn muốn 'Thanh toán' hay biết thêm về món nào không ạ?"
                    self.conversation_history.append(
                        ChatMessage(role="assistant", content=reply)
                    )
                    return clean_star_lines(insert_dish_images(reply))
                # Nếu không tìm thấy, vẫn tiếp tục logic như cũ
            # Nếu user hỏi tiếp kiểu "còn món nào nữa không", "gợi ý thêm",... thì dùng lại intent/filters trước đó
            followup_phrases = ["còn món nào nữa", "gợi ý thêm", "thêm món", "còn gì nữa", "còn món nào", "nữa không", "nữa nhé", "món khác", "khác không"]
            if any(phrase in user_message.lower() for phrase in followup_phrases):
                if self.last_intent:
                    intent = self.last_intent.copy()
                    # Nếu user hỏi tiếp mà không nêu rõ filter, giữ lại filter cũ
                    if self.last_filters:
                        intent['filters'] = self.last_filters.copy()
                    # THÊM LOGIC LOẠI TRỪ CÁC MÓN ĐÃ GỢI Ý
                    if 'exclude_dishes' not in intent:
                        intent['exclude_dishes'] = []
                    if self.last_suggested_dishes:
                        intent['exclude_dishes'].extend(self.last_suggested_dishes)
                        print(f"[DEBUG] Excluding previously suggested dishes: {self.last_suggested_dishes}")
                context_query = self.last_query or user_message
            else:
                context_query = user_message
            # Nếu hỏi về nguyên liệu/cách làm mà không nêu tên món, dùng last_dish
            if intent['type'] in ["ingredient", "recipe"] and not dish_name and self.last_dish:
                context_query = self.last_dish
            
            # Lấy danh sách món cần loại trừ
            exclude_dishes = intent.get('exclude_dishes', [])
            context = rag_system.get_context_for_llm(context_query, exclude_dishes)
            # Nếu context không có món nào phù hợp, trả lời xin lỗi, không gọi LLM
            if context.strip().startswith("Không tìm thấy thông tin phù hợp"):
                if "cơm" in user_message.lower():
                    # Nếu đang focus vào một món cụ thể, trả lời về món đó
                    if self.last_dish:
                        dish = rag_system.dishes_lookup.get(self.last_dish, None)
                        if dish:
                            reply = f"🍜 Món <span class=\"dish-name\">{dish.name}</span> hoàn toàn có thể dùng chung với cơm, rất ngon và bổ dưỡng đó ạ. Bạn muốn biết thêm gì về món này không?"
                            self.conversation_history.append(
                                ChatMessage(role="assistant", content=reply)
                            )
                            return clean_star_lines(insert_dish_images(reply))
                    # Nếu không có món focus, gợi ý các món hợp ăn với cơm
                    suggest_keywords = ["kho", "xào", "chiên", "rán", "rim", "cá", "thịt", "gà", "bò", "heo", "tôm", "mực", "trứng", "sườn", "đậu", "mắm", "mặn"]
                    # Sử dụng hàm normalize để so sánh không dấu, không phân biệt hoa thường
                    suggest_keywords_norm = [normalize(kw) for kw in suggest_keywords]
                    suggested_dishes = [dish for dish in rag_system.dishes_lookup.values()
                                        if any(kw in normalize(dish.name) for kw in suggest_keywords_norm)
                                        and self._is_dish_available(dish.name)]
                    if suggested_dishes:
                        reply = "🍜 Một số món rất hợp ăn với cơm rất ngon mà nhà hàng gợi ý cho bạn:<br>"
                        for idx, dish in enumerate(suggested_dishes[:20], 1):
                            img_html = f"<br><img src='{dish.image}' alt='{dish.name}' width='120'>" if getattr(dish, 'image', None) else ""
                            reply += f"{idx}. {dish.name}{img_html}<br>"
                        reply += "Bạn muốn 'Thanh toán' hay biết thêm về món nào không ạ?"
                        self.conversation_history.append(
                            ChatMessage(role="assistant", content=reply)
                        )
                        return clean_star_lines(insert_dish_images(reply))
                # Lưu lại intent/filters/query cho lần hỏi tiếp theo
            self.last_intent = intent.copy()
            self.last_filters = intent.get('filters', {}).copy() if 'filters' in intent else {}
            self.last_query = context_query
            full_prompt = self._create_full_prompt(user_message, context, intent)
            llm = ai_models.get_llm()
            response = llm.invoke(full_prompt)
            bot_response = self._process_llm_response(response, intent, context, user_message, user_id=user_id, order_id=order_id)
            self.conversation_history.append(
                ChatMessage(role="assistant", content=bot_response)
            )
            return clean_star_lines(insert_dish_images(bot_response))
        except Exception as e:
            error_msg = f"Xin lỗi, tôi gặp lỗi khi xử lý câu hỏi của bạn: {str(e)}"
            self.conversation_history.append(
                ChatMessage(role="assistant", content=error_msg)
            )
            return clean_star_lines(insert_dish_images(error_msg))

    def _extract_dish_name(self, user_message: str) -> str:
        user_norm = normalize(user_message)
        print(f"[DEBUG][extract] user_norm: {user_norm}")
        for dish in rag_system.dishes_lookup.values():
            dish_norm = normalize(dish.name)
            print(f"[DEBUG][extract] so khop: {user_norm} == {dish_norm} ? {user_norm == dish_norm}")
            if user_norm == dish_norm:
                print(f"[DEBUG][extract] MATCH TUYET DOI: {dish.name}")
                return dish.name
        # Nếu không match tuyệt đối, thử match substring
        for dish in rag_system.dishes_lookup.values():
            dish_norm = normalize(dish.name)
            if dish_norm in user_norm:
                return dish.name
        # Nếu không match substring, thử fuzzy match với cutoff 0.7
        dish_names = [dish.name for dish in rag_system.dishes_lookup.values()]
        norm_dish_names = [normalize(name) for name in dish_names]
        import difflib
        match = difflib.get_close_matches(user_norm, norm_dish_names, n=1, cutoff=0.7)
        if match:
            idx = norm_dish_names.index(match[0])
            return dish_names[idx]
        # Nếu không match fuzzy, thử match tất cả từ khóa chính của tên món đều xuất hiện trong câu hỏi
        for dish in rag_system.dishes_lookup.values():
            dish_norm = normalize(dish.name)
            keywords = [w for w in dish_norm.split() if len(w) > 1]
            if all(kw in user_norm for kw in keywords):
                return dish.name
        return ""

    def _create_system_prompt(self) -> str:
        return (
            "Bạn là MC ảo của nhà hàng Việt Nam, chuyên nghiệp, thân thiện và hiểu biết sâu sắc về ẩm thực.\n"
            "\nNHIỆM VỤ:\n"
            "- Tư vấn món ăn, khẩu phần, thực đơn, giá tiền, dinh dưỡng, cách làm, nguyên liệu... dựa trên dữ liệu nhà hàng cung cấp.\n"
            "- Gợi ý món phù hợp với sở thích, tình huống, số người, tâm trạng, vùng miền, dịp đặc biệt.\n"
            "- Tính tổng tiền khẩu phần, giải thích giá, đơn vị tính, thành phần dinh dưỡng nếu khách hỏi.\n"
            "- Lên thực đơn cho nhóm, gia đình, sự kiện, hoặc tư vấn món theo yêu cầu.\n"
            "- KHI KHÁCH HỎI VỀ GƢỢI Ý MÓN NGON, LUÔN GỢI Ý TỪ 3-5 MÓN KHÁC NHAU để khách có nhiều lựa chọn.\n"
            "\nPHONG CÁCH TRÌNH BÀY:\n"
            "- Thân thiện, tự nhiên, chuyên nghiệp như một người phục vụ thực thụ.\n"
            "- Luôn xưng hô lịch sự, chủ động hỏi lại để phục vụ tốt hơn.\n"
            "- Chỉ trả lời dựa trên dữ liệu nhà hàng, không bịa đặt món ăn ngoài thực đơn.\n"
            "\nQUY TẮC:\n"
            "1. Chỉ tư vấn dựa trên thông tin món ăn, giá, dinh dưỡng, thực đơn có trong dữ liệu.\n"
            "2. Nếu không có thông tin, hãy lịch sự xin lỗi và gợi ý món khác.\n"
            "3. Khi khách hỏi về giá, khẩu phần, hãy tính toán và giải thích rõ ràng.\n"
            "4. Khi khách hỏi về món đặc biệt, vùng miền, dịp lễ, hãy ưu tiên gợi ý phù hợp.\n"
            "5. Luôn hỏi lại khách có muốn tư vấn thêm, hoặc cần hỗ trợ gì khác không.\n"
            "6. TUYỆT ĐỐI KHÔNG tự nghĩ ra món ăn, thực đơn, nguyên liệu, giá, dinh dưỡng ngoài danh sách context. Nếu không có trong context, hãy xin lỗi và gợi ý hỏi món khác.\n"
            "7. TUYỆT ĐỐI KHÔNG được tự tổng hợp hóa đơn, tổng tiền, danh sách món đã gọi, chỉ được trả lời hóa đơn/thanh toán khi có context hóa đơn từ hệ thống. Nếu không có context hóa đơn, hãy xin lỗi và hướng dẫn khách dùng chức năng 'Xem hóa đơn' hoặc 'Thanh toán'.\n"
            "\nĐỊNH DẠNG PHẢN HỒI:\n"
            "- Khi gợi ý thực đơn, LUÔN trình bày NHIỀU MÓN ĂN (3-5 món) trên nhiều dòng theo đúng format:\n"
            "[Tên món]: (Giá VNĐ/phần) Mô tả...\n"
            "Ví dụ:\n"
            "Gỏi rau mầm tôm: (60.000 VNĐ/phần) Món này thanh mát, nhiều rau mầm và tôm tươi, lại có vị chua ngọt rất dễ ăn.\n"
            "Canh bó xôi bò viên: (40.000 VNĐ/phần) Canh có rau bó xôi xanh mướt, ngọt mát, lại có thêm bò viên đậm đà.\n"
            "Bún chả cá Nha Trang: (45.000 VNĐ/phần) Bún với chả cá thơm ngon, nước dùng đậm đà hương vị miền Trung.\n"
            "\nHãy trả lời bằng tiếng Việt tự nhiên, thân thiện, chuyên nghiệp như một MC nhà hàng thực thụ!"
        )

    def _create_full_prompt(self, user_message: str, context: str, intent: Dict[str, Any]) -> List:
        # Tăng số lượng history lên 30
        messages = []
        # Add system prompt if not empty
        if self.system_prompt and self.system_prompt.strip():
            messages.append(SystemMessage(content=self.system_prompt))
        context_message = f"""
CHỈ ĐƯỢC PHÉP TRẢ LỜI DỰA TRÊN DANH SÁCH MÓN ĂN DƯỚI ĐÂY (context). TUYỆT ĐỐI KHÔNG ĐƯỢC TỰ NGHĨ RA MÓN ĂN, GIÁ, NGUYÊN LIỆU, DINH DƯỠNG, CÁCH LÀM, V.V. NGOÀI DANH SÁCH NÀY. 

QUAN TRỌNG: KHI KHÁCH HỎI "GỢI Ý MÓN NGON", "GỢI Ý MÓN ĂN", "MÓN GÌ NGON", v.v. HÃY LUÔN GỢI Ý 3-5 MÓN KHÁC NHAU từ danh sách context để khách có nhiều lựa chọn.

KHI GỢI Ý THỰC ĐƠN THEO GIÁ TRỊ (VD: ĐỦ 1 TRIỆU ĐỒNG), CHỈ ĐƯỢC PHÉP CHỌN MÓN TỪ DANH SÁCH CONTEXT, KHÔNG ĐƯỢC BỊA RA MÓN MỚI.
Nếu không có món phù hợp, hãy xin lỗi và gợi ý khách hỏi món khác.

CONTEXT - Thông tin món ăn liên quan:
{context}

PHÂN TÍCH CÂU HỎI:
- Loại câu hỏi: {intent['type']}
- Từ khóa chính: {', '.join(intent['keywords'])}
- Bộ lọc: {str(intent['filters']) if intent['filters'] else 'Không có'}
"""
        if context_message and context_message.strip():
            messages.append(SystemMessage(content=context_message))
        recent_history = self.conversation_history[-30:] if len(self.conversation_history) > 30 else self.conversation_history
        for msg in recent_history:
            if not msg.content or not msg.content.strip():
                continue
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            else:
                messages.append(AIMessage(content=msg.content))
        if user_message and user_message.strip():
            messages.append(HumanMessage(content=user_message))
        # Filter out any message with empty or whitespace-only content (extra safety)
        messages = [m for m in messages if hasattr(m, 'content') and m.content and m.content.strip()]
        return messages

    def _highlight_dish_names(self, text: str, context: str) -> str:
        # Lấy danh sách tên món trong context
        dish_names = []
        for line in context.split('\n'):
            m = re.match(r"\d+\. (.+)", line.strip())
            if m:
                dish_names.append(m.group(1).strip())
        # Sắp xếp tên món theo độ dài giảm dần để tránh lồng nhau
        dish_names = sorted(dish_names, key=len, reverse=True)
        for name in dish_names:
            # Regex: match tên món không phân biệt hoa thường, không nằm trong thẻ HTML (không highlight nếu đã có <span class="dish-name">)
            pattern = re.compile(rf'(?<![>])(?<!<span class="dish-name">)({re.escape(name)})(?![<])', re.IGNORECASE)
            text = pattern.sub(r'<span class="dish-name">\1</span>', text)
        return text

    def _process_llm_response(self, response: Any, intent: Dict[str, Any], context: str, user_message: str = "", user_id: str = "default", order_id: str = None) -> str:
        try:
            # Nếu intent là hỏi nguyên liệu, ưu tiên trả lời trực tiếp từ dữ liệu nếu có
            if intent['type'] == 'ingredient' and self.last_dish:
                dish = rag_system.dishes_lookup.get(self.last_dish, None)
                if dish and getattr(dish, 'ingredients', None):
                    reply = f"🛒 Nguyên liệu của món <span class=\"dish-name\">{dish.name}</span> gồm: {dish.ingredients}. Bạn muốn biết thêm về cách làm hoặc dinh dưỡng của món này không ạ?"
                    return clean_star_lines(insert_dish_images(reply))
            # Nếu intent là hỏi cách làm, ưu tiên trả lời trực tiếp từ dữ liệu nếu có
            if intent['type'] == 'recipe' and self.last_dish:
                dish = rag_system.dishes_lookup.get(self.last_dish, None)
                if dish and getattr(dish, 'recipe', None):
                    reply = f"👨‍🍳 Cách chế biến món <span class=\"dish-name\">{dish.name}</span>: {dish.recipe}. Bạn muốn biết thêm về nguyên liệu hoặc dinh dưỡng của món này không ạ?"
                    return clean_star_lines(insert_dish_images(reply))
            # Nếu intent là hỏi dinh dưỡng, ưu tiên trả lời trực tiếp từ dữ liệu nếu có
            if intent['type'] == 'nutrition' and self.last_dish:
                dish = rag_system.dishes_lookup.get(self.last_dish, None)
                if dish:
                    nutrition_fields = [
                        ('calories', 'calo'),
                        ('fat', 'chất béo'),
                        ('fiber', 'chất xơ'),
                        ('sugar', 'đường'),
                        ('protein', 'protein'),
                    ]
                    nutrition_info = []
                    for field, label in nutrition_fields:
                        value = getattr(dish, field, None)
                        if value and str(value).strip():
                            nutrition_info.append(f"{label}: {value}")
                    if nutrition_info:
                        reply = f"🍜 Hàm lượng dinh dưỡng của món <span class=\"dish-name\">{dish.name}</span> gồm: " + ", ".join(nutrition_info) + ". Bạn cần biết thêm gì về món này không ạ?"
                        return clean_star_lines(insert_dish_images(reply))
            # Nếu intent là recommendation, KHÔNG kiểm tra tên món trong output, luôn trả về gợi ý tự nhiên
            if hasattr(response, 'content'):
                content = response.content
            else:
                content = str(response)
            
            print(f"[DEBUG] Raw LLM response: {content}")
            content = text_processor.clean_text(content)
            print(f"[DEBUG] Cleaned content: {content}")
            # --- Filter: Nếu LLM trả về hóa đơn/tổng tiền, override bằng logic backend ---
            bill_keywords = ["tổng cộng", "hóa đơn", "order của bạn", "tổng tiền", "thanh toán", "bill"]
            if any(kw in content.lower() for kw in bill_keywords):
                # Lấy hóa đơn thật từ backend
                bill = order_manager.get_bill(user_id, order_id=order_id)
                if not bill['items']:
                    reply = "Bạn chưa có món nào trong hóa đơn. Hãy chọn món trước nhé!"
                else:
                    reply = f"🧾 Hóa đơn của bạn (Order ID: {bill['order_id']}):\n"
                    for idx, item in enumerate(bill['items'], 1):
                        note_str = f" (Ghi chú: {item['note']})" if item['note'] else ""
                        reply += f"{idx}. {item['dish']} x{item['quantity']}{note_str} - {item['unit_price']:,}đ = {item['amount']:,}đ\n"
                    reply += f"Tổng cộng: {bill['total']:,}đ\n"
                    reply += "Nếu bạn muốn thanh toán, chỉ cần chọn 'Chuyển khoản' hay 'Tiền mặt' hoặc muốn thêm món gì nữa cứ nói nhé?"
                return clean_star_lines(insert_dish_images(reply))
            parsed = parse_suggested_menu(content)
            if parsed:
                self.last_suggested_dishes = parsed
                print('[DEBUG] Đã lưu pending_menu:', parsed)
                # Loại bỏ mọi dấu * ở đầu dòng, giữa dòng, và bất kỳ vị trí nào
                import re as _re
                content = _re.sub(r'(^|[\r\n])\s*\*+\s*', r'\1', content)
                content = _re.sub(r'\*+\s*', '', content)
                # Chèn ảnh cho mọi tên món có trong dòng (không chỉ các món parse ra)
                lines = content.split('\n')
                dish_keys = list(rag_system.dishes_lookup.keys())
                norm_dish_keys = [normalize(k) for k in dish_keys]
                for idx, line in enumerate(lines):
                    line_norm = normalize(line)
                    found = False
                    for i, dish_key in enumerate(dish_keys):
                        dish_norm = norm_dish_keys[i]
                        # Nếu tên món xuất hiện trong dòng (normalize)
                        if dish_norm and dish_norm in line_norm:
                            dish_obj = rag_system.dishes_lookup[dish_key]
                            img_html = get_img_html(dish_key, dish_obj)
                            lines[idx] = line + img_html
                            print(f"[DEBUG][img_force_insert] {dish_key} -> {img_html}")
                            found = True
                            break
                    if not found:
                        # Fuzzy match nếu không tìm thấy tuyệt đối
                        for i, dish_key in enumerate(dish_keys):
                            dish_norm = norm_dish_keys[i]
                            import difflib
                            matches = difflib.get_close_matches(dish_norm, [line_norm], n=1, cutoff=0.6)
                            if matches:
                                dish_obj = rag_system.dishes_lookup[dish_key]
                                img_html = get_img_html(dish_key, dish_obj)
                                lines[idx] = line + img_html
                                print(f"[DEBUG][img_force_fuzzy] {dish_key} ~ {line.strip()} -> {img_html}")
                                break
                content = '\n'.join(lines)
            else:
                self.last_suggested_dishes = []
                print('[DEBUG] pending_menu rỗng sau khi parse.')
                # Không chèn ảnh cho toàn bộ dish_names nữa

            print("[DEBUG][final content]", content)
            # Tạo phiên bản sạch để đọc (không có emoji)
            clean_content_for_reading = text_processor.clean_text_for_reading(content)
            # Giữ nguyên content gốc để hiển thị UI - KHÔNG thêm emoji ở đây nữa
            print("[DEBUG][response to UI]", content)
            print("[DEBUG][clean content for reading]", clean_content_for_reading)
            
            # Trả về content gốc có đầy đủ thông tin
            final_content = clean_star_lines(insert_dish_images(content))
            return final_content
        except Exception as e:
            return clean_star_lines(insert_dish_images(f"Có lỗi khi xử lý phản hồi: {str(e)}"))

    def get_conversation_summary(self) -> Dict[str, Any]:
        return {
            'total_messages': len(self.conversation_history),
            'user_messages': len([msg for msg in self.conversation_history if msg.role == "user"]),
            'bot_messages': len([msg for msg in self.conversation_history if msg.role == "assistant"]),
            'recent_topics': self._extract_recent_topics()
        }

    def _extract_recent_topics(self) -> List[str]:
        topics = []
        recent_messages = self.conversation_history[-6:]
        for msg in recent_messages:
            if msg.role == "user":
                keywords = text_processor.extract_keywords(msg.content)
                topics.extend(keywords[:2])
        unique_topics = list(dict.fromkeys(topics))[:5]
        return unique_topics

    def clear_conversation(self):
        self.conversation_history.clear()

    def get_suggested_questions(self) -> List[str]:
        base_questions = [
            "Bạn có thể gợi ý món ăn phù hợp với thời tiết hôm nay không?",
            "Tôi muốn tìm món ăn đặc sản miền Bắc",
            "Có món chay nào ngon và dễ làm không?",
            "Gợi ý món ăn phù hợp cho bữa tối gia đình",
            "Món nào phù hợp khi tôi đang buồn?",
            "Cách làm phở bò truyền thống như thế nào?",
            "Nguyên liệu cần thiết để làm bánh chưng là gì?",
            "Món ăn nào có thể làm nhanh trong 30 phút?",
        ]
        recent_topics = self._extract_recent_topics()
        dynamic_questions = []
        for topic in recent_topics[:2]:
            dynamic_questions.append(f"Còn món nào khác liên quan đến {topic}?")
            dynamic_questions.append(f"Cách làm {topic} tại nhà như thế nào?")
        all_questions = base_questions + dynamic_questions
        return all_questions[:6]

    def get_chatbot_stats(self) -> Dict[str, Any]:
        return {
            'is_ready': self.is_ready,
            'conversation_stats': self.get_conversation_summary(),
            'rag_stats': rag_system.get_statistics(),
            'system_info': {
                'model': settings.CHAT_MODEL,
                'provider': settings.MODEL_PROVIDER
            }
        }

    def auto_confirm_pending_order(self, user_id):
        pending_items = getattr(self, 'last_suggested_dishes', [])
        if pending_items:
            added_dishes = []
            # Lấy danh sách tên món đã có trong bill hiện tại
            current_bill = order_manager.get_bill(user_id)
            current_dish_names = set()
            if current_bill and 'items' in current_bill:
                current_dish_names = set(item['dish'] for item in current_bill['items'])
            # Lọc ra các món trong pending menu chưa có trong bill
            to_add = []
            for item in pending_items:
                dish_name_norm = normalize(item['dish'])
                matched_dish = None
                for key in rag_system.dishes_lookup.keys():
                    if normalize(key) == dish_name_norm:
                        matched_dish = rag_system.dishes_lookup[key]
                        break
                if matched_dish and matched_dish.name not in current_dish_names:
                    to_add.append((item, matched_dish))
            if not to_add:
                reply = (
                    "Bạn đã chọn xong thực đơn, không còn món nào trong gợi ý cần thêm nữa! Bạn muốn xem hóa đơn hay cần hỗ trợ gì thêm không ạ?"
                )
            else:
                for item, matched_dish in to_add:
                    order_manager.add_dish(
                        user_id,
                        matched_dish,
                        quantity=item.get('quantity', 1)
                    )
                    img_html = f"<br><img src='{matched_dish.image}' alt='{matched_dish.name}' width='120'>" if getattr(matched_dish, 'image', None) else ""
                    added_dishes.append(f"{item['dish']} x{item.get('quantity', 1)}{img_html}")
                reply = (
                    "✅ Em đã chốt thực đơn cho mình gồm: "
                    + ", ".join(added_dishes)
                    + ".<br>Bạn muốn xem hóa đơn hay cần hỗ trợ gì thêm không ạ?, Nếu không hãy click vào nút ở dưới để nhà hàng làm món cho bạn nhé" + confirm_order_button
                )
            self.last_suggested_dishes = []  # Clear sau khi chốt hoặc xác nhận
        else:
            reply = (
                "Hiện tại chưa có thực đơn nào để chốt. "
                "Bạn muốn gợi ý lại thực đơn không ạ?"
            )
        self.conversation_history.append(
            ChatMessage(role="assistant", content=reply)
        )
        return clean_star_lines(insert_dish_images(reply))

    def notify_paid(self, user_id: str, order_id: str = None):
        """
        Gửi thông báo xác nhận chuyển khoản thành công vào hội thoại chatbot.
        """
        message = "\U0001F389 Nhà hàng đã xác nhận chuyển khoản thành công! Cảm ơn bạn."
        self.conversation_history.append(
            ChatMessage(role="assistant", content=message)
        )

    # Intent gọi nhân viên/phục vụ
    def handle_call_staff(self, user_id):
        try:
            # Gửi request đến API gọi nhân viên
            api_url = "http://localhost:5000/api/call_staff"
            payload = {"table_id": user_id}
            requests.post(api_url, json=payload, timeout=2)
            reply = "✅ Đã gửi yêu cầu gọi nhân viên! Nhân viên sẽ đến hỗ trợ bạn trong giây lát."
            self.conversation_history.append(
                ChatMessage(role="assistant", content=reply)
            )
            return clean_star_lines(reply)
        except Exception:
            reply = "Đã xảy ra lỗi khi gửi yêu cầu gọi nhân viên. Vui lòng thử lại hoặc báo trực tiếp với nhân viên."
            self.conversation_history.append(
                ChatMessage(role="assistant", content=reply)
            )
            return clean_star_lines(reply)

# Định nghĩa HTML nút xác nhận chốt món
confirm_order_button = (
    '<br><button onclick="if(window.chatSendMessage){window.chatSendMessage(\'Xác nhận chốt món cho nhà hàng\');}else{document.getElementById(\'chat-input\').value=\'Xác nhận chốt món cho nhà hàng\';document.getElementById(\'chat-send-btn\').click();}">Xác nhận chốt món cho nhà hàng</button>'
)

vietnamese_food_chatbot = VietnameseFoodChatbot()
