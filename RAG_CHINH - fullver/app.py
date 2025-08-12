from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from core.chatbot import vietnamese_food_chatbot
from utils.excel_loader import load_dishes_from_excel
from models.ai_models import ai_models
import os
from core.order_manager import order_manager
from core.rag_system import rag_system
from core.chatbot import normalize
from core.table_manager import table_manager
from datetime import datetime

app = Flask(__name__)

# Khởi tạo chatbot nếu chưa sẵn sàng
def ensure_chatbot_ready():
    if not ai_models.is_initialized():
        ai_models.initialize_models()
    if not vietnamese_food_chatbot.is_ready:
        data_path = os.path.join(os.path.dirname(__file__), 'data100mon.xlsx')
        dishes = load_dishes_from_excel(data_path)
        vietnamese_food_chatbot.initialize(dishes)
        # Debug: In ra toàn bộ tên món đã nạp vào hệ thống (cả gốc và normalize)
        print("==== Danh sách tên món đã nạp vào chatbot ====")
        for dish in rag_system.dishes_lookup.values():
            print(f"- [{normalize(dish.name)}] | [{dish.name}]")
        print("=============================================")

# --- Quản lý trạng thái món ăn (bật/tắt) ---
# Lưu trạng thái món vào biến toàn cục (có thể thay bằng DB nếu cần)
dish_status_map = {}  # name -> True (hiện) / False (tạm hết)

# --- Quản lý gọi nhân viên ---
staff_calls = []  # Mỗi phần tử: {'user_id': ..., 'table_id': ..., 'timestamp': ...}

@app.route('/')
def index():
    return render_template('menu.html')


@app.route('/mobile_menu')
def mobile_menu():
    # Ưu tiên kiểm tra token phiên bàn
    table_token = request.args.get('table_token')
    if table_token:
        # Tìm session theo token
        session = None
        table = None
        for s in table_manager.sessions.values():
            if s.session_token == table_token and s.status == 'active':
                session = s
                table = table_manager.get_table(s.table_id)
                break
        if not session or not table or table.status != 'occupied':
            return render_template('table_closed.html', table=table)
        # Token hợp lệ, cho vào menu
        return render_template('mobile_menu.html', table=table)
    # Nếu không có token, fallback về logic cũ (dành cho admin hoặc trường hợp đặc biệt)
    table_id = request.args.get('table_id')
    table_name = request.args.get('table_name')
    if table_name and not table_id:
        for t in table_manager.get_all_tables():
            if t.name.strip().lower() == table_name.strip().lower():
                table_id = t.id
                break
    if table_id:
        table = table_manager.get_table(table_id)
        if not table or table.status != 'occupied':
            return render_template('table_closed.html', table=table)
    else:
        return render_template('table_closed.html', table=None)
    return render_template('mobile_menu.html', table=table)

@app.route('/qr-scanner')
def qr_scanner():
    return render_template('qr_scanner.html')

@app.route('/api/dishes')
def api_dishes():
    ensure_chatbot_ready()
    dishes = []
    for dish in rag_system.dishes_lookup.values():
        # Đã tắt log debug tên món ở đây để tránh spam khi polling
        dishes.append({
            'name': dish.name,
            'price': getattr(dish, 'price', None),
            'description': getattr(dish, 'description', ''),
            'image': getattr(dish, 'image', None),
            'dish_type': getattr(dish, 'dish_type', ''),
            'meal_category': getattr(dish, 'meal_category', ''),
            'region': getattr(dish, 'region', ''),
            'texture': getattr(dish, 'texture', ''),
            'status': dish_status_map.get(dish.name, True)
        })
    return jsonify(dishes)

@app.route('/api/order', methods=['POST'])
def api_order():
    ensure_chatbot_ready()
    data = request.get_json()
    items = data.get('items', [])
    table_id = data.get('table_id') or request.args.get('table_id')
    user_id = table_id or request.remote_addr or 'default'
    added = []
    for item in items:
        name = item.get('name')
        quantity = int(item.get('quantity', 1))
        dish = rag_system.dishes_lookup.get(name)
        if dish:
            order_manager.add_dish(user_id, dish, quantity=quantity)
            added.append(name)
    if added:
        return jsonify({'success': True, 'added': added})
    return jsonify({'success': False, 'error': 'No valid dish'}), 400

@app.route('/api/cart', methods=['POST'])
def api_cart():
    ensure_chatbot_ready()
    data = request.get_json() or {}
    table_id = data.get('table_id') or request.args.get('table_id')
    user_id = table_id or request.remote_addr or 'default'
    orders = order_manager.get_all_bills(user_id)
    bills = []
    for order in orders:
        bill = order_manager.get_bill(user_id, order_id=order.order_id)
        if bill:
            bills.append(bill)
    return jsonify({'orders': bills})

@app.route('/api/cart/confirm', methods=['POST'])
def api_cart_confirm():
    ensure_chatbot_ready()
    data = request.get_json()
    table_id = data.get('table_id') or request.args.get('table_id')
    user_id = table_id or request.remote_addr or 'default'
    order_id = data.get('order_id')
    if not order_id:
        return jsonify({'success': False, 'error': 'Thiếu order_id'}), 400
    order_manager.update_bill_status(user_id, 'confirmed', order_id=order_id)
    return jsonify({'success': True})

@app.route('/api/cart/remove_item', methods=['POST'])
def api_cart_remove_item():
    ensure_chatbot_ready()
    data = request.get_json()
    table_id = data.get('table_id') or request.args.get('table_id')
    user_id = table_id or request.remote_addr or 'default'
    dish_name = data.get('dish_name')
    order_id = data.get('order_id')
    if not dish_name or not order_id:
        return jsonify({'success': False, 'error': 'Thiếu tên món hoặc order_id'}), 400
    order = None
    for o in order_manager.get_all_bills(user_id):
        if o.order_id == order_id:
            order = o
            break
    if order:
        order.remove_item(dish_name)
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Không tìm thấy hóa đơn'}), 404

@app.route('/api/cart/update_note', methods=['POST'])
def api_cart_update_note():
    ensure_chatbot_ready()
    data = request.get_json()
    table_id = data.get('table_id') or request.args.get('table_id')
    user_id = table_id or request.remote_addr or 'default'
    order_id = data.get('order_id')
    dish_name = data.get('dish_name')
    note = data.get('note', '')
    if not order_id or not dish_name:
        return jsonify({'success': False, 'error': 'Thiếu order_id hoặc dish_name'}), 400
    order = None
    for o in order_manager.get_all_bills(user_id):
        if o.order_id == order_id:
            order = o
            break
    if order:
        for item in order.items:
            if item.dish.name == dish_name:
                item.note = note
                return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Không tìm thấy hóa đơn hoặc món'}), 404

@app.route('/api/chat', methods=['POST'])
def chat_api():
    ensure_chatbot_ready()
    user_message = request.json.get('message', '')
    if not user_message.strip():
        return jsonify({'response': 'Vui lòng nhập nội dung câu hỏi.'})
    user_id = request.remote_addr or 'default'
    bot_response = vietnamese_food_chatbot.chat(user_message, user_id=user_id)
    
    # Làm sạch HTML tags để đọc text-to-speech
    def clean_html_for_reading(text):
        import re
        # Loại bỏ tất cả HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Loại bỏ các ký tự đặc biệt HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        text = text.replace('&#39;', "'")
        # Loại bỏ các dòng trống liên tiếp
        text = re.sub(r'\n\s*\n', '\n', text)
        # Loại bỏ khoảng trắng thừa
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    clean_response_for_reading = clean_html_for_reading(bot_response)
    
    return jsonify({
        'response': bot_response,
        'clean_response_for_reading': clean_response_for_reading
    })

@app.route('/chatbot-popup')
def chatbot_popup():
    return render_template('chat.html')

# --- Interface quản lý bill cho nhà hàng ---
@app.route('/admin/bills')
def admin_bills():
    # Lấy danh sách user_id từ order_manager.orders
    user_ids = list(order_manager.orders.keys())
    # Lấy tất cả hóa đơn cho từng user
    all_bills = []
    for user_id in user_ids:
        user_bills = order_manager.get_all_bills(user_id)
        for bill in user_bills:
            bill_dict = order_manager.get_bill(user_id, order_id=bill.order_id)
            all_bills.append(bill_dict)
    return render_template('admin_bills.html', bills=all_bills)

@app.route('/admin/bill/<user_id>/<order_id>')
def admin_bill_detail(user_id, order_id):
    bill = order_manager.get_bill(user_id, order_id=order_id)
    if not bill or not bill.get('items'):
        return render_template('admin_bill_detail.html', bill=None, user_id=user_id, order_id=order_id)
    return render_template('admin_bill_detail.html', bill=bill, user_id=user_id, order_id=order_id)

@app.route('/admin/bill/<user_id>/<order_id>/status', methods=['POST'])
def admin_bill_update_status(user_id, order_id):
    status = request.form.get('status')
    order_manager.update_bill_status(user_id, status, order_id=order_id)
    return redirect(url_for('admin_bill_detail', user_id=user_id, order_id=order_id))

@app.route('/admin/bill/<user_id>/<order_id>/remove_item', methods=['POST'])
def admin_remove_item(user_id, order_id):
    dish_name = request.form.get('dish_name')
    # Xóa món khỏi đúng hóa đơn
    bill = order_manager.get_bill(user_id, order_id=order_id)
    if bill:
        order = None
        for o in order_manager.get_all_bills(user_id):
            if o.order_id == order_id:
                order = o
                break
        if order:
            order.remove_item(dish_name)
    return redirect(url_for('admin_bill_detail', user_id=user_id, order_id=order_id))

@app.route('/admin/status')
def admin_status():
    ensure_chatbot_ready()
    # Lấy danh sách món ăn
    dishes = []
    for dish in rag_system.dishes_lookup.values():
        dishes.append({
            'name': dish.name,
            'price': getattr(dish, 'price', None),
            'description': getattr(dish, 'description', ''),
            'image': getattr(dish, 'image', None),
            'dish_type': getattr(dish, 'dish_type', ''),
            'meal_category': getattr(dish, 'meal_category', ''),
            'region': getattr(dish, 'region', ''),
            'texture': getattr(dish, 'texture', ''),
            'status': dish_status_map.get(dish.name, True)
        })
    return render_template('admin_status.html', dishes=dishes)

@app.route('/api/admin/dish_status', methods=['POST'])
def api_admin_dish_status():
    data = request.get_json()
    name = data.get('name')
    status = data.get('status')
    if name is None or status is None:
        return jsonify({'success': False, 'error': 'Thiếu tên món hoặc trạng thái'}), 400
    dish_status_map[name] = bool(status)
    return jsonify({'success': True})

@app.route('/api/admin/bills_status')
def api_admin_bills_status():
    # Lấy danh sách user_id từ order_manager.orders
    user_ids = list(order_manager.orders.keys())
    all_bills = []
    for user_id in user_ids:
        user_bills = order_manager.get_all_bills(user_id)
        for bill in user_bills:
            bill_dict = order_manager.get_bill(user_id, order_id=bill.order_id)
            if bill_dict:
                # Lấy danh sách món (tên, số lượng)
                items = bill_dict.get('items', [])
                dish_list = [{'dish': item['dish'], 'quantity': item['quantity']} for item in items]
                all_bills.append({
                    'order_id': bill_dict['order_id'],
                    'user_id': bill_dict['user_id'],
                    'created_at': str(bill_dict['created_at']),
                    'status': bill_dict.get('status', 'pending'),
                    'total': bill_dict.get('total', 0),
                    'dishes': dish_list
                })
    return jsonify({'bills': all_bills})

@app.route('/api/call_staff', methods=['POST'])
def api_call_staff():
    data = request.get_json() or {}
    table_id = data.get('table_id') or request.args.get('table_id')
    user_id = table_id or request.remote_addr or 'default'
    staff_calls.append({
        'user_id': user_id,
        'table_id': table_id,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
    return jsonify({'success': True, 'message': 'Đã gửi yêu cầu gọi nhân viên!'})

@app.route('/api/admin/staff_calls', methods=['GET', 'POST'])
def api_admin_staff_calls():
    global staff_calls
    if request.method == 'POST':
        # Reset danh sách gọi nhân viên (sau khi admin đã xem)
        staff_calls = []
        return jsonify({'success': True})
    # GET: trả về danh sách bàn vừa gọi nhân viên
    return jsonify({'calls': staff_calls})

# --- Quản lý bàn và QR code ---
@app.route('/admin/tables')
def admin_tables():
    """Trang quản lý bàn"""
    return render_template('admin_tables.html')

@app.route('/api/tables')
def api_tables():
    """API lấy danh sách tất cả bàn"""
    tables = table_manager.get_all_tables()
    table_list = []
    for table in tables:
        active_session = table_manager.get_active_session(table.id)
        table_list.append({
            'id': table.id,
            'name': table.name,
            'capacity': table.capacity,
            'status': table.status,
            'location': table.location,
            'qr_code': table.qr_code,
            'created_at': table.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'active_session': {
                'id': active_session.id,
                'start_time': active_session.start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'customer_count': active_session.customer_count,
                'session_token': active_session.session_token  # Thêm dòng này
            } if active_session else None
        })
    return jsonify({'tables': table_list})

@app.route('/api/tables', methods=['POST'])
def api_create_table():
    """API tạo bàn mới"""
    data = request.get_json()
    name = data.get('name')
    capacity = data.get('capacity')
    location = data.get('location')
    
    if not all([name, capacity, location]):
        return jsonify({'success': False, 'error': 'Thiếu thông tin bàn'}), 400
    
    try:
        table = table_manager.create_table(name, int(capacity), location)
        return jsonify({
            'success': True,
            'table': {
                'id': table.id,
                'name': table.name,
                'capacity': table.capacity,
                'status': table.status,
                'qr_code': table.qr_code
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tables/<table_id>/status', methods=['PUT'])
def api_update_table_status(table_id):
    """API cập nhật trạng thái bàn"""
    data = request.get_json()
    status = data.get('status')
    
    if not status:
        return jsonify({'success': False, 'error': 'Thiếu trạng thái'}), 400
    
    success = table_manager.update_table_status(table_id, status)
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Không tìm thấy bàn'}), 404

@app.route('/api/tables/<table_id>/session', methods=['POST'])
def api_start_table_session(table_id):
    """API bắt đầu phiên làm việc cho bàn"""
    data = request.get_json()
    customer_count = data.get('customer_count', 0)
    
    session = table_manager.start_table_session(table_id, customer_count)
    if session:
        return jsonify({
            'success': True,
            'session': {
                'id': session.id,
                'table_name': session.table_name,
                'start_time': session.start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'customer_count': session.customer_count
            }
        })
    else:
        return jsonify({'success': False, 'error': 'Không thể bắt đầu phiên làm việc'}), 400

@app.route('/api/tables/<table_id>/session', methods=['DELETE'])
def api_end_table_session(table_id):
    """API kết thúc phiên làm việc cho bàn"""
    success = table_manager.end_table_session(table_id)
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Không tìm thấy phiên làm việc'}), 404

@app.route('/api/tables/summary')
def api_tables_summary():
    """API lấy tổng quan về tất cả bàn"""
    summary = table_manager.get_table_summary()
    return jsonify(summary)

@app.route('/api/qr/scan', methods=['POST'])
def api_scan_qr():
    """API xử lý khi quét QR code"""
    data = request.get_json()
    qr_data = data.get('qr_data')
    
    if not qr_data:
        return jsonify({'success': False, 'error': 'Thiếu dữ liệu QR code'}), 400
    
    result = table_manager.scan_qr_code(qr_data)
    return jsonify(result)

@app.route('/table/<table_id>')
def table_menu(table_id):
    """Trang menu cho bàn cụ thể"""
    # Kiểm tra bàn có tồn tại không
    table = table_manager.get_table_by_id(table_id)
    if not table:
        return "Bàn không tồn tại", 404
    
    # Cập nhật trạng thái bàn thành occupied nếu chưa có session
    active_session = table_manager.get_active_session(table_id)
    if not active_session:
        # Tự động bắt đầu session khi khách truy cập
        table_manager.start_table_session(table_id, customer_count=0)
    
    return redirect(f'/mobile_menu?table_id={table_id}')

@app.route('/api/tables/<table_id>', methods=['DELETE'])
def api_delete_table(table_id):
    """API xóa bàn khỏi hệ thống"""
    success = table_manager.delete_table(table_id)
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Không tìm thấy bàn'}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)