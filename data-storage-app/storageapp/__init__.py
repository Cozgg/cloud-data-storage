from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Cấu hình app
app.secret_key = "MY_VERY_SECRET_KEY_123!@#" # BẮT BUỘC cho Flask-Login
app.config["MINIO_ENDPOINT"] = "127.0.0.1:9000"
app.config["MINIO_ACCESS_KEY"] = "minioadmin"
app.config["MINIO_SECRET_KEY"] = "minioadmin"
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://admin:cl0udst0rage@clouddb.ca1bkb68q3gi.us-east-1.rds.amazonaws.com/cloud"
# username admmin
# password db cl0udst0rage
# docker run -p 9000:9000 -p 9001:9001 -e "MINIO_ROOT_USER=minioadmin" -e "MINIO_ROOT_PASSWORD=minioadmin" -v C:\minio-data:/data quay.io/minio/minio server /data --console-address ":9001"
db = SQLAlchemy(app)
login = LoginManager(app)