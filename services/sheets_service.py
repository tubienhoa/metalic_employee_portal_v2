import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource(ttl=3600)
def get_gspread_client():
    """
    Khoi tao va tra ve gspread client su dung thong tin Service Account tu st.secrets.
    """
    if "gcp_service_account" not in st.secrets:
        raise ValueError("Chua cau hinh st.secrets['gcp_service_account']. Vui long kiem tra lai.")

    creds_info = dict(st.secrets["gcp_service_account"])
    if "private_key" in creds_info and "\\n" in creds_info["private_key"]:
        creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")

    creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client

def get_spreadsheet():
    """
    Mo Google Spreadsheet theo ten duoc cau hinh trong st.secrets['app']['spreadsheet_name'].
    """
    client = get_gspread_client()
    spreadsheet_name = st.secrets.get("app", {}).get("spreadsheet_name", "METALIC_PORTAL_DATABASE")
    try:
        sh = client.open(spreadsheet_name)
        return sh
    except gspread.SpreadsheetNotFound:
        raise FileNotFoundError(f"Khong tim thay Google Sheet co ten: '{spreadsheet_name}'. Hay dam bao da chia se quyen Editor cho Service Account.")
    except Exception as e:
        raise RuntimeError(f"Loi khi ket noi Google Sheets: {str(e)}")

def get_records(worksheet_name):
    """
    Doc tat ca ban ghi tu worksheet chi dinh va tra ve list cac dictionary.
    """
    try:
        sh = get_spreadsheet()
        worksheet = sh.worksheet(worksheet_name)
        return worksheet.get_all_records()
    except gspread.WorksheetNotFound:
        st.warning(f"Chua tim thay sheet '{worksheet_name}'.")
        return []
    except Exception as e:
        st.error(f"Loi khi doc sheet '{worksheet_name}': {str(e)}")
        return []

def append_record(worksheet_name, record):
    """
    Them mot dong ban ghi moi vao worksheet (record co the la list cac gia tri).
    """
    try:
        sh = get_spreadsheet()
        worksheet = sh.worksheet(worksheet_name)
        worksheet.append_row(record)
        return True
    except Exception as e:
        st.error(f"Loi khi ghi vao sheet '{worksheet_name}': {str(e)}")
        return False

def update_user_password(username, new_password_hash):
    """
    Cap nhat mat khau ma hoa (Password_Hash) moi cho username trong sheet Users.
    """
    try:
        sh = get_spreadsheet()
        worksheet = sh.worksheet("Users")
        users = worksheet.get_all_records()

        # Cot Password_Hash la cot H (cot so 8)
        headers = worksheet.row_values(1)
        pwd_col_idx = headers.index("Password_Hash") + 1 if "Password_Hash" in headers else 8

        for idx, u in enumerate(users, start=2):
            if str(u.get("Username", "")).strip().lower() == str(username).strip().lower():
                worksheet.update_cell(idx, pwd_col_idx, new_password_hash)
                return True
        return False
    except Exception as e:
        st.error(f"Loi khi cap nhat mat khau: {str(e)}")
        return False


# ---------------------------------------------------------------------------
# [PHASE 1 - BO SUNG CRUD TAI KHOAN] (Cau 4 - Phuong an A: van dung Google Sheet
# 'Users' lam noi luu, nhung Admin thao tac tao/khoa/mo khoa/gan quyen ngay tren
# portal thay vi phai sua tay truc tiep trong Google Sheet).
# ---------------------------------------------------------------------------

def find_user_row(worksheet, username):
    """
    Tra ve (row_index, user_dict) cua nguoi dung theo Username (khong phan biet hoa/thuong).
    row_index la vi tri dong tren Google Sheet (dong 1 la header nen du lieu bat dau tu dong 2).
    Tra ve (None, None) neu khong tim thay.
    """
    users = worksheet.get_all_records()
    for idx, u in enumerate(users, start=2):
        if str(u.get("Username", "")).strip().lower() == str(username).strip().lower():
            return idx, u
    return None, None


def username_exists(username):
    """Kiem tra Username da ton tai trong sheet Users hay chua (tranh tao trung)."""
    try:
        sh = get_spreadsheet()
        worksheet = sh.worksheet("Users")
        idx, _ = find_user_row(worksheet, username)
        return idx is not None
    except Exception as e:
        st.error(f"Loi khi kiem tra Username: {str(e)}")
        return False


def create_user(user_fields: dict) -> bool:
    """
    Tao tai khoan nhan vien moi trong sheet Users.
    user_fields: dict voi key trung ten cot tren sheet, vi du:
        {"Username": "...", "Full_Name": "...", "Password_Hash": "...",
         "Position": "...", "Department": "...", "Factory": "1",
         "Role": "EMPLOYEE", "Status": "ACTIVE", "Failed_Attempts": 0}
    Cac cot khong duoc truyen se de trong. Thu tu cot lay theo dong header thuc te
    tren Google Sheet, khong gia dinh thu tu co dinh trong code.
    """
    try:
        sh = get_spreadsheet()
        worksheet = sh.worksheet("Users")
        headers = worksheet.row_values(1)
        if not headers:
            st.error("Sheet 'Users' chua co dong tieu de (header).")
            return False
        row = [str(user_fields.get(h, "")) for h in headers]
        worksheet.append_row(row)
        return True
    except Exception as e:
        st.error(f"Loi khi tao tai khoan: {str(e)}")
        return False


def set_user_status(username: str, new_status: str) -> bool:
    """
    Khoa ("LOCKED") hoac mo khoa / kich hoat lai ("ACTIVE") mot tai khoan.
    Dung cho tinh huong: nhan vien nghi viec (Admin khoa) hoac tuyen lai (Admin mo khoa).
    Khi mo khoa, dong thoi reset Failed_Attempts ve 0 (neu sheet co cot nay) de
    tai khoan khong bi tinh la dang bi khoa do dang nhap sai truoc do.
    """
    try:
        sh = get_spreadsheet()
        worksheet = sh.worksheet("Users")
        headers = worksheet.row_values(1)
        idx, _ = find_user_row(worksheet, username)
        if idx is None:
            return False

        if "Status" not in headers:
            st.error("Sheet 'Users' chua co cot 'Status'.")
            return False
        status_col_idx = headers.index("Status") + 1
        worksheet.update_cell(idx, status_col_idx, new_status)

        if new_status.strip().upper() == "ACTIVE" and "Failed_Attempts" in headers:
            fa_col_idx = headers.index("Failed_Attempts") + 1
            worksheet.update_cell(idx, fa_col_idx, 0)

        return True
    except Exception as e:
        st.error(f"Loi khi cap nhat trang thai tai khoan: {str(e)}")
        return False


def update_user_fields(username: str, fields: dict) -> bool:
    """
    Cap nhat cac truong khac cua tai khoan (vi du: Role, Department, Factory, Position...).
    fields: dict {ten_cot: gia_tri_moi}. Chi cap nhat cac cot ton tai tren sheet.
    """
    try:
        sh = get_spreadsheet()
        worksheet = sh.worksheet("Users")
        headers = worksheet.row_values(1)
        idx, _ = find_user_row(worksheet, username)
        if idx is None:
            return False

        for field_name, value in fields.items():
            if field_name in headers:
                col_idx = headers.index(field_name) + 1
                worksheet.update_cell(idx, col_idx, value)
        return True
    except Exception as e:
        st.error(f"Loi khi cap nhat thong tin tai khoan: {str(e)}")
        return False


def increment_failed_attempts(username: str) -> int:
    """
    [PHASE 1 - KHOA TAI KHOAN SAU N LAN DANG NHAP SAI]
    Tang bo dem Failed_Attempts len 1 va tra ve gia tri moi.
    Neu sheet 'Users' CHUA co cot 'Failed_Attempts', ham se bo qua (tra ve -1)
    de khong lam gian doan luong dang nhap - can bo sung cot nay thu cong tren
    Google Sheet (gia tri mac dinh 0) de tinh nang khoa tu dong hoat dong.
    """
    try:
        sh = get_spreadsheet()
        worksheet = sh.worksheet("Users")
        headers = worksheet.row_values(1)
        if "Failed_Attempts" not in headers:
            return -1

        idx, user = find_user_row(worksheet, username)
        if idx is None:
            return -1

        current = int(user.get("Failed_Attempts", 0) or 0)
        new_value = current + 1
        col_idx = headers.index("Failed_Attempts") + 1
        worksheet.update_cell(idx, col_idx, new_value)
        return new_value
    except Exception as e:
        print(f"[AUTH WARNING] Khong the cap nhat Failed_Attempts: {str(e)}")
        return -1


def reset_failed_attempts(username: str) -> bool:
    """Dua bo dem Failed_Attempts ve 0 sau khi dang nhap thanh cong."""
    try:
        sh = get_spreadsheet()
        worksheet = sh.worksheet("Users")
        headers = worksheet.row_values(1)
        if "Failed_Attempts" not in headers:
            return False

        idx, _ = find_user_row(worksheet, username)
        if idx is None:
            return False

        col_idx = headers.index("Failed_Attempts") + 1
        worksheet.update_cell(idx, col_idx, 0)
        return True
    except Exception as e:
        print(f"[AUTH WARNING] Khong the reset Failed_Attempts: {str(e)}")
        return False
