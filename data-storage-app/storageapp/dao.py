import hashlib
from sqlalchemy import func
from storageapp import db
from storageapp.models import User, File, Folder


def auth_user(username, password):
    password = str(hashlib.md5(password.encode('utf-8')).hexdigest())
    return User.query.filter(User.username == username, User.password == password).first()


def get_user_by_id(user_id):
    return User.query.get(user_id)


def add_user(name, username, password):
    password_hash = str(hashlib.md5(password.encode('utf-8')).hexdigest())
    u = User(name=name, username=username, password=password_hash)
    db.session.add(u)
    db.session.commit()
    return u


def get_files_for_user(user_id, q=None):
    query = File.query.filter_by(user_id=user_id)
    if q:
        query = query.filter(File.object_name.like(f"%{q}%"))
    return query.all()


def get_all_users():
    return User.query.all()


def get_all_files():
    return File.query.all()


def get_user_storage_usage(user_id):
    usage = db.session.query(func.sum(File.size_mb)).filter_by(user_id=user_id).scalar()
    return usage or 0


def get_user_quota_limit(user_id):
    user = User.query.get(user_id)
    if user and user.storage_limit_gb:
        return user.storage_limit_gb * 1024
    return 15 * 1024

def create_folder(user_id, folder_name, parent_id=None):
    f = Folder(name=folder_name, user_id=user_id, parent_id=parent_id)
    db.session.add(f)
    db.session.commit()
    return f


def get_folder_by_id(folder_id):
    return Folder.query.get(folder_id)


def get_content_by_folder(user_id, folder_id=None, q=None):
    folders_query = Folder.query.filter_by(user_id=user_id, parent_id=folder_id)
    files_query = File.query.filter_by(user_id=user_id, folder_id=folder_id)

    if q:
        folders_query = folders_query.filter(Folder.name.like(f"%{q}%"))
        files_query = files_query.filter(File.object_name.like(f"%{q}%"))

    return folders_query.all(), files_query.all()


def add_file_record(user_id, object_name, size_mb, folder_id=None):
    short_name = object_name.split('/')[-1]
    new_file = File(name=short_name, object_name=object_name, size_mb=size_mb, user_id=user_id, folder_id=folder_id)
    db.session.add(new_file)
    db.session.commit()
    return new_file


def delete_file_record(object_name):
    file_record = File.query.filter_by(object_name=object_name).first()
    if file_record:
        db.session.delete(file_record)
        db.session.commit()
        return True
    return False


def get_folder_breadcrumbs(folder_id):
    crumbs = []
    current = Folder.query.get(folder_id)
    while current:
        crumbs.insert(0, current)
        if current.parent_id:
            current = Folder.query.get(current.parent_id)
        else:
            current = None
    return crumbs