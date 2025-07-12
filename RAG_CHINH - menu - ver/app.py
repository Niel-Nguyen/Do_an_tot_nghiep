from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from core.chatbot import vietnamese_food_chatbot
from utils.excel_loader import load_dishes_from_excel
from models.ai_models import ai_models
import os
from core.order_manager import order_manager
from core.rag_system import rag_system

app = Flask(__name__)

# Khởi tạo chatbot nếu chưa sẵn sàng
def ensure_chatbot_ready():
    if not ai_models.is_initialized():
        ai_models.initialize_models()
    if not vietnamese_food_chatbot.is_ready:
        data_path = os.path.join(os.path.dirname(__file__), 'data100mon.xlsx')
        dishes = load_dishes_from_excel(data_path)
        vietnamese_food_chatbot.initialize(dishes)

# --- Quản lý trạng thái món ăn (bật/tắt) ---
# Lưu trạng thái món vào biến toàn cục (có thể thay bằng DB nếu cần)
dish_status_map = {}  # name -> True (hiện) / False (tạm hết)

@app.route('/')
def index():
    return render_template('menu.html')

@app.route('/api/dishes')
def api_dishes():
    ensure_chatbot_ready()
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
    return jsonify(dishes)

@app.route('/api/order', methods=['POST'])
def api_order():
    ensure_chatbot_ready()
    data = request.get_json()
    items = data.get('items', [])
    user_id = request.remote_addr or 'default'  # Đơn giản hóa, thực tế nên dùng session/user id
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

@app.route('/api/cart')
def api_cart():
    ensure_chatbot_ready()
    user_id = request.remote_addr or 'default'
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
    user_id = request.remote_addr or 'default'
    data = request.get_json()
    order_id = data.get('order_id')
    if not order_id:
        return jsonify({'success': False, 'error': 'Thiếu order_id'}), 400
    order_manager.update_bill_status(user_id, 'confirmed', order_id=order_id)
    return jsonify({'success': True})

@app.route('/api/cart/remove_item', methods=['POST'])
def api_cart_remove_item():
    ensure_chatbot_ready()
    user_id = request.remote_addr or 'default'
    data = request.get_json()
    dish_name = data.get('dish_name')
    order_id = data.get('order_id')
    if not dish_name or not order_id:
        return jsonify({'success': False, 'error': 'Thiếu tên món hoặc order_id'}), 400
    # Xóa món khỏi đúng hóa đơn
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
    user_id = request.remote_addr or 'default'
    data = request.get_json()
    order_id = data.get('order_id')
    dish_name = data.get('dish_name')
    note = data.get('note', '')
    if not order_id or not dish_name:
        return jsonify({'success': False, 'error': 'Thiếu order_id hoặc dish_name'}), 400
    # Cập nhật ghi chú cho đúng hóa đơn
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
    return jsonify({'response': bot_response})

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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
