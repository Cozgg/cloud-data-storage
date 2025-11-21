from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.secret_key = "Cozgdeptraiokechuaae123@"

# Thay 'PUBLIC_IP_CUA_EC2_MINIO' bằng IP thật trên AWS của bạn (ví dụ: 3.14.15.92)
app.config["MINIO_ENDPOINT"] = "54.158.50.254:9000"
app.config["MINIO_ACCESS_KEY"] = "admin"
app.config["MINIO_SECRET_KEY"] = "matkhaucuaban123"
app.config["MINIO_SECURE"] = False

# --- CẤU HÌNH DATABASE (RDS HOẶC EC2 SỐ 2) ---
# Thay 'ENDPOINT_CUA_RDS' bằng đường dẫn AWS cấp cho bạn
DB_USER = "admin"
DB_PASS = "12345678"
DB_HOST = "database-cloud-storage.cuakz9khnlh0.us-east-1.rds.amazonaws.com" # Endpoint RDS
DB_NAME = "cloudstorage"

app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
login = LoginManager(app)

# docker run -p 9000:9000 -p 9001:9001 -e "MINIO_ROOT_USER=minioadmin" -e "MINIO_ROOT_PASSWORD=minioadmin" -v C:\minio-data:/data quay.io/minio/minio server /data --console-address ":9001"

