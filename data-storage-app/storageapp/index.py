from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user, login_required
from storageapp import app, dao, login
from storageapp import controllers  # Giữ lại controllers cho logic MinIO

# --- Cấu hình Flask-Login ---
login.login_view = 'user_login'
login.login_message = 'Vui lòng đăng nhập để xem trang này!'
login.login_message_category = 'info'  # Dùng cho flash() của Bootstrap


@login.user_loader
def load_user(user_id):
    return dao.get_user_by_id(user_id)


# --- 1. ROUTE CÔNG KHAI (PUBLIC) ---

@app.route("/")
def homepage():
    """
    Trang chủ (Landing Page) công khai.
    Nếu đã đăng nhập, tự động chuyển hướng đến dashboard.
    """
    if current_user.is_authenticated:
        if current_user.role == 'ADMIN':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('user_dashboard'))

    return render_template("homepage.html")


# --- 2. ROUTE XÁC THỰC (AUTHENTICATION) ---

@app.route("/login", methods=["get", "post"])
def user_login():
    """
    Trang đăng nhập (cho cả User và Admin).
    """
    if current_user.is_authenticated:
        # Nếu đã đăng nhập, đá về dashboard tương ứng
        if current_user.role == 'ADMIN':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('user_dashboard'))

    err_msg = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Dùng mock DAO để xác thực
        user_dict = dao.auth_user(username, password)

        if user_dict:
            user_obj = dao.get_user_by_id(user_dict['id'])
            login_user(user_obj)

            # PHÂN QUYỀN: Kiểm tra vai trò
            if user_dict['role'] == 'ADMIN':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            err_msg = "Tài khoản hoặc mật khẩu không đúng!"

    return render_template("login.html", err_msg=err_msg)


@app.route("/register", methods=["get", "post"])
def user_register():
    if current_user.is_authenticated:
        return redirect(url_for('user_dashboard'))

    err_msg = None
    if request.method == "POST":
        name = request.form.get("name")
        username = request.form.get("username")
        password = request.form.get("password")
        confirm = request.form.get("confirm_password")

        # Logic xác thực cơ bản
        if password != confirm:
            err_msg = "Mật khẩu xác nhận không khớp!"
        else:
            # TODO: Thêm logic dao.create_user(name, username, password)
            # (Trong dự án thật:
            # 1. Tạo User trong MySQL
            # 2. Tạo Bucket trên MinIO với tên bucket = "user-{user_id}"
            # )
            err_msg = "Chức năng đăng ký đang được bảo trì (đã validate)."
            # Sau khi tạo user thành công, nên:
            # flash('Đăng ký thành công! Vui lòng đăng nhập.', 'success')
            # return redirect(url_for('user_login'))

    return render_template("register.html", err_msg=err_msg)


@app.route("/logout")
@login_required  # Chỉ người đã đăng nhập mới logout được
def user_logout():
    logout_user()
    return redirect(url_for('homepage'))  # Về trang chủ


# --- 3. ROUTE CỦA NGƯỜI DÙNG (USER) ---

@app.route("/dashboard")
@login_required
def user_dashboard():
    """
    Dashboard chính của User (Giao diện Google Drive).
    """
    # Bảo vệ route: Chỉ User được vào
    if current_user.role != 'USER':
        return redirect(url_for('admin_dashboard'))  # Đá Admin về trang của Admin

    q = request.args.get("q")
    # Lấy file CHỈ của user đang đăng nhập
    files = dao.get_files_for_user(user_id=current_user.id, q=q)
    return render_template("index.html", files=files)


@app.route("/billing")
@login_required
def billing():
    """
    Trang thanh toán (Quản lý Quota, Gói cước).
    """
    if current_user.role != 'USER':
        return redirect(url_for('admin_dashboard'))

    # TODO: Lấy thông tin Quota, Gói cước của current_user
    # (Ví dụ: usage = dao.get_user_storage_usage(current_user.id))

    return render_template("billing.html")


# --- 4. ROUTE CỦA QUẢN TRỊ VIÊN (ADMIN) ---

@app.route("/admin")
@login_required
def admin_dashboard():
    """
    Dashboard của Admin (Giao diện Drive Admin).
    """
    # Bảo vệ route: Chỉ Admin được vào
    if current_user.role != 'ADMIN':
        return redirect(url_for('user_dashboard'))  # Đá User về trang của User

    # Lấy TẤT CẢ user và TẤT CẢ file
    all_users = dao.get_all_users()
    all_files = dao.get_all_files()

    return render_template("admin/admin_dashboard.html",
                           all_users=all_users,
                           all_files=all_files)


# --- 5. FILE API ROUTES (MinIO) ---

@app.route('/upload', methods=['POST'])
@login_required
def api_upload_file():
    # TODO: Cần kiểm tra Quota của user trước khi upload

    # Gọi logic từ controllers.py
    response, code = controllers.api_upload_file()

    if code == 201:
        # TODO: Cập nhật lại dung lượng đã dùng (usage) cho user
        flash('Tải tệp lên thành công!', 'success')
    else:
        flash('Có lỗi xảy ra khi tải tệp.', 'danger')

    # Quay về dashboard của user
    return redirect(url_for('user_dashboard'))


@app.route('/download-url/<path:object_name>', methods=['GET'])
@login_required
def api_get_download_url(object_name):
    # TODO: Logic kiểm tra file này có thuộc current_user không
    # (hoặc user có phải là Admin không)
    # file = dao.get_file(object_name)
    # if file.user_id != current_user.id and current_user.role != 'ADMIN':
    #     return "Không có quyền truy cập file", 403

    response_data = controllers.api_get_download_url(object_name)

    if isinstance(response_data, tuple):
        response_body, status_code = response_data
        if status_code == 200:
            url = response_body.get_json()['url']
            return redirect(url)

    return "Không tìm thấy file hoặc có lỗi", 404


# ... (Thêm route /delete/<path:object_name> tương tự) ...

if __name__ == "__main__":
    app.run(debug=True)