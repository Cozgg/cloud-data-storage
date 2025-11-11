# minio_client.py
from minio import Minio

minio_client = Minio(
    "127.0.0.1:9000",  # Địa chỉ MinIO server của em
    access_key="YOUR_ACCESS_KEY",  # Key của MinIO
    secret_key="YOUR_SECRET_KEY", # Secret của MinIO
    secure=False  # Đặt là True nếu em dùng HTTPS
)