# Cloud Data Storage System ☁️

## 1. 📖 Tổng quan (Overview)

Dự án xây dựng hệ thống lưu trữ dữ liệu đám mây phân tán, tích hợp khả năng tự động mở rộng (Auto Scaling) và thanh toán trực tuyến. Hệ thống được thiết kế để đảm bảo tính sẵn sàng cao (High Availability) và tối ưu hóa chi phí trên hạ tầng AWS.

- **Mục tiêu:** Vận dụng kiến thức điện toán đám mây để thiết kế, triển khai và vận hành hệ thống Web quy mô lớn trên AWS.
- **Công nghệ chính:** - **Backend:** Python (Flask), Gunicorn.
  - **Database & Storage:** MySQL (AWS RDS), MinIO Object Storage.
  - **Domain Name:** No IP.
  - **Infra & DevOps:** AWS (EC2, VPC, ALB, Auto Scaling Group), Nginx, Systemd.
- **Domain (demo):** [http://ngustoragecloud.ddns.net](http://ngustoragecloud.ddns.net)

---

## 2. 🏗️ Kiến trúc Hệ thống (System Architecture)

Hệ thống được thiết kế theo mô hình **High Availability (HA)**, phân tán trên 2 Availability Zones (`us-east-1a` và `us-east-1b`) tại vùng AWS US East (N. Virginia).

### Sơ đồ cấu trúc hạ tầng (Infrastructure Diagram)
![Sơ đồ kiến trúc AWS](https://res.cloudinary.com/dp6npbtxz/image/upload/v1765687666/Screenshot_2025-12-14_114715_yswm4v.png)

### Luồng dữ liệu (Data Flow)
1. **Truy cập:** Người dùng truy cập qua tên miền (DDNS) → Được trỏ CNAME về **Application Load Balancer (ALB)**.
2. **Điều phối:** ALB tự động phân tải request đến các **Web Server** khỏe mạnh trong nhóm **Auto Scaling Group**.
3. **Xử lý:** Web Server (Nginx + Flask) xử lý logic:
   - Truy vấn thông tin người dùng/file từ **AWS RDS (MySQL)**.
   - Tạo Presigned URL từ **MinIO Server** để cấp quyền truy cập file.
4. **Lưu trữ:** Client upload/download dữ liệu trực tiếp với **MinIO Server** (giảm tải băng thông cho Web Server).

---

## 3. 🛠️ Chi tiết Triển khai (Implementation Details)

### A. Hạ tầng Mạng (Networking)
- **VPC:** Custom VPC (`10.0.0.0/16`) với cấu hình mạng nâng cao.
- **Subnets:** Sử dụng 2 Public Subnets trải rộng trên 2 AZ để đảm bảo dự phòng (Failover).
- **Security Groups:** Thiết lập theo mô hình "Least Privilege":
	- **ALB SG:** Mở port 80/443 (Internet).
	- **Web Server SG:** Chỉ nhận traffic từ ALB SG.
	- **MinIO SG:** Mở port 9000/9001 (API/Console).
	- **RDS SG:** Chỉ cho phép kết nối từ Web Server SG.

### B. Cân bằng tải & Mở rộng (Load Balancing & Auto Scaling)
- **ALB (Application Load Balancer):** Đóng vai trò cửa ngõ duy nhất, thực hiện Health Check liên tục tới các instance.
- **Auto Scaling Group (ASG):**
  - **Cơ chế:** Tự động tăng/giảm số lượng server dựa trên mức độ sử dụng CPU (Target Tracking Policy: CPU > 50%).
  - **Capacity:** Min: 1 | Desired: 2 | Max: 5.
  - **Launch Template:** Tự động cấp phát máy chủ Ubuntu 24.04 đã cài sẵn môi trường (AMI custom).

### C. Máy chủ Ứng dụng (Application Tier)
- **Instance Type:** t3.small.
- **Runtime:** Nginx (Reverse Proxy) → Gunicorn (Port 5000) → Flask App.
- **Quản lý Process:** Systemd service (`cloudapp`) đảm bảo ứng dụng tự khởi động lại khi gặp sự cố.

### D. Lưu trữ (Storage Tier)
- **MinIO Object Storage:** Triển khai trên instance riêng biệt (`t3.medium`) để tối ưu hiệu năng I/O.
- **Cấu hình:** Tích hợp Bucket Policy, CORS và Presigned URL để bảo mật dữ liệu.

### E. Thanh toán (Payment Gateway — MoMo)
- Tích hợp cổng thanh toán MoMo QR Code.
- Sử dụng cơ chế **IPN (Instant Payment Notification)** để xử lý giao dịch realtime.
- Webhook nhận kết quả thanh toán được định tuyến qua ALB để đảm bảo tính ổn định.

---

## 4. 👨‍💻 Tác giả

- **Thực hiện bởi:** [Cozg] & Team.
- **Xem thêm:** [Danh sách đóng góp (Contributors)](https://github.com/Cozgg/cloud-data-storage/graphs/contributors)
- **Liên hệ:** nguyenhuucong295@gmail.com

---
© 2025 Cloud Data Storage Project
