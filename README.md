# CỔNG THÔNG TIN NHÂN VIÊN METALIC (METALIC EMPLOYEE PORTAL)

Dự án Cổng thông tin nhân viên nội bộ dành cho Công ty Sản xuất & Gia công thép xuất khẩu Metalic Việt Nam (2 nhà máy).

## 1. Cấu trúc thư mục
```
metalic_employee_portal/
│
├── app.py
├── requirements.txt
├── README.md
│
├── services/
│   ├── __init__.py
│   ├── auth_service.py
│   ├── sheets_service.py
│   ├── drive_service.py
│   └── audit_service.py
│
├── pages/
│   ├── __init__.py
│   ├── home.py
│   ├── documents.py
│   └── admin.py
│
└── utils/
    ├── __init__.py
    └── create_password_hash.py
```

## 2. Cấu hình Streamlit Secrets (.streamlit/secrets.toml hoặc trên Streamlit Cloud)
```toml
[gcp_service_account]
type = "service_account"
project_id = "YOUR_PROJECT_ID"
private_key_id = "YOUR_PRIVATE_KEY_ID"
private_key = "-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY\n-----END PRIVATE KEY-----\n"
client_email = "YOUR_SERVICE_ACCOUNT_EMAIL"
client_id = "YOUR_CLIENT_ID"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "YOUR_CLIENT_CERT_URL"

[app]
spreadsheet_name = "METALIC_PORTAL_DATABASE"
drive_root_folder_id = "YOUR_DRIVE_FOLDER_ID"
```

## 3. Hướng dẫn chạy thử nghiệm cục bộ (Local Run)
1. Cài đặt môi trường:
   ```bash
   pip install -r requirements.txt
   ```
2. Tạo file hash mật khẩu mẫu nếu cần:
   ```bash
   python utils/create_password_hash.py
   ```
3. Khởi chạy Streamlit:
   ```bash
   streamlit run app.py
   ```
