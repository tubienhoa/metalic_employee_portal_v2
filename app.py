import streamlit as st
import sys
import os
import bcrypt

# Dam bao Python nhan dien thu muc goc cua du an
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from services.auth_service import login_screen, logout
from services.sheets_service import update_user_password
from services.audit_service import write_audit_log
from pages.home import show_home
from pages.documents import show_documents
from pages.admin import show_admin

# Cau hinh trang
st.set_page_config(
    page_title="Cổng thông tin Metalic Việt Nam",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS tuy bien: An menu mac dinh, lam dep thanh Tab dieu huong tren cung
st.markdown(
    """
    <style>
    [data-testid="stSidebarNav"] {display: none;}
    
    /* Canh chinh va tao phong cach hien dai cho thanh Tab dieu huong tren cung */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #F1F5F9;
        padding: 8px 12px;
        border-radius: 10px;
        border: 1px solid #E2E8F0;
        margin-bottom: 20px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 46px;
        font-weight: 600;
        font-size: 15px;
        padding: 0 20px;
        border-radius: 8px;
        color: #475569;
        background-color: transparent;
        border: none;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF !important;
        color: #1E3A8A !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.06);
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Kiem tra trang thai dang nhap
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_info" not in st.session_state:
    st.session_state["user_info"] = None

if not st.session_state["logged_in"] or not st.session_state["user_info"]:
    login_screen()
    st.stop()

user = st.session_state["user_info"]

# Thanh Sidebar ben trai: Chi giu thong tin ca nhan va cac tien ich tai khoan
with st.sidebar:
    st.markdown("### 🏭 METALIC VIỆT NAM")
    st.caption("Cổng Thông Tin Nội Bộ 2 Nhà Máy")
    st.markdown("---")
    
    st.markdown(f"👤 **{user.get('Full_Name', user.get('Username'))}**")
    st.markdown(f"🏷️ Chức vụ: *{user.get('Position', 'Nhân viên')}*")
    st.markdown(f"🏢 Khối/Phòng: *{user.get('Department', 'Văn phòng')}*")
    st.markdown(f"🏭 Cơ sở trực thuộc: *Nhà máy {user.get('Factory', '1 & 2')}*")
    st.markdown("---")

    with st.expander("🔐 Đổi mật khẩu tài khoản", expanded=False):
        with st.form("sidebar_change_pwd_form"):
            new_pw = st.text_input("Mật khẩu mới:", type="password", placeholder="Nhập pass mới...")
            confirm_pw = st.text_input("Xác nhận lại:", type="password", placeholder="Nhập lại...")
            btn_save = st.form_submit_button("Cập nhật", type="primary", use_container_width=True)
            
            if btn_save:
                if not new_pw or not confirm_pw:
                    st.error("Vui lòng điền đủ thông tin.")
                elif len(new_pw) < 6:
                    st.error("Tối thiểu 6 ký tự.")
                elif new_pw != confirm_pw:
                    st.error("Xác nhận không khớp.")
                else:
                    salt = bcrypt.gensalt(rounds=12)
                    hashed = bcrypt.hashpw(new_pw.encode("utf-8"), salt).decode("utf-8")
                    username = user.get("Username")
                    if update_user_password(username, hashed):
                        write_audit_log(username, "CHANGE_PASSWORD", "Sidebar", "Doi mat khau ca nhan")
                        st.success("Đổi mật khẩu thành công!")
                    else:
                        st.error("Lỗi cập nhật. Vui lòng thử lại.")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚪 Đăng Xuất", use_container_width=True, type="secondary"):
        logout()

# THANH TAB DIEU HUONG CHINH PHIA TREN CUNG (TOP NAVIGATION)
user_role = str(user.get("Role", "")).upper()
is_admin = user_role in ["SYSTEM_ADMIN", "SUPER_ADMIN", "HR_ADMIN"]

if is_admin:
    tab_home, tab_docs, tab_admin = st.tabs([
        "🏠 Trang Chủ & Bảng Tin", 
        "📚 Kho Quy Trình & Biểu Mẫu", 
        "⚙️ Quản Trị Hệ Thống"
    ])
    with tab_home:
        show_home(user)
    with tab_docs:
        show_documents(user)
    with tab_admin:
        show_admin(user)
else:
    tab_home, tab_docs = st.tabs([
        "🏠 Trang Chủ & Bảng Tin", 
        "📚 Kho Quy Trình & Biểu Mẫu"
    ])
    with tab_home:
        show_home(user)
    with tab_docs:
        show_documents(user)
