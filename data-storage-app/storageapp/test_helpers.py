import os
from datetime import datetime, timedelta
from storageapp.minio_client import minio_client  # Giữ nguyên

DEFAULT_BUCKET = "my-bucket"  # Tên bucket của bạn


def upload_file_to_minio(object_name, data_stream, data_length):
    if not minio_client:
        raise Exception("MinIO client chưa được khởi tạo")

    try:
        # --- MỚI: KIỂM TRA VÀ TẠO BUCKET ---
        found = minio_client.bucket_exists(DEFAULT_BUCKET)
        if not found:
            minio_client.make_bucket(DEFAULT_BUCKET)
            print(f"Đã tạo bucket '{DEFAULT_BUCKET}' vì nó không tồn tại.")
        # --- KẾT THÚC THÊM ---

        data_stream.seek(0) # Đảm bảo stream ở đầu

        minio_client.put_object(
            DEFAULT_BUCKET,
            object_name,
            data_stream,
            length=data_length
        )
        print(f"Tải {object_name} lên thành công")
        return True, data_length
    except Exception as e:
        print(f"Lỗi khi tải file lên: {e}")
        return False, 0


def get_presigned_download_url(object_name):
    if not minio_client:
        raise Exception("MinIO client chưa được khởi tạo")

    try:
        url = minio_client.get_presigned_url(
            'GET',
            DEFAULT_BUCKET,
            object_name,
            expires=timedelta(hours=1)
        )
        return url
    except Exception as e:
        print(f"Lỗi khi tạo link download: {e}")
        return None

def delete_file_from_minio(bucket_name, object_name):
    if not minio_client:
        raise Exception("MinIO client chưa được khởi tạo")

    try:
        minio_client.remove_object(bucket_name=bucket_name, object_name=object_name)
        return True
    except Exception as e:
        print(f"Lỗi khi xóa file: {e}")
        return False

def get_presigned_upload_url(object_name):
    if not minio_client:
        raise Exception("MinIO client chưa được khởi tạo")
    try:
        url = minio_client.get_presigned_url(
            "PUT",
            DEFAULT_BUCKET,
            object_name,
            expires=timedelta(hours=1)
        )
        return url
    except Exception as e:
        print(f"Lỗi tạo URL upload: {e}")
        return None
