import streamlit as st
import pandas as pd
import re
from services.sheets_service import get_records
from services.drive_service import list_portal_documents
from services.audit_service import write_audit_log

def convert_drive_url_to_preview(url: str) -> str:
    """
    Chuyen doi bat ky link Google Drive (view/edit/share) 
    sang dinh dang Preview nhung truc tiep tren web, khong cho tai xuong.
    """
    if not url or not isinstance(url, str):
        return ""
    # Trich xuat File ID bang bieu thuc chinh quy
    match = re.search(r'/d/([a-zA-Z0-9_-]+)', url)
    if not match:
        match = re.search(r'id=([a-zA-Z0-9_-]+)', url)
    
    if match:
        file_id = match.group(1)
        # Link preview nhung an thanh cong cu tai xuong
        return f"https://drive.google.com/file/d/{file_id}/preview"
    return url

def show_documents(user_info):
    """
    Giao dien Tra cuu & Doc tai lieu truc tiep tren Web (Khong cho phep tai ve).
    Chi Quản trị viên moi co quyen truy cap tab cau truc Google Drive.
    """
    st.markdown("### 📚 Trung Tâm Tra Cứu Văn Bản, Quy Trình & Biểu Mẫu")
    st.caption("Xem trực tiếp các quy định chung, quy trình nghiệp vụ (SOP) và biểu mẫu công ty Metalic.")

    user_role = str(user_info.get("Role", "")).upper()
    is_admin = user_role in ["SYSTEM_ADMIN", "SUPER_ADMIN", "HR_ADMIN"]

    # Phan quyen: Chi Admin moi co tab xem truc tiep cay thu muc Drive
    if is_admin:
        tab_list = ["📖 Tra Cứu & Đọc Văn Bản", "🔒 Quản Trị Google Drive (Chỉ Quản Trị Viên)"]
    else:
        tab_list = ["📖 Tra Cứu & Đọc Văn Bản"]

    tabs = st.tabs(tab_list)

    # TAB 1: TRA CUU & DOC TAI LIEU TAI CHO
    with tabs[0]:
        # Bo loc thong minh 3 chieu
        f_col1, f_col2, f_col3, f_col4 = st.columns([1.2, 1.2, 1.2, 2])
        
        with f_col1:
            type_filter = st.selectbox(
                "Phân loại:",
                options=["Tất cả", "Quy định chung (Policy)", "Quy trình nghiệp vụ (SOP)", "Biểu mẫu (Template)"]
            )
        with f_col2:
            factory_filter = st.selectbox(
                "Cơ sở áp dụng:",
                options=["Tất cả", "Toàn công ty", "Nhà máy 1", "Nhà máy 2"]
            )
        with f_col3:
            dept_filter = st.selectbox(
                "Phòng ban / Khối:",
                options=["Tất cả", "Chung", "Sản xuất", "QA/QC", "Kho vận", "Kỹ thuật", "An toàn (HSE)", "Nhân sự"]
            )
        with f_col4:
            search_query = st.text_input("🔍 Tìm kiếm theo tên hoặc mã số hiệu:", placeholder="Nhập từ khóa...")

        docs = get_records("Documents")
        
        if docs:
            df = pd.DataFrame(docs)

            # 1. Loc van ban con hieu luc (neu khong phai Admin)
            if "Status" in df.columns and not is_admin:
                df = df[df["Status"].astype(str).str.upper() == "HIEU_LUC"]

            # 2. Loc theo Loai tai lieu
            if type_filter != "Tất cả" and "Type" in df.columns:
                type_map = {
                    "Quy định chung (Policy)": "QUY_DINH",
                    "Quy trình nghiệp vụ (SOP)": "QUY_TRINH",
                    "Biểu mẫu (Template)": "BIEU_MAU"
                }
                selected_type = type_map.get(type_filter, "")
                df = df[df["Type"].astype(str).str.upper() == selected_type]

            # 3. Loc theo Nha may
            if factory_filter != "Tất cả" and "Factory" in df.columns:
                target_f = "ALL" if factory_filter == "Toàn công ty" else ("1" if "1" in factory_filter else "2")
                df = df[(df["Factory"].astype(str) == target_f) | (df["Factory"].astype(str) == "ALL") | (df["Factory"].isna())]

            # 4. Loc theo Phong ban
            if dept_filter != "Tất cả" and "Department" in df.columns:
                df = df[df["Department"].astype(str).str.contains(dept_filter, case=False, na=False)]

            # 5. Loc theo tu khoa tim kiem
            if search_query and not df.empty:
                mask = df.astype(str).apply(lambda row: row.str.contains(search_query, case=False, na=False)).any(axis=1)
                df = df[mask]

            st.markdown("---")

            if not df.empty:
                st.write(f"Tìm thấy **{len(df)}** văn bản phù hợp:")
                
                # Trinh bay danh sach dang the (Cards) de nhung trinh doc tai cho
                for _, row in df.iterrows():
                    doc_id = row.get("Document_ID", "---")
                    doc_name = row.get("Document_Name", "Văn bản chưa đặt tên")
                    doc_type = row.get("Type", "QUY_DINH")
                    doc_dept = row.get("Department", "Toàn công ty")
                    doc_ver = row.get("Version", "v1.0")
                    doc_factory = row.get("Factory", "ALL")
                    raw_url = str(row.get("Drive_URL", "")).strip()

                    factory_label = "Toàn công ty" if doc_factory == "ALL" else f"Nhà máy {doc_factory}"
                    
                    with st.expander(f"📄 [{doc_id}] {doc_name} ({doc_ver})", expanded=False):
                        st.markdown(
                            f"**Loại:** `{doc_type}` | **Phòng ban:** `{doc_dept}` | **Phạm vi:** `{factory_label}`"
                        )
                        
                        if raw_url and ("drive.google.com" in raw_url):
                            preview_url = convert_drive_url_to_preview(raw_url)
                            
                            # Nhúng khung doc tai cho, chan menu context / chan download
                            st.markdown(
                                f"""
                                <div style="border: 1px solid #CBD5E1; border-radius: 8px; overflow: hidden; margin-top: 10px;">
                                    <iframe 
                                        src="{preview_url}" 
                                        width="100%" 
                                        height="650px" 
                                        allow="autoplay"
                                        style="border: none;">
                                    </iframe>
                                </div>
                                <p style="color: #64748B; font-size: 12px; margin-top: 5px;">
                                    * Chế độ đọc bảo mật: Tài liệu chỉ xem nội bộ, không cho phép tải xuống.
                                </p>
                                """,
                                unsafe_allow_html=True
                            )
                            # Ghi log doc tai lieu
                            write_audit_log(user_info.get("Username"), "PREVIEW_DOCUMENT", doc_id, f"Doc truc tiep van ban: {doc_name}")
                        else:
                            st.warning("Văn bản này chưa được quản trị viên gắn link xem hợp lệ trên hệ thống.")
            else:
                st.info("Không tìm thấy tài liệu nào khớp với tiêu chí tìm kiếm.")
        else:
            st.info("Chưa có cơ sở dữ liệu tài liệu.")

    # TAB 2: KHAI THAC GOOGLE DRIVE (CHI HIEN THI KHI LA ADMIN)
    if is_admin:
        with tabs[1]:
            st.markdown("#### 🛠️ Khu vực quản lý cấu trúc thư mục Google Drive (Admin Only)")
            st.warning("Lưu ý: Khu vực này chỉ hiển thị cho Quản trị viên để kiểm tra và lấy liên kết tài liệu. Nhân viên thông thường không nhìn thấy tab này.")
            
            try:
                items = list_portal_documents()
                if items:
                    st.write(f"Tìm thấy **{len(items)}** thư mục/tệp tin quản lý trên Drive:")
                    for item in items:
                        icon = "📁 Thư mục" if item.get("mimeType") == "application/vnd.google-apps.folder" else "📄 Tệp"
                        c_info, c_btn = st.columns([3, 1])
                        with c_info:
                            st.markdown(f"**{icon}** &nbsp; `{item.get('name')}`")
                            st.caption(f"ID: `{item.get('id')}` | Cập nhật: {item.get('modifiedTime', '')[:10]}")
                        with c_btn:
                            st.link_button("Mở trên Drive ↗", item.get("webViewLink", "https://drive.google.com"), use_container_width=True)
                        st.divider()
                else:
                    st.info("Không tìm thấy tệp hoặc thư mục nào.")
            except Exception as e:
                st.error(f"Lỗi truy cập Drive: {str(e)}")
