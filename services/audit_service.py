import datetime
from services.sheets_service import append_record

def write_audit_log(username, action, target="", detail=""):
    """
    Ghi nhat ky he thong (Audit Log) vao worksheet 'Audit_Log'.
    Cac truong: Timestamp, Username, Action, Target, Detail.
    Dam bao neu co loi thi ung dung khong bi dung hoan toan.
    """
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record = [
            str(timestamp),
            str(username),
            str(action),
            str(target),
            str(detail)
        ]
        # Goi append_record de ghi dong vao sheet Audit_Log
        append_record("Audit_Log", record)
    except Exception as e:
        # Ghi log noi bo ra console, khong raise exception de tranh gián doan luong ung dung
        print(f"[AUDIT LOG ERROR] Khong the ghi log: {str(e)}")
