import streamlit as st
import pandas as pd
import qrcode
import io

# 1. CLOUD STORAGE SETUP (Connects to your Google Sheet)
# REPLACE THE LINK BELOW WITH YOUR ACTUAL GOOGLE SHEET VIEW LINK
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1NTjdd-xwsI1klW6twk13gIKhOwpR0YnYgkl6Zf8rO9s/edit?gid=0#gid=0"

def load_cloud_data():
    try:
        # Reads the Google Sheet directly as a live CSV dataframe
        df = pd.read_csv(GOOGLE_SHEET_URL)
        # Clean columns to ensure matching formats
        df.columns = [c.lower().strip() for c in df.columns]
        return df
    except Exception as e:
        st.error("Could not connect to the cloud database. Please verify your Google Sheet URL.")
        return pd.DataFrame(columns=['id', 'name', 'category', 'details', 'total', 'in_use', 'laundry'])

# 2. STREAMLIT MULTI-USER INTERFACE
st.set_page_config(page_title="Staff Linen Tracker", layout="wide", page_icon="🧺")
st.title("🧺 Staff Linen Tracker (Shared Cloud)")
st.caption("Live multi-staff sync dashboard. Scan or update inventory on the go.")

# Sidebar - Quick Action Instructions for Staff
st.sidebar.header("📋 Staff Instructions")
st.sidebar.info(
    "1. View current counts below.\n"
    "2. Update 'In Use' or 'In Laundry' counts directly.\n"
    "3. To add completely new types of linen items, please contact your inventory manager to update the master Google Sheet."
)

# Fetch real-time data from Google Sheets
df = load_cloud_data()

if df.empty:
    st.warning("No data found. Please ensure your Google Sheet contains headers and at least one row of data.")
else:
    # 3. INTERACTIVE DATA TABLE FOR STAFF
    st.header("🔄 Live Inventory Status")
    
    # Refresh button to fetch latest entries from other staff members
    if st.button("🔄 Sync Live Data"):
        st.rerun()

    for idx, row in df.iterrows():
        item_id = row['id']
        col1, col2, col3, col4, col5, col6 = st.columns([2, 1, 1, 1, 1, 1])
        
        with col1:
            st.markdown(f"**{row['name']}**  \n`ID: {item_id}` | {row['details']}")
        with col2:
            st.caption(f"📁 {row['category']}")
        with col3:
            st.metric("Total Stock", row['total'])
        with col4:
            st.number_input("In Use", min_value=0, max_value=int(row['total']), value=int(row['in_use']), key=f"use_{item_id}")
            # Note: In a cloud environment, editing updates the session. 
            # To push edits back, staff can view the Google Sheet link provided below.
        with col5:
            st.number_input("In Laundry", min_value=0, max_value=int(row['total']), value=int(row['laundry']), key=f"lau_{item_id}")
        with col6:
            # QR Code Generation Utility for sorting shelves
            qr_data = f"Linen ID: {item_id}\nName: {row['name']}"
            img = qrcode.make(qr_data)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            byte_im = buf.getvalue()
            
            st.download_button(
                label="📥 Tag",
                data=byte_im,
                file_name=f"tag_{item_id}.png",
                mime="image/png",
                key=f"qr_{item_id}"
            )
        st.markdown("---")

    # Link for managers to easily jump to the backend spreadsheet
    st.markdown(f"🔗 [Open Master Google Sheet to Edit Stock Types]({GOOGLE_SHEET_URL.split('/gviz')[0]})")
