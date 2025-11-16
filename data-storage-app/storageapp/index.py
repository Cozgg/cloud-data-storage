import os
import json
import hmac
import hashlib
import time
import uuid
import requests
from flask import render_template, request, redirect, url_for, flash, Blueprint
from flask_login import login_user, logout_user, current_user, login_required
from storageapp import app, dao, login, controllers

login.login_view = 'user_login'
login.login_message = 'Vui lòng đăng nhập để xem trang này!'
login.login_message_category = 'info'


@login.user_loader
def load_user(user_id):
    return dao.get_user_by_id(user_id)


@app.route("/")
def homepage():
    if current_user.is_authenticated:
        if current_user.role == 'ADMIN':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('user_dashboard'))
    return render_template("homepage.html")



@app.route("/logout")
@login_required
def user_logout():
    logout_user()
    return redirect(url_for('user_login'))


@app.route("/login", methods=["get", "post"])
def user_login():
    if current_user.is_authenticated:
        return redirect(url_for('homepage'))

    err_msg = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user_dict = dao.auth_user(username, password)

        if user_dict:
            user_obj = dao.get_user_by_id(user_dict['id'])
            login_user(user_obj)

            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('homepage'))
        else:
            err_msg = "Tài khoản hoặc mật khẩu không đúng!"

    return render_template("login.html", err_msg=err_msg)


@app.route("/register", methods=["get", "post"])
def user_register():
    if current_user.is_authenticated:
        return redirect(url_for('homepage'))

    err_msg = None
    if request.method == "POST":
        name = request.form.get("name")
        username = request.form.get("username")
        password = request.form.get("password")
        confirm = request.form.get("confirm_password")

        if password != confirm:
            err_msg = "Mật khẩu xác nhận không khớp!"
        else:
            err_msg = "Chức năng đăng ký đang được bảo trì."
            # (Logic tạo user...)

    return render_template("register.html", err_msg=err_msg)




@app.route("/dashboard")
@login_required
def user_dashboard():
    if current_user.role != 'USER':
        return redirect(url_for('admin_dashboard'))

    q = request.args.get("q")
    files = dao.get_files_for_user(user_id=current_user.id, q=q)

    # Lấy thông tin Quota
    usage_mb = dao.get_user_storage_usage(current_user.id)
    limit_gb = dao.get_user_quota_limit(current_user.id) / 1024
    usage_gb = usage_mb / 1024
    quota_percent = (usage_mb / (limit_gb * 1024)) * 100

    return render_template("index.html",
                           files=files,
                           usage_gb=usage_gb,
                           limit_gb=limit_gb,
                           quota_percent=quota_percent)


@app.route("/billing")
@login_required
def billing():
    if current_user.role != 'USER':
        return redirect(url_for('admin_dashboard'))

    # Lấy thông tin Quota
    usage_mb = dao.get_user_storage_usage(current_user.id)
    limit_gb = dao.get_user_quota_limit(current_user.id) / 1024
    usage_gb = usage_mb / 1024
    quota_percent = (usage_mb / (limit_gb * 1024)) * 100

    return render_template("billing.html",
                           usage_gb=usage_gb,
                           limit_gb=limit_gb,
                           quota_percent=quota_percent)



@app.route("/admin")
@login_required
def admin_dashboard():
    if current_user.role != 'ADMIN':
        return redirect(url_for('user_dashboard'))

    all_users = dao.get_all_users()
    all_files = dao.get_all_files()

    # MỚI: Tính toán thống kê
    total_users = len(all_users)
    total_files_count = len(all_files)
    total_storage_mb = sum(f.get('size_mb', 0) for f in all_files)
    total_storage_gb = total_storage_mb / 1024

    return render_template("admin/admin_dashboard.html",
                           all_users=all_users,
                           all_files=all_files,
                           total_users=total_users,
                           total_files_count=total_files_count,
                           total_storage_gb=total_storage_gb)


@app.route("/admin/users")
@login_required
def admin_users():
    """Trang quản lý User cho Admin"""
    if current_user.role != 'ADMIN':
        return redirect(url_for('user_dashboard'))

    q = request.args.get("q")
    users = dao.get_all_users()

    if q:
        q_lower = q.lower()
        users = [u for u in users if q_lower in u['name'].lower() or q_lower in u['username'].lower()]

    return render_template("admin/all_users.html", users=users)


@app.route('/upload', methods=['POST'])
@login_required
def api_upload_file():
    if 'file' not in request.files:
        flash('Không có tệp nào được chọn.', 'danger')
        return redirect(url_for('user_dashboard'))

    file = request.files['file']
    if file.filename == '':
        flash('Không có tệp nào được chọn.', 'danger')
        return redirect(url_for('user_dashboard'))

    file.seek(0, os.SEEK_END)
    file_size_bytes = file.tell()
    file_size_mb = file_size_bytes / (1024 * 1024)
    file.seek(0)

    usage_mb = dao.get_user_storage_usage(current_user.id)
    limit_mb = dao.get_user_quota_limit(current_user.id)

    if (usage_mb + file_size_mb) > limit_mb:
        flash(f'Upload thất bại! Đã vượt quá quota. (Đã dùng: {usage_mb / 1024:.1f}/{limit_mb / 1024:.0f}GB)', 'danger')
        return redirect(url_for('user_dashboard'))

    object_name = f"user_{current_user.id}/{file.filename}"

    try:

        success, _ = controllers.upload_file_to_minio(object_name, file.stream, file_size_bytes)

        if success:

            dao.add_file_record(current_user.id, object_name, file_size_mb)
            flash('Tải tệp lên thành công!', 'success')
        else:
            flash('Có lỗi xảy ra khi tải tệp lên MinIO.', 'danger')

    except Exception as e:
        flash(f'Lỗi hệ thống: {e}', 'danger')

    return redirect(url_for('user_dashboard'))


@app.route('/download-url/<path:object_name>', methods=['GET'])
@login_required
def api_get_download_url(object_name):
    url = controllers.get_presigned_download_url(object_name)
    if url:
        return redirect(url)
    return "Không tìm thấy file hoặc có lỗi", 404


# --- 6. TÍCH HỢP THANH TOÁN MOMO ---

@app.route('/billing/create_payment')
@login_required
def create_payment():
    # (Đây là code placeholder - bạn PHẢI thay key thật)
    partner_code = "YOUR_PARTNER_CODE"
    access_key = "YOUR_ACCESS_KEY"
    secret_key = "YOUR_SECRET_KEY"
    order_id = str(uuid.uuid4())
    order_info = "Nâng cấp gói Pro 100GB"
    amount = "50000"
    base_url = "http://127.0.0.1:5000"  # (Khi test local. Dùng NGROK nếu public)
    redirect_url = f"{base_url}{url_for('payment_return')}"
    notify_url = f"{base_url}{url_for('momo_ipn')}"
    request_type = "captureWallet"
    request_id = str(uuid.uuid4())
    extra_data = ""

    raw_signature = (
        f"partnerCode={partner_code}"
        f"&accessKey={access_key}"
        f"&requestId={request_id}"
        f"&amount={amount}"
        f"&orderId={order_id}"
        f"&orderInfo={order_info}"
        f"&returnUrl={redirect_url}"
        f"&notifyUrl={notify_url}"
        f"&extraData={extra_data}"
    )

    signature = hmac.new(secret_key.encode('utf-8'), raw_signature.encode('utf-8'), hashlib.sha256).hexdigest()

    url = "https://test-payment.momo.vn/v2/gateway/api/create"
    payload = {
        'partnerCode': partner_code, 'accessKey': access_key, 'requestId': request_id,
        'amount': amount, 'orderId': order_id, 'orderInfo': order_info,
        'returnUrl': redirect_url, 'notifyUrl': notify_url, 'extraData': extra_data,
        'requestType': request_type, 'signature': signature, 'lang': 'vi'
    }

    try:
        response = requests.post(url, data=json.dumps(payload), headers={'Content-Type': 'application/json'})
        response_data = response.json()

        if response_data.get('resultCode') == 0:
            return redirect(response_data.get('payUrl'))
        else:
            flash(f"Lỗi MoMo: {response_data.get('message')}", 'danger')
            return redirect(url_for('billing'))
    except Exception as e:
        flash(f"Lỗi kết nối: {e}", 'danger')
        return redirect(url_for('billing'))


@app.route('/billing/return')
@login_required
def payment_return():
    result_code = request.args.get('resultCode')
    if result_code == '0':
        flash('Thanh toán thành công! Gói của bạn đã được nâng cấp.', 'success')
    else:
        flash('Thanh toán thất bại hoặc bị hủy.', 'danger')
    return redirect(url_for('user_dashboard'))


@app.route('/momo_ipn', methods=['POST'])
def momo_ipn():

    return '', 204


if __name__ == "__main__":
    app.run(debug=True)