import streamlit as st
import pandas as pd
from services.drive_service import scan_all_drive_documents
from services.audit_service import write_audit_log

def show_documents(user_info):
    """
    Giao dien Tra cuu & Doc tai lieu tu dong 100% tu cay thu muc Google Drive (Phuong an A).
    Khong dung Google Sheet Documents, tu dong nhan dien ID that de preview.
    """
    st.markdown("### 📚 Trung Tâm Tra Cứu Quy Trình, Quy Định & Biểu Mẫu")
    st.caption("Dữ liệu được đồng bộ tự động theo thời gian thực từ Google Drive Metalic.")

    # Nut lam moi cache
    col_t, col_btn = st.columns([4, 1])
    with col_btn:
        if st.button("🔄 Làm mới dữ liệu", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    # Quet file tu Drive
    docs = scan_all_drive_documents()

    if not docs:
        st.warning("Đang kết nối kho dữ liệu Google Drive hoặc chưa tìm thấy tệp trong các thư mục...")
        return

    df = pd.DataFrame(docs)

    # Bo loc thong minh
    f_col1, f_col2, f_col3, f_col4 = st.columns([1.2, 1.2, 1.2, 2])

    with f_col1:
        type_filter = st.selectbox("Phân loại:", options=["Tất cả", "Quy định chung", "Quy trình (SOP)", "Biểu mẫu"])
    with f_col2:
        factory_filter = st.selectbox("Cơ sở áp dụng:", options=["Tất cả", "Toàn công ty", "Nhà máy 1", "Nhà máy 2"])
    with f_col3:
        dept_filter = st.selectbox("Khối / Phòng ban:", options=["Tất cả", "Toàn công ty", "Sản xuất", "QA/QC", "Kho vận", "Kỹ thuật", "An toàn (HSE)", "Nhân sự", "Hành chính"])
    with f_col4:
        search_query = st.text_input("🔍 Tìm kiếm theo tên hoặc mã:", placeholder="Nhập từ khóa...")

    # Xu ly bo loc
    if type_filter != "Tất cả":
        type_map = {"Quy định chung": "QUY_DINH", "Quy trình (SOP)": "QUY_TRINH", "Biểu mẫu": "BIEU_MAU"}
        df = df[df["Type"] == type_map.get(type_filter, "")]

    if factory_filter != "Tất cả":
        target_f = "ALL" if factory_filter == "Toàn công ty" else ("1" if "1" in factory_filter else "2")
        df = df[(df["Factory"] == target_f) | (df["Factory"] == "ALL")]

    if dept_filter != "Tất cả":
        df = df[df["Department"].str.contains(dept_filter, case=False, na=False)]

    if search_query:
        mask = df.astype(str).apply(lambda r: r.str.contains(search_query, case=False, na=False)).any(axis=1)
        df = df[mask]

    st.markdown("---")

    if not df.empty:
        st.write(f"Tìm thấy **{len(df)}** văn bản phù hợp:")
        for _, row in df.iterrows():
            doc_id = row.get("Document_ID", "---")
            doc_name = row.get("Document_Name", "")
            doc_type = row.get("Type", "")
            doc_dept = row.get("Department", "")
            doc_ver = row.get("Version", "v1.0")
            doc_factory = row.get("Factory", "ALL")
            preview_url = row.get("Drive_URL", "")
            folder_src = row.get("Folder", "")

            fac_label = "Toàn công ty" if doc_factory == "ALL" else f"Nhà máy {doc_factory}"

            with st.expander(f"📄 [{doc_id}] {doc_name} ({doc_ver})", expanded=False):
                st.markdown(f"**Phân loại:** `{doc_type}` | **Phòng ban:** `{doc_dept}` | **Phạm vi:** `{fac_label}` | **Thư mục:** `{folder_src}`")
                if preview_url:
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
                    write_audit_log(user_info.get("Username"), "VIEW_DOCUMENT", doc_id, f"Xem tai lieu: {doc_name}")
    else:
        st.info("Không có tài liệu nào khớp với tiêu chí tìm kiếm đã chọn.")
