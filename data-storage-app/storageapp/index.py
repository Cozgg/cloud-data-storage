import os
import json
import hmac
import hashlib
import time
import uuid
import requests
from flask import render_template, request, redirect, url_for, flash, Blueprint, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from storageapp import app, dao, login, controllers, db
from storageapp.models import User, UserRole, Transaction
from storageapp.test_helpers import delete_file_from_minio, DEFAULT_BUCKET

login.login_view = 'user_login'
login.login_message = 'Vui lòng đăng nhập để xem trang này!'
login.login_message_category = 'info'


@login.user_loader
def load_user(user_id):
    user = dao.get_user_by_id(user_id)
    if user and user.is_locked:
        return None
    return user


@app.route("/")
def homepage():
    if current_user.is_authenticated:
        if current_user.role == UserRole.ADMIN:
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
            if user_dict.is_locked:  # THÊM KIỂM TRA KHÓA
                err_msg = "Tài khoản này đã bị khóa."
            else:
                login_user(user=user_dict)
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                if user_dict.role == UserRole.ADMIN:
                    return redirect(url_for('admin_dashboard'))
                else:
                    return redirect(url_for('user_dashboard'))
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
            try:
                dao.add_user(name, username, password)
                flash("Đăng ký thành công! Vui lòng đăng nhập.", "success")
                return redirect(url_for('user_login'))
            except Exception as e:
                err_msg = f"Lỗi: {str(e)}"

    return render_template("register.html", err_msg=err_msg)


@app.route("/dashboard")
@app.route("/dashboard/<int:folder_id>")
@login_required
def user_dashboard(folder_id=None):
    if current_user.role != UserRole.USER:
        return redirect(url_for('admin_dashboard'))

    q = request.args.get("q")

    current_folder = None
    breadcrumbs = []
    if folder_id:
        current_folder = dao.get_folder_by_id(folder_id)
        if not current_folder or current_folder.user_id != current_user.id:
            flash("Thư mục không tồn tại hoặc bạn không có quyền truy cập", "danger")
            return redirect(url_for('user_dashboard'))

        breadcrumbs = dao.get_folder_breadcrumbs(folder_id)

    folders, files = dao.get_content_by_folder(current_user.id, folder_id, q)

    # Quota
    usage_mb = dao.get_user_storage_usage(current_user.id)
    limit_mb = dao.get_user_quota_limit(current_user.id)
    usage_gb = usage_mb / 1024
    limit_gb = limit_mb / 1024
    quota_percent = (usage_mb / limit_mb) * 100 if limit_mb > 0 else 0

    return render_template("index.html",
                           folders=folders,
                           files=files,
                           current_folder=current_folder,
                           breadcrumbs=breadcrumbs,
                           usage_gb=usage_gb,
                           limit_gb=limit_gb,
                           quota_percent=quota_percent)


@app.route('/create-folder', methods=['POST'])
@login_required
def create_new_folder():
    name = request.form.get('folder_name')
    parent_id = request.form.get('parent_id')

    if not name:
        flash('Tên thư mục không được để trống', 'warning')
    else:
        p_id = int(parent_id) if parent_id and parent_id != 'None' and parent_id != '' else None
        try:
            dao.create_folder(current_user.id, name, p_id)
            flash('Đã tạo thư mục mới', 'success')
        except Exception as e:
            flash(f'Lỗi tạo thư mục: {e}', 'danger')

    return redirect_back(parent_id)


# @app.route('/api/get-upload-url', methods=['POST'])
# @login_required
# def get_upload_url():
#     # Chỉnh sửa để chấp nhận đường dẫn tương đối (folder upload) hoặc tên file
#     path_or_filename = request.json.get('path_or_filename')
#     # file_type không còn cần thiết
#
#     if not path_or_filename:
#         return jsonify({"error": "Thiếu tên file hoặc đường dẫn"}), 400
#
#     # object_name sẽ là full path trên MinIO, ví dụ: user_1/MyFolder/file.txt
#     object_name = f"user_{current_user.id}/{path_or_filename}"
#
#     try:
#         presigned_url = controllers.get_presigned_upload_url(object_name)
#
#         if presigned_url:
#             return jsonify({
#                 "url": presigned_url,
#                 "object_name": object_name
#             })
#         else:
#             return jsonify({"error": "Lỗi kết nối MinIO"}), 500
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500



@app.route('/api/get-upload-url', methods=['POST'])
@login_required
def get_upload_url():
    filename = request.json.get('filename')
    file_type = request.json.get('file_type')

    if not filename:
        return jsonify({"error": "Thiếu tên file"}), 400

    object_name = f"user_{current_user.id}/{filename}"

    try:

        presigned_url = controllers.get_presigned_upload_url(object_name)

        if presigned_url:
            return jsonify({
                "url": presigned_url,
                "object_name": object_name
            })
        else:
            return jsonify({"error": "Lỗi kết nối MinIO"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/complete-upload', methods=['POST'])
@login_required
def complete_upload():
    data = request.json
    object_name = data.get('object_name')
    size_bytes = data.get('size_bytes')
    folder_id_str = data.get('folder_id')

    folder_id = int(folder_id_str) if folder_id_str and folder_id_str != 'None' and folder_id_str != '' else None

    file_size_mb = size_bytes / (1024 * 1024)

    usage_mb = dao.get_user_storage_usage(current_user.id)
    limit_mb = dao.get_user_quota_limit(current_user.id)

    if (usage_mb + file_size_mb) > limit_mb:
        delete_file_from_minio(DEFAULT_BUCKET, object_name)
        return jsonify({"error": "Hết dung lượng lưu trữ!"}), 403

    try:
        dao.add_file_record(current_user.id, object_name, file_size_mb, folder_id)
        flash('Tải tệp lên thành công!', 'success')
        return jsonify({"message": "Saved"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def redirect_back(folder_id):
    if folder_id and str(folder_id) != 'None':
        return redirect(url_for('user_dashboard', folder_id=folder_id))
    return redirect(url_for('user_dashboard'))


@app.route('/download-url/<path:object_name>', methods=['GET'])
@login_required
def api_get_download_url(object_name):
    url = controllers.get_presigned_download_url(object_name)
    if url:
        return redirect(url)
    return "Không tìm thấy file hoặc có lỗi", 404


@app.route('/delete-file/<path:object_name>', methods=['POST'])
@login_required
def api_delete_file(object_name):
    user_files = dao.get_files_for_user(current_user.id)
    owned_object_names = [f.object_name for f in user_files]

    if object_name not in owned_object_names:
        flash('Bạn không có quyền xóa file này!', 'danger')
        return redirect(url_for('user_dashboard'))

    try:
        delete_minio_success = delete_file_from_minio(DEFAULT_BUCKET, object_name)

        dao.delete_file_record(object_name)
        flash('Đã xóa file thành công!', 'success')

    except Exception as e:
        flash(f'Lỗi hệ thống khi xóa file: {e}', 'danger')

    return redirect(url_for('user_dashboard'))


@app.route("/billing")
@login_required
def billing():
    if current_user.role != UserRole.USER:
        return redirect(url_for('admin_dashboard'))

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
    if current_user.role != UserRole.ADMIN:
        return redirect(url_for('user_dashboard'))

    all_users = dao.get_all_users()
    all_files = dao.get_all_files()

    total_users = len(all_users)
    total_files_count = len(all_files)
    total_storage_mb = sum(f.size_mb for f in all_files)
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
    if current_user.role != UserRole.ADMIN:
        return redirect(url_for('user_dashboard'))

    q = request.args.get("q")
    users = dao.get_all_users()

    if q:
        q_lower = q.lower()
        users = [u for u in users if q_lower in u.name.lower() or q_lower in u.username.lower()]

    return render_template("admin/all_users.html", users=users)


@app.route('/admin/create-user', methods=['POST'])
@login_required
def admin_create_user():
    if current_user.role != UserRole.ADMIN:
        flash('Bạn không có quyền truy cập trang này!', 'danger')
        return redirect(url_for('user_dashboard'))

    name = request.form.get("name")
    username = request.form.get("username")
    password = request.form.get("password")
    role_str = request.form.get("role")
    storage_limit_gb = request.form.get("storage_limit_gb")

    if not name or not username or not password or not role_str or not storage_limit_gb:
        flash("Vui lòng điền đầy đủ thông tin.", "danger")
        return redirect(url_for('admin_users'))

    try:
        storage_limit_gb = int(storage_limit_gb)
        if storage_limit_gb < 0:
            raise ValueError("Dung lượng phải là số dương.")

        existing_user = dao.get_user_by_username(username)
        if existing_user:
            flash("Tên tài khoản đã tồn tại.", "danger")
            return redirect(url_for('admin_users'))

        role = UserRole.ADMIN if role_str == 'ADMIN' else UserRole.USER

        dao.add_user_full(name, username, password, role, storage_limit_gb)

        flash(f"Đã tạo tài khoản '{username}' thành công.", "success")
    except ValueError as e:
        flash(f"Lỗi nhập liệu: {e}", "danger")
    except Exception as e:
        flash(f"Lỗi hệ thống khi tạo người dùng: {e}", "danger")

    return redirect(url_for('admin_users', q=request.args.get('q')))


@app.route('/admin/update-user/<int:user_id>', methods=['POST'])
@login_required
def update_user_info(user_id):
    if current_user.role != UserRole.ADMIN:
        flash('Bạn không có quyền truy cập trang này!', 'danger')
        return redirect(url_for('user_dashboard'))

    user_to_update = dao.get_user_by_id(user_id)
    if not user_to_update:
        flash("Không tìm thấy người dùng.", "danger")
        return redirect(url_for('admin_users'))

    if user_to_update.role == UserRole.ADMIN and user_to_update.id != current_user.id:
        flash("Không thể chỉnh sửa thông tin của Quản trị viên khác.", "danger")
        return redirect(url_for('admin_users'))

    name = request.form.get("name")
    new_limit_gb = request.form.get("storage_limit_gb")

    if not name or not new_limit_gb:
        flash("Tên và Dung lượng không được để trống.", "danger")
        return redirect(url_for('admin_users'))

    try:
        new_limit_gb = int(new_limit_gb)
        if new_limit_gb < 0:
            raise ValueError("Dung lượng phải là số dương.")

        dao.update_user(user_to_update.id, name, new_limit_gb)

        flash(f"Đã cập nhật thông tin người dùng '{user_to_update.username}' thành công.", "success")
    except ValueError as e:
        flash(f"Lỗi nhập liệu: {e}", "danger")
    except Exception as e:
        flash(f"Lỗi hệ thống khi cập nhật người dùng: {e}", "danger")

    return redirect(url_for('admin_users', q=request.args.get('q')))


@app.route('/admin/delete-user/<int:user_id>', methods=['POST'])
@login_required
def api_delete_user(user_id):
    if current_user.role != UserRole.ADMIN:
        flash('Bạn không có quyền truy cập trang này!', 'danger')
        return redirect(url_for('user_dashboard'))

    user_to_delete = dao.get_user_by_id(user_id)

    if not user_to_delete:
        flash("Không tìm thấy người dùng.", "danger")
        return redirect(url_for('admin_users'))

    if user_to_delete.role == UserRole.ADMIN:
        flash("Không thể xóa tài khoản Quản trị viên.", "danger")
        return redirect(url_for('admin_users'))

    if user_to_delete.id == current_user.id:
        flash("Không thể tự xóa tài khoản của mình.", "danger")
        return redirect(url_for('admin_users'))

    try:
        user_files = dao.get_files_for_user(user_to_delete.id)
        minio_delete_success = True
        for f in user_files:
            if not delete_file_from_minio(DEFAULT_BUCKET, f.object_name):
                minio_delete_success = False

        dao.delete_user_and_content(user_to_delete.id)

        flash(f"Đã xóa tài khoản '{user_to_delete.username}' và toàn bộ dữ liệu thành công.", "success")
        if not minio_delete_success:
            flash("Cảnh báo: Một số tệp tin MinIO có thể không được xóa do lỗi kết nối.", "warning")

    except Exception as e:
        flash(f"Lỗi hệ thống khi xóa người dùng: {e}", "danger")

    return redirect(url_for('admin_users', q=request.args.get('q')))



@app.route('/admin/toggle-user-lock/<int:user_id>', methods=['POST'])
@login_required
def toggle_user_lock(user_id):
    if current_user.role != UserRole.ADMIN:
        return redirect(url_for('user_dashboard'))

    user_to_toggle = dao.get_user_by_id(user_id)

    if user_to_toggle and user_to_toggle.id != current_user.id and user_to_toggle.role != UserRole.ADMIN:
        try:
            user_to_toggle.is_locked = not user_to_toggle.is_locked
            db.session.commit()

            status = "khóa" if user_to_toggle.is_locked else "mở khóa"
            flash(f"Đã {status} tài khoản '{user_to_toggle.username}' thành công.", "success")

        except Exception as e:
            flash(f"Lỗi khi thực hiện hành động: {e}", "danger")
    elif user_to_toggle and user_to_toggle.role == UserRole.ADMIN:
         flash("Không thể khóa tài khoản của Quản trị viên.", "danger")
    elif user_to_toggle and user_to_toggle.id == current_user.id:
         flash("Không thể tự khóa tài khoản của mình.", "danger")
    else:
        flash("Không tìm thấy người dùng.", "danger")

    return redirect(url_for('admin_users', q=request.args.get('q'))) # Giữ nguyên query tìm kiếm


@app.route('/billing/create_payment')
@login_required
def create_payment():
    # 1. Lấy thông tin gói cước từ URL (?pkg=pro hoặc ?pkg=vip)
    package_type = request.args.get('pkg', 'pro')  # Mặc định là pro nếu không có

    # 2. Thiết lập giá tiền dựa trên gói
    if package_type == 'vip':
        amount = "1000000"  # 1 Triệu
        order_info = f"Mua goi VIP PRO (1TB) cho {current_user.username}"
    else:
        amount = "50000"  # 50 Ngàn
        order_info = f"Nang cap goi Pro (100GB) cho {current_user.username}"
    # 1. Chuẩn bị dữ liệu đơn hàng
    order_id = str(uuid.uuid4())
    request_id = str(uuid.uuid4())

    # 2. Lưu đơn hàng vào Database (PENDING)
    try:
        new_trans = Transaction(name=f"Giao dich cua {current_user.name}",order_id=order_id, amount=float(amount), order_info=order_info, status='PENDING',
                                user_id=current_user.id)
        db.session.add(new_trans)
        db.session.commit()
    except Exception as e:
        print(e)
        return redirect(url_for('billing'))

    # 3. Tạo chữ ký (Signature) theo công thức của MoMo
    raw_signature = (f"accessKey={app.config['MOMO_ACCESS_KEY']}&amount={amount}&extraData=&ipnUrl={app.config['MOMO_IPN_URL']}"
                     f"&orderId={order_id}&orderInfo={order_info}&partnerCode={app.config['MOMO_PARTNER_CODE']}"
                     f"&redirectUrl={app.config['MOMO_REDIRECT_URL']}&requestId={request_id}&requestType=captureWallet")

    h = hmac.new(bytes(app.config['MOMO_SECRET_KEY'], 'ascii'), bytes(raw_signature, 'utf-8'), hashlib.sha256)
    signature = h.hexdigest()

    # 4. Gửi yêu cầu sang MoMo (Dùng URL trong ảnh bạn gửi)
    data = {
        'partnerCode': app.config['MOMO_PARTNER_CODE'],
        'partnerName': "Cloud Storage Test",
        'storeId': "MomoTestStore",
        'requestId': request_id,
        'amount': amount,
        'orderId': order_id,
        'orderInfo': order_info,
        'redirectUrl': app.config['MOMO_REDIRECT_URL'],
        'ipnUrl': app.config['MOMO_IPN_URL'],
        'lang': 'vi',
        'extraData': "",
        'requestType': "captureWallet",
        'signature': signature
    }

    try:
        response = requests.post(app.config['MOMO_ENDPOINT'], json=data)  # Gửi POST request
        result = response.json()
        if result['resultCode'] == 0:
            return redirect(result['payUrl'])  # Chuyển hướng sang MoMo
        else:
            flash(result.get('message'), "danger")
            return redirect(url_for('billing'))
    except Exception as e:
        flash(str(e), "danger")
        return redirect(url_for('billing'))


@app.route('/billing/return')
@login_required
def payment_return():
    result_code = request.args.get('resultCode')
    order_id = request.args.get('orderId')

    transaction = Transaction.query.filter_by(order_id=order_id).first()

    if transaction and result_code == '0':
        if transaction.status != 'SUCCESS':
            transaction.status = 'SUCCESS'
            # Nâng cấp dung lượng lên 100GB
            user = User.query.get(current_user.id)
            # Nếu đóng 1 Triệu -> Lên 1TB (1024 GB)
            if transaction.amount >= 1000000:
                user.storage_limit_gb = 1024
                flash("Đẳng cấp! Bạn đã sở hữu gói VIP PRO 1TB.", "success")

            # Nếu đóng 50 Ngàn -> Lên 100 GB
            elif transaction.amount >= 50000:
                user.storage_limit_gb = 100
                flash("Thanh toán thành công! Dung lượng đã lên 100GB.", "success")

            db.session.commit()
    else:
        if transaction:
            transaction.status = 'FAILED'
            db.session.commit()
        flash("Thanh toán thất bại.", "danger")

    return redirect(url_for('user_dashboard'))


# @app.route('/momo_ipn', methods=['POST'])
# def momo_ipn():
#     return '', 204


if __name__ == "__main__":
    app.run(debug=True)