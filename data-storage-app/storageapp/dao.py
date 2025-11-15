import json
import os


# --- Lớp MockUser (BẮT BUỘC cho Flask-Login) ---
# Flask-Login cần một đối tượng, không phải dict
class MockUser:
    def __init__(self, id, name, role):
        self.id = id
        self.name = name
        self.role = role

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
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


# --- Logic xác thực (Giống saleappg1) ---
def auth_user(username, password):
    """
    Xác thực người dùng từ mock data.
    """
    users = load_users()
    for u in users:
        if u['username'] == username and u['password'] == password:
            return u  # Trả về dict
    return None


def get_user_by_id(user_id):
    """
    Hàm này BẮT BUỘC cho Flask-Login.
    """
    users = load_users()
    for u in users:
        if u['id'] == int(user_id):
            return MockUser(id=u['id'], name=u['name'], role=u['role'])  # Trả về đối tượng
    return None


# --- Logic nghiệp vụ (Phân quyền) ---
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