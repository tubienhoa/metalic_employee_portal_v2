import streamlit as st
import pandas as pd
from services.drive_service import list_files_in_folder
from services.sheets_service import get_records
from services.audit_service import write_audit_log

def show_documents(user_info):
    """
    Giao dien tra cuu tai lieu, quy trinh, bieu mau noi bo.
    Ket hop danh muc trong Sheet Documents va Google Drive Storage.
    """
    st.subheader("📁 Kho Tài Liệu & Quy Trình Nội Bộ")
    st.caption("Tra cứu văn bản, quy chuẩn sản xuất thép xuất khẩu, biểu mẫu hành chính và đào tạo.")

    tab1, tab2 = st.tabs(["📑 Danh Mục Hồ Sơ & Biểu Mẫu", "☁️ Thư Mục Google Drive"])

    with tab1:
        st.markdown("##### 📄 Danh mục tài liệu theo phân quyền")
        docs = get_records("Documents")
        if docs:
            user_role = str(user_info.get("Role", "EMPLOYEE")).upper()
            filtered_docs = []
            for d in docs:
                access_role = str(d.get("Access_Role", "EMPLOYEE")).upper()
                # Neu access_role la EMPLOYEE hoac quyen user la ADMIN thi deu xem duoc
                if access_role in ["EMPLOYEE", "ALL", ""] or access_role in user_role or "ADMIN" in user_role:
                    filtered_docs.append(d)

            if filtered_docs:
                df = pd.DataFrame(filtered_docs)
                # Chon loc cac cot quan trong de hien thi
                display_cols = [col for col in ["Document_ID", "Document_Name", "Category", "Department", "Drive_URL"] if col in df.columns]
                
                # Tim kiem nhanh
                search_query = st.text_input("🔍 Tìm kiếm tài liệu theo tên hoặc danh mục:", placeholder="Nhập từ khóa...")
                if search_query:
                    mask = df["Document_Name"].astype(str).str.contains(search_query, case=False, na=False) | \
                           df["Category"].astype(str).str.contains(search_query, case=False, na=False)
                    df = df[mask]
                
                st.dataframe(df[display_cols], use_container_width=True, hide_index=True)
                
                # Ghi nhat ky
                write_audit_log(user_info.get("Username"), "VIEW_DOCUMENTS_CATALOG", "Documents", "Xem danh muc tai lieu")
            else:
                st.info("Hiện không có tài liệu nào thuộc phạm vi phân quyền của bạn.")
        else:
            st.info("Chưa có danh mục tài liệu được cập nhật trong hệ thống.")

    with tab2:
        st.markdown("##### 📂 Khai thác trực tiếp từ Google Drive")
        try:
            files = list_files_in_folder()
            if files:
                st.write(f"Tìm thấy **{len(files)}** tệp/thư mục trong bộ lưu trữ:")
                for f in files:
                    col_icon, col_info, col_btn = st.columns([1, 6, 2])
                    with col_icon:
                        if f.get("mimeType") == "application/vnd.google-apps.folder":
                            st.markdown("📁 **Thư mục**")
                        else:
                            st.markdown("📄 **Tệp**")
                    with col_info:
                        st.markdown(f"**{f.get('name')}**")
                        st.caption(f"Cập nhật: {f.get('modifiedTime', 'N/A')[:10]}")
                    with col_btn:
                        link = f.get("webViewLink", "#")
                        st.link_button("Mở tài liệu ↗", url=link, use_container_width=True)
                
                write_audit_log(user_info.get("Username"), "VIEW_DRIVE_FOLDER", "Google Drive", "Xem danh sach Drive")
            else:
                st.info("Thư mục Google Drive hiện đang trống hoặc chưa được cấu hình 'drive_root_folder_id'.")
        except Exception as e:
            st.error("Không thể kết nối trực tiếp đến Google Drive. Vui lòng kiểm tra lại quyền truy cập của Service Account.")
