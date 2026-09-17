import streamlit as st
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

@st.cache_resource(ttl=3600)
def get_drive_service():
    """
    Khoi tao va tra ve Google Drive API service client.
    """
    if "gcp_service_account" not in st.secrets:
        raise ValueError("Chua cau hinh st.secrets['gcp_service_account']. Vui long kiem tra lai.")
        
    creds_info = dict(st.secrets["gcp_service_account"])
    if "private_key" in creds_info and "\\n" in creds_info["private_key"]:
        creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
        
    creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
    service = build("drive", "v3", credentials=creds)
    return service

def list_portal_documents():
    """
    Lay danh sach cac tep tin va thu muc con ben trong thu muc goc METALIC_EMPLOYEE_PORTAL.
    """
    try:
        service = get_drive_service()
        folder_id = st.secrets.get("app", {}).get("drive_root_folder_id", "")
        if not folder_id:
            return []
            
        query = f"'{folder_id}' in parents and trashed = false"
        results = service.files().list(
            q=query,
            fields="files(id, name, mimeType, webViewLink, modifiedTime)",
            orderBy="folder, name",
            pageSize=100
        ).execute()
        
        return results.get("files", [])
    except Exception as e:
        st.error(f"Loi khi truy van Google Drive API: {str(e)}")
        return []

# Alias de tranh bat ky loi cu phap nao goi ten ham cu
def get_drive_files():
    return list_portal_documents()
