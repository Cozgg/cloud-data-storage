import os
import json
import hmac
import hashlib
import time
import uuid
import requests
from flask import render_template, request, redirect, url_for, flash, Blueprint
from flask_login import login_user, logout_user, current_user, login_required
from storageapp import app, dao, login, controllers, db
from storageapp.models import User, UserRole, Transaction
from storageapp.test_helpers import delete_file_from_minio, DEFAULT_BUCKET

login.login_view = 'user_login'
login.login_message = 'Vui lòng đăng nhập để xem trang này!'
login.login_message_category = 'info'


@login.user_loader
def load_user(user_id):
    return dao.get_user_by_id(user_id)


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
            login_user(user=user_dict)
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
            try:
                # Dùng hàm add_user mới trong dao
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

    # Kiểm tra folder hiện tại
    current_folder = None
    breadcrumbs = []
    if folder_id:
        current_folder = dao.get_folder_by_id(folder_id)
        # Bảo mật: Không cho xem folder của người khác
        if not current_folder or current_folder.user_id != current_user.id:
            flash("Thư mục không tồn tại hoặc bạn không có quyền truy cập", "danger")
            return redirect(url_for('user_dashboard'))

        breadcrumbs = dao.get_folder_breadcrumbs(folder_id)

    # Lấy nội dung (Folder con + File)
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
        # Chuyển đổi parent_id
        p_id = int(parent_id) if parent_id and parent_id != 'None' and parent_id != '' else None
        try:
            dao.create_folder(current_user.id, name, p_id)
            flash('Đã tạo thư mục mới', 'success')
        except Exception as e:
            flash(f'Lỗi tạo thư mục: {e}', 'danger')

    # Reload lại trang hiện tại
    return redirect_back(parent_id)


@app.route('/upload', methods=['POST'])
@login_required
def api_upload_file():
    folder_id_str = request.form.get('folder_id')
    folder_id = int(folder_id_str) if folder_id_str and folder_id_str != 'None' and folder_id_str != '' else None

    if 'file' not in request.files:
        flash('Không có tệp nào được chọn.', 'danger')
        return redirect_back(folder_id)

    file = request.files['file']
    if file.filename == '':
        flash('Tên tệp không hợp lệ.', 'danger')
        return redirect_back(folder_id)

    file.seek(0, os.SEEK_END)
    file_size_bytes = file.tell()
    file_size_mb = file_size_bytes / (1024 * 1024)
    file.seek(0)

    # Check Quota
    usage_mb = dao.get_user_storage_usage(current_user.id)
    limit_mb = dao.get_user_quota_limit(current_user.id)
    if (usage_mb + file_size_mb) > limit_mb:
        flash('Hết dung lượng lưu trữ!', 'danger')
        return redirect_back(folder_id)

    object_name = f"user_{current_user.id}/{file.filename}"
    # Để tránh trùng tên file, có thể thêm UUID:
    # object_name = f"user_{current_user.id}/{uuid.uuid4()}_{file.filename}"

    try:
        success, _ = controllers.upload_file_to_minio(object_name, file.stream, file_size_bytes)
        if success:
            # Lưu file vào DB kèm theo folder_id
            dao.add_file_record(current_user.id, object_name, file_size_mb, folder_id)
            flash('Tải tệp lên thành công!', 'success')
        else:
            flash('Lỗi MinIO.', 'danger')
    except Exception as e:
        flash(f'Lỗi: {e}', 'danger')

    return redirect_back(folder_id)


def redirect_back(folder_id):
    """Helper function để redirect về đúng folder đang đứng"""
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
    owned_object_names = [f.object_name for f in user_files]  # Sửa: truy cập thuộc tính object_name của Model

    if object_name not in owned_object_names:
        flash('Bạn không có quyền xóa file này!', 'danger')
        return redirect(url_for('user_dashboard'))

    try:
        delete_minio_success = delete_file_from_minio(DEFAULT_BUCKET, object_name)
        # Lưu ý: Nếu file không tồn tại trên MinIO nhưng có trong DB, vẫn nên cho xóa DB
        # Nên ta sẽ ưu tiên xóa DB nếu MinIO xóa OK hoặc MinIO báo không tìm thấy

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


# --- PHẦN MOMO ĐƯỢC COMMENT TẠM THỜI ---
# Bạn có thể mở lại khi đã sẵn sàng test thanh toán

# @app.route('/billing/create_payment')
# @login_required
# def create_payment():
#     # ... (Code cũ của bạn) ...
#     return "Tính năng đang bảo trì", 503

# @app.route('/billing/return')
# @login_required
# def payment_return():
#     # ...
#     return redirect(url_for('user_dashboard'))

# @app.route('/momo_ipn', methods=['POST'])
# def momo_ipn():
#     return '', 204


if __name__ == "__main__":
    app.run(debug=True)