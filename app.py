import streamlit as st
import sys
import os

# Dam bao Python nhan dien thu muc goc cua du an khi chay tren Streamlit Cloud
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from services.auth_service import login_screen, logout
from pages.home import show_home
from pages.documents import show_documents
from pages.admin import show_admin

# Thiet lap cau hinh trang Streamlit
st.set_page_config(
    page_title="Cổng thông tin nhân viên Metalic",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# An menu dieu huong mac dinh tu dong cua Streamlit
st.markdown(
    """
    <style>
    [data-testid="stSidebarNav"] {display: none;}
    </style>
    """,
    unsafe_allow_html=True
)

# Khoi tao trang thai dang nhap trong session_state
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_info" not in st.session_state:
    st.session_state["user_info"] = None

# Kiem tra neu chua dang nhap: hien thi man hinh Login va dung luong
if not st.session_state["logged_in"] or not st.session_state["user_info"]:
    login_screen()
    st.stop()

# Khi da dang nhap thanh cong: Hien thi Menu Sidebar va Noi dung
user = st.session_state["user_info"]

with st.sidebar:
    st.markdown("### 🏭 METALIC VIỆT NAM")
    st.caption("Cổng Thông Tin Nhân Viên Nội Bộ")
    st.markdown("---")
    
    st.markdown(f"👤 **{user.get('Full_Name', user.get('Username'))}**")
    st.markdown(f"🏷️ Vị trí: *{user.get('Position', 'Nhân viên')}*")
    st.markdown(f"🏢 Phòng ban: *{user.get('Department', 'Văn phòng')}*")
    st.markdown(f"🏭 Cơ sở: *Nhà máy {user.get('Factory', '1')}*")
    st.markdown("---")
    
    # Danh sach menu dieu huong
    menu_options = ["🏠 Trang Chủ", "📁 Kho Tài Liệu & Biểu Mẫu"]
    user_role = str(user.get("Role", "")).upper()
    if user_role in ["SYSTEM_ADMIN", "SUPER_ADMIN", "HR_ADMIN"]:
        menu_options.append("⚙️ Quản Trị Hệ Thống")
        
    choice = st.radio("Điều hướng:", menu_options)
    
    st.markdown("---")
    if st.button("🚪 Đăng Xuất", use_container_width=True, type="secondary"):
        logout()

# Dieu huong noi dung theo lua chon cua nguoi dung
if choice == "🏠 Trang Chủ":
    show_home(user)
elif choice == "📁 Kho Tài Liệu & Biểu Mẫu":
    show_documents(user)
elif choice == "⚙️ Quản Trị Hệ Thống":
    show_admin(user)
