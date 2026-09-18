import streamlit as st
import base64
from services.sheets_service import get_records
from services.drive_service import scan_all_drive_documents, get_file_bytes
from services.audit_service import write_audit_log

@st.dialog("📖 Trình Xem Tài Liệu Nội Bộ", width="large")
def preview_modal(doc_id, doc_name, file_id):
    st.markdown(f"### 📄 [{doc_id}] {doc_name}")
    if not file_id:
        st.warning("Không tìm thấy tệp tương ứng.")
        return

    # [PHASE 1 - VA LO HONG BAO MAT] Giong documents.py: lay noi dung file qua
    # Service Account sau khi da dang nhap, khong con nhung link Drive cong khai.
    try:
        with st.spinner("Đang tải tài liệu..."):
            file_bytes = get_file_bytes(file_id)
        b64_data = base64.b64encode(file_bytes).decode("utf-8")
        st.markdown(
            f"""
            <div style="border: 1px solid #E2E8F0; border-radius: 10px; overflow: hidden; margin-top: 10px;">
                <iframe src="data:application/pdf;base64,{b64_data}" width="100%" height="650px" style="border: none;"></iframe>
            </div>
            <div style="font-size: 12px; color: #94A3B8; margin-top: 8px;">* Chế độ xem an toàn: Không hỗ trợ tải xuống.</div>
            """,
            unsafe_allow_html=True
        )
    except Exception as e:
        st.error(f"Không thể tải nội dung tài liệu: {str(e)}")

def show_home(user_info):
    docs = scan_all_drive_documents()
    docs_map = {d.get("Document_ID"): d for d in docs} if docs else {}

    col_main, col_side = st.columns([2.2, 1.1], gap="large")

    with col_main:
        st.markdown(
            """
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <span style="font-size: 18px; font-weight: 700; color: #0F172A;">Thông Báo & Chỉ Đạo Nội Bộ</span>
                <span style="font-size: 12px; color: #64748B;">Cập nhật từ Ban Lãnh Đạo</span>
            </div>
            """,
            unsafe_allow_html=True
        )

        try:
            announcements = get_records("Announcements")
            active_list = [a for a in announcements if str(a.get("Status", "")).upper() == "ACTIVE"] if announcements else []

            # [PHASE 1] Loc thong bao theo Nha may cua nguoi xem (giu nguyen thong
            # bao "Toan cong ty" / khong ghi ro nha may cho moi nguoi deu thay).
            user_factory = str(user_info.get("Factory", "")).strip()
            if user_factory and user_factory.upper() not in ("ALL", ""):
                def _matches_factory(item):
                    scope = str(item.get("Department", "")).strip()
                    # Truong Department cua Announcements hien dang luu ca pham vi
                    # Nha may/Phong ban dang tu do (vi du: "Toàn công ty"); chi loai
                    # bo khi ghi ro dich danh mot nha may khac voi nguoi xem.
                    if f"Nhà máy {user_factory}" in scope or "Toàn công ty" in scope or not scope:
                        return True
                    if "Nhà máy" in scope and f"Nhà máy {user_factory}" not in scope:
                        return False
                    return True
                active_list = [a for a in active_list if _matches_factory(a)]

            if active_list:
                for item in reversed(active_list[-5:]):
                    st.markdown(
                        f"""
                        <div class="portal-card">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                                <span style="background: #F1F5F9; color: #475569; font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 4px;">{item.get('Publish_Date', '')}</span>
                                <span style="font-size: 12px; color: #64748B;">Phạm vi: <b>{item.get('Department', 'Toàn công ty')}</b></span>
                            </div>
                            <div style="font-size: 15px; font-weight: 600; color: #0F172A; margin-bottom: 6px;">{item.get('Title', 'Thông báo')}</div>
                            <div style="font-size: 13px; color: #475569; line-height: 1.5;">{item.get('Content', '')}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            else:
                st.info("Chưa có thông báo nào.")
        except Exception:
            st.info("Đang nạp bảng tin...")

    with col_side:
        st.markdown(
            """
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <span style="font-size: 18px; font-weight: 700; color: #0F172A;">Lối Tắt Vận Hành</span>
            </div>
            """,
            unsafe_allow_html=True
        )

        shortcuts = [
            ("QD-HSE-01", "🛡️ An toàn lao động (PPE)", "Quy định bảo hộ bắt buộc"),
            ("QD-CT-01", "⏱️ Ca kíp & Kỷ luật", "Nội quy 3 ca 4 kíp NM1 & NM2"),
            ("BM-QA-01", "📋 Nghiệm thu chất lượng thép", "Biên bản thử kéo mác thép MTC"),
            ("SOP-KV-02", "🚢 Đóng hàng container XK", "Tiêu chuẩn chằng buộc (Lashing)"),
            ("BM-DC-01", "📝 Biểu mẫu bàn giao & Nghỉ phép", "Đơn từ hành chính dùng chung")
        ]

        for code, label, desc in shortcuts:
            doc_info = docs_map.get(code, {})
            p_file_id = doc_info.get("File_ID", "")
            d_name = doc_info.get("Document_Name", label)

            st.markdown(
                f"""
                <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px 14px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-size: 13px; font-weight: 600; color: #0F172A;">{label}</div>
                        <div style="font-size: 11px; color: #64748B;">{desc}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            if st.button("Mở đọc văn bản", key=f"btn_card_{code}", use_container_width=True):
                write_audit_log(user_info.get("Username"), "SHORTCUT_CLICK", code, f"Xem {label}")
                preview_modal(code, d_name, p_file_id)

        st.markdown(
            """
            <div class="portal-card" style="margin-top: 15px; background: #F8FAFC;">
                <div style="font-weight: 600; font-size: 13px; color: #0F172A; margin-bottom: 6px;">📞 Đường Dây Nóng Khẩn Cấp</div>
                <div style="font-size: 12px; color: #475569; line-height: 1.6;">
                    • Cấp cứu y tế: <b>Ext 115</b><br>
                    • Trực an toàn HSE: <b>Ext 114</b><br>
                    • Hỗ trợ IT / ERP: <b>Ext 102</b>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
