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
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)


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



def get_files_for_user(user_id, q=None):
    files = load_files()
    user_files = [f for f in files if f['user_id'] == user_id]

    if q:
        q_lower = q.lower()
        user_files = [f for f in user_files if q_lower in f["object_name"].lower()]

    return user_files


def get_all_files(q=None):
    files = load_files()
    if q:
        q_lower = q.lower()
        files = [f for f in files if q_lower in f["object_name"].lower()]
    return files


def get_all_users():
    return load_users()




def get_user_storage_usage(user_id):
    files = get_files_for_user(user_id)
    total_mb = sum(f.get('size_mb', 0) for f in files)
    return total_mb


def get_user_quota_limit(user_id):
    return 15 * 1024


def add_file_record(user_id, object_name, size_mb):

    files = load_files()


    new_file = {
        "id": len(files) + 101,
        "object_name": object_name,
        "size_mb": size_mb,
        "last_modified": "2025-11-15",
        "user_id": user_id
    }
    files.append(new_file)


    try:
        with open(files_path, 'w', encoding='utf-8') as f:
            json.dump(files, f, indent=2)
        return True
    except Exception as e:
        print(f"Lỗi khi ghi file JSON: {e}")
        return False