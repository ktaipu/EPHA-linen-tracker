import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import qrcode
import io
from datetime import datetime

# 1. LIVE MASTER GOOGLE SHEET LINK
MASTER_SHEET_LINK = "https://docs.google.com/spreadsheets/d/1NTjdd-xwsI1klW6twk13gIKhOwpR0YnYgkl6Zf8rO9s/edit?gid=0#gid=0"

def load_cloud_data():
    try:
        # Securely connect to your Google Sheet database
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=MASTER_SHEET_LINK, ttl="2s")
        df.columns = df.columns.str.strip().str.lower()
        return df
    except Exception as e:
        st.sidebar.error(f"⚠️ Cloud sync paused. Using local storage fallback.")
        # Local state fallback mechanism
        if 'fallback_db' not in st.session_state:
            st.session_state.fallback_db = pd.DataFrame([{
                'id': 1, 'day': 'Thursday', 'date': '2026-06-04', 'shift': 'Night',
                'linen type': 'Pillow', 'opening balance': 40, 'received from laundry': 10,
                'sent to laundry': 5, 'in use': 30, 'damaged': 1, 'lost': 0,
                'closing balance': 44, 'checked by': 'RK', 'witness': 'RP', 'remarks': '1 Still in Laundry'
            }])
        return st.session_state.fallback_db

def append_cloud_data(new_row_dict):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        # Pull current state, append, and upload
        df = conn.read(spreadsheet=MASTER_SHEET_LINK)
        new_df = pd.concat([df, pd.DataFrame([new_row_dict])], ignore_index=True)
        conn.update(spreadsheet=MASTER_SHEET_LINK, data=new_df)
        st.cache_data.clear()
        return True
    except Exception as e:
        # If cloud update fails, save to fallback session state
        if 'fallback_db' in st.session_state:
            st.session_state.fallback_db = pd.concat([st.session_state.fallback_db, pd.DataFrame([new_row_dict])], ignore_index=True)
        return False

# 2. STREAMLIT INTERFACE SETUP
st.set_page_config(page_title="Epha Linen Tracker", layout="wide", page_icon="🧺")
st.title("🧺 Epha Linen Tracker")
st.caption("Advanced Shift Log, Live Calculator & Mobile Data Submittal Hub.")

df = load_cloud_data()

# 3. SIDEBAR: ANDROID-OPTIMIZED DATA ENTRY FORM
st.sidebar.header("📝 Submit New Shift Check")
with st.sidebar.form("shift_log_form", clear_on_submit=True):
    # Form input fields using your specific options
    f_linen = st.selectbox("Linen Type", ["Pillow", "Pillow case", "Bed Spreadsheet", "Blanket", "Macintosh"])
    f_shift = st.selectbox("Shift", ["AM", "PM", "Night"])
    f_date = st.date_input("Date Logged", datetime.now())
    f_day = f_date.strftime("%A")
    
    st.markdown("---")
    f_opening = st.number_input("Opening Balance Count", min_value=0, value=0, step=1)
    f_in_use = st.number_input("Current Pieces In Use", min_value=0, value=0, step=1)
    f_sent = st.number_input("Sent to Laundry", min_value=0, value=0, step=1)
    f_rec = st.number_input("Received from Laundry", min_value=0, value=0, step=1)
    f_damaged = st.number_input("Damaged Pieces", min_value=0, value=0, step=1)
    f_lost = st.number_input("Lost Pieces", min_value=0, value=0, step=1)
    
    st.markdown("---")
    f_checker = st.text_input("Checked By (Initials)", placeholder="e.g., RK").upper().strip()
    f_witness = st.text_input("Witness (Initials)", placeholder="e.g., RP").upper().strip()
    f_remarks = st.text_input("Remarks / Notes", placeholder="e.g., 1 Still in Laundry")
    
    # 4. LIVE AUTOMATIC MATHEMATICAL CALCULATOR
    # Formula: Closing = Opening + Received - Sent - Damaged - Lost
    f_closing = f_opening + f_rec - f_sent - f_damaged - f_lost
    st.sidebar.metric("Calculated Closing Balance", f_closing)
    
    submit_btn = st.form_submit_button("🚀 Submit Entry to Cloud")
    
    if submit_btn:
        next_id = int(df['id'].max() + 1) if not df.empty and 'id' in df.columns else 1
        new_entry = {
            'Id': next_id, 'Day': f_day, 'Date': f_date.strftime("%d/%m/%Y"), 'Shift': f_shift,
            'Linen Type': f_linen, 'Opening Balance': f_opening, 'Received From Laundry': f_rec,
            'Sent To Laundry': f_sent, 'In Use': f_in_use, 'Damaged': f_damaged, 'Lost': f_lost,
            'Closing Balance': f_closing, 'Checked By': f_checker, 'Witness': f_witness, 'Remarks': f_remarks
        }
        
        if append_cloud_data(new_entry):
            st.sidebar.success("✅ Entry recorded directly to Google Sheet!")
            st.rerun()
        else:
            st.sidebar.warning("💾 Saved to local offline display (Sheet permission pending).")
            st.rerun()

# 5. HEADER BAR: SEARCH AND FILTER TOOLS
st.header("🔍 Filter Log Entries")
search_col1, search_col2, search_col3 = st.columns(3)

with search_col1:
    search_initials = st.text_input("Filter by Inspector Initials (e.g., RK)", "").upper().strip()
with search_col2:
    filter_linen = st.multiselect("Filter by Linen Type", ["Pillow", "Pillow case", "Bed Spreadsheet", "Blanket", "Macintosh"])
with search_col3:
    filter_shift = st.multiselect("Filter by Shift", ["AM", "PM", "Night"])

# Apply staff filters to data frame dynamically
filtered_df = df.copy()
if search_initials:
    checker_col = 'checked by' if 'checked by' in filtered_df.columns else 'checkedby'
    if checker_col in filtered_df.columns:
        filtered_df = filtered_df[filtered_df[checker_col].astype(str).str.contains(search_initials, na=False)]
if filter_linen:
    type_col = 'linen type' if 'linen type' in filtered_df.columns else 'linentype'
    if type_col in filtered_df.columns:
        filtered_df = filtered_df[filtered_df[type_col].isin(filter_linen)]
if filter_shift:
    if 'shift' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['shift'].isin(filter_shift)]

# 6. MAIN DISPLAY: INTERACTIVE LOG CARDS
st.markdown("---")
st.subheader("🔄 Active Shift Inventory Logs")

if st.button("🔄 Sync & Clear Old Cache"):
    st.cache_data.clear()
    st.rerun()

if filtered_df.empty:
    st.info("No matching shift records found for the selected filters.")
else:
    for idx, row in filtered_df.iterrows():
        # Clean extraction fallbacks
        item_id = row.get('id', idx + 1)
        linen_name = row.get('linen type', row.get('linentype', 'Unknown Item'))
        
        # Real-time math engine variables
        val_opening = int(row.get('opening balance', row.get('openingbalance', 0)))
        val_in_use = int(row.get('in use', row.get('inuse', 0)))
        val_sent = int(row.get('sent to laundry', row.get('senttolaundry', 0)))
        val_received = int(row.get('received from laundry', row.get('receivedfromlaundry', 0)))
        val_damaged = int(row.get('damaged', 0))
        val_lost = int(row.get('lost', 0))
        
        # Automatic math update on data feed card
        val_closing = val_opening + val_received - val_sent - val_damaged - val_lost
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.markdown(f"### **{linen_name}**")
            st.markdown(f"`Log Entry ID: {item_id}` | **Shift: {row.get('shift', 'N/A')}**")
            st.caption(f"📅 Date: {row.get('date', 'N/A')} ({row.get('day', 'N/A')})")
            st.markdown(f"✍️ **By:** {row.get('checked by', row.get('checkedby', 'N/A'))} | **Wit:** {row.get('witness', 'N/A')}")
                
        with col2:
            st.metric("Opening Balance", val_opening)
            st.metric("Closing Balance", val_closing, delta=int(val_closing - val_opening))
            
        with col3:
            st.number_input("In Use", min_value=0, value=val_in_use, key=f"use_{idx}_{item_id}")
            st.number_input("Sent to Laundry", min_value=0, value=val_sent, key=f"sent_{idx}_{item_id}")
            
        with col4:
            st.number_input("Received Laundry", min_value=0, value=val_received, key=f"rec_{idx}_{item_id}")
            st.metric("Damaged / Lost Stock", f"⚠️ {val_damaged} / {val_lost}")
            if pd.notna(row.get('remarks')) and str(row['remarks']).strip() != "":
                st.caption(f"💬 **Note:** {row['remarks']}")
            
        with col5:
            # Generate QR tracking tokens matching row profiles
            qr_text = f"Epha Linen ID: {item_id}\nType: {linen_name}\nClosing Stock: {val_closing}\nChecked By: {row.get('checked by', 'N/A')}"
            img = qrcode.make(qr_text)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            
            st.download_button(
                label="📥 Print Tag",
                data=buf.getvalue(),
                file_name=f"epha_tag_{item_id}.png",
                mime="image/png",
                key=f"qr_{idx}_{item_id}"
            )
        st.markdown("---")

st.markdown(f"🔗 [Open Master Google Sheet to View Spreadsheet Raw Columns]({MASTER_SHEET_LINK})")
