from flask import render_template, request, redirect, url_for, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from storageapp import app, dao, login
from storageapp import controllers  # Giữ lại controllers cho logic MinIO

# --- Cấu hình Flask-Login (giống saleappg1) ---
login.login_view = 'user_login'
login.login_message = 'Vui lòng đăng nhập để xem trang này!'
login.login_message_category = 'info'  # Bootstrap category


@login.user_loader
def load_user(user_id):
    return dao.get_user_by_id(user_id)


# --- USER ROUTES ---
@app.route("/")
@login_required  # Bắt buộc đăng nhập
def home():
    """
    Hiển thị Dashboard (giống Google Drive)
    CHỈ hiển thị file của user đang đăng nhập.
    """
    q = request.args.get("q")
    files = dao.get_files_for_user(user_id=current_user.id, q=q)
    return render_template("index.html", files=files)


@app.route("/login", methods=["get", "post"])
def user_login():
    """
    Trang đăng nhập (cho cả User và Admin)
    """
    if current_user.is_authenticated:
        return redirect("/")

    err_msg = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Dùng mock DAO để xác thực
        user_dict = dao.auth_user(username, password)

        if user_dict:
            # Lấy đối tượng MockUser từ ID
            user_obj = dao.get_user_by_id(user_dict['id'])
            login_user(user_obj)

            # PHÂN QUYỀN: Kiểm tra vai trò
            if user_dict['role'] == 'ADMIN':
                return redirect("/admin")  # Chuyển đến trang Admin
            else:
                return redirect("/")  # Chuyển đến Dashboard User
        else:
            err_msg = "Tài khoản hoặc mật khẩu không đúng!"

    return render_template("login.html", err_msg=err_msg)


@app.route("/register", methods=["get", "post"])
def user_register():
    if current_user.is_authenticated:
        return redirect("/")

    err_msg = None
    if request.method == "POST":
        # (Logic đăng ký với mockdata phức tạp, tạm bỏ qua)
        # (Trong dự án thật, bạn sẽ ghi vào file JSON hoặc DB)
        err_msg = "Chức năng đăng ký đang được bảo trì."

    return render_template("register.html", err_msg=err_msg)


@app.route("/logout")
def user_logout():
    logout_user()
    return redirect('/login')


@app.route("/billing")
@login_required
def billing():
    """
    Trang thanh toán (theo yêu cầu)
    """
    return render_template("billing.html")


# --- ADMIN ROUTE (MỚI) ---
@app.route("/admin")
@login_required
def admin_dashboard():
    """
    Trang quản trị tùy chỉnh (Thay thế Flask-Admin)
    """
    # Bảo vệ route: Chỉ Admin được vào
    if current_user.role != 'ADMIN':
        return redirect("/")

    all_users = dao.get_all_users()
    all_files = dao.get_all_files()

    return render_template("admin_dashboard.html",
                           all_users=all_users,
                           all_files=all_files)


# --- FILE API ROUTES (Giữ nguyên của cozgg) ---
# Thêm @login_required để bảo vệ
@app.route('/upload', methods=['POST'])
@login_required
def api_upload_file():
    # Gọi logic từ controllers.py [cite: cozgg/cloud-data-storage/cloud-data-storage-83fa1480202b049c020effcb27d60f4c884d5f51/data-storage-app/storageapp/controllers.py]
    response, code = controllers.api_upload_file()
    if code == 201:
        # Upload thành công, quay về trang chủ
        return redirect("/")

    # (Có thể thêm thông báo lỗi qua flash())
    return redirect("/")


@app.route('/download-url/<path:object_name>', methods=['GET'])
@login_required
def api_get_download_url(object_name):
    # (Cần thêm logic kiểm tra file này có thuộc current_user không)
    response_data = controllers.api_get_download_url(object_name)

    # Kiểm tra xem response_data có phải là tuple không (do jsonify trả về)
    if isinstance(response_data, tuple):
        response_body, status_code = response_data
        if status_code == 200:
            # Lấy URL từ JSON và chuyển hướng
            url = response_body.get_json()['url']
            return redirect(url)

    # Nếu lỗi
    return "Không tìm thấy file hoặc có lỗi", 404


# ... (Thêm route /delete/<path:object_name> tương tự) ...

if __name__ == "__main__":
    app.run(debug=True)