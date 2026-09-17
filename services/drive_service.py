import streamlit as st
import re
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

@st.cache_resource(ttl=3600)
def get_drive_service():
    """
    Khoi tao Google Drive API client tu st.secrets['gcp_service_account'].
    """
    if "gcp_service_account" not in st.secrets:
        raise ValueError("Chua cau hinh st.secrets['gcp_service_account'].")
        
    creds_info = dict(st.secrets["gcp_service_account"])
    if "private_key" in creds_info and "\\n" in creds_info["private_key"]:
        creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
        
    creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
    return build("drive", "v3", credentials=creds)

def parse_filename_metadata(filename: str, parent_folder_name: str):
    """
    Tu dong boc tach thong tin tu ten file chuan:
    [MA]__[TEN TAI LIEU]__[NHA MAY]__[PHIEN BAN].pdf
    """
    # Xoa duoi file .pdf
    clean_name = re.sub(r'\.[a-zA-Z0-9]+$', '', filename).strip()
    parts = clean_name.split("__")
    
    # Gia tri mac dinh
    doc_code = "DOC-AUTO"
    doc_title = clean_name
    factory = "ALL"
    version = "v1.0"
    
    if len(parts) >= 4:
        doc_code = parts[0].strip()
        doc_title = parts[1].strip()
        factory = parts[2].strip()
        version = parts[3].strip()
    elif len(parts) == 3:
        doc_code = parts[0].strip()
        doc_title = parts[1].strip()
        factory = parts[2].strip()
    elif len(parts) == 2:
        doc_code = parts[0].strip()
        doc_title = parts[1].strip()

    # Nhan dien Nha may tu ten thu muc neu file de ALL nhung nam trong thu muc con
    folder_upper = parent_folder_name.upper()
    if "NHA_MAY_1" in folder_upper or "KHO_NHA_MAY_1" in folder_upper:
        factory = "1"
    elif "NHA_MAY_2" in folder_upper or "KHO_NHA_MAY_2" in folder_upper:
        factory = "2"

    # Tu dong nhan dien Phan loai (Type) va Phong ban tu Ten thu muc cha
    doc_type = "QUY_TRINH"
    dept = "Toàn công ty"
    
    if "QUY_DINH" in folder_upper or "AN_TOAN" in folder_upper:
        doc_type = "QUY_DINH"
    elif "BIEU_MAU" in folder_upper:
        doc_type = "BIEU_MAU"
    else:
        doc_type = "QUY_TRINH"

    if "AN_TOAN" in folder_upper:
        dept = "An toàn (HSE)"
    elif "SAN_XUAT" in folder_upper:
        dept = "Sản xuất"
    elif "CHAT_LUONG" in folder_upper:
        dept = "QA/QC"
    elif "KHO_VAN" in folder_upper:
        dept = "Kho vận"
    elif "KY_THUAT" in folder_upper:
        dept = "Kỹ thuật"
    elif "NHAN_SU" in folder_upper:
        dept = "Nhân sự"
    elif "HANH_CHINH" in folder_upper or "DUNG_CHUNG" in folder_upper:
        dept = "Hành chính"

    return {
        "Document_ID": doc_code,
        "Document_Name": doc_title,
        "Type": doc_type,
        "Department": dept,
        "Factory": factory,
        "Version": version
    }

@st.cache_data(ttl=600)
def scan_all_drive_documents():
    """
    Quet de quy tat ca cac thu muc con va tep PDF ben trong METALIC_EMPLOYEE_PORTAL.
    Co co che cache trong 10 phut de toi uu toc do tai trang.
    """
    service = get_drive_service()
    root_id = st.secrets.get("app", {}).get("drive_root_folder_id", "")
    if not root_id:
        return []

    documents = []

    def scan_folder(folder_id, folder_name="Root"):
        query = f"'{folder_id}' in parents and trashed = false"
        page_token = None
        
        while True:
            response = service.files().list(
                q=query,
                fields="nextPageToken, files(id, name, mimeType, modifiedTime)",
                pageSize=100,
                pageToken=page_token
            ).execute()
            
            for item in response.get("files", []):
                mime = item.get("mimeType")
                if mime == "application/vnd.google-apps.folder":
                    # Bo qua thu muc 00_SYSTEM de bao mat co so du lieu
                    if "00_SYSTEM" not in item.get("name", ""):
                        scan_folder(item.get("id"), item.get("name"))
                else:
                    file_name = item.get("name", "")
                    if file_name.lower().endswith((".pdf", ".xlsx", ".docx", ".doc")):
                        meta = parse_filename_metadata(file_name, folder_name)
                        documents.append({
                            "Document_ID": meta["Document_ID"],
                            "Document_Name": meta["Document_Name"],
                            "Type": meta["Type"],
                            "Department": meta["Department"],
                            "Factory": meta["Factory"],
                            "Version": meta["Version"],
                            "File_ID": item.get("id"),
                            "Drive_URL": f"https://drive.google.com/file/d/{item.get('id')}/preview",
                            "Folder": folder_name,
                            "Modified_Time": item.get("modifiedTime", "")[:10]
                        })
            
            page_token = response.get("nextPageToken", None)
            if not page_token:
                break

    try:
        scan_folder(root_id)
    except Exception as e:
        st.error(f"Lỗi quét Google Drive API: {str(e)}")

    return documents

def list_portal_documents():
    return scan_all_drive_documents()
