import os
from flask import request, jsonify
from datetime import datetime

from storageapp.test_helpers import (
    upload_file_to_minio,
    get_presigned_download_url,
    delete_file_from_minio
)

DEFAULT_BUCKET = "my-bucket"
"""
    object_name: Tên đầy đủ của file trên MinIO (bao gồm cả thư mục nếu có).
"""
def api_upload_file():

    if 'file' not in request.files:
        return jsonify({"error": "Không tìm thấy file trong request"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "Tên file không được để trống"}), 400

    if file:
        try:
            object_name = file.filename

            file.stream.seek(0, os.SEEK_END)
            data_length = file.stream.tell()
            file.stream.seek(0)

            success = upload_file_to_minio(
                bucket_name=DEFAULT_BUCKET,
                object_name=object_name,
                data_stream=file.stream,
                data_length=data_length
            )

            if success:
                return jsonify({
                    "message": "Tải file lên thành công",
                    "bucket": DEFAULT_BUCKET,
                    "object_name": object_name
                }), 201
            else:
                return jsonify({"error": "Không thể tải file lên"}), 500

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return jsonify({"error": "Đã xảy ra lỗi không xác định"}), 500

def api_get_download_url(object_name):

    if not object_name:
        return jsonify({"error": "Thiếu tên file (object_name)"}), 400

    try:
        url = get_presigned_download_url(
            bucket_name=DEFAULT_BUCKET,
            object_name=object_name
        )

        if url:
            return jsonify({
                "message": "Lấy URL thành công",
                "url": url,
                "object_name": object_name,
                "expires_in": "1 giờ"
            }), 200
        else:

            return jsonify({"error": "Không thể tạo URL (file có thể không tồn tại)"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def api_delete_file(object_name):
    """
     object_name: Tên đầy đủ của file trên MinIO.
    """
    if not object_name:
        return jsonify({"error": "Thiếu tên file (object_name)"}), 400

    try:
        success = delete_file_from_minio(
            bucket_name=DEFAULT_BUCKET,
            object_name=object_name
        )

        if success:
            return jsonify({
                "message": "Xóa file thành công",
                "object_name": object_name
            }), 200
        else:
            return jsonify({"error": "Không thể xóa file (file có thể không tồn tại)"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500