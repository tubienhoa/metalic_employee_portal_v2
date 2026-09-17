import streamlit as st
import pandas as pd
from services.sheets_service import get_records
from services.drive_service import scan_all_drive_documents

def show_home(user_info):
    """
    Trang chu Dashboard chuan Doanh nghiep San xuat Thep.
    Su dung st.metric goc ket hop CSS nhe, chong loi vo HTML code block.
    """
    # 1. Lay so luong van ban thuc te tu Drive
    try:
        total_docs = len(scan_all_drive_documents())
    except Exception:
        total_docs = 14

    # 2. THANH CHI SO VAN HANH & AN TOAN (HSE & OPERATIONS METRICS)
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric(
            label="🛡️ CHỈ SỐ AN TOÀN (HSE)",
            value="528 Ngày",
            delta="Không sự cố tai nạn",
            delta_color="normal"
        )
    with m2:
        st.metric(
            label="🏭 NHÀ MÁY 1 (CÁN THÉP)",
            value="Đang chạy Ca 1",
            delta="Công suất 100%",
            delta_color="normal"
        )
    with m3:
        st.metric(
            label="📦 NHÀ MÁY 2 (GIA CÔNG XK)",
            value="Đóng Container",
            delta="Đạt tiến độ tàu biển",
            delta_color="normal"
        )
    with m4:
        st.metric(
            label="📚 KHO QUY TRÌNH & SOP",
            value=f"{total_docs} Văn Bản",
            delta="Đồng bộ tự động",
            delta_color="normal"
        )

    st.markdown("---")

    # 3. NOI DUNG BANG TIN & HUONG DAN VAN HANH
    c_left, c_right = st.columns([2.3, 1.2])

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
                    for item in reversed(active_announcements[-5:]):
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
        st.subheader("⚡ Lối Tắt Vận Hành")
        st.caption("Chỉ dẫn kỹ thuật thường dùng")
        
        st.markdown(
            """
            * 🛡️ **An Toàn Lao Động:** Tuân thủ 100% đồ bảo hộ cá nhân (PPE) khi vào xưởng cán.
            * ⏱️ **Giao Ca:** Thực hiện bàn giao số liệu lò và mác thép trước 15 phút.
            * 🔍 **Kiểm Soát QA/QC:** Kiểm tra biên bản thử kéo, uốn trước khi xuất xưởng.
            * 🚢 **Logistics:** Tiêu chuẩn chằng buộc (Lashing) cuộn cán nguội container.
            """
        )
        
        st.markdown("---")
        st.markdown("📞 **Đường Dây Nóng Khẩn Cấp:**")
        st.markdown(
            """
            * Y tế & Cấp cứu NM1 / NM2: **Ext 115**
            * Trực ban An toàn (HSE): **Ext 114**
            * IT & Hệ thống ERP: **Ext 102**
            """
        )
