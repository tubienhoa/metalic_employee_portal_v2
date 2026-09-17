import streamlit as st
import pandas as pd
from services.sheets_service import get_records, append_record
from services.audit_service import write_audit_log

def show_admin(user_info):
    """
    Khu vuc danh cho Quan tri vien he thong Metalic Employee Portal.
    Kiem tra nghiem ngat quyen han truoc khi hien thi.
    """
    user_role = str(user_info.get("Role", "")).strip().upper()
    allowed_roles = ["SYSTEM_ADMIN", "SUPER_ADMIN", "HR_ADMIN"]

    if user_role not in allowed_roles:
        st.error("⛔ CẢNH BÁO: Bạn không có quyền truy cập vào Khu vực Quản trị!")
        st.warning("Hệ thống đã ghi lại thao tác truy cập trái phép này vào nhật ký an ninh.")
        write_audit_log(user_info.get("Username"), "ACCESS_DENIED", "Admin Area", f"Quyen yeu cau khong dap ung (Role: {user_role})")
        return

    st.title("⚙️ Khu Vực Quản Trị Hệ Thống")
    st.caption("Dành riêng cho Quản trị viên IT và Nhân sự (Admin)")

    # Ghi nhat ky truy cap quan tri
    write_audit_log(user_info.get("Username"), "ACCESS_ADMIN", "Admin Area", "Vao trang quan tri")

    tab_users, tab_announcements, tab_audit = st.tabs([
        "👥 Quản Lý Người Dùng",
        "📢 Quản Lý Thông Báo",
        "🛡️ Nhật Ký Hoạt Động (Audit Log)"
    ])

    with tab_users:
        st.subheader("Danh sách Tài khoản Người dùng")
        users = get_records("Users")
        if users:
            df_users = pd.DataFrame(users)
            # Khong hien thi cot mat khau hash tren man hinh de dam bao an toan
            safe_cols = [c for c in df_users.columns if c != "Password_Hash"]
            st.dataframe(df_users[safe_cols], use_container_width=True)
        else:
            st.info("Chưa có danh sách người dùng.")

    with tab_announcements:
        st.subheader("Tạo Thông Báo Nội Bộ Mới")
        with st.form("create_announcement_form"):
            a_title = st.text_input("Tiêu đề thông báo:")
            a_dept = st.selectbox("Phòng ban áp dụng:", ["Toàn công ty", "Sản xuất", "Kho vận", "Kinh doanh", "Nhân sự", "Kỹ thuật - Bảo trì"])
            a_factory = st.selectbox("Nhà máy:", ["Cả 2 nhà máy", "Nhà máy 1", "Nhà máy 2"])
            a_content = st.text_area("Nội dung thông báo chi tiết:")
            submit_announcement = st.form_submit_button("Đăng thông báo", type="primary")

            if submit_announcement:
                if a_title and a_content:
                    import datetime
                    new_id = f"TB-{datetime.datetime.now().strftime('%Y%m%d%H%M')}"
                    today_str = datetime.date.today().strftime("%Y-%m-%d")
                    record = [
                        new_id,
                        a_title,
                        a_content,
                        a_dept,
                        a_factory,
                        today_str,
                        "",
                        "ACTIVE",
                        user_info.get("Username")
                    ]
                    success = append_record("Announcements", record)
                    if success:
                        st.success("Đã ban hành thông báo thành công!")
                        write_audit_log(user_info.get("Username"), "CREATE_ANNOUNCEMENT", "Announcements", f"Tao thong bao {new_id}")
                else:
                    st.error("Vui lòng điền đầy đủ tiêu đề và nội dung.")

    with tab_audit:
        st.subheader("Nhật Ký Hệ Thống (Audit Logs)")
        logs = get_records("Audit_Log")
        if logs:
            df_logs = pd.DataFrame(logs)
            st.dataframe(df_logs.tail(50), use_container_width=True)
        else:
            st.info("Chưa có nhật ký hoạt động.")
