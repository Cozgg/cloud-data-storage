from storageapp.models import db, app, User
from storageapp.index import dao  # Giữ nguyên import dao để sử dụng dao.add_user
import os
import json


# Đọc dữ liệu người dùng từ file JSON
def load_user_data():
    """Tải và trả về danh sách người dùng từ file JSON."""
    try:
        # Lấy thư mục gốc của ứng dụng Flask, đây là thư mục chứa 'storageapp'
        # __file__ là đường dẫn của init_db.py.
        # Chúng ta giả định file user.json luôn nằm ở 'storageapp/data/user.json'

        # SỬA LOGIC: Lấy thư mục chứa file user.json bằng cách dùng đường dẫn tương đối
        # sau đó chuyển thành tuyệt đối
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'storageapp', 'data'))
        file_path = os.path.join(base_path, 'user.json')

        # Dùng phương pháp kiểm tra an toàn hơn
        if not os.path.exists(file_path):
            # Nếu không tìm thấy, thử đường dẫn cũ (giả định file init_db.py nằm ở thư mục cha)
            alt_path = os.path.abspath(
                os.path.join(os.path.dirname(os.path.dirname(__file__)), 'storageapp', 'data', 'user.json'))
            if os.path.exists(alt_path):
                file_path = alt_path
            else:
                print(f"LỖI: Không tìm thấy file dữ liệu người dùng. Đã kiểm tra: {file_path}")
                return []

        with open(file_path, 'r', encoding='utf-8') as f:
            print(f"-> Đã tìm thấy file user.json tại: {file_path}")
            return json.load(f)

    except Exception as e:
        print(f"LỖI ĐỌC FILE JSON: {e}")
        return []


def create_initial_data():
    """Tạo người dùng và dữ liệu khởi tạo nếu Database trống."""

    # 1. Tải dữ liệu từ file user.json
    user_data = load_user_data()

    # KIỂM TRA LẠI: Lần chạy đầu tiên phải có db.session.query(User).count() == 0
    if db.session.query(User).count() == 0:
        print("-> Database trống. Đang tạo bảng và dữ liệu khởi tạo...")

        # 1. Tạo tất cả các bảng (User, File, Folder, Transaction,...)
        db.create_all()
        print("-> Đã tạo tất cả các bảng.")

        # 2. Thêm dữ liệu người dùng ban đầu từ file user.json
        if user_data:  # KIỂM TRA ĐỂ ĐẢM BẢO user_data LÀ LIST
            try:
                for u_data in user_data:
                    # Hàm add_user trong dao đã hash mật khẩu
                    dao.add_user(u_data['name'], u_data['username'], u_data['password'])

                db.session.commit()
                print("-> Đã thêm người dùng Admin và User khởi tạo.")

            except Exception as e:
                # Bắt lỗi khi commit và in ra chi tiết
                db.session.rollback()
                print("==================================================================")
                print(f"LỖI LƯU DỮ LIỆU VÀO DATABASE: {type(e).__name__}")
                print(f"Nội dung lỗi: {e}")
                print("==================================================================")
                print(
                    "Gợi ý: Lỗi này thường xảy ra khi có dữ liệu bị trùng (UNIQUE constraint) hoặc thiếu trường (NOT NULL).")
                return  # Dừng nếu lỗi lưu dữ liệu

        else:
            print("CẢNH BÁO: user.json không có dữ liệu hoặc lỗi đọc file.")

    else:
        print("-> Database đã có dữ liệu. Bỏ qua bước tạo dữ liệu khởi tạo.")


if __name__ == "__main__":
    with app.app_context():
        create_initial_data()
        print("Hoàn tất quá trình khởi tạo cơ sở dữ liệu.")