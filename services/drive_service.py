import streamlit as st
import re
import io
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
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


@st.cache_data(ttl=300, show_spinner=False)
def get_file_bytes(file_id: str) -> bytes:
    """
    [PHASE 1 - VA LO HONG BAO MAT #1/#2]
    Tai noi dung file truc tiep tu Google Drive bang quyen doc cua Service Account,
    KHONG con phu thuoc vao che do chia se cong khai "Anyone with link" cua file nua.

    Ham nay chi duoc goi TU BEN TRONG cac man hinh da qua man hinh dang nhap
    (sau khi authenticate() thanh cong), nen viec xem tai lieu luon di kem xac thuc
    nguoi dung, khong con lo hong ro ri qua URL cong khai.

    Tra ve: bytes noi dung file (vi du: noi dung PDF) de nhung truc tiep vao trinh duyet
    nguoi dung dang duoi dang base64, thay vi nhung thang link Drive vao iframe.
    """
    service = get_drive_service()
    request = service.files().get_media(fileId=file_id)
    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return buffer.getvalue()


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
    #
    # [PHASE 1 - QUYET DINH 18/09] "Huong dan cong viec" duoc xac nhan la MOT DANG
    # cua Quy trinh van hanh tieu chuan (SOP) => KHONG tao Type rieng, van dung QUY_TRINH.
    # "Tai lieu ISO/QMS" duoc xac nhan la muc TAI LIEU DOC LAP => them Type = ISO_QMS.
    # Ngoai ra bo sung Type = DAO_TAO cho thu muc 20_TAI_LIEU_DAO_TAO.
    doc_type = "QUY_TRINH"
    dept = "Toàn công ty"

    if "ISO" in folder_upper or "QMS" in folder_upper:
        doc_type = "ISO_QMS"
    elif "DAO_TAO" in folder_upper:
        doc_type = "DAO_TAO"
    elif "QUY_DINH" in folder_upper or "AN_TOAN" in folder_upper:
        doc_type = "QUY_DINH"
    elif "BIEU_MAU" in folder_upper:
        doc_type = "BIEU_MAU"
    else:
        doc_type = "QUY_TRINH"

    if "AN_TOAN" in folder_upper:
        dept = "An toàn (HSE)"
    elif "SAN_XUAT" in folder_upper:
        dept = "Sản xuất"
    elif "CHAT_LUONG" in folder_upper or "ISO" in folder_upper or "QMS" in folder_upper:
        dept = "QA/QC"
    elif "KHO_VAN" in folder_upper:
        dept = "Kho vận"
    elif "KY_THUAT" in folder_upper:
        dept = "Kỹ thuật"
    elif "NHAN_SU" in folder_upper:
        dept = "Nhân sự"
    elif "DAO_TAO" in folder_upper:
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

    Luu y bao mat (Phase 1): tu day chi tra ve File_ID (khong con Drive_URL cong khai).
    Man hinh hien thi phai goi get_file_bytes(File_ID) SAU KHI nguoi dung da dang nhap
    de lay noi dung file, thay vi nhung thang link Drive vao iframe.
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
                            "Mime_Type": mime,
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
