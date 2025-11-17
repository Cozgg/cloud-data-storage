from flask import Flask
from flask_login import LoginManager

app = Flask(__name__)

# Cấu hình app
app.secret_key = "MY_VERY_SECRET_KEY_123!@#" # BẮT BUỘC cho Flask-Login
app.config["MINIO_ENDPOINT"] = "127.0.0.1:9000"
app.config["MINIO_ACCESS_KEY"] = "minioadmin"
app.config["MINIO_SECRET_KEY"] = "minioadmin"

# docker run -p 9000:9000 -p 9001:9001 -e "MINIO_ROOT_USER=minioadmin" -e "MINIO_ROOT_PASSWORD=minioadmin" -v C:\minio-data:/data quay.io/minio/minio server /data --console-address ":9001"

login = LoginManager(app)