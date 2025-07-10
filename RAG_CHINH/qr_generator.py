from flask import Flask, render_template_string, request

app = Flask(__name__)

# ========================
# CONFIG BANK INFO - BIDV
# ========================
BANK_ID = "bidv"
ACCOUNT_NUMBER = "5811471677"
ACCOUNT_NAME = "NGUYEN NGOC PHUC"

# ========================
# Tạo VietQR URL
# ========================
def generate_vietqr_url(total_amount, order_id):
    message = f"Thanh toan don {order_id}"
    encoded_name = ACCOUNT_NAME.replace(" ", "%20")
    return (
        f"https://img.vietqr.io/image/{BANK_ID}-{ACCOUNT_NUMBER}-qr_only.png"
        f"?amount={total_amount}&addInfo={message}&accountName={encoded_name}"
    )

# ========================
# HTML Template
# ========================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>Thanh Toán Đơn Hàng</title>
</head>
<body style="font-family: Arial, sans-serif; text-align: center; padding-top: 50px;">
    <h2>🧾 Thanh Toán Đơn Hàng: {{ order_id }}</h2>
    <p>Tổng tiền: <strong>{{ total_amount }} VNĐ</strong></p>
    <img src="{{ qr_url }}" alt="QR Thanh Toán" width="300">
    <p>📱 Vui lòng mở ứng dụng ngân hàng, quét mã để thanh toán.</p>
</body>
</html>
"""

# ========================
# Route chính (/) render QR luôn
# ========================
@app.route("/")
def show_qr():
    # Lấy từ URL hoặc dùng mặc định
    order_id = request.args.get("order_id", "DEMO123")
    total_amount = request.args.get("amount", "150000")

    qr_url = generate_vietqr_url(total_amount, order_id)

    return render_template_string(
        HTML_TEMPLATE,
        order_id=order_id,
        total_amount=total_amount,
        qr_url=qr_url
    )

# ========================
# Chạy server Flask
# ========================
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
