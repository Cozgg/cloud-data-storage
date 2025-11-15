from flask import Flask
from flask_login import LoginManager

app = Flask(__name__)

# Cấu hình app
app.secret_key = "MY_VERY_SECRET_KEY_123!@#" # BẮT BUỘC cho Flask-Login
app.config["MINIO_ENDPOINT"] = "127.0.0.1:9000"
app.config["MINIO_ACCESS_KEY"] = "minioadmin"
app.config["MINIO_SECRET_KEY"] = "minioadmin"

# Khởi tạo LoginManager (Giống saleappg1) [cite: haunt2204/saleappit2301/SaleAppIT2301-81a57e4e5e2829d3b67b781d5904d82ff1286507/saleappg1/saleapp/__init__.py]
login = LoginManager(app)