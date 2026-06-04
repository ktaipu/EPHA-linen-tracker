import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import qrcode
import io

# 1. YOUR LIVE GOOGLE SHEET LINK
MASTER_SHEET_LINK = "https://docs.google.com/spreadsheets/d/1NTjdd-xwsI1klW6twk13gIKhOwpR0YnYgkl6Zf8rO9s/edit?gid=0#gid=0"

def load_cloud_data():
    try:
        # Streamlit official engine connection
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=MASTER_SHEET_LINK, ttl="10s")
        
        # Format names to match your spreadsheet casing perfectly
        df.columns = df.columns.str.strip().str.lower()
        return df
    except Exception as e:
        st.sidebar.error(f"⚠️ Cloud sync paused. Error: {e}")
        # Safe fallback block mapping your exact sheet structures
        fallback_data = {
            'id': [1], 'day': ['Thursday'], 'date': ['04/06/2026'], 'shift': ['AM'],
            'linen type': ['Pillow'], 'opening balance': [40], 
            'received from laundry': [4], 'sent to laundry': [5], 
            'in use': [30], 'damaged': [0], 'lost': [0], 
            'closing balance': [40], 'checked by': ['RK'], 'witness': ['RP'], 'remarks': ['1 Still in Laundry']
        }
        return pd.DataFrame(fallback_data)

# 2. STREAMLIT INTERFACE SETUP
st.set_page_config(page_title="Epha Linen Tracker", layout="wide", page_icon="🧺")
st.title("🧺 Epha Linen Tracker")
st.caption("Live Dashboard connected directly to your Google Sheet.")

df = load_cloud_data()

# Automated verification check to completely block KeyErrors
expected_cols = ['id', 'linen type', 'opening balance', 'in use', 'sent to laundry', 'received from laundry']
for col in expected_cols:
    if col not in df.columns:
        df[col] = 0 if col != 'linen type' else "Unknown"

if df.empty:
    st.warning("Google Sheet loaded successfully but no tracking rows were found.")
else:
    # 3. INTERACTIVE DATA CARDS FOR MULTIPLE STAFF
    st.header("🔄 Live Shift Tracking Status")
    
    if st.button("🔄 Sync & Refresh Staff Data"):
        st.cache_data.clear()
        st.rerun()

    for idx, row in df.iterrows():
        # Extracted cleanly using your exact structural keys
        item_id = row['id']
        linen_name = row['linen type']
        
        col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
        
        with col1:
            st.markdown(f"### **{linen_name}**")
            st.markdown(f"`Log Entry ID: {item_id}` | Date: {row.get('date', 'N/A')} ({row.get('shift', 'AM')})")
            if pd.notna(row.get('remarks')):
                st.caption(f"💬 Note: {row['remarks']}")
                
        with col2:
            st.metric("Opening Balance", row['opening balance'])
            
        with col3:
            st.number_input("In Use", min_value=0, value=int(row['in_use']), key=f"use_{idx}")
            st.number_input("Sent to Laundry", min_value=0, value=int(row['sent to laundry']), key=f"sent_{idx}")
            
        with col4:
            st.number_input("Received Laundry", min_value=0, value=int(row['received from laundry']), key=f"rec_{idx}")
            st.metric("Damaged / Lost", f"⚠️ {int(row.get('damaged', 0))} / {int(row.get('lost', 0))}")
            
        with col5:
            # Generate QR codes matching physical tags
            qr_text = f"Linen Log ID: {item_id}\nType: {linen_name}\nOpening Count: {row['opening balance']}"
            img = qrcode.make(qr_text)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            
            st.download_button(
                label="📥 Print Tag",
                data=buf.getvalue(),
                file_name=f"linen_tag_{item_id}.png",
                mime="image/png",
                key=f"qr_{idx}"
            )
        st.markdown("---")

    st.markdown(f"🔗 [Open Master Google Sheet to Add Shift Entries]({MASTER_SHEET_LINK})")
