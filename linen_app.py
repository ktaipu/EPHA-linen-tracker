import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import qrcode
import io

# 1. LIVE MASTER GOOGLE SHEET LINK
MASTER_SHEET_LINK = "https://docs.google.com/spreadsheets/d/1NTjdd-xwsI1klW6twk13gIKhOwpR0YnYgkl6Zf8rO9s/edit?gid=0#gid=0"

def load_cloud_data():
    try:
        # Securely connect to your Google Sheet database
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=MASTER_SHEET_LINK, ttl="1s") # Low TTL forces real-time updates
        
        # Standardize column headers: lowercase and remove leading/trailing spaces
        df.columns = df.columns.str.strip().str.lower()
        return df
    except Exception as e:
        st.sidebar.error(f"⚠️ Cloud sync paused. Error: {e}")
        # Universal emergency fallback table structure
        fallback_data = {
            'id': [1], 'day': ['Thursday'], 'date': ['04/06/2026'], 'shift': ['AM'],
            'linen type': ['Pillow'], 'opening balance': [40], 
            'received from laundry': [0], 'sent to laundry': [0], 
            'in use': [0], 'damaged': [0], 'lost': [0], 
            'closing balance': [40], 'checked by': ['RK'], 'witness': ['RP'], 'remarks': ['1 Still in Laundry']
        }
        return pd.DataFrame(fallback_data)

# 2. STREAMLIT INTERFACE SETUP
st.set_page_config(page_title="Epha Linen Tracker", layout="wide", page_icon="🧺")
st.title("🧺 Epha Linen Tracker")
st.caption("Live Dashboard connected directly to your Google Sheet.")

# Fetch the columns and rows
df = load_cloud_data()

if df.empty:
    st.warning("Google Sheet loaded successfully but no tracking rows were found.")
else:
    st.header("🔄 Live Shift Tracking Status")
    
    # Force Clear Cache Button to instantly fetch updates
    if st.button("🔄 Sync & Clear Old Cache"):
        st.cache_data.clear()
        st.rerun()

    for idx, row in df.iterrows():
        # HELPER: Try multiple formatting names to locate your sheet's column
        item_id = row.get('id', idx + 1)
        
        # Tries variations of linen name column titles safely
        linen_name = row.get('linen type', row.get('linentype', row.get('linen_type', 'Unknown Item')))
        
        # Ultra-Safe extraction system: Default to 0 instead of crashing if names mismatch
        val_opening = int(row.get('opening balance', row.get('openingbalance', row.get('opening_balance', 0))))
        val_in_use = int(row.get('in use', row.get('inuse', row.get('in_use', 0))))
        val_sent = int(row.get('sent to laundry', row.get('senttolaundry', row.get('sent_to_laundry', 0))))
        val_received = int(row.get('received from laundry', row.get('receivedfromlaundry', row.get('received_from_laundry', 0))))
        val_damaged = int(row.get('damaged', 0))
        val_lost = int(row.get('lost', 0))
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.markdown(f"### **{linen_name}**")
            st.markdown(f"`Log Entry ID: {item_id}` | Date: {row.get('date', 'N/A')} ({row.get('shift', 'AM')})")
            if pd.notna(row.get('remarks')):
                st.caption(f"💬 Note: {row['remarks']}")
                
        with col2:
            st.metric("Opening Balance", val_opening)
            
        with col3:
            st.number_input("In Use", min_value=0, value=val_in_use, key=f"use_{idx}")
            st.number_input("Sent to Laundry", min_value=0, value=val_sent, key=f"sent_{idx}")
            
        with col4:
            st.number_input("Received Laundry", min_value=0, value=val_received, key=f"rec_{idx}")
            st.metric("Damaged / Lost", f"⚠️ {val_damaged} / {val_lost}")
            
        with col5:
            # Generate clean item tracking codes for sorting shelves
            qr_text = f"Linen Log ID: {item_id}\nType: {linen_name}\nOpening Count: {val_opening}"
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
