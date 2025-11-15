import os
from datetime import datetime
from storageapp.minio_client import minio_client  # Giữ nguyên

DEFAULT_BUCKET = "my-bucket"  # (Nên tạo bucket này trước)


def upload_file_to_minio(object_name, data_stream):
    if not minio_client:
        raise Exception("MinIO client chưa được khởi tạo")

    try:
        # Refactor lại từ code gốc
        data_stream.seek(0, os.SEEK_END)
        data_length = data_stream.tell()
        data_stream.seek(0)

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
        # Giữ nguyên logic
        url = minio_client.get_presigned_url(
            DEFAULT_BUCKET,
            object_name,
            expires=datetime.timedelta(hours=1)
        )
        return url
    except Exception as e:
        print(f"Lỗi khi tạo link download: {e}")
        return None

# ... (Thêm hàm delete_file_from_minio) ...