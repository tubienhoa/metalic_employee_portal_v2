import streamlit as st
import bcrypt
from services.sheets_service import (
    get_records,
    increment_failed_attempts,
    reset_failed_attempts,
)
from services.audit_service import write_audit_log

# [PHASE 1 - P1] So lan dang nhap sai toi da truoc khi tai khoan bi khoa tu dong.
# Khoa tu dong (do Failed_Attempts) khac voi khoa thu cong (Status = LOCKED, dung khi
# nhan vien nghi viec) - Admin "Mo khoa" se reset ca hai.
MAX_FAILED_ATTEMPTS = 5

# Do dai mat khau toi thieu khi tao/doi mat khau (nang tu 6 len 8 ky tu - Phase 1).
PASSWORD_MIN_LENGTH = 8


def authenticate(username, password):
    """
    Kiem tra thong tin dang nhap:
    - Tim nguoi dung theo Username trong sheet Users
    - Kiem tra trang thai tai khoan: Status == 'ACTIVE'
    - Kiem tra so lan dang nhap sai lien tiep (Failed_Attempts) - qua nguong thi khoa tu dong
    - Kiem tra mat khau bang bcrypt
    Tra ve dictionary thong tin user neu thanh cong, "LOCKED" neu tai khoan bi khoa,
    nguoc lai tra ve None.
    """
    if not username or not password:
        return None

    try:
        users = get_records("Users")
    except Exception:
        return None

    for u in users:
        # Kiem tra khop username (khong phan biet chu hoa thuong khi tim)
        if str(u.get("Username", "")).strip().lower() == str(username).strip().lower():
            # Kiem tra trang thai Status (khoa thu cong - vi du nhan vien da nghi viec)
            status = str(u.get("Status", "")).strip().upper()
            if status != "ACTIVE":
                return "LOCKED"

            # Kiem tra khoa tu dong do dang nhap sai qua nhieu lan
            failed_attempts = int(u.get("Failed_Attempts", 0) or 0)
            if failed_attempts >= MAX_FAILED_ATTEMPTS:
                return "LOCKED"

            stored_hash = str(u.get("Password_Hash", "")).strip()
            try:
                # Kiem tra mat khau bcrypt
                if bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8")):
                    reset_failed_attempts(u.get("Username"))
                    return u
                else:
                    increment_failed_attempts(u.get("Username"))
                    return None
            except Exception:
                return None
    return None

def login_screen():
    """
    Hien thi man hinh dang nhap chuan cua Cong thong tin nhan vien Metalic.
    """
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(
            """
            <div style="text-align: center; padding: 20px 0;">
                <h2 style="color: #1E3A8A; margin-bottom: 5px;">CÔNG TY METALIC VIỆT NAM</h2>
                <h4 style="color: #475569; font-weight: 500;">CỔNG THÔNG TIN NHÂN VIÊN</h4>
                <p style="color: #64748B; font-size: 14px;">Hệ thống tra cứu thông tin, tài liệu & quy trình nội bộ</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        with st.form("login_form", clear_on_submit=False):
            username_input = st.text_input("Tên đăng nhập (Username)", placeholder="Nhập mã nhân viên hoặc username...")
            password_input = st.text_input("Mật khẩu (Password)", type="password", placeholder="Nhập mật khẩu...")
            submitted = st.form_submit_button("Đăng Nhập", use_container_width=True, type="primary")

            if submitted:
                if not username_input or not password_input:
                    st.error("Vui lòng điền đầy đủ Tên đăng nhập và Mật khẩu.")
                    return

                res = authenticate(username_input, password_input)
                if res == "LOCKED":
                    st.error("Tài khoản của bạn đã bị khóa hoặc không hoạt động. Vui lòng liên hệ phòng CNTT / Nhân sự.")
                    write_audit_log(username_input, "LOGIN_FAILED", "Auth", "Tai khoan bi khoa hoac chua kich hoat")
                elif res and isinstance(res, dict):
                    st.session_state["logged_in"] = True
                    st.session_state["user_info"] = res
                    write_audit_log(res.get("Username"), "LOGIN_SUCCESS", "Auth", "Dang nhap thanh cong")
                    st.success("Đăng nhập thành công! Đang chuyển hướng...")
                    st.rerun()
                else:
                    st.error("Tên đăng nhập hoặc mật khẩu không đúng.")
                    write_audit_log(username_input, "LOGIN_FAILED", "Auth", "Sai ten dang nhap hoac mat khau")

def logout():
    """
    Dang xuat tai khoan hien tai, ghi audit log va lam moi session_state.
    """
    if "user_info" in st.session_state and st.session_state["user_info"]:
        user = st.session_state["user_info"].get("Username", "Unknown")
        write_audit_log(user, "LOGOUT", "Auth", "Nguoi dung chu dong dang xuat")

    st.session_state["logged_in"] = False
    st.session_state["user_info"] = None
    st.rerun()
