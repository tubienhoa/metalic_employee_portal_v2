import streamlit as st
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

@st.cache_resource(ttl=3600)
def get_drive_service():
    """
    Khoi tao Google Drive API Client (v3) bang Service Account.
    """
    if "gcp_service_account" not in st.secrets:
        raise ValueError("Chua cau hinh st.secrets['gcp_service_account']. Vui long kiem tra lai.")
        
    creds_info = dict(st.secrets["gcp_service_account"])
    if "private_key" in creds_info and "\\n" in creds_info["private_key"]:
        creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
        
    creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
    service = build("drive", "v3", credentials=creds)
    return service

def list_files_in_folder(folder_id=None):
    """
    Lay danh sach tai lieu trong thu muc Google Drive chi dinh hoac thu muc goc duoc cau hinh.
    Tra ve danh sach cac dict gom: id, name, mimeType, webViewLink, modifiedTime.
    """
    if not folder_id:
        folder_id = st.secrets.get("app", {}).get("drive_root_folder_id", "")
        
    if not folder_id or folder_id == "YOUR_DRIVE_FOLDER_ID":
        return []
        
    try:
        service = get_drive_service()
        query = f"'{folder_id}' in parents and trashed = false"
        results = service.files().list(
            q=query,
            fields="files(id, name, mimeType, webViewLink, modifiedTime, size)",
            orderBy="folder, name"
        ).execute()
        
        return results.get("files", [])
    except Exception as e:
        st.warning(f"Loi khi truy van thu muc Google Drive: {str(e)}")
        return []
