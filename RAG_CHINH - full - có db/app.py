from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from core.chatbot import vietnamese_food_chatbot
from utils.excel_loader import load_dishes_from_excel
from models.ai_models import ai_models
import os
from core.order_manager import order_manager
from core.rag_system import rag_system
from core.chatbot import normalize
# from core.revenue_manager import revenue_manager  # Tạm comment, sẽ cập nhật API sau
from core.revenue_manager import revenue_manager
from core.database_manager import db_manager
from datetime import datetime
import time
import threading
import hashlib
from functools import wraps
import sqlite3

# Initialize table_manager with database support
from core.table_manager import TableManager
table_manager = TableManager(db_manager)

app = Flask(__name__)
app.secret_key = 'restaurant_management_secret_key_2024'  # Thay đổi trong production

# Admin credentials - trong thực tế nên lưu trong database với mã hóa
ADMIN_CREDENTIALS = {
    'admin': 'admin123'
}

# Global variables for realtime tracking
last_data_change = time.time()
change_events = []  # Store recent changes
realtime_clients = set()  # Track connected clients

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or not session['logged_in']:
            if request.is_json:
                return jsonify({'error': 'Authentication required', 'redirect': '/admin/login'}), 401
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def trigger_realtime_update(event_type, data):
    """Trigger realtime update for all connected clients"""
    global last_data_change
    last_data_change = time.time()
    
    event = {
        'type': event_type,
        'timestamp': last_data_change,
        'data': data
    }
    change_events.append(event)
    
    # Keep only last 50 events
    if len(change_events) > 50:
        change_events.pop(0)

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

# Store dish_status_map in app context for sharing with other modules
app.dish_status_map = dish_status_map

# --- Quản lý gọi nhân viên ---
staff_calls = []  # Mỗi phần tử: {'user_id': ..., 'table_id': ..., 'timestamp': ...}

@app.route('/')
def index():
    return redirect(url_for('admin_login'))


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
        # Token hợp lệ, cho vào menu với thông tin table_id và table_token
        return render_template('mobile_menu.html', table=table, table_id=table.id, table_token=table_token)
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
    return render_template('mobile_menu.html', table=table, table_id=table_id)

@app.route('/table_closed')
def table_closed():
    """Trang hiển thị khi bàn đã được đóng"""
    return render_template('table_closed.html', table=None)

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
    print(f"[DEBUG] api_order: table_id={table_id}, user_id={user_id}, remote_addr={request.remote_addr}")
    added = []
    for item in items:
        name = item.get('name')
        quantity = int(item.get('quantity', 1))
        dish = rag_system.dishes_lookup.get(name)
        if dish:
            order_manager.add_dish(user_id, dish, quantity=quantity)
            added.append(name)
    if added:
        # Trigger realtime update
        trigger_realtime_update('new_order', {
            'user_id': user_id,
            'table_id': table_id,
            'items': added,
            'message': f'Đơn hàng mới: {", ".join(added)}'
        })
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
        # Only include orders that have items
        if order.items and len(order.items) > 0:
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
        
        # Kiểm tra nếu hóa đơn không còn món nào thì xóa hóa đơn
        if len(order.items) == 0:
            print(f"Order {order_id} is empty, removing it completely")
            # Xóa order khỏi danh sách
            if hasattr(order_manager, 'orders') and user_id in order_manager.orders:
                order_manager.orders[user_id] = [o for o in order_manager.orders[user_id] if o.order_id != order_id]
                # Nếu user không còn order nào, xóa luôn user khỏi dict
                if len(order_manager.orders[user_id]) == 0:
                    del order_manager.orders[user_id]
        
        return jsonify({'success': True, 'order_deleted': len(order.items) == 0})
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

@app.route('/api/clear_cart', methods=['POST'])
def api_clear_cart():
    """Clear all cart data for a table when session ends"""
    ensure_chatbot_ready()
    data = request.get_json() or {}
    table_id = data.get('table_id') or request.args.get('table_id')
    if not table_id:
        return jsonify({'success': False, 'error': 'Thiếu table_id'}), 400
    
    user_id = table_id
    
    # Clear all orders for this table completely
    try:
        # Get reference to the order manager's storage (it's 'orders', not 'bills')
        if hasattr(order_manager, 'orders') and user_id in order_manager.orders:
            # Remove all orders for this user completely
            order_count = len(order_manager.orders[user_id])
            del order_manager.orders[user_id]
            print(f"Completely removed {order_count} orders for table {table_id}")
            return jsonify({
                'success': True, 
                'message': f'Completely cleared {order_count} orders for table {table_id}',
                'table_id': table_id
            })
        else:
            # No orders found for this user
            print(f"No orders found for table {table_id}")
            return jsonify({
                'success': True, 
                'message': f'No orders to clear for table {table_id}',
                'table_id': table_id
            })
        
    except Exception as e:
        print(f"Error clearing cart for table {table_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat_api():
    ensure_chatbot_ready()
    user_message = request.json.get('message', '')
    if not user_message.strip():
        return jsonify({'response': 'Vui lòng nhập nội dung câu hỏi.'})
    
    # Sử dụng cùng logic với /api/order để xác định user_id
    table_id = request.json.get('table_id') or request.args.get('table_id')
    user_id = table_id or request.remote_addr or 'default'
    print(f"[DEBUG] chat_api: table_id={table_id}, user_id={user_id}, remote_addr={request.remote_addr}")
    print(f"[DEBUG] chat_api: user_message={user_message}")
    print(f"[DEBUG] chat_api: current dish_status_map in app.py = {dish_status_map}")
    
    bot_response = vietnamese_food_chatbot.chat(user_message, user_id=user_id)
    print(f"[DEBUG] chat_api: bot_response={bot_response[:100]}...")
    
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
    table_id = request.args.get('table_id')
    return render_template('chat.html', table_id=table_id)

# --- Interface quản lý bill cho nhà hàng ---
@app.route('/admin/bills')
@login_required
def admin_bills():
    """Trang quản lý hóa đơn - chỉ hiển thị đơn chưa thanh toán"""
    try:
        # Lấy dữ liệu trực tiếp từ database SQLite để đảm bảo tính chính xác
        import sqlite3
        with sqlite3.connect('restaurant.db') as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Lấy tất cả đơn hàng chưa thanh toán (status != 'paid')
            cursor.execute('''
                SELECT o.*, t.name as table_name
                FROM orders o
                LEFT JOIN tables t ON o.table_id = t.id
                WHERE o.status != 'paid'
                ORDER BY o.created_at DESC
            ''')
            
            active_orders = []
            for row in cursor.fetchall():
                order = dict(row)
                
                # Lấy items cho đơn hàng
                cursor.execute('SELECT * FROM order_items WHERE order_id = ?', (order['id'],))
                items = [dict(item_row) for item_row in cursor.fetchall()]
                
                # Format order để tương thích với template
                bill = {
                    'order_id': order['id'],
                    'user_id': order['user_id'],
                    'table_id': order['table_id'],
                    'table_name': order['table_name'],
                    'total_amount': order['total_amount'],
                    'status': order['status'],
                    'created_at': order['created_at'],
                    'payment_time': order['payment_time'],
                    'items': items
                }
                active_orders.append(bill)
            
            # Đếm số đơn hàng đã thanh toán
            cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'paid'")
            paid_count = cursor.fetchone()[0]
            
            return render_template('admin_bills.html', 
                                 bills=active_orders, 
                                 active_count=len(active_orders), 
                                 paid_count=paid_count)
    
    except Exception as e:
        print(f"Error loading bills from database: {e}")
        # Fallback to old method if database fails
        user_ids = list(order_manager.orders.keys())
        all_bills = []
        paid_count = 0
        
        for user_id in user_ids:
            user_bills = order_manager.get_all_bills(user_id)
            for bill in user_bills:
                bill_dict = order_manager.get_bill(user_id, order_id=bill.order_id)
                if bill_dict:
                    if bill_dict.get('status') == 'paid':
                        paid_count += 1
                    else:
                        all_bills.append(bill_dict)
        
        return render_template('admin_bills.html', bills=all_bills, active_count=len(all_bills), paid_count=paid_count)

@app.route('/admin/bill/<user_id>/<order_id>')
@login_required
def admin_bill_detail(user_id, order_id):
    bill = order_manager.get_bill(user_id, order_id=order_id)
    if not bill or not bill.get('items'):
        return render_template('admin_bill_detail.html', bill=None, user_id=user_id, order_id=order_id)
    return render_template('admin_bill_detail.html', bill=bill, user_id=user_id, order_id=order_id)

@app.route('/admin/bill/<user_id>/<order_id>/status', methods=['POST'])
def admin_bill_update_status(user_id, order_id):
    old_bill = order_manager.get_bill(user_id, order_id=order_id)
    old_status = old_bill.get('status') if old_bill else None
    
    status = request.form.get('status')
    order_manager.update_bill_status(user_id, status, order_id=order_id)
    
    # Nếu trạng thái chuyển thành "paid", chỉ lưu vào database SQLite
    if status == 'paid' and old_status != 'paid':
        updated_bill = order_manager.get_bill(user_id, order_id=order_id)
        if updated_bill:
            try:
                # Chỉ lưu vào database SQLite, bỏ revenue_manager (JSON)
                bill_data = updated_bill.copy()
                bill_data['user_id'] = user_id
                bill_data['order_id'] = order_id
                bill_data['total_amount'] = bill_data.get('total', 0)
                bill_data['status'] = status
                
                # Tìm table thực tế từ table_manager nếu có
                table = table_manager.find_table_by_user_context(user_id)
                if table:
                    bill_data['table_id'] = table.id
                else:
                    bill_data['table_id'] = user_id
                
                # Lưu vào database SQLite
                db_manager.save_order(bill_data)
                # Cập nhật trạng thái với payment_time để trigger revenue summary update
                payment_time = datetime.now()
                db_manager.update_order_status(order_id, status, payment_time)
                print(f"Đã lưu đơn hàng vào database SQLite: {order_id} - {bill_data.get('total', 0)} VND")
                
                # XÓA đơn hàng khỏi memory để nó không hiển thị trong admin/bills nữa
                try:
                    if user_id in order_manager.orders:
                        # Tìm và xóa bill khỏi danh sách
                        user_bills = order_manager.orders[user_id]
                        order_manager.orders[user_id] = [bill for bill in user_bills if bill.order_id != order_id]
                        
                        # Nếu user không còn bill nào, xóa user_id khỏi orders
                        if not order_manager.orders[user_id]:
                            del order_manager.orders[user_id]
                        
                        print(f"Đã xóa đơn hàng {order_id} khỏi memory")
                except Exception as e:
                    print(f"Lỗi khi xóa đơn hàng khỏi memory: {e}")
                
            except Exception as e:
                print(f"Lỗi khi lưu vào database: {e}")
    else:
        # Chỉ cập nhật trạng thái trong database
        try:
            updated_bill = order_manager.get_bill(user_id, order_id=order_id)
            if updated_bill:
                bill_data = updated_bill.copy()
                bill_data['order_id'] = order_id
                bill_data['user_id'] = user_id
                bill_data['total_amount'] = bill_data.get('total', 0)
                bill_data['status'] = status
                
                table = table_manager.find_table_by_user_context(user_id)
                if table:
                    bill_data['table_id'] = table.id
                
                db_manager.save_order(bill_data)
                db_manager.update_order_status(order_id, status)
                
        except Exception as e:
            print(f"Lỗi khi cập nhật database: {e}")
    
    trigger_realtime_update('bill_status_updated', {
        'user_id': user_id,
        'order_id': order_id,
        'status': status,
        'timestamp': time.time()
    })
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
@login_required
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
@login_required
def api_admin_dish_status():
    data = request.get_json()
    name = data.get('name')
    status = data.get('status')
    if name is None or status is None:
        return jsonify({'success': False, 'error': 'Thiếu tên món hoặc trạng thái'}), 400
    dish_status_map[name] = bool(status)
    # Also update Flask app context
    app.dish_status_map[name] = bool(status)
    print(f"[DEBUG] Updated dish_status_map in app.py: {name} = {bool(status)}")
    print(f"[DEBUG] Full dish_status_map: {dish_status_map}")
    print(f"[DEBUG] Full app.dish_status_map: {app.dish_status_map}")
    return jsonify({'success': True})

@app.route('/api/admin/bills_status')
@login_required
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
    
    # Thêm thống kê theo status
    bills_by_status = {}
    for bill in all_bills:
        status = bill.get('status', 'pending')
        bills_by_status[status] = bills_by_status.get(status, 0) + 1
    
    return jsonify({
        'bills': all_bills,
        'bills_by_status': bills_by_status,
        'total_bills': len(all_bills)
    })

@app.route('/api/admin/bill_detail/<user_id>/<order_id>')
@login_required
def api_admin_bill_detail(user_id, order_id):
    """API lấy chi tiết đơn hàng cụ thể từ database"""
    try:
        # Thử lấy từ database SQLite trước
        order_from_db = db_manager.get_order_by_id(order_id)
        
        if order_from_db and order_from_db['items']:
            # Format lại dữ liệu từ database
            formatted_bill = {
                'order_id': order_from_db['id'],
                'user_id': order_from_db['user_id'],
                'table_id': order_from_db.get('table_name') or order_from_db.get('table_id', user_id),
                'created_at': order_from_db['created_at'],
                'status': order_from_db['status'],
                'total_amount': order_from_db['total_amount'],
                'payment_time': order_from_db.get('payment_time') or order_from_db['created_at'],
                'items': []
            }
            
            # Format lại items từ database
            for item in order_from_db['items']:
                formatted_bill['items'].append({
                    'name': item['dish_name'],
                    'quantity': item['quantity'],
                    'price': item['unit_price'],
                    'total': item['total_price']
                })
            
            return jsonify(formatted_bill)
        
        # Fallback: lấy từ order_manager
        bill_dict = order_manager.get_bill(user_id, order_id=order_id)
        if not bill_dict:
            return jsonify({'error': 'Không tìm thấy đơn hàng'}), 404
        
        # Format lại dữ liệu từ order_manager
        formatted_bill = {
            'order_id': bill_dict['order_id'],
            'user_id': bill_dict['user_id'],
            'table_id': bill_dict.get('table_name', user_id),
            'created_at': bill_dict['created_at'],
            'status': bill_dict.get('status', 'pending'),
            'total_amount': bill_dict.get('total', 0),
            'payment_time': bill_dict['created_at'],  # Sử dụng created_at làm payment_time
            'items': []
        }
        
        # Format lại items từ order_manager
        for item in bill_dict.get('items', []):
            formatted_bill['items'].append({
                'name': item.get('dish', ''),
                'quantity': item.get('quantity', 1),
                'price': item.get('unit_price', 0),
                'total': item.get('amount', 0)
            })
        
        return jsonify(formatted_bill)
        
    except Exception as e:
        print(f"Error getting bill detail: {e}")
        return jsonify({'error': 'Có lỗi xảy ra khi lấy chi tiết đơn hàng'}), 500

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
@login_required
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
        trigger_realtime_update('table_status_updated', {
            'table_id': table_id,
            'status': status,
            'timestamp': time.time()
        })
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
        # Trigger realtime update
        trigger_realtime_update('table_session_start', {
            'table_id': table_id,
            'table_name': session.table_name,
            'customer_count': customer_count,
            'message': f'Bắt đầu phiên cho {session.table_name}'
        })
        return jsonify({
            'success': True,
            'session': {
                'id': session.id,
                'table_name': session.table_name,
                'start_time': session.start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'customer_count': session.customer_count,
                'token': session.session_token  # Thêm token vào response
            },
            'token': session.session_token  # Thêm token ở level cao cho dễ access
        })
    else:
        return jsonify({'success': False, 'error': 'Không thể bắt đầu phiên làm việc'}), 400

@app.route('/api/tables/<table_id>/session', methods=['DELETE'])
def api_end_table_session(table_id):
    """API kết thúc phiên làm việc cho bàn"""
    success = table_manager.end_table_session(table_id)
    if success:
        # Cập nhật database để đánh dấu bàn đã đóng
        try:
            with sqlite3.connect('restaurant.db') as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE tables 
                    SET is_closed = 1, token = NULL, updated_at = ?
                    WHERE id = ?
                ''', (datetime.now().isoformat(), table_id))
                conn.commit()
        except Exception as e:
            print(f"Error updating table status in database: {e}")
        
        trigger_realtime_update('table_session_ended', {
            'table_id': table_id,
            'timestamp': time.time()
        })
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Không tìm thấy phiên làm việc'}), 404

@app.route('/api/tables/summary')
def api_tables_summary():
    """API lấy tổng quan về tất cả bàn"""
    summary = table_manager.get_table_summary()
    
    # Thêm thống kê bills từ order_manager
    user_ids = list(order_manager.orders.keys())
    total_bills_count = 0
    for user_id in user_ids:
        user_bills = order_manager.get_all_bills(user_id)
        total_bills_count += len(user_bills)
    
    summary["total_bills"] = total_bills_count
    
    return jsonify(summary)

@app.route('/api/realtime/status')
@login_required
def api_realtime_status():
    """API check realtime status and recent changes"""
    client_last_update = float(request.args.get('last_update', 0))
    
    # Get recent events since client's last update
    recent_events = [
        event for event in change_events 
        if event['timestamp'] > client_last_update
    ]
    
    # Get current stats
    summary = table_manager.get_table_summary()
    user_ids = list(order_manager.orders.keys())
    total_bills_count = 0
    pending_bills_count = 0
    
    for user_id in user_ids:
        user_bills = order_manager.get_all_bills(user_id)
        total_bills_count += len(user_bills)
        for bill in user_bills:
            if bill.status in ['pending', 'confirmed']:
                pending_bills_count += 1
    
    summary["total_bills"] = total_bills_count
    summary["pending_bills"] = pending_bills_count
    
    return jsonify({
        'last_change': last_data_change,
        'has_changes': len(recent_events) > 0,
        'events': recent_events,
        'current_stats': summary
    })

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

# --- Revenue Management Routes ---
@app.route('/admin/revenue')
@login_required
def admin_revenue():
    """Trang thống kê doanh thu - yêu cầu đăng nhập"""
    return render_template('doanh_thu.html')

@app.route('/debug/revenue')
@login_required
def debug_revenue():
    """Debug route để kiểm tra dữ liệu revenue"""
    try:
        # Kiểm tra database SQLite
        with sqlite3.connect('restaurant.db') as conn:
            cursor = conn.cursor()
            
            # Kiểm tra orders
            cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'paid'")
            paid_orders_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT SUM(total_amount) FROM orders WHERE status = 'paid'")
            paid_orders_total = cursor.fetchone()[0] or 0
            
            # Kiểm tra revenue_summary
            cursor.execute("SELECT COUNT(*) FROM revenue_summary")
            revenue_summary_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT SUM(total_revenue) FROM revenue_summary")
            revenue_summary_total = cursor.fetchone()[0] or 0
            
            # Lấy 5 orders gần nhất
            cursor.execute('''
                SELECT id, user_id, table_id, total_amount, status, payment_time, created_at 
                FROM orders 
                ORDER BY created_at DESC 
                LIMIT 5
            ''')
            recent_orders = cursor.fetchall()
            
            # Lấy revenue summary
            cursor.execute('SELECT * FROM revenue_summary ORDER BY date DESC LIMIT 5')
            recent_revenue = cursor.fetchall()
            
        debug_info = {
            'paid_orders_count': paid_orders_count,
            'paid_orders_total': paid_orders_total,
            'revenue_summary_count': revenue_summary_count,
            'revenue_summary_total': revenue_summary_total,
            'recent_orders': recent_orders,
            'recent_revenue': recent_revenue,
            'db_summary_stats': db_manager.get_revenue_summary_stats()
        }
        
        return jsonify(debug_info)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/revenue/summary')
@login_required  
def api_revenue_summary():
    """API lấy tổng quan doanh thu từ database SQLite"""
    try:
        # Chỉ lấy từ database SQLite
        with sqlite3.connect('restaurant.db') as conn:
            cursor = conn.cursor()
            
            today = datetime.now().date()
            
            # Doanh thu hôm nay
            cursor.execute("SELECT SUM(total_amount), COUNT(*) FROM orders WHERE status = 'paid' AND DATE(payment_time) = ?", (str(today),))
            today_data = cursor.fetchone() or (0, 0)
            
            # Doanh thu tháng này
            month = today.strftime('%Y-%m')
            cursor.execute("SELECT SUM(total_amount), COUNT(*) FROM orders WHERE status = 'paid' AND DATE(payment_time) LIKE ?", (f"{month}%",))
            month_data = cursor.fetchone() or (0, 0)
            
            # Tổng doanh thu
            cursor.execute("SELECT SUM(total_amount), COUNT(*) FROM orders WHERE status = 'paid'")
            total_data = cursor.fetchone() or (0, 0)
            
            summary = {
                'today_revenue': today_data[0] or 0,
                'today_orders': today_data[1] or 0,
                'month_revenue': month_data[0] or 0,
                'month_orders': month_data[1] or 0,
                'total_revenue': total_data[0] or 0,
                'total_orders': total_data[1] or 0
            }
        
        return jsonify(summary)
        
    except Exception as e:
        print(f"Error getting revenue summary from database: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/revenue/daily')
@login_required
def api_revenue_daily():
    """API lấy doanh thu theo ngày từ database SQLite"""
    try:
        target_date = request.args.get('date')
        if not target_date:
            return jsonify({'error': 'Missing date parameter'}), 400
        
        # Lấy trực tiếp từ database SQLite
        with sqlite3.connect('restaurant.db') as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Lấy tổng doanh thu ngày
            cursor.execute("SELECT SUM(total_amount), COUNT(*) FROM orders WHERE status = 'paid' AND DATE(payment_time) = ?", (target_date,))
            day_summary = cursor.fetchone() or (0, 0)
            
            # Lấy chi tiết các đơn hàng
            cursor.execute('''
                SELECT o.id, o.user_id, o.table_id, o.total_amount, o.created_at, o.payment_time,
                       GROUP_CONCAT(oi.dish_name || '|' || oi.quantity || '|' || oi.unit_price || '|' || oi.total_price, ';') as items_data
                FROM orders o
                LEFT JOIN order_items oi ON o.id = oi.order_id
                WHERE o.status = 'paid' AND DATE(o.payment_time) = ?
                GROUP BY o.id
                ORDER BY o.payment_time DESC
            ''', (target_date,))
            
            orders = []
            for row in cursor.fetchall():
                order = dict(row)
                
                # Parse items data
                items = []
                if order['items_data']:
                    for item_str in order['items_data'].split(';'):
                        parts = item_str.split('|')
                        if len(parts) >= 4:
                            items.append({
                                'name': parts[0],
                                'quantity': int(parts[1]),
                                'price': float(parts[2]),
                                'total': float(parts[3])
                            })
                
                orders.append({
                    'order_id': order['id'],
                    'user_id': order['user_id'],
                    'table_id': order['table_id'],
                    'total_amount': order['total_amount'],
                    'payment_time': order['payment_time'] or order['created_at'],
                    'items': items
                })
            
            revenue_data = {
                'date': target_date,
                'total_revenue': day_summary[0] or 0,
                'orders_count': day_summary[1] or 0,
                'orders': orders
            }
        
        return jsonify(revenue_data)
        
    except Exception as e:
        print(f"Error getting daily revenue: {e}")
        return jsonify({'error': str(e)}), 500
        
        # Nếu không có dữ liệu trong database, fallback sang revenue_manager
        if revenue_data['orders_count'] == 0:
            try:
                fallback_data = revenue_manager.get_daily_revenue(target_date)
                if fallback_data.get('orders_count', 0) > 0:
                    revenue_data = fallback_data
            except Exception as e:
                print(f"Error getting fallback revenue data: {e}")
        
        return jsonify(revenue_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/revenue/monthly')
@login_required
def api_revenue_monthly():
    """API lấy doanh thu theo tháng từ database SQLite"""
    try:
        year = int(request.args.get('year'))
        month = int(request.args.get('month'))
        
        # Lấy từ database SQLite
        with sqlite3.connect('restaurant.db') as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Format tháng (YYYY-MM)
            month_str = f"{year}-{month:02d}"
            
            # Lấy tổng doanh thu tháng
            cursor.execute("SELECT SUM(total_amount), COUNT(*) FROM orders WHERE status = 'paid' AND strftime('%Y-%m', payment_time) = ?", (month_str,))
            month_summary = cursor.fetchone() or (0, 0)
            
            # Lấy chi tiết theo ngày trong tháng
            cursor.execute('''
                SELECT DATE(payment_time) as date, SUM(total_amount) as revenue, COUNT(*) as orders_count
                FROM orders 
                WHERE status = 'paid' AND strftime('%Y-%m', payment_time) = ?
                GROUP BY DATE(payment_time)
                ORDER BY date
            ''', (month_str,))
            
            daily_data = [dict(row) for row in cursor.fetchall()]
            
            revenue_data = {
                'year': year,
                'month': month,
                'total_revenue': month_summary[0] or 0,
                'orders_count': month_summary[1] or 0,
                'daily_data': daily_data
            }
        
        return jsonify(revenue_data)
        
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid year or month parameter'}), 400
    except Exception as e:
        print(f"Error getting monthly revenue: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/revenue/range')
@login_required
def api_revenue_range():
    """API lấy doanh thu theo khoảng thời gian"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date or not end_date:
            return jsonify({'error': 'Missing start_date or end_date parameter'}), 400
        
        revenue_data = revenue_manager.get_date_range_revenue(start_date, end_date)
        return jsonify(revenue_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/revenue/debug')
@login_required
def api_revenue_debug():
    """API debug để kiểm tra doanh thu đã lưu"""
    try:
        # Lấy tất cả doanh thu
        all_revenue = revenue_manager.get_all_revenue()
        
        # Thống kê tổng quan
        total_revenue = sum(item['amount'] for item in all_revenue)
        total_records = len(all_revenue)
        
        return jsonify({
            'total_revenue': total_revenue,
            'total_records': total_records,
            'latest_records': all_revenue[-10:] if all_revenue else [],  # 10 bản ghi mới nhất
            'all_records': all_revenue  # Tất cả bản ghi để debug
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- Authentication Routes ---
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Trang đăng nhập admin"""
    if request.method == 'GET':
        # Nếu đã đăng nhập, chuyển hướng đến dashboard
        if 'logged_in' in session and session['logged_in']:
            return redirect(url_for('manager_admin'))
        return render_template('admin_login.html')
    
    # POST request - xử lý đăng nhập
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        remember_me = data.get('remember_me', False)
        
        # Kiểm tra thông tin đăng nhập
        if username in ADMIN_CREDENTIALS and ADMIN_CREDENTIALS[username] == password:
            # Đăng nhập thành công
            session['logged_in'] = True
            session['username'] = username
            session['login_time'] = datetime.now().isoformat()
            
            # Nếu chọn ghi nhớ, session sẽ tồn tại lâu hơn
            if remember_me:
                session.permanent = True
                app.permanent_session_lifetime = 30 * 24 * 60 * 60  # 30 days
            
            return jsonify({
                'success': True,
                'message': 'Đăng nhập thành công',
                'redirect': '/admin/dashboard'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Tên đăng nhập hoặc mật khẩu không đúng'
            }), 401
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Có lỗi xảy ra trong quá trình đăng nhập'
        }), 500

@app.route('/admin/logout')
def admin_logout():
    """Đăng xuất admin"""
    session.clear()
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@login_required
def manager_admin():
    """Trang dashboard quản trị - yêu cầu đăng nhập"""
    return render_template('manager_admin.html', username=session.get('username'))

# --- Order History APIs ---
@app.route('/api/orders/history')
@login_required
def api_orders_history():
    """API lấy lịch sử đơn hàng đã thanh toán với filter"""
    try:
        filter_type = request.args.get('filter_type', 'all')
        
        with sqlite3.connect('restaurant.db') as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Base query
            base_query = '''
                SELECT o.id, o.table_id, o.total_amount, o.payment_time, t.name as table_name
                FROM orders o
                LEFT JOIN tables t ON o.table_id = t.id
                WHERE o.status = 'paid' AND o.payment_time IS NOT NULL
            '''
            
            params = []
            
            # Thêm filter theo loại
            if filter_type == 'date':
                target_date = request.args.get('date')
                if target_date:
                    base_query += ' AND DATE(o.payment_time) = ?'
                    params.append(target_date)
            
            elif filter_type == 'month':
                target_month = request.args.get('month')
                if target_month:
                    # target_month format: YYYY-MM
                    base_query += ' AND strftime("%Y-%m", o.payment_time) = ?'
                    params.append(target_month)
            
            elif filter_type == 'range':
                from_date = request.args.get('from_date')
                to_date = request.args.get('to_date')
                if from_date and to_date:
                    base_query += ' AND DATE(o.payment_time) BETWEEN ? AND ?'
                    params.extend([from_date, to_date])
            
            # Sắp xếp và giới hạn
            base_query += ' ORDER BY o.payment_time DESC'
            
            if filter_type == 'all':
                base_query += ' LIMIT 100'  # Giới hạn 100 bản ghi cho "tất cả"
            
            cursor.execute(base_query, params)
            
            orders = []
            for row in cursor.fetchall():
                orders.append({
                    'id': row['id'],
                    'table_id': row['table_id'],
                    'table_name': row['table_name'],
                    'total_amount': row['total_amount'],
                    'payment_time': row['payment_time']
                })
            
            return jsonify(orders)
            
    except Exception as e:
        print(f"Error getting order history: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/orders/<order_id>/detail')
@login_required
def api_order_detail(order_id):
    """API lấy chi tiết đơn hàng"""
    try:
        with sqlite3.connect('restaurant.db') as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Lấy thông tin đơn hàng
            cursor.execute('''
                SELECT o.*, t.name as table_name
                FROM orders o
                LEFT JOIN tables t ON o.table_id = t.id
                WHERE o.id = ?
            ''', (order_id,))
            
            order_row = cursor.fetchone()
            if not order_row:
                return jsonify({'error': 'Đơn hàng không tồn tại'}), 404
            
            order = dict(order_row)
            
            # Lấy chi tiết các món trong đơn hàng
            cursor.execute('''
                SELECT dish_name, quantity, unit_price, total_price
                FROM order_items
                WHERE order_id = ?
                ORDER BY dish_name
            ''', (order_id,))
            
            items = []
            for item_row in cursor.fetchall():
                items.append({
                    'dish_name': item_row['dish_name'],
                    'quantity': item_row['quantity'],
                    'unit_price': item_row['unit_price'],
                    'total_price': item_row['total_price']
                })
            
            order['items'] = items
            
            return jsonify(order)
            
    except Exception as e:
        print(f"Error getting order detail: {e}")
        return jsonify({'error': str(e)}), 500

# --- Table Status API ---
@app.route('/api/table/status/<table_token>')
def api_table_status(table_token):
    """API kiểm tra trạng thái bàn theo token"""
    try:
        print(f"Checking status for token: {table_token[:8]}...")
        
        # Kiểm tra trong memory trước
        table_info = table_manager.get_table_by_token(table_token)
        print(f"Memory check result: {table_info}")
        
        if table_info:
            return jsonify({
                'table_id': table_info['table_id'],
                'is_closed': table_info.get('is_closed', False),
                'status': table_info.get('status', 'active'),
                'token_valid': True
            })
        
        # Nếu không tìm thấy trong memory, kiểm tra database
        with sqlite3.connect('restaurant.db') as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, status, is_closed 
                FROM tables 
                WHERE token = ? AND token IS NOT NULL
            ''', (table_token,))
            
            table_row = cursor.fetchone()
            print(f"Database check result: {dict(table_row) if table_row else None}")
            
            if table_row:
                return jsonify({
                    'table_id': table_row['id'],
                    'is_closed': bool(table_row['is_closed']),
                    'status': table_row['status'],
                    'token_valid': True
                })
            else:
                print(f"Token {table_token[:8]} not found - returning closed status")
                return jsonify({
                    'token_valid': False,
                    'is_closed': True,
                    'status': 'closed'
                }), 404
                
    except Exception as e:
        print(f"Error checking table status: {e}")
        return jsonify({
            'error': str(e),
            'token_valid': False,
            'is_closed': True,
            'status': 'error'
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)