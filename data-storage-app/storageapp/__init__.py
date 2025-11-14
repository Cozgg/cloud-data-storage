from flask import Flask

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:root@localhost/clouddb?charset=utf8mb4"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config["MINIO_ENDPOINT"] = "127.0.0.1:9000"
app.config["MINIO_ACCESS_KEY"] = "minioadmin"
app.config["MINIO_SECRET_KEY"] = "minioadmin"

# docker run -p 9000:9000 -p 9001:9001 -e "MINIO_ROOT_USER=minioadmin" -e "MINIO_ROOT_PASSWORD=minioadmin" -v C:\minio-data:/data quay.io/minio/minio server /data --console-address ":9001"