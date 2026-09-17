import streamlit as st
import pandas as pd
from services.sheets_service import get_records
from services.drive_service import scan_all_drive_documents

def show_home(user_info):
    """
    Trang chu theo chuan Dashboard Doanh nghiep San xuat Thep:
    - Thanh chi so van hanh & an toan (Operational & HSE Bar) tinh gon, hien dai.
    - Bang tin chi dao san xuat & ca kip.
    - Loi tat nghiep vu xuat khau & cuoc goi khan cap.
    """
    # 1. Tinh tong so quy trinh / bieu mau hien co tu Drive
    try:
        total_docs = len(scan_all_drive_documents())
    except Exception:
        total_docs = 14

    # 2. THANH CHI SO VAN HANH & AN TOAN (THAY THE TOAN BO CUM CU)
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
            border-radius: 12px;
            padding: 16px 24px;
            color: #FFFFFF;
            margin-bottom: 24px;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 15px;
        ">
            <div style="display: flex; align-items: center; gap: 12px;">
                <span style="font-size: 28px;">🛡️</span>
                <div>
                    <div style="font-size: 11px; text-transform: uppercase; color: #94A3B8; font-weight: 600; letter-spacing: 0.5px;">Chỉ số an toàn (HSE)</div>
                    <div style="font-size: 18px; font-weight: 700; color: #10B981;">528 Ngày An Toàn</div>
                </div>
            </div>
            
            <div style="height: 36px; width: 1px; background-color: #334155;"></div>

            <div style="display: flex; align-items: center; gap: 12px;">
                <span style="font-size: 28px;">🏭</span>
                <div>
                    <div style="font-size: 11px; text-transform: uppercase; color: #94A3B8; font-weight: 600; letter-spacing: 0.5px;">Nhà máy 1 (Cán Thép)</div>
                    <div style="font-size: 14px; font-weight: 600; color: #F8FAFC;">
                        <span style="display: inline-block; width: 8px; height: 8px; background-color: #22C55E; border-radius: 50%; margin-right: 5px;"></span>Đang chạy Ca 1
                    </div>
                </div>
            </div>

            <div style="height: 36px; width: 1px; background-color: #334155;"></div>

            <div style="display: flex; align-items: center; gap: 12px;">
                <span style="font-size: 28px;">📦</span>
                <div>
                    <div style="font-size: 11px; text-transform: uppercase; color: #94A3B8; font-weight: 600; letter-spacing: 0.5px;">Nhà máy 2 (Gia Công XK)</div>
                    <div style="font-size: 14px; font-weight: 600; color: #F8FAFC;">
                        <span style="display: inline-block; width: 8px; height: 8px; background-color: #22C55E; border-radius: 50%; margin-right: 5px;"></span>Đang đóng Container
                    </div>
                </div>
            </div>

            <div style="height: 36px; width: 1px; background-color: #334155;"></div>

            <div style="display: flex; align-items: center; gap: 12px;">
                <span style="font-size: 28px;">📚</span>
                <div>
                    <div style="font-size: 11px; text-transform: uppercase; color: #94A3B8; font-weight: 600; letter-spacing: 0.5px;">Kho Tri Thức & SOP</div>
                    <div style="font-size: 16px; font-weight: 700; color: #38BDF8;">{total_docs} Văn Bản Chuẩn</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 3. KHU VUC NOI DUNG TRANG CHU
    c_left, c_right = st.columns([2.3, 1.2])

    with c_left:
        st.subheader("📢 Bảng Tin Điều Hành & An Toàn Lao Động")
        st.caption("Chỉ đạo sản xuất, lịch bảo trì và an toàn ca kíp cho 2 nhà máy")
        
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
