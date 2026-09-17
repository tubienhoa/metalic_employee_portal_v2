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
    # Xu ly private_key chua escape newline
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
