import streamlit as st
import pandas as pd
from components.api_client import APIClient

st.set_page_config(
    page_title="Manage Warehouses | Occupancy Platform",
    page_icon="🏭",
    layout="wide"
)

# Custom header banner
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    .page-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 25px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .header-title {
        color: #ffffff;
        font-size: 24px;
        font-weight: 700;
        margin: 0;
    }
</style>
<div class="page-header">
    <h2 class="header-title">🏭 Warehouse Management</h2>
</div>
""", unsafe_allow_html=True)

# Layout: Form and List
left_col, right_col = st.columns([1, 2])

with left_col:
    st.subheader("➕ Add New Warehouse")
    with st.form("add_warehouse_form", clear_on_submit=True):
        name = st.text_input("Warehouse Name*", placeholder="e.g. Delhi Cargo Hub")
        location = st.text_input("Location*", placeholder="e.g. Sector 18, Dwarka, Delhi")
        description = st.text_area("Description / Notes", placeholder="e.g. Storage for high-value electronics")
        
        submit_btn = st.form_submit_button("Register Warehouse", use_container_width=True)
        
        if submit_btn:
            if not name or not location:
                st.error("Please fill out all mandatory fields (*).")
            else:
                with st.spinner("Registering warehouse..."):
                    result = APIClient.create_warehouse(name, location, description)
                    if result:
                        st.success(f"Warehouse '{name}' registered successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to register warehouse. Please check backend status.")

with right_col:
    st.subheader("📋 Registered Facilities")
    warehouses = APIClient.get_warehouses()
    
    if warehouses:
        df_wh = pd.DataFrame(warehouses)
        df_wh = df_wh.rename(columns={
            "id": "Warehouse ID",
            "name": "Warehouse Name",
            "location": "Location",
            "description": "Description",
            "created_at": "Registered At"
        })
        
        # Display formatted list
        for idx, row in df_wh.iterrows():
            with st.container():
                st.markdown(f"""
                <div style="background-color: rgba(30, 41, 59, 0.5); padding: 15px; border-radius: 10px; margin-bottom: 15px; border: 1px solid rgba(255,255,255,0.05);">
                    <h4 style="margin: 0; color: #38bdf8;">{row['Warehouse Name']}</h4>
                    <p style="margin: 5px 0 0 0; font-size: 14px; color: #94a3b8;">📍 <b>Location:</b> {row['Location']}</p>
                    <p style="margin: 5px 0 0 0; font-size: 14px; color: #cbd5e1;">📝 <b>Description:</b> {row['Description'] or 'N/A'}</p>
                    <small style="color: #64748b; font-size: 12px; display: block; margin-top: 10px;">ID: {row['Warehouse ID']} | Registered at: {row['Registered At']}</small>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No warehouses registered yet. Use the registration form to add facilities.")
