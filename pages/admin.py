import streamlit as st
import pandas as pd
import bcrypt
from services.sheets_service import (
    get_records,
    append_record,
    create_user,
    username_exists,
    set_user_status,
    update_user_fields,
)
from services.audit_service import write_audit_log
from services.auth_service import PASSWORD_MIN_LENGTH

ROLE_OPTIONS = ["EMPLOYEE", "HR_ADMIN", "SYSTEM_ADMIN", "SUPER_ADMIN"]
DEPARTMENT_OPTIONS = ["Sản xuất", "QA/QC", "Kho vận", "Kỹ thuật", "An toàn (HSE)", "Nhân sự", "Hành chính", "Kinh doanh"]
FACTORY_OPTIONS = ["1", "2", "ALL"]


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
        "👥 Quản Lý Tài Khoản",
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
            users = []

        st.markdown("---")

        col_create, col_manage = st.columns(2, gap="large")

        # ------------------------------------------------------------------
        # [PHASE 1] TAO TAI KHOAN MOI - khong con phai sua tay tren Google Sheet
        # ------------------------------------------------------------------
        with col_create:
            st.markdown("##### ➕ Tạo tài khoản mới")
            with st.form("create_user_form", clear_on_submit=True):
                c_username = st.text_input("Username (mã nhân viên / tên đăng nhập)")
                c_fullname = st.text_input("Họ và tên")
                c_position = st.text_input("Chức danh / Vị trí")
                c_dept = st.selectbox("Phòng ban", DEPARTMENT_OPTIONS)
                c_factory = st.selectbox("Nhà máy", FACTORY_OPTIONS, format_func=lambda x: "Cả 2 nhà máy" if x == "ALL" else f"Nhà máy {x}")
                c_role = st.selectbox("Vai trò (Role)", ROLE_OPTIONS)
                c_password = st.text_input("Mật khẩu tạm thời", type="password", help=f"Tối thiểu {PASSWORD_MIN_LENGTH} ký tự. Nhân viên nên đổi lại sau khi đăng nhập lần đầu.")
                submit_create = st.form_submit_button("Tạo tài khoản", type="primary", use_container_width=True)

                if submit_create:
                    if not c_username or not c_fullname or not c_password:
                        st.error("Vui lòng điền đầy đủ Username, Họ tên và Mật khẩu tạm thời.")
                    elif len(c_password) < PASSWORD_MIN_LENGTH:
                        st.error(f"Mật khẩu tạm thời phải có tối thiểu {PASSWORD_MIN_LENGTH} ký tự.")
                    elif username_exists(c_username):
                        st.error(f"Username '{c_username}' đã tồn tại. Vui lòng chọn Username khác.")
                    else:
                        salt = bcrypt.gensalt(rounds=12)
                        hashed = bcrypt.hashpw(c_password.encode("utf-8"), salt).decode("utf-8")
                        new_user = {
                            "Username": c_username.strip(),
                            "Full_Name": c_fullname.strip(),
                            "Position": c_position.strip(),
                            "Department": c_dept,
                            "Factory": c_factory,
                            "Role": c_role,
                            "Status": "ACTIVE",
                            "Password_Hash": hashed,
                            "Failed_Attempts": 0,
                        }
                        if create_user(new_user):
                            write_audit_log(user_info.get("Username"), "CREATE_USER", c_username, f"Tao tai khoan moi ({c_role} - {c_dept})")
                            st.success(f"Đã tạo tài khoản '{c_username}' thành công!")
                        else:
                            st.error("Không thể tạo tài khoản. Vui lòng kiểm tra lại cấu hình Sheet 'Users'.")

        # ------------------------------------------------------------------
        # [PHASE 1] KHOA / MO KHOA TAI KHOAN - dung khi nhan vien nghi viec
        # hoac can tam ngung truy cap, thay vi sua tay tren Google Sheet.
        # ------------------------------------------------------------------
        with col_manage:
            st.markdown("##### 🔒 Khóa / Mở khóa tài khoản")
            usernames = [str(u.get("Username", "")) for u in users if u.get("Username")]
            if usernames:
                sel_username = st.selectbox("Chọn tài khoản", usernames, key="lock_user_select")
                current_user_row = next((u for u in users if str(u.get("Username", "")) == sel_username), {})
                current_status = str(current_user_row.get("Status", "")).strip().upper()
                st.caption(f"Trạng thái hiện tại: **{current_status or 'Không rõ'}**")

                c_lock, c_unlock = st.columns(2)
                with c_lock:
                    if st.button("🔒 Khóa tài khoản", use_container_width=True, disabled=(sel_username == user_info.get("Username"))):
                        if set_user_status(sel_username, "LOCKED"):
                            write_audit_log(user_info.get("Username"), "LOCK_USER", sel_username, "Khoa tai khoan (vi du: nhan vien nghi viec)")
                            st.success(f"Đã khóa tài khoản '{sel_username}'.")
                            st.rerun()
                with c_unlock:
                    if st.button("🔓 Mở khóa tài khoản", use_container_width=True):
                        if set_user_status(sel_username, "ACTIVE"):
                            write_audit_log(user_info.get("Username"), "UNLOCK_USER", sel_username, "Mo khoa tai khoan, reset so lan dang nhap sai")
                            st.success(f"Đã mở khóa tài khoản '{sel_username}'.")
                            st.rerun()

                if sel_username == user_info.get("Username"):
                    st.caption("⚠️ Không thể tự khóa tài khoản đang đăng nhập của chính mình.")

                st.markdown("###### Gán lại Vai trò / Phòng ban / Nhà máy")
                with st.form("update_role_form"):
                    n_role = st.selectbox("Vai trò (Role)", ROLE_OPTIONS, index=ROLE_OPTIONS.index(current_user_row.get("Role")) if current_user_row.get("Role") in ROLE_OPTIONS else 0)
                    n_dept = st.selectbox("Phòng ban", DEPARTMENT_OPTIONS, index=DEPARTMENT_OPTIONS.index(current_user_row.get("Department")) if current_user_row.get("Department") in DEPARTMENT_OPTIONS else 0)
                    n_factory = st.selectbox("Nhà máy", FACTORY_OPTIONS, index=FACTORY_OPTIONS.index(str(current_user_row.get("Factory"))) if str(current_user_row.get("Factory")) in FACTORY_OPTIONS else 0, format_func=lambda x: "Cả 2 nhà máy" if x == "ALL" else f"Nhà máy {x}")
                    if st.form_submit_button("Cập nhật", use_container_width=True):
                        if update_user_fields(sel_username, {"Role": n_role, "Department": n_dept, "Factory": n_factory}):
                            write_audit_log(user_info.get("Username"), "UPDATE_USER", sel_username, f"Gan Role={n_role}, Department={n_dept}, Factory={n_factory}")
                            st.success("Đã cập nhật thông tin tài khoản.")
                            st.rerun()
            else:
                st.info("Chưa có tài khoản nào để quản lý.")

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
