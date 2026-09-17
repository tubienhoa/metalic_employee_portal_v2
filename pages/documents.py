import streamlit as st
import pandas as pd
from services.sheets_service import get_records
from services.drive_service import list_portal_documents
from services.audit_service import write_audit_log

def show_documents(user_info):
    """
    Giao dien Tra cuu Kho tai lieu va Bieu mau noi bo Metalic Viet Nam.
    Tich hop bo loc theo Nha may, Phong ban va Tim kiem truc tiep tu Drive.
    """
    st.markdown("### 📁 Kho Tài Liệu & Quy Trình Nội Bộ")
    st.caption("Tra cứu văn bản, quy chuẩn sản xuất thép xuất khẩu, biểu mẫu hành chính và đào tạo.")

    tab1, tab2 = st.tabs(["📑 Danh Mục Hồ Sơ & Biểu Mẫu", "☁️ Thư Mục Google Drive"])

    user_factory = str(user_info.get("Factory", "1")).strip()
    user_role = str(user_info.get("Role", "")).upper()

    with tab1:
        st.markdown("#### 📄 Danh mục tài liệu theo phân quyền")
        
        # Bo loc thong minh
        col_f1, col_f2, col_f3 = st.columns([1, 1, 2])
        with col_f1:
            factory_filter = st.selectbox(
                "Cơ sở áp dụng:",
                options=["Tất cả", "Toàn công ty", "Nhà máy 1", "Nhà máy 2"],
                index=0
            )
        with col_f2:
            dept_filter = st.selectbox(
                "Khối / Phòng ban:",
                options=["Tất cả", "Sản xuất", "QA/QC", "Kho vận", "Kỹ thuật", "An toàn (HSE)", "Nhân sự", "Hành chính"]
            )
        with col_f3:
            search_query = st.text_input("🔍 Tìm kiếm tài liệu theo tên hoặc mã:", placeholder="Nhập từ khóa...")

        docs = get_records("Documents")
        if docs:
            df = pd.DataFrame(docs)

            # Loc theo quyen han (neu can che tai lieu noi bo)
            if "Role_Required" in df.columns and user_role not in ["SYSTEM_ADMIN", "SUPER_ADMIN"]:
                df = df[df["Role_Required"].isna() | (df["Role_Required"] == "") | (df["Role_Required"] == "ALL") | (df["Role_Required"] == user_role)]

            # Loc theo Nha may
            if "Factory" in df.columns and factory_filter != "Tất cả":
                target_f = "ALL" if factory_filter == "Toàn công ty" else ("1" if "1" in factory_filter else "2")
                df = df[(df["Factory"].astype(str) == target_f) | (df["Factory"].astype(str) == "ALL") | (df["Factory"].isna())]

            # Loc theo Phong ban
            if "Department" in df.columns and dept_filter != "Tất cả":
                df = df[df["Department"].astype(str).str.contains(dept_filter, case=False, na=False)]

            # Loc theo tu khoa
            if search_query and not df.empty:
                mask = df.astype(str).apply(lambda row: row.str.contains(search_query, case=False, na=False)).any(axis=1)
                df = df[mask]

            if not df.empty:
                # Chon cac cot hien thi than thien
                display_cols = [c for c in ["Document_ID", "Document_Name", "Category", "Department", "Factory", "Drive_URL"] if c in df.columns]
                st.dataframe(df[display_cols], use_container_width=True, hide_index=True)
            else:
                st.info("Không tìm thấy tài liệu phù hợp với bộ lọc hiện tại.")
        else:
            st.info("Chưa có dữ liệu trong danh mục tài liệu.")

        write_audit_log(user_info.get("Username"), "VIEW_DOCUMENTS_CATALOG", "Documents", "Xem danh muc tai lieu noi bo")

    with tab2:
        st.markdown("#### 📂 Khai thác trực tiếp từ Google Drive")
        try:
            items = list_portal_documents()
            if items:
                st.write(f"Tìm thấy **{len(items)}** tệp/thư mục trong bộ lưu trữ:")
                for item in items:
                    icon = "📁 Thư mục" if item.get("mimeType") == "application/vnd.google-apps.folder" else "📄 Tệp tin"
                    with st.container():
                        col_info, col_btn = st.columns([3, 1])
                        with col_info:
                            st.markdown(f"**{icon}** &nbsp; `{item.get('name')}`")
                            st.caption(f"Cập nhật: {item.get('modifiedTime', '')[:10]}")
                        with col_btn:
                            st.link_button("Mở tài liệu ↗", item.get("webViewLink", "https://drive.google.com"), use_container_width=True)
                        st.divider()
            else:
                st.info("Thư mục Google Drive hiện chưa có tệp hoặc chưa được cấp quyền chia sẻ.")
        except Exception as e:
            st.error(f"Không thể tải danh sách Google Drive: {str(e)}")

        write_audit_log(user_info.get("Username"), "VIEW_DRIVE_FOLDER", "Google Drive", "Xem danh sach thu muc Drive")
