from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from core.chatbot import vietnamese_food_chatbot
from utils.excel_loader import load_dishes_from_excel
from models.ai_models import ai_models
import os
from core.order_manager import order_manager
from core.rag_system import rag_system
from core.chatbot import normalize
from datetime import datetime
from face_login import recognize_user, register_user
from chat_history_manager import save_chat_history, load_chat_history
from paid_dishes_manager import save_paid_dishes, load_paid_dishes
from paid_bills_manager import load_paid_bills, save_paid_bill
from paid_bill_histories_manager import save_paid_bill_history
import copy

app = Flask(__name__)
app.secret_key = "okevip"

def ensure_chatbot_ready():
    import asyncio
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())
    if not ai_models.is_initialized():
        ai_models.initialize_models()
    if not vietnamese_food_chatbot.is_ready:
        data_path = os.path.join(os.path.dirname(__file__), 'data100mon.xlsx')
        dishes = load_dishes_from_excel(data_path)
        vietnamese_food_chatbot.initialize(dishes)
        print("==== Danh sách tên món đã nạp vào chatbot ====")
        for dish in rag_system.dishes_lookup.values():
            print(f"- [{normalize(dish.name)}] | [{dish.name}]")
        print("=============================================")

dish_status_map = {}
staff_calls = []

@app.route('/')
def index():
    if 'user_name' not in session:
        return redirect(url_for('face_login_page'))
    return render_template('menu.html')

@app.route('/login')
def face_login_page():
    return render_template('login.html')

@app.route('/mobile_menu')
def mobile_menu():
    return render_template('mobile_menu.html')

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
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Dữ liệu không hợp lệ'}), 400
            
        items = data.get('items', [])
        if not items:
            return jsonify({'success': False, 'error': 'Chưa chọn món nào'}), 400

        table_id = data.get('table_id') or request.args.get('table_id')
        user_id = session.get('user_name') or request.remote_addr or 'default'
        added = []
        failed = []
            
        for item in items:
            name = item.get('name')
            if not name:
                continue
                
            try:
                quantity = int(item.get('quantity', 1))
            except (ValueError, TypeError):
                quantity = 1
                
            dish = rag_system.dishes_lookup.get(name)
            if dish:
                try:
                    order_manager.add_dish(user_id, dish, quantity=quantity)
                    added.append(name)
                except Exception as e:
                    print(f"Error adding dish {name}: {str(e)}")
                    failed.append(name)
                
        if added:
            message = f'Đã thêm {len(added)} món vào giỏ hàng'
            if failed:
                message += f' (Không thêm được {len(failed)} món)'
            return jsonify({
                'success': True, 
                'added': added,
                'failed': failed,
                'message': message
            })
        return jsonify({'success': False, 'error': 'Không có món hợp lệ để thêm'}), 400
        
    except Exception as e:
        print(f"Error in api_order: {str(e)}")
        return jsonify({'success': False, 'error': 'Có lỗi xảy ra khi xử lý đơn hàng'}), 500

@app.route('/api/cart', methods=['GET', 'POST'])
def api_cart():
    ensure_chatbot_ready()
    if request.method == 'POST':
        data = request.get_json() or {}
    else:
        data = {}
    table_id = data.get('table_id') or request.args.get('table_id')
    user_id = session.get('user_name') or request.remote_addr or 'default'
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
    user_id = session.get('user_name') or request.remote_addr or 'default'
    order_id = data.get('order_id')
    if not order_id:
        order = order_manager.get_pending_order(user_id)
        if not order:
            return jsonify({'success': False, 'error': 'Thiếu order_id'}), 400
        order_id = order.order_id
    order_manager.update_bill_status(user_id, 'confirmed', order_id=order_id)
    order = order_manager.get_bill(user_id, order_id=order_id)
    if order:
        save_paid_dishes(user_id, [
            item.dish.name if hasattr(item, 'dish') and hasattr(item.dish, 'name')
            else item['dish']['name'] if isinstance(item.get('dish'), dict) and 'name' in item['dish']
            else item['dish'] if isinstance(item.get('dish'), str)
            else None
            for item in order['items']
        ])
        order_dict = order if isinstance(order, dict) else copy.deepcopy(order.__dict__)
        save_paid_bill(user_id, order_dict)
    return jsonify({'success': True})

@app.route('/api/cart/remove_item', methods=['POST'])
def api_cart_remove_item():
    ensure_chatbot_ready()
    data = request.get_json()
    table_id = data.get('table_id') or request.args.get('table_id')
    user_id = session.get('user_name') or request.remote_addr or 'default'
    dish_name = data.get('dish_name')
    order_id = data.get('order_id')
    if not dish_name:
        return jsonify({'success': False, 'error': 'Thiếu tên món'}), 400
    if not order_id:
        order = order_manager.get_pending_order(user_id)
        if not order:
            return jsonify({'success': False, 'error': 'Không tìm thấy hóa đơn'}), 404
    else:
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
    user_id = session.get('user_name') or request.remote_addr or 'default'
    order_id = data.get('order_id')
    dish_name = data.get('dish_name')
    note = data.get('note', '')
    if not dish_name:
        return jsonify({'success': False, 'error': 'Thiếu dish_name'}), 400
    if not order_id:
        order = order_manager.get_pending_order(user_id)
        if not order:
            return jsonify({'success': False, 'error': 'Không tìm thấy hóa đơn'}), 404
    else:
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
    user_name = session.get('user_name') or request.remote_addr or 'default'

    history = load_chat_history(user_name)
    history.append({'role': 'user', 'content': user_message})

    try:
        bot_response = vietnamese_food_chatbot.chat(user_message, user_id=user_name, history=history)
    except TypeError:
        try:
            bot_response = vietnamese_food_chatbot.chat(user_message, user_id=user_name)
        except Exception as e:
            bot_response = "Xin lỗi, tôi đang gặp sự cố. Vui lòng thử lại sau!"

    history.append({'role': 'bot', 'content': bot_response})
    save_chat_history(user_name, history)

    return jsonify({'response': bot_response, 'history': history})

@app.route('/chatbot-popup')
def chatbot_popup():
    return render_template('chat.html')

@app.route('/admin/bills')
def admin_bills():
    user_ids = list(order_manager.orders.keys())
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
    
    if status == 'paid':
        bill = order_manager.get_bill(user_id, order_id=order_id)
        if bill:
            save_paid_bill_history(user_id, bill)
            
            dish_names = [
                item.get('dish', {}).get('name', '') if isinstance(item.get('dish'), dict)
                else item.get('dish', '')
                for item in bill.get('items', [])
            ]
            save_paid_dishes(user_id, dish_names)
            
    return redirect(url_for('admin_bill_detail', user_id=user_id, order_id=order_id))

@app.route('/admin/bill/<user_id>/<order_id>/remove_item', methods=['POST'])
def admin_remove_item(user_id, order_id):
    dish_name = request.form.get('dish_name')
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

@app.route('/face-register', methods=['POST'])
def face_register_route():
    data = request.get_json()
    name = data.get("name")
    image_b64 = data.get("image")

    register_user(name, image_b64)
    session['user_name'] = name
    return jsonify({"status": "registered", "name": name})

@app.route('/face-login', methods=['POST'])
def face_login_route():
    data = request.get_json()
    image_b64 = data.get("image")

    user = recognize_user(image_b64)
    if user:
        session['user_name'] = user
        return jsonify({"status": "success", "name": user})
    else:
        return jsonify({"status": "new_user"})

@app.route('/api/chat/history', methods=['GET', 'POST'])
def chat_history():
    user_name = session.get('user_name') or request.remote_addr or 'default'
    history = load_chat_history(user_name)
    return jsonify({'history': history})

@app.route('/api/admin/dish_status', methods=['POST'])
def api_admin_dish_status():
    data = request.get_json()
    name = data.get('name')
    status = data.get('status')
    if name is None or status is None:
        return jsonify({'success': False, 'error': 'Thiếu tên món hoặc trạng thái'}), 400
    dish_status_map[name] = bool(status)
    return jsonify({'success': True})

@app.route('/api/paid_dishes', methods=['GET'])
def api_paid_dishes():
    user_name = session.get('user_name') or request.remote_addr or 'default'
    used_dishes = load_paid_dishes(user_name)
    return jsonify({'paid_dishes': used_dishes})

@app.route('/api/paid_bills', methods=['GET'])
def api_paid_bills():
    user_name = session.get('user_name') or request.remote_addr or 'default'
    bills = load_paid_bills(user_name)
    return jsonify({'paid_bills': bills})

@app.route('/api/admin/bills_status')
def api_admin_bills_status():
    user_ids = list(order_manager.orders.keys())
    all_bills = []
    for user_id in user_ids:
        user_bills = order_manager.get_all_bills(user_id)
        for bill in user_bills:
            bill_dict = order_manager.get_bill(user_id, order_id=bill.order_id)
            if bill_dict:
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
    user_id = session.get('user_name') or request.remote_addr or 'default'
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
        staff_calls = []
        return jsonify({'success': True})
    return jsonify({'calls': staff_calls})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
