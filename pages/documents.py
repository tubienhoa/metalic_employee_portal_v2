import streamlit as st
import pandas as pd
from services.drive_service import scan_all_drive_documents
from services.audit_service import write_audit_log

@st.dialog("📖 Xem Chi Tiết Tài Liệu", width="large")
def preview_modal(doc_id, doc_name, preview_url):
    st.markdown(f"### 📄 [{doc_id}] {doc_name}")
    if preview_url:
        st.markdown(
            f"""
            <div style="border: 1px solid #E2E8F0; border-radius: 10px; overflow: hidden; margin-top: 10px;">
                <iframe src="{preview_url}" width="100%" height="650px" style="border: none;"></iframe>
            </div>
            <div style="font-size: 12px; color: #94A3B8; margin-top: 8px;">* Chế độ đọc bảo mật: Tài liệu chỉ xem nội bộ, không cho phép tải xuống.</div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.warning("Liên kết xem không khả dụng.")

def show_documents(user_info):
    c_head, c_btn = st.columns([4, 1])
    with c_head:
        st.markdown(
            """
            <div style="font-size: 20px; font-weight: 700; color: #0F172A; margin-bottom: 2px;">Kho Tri Thức & Quy Chuẩn Doanh Nghiệp</div>
            <div style="font-size: 13px; color: #64748B;">Tra cứu toàn bộ quy định chung, quy trình nghiệp vụ (SOP) và biểu mẫu công ty</div>
            """,
            unsafe_allow_html=True
        )
    with c_btn:
        if st.button("🔄 Đồng bộ Drive", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    docs = scan_all_drive_documents()
    if not docs:
        st.info("Đang kết nối kho tài liệu Google Drive...")
        return

    df = pd.DataFrame(docs)

    # THANH BO LOC GON GANG
    f1, f2, f3, f4 = st.columns([1.2, 1.2, 1.2, 2])
    with f1:
        type_filter = st.selectbox("Phân loại", ["Tất cả", "Quy định", "Quy trình (SOP)", "Biểu mẫu"])
    with f2:
        factory_filter = st.selectbox("Cơ sở", ["Tất cả", "Toàn công ty", "Nhà máy 1", "Nhà máy 2"])
    with f3:
        dept_filter = st.selectbox("Phòng ban", ["Tất cả", "Sản xuất", "QA/QC", "Kho vận", "Kỹ thuật", "An toàn (HSE)", "Nhân sự", "Hành chính"])
    with f4:
        search_query = st.text_input("Tìm kiếm", placeholder="Nhập tên hoặc mã văn bản...")

    # Xu ly loc
    if type_filter != "Tất cả":
        type_map = {"Quy định": "QUY_DINH", "Quy trình (SOP)": "QUY_TRINH", "Biểu mẫu": "BIEU_MAU"}
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
    st.markdown(f"<div style='font-size: 13px; color: #64748B; margin-bottom: 15px;'>Tìm thấy <b>{len(df)}</b> tài liệu hợp lệ:</div>", unsafe_allow_html=True)

    # HIEN THI TAI LIEU DANG THE CARD CAO CAP
    for _, row in df.iterrows():
        doc_id = row.get("Document_ID", "---")
        doc_name = row.get("Document_Name", "")
        doc_type = row.get("Type", "QUY_TRINH")
        doc_dept = row.get("Department", "")
        doc_ver = row.get("Version", "v1.0")
        doc_factory = row.get("Factory", "ALL")
        preview_url = row.get("Drive_URL", "")

        # Badges mau pastel theo Loai
        badge_bg = "#EFF6FF" if doc_type == "QUY_TRINH" else ("#ECFDF5" if doc_type == "QUY_DINH" else "#FFFBEB")
        badge_text = "#1E40AF" if doc_type == "QUY_TRINH" else ("#065F46" if doc_type == "QUY_DINH" else "#92400E")
        fac_text = "Toàn công ty" if doc_factory == "ALL" else f"Nhà máy {doc_factory}"

        c_info, c_action = st.columns([4, 1])
        with c_info:
            st.markdown(
                f"""
                <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 4px;">
                    <span style="font-weight: 700; font-size: 14px; color: #0F172A;">{doc_id}</span>
                    <span style="background: {badge_bg}; color: {badge_text}; font-size: 11px; font-weight: 600; padding: 1px 7px; border-radius: 5px;">{doc_type}</span>
                    <span style="background: #F1F5F9; color: #475569; font-size: 11px; font-weight: 500; padding: 1px 7px; border-radius: 5px;">{fac_text}</span>
                    <span style="color: #94A3B8; font-size: 11px;">{doc_ver}</span>
                </div>
                <div style="font-size: 14px; font-weight: 500; color: #334155; margin-bottom: 4px;">{doc_name}</div>
                <div style="font-size: 12px; color: #64748B;">Khối / Bộ phận: {doc_dept}</div>
                """,
                unsafe_allow_html=True
            )
        with c_action:
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            if st.button("Đọc tài liệu", key=f"view_{doc_id}", use_container_width=True):
                write_audit_log(user_info.get("Username"), "VIEW_DOCUMENT", doc_id, f"Xem {doc_name}")
                preview_modal(doc_id, doc_name, preview_url)
        
        st.markdown("<hr style='margin: 12px 0; border: 0; border-top: 1px solid #F1F5F9;'>", unsafe_allow_html=True)
