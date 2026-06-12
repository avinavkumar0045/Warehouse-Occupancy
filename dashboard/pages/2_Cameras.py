"""
2_Cameras.py — Camera Management Dashboard Page (Phase 6 Enhanced)

Phase 6 additions:
  - Shows camera_status (ONLINE/OFFLINE/ERROR) with colour badges
  - Shows last_successful_capture timestamp
  - Shows coverage_weight and notes
  - create_camera form now includes coverage_weight and notes inputs
"""

import streamlit as st
import pandas as pd
from components.api_client import APIClient

st.set_page_config(
    page_title="Manage Cameras | Occupancy Platform",
    page_icon="🎥",
    layout="wide",
)

# ── Styling ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Outfit', sans-serif; }

    .page-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding: 22px 28px;
        border-radius: 14px;
        margin-bottom: 28px;
        border: 1px solid rgba(255,255,255,0.06);
        box-shadow: 0 8px 24px rgba(0,0,0,0.25);
    }
    .header-title { color: #fff; font-size: 24px; font-weight: 700; margin: 0; }
    .header-sub   { color: #94a3b8; font-size: 14px; margin: 4px 0 0 0; }

    .cam-card {
        background: rgba(30, 41, 59, 0.45);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 12px;
        padding: 14px 18px;
        margin-bottom: 12px;
        transition: border-color 0.2s;
    }
    .cam-card:hover { border-color: rgba(99,102,241,0.4); }
    .cam-name  { color: #f8fafc; font-size: 15px; font-weight: 600; margin: 0; }
    .cam-url   { color: #94a3b8; font-size: 11px; margin-top: 3px; word-break: break-all; }
    .cam-meta  { color: #cbd5e1; font-size: 12px; margin-top: 6px; }

    .badge {
        display: inline-block;
        padding: 3px 9px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 600;
        color: #fff;
    }
    .badge-online  { background: #16a34a; }
    .badge-offline { background: #dc2626; }
    .badge-error   { background: #d97706; }
    .badge-unknown { background: #475569; }
    .badge-active  { background: #2563eb; }
    .badge-inactive{ background: #475569; }
</style>
<div class="page-header">
    <h2 class="header-title">🎥 CCTV Camera Management</h2>
    <p class="header-sub">Register and monitor CP Plus CCTV streams across all warehouse facilities</p>
</div>
""", unsafe_allow_html=True)

# ── Data fetch ─────────────────────────────────────────────────────────────────
warehouses = APIClient.get_warehouses()
cameras    = APIClient.get_cameras()

left_col, right_col = st.columns([1, 2])

# ── LEFT: Registration Form ────────────────────────────────────────────────────
with left_col:
    st.subheader("➕ Register Camera Stream")

    if not warehouses:
        st.warning("⚠️ No warehouses registered. Please create a warehouse first.")
    else:
        wh_options = {wh["name"]: wh["id"] for wh in warehouses}
        selected_wh_name = st.selectbox("Warehouse Facility *", options=list(wh_options.keys()))
        selected_wh_id   = wh_options[selected_wh_name]

        with st.form("register_camera_form", clear_on_submit=True):
            camera_name = st.text_input(
                "Camera Name *", placeholder="e.g. Storage Row A North"
            )
            rtsp_url = st.text_input(
                "RTSP Stream URL *",
                placeholder="rtsp://admin:password@192.168.1.100:554/stream1",
            )

            col_a, col_b = st.columns(2)
            with col_a:
                is_storage_camera = st.checkbox(
                    "Monitors Storage Area?",
                    value=True,
                    help="If checked, this camera feeds into occupancy calculations.",
                )
            with col_b:
                is_active = st.checkbox(
                    "Active / Polling?",
                    value=True,
                    help="If checked, the hourly scheduler will poll this camera.",
                )

            coverage_weight = st.slider(
                "Coverage Weight",
                min_value=0.1,
                max_value=5.0,
                value=1.0,
                step=0.1,
                help=(
                    "Relative weight for weighted occupancy averaging. "
                    "A camera covering a larger area should have a higher weight."
                ),
            )
            notes = st.text_area(
                "Notes (optional)",
                placeholder="e.g. Covers north-west quadrant of racking aisle 3",
                height=80,
            )

            submit_btn = st.form_submit_button("Register Camera", use_container_width=True)

            if submit_btn:
                if not camera_name or not rtsp_url:
                    st.error("Please fill out all mandatory fields (*).")
                else:
                    with st.spinner("Registering camera stream..."):
                        result = APIClient.create_camera(
                            warehouse_id=selected_wh_id,
                            camera_name=camera_name,
                            rtsp_url=rtsp_url,
                            is_storage_camera=is_storage_camera,
                            is_active=is_active,
                            coverage_weight=coverage_weight,
                            notes=notes if notes else None,
                        )
                        if result:
                            st.success(
                                f"✅ Camera '{camera_name}' registered under '{selected_wh_name}'!"
                            )
                            st.rerun()
                        else:
                            st.error("Failed to register camera. Check backend logs.")

# ── RIGHT: Camera Cards ────────────────────────────────────────────────────────
with right_col:
    st.subheader("📋 Configured CCTV Streams")

    if cameras:
        wh_lookup = {wh["id"]: wh["name"] for wh in warehouses}
        df_cam = pd.DataFrame(cameras)

        for wh_id, group in df_cam.groupby("warehouse_id"):
            wh_name = wh_lookup.get(wh_id, f"Warehouse {wh_id}")
            st.markdown(f"### 🏢 {wh_name}")

            for _, row in group.iterrows():
                # Determine status badge
                cam_status = row.get("camera_status", "UNKNOWN").upper()
                if cam_status == "ONLINE":
                    badge_cls, badge_lbl = "badge-online",  "● ONLINE"
                elif cam_status == "OFFLINE":
                    badge_cls, badge_lbl = "badge-offline", "● OFFLINE"
                elif cam_status == "ERROR":
                    badge_cls, badge_lbl = "badge-error",   "⚠ ERROR"
                else:
                    badge_cls, badge_lbl = "badge-unknown", "● UNKNOWN"

                active_cls  = "badge-active"   if row["is_active"] else "badge-inactive"
                active_lbl  = "Polling Active" if row["is_active"] else "Inactive"
                storage_ico = "📥 Storage"    if row["is_storage_camera"] else "👁️ General"

                last_cap = row.get("last_successful_capture") or "Never"
                weight   = row.get("coverage_weight", 1.0)
                notes_v  = row.get("notes") or "—"
                roi_set  = "✅ Set" if row.get("roi_polygon") else "Not configured"

                st.markdown(f"""
                <div class="cam-card">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                        <div>
                            <p class="cam-name">{row['camera_name']}</p>
                            <code class="cam-url">{row['rtsp_url']}</code>
                        </div>
                        <div style="text-align:right; white-space:nowrap; margin-left:12px;">
                            <span class="badge {badge_cls}">{badge_lbl}</span><br>
                            <span class="badge {active_cls}" style="margin-top:5px;">{active_lbl}</span>
                        </div>
                    </div>
                    <div class="cam-meta" style="margin-top:10px; display:grid; grid-template-columns:1fr 1fr; gap:4px;">
                        <span>{storage_ico}</span>
                        <span>⚖️ Weight: <b>{weight}</b></span>
                        <span>🕒 Last Capture: <b>{last_cap}</b></span>
                        <span>🗺 ROI: <b>{roi_set}</b></span>
                        <span style="grid-column:span 2;">📝 Notes: {notes_v}</span>
                        <span style="color:#475569; font-size:11px;">ID: {row['id']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No CCTV cameras configured yet. Use the form to register your first camera stream.")
