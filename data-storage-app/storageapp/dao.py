import json
import os


# ... (Giữ nguyên class MockUser) ...

# --- Lớp MockUser ---
class MockUser:
    def __init__(self, id, name, role):
        self.id = id
        self.name = name
        self.role = role

    def is_authenticated(self):
        """Hàm bắt buộc: Trả về True nếu user đã đăng nhập."""
        return True

    def is_active(self):
        """Hàm bắt buộc: Trả về True nếu user được phép đăng nhập."""
        return True

    def is_anonymous(self):
        """Hàm bắt buộc: Trả về False."""
        return False

    def get_id(self):
        """Hàm bắt buộc: Trả về ID (dưới dạng chuỗi) của user."""
        return str(self.id)


# --- Đường dẫn đến file JSON ---
base_dir = os.path.abspath(os.path.dirname(__file__))
users_path = os.path.join(base_dir, 'data', 'user.json')
files_path = os.path.join(base_dir, 'data', 'files.json')


def load_users():
    try:
        with open(users_path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def load_files():
    try:
        with open(files_path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


# --- Logic xác thực ---
def auth_user(username, password):
    users = load_users()
    for u in users:
        if u['username'] == username and u['password'] == password:
            return u
    return None


def get_user_by_id(user_id):
    users = load_users()
    for u in users:
        if u['id'] == int(user_id):
            return MockUser(id=u['id'], name=u['name'], role=u['role'])
    return None


# --- Logic nghiệp vụ (Phân quyền & Quota) ---

def get_files_for_user(user_id, q=None):
    """
    CHỈ lấy file thuộc về user_id cụ thể.
    """
    files = load_files()
    user_files = [f for f in files if f['user_id'] == user_id]

    if q:
        q_lower = q.lower()
        user_files = [f for f in user_files if q_lower in f["object_name"].lower()]

    return user_files


def get_all_files(q=None):
    """
    Lấy TẤT CẢ file (dùng cho Admin).
    """
    files = load_files()
    if q:
        q_lower = q.lower()
        files = [f for f in files if q_lower in f["object_name"].lower()]
    return files


def get_all_users():
    """
    Lấy TẤT CẢ user (dùng cho Admin).
    """
    return load_users()


# --- MỚI: CÁC HÀM TÍNH QUOTA VÀ LƯU DATA ---

def get_user_storage_usage(user_id):
    """Tính tổng dung lượng (MB) user đã sử dụng."""
    files = get_files_for_user(user_id)
    total_mb = sum(f.get('size_mb', 0) for f in files)
    return total_mb


def get_user_quota_limit(user_id):
    """Lấy giới hạn quota (MB). Tạm thời 15GB."""
    # TODO: Sau này sẽ đọc từ DB xem user dùng gói nào
    return 15 * 1024  # 15GB (tính bằng MB)


def add_file_record(user_id, object_name, size_mb):
    """Thêm record mới vào files.json SAU KHI upload thành công."""
    files = load_files()

    # Tạo file record mới
    new_file = {
        "id": len(files) + 101,  # ID đơn giản
        "object_name": object_name,
        "size_mb": size_mb,
        "last_modified": "2025-11-15",  # (Nên dùng datetime)
        "user_id": user_id
    }
    files.append(new_file)

    # Ghi đè lại file JSON (cẩn thận, chỉ dùng cho MOCK)
    try:
        with open(files_path, 'w', encoding='utf-8') as f:
            json.dump(files, f, indent=2)
        return True
    except Exception as e:
        print(f"Lỗi khi ghi file JSON: {e}")
        return False