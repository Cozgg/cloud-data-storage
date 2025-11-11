from datetime import datetime

from storageapp.minio_client import minio_client


def upload_file_to_minio(bucket_name, object_name, data_stream, data_length):
    """
        Upload một file stream lên MinIO.
        object_name: Tên file trên MinIO (ví dụ: "user_1/image.png")
        data_stream: Dữ liệu file (ví dụ: request.files['myFile'].stream)
        data_length: Kích thước file (ví dụ: request.files['myFile'].tell())
        """

    if not minio_client:
        raise Exception("MinIO client chưa được khởi tạo")

    try:
        minio_client.put_object(
            bucket_name,
            object_name,
            data_stream,
            length=data_length
        )
        print(f"Tải dữ liệu {object_name} lên thành công")
        return True
    except Exception as e:
        print(f"Lỗi khi tải file lên: {e}")
        return False


def get_presigned_download_url(bucket_name, object_name):

    if not minio_client:
        raise Exception("MinIO client chưa được khởi tạo")

    try:
        #thời gian time out là 1 giờ
        url = minio_client.get_presigned_url(
            bucket_name,
            object_name,
            expires=datetime.timedelta(hours=1)
        )
        print(f"Tạo link download cho {object_name} thành công!")
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

