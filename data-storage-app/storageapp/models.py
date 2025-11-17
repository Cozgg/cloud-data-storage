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
    password = Column(String(150), nullable=False)
    avatar = Column(String(300), nullable=True)
    role = Column(Enum(UserRole), default=UserRole.USER)
    is_locked = Column(Boolean, default=False)

    files = relationship('File', backref='user', lazy=True)


class File(Base):
    size_mb = Column(Float, default=0.0)
    last_modified = Column(DateTime, default=datetime.now())
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)


class BillingPackage(Base):
    price = Column(Float, default=0.0)
    storage_limit_gb = Column(Integer, default=15)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()