"""
3_Occupancy_Dashboard.py — Occupancy Analytics Dashboard (Phase 6 Enhanced)

Phase 6 additions:
  - Weighted average occupancy using camera coverage_weight
  - confidence_score, model_version, processing_time_ms columns
  - Camera health status badges
  - Model metadata summary panel
"""

import streamlit as st
import pandas as pd
from components.api_client import APIClient

st.set_page_config(
    page_title="Occupancy Dashboard | Analytics",
    page_icon="📈",
    layout="wide",
)

# ── Styling ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Outfit', sans-serif; }

    .page-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding: 22px 28px; border-radius: 14px; margin-bottom: 28px;
        border: 1px solid rgba(255,255,255,0.06);
        box-shadow: 0 8px 24px rgba(0,0,0,0.25);
    }
    .header-title { color: #fff; font-size: 24px; font-weight: 700; margin: 0; }
    .header-sub   { color: #94a3b8; font-size: 14px; margin: 4px 0 0 0; }

    .occupancy-box {
        background: radial-gradient(circle at top left, rgba(30,41,59,0.85), rgba(15,23,42,0.95));
        border-radius: 18px; border: 1px solid rgba(99,102,241,0.3);
        padding: 30px; text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }
    .occupancy-val {
        font-size: 72px; font-weight: 700; margin: 10px 0;
        background: linear-gradient(135deg, #38bdf8 0%, #818cf8 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .occupancy-lbl {
        color: #94a3b8; font-size: 14px; text-transform: uppercase;
        letter-spacing: 0.12em; font-weight: 600;
    }
    .meta-row { color: #94a3b8; font-size: 13px; margin: 5px 0 0 0; }

    .badge {
        display: inline-block; padding: 3px 9px; border-radius: 6px;
        font-size: 11px; font-weight: 600; color: #fff;
    }
    .badge-online  { background: #16a34a; }
    .badge-offline { background: #dc2626; }
    .badge-error   { background: #d97706; }
    .badge-unknown { background: #475569; }

    .model-panel {
        background: rgba(30,41,59,0.5);
        border: 1px solid rgba(99,102,241,0.2);
        border-radius: 12px; padding: 16px;
        margin-top: 16px;
    }
    .model-title { color: #a5b4fc; font-size: 13px; font-weight: 600;
                   text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 10px; }
</style>
<div class="page-header">
    <h2 class="header-title">📈 Occupancy Analytics & Dashboard</h2>
    <p class="header-sub">Real-time space utilisation powered by weighted multi-camera analysis</p>
</div>
""", unsafe_allow_html=True)

# ── Data fetch ─────────────────────────────────────────────────────────────────
warehouses = APIClient.get_warehouses()

if not warehouses:
    st.info("No warehouses registered yet. Go to **Warehouses** in the sidebar to configure one.")
    st.stop()

wh_options       = {wh["name"]: wh for wh in warehouses}
selected_wh_name = st.selectbox("Select Warehouse Facility", options=list(wh_options.keys()))
selected_wh      = wh_options[selected_wh_name]
wh_id            = selected_wh["id"]

cameras        = APIClient.get_cameras(warehouse_id=wh_id)
storage_cameras = [c for c in cameras if c.get("is_storage_camera") and c.get("is_active")]
readings       = APIClient.get_occupancy(warehouse_id=wh_id)

st.write("")

# ── Latest per-camera readings ─────────────────────────────────────────────────
latest_per_camera: dict = {}
last_updated_time = None

if readings:
    df_readings = pd.DataFrame(readings)
    df_readings["captured_at"] = pd.to_datetime(df_readings["captured_at"])

    # Ensure Phase 6 columns exist (backwards compat if older readings stored)
    for col, default in [
        ("confidence_score", 1.0),
        ("processing_time_ms", 0),
        ("model_version", "1.0.0"),
    ]:
        if col not in df_readings.columns:
            df_readings[col] = default

    for cam in cameras:
        cam_id     = cam["id"]
        cam_rds    = df_readings[df_readings["camera_id"] == cam_id]
        if not cam_rds.empty:
            latest_idx  = cam_rds["captured_at"].idxmax()
            lr          = cam_rds.loc[latest_idx]
            latest_per_camera[cam_id] = {
                "occupancy":         lr["occupancy_percentage"],
                "confidence":        lr.get("confidence_score", 1.0),
                "model_version":     lr.get("model_version", "1.0.0"),
                "processing_time_ms": int(lr.get("processing_time_ms", 0)),
                "captured_at":       lr["captured_at"],
            }
            if last_updated_time is None or lr["captured_at"] > last_updated_time:
                last_updated_time = lr["captured_at"]

# ── Weighted Occupancy Calculation ─────────────────────────────────────────────
# Formula: Σ(weight_i * occupancy_i) / Σ(weight_i)
weighted_sum     = 0.0
total_weight     = 0.0
contributing     = 0

for cam in storage_cameras:
    cam_id = cam["id"]
    if cam_id in latest_per_camera:
        w  = float(cam.get("coverage_weight", 1.0))
        occ = latest_per_camera[cam_id]["occupancy"]
        weighted_sum += w * occ
        total_weight += w
        contributing += 1

warehouse_occupancy = (weighted_sum / total_weight) if total_weight > 0 else None

# Average confidence across contributing cameras
avg_confidence = None
if contributing > 0:
    avg_confidence = sum(
        latest_per_camera[c["id"]]["confidence"]
        for c in storage_cameras
        if c["id"] in latest_per_camera
    ) / contributing

# ── Main Layout ────────────────────────────────────────────────────────────────
col_main, col_detail = st.columns([1, 2])

with col_main:
    # Primary occupancy gauge card
    st.markdown('<div class="occupancy-box">', unsafe_allow_html=True)
    st.markdown('<div class="occupancy-lbl">Weighted Warehouse Occupancy</div>', unsafe_allow_html=True)

    if warehouse_occupancy is not None:
        # Colour: green < 50%, amber 50–80%, red > 80%
        color = "#22c55e" if warehouse_occupancy < 50 else ("#f59e0b" if warehouse_occupancy < 80 else "#ef4444")
        st.markdown(
            f'<div class="occupancy-val" style="background:linear-gradient(135deg,{color},#818cf8);'
            f'-webkit-background-clip:text;-webkit-text-fill-color:transparent;">'
            f'{warehouse_occupancy:.1f}%</div>',
            unsafe_allow_html=True,
        )
        st.progress(warehouse_occupancy / 100.0)
    else:
        st.markdown(
            '<div class="occupancy-val" style="font-size:28px;color:#64748b;margin:24px 0;">'
            'No Readings Yet</div>',
            unsafe_allow_html=True,
        )

    st.markdown(f"""
    <div style="margin-top:18px;text-align:left;font-size:13px;
                border-top:1px solid rgba(255,255,255,0.06);padding-top:14px;">
        <p class="meta-row">🏢 <b>Warehouse ID:</b> {wh_id}</p>
        <p class="meta-row">📍 <b>Location:</b> {selected_wh['location']}</p>
        <p class="meta-row">🎥 <b>Storage Cameras (active):</b> {len(storage_cameras)}</p>
        <p class="meta-row">⚖️ <b>Total Weight:</b> {total_weight:.1f}</p>
        <p class="meta-row">📊 <b>Avg Confidence:</b> {f"{avg_confidence:.2%}" if avg_confidence is not None else "N/A"}</p>
        <p class="meta-row">🕒 <b>Last Reading:</b> {last_updated_time.strftime('%Y-%m-%d %H:%M:%S') if last_updated_time else 'Never'}</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Model metadata panel
    if latest_per_camera:
        versions = list({v["model_version"] for v in latest_per_camera.values()})
        times_ms = [v["processing_time_ms"] for v in latest_per_camera.values()]
        avg_ms   = sum(times_ms) / len(times_ms) if times_ms else 0
        st.markdown(f"""
        <div class="model-panel">
            <div class="model-title">🤖 AI Model Metadata</div>
            <p class="meta-row">🏷 <b>Model Version(s):</b> {', '.join(versions)}</p>
            <p class="meta-row">⚡ <b>Avg Inference Time:</b> {avg_ms:.0f} ms</p>
            <p class="meta-row">🎯 <b>Engine:</b> SegFormer-B0 (simulation mode)</p>
        </div>
        """, unsafe_allow_html=True)

with col_detail:
    st.subheader("🎥 Camera Status & Readings")

    if cameras:
        camera_rows = []
        for cam in cameras:
            cam_id      = cam["id"]
            reading     = latest_per_camera.get(cam_id)
            cam_status  = cam.get("camera_status", "UNKNOWN").upper()

            if cam_status == "ONLINE":
                status_icon = "🟢 ONLINE"
            elif cam_status == "OFFLINE":
                status_icon = "🔴 OFFLINE"
            elif cam_status == "ERROR":
                status_icon = "🟠 ERROR"
            else:
                status_icon = "⚪ UNKNOWN"

            camera_rows.append({
                "Camera Name":    cam["camera_name"],
                "Type":           "💾 Storage" if cam["is_storage_camera"] else "👁 General",
                "Health":         status_icon,
                "Weight":         cam.get("coverage_weight", 1.0),
                "Occupancy":      f"{reading['occupancy']:.1f}%"    if reading else "N/A",
                "Confidence":     f"{reading['confidence']:.2%}"    if reading else "N/A",
                "Model":          reading["model_version"]           if reading else "N/A",
                "Inf. Time (ms)": reading["processing_time_ms"]     if reading else "N/A",
                "Last Capture":   reading["captured_at"].strftime("%Y-%m-%d %H:%M") if reading else "Never",
            })

        df_status = pd.DataFrame(camera_rows)
        st.dataframe(df_status, use_container_width=True, hide_index=True)
    else:
        st.info("No cameras configured for this warehouse.")

st.divider()

# ── Historical Trends ──────────────────────────────────────────────────────────
st.subheader("📈 Historical Weighted Occupancy Trend")

if readings:
    df_r  = pd.DataFrame(readings)
    df_r["captured_at"] = pd.to_datetime(df_r["captured_at"])

    storage_ids = {c["id"]: float(c.get("coverage_weight", 1.0)) for c in storage_cameras}
    df_storage  = df_r[df_r["camera_id"].isin(storage_ids)].copy()

    if not df_storage.empty:
        # Compute weighted average per timestamp group (readings batched per hourly job run)
        df_storage["weight"] = df_storage["camera_id"].map(storage_ids)
        df_storage["w_occ"]  = df_storage["weight"] * df_storage["occupancy_percentage"]

        trend = (
            df_storage.groupby("captured_at")
            .apply(lambda g: g["w_occ"].sum() / g["weight"].sum())
            .reset_index(name="Weighted Occupancy (%)")
        )
        trend = trend.rename(columns={"captured_at": "Timestamp"}).sort_values("Timestamp")

        st.line_chart(
            data=trend,
            x="Timestamp",
            y="Weighted Occupancy (%)",
            color="#6366f1",
            use_container_width=True,
        )

        # Confidence trend (if available)
        if "confidence_score" in df_storage.columns:
            conf_trend = (
                df_storage.groupby("captured_at")["confidence_score"]
                .mean()
                .reset_index(name="Avg Confidence")
                .rename(columns={"captured_at": "Timestamp"})
                .sort_values("Timestamp")
            )
            with st.expander("📊 Confidence Score Trend", expanded=False):
                st.line_chart(
                    data=conf_trend,
                    x="Timestamp",
                    y="Avg Confidence",
                    color="#22c55e",
                    use_container_width=True,
                )
    else:
        st.info("No historical readings found for active storage cameras.")
else:
    st.info(
        "No readings yet. Use **🚀 Run Occupancy Polling Job** on the Home page "
        "to trigger an immediate capture."
    )
