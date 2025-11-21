from storageapp import db, app
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
from flask_login import UserMixin
from datetime import datetime
import enum


class UserRole(enum.Enum):
    USER = 1
    ADMIN = 2


class Base(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(150), nullable=False)
    created_date = Column(DateTime, default=datetime.now())


class User(Base, UserMixin):
    username = Column(String(150), unique=True, nullable=False)
    password = Column(String(150), nullable=False)  # MD5
    avatar = Column(String(300), nullable=True)
    role = Column(Enum(UserRole), default=UserRole.USER)
    storage_limit_gb = Column(Integer, default=15)

    files = relationship('File', backref='user', lazy=True)
    folders = relationship('Folder', backref='user', lazy=True)


class Folder(Base):

    parent_id = Column(Integer, ForeignKey('folder.id'), nullable=True)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)

    sub_folders = relationship('Folder',
                               backref=db.backref('parent', remote_side=[Base.id]),
                               lazy=True)
    files = relationship('File', backref='folder', lazy=True)


class File(Base):
    object_name = Column(String(500), nullable=False)
    size_mb = Column(Float, default=0.0)
    last_modified = Column(DateTime, default=datetime.now())
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)

    folder_id = Column(Integer, ForeignKey(Folder.id), nullable=True)


class BillingPackage(Base):
    price = Column(Float, default=0.0)
    storage_limit_gb = Column(Integer, default=15)


class Transaction(Base):
    order_id = Column(String(100), unique=True, nullable=False)
    amount = Column(Float, nullable=False)
    order_info = Column(String(200))
    status = Column(String(20), default='PENDING')
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()