import streamlit as st
import pandas as pd
from components.api_client import APIClient

# Page configuration
st.set_page_config(
    page_title="Multi-Warehouse Occupancy Platform",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject Premium custom styling
st.markdown("""
<style>
    /* Global Styles */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Header Gradient Banner */
    .header-banner {
        background: linear-gradient(135deg, #1e1b4b 0%, #311042 50%, #0f172a 100%);
        padding: 30px;
        border-radius: 16px;
        margin-bottom: 25px;
        border: 1px solid rgba(99, 102, 241, 0.2);
        box-shadow: 0 10px 30px -15px rgba(0, 0, 0, 0.5);
    }
    
    .header-title {
        color: #ffffff;
        font-size: 32px;
        font-weight: 700;
        margin: 0;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.4);
    }
    
    .header-subtitle {
        color: #a5b4fc;
        font-size: 16px;
        margin-top: 5px;
        margin-bottom: 0;
        font-weight: 300;
    }
    
    /* Premium KPI Metric Cards */
    .kpi-container {
        display: flex;
        gap: 20px;
        margin-bottom: 30px;
    }
    
    .kpi-card {
        flex: 1;
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .kpi-card:hover {
        transform: translateY(-5px);
        border-color: rgba(99, 102, 241, 0.4);
        box-shadow: 0 12px 40px -10px rgba(99, 102, 241, 0.3);
        background: rgba(30, 41, 59, 0.95);
    }
    
    .kpi-value {
        font-size: 42px;
        font-weight: 700;
        background: linear-gradient(135deg, #38bdf8 0%, #818cf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 5px;
    }
    
    .kpi-label {
        font-size: 14px;
        font-weight: 600;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
</style>
""", unsafe_allow_html=True)

# Custom header banner
st.markdown("""
<div class="header-banner">
    <h1 class="header-title">🏭 Multi-Warehouse Occupancy Estimation</h1>
    <p class="header-subtitle">Production-grade real-time space utilization platform driven by surveillance streams</p>
</div>
""", unsafe_allow_html=True)

# Fetch data for stats
warehouses = APIClient.get_warehouses()
cameras = APIClient.get_cameras()
active_cams = [c for c in cameras if c.get("is_active", False)]
storage_cams = [c for c in cameras if c.get("is_storage_camera", False)]

# Grid metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value">{len(warehouses)}</div>
        <div class="kpi-label">Warehouses</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value">{len(cameras)}</div>
        <div class="kpi-label">Total Cameras</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value">{len(active_cams)}</div>
        <div class="kpi-label">Active Cameras</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value">{"Healthy" if len(warehouses) > 0 else "Pending Setup"}</div>
        <div class="kpi-label">Pipeline Status</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")
st.write("")

# Main Panel
left_col, right_col = st.columns([2, 1])

with left_col:
    st.subheader("📋 Registered Warehouses")
    if warehouses:
        df_wh = pd.DataFrame(warehouses)
        # Format columns for display
        df_wh = df_wh.rename(columns={
            "id": "Warehouse ID",
            "name": "Warehouse Name",
            "location": "Location",
            "description": "Description",
            "created_at": "Registered At"
        })
        st.dataframe(df_wh, use_container_width=True, hide_index=True)
    else:
        st.info("No warehouses registered yet. Go to **Warehouses** in the sidebar to add your first facility!")

    st.subheader("🎥 Cameras Overview")
    if cameras:
        df_cam = pd.DataFrame(cameras)
        df_cam = df_cam.rename(columns={
            "id": "Camera ID",
            "warehouse_id": "Warehouse ID",
            "camera_name": "Camera Name",
            "rtsp_url": "RTSP URL",
            "is_storage_camera": "Storage Area?",
            "is_active": "Active?",
            "created_at": "Added At"
        })
        st.dataframe(df_cam, use_container_width=True, hide_index=True)
    else:
        st.info("No cameras configured yet. Go to **Cameras** in the sidebar to register CCTV streams.")

with right_col:
    st.subheader("⚡ Quick Actions")
    st.write("Trigger pipeline validation on-demand to test the hourly snapshot engine:")
    
    if st.button("🚀 Run Occupancy Polling Job", use_container_width=True):
        if not active_cams:
            st.warning("Cannot run polling job. There are no registered active cameras.")
        else:
            with st.spinner("Scheduler triggering polling job..."):
                success = APIClient.trigger_polling()
                if success:
                    st.success("Successfully executed occupancy polling! Refresh the **Occupancy Dashboard** to see the new metrics.")
                else:
                    st.error("Failed to trigger polling job. Ensure backend is running.")
                    
    st.write("---")
    st.subheader("💡 System Architecture")
    st.markdown("""
    This platform implements a modular architecture:
    1. **Registry**: Register warehouses & CCTV streams without changing code.
    2. **Scheduler**: Hourly trigger queries active streams.
    3. **RTSP Layer**: Captures live frames from CP Plus cameras.
    4. **Inference Engine**: Abstracted SegFormer semantic segmentation model calculates percentage.
    5. **Database**: High-performance PostgreSQL stores history.
    """)
