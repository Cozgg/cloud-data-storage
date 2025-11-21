from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.secret_key = "Cozgdeptraiokechuaae123@"

# Thay 'PUBLIC_IP_CUA_EC2_MINIO' bằng IP thật trên AWS của bạn (ví dụ: 3.14.15.92)
MINIO_IP = "PUBLIC_IP_CUA_EC2_MINIO"
app.config["MINIO_ENDPOINT"] = f"{MINIO_IP}:9000"
app.config["MINIO_ACCESS_KEY"] = "minioadmin"
app.config["MINIO_SECRET_KEY"] = "minioadmin"
app.config["MINIO_SECURE"] = False

# --- CẤU HÌNH DATABASE (RDS HOẶC EC2 SỐ 2) ---
# Thay 'ENDPOINT_CUA_RDS' bằng đường dẫn AWS cấp cho bạn
DB_USER = "admin"
DB_PASS = "password123"
DB_HOST = "database-do-an.xxxxxx.us-east-1.rds.amazonaws.com" # Endpoint RDS
DB_NAME = "cloudstorage"

app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
login = LoginManager(app)