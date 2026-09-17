import streamlit as st
import sys
import os
import bcrypt

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from services.auth_service import login_screen, logout
from services.sheets_service import update_user_password
from services.audit_service import write_audit_log
from pages.home import show_home
from pages.documents import show_documents
from pages.admin import show_admin

st.set_page_config(
    page_title="Metalic Portal | Cổng Thông Tin Nội Bộ",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# BO CSS THEME HIEN DAI (CHUAN CLAUDE ARTIFACT / SAAS DESIGN SYSTEM)
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #0F172A;
    }
    
    /* An mac dinh Streamlit */
    [data-testid="stSidebarNav"], #MainMenu, footer, header {
        display: none !important;
    }
    
    .main .block-container {
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
        max-width: 1400px;
    }

    /* Lam dep thanh Tab dieu huong tren cung (Pill Navigation) */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #F1F5F9;
        padding: 5px;
        border-radius: 12px;
        gap: 6px;
        border: 1px solid #E2E8F0;
        margin-bottom: 25px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 42px;
        padding: 0 22px;
        border-radius: 8px;
        font-weight: 500;
        font-size: 14px;
        color: #475569;
        background-color: transparent;
        border: none !important;
        transition: all 0.2s ease-in-out;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        font-weight: 600 !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08), 0 1px 2px rgba(0, 0, 0, 0.04) !important;
    }

    /* Sidebar hien dai */
    [data-testid="stSidebar"] {
        background-color: #FAFAFA;
        border-right: 1px solid #E5E7EB;
    }
    
    /* Card Container */
    .portal-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        transition: all 0.2s ease;
    }
    .portal-card:hover {
        border-color: #CBD5E1;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.06);
    }
    
    /* Nut bam toi gian */
    div.stButton > button {
        border-radius: 8px;
        font-weight: 500;
        font-size: 14px;
        border: 1px solid #E2E8F0;
        background-color: #FFFFFF;
        color: #0F172A;
        transition: all 0.15s ease;
    }
    div.stButton > button:hover {
        border-color: #94A3B8;
        background-color: #F8FAFC;
    }
    div.stButton > button[kind="primary"] {
        background-color: #0F172A;
        color: #FFFFFF;
        border: none;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #1E293B;
    }
    </style>
    """,
    unsafe_allow_html=True
)

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_info" not in st.session_state:
    st.session_state["user_info"] = None

if not st.session_state["logged_in"] or not st.session_state["user_info"]:
    login_screen()
    st.stop()

user = st.session_state["user_info"]

# SIDEBAR PROFILE PROFILE CAO CAP
with st.sidebar:
    st.markdown(
        """
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 15px;">
            <div style="background: #0F172A; color: white; width: 36px; height: 36px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 18px;">🏭</div>
            <div>
                <div style="font-weight: 700; font-size: 15px; color: #0F172A; line-height: 1.2;">METALIC VIETNAM</div>
                <div style="font-size: 11px; color: #64748B;">Internal Employee Portal</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown(
        f"""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 14px; margin-bottom: 20px;">
            <div style="font-size: 11px; text-transform: uppercase; color: #94A3B8; font-weight: 600; margin-bottom: 4px;">Tài khoản đăng nhập</div>
            <div style="font-weight: 600; font-size: 15px; color: #0F172A;">{user.get('Full_Name', user.get('Username'))}</div>
            <div style="font-size: 12px; color: #475569; margin-top: 2px;">{user.get('Position', 'Nhân viên')} • {user.get('Department', 'Văn phòng')}</div>
            <div style="margin-top: 10px; display: flex; gap: 6px;">
                <span style="background: #EFF6FF; color: #1E40AF; font-size: 11px; font-weight: 500; padding: 2px 8px; border-radius: 6px;">Nhà máy {user.get('Factory', '1')}</span>
                <span style="background: #F1F5F9; color: #334155; font-size: 11px; font-weight: 500; padding: 2px 8px; border-radius: 6px;">{user.get('Role', 'EMPLOYEE')}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    with st.expander("🔐 Đổi mật khẩu", expanded=False):
        with st.form("pwd_form"):
            new_pw = st.text_input("Mật khẩu mới", type="password")
            confirm_pw = st.text_input("Xác nhận", type="password")
            if st.form_submit_button("Lưu mật khẩu", type="primary", use_container_width=True):
                if new_pw and new_pw == confirm_pw and len(new_pw) >= 6:
                    salt = bcrypt.gensalt(rounds=12)
                    hashed = bcrypt.hashpw(new_pw.encode("utf-8"), salt).decode("utf-8")
                    if update_user_password(user.get("Username"), hashed):
                        write_audit_log(user.get("Username"), "CHANGE_PASSWORD", "Sidebar", "Doi mat khau")
                        st.success("Cập nhật thành công!")
                else:
                    st.error("Mật khẩu không khớp hoặc dưới 6 ký tự.")

    if st.button("Đăng xuất", use_container_width=True):
        logout()

# THANH DIEU HUONG TAB PHIA TREN
user_role = str(user.get("Role", "")).upper()
is_admin = user_role in ["SYSTEM_ADMIN", "SUPER_ADMIN", "HR_ADMIN"]

if is_admin:
    t_home, t_docs, t_admin = st.tabs(["Trang Chủ", "Kho Tài Liệu & Biểu Mẫu", "Quản Trị Hệ Thống"])
    with t_home:
        show_home(user)
    with t_docs:
        show_documents(user)
    with t_admin:
        show_admin(user)
else:
    t_home, t_docs = st.tabs(["Trang Chủ", "Kho Tài Liệu & Biểu Mẫu"])
    with t_home:
        show_home(user)
    with t_docs:
        show_documents(user)
