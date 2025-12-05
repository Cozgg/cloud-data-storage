## 1. 📖 Tổng quan (Overview)

- **Mục tiêu:** Vận dụng kiến thức điện toán đám mây để thiết kế và triển khai hệ thống Web trên AWS.
- **Công nghệ chính:** Python (Flask), MySQL, Nginx, Gunicorn, AWS (EC2, RDS, ALB), MinIO.
- **Domain (demo):** http://ngustoragecloud.ddns.net

---

## 2. 🏗️ Kiến trúc Hệ thống (System Architecture)

Hệ thống được thiết kế theo mô hình phân tán trên 2 Availability Zones (us-east-1a và us-east-1b) để đảm bảo tính sẵn sàng cao (High Availability).

### Sơ đồ cấu trúc hạ tầng
![Sơ đồ kiến trúc AWS](https://res.cloudinary.com/dp6npbtxz/image/upload/v1764952547/aws_icn6is.jpg)
### Luồng dữ liệu (Data Flow)
- Người dùng truy cập qua tên miền (No-IP) → ALB → Nginx (Web Server).
- Web Server xử lý logic, gọi RDS để lấy metadata và cấp Presigned URL cho MinIO.
- Client upload/download trực tiếp tới MinIO bằng Presigned URL.

---

## 3. 🛠️ Chi tiết Triển khai

### A. Hạ tầng Mạng
- Sử dụng 2 Public Subnets trải trên 2 AZ để cân bằng tải và dự phòng.
- VPC mẫu: `10.0.0.0/16`.
- Security Groups chỉ mở port cần thiết:
	- HTTP (80) cho ALB → Nginx
	- MinIO (9000/9001) nội bộ
	- MySQL (3306) chỉ cho Web Server

### B. Cân bằng tải 
- ALB (Application Load Balancer) dùng cho web tier.
- Listener: port 80 (hoặc 443 nếu bật TLS).
- Target group: EC2 chạy Nginx (port 80).

### C. Máy chủ Ứng dụng
- EC2: Ubuntu 24.04 (t3.small).
- Nginx làm reverse proxy → Gunicorn (port 8000) chạy Flask app.
- Dùng systemd để quản lý process (Restart=always).

### D. Lưu trữ (MinIO Object Storage)
- MinIO chạy trên EC2 (t3.medium) để tiết kiệm chi phí so với S3 cho workload nhỏ.
- Cấu hình: bật CORS, sử dụng Presigned URL cho upload/download.

### E. Thanh toán (Payment Gateway — MoMo)
- Tích hợp MoMo để xử lý thanh toán dung lượng.
- Redirect URL sử dụng DNS của ALB.
- Xử lý IPN (Instant Payment Notification) để cập nhật gói dung lượng ngay lập tức trên hệ thống.
---

## 4. 👨‍💻 Tác giả

- **Tên:** Xem thêm trong [contributors](https://github.com/Cozgg/cloud-data-storage/graphs/contributors)
- **Dự án:** Cloud Data Storage
- **Email:** nguyenhuucong295@gmail.com

© 2025 Cloud Data Storage Project

---
