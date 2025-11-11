
from minio import Minio

from storageapp import app

try:
    minio_client = Minio(
        app.config["MINIO_ENDPOINT"],
        access_key=app.config["MINIO_ACCESS_KEY"],
        secret_key=app.config["MINIO_SECRET_KEY"],
        secure=False # Đặt là False nếu chạy local không có SSL
    )
    print("Kết nối MinIO thành công!")
except Exception as e:
    print(f"Lỗi khi kết nối MinIO: {e}")
    minio_client = None