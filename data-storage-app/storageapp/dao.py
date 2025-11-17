import hashlib
import json
import os

from sqlalchemy import func

from storageapp import db
from storageapp.models import User, File


def auth_user(username, password):
    password = str(hashlib.md5(password.encode('utf-8')).hexdigest())
    user = User.query.filter(User.username.__eq__(username), User.password.__eq__(password))

    return user.first()


def get_user_by_id(user_id):
    user = User.query.get(user_id)
    return user


def get_files_for_user(user_id, q=None):
    """Lấy danh sách file của user từ RDS."""
    query = File.query.filter_by(user_id=user_id)
    if q:
        query = query.filter(File.name.like(f"%{q}%"))
    return query.all()


def get_all_files():
    return File.query.all()


def get_all_users():
    return User.query.all()


def get_user_storage_usage(user_id):
    usage = db.session.query(func.sum(File.size_mb)) \
        .filter_by(user_id=user_id).scalar()
    return usage or 0


def get_user_quota_limit(user_id):
    return 15 * 1024


def add_file_record(user_id, file_name, size_mb):
    new_file = File(
        name=file_name,
        size_mb=size_mb,
        user_id=user_id
    )
    db.session.add(new_file)
    db.session.commit()
    return new_file


def delete_file_record(file_record):
    db.session.delete(file_record)
    db.session.commit()

    return False


def get_file_by_id(file_id, user_id):
    """Lấy 1 file và kiểm tra quyền sở hữu."""
    return File.query.filter_by(id=file_id, user_id=user_id).first()
