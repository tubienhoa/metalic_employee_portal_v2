import streamlit as st
import pandas as pd
import bcrypt
from services.sheets_service import get_records, update_user_password
from services.audit_service import write_audit_log

def show_home(user_info):
    """
    Giao dien Trang chu cho Nhan vien cong ty Metalic Viet Nam.
    Tich hop tien ich Thong bao noi bo va Doi mat khau ca nhan.
    """
    st.markdown(
        f"""
        <div style="background-color: #F8FAFC; border-left: 5px solid #1E3A8A; padding: 15px 20px; border-radius: 6px; margin-bottom: 25px;">
            <h3 style="color: #0F172A; margin: 0;">Xin chào, {user_info.get('Full_Name', user_info.get('Username'))}! 👋</h3>
            <p style="color: #475569; margin: 5px 0 0 0; font-size: 14px;">
                Vị trí: <b>{user_info.get('Position', 'Nhân viên')}</b> | 
                Phòng ban: <b>{user_info.get('Department', 'Chưa phân bổ')}</b> | 
                Nhà máy: <b>Nhà máy {user_info.get('Factory', '1 & 2')}</b>
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Thong tin chi so nhanh
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Mã định danh", value=user_info.get("Username", "---"))
    with col2:
        st.metric(label="Phân quyền (Role)", value=user_info.get("Role", "EMPLOYEE"))
    with col3:
        st.metric(label="Trạng thái", value=user_info.get("Status", "ACTIVE"))
    with col4:
        st.metric(label="Khu vực", value=f"Nhà máy {user_info.get('Factory', '1')}")

    st.markdown("---")

    c_left, c_right = st.columns([2, 1])

    with c_left:
        st.subheader("📢 Thông Báo Nội Bộ Mới Nhất")
        try:
            announcements = get_records("Announcements")
            if announcements:
                active_announcements = [
                    a for a in announcements 
                    if str(a.get("Status", "")).strip().upper() == "ACTIVE"
                ]
                if active_announcements:
                    for item in active_announcements[-5:]:
                        with st.expander(f"📌 [{item.get('Publish_Date', '')}] {item.get('Title', 'Thông báo')}", expanded=True):
                            st.write(item.get("Content", ""))
                            st.caption(f"Ban hành bởi: {item.get('Created_By', 'Ban Lãnh Đạo')} | Áp dụng: {item.get('Department', 'Toàn công ty')}")
                else:
                    st.info("Hiện tại chưa có thông báo mới.")
            else:
                st.info("Chưa có dữ liệu thông báo nội bộ trong hệ thống.")
        except Exception:
            st.info("Hệ thống thông báo đang được cập nhật.")

    with c_right:
        st.subheader("🔐 Đổi Mật Khẩu Cá Nhân")
        with st.expander("Thay đổi mật khẩu tài khoản", expanded=False):
            with st.form("change_password_form"):
                new_pw = st.text_input("Mật khẩu mới:", type="password", placeholder="Nhập mật khẩu mới...")
                confirm_pw = st.text_input("Xác nhận mật khẩu:", type="password", placeholder="Nhập lại mật khẩu mới...")
                btn_change = st.form_submit_button("Lưu mật khẩu mới", type="primary", use_container_width=True)

                if btn_change:
                    if not new_pw or not confirm_pw:
                        st.error("Vui lòng điền đầy đủ cả 2 trường.")
                    elif len(new_pw) < 6:
                        st.error("Mật khẩu mới phải có độ dài tối thiểu từ 6 ký tự.")
                    elif new_pw != confirm_pw:
                        st.error("Mật khẩu xác nhận không trùng khớp.")
                    else:
                        # Tao chuoi bam bcrypt va cap nhat vao Google Sheet
                        salt = bcrypt.gensalt(rounds=12)
                        hashed = bcrypt.hashpw(new_pw.encode("utf-8"), salt).decode("utf-8")
                        username = user_info.get("Username")
                        
                        if update_user_password(username, hashed):
                            write_audit_log(username, "CHANGE_PASSWORD", "User Profile", "Doi mat khau ca nhan thanh cong")
                            st.success("Đổi mật khẩu thành công! Hãy ghi nhớ mật khẩu mới này.")
                        else:
                            st.error("Không thể cập nhật mật khẩu vào hệ thống. Vui lòng thử lại.")

        st.markdown("---")
        st.subheader("🔗 Lối Tắt Tiện Ích")
        st.markdown(
            """
            - 📑 **Quy trình sản xuất & an toàn thép**
            - 📋 **Biểu mẫu đề xuất xuất/nhập kho**
            - ⏱️ **Quy định ca kíp nhà máy 1 & 2**
            - 📦 **Quy trình kiểm soát chất lượng (QA/QC)**
            - 📞 **Đường dây nóng hỗ trợ IT & Nhân sự**
            """
        )
