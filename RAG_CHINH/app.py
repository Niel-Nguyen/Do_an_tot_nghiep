from flask import Flask, render_template, request, jsonify, redirect, url_for
from core.chatbot import vietnamese_food_chatbot
from utils.excel_loader import load_dishes_from_excel
from models.ai_models import ai_models
import os
from core.order_manager import order_manager

app = Flask(__name__)

# Khởi tạo chatbot nếu chưa sẵn sàng
def ensure_chatbot_ready():
    if not ai_models.is_initialized():
        ai_models.initialize_models()
    if not vietnamese_food_chatbot.is_ready:
        data_path = os.path.join(os.path.dirname(__file__), 'data100mon.xlsx')
        dishes = load_dishes_from_excel(data_path)
        vietnamese_food_chatbot.initialize(dishes)

@app.route('/')
def index():
    return render_template('chat.html')

@app.route('/api/chat', methods=['POST'])
def chat_api():
    ensure_chatbot_ready()
    user_message = request.json.get('message', '')
    if not user_message.strip():
        return jsonify({'response': 'Vui lòng nhập nội dung câu hỏi.'})
    bot_response = vietnamese_food_chatbot.chat(user_message)
    return jsonify({'response': bot_response})

# --- Interface quản lý bill cho nhà hàng ---
@app.route('/admin/bills')
def admin_bills():
    # Lấy danh sách user_id từ order_manager.orders
    user_ids = list(order_manager.orders.keys())
    bills = [order_manager.get_bill(user_id) for user_id in user_ids]
    return render_template('admin_bills.html', bills=bills)

@app.route('/admin/bill/<user_id>')
def admin_bill_detail(user_id):
    bill = order_manager.get_bill(user_id)
    if not bill or not bill.get('items'):
        return render_template('admin_bill_detail.html', bill=None, user_id=user_id)
    return render_template('admin_bill_detail.html', bill=bill)

@app.route('/admin/bill/<user_id>/status', methods=['POST'])
def admin_bill_update_status(user_id):
    status = request.form.get('status')
    order_manager.update_bill_status(user_id, status)
    return redirect(url_for('admin_bill_detail', user_id=user_id))

@app.route('/admin/bill/<user_id>/remove_item', methods=['POST'])
def admin_remove_item(user_id):
    dish_name = request.form.get('dish_name')
    order_manager.remove_dish(user_id, dish_name)
    return redirect(url_for('admin_bill_detail', user_id=user_id))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
