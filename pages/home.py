import streamlit as st
import pandas as pd
from services.sheets_service import get_records
from services.drive_service import scan_all_drive_documents
from services.audit_service import write_audit_log

# Ham hien thi cua so doc van ban truc tiep ngay tai Trang chu
@st.dialog("📖 Xem Văn Bản & Quy Trình Nhanh", width="large")
def preview_modal(doc_id, doc_name, preview_url):
    st.markdown(f"#### 📄 [{doc_id}] {doc_name}")
    if preview_url:
        st.markdown(
            f"""
            <div style="border: 1px solid #CBD5E1; border-radius: 8px; overflow: hidden; margin-top: 10px;">
                <iframe 
                    src="{preview_url}" 
                    width="100%" 
                    height="620px" 
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
    else:
        st.warning("Chưa tìm thấy liên kết tệp khả dụng trên Google Drive.")

def show_home(user_info):
    """
    Giao dien Trang chu tinh gon:
    - Da loai bo hoan toan thanh chi so khong can thiet.
    - Gan lien ket truc tiep cho tung muc trong Loi Tat Van Hanh.
    """
    # Lay danh sach file thuc te tu Drive de tao link dong
    docs = scan_all_drive_documents()
    docs_map = {d.get("Document_ID"): d for d in docs} if docs else {}

    c_left, c_right = st.columns([2.2, 1.2])

    with c_left:
        st.subheader("📢 Bảng Tin Điều Hành & An Toàn Lao Động")
        st.caption("Chỉ đạo sản xuất, lịch bảo dưỡng và an toàn ca kíp cho 2 nhà máy")
        
        try:
            announcements = get_records("Announcements")
            if announcements:
                active_announcements = [
                    a for a in announcements 
                    if str(a.get("Status", "")).strip().upper() == "ACTIVE"
                ]
                if active_announcements:
                    for item in reversed(active_announcements[-6:]):
                        date_str = item.get("Publish_Date", "")
                        title_str = item.get("Title", "Thông báo")
                        with st.expander(f"📌 [{date_str}] {title_str}", expanded=True):
                            st.write(item.get("Content", ""))
                            st.caption(
                                f"Ban hành bởi: **{item.get('Created_By', 'Ban Lãnh Đạo')}** | "
                                f"Phạm vi: **{item.get('Department', 'Toàn công ty')}**"
                            )
                else:
                    st.info("Hiện tại chưa có thông báo mới.")
            else:
                st.info("Chưa có dữ liệu bảng tin.")
        except Exception:
            st.info("Bảng tin đang kết nối máy chủ...")

    with c_right:
        st.subheader("⚡ Lối Tắt Vận Hành & Biểu Mẫu")
        st.caption("Bấm nút xem để mở văn bản trực tiếp")

        # Danh muc loi tat kem ma tai lieu thuc te trong kho Drive
        shortcuts = [
            ("QD-HSE-01", "🛡️ An toàn lao động (PPE)", "Quy định bảo hộ cá nhân xưởng luyện cán"),
            ("QD-CT-01", "⏱️ Chế độ ca kíp & Nội quy", "Quy định làm việc 3 ca 4 kíp 2 nhà máy"),
            ("BM-QA-01", "📋 Nghiệm thu chất lượng thép (MTC)", "Biên bản thử kéo, uốn kiểm định mác thép"),
            ("SOP-KV-02", "🚢 Đóng hàng container xuất khẩu", "Quy chuẩn chằng buộc (Lashing) cuộn cán nguội"),
            ("BM-DC-01", "📝 Biểu mẫu bàn giao & Đơn từ", "Đơn xin nghỉ phép, bàn giao ca kíp")
        ]

        for code, label, desc in shortcuts:
            doc_info = docs_map.get(code, {})
            p_url = doc_info.get("Drive_URL", "")
            d_name = doc_info.get("Document_Name", label)

            c_info, c_btn = st.columns([3, 1.2])
            with c_info:
                st.markdown(f"**{label}**")
                st.caption(f"{desc} (`{code}`)")
            with c_btn:
                if st.button("Xem ngay", key=f"btn_sc_{code}", use_container_width=True):
                    write_audit_log(user_info.get("Username"), "QUICK_SHORTCUT_VIEW", code, f"Xem nhanh {label}")
                    preview_modal(code, d_name, p_url)
            st.markdown("<hr style='margin: 4px 0 10px 0;'>", unsafe_allow_html=True)

        st.markdown("📞 **Đường Dây Nóng Khẩn Cấp:**")
        st.caption("• Y tế & Cấp cứu NM1 / NM2: **Ext 115**\n\n• Trực ban An toàn (HSE): **Ext 114**\n\n• IT & Hệ thống ERP: **Ext 102**")
