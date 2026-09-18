# Ghi chú triển khai Phase 1 (18/09/2026)

Tài liệu này liệt kê các việc **thủ công** Anh Tư / IT cần làm trên Google Sheet và Google Drive
để các thay đổi code Phase 1 hoạt động đúng. Mã nguồn đã được sửa và syntax-check (py_compile) thành
công, nhưng **chưa được chạy thử với dữ liệu Google Sheets/Drive thật** vì môi trường chỉnh sửa này
không có `st.secrets` (thông tin đăng nhập Service Account) của công ty — cần Anh Tư tự kiểm thử lại
trên Streamlit Cloud hoặc local trước khi phát hành cho nhân viên.

## 1. Vá lỗ hổng chia sẻ tài liệu Drive (P0)

- Portal giờ lấy nội dung file trực tiếp qua Service Account (`services/drive_service.py::get_file_bytes`)
  và nhúng base64 vào trang, **không còn phụ thuộc link Drive công khai** (`.../preview`) nữa.
- Vì vậy: có thể (và nên) **tắt chế độ chia sẻ "Anyone with link" (Bất kỳ ai có đường liên kết)** trên
  toàn bộ file PDF/DOCX/XLSX trong thư mục gốc `METALIC_EMPLOYEE_PORTAL`.
- Chỉ cần đảm bảo Service Account (email ở `st.secrets['gcp_service_account']['client_email']`) vẫn
  có quyền **Viewer** trên thư mục gốc (thường đã có sẵn nếu trước đó đã chia sẻ thư mục gốc cho
  Service Account để `scan_all_drive_documents()` hoạt động).

## 2. Cột mới cần thêm vào sheet `Users`

Thêm cột **`Failed_Attempts`** (kiểu số, giá trị mặc định `0` cho toàn bộ tài khoản hiện có).

- Dùng để đếm số lần đăng nhập sai liên tiếp; đạt ngưỡng `MAX_FAILED_ATTEMPTS = 5`
  (`services/auth_service.py`) thì tài khoản tự động bị khóa (trả về như `Status = LOCKED`).
- Nếu **chưa** thêm cột này, hệ thống vẫn chạy bình thường (không lỗi) nhưng tính năng khóa tự động
  sẽ không hoạt động — chỉ còn khóa thủ công qua cột `Status`.
- Khi Admin bấm "Mở khóa tài khoản" trên portal, hệ thống tự reset `Failed_Attempts` về 0.

## 3. Thư mục Drive mới cho tài liệu ISO/QMS

Đã chốt: "Tài liệu ISO/QMS" là mục **độc lập** (không gộp vào Chất lượng hiện có).

- Cần tạo thêm 1 thư mục con trên Drive có tên chứa `ISO` hoặc `QMS` (ví dụ: `11_ISO_QMS` ở cấp gốc,
  hoặc `08_CHAT_LUONG/ISO_QMS`) — hệ thống tự nhận diện `Type = ISO_QMS` khi tên thư mục cha chứa
  các từ khóa này (`services/drive_service.py::parse_filename_metadata`).
- Không cần tạo thư mục riêng cho "Hướng dẫn công việc": đã chốt đây là một dạng của SOP nên vẫn đặt
  chung trong các thư mục SOP hiện có (`07_SAN_XUAT/...`), hệ thống coi là `Type = QUY_TRINH`.
- Thư mục `20_TAI_LIEU_DAO_TAO` đã được nhận diện tự động là `Type = DAO_TAO`, không cần đổi tên.

## 4. Phân quyền theo Nhà máy (P1)

- Nhân viên (không phải Admin) giờ chỉ thấy tài liệu và thông báo của đúng Nhà máy mình (`Factory`
  trong hồ sơ tài khoản) hoặc tài liệu áp dụng "Toàn công ty" (`Factory = ALL`).
- Admin (SYSTEM_ADMIN / SUPER_ADMIN / HR_ADMIN) vẫn thấy toàn bộ để phục vụ quản trị.
- **Chưa** lọc cứng theo Phòng ban (`Department`) vì rủi ro chặn nhầm các văn bản áp dụng nhiều phòng
  ban — bộ lọc Phòng ban trên Kho tài liệu vẫn là bộ lọc UI tự chọn như cũ. Nếu Anh Tư muốn khóa cứng
  theo phòng ban luôn, cần chốt thêm ma trận quyền cụ thể (phòng ban nào không được thấy phòng ban nào).

## 5. Quản lý tài khoản trong Admin (P1 — Câu 4, Phương án A)

- Vẫn dùng Google Sheet `Users` làm nơi lưu (không đổi sang Firebase/Entra ID).
- Đã bổ sung trong `pages/admin.py`, tab "👥 Quản Lý Tài Khoản":
  - Form **Tạo tài khoản mới** (Username, Họ tên, Chức danh, Phòng ban, Nhà máy, Role, mật khẩu tạm
    thời ≥ 8 ký tự, được băm bcrypt trước khi lưu).
  - Nút **Khóa / Mở khóa tài khoản** (không cho tự khóa tài khoản đang đăng nhập của chính mình).
  - Form **Gán lại Role / Phòng ban / Nhà máy** cho tài khoản đã có.
- Độ dài mật khẩu tối thiểu toàn hệ thống đã nâng từ 6 lên **8 ký tự** (`PASSWORD_MIN_LENGTH` trong
  `services/auth_service.py`, áp dụng cho cả form đổi mật khẩu trong sidebar và form tạo tài khoản).

## 6. Việc cần Anh Tư / IT làm trước khi phát hành

1. Thêm cột `Failed_Attempts` vào sheet `Users` (mục 2).
2. Tạo thư mục ISO/QMS trên Drive (mục 3), sắp xếp lại tài liệu ISO/QMS hiện có (nếu có) vào thư mục
   này theo đúng quy chuẩn đặt tên file.
3. Rà soát và tắt "Anyone with link" trên các file Drive hiện có (mục 1) sau khi đã xác nhận bản
   code mới chạy ổn định (khuyến nghị: giữ song song vài ngày, không tắt vội để tránh gián đoạn nếu
   phát sinh lỗi khi triển khai).
4. Deploy code mới lên Streamlit Cloud (hoặc môi trường đang chạy), test lại đầy đủ: đăng nhập, đăng
   nhập sai 5 lần liên tiếp (kiểm tra tự khóa), tạo tài khoản mới, khóa/mở khóa, xem tài liệu từng
   loại (Quy định / SOP / Biểu mẫu / Đào tạo / ISO-QMS), kiểm tra nhân viên NM1 không thấy tài liệu
   riêng của NM2 và ngược lại.
5. `requirements.txt` **không cần thêm gói mới** — `MediaIoBaseDownload` đã nằm trong
   `google-api-python-client` đã khai báo sẵn.
