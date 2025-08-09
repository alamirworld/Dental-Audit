# app.py
import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import json
import io
import re
import numpy as np
from datetime import datetime, timedelta
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest

# ------------------- إعداد كلمات السر -------------------
# Site-wide login: admin
SITE_LOGIN_PASSWORD_HASH = hashlib.md5("admin".encode()).hexdigest()
# Upload rules password: password
ADMIN_PASSWORD_HASH = hashlib.md5("password".encode()).hexdigest()
# Delete rules password: delete
DELETE_PASSWORD_HASH = hashlib.md5("delete".encode()).hexdigest()

# ------------------- إعداد قاعدة البيانات -------------------
DB_NAME = "dental_rules.db"

# ------------------- واجهة المستخدم و CSS/JS -------------------
def setup_ui():
    st.set_page_config(
        page_title="Dental Audit System",
        layout="wide",
        page_icon="🦷",
        initial_sidebar_state="expanded"
    )

    # DataTables + style injection (CSS + JS via CDN)
    datatables_css_js = """
    <!-- DataTables & jQuery -->
    <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.13.4/css/dataTables.bootstrap5.min.css"/>
    <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/buttons/2.3.6/css/buttons.bootstrap5.min.css"/>
    <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/responsive/2.4.1/css/responsive.bootstrap5.min.css"/>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.4/js/jquery.dataTables.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.4/js/dataTables.bootstrap5.min.js"></script>
    <script src="https://cdn.datatables.net/buttons/2.3.6/js/dataTables.buttons.min.js"></script>
    <script src="https://cdn.datatables.net/buttons/2.3.6/js/buttons.bootstrap5.min.js"></script>
    <script src="https://cdn.datatables.net/buttons/2.3.6/js/buttons.html5.min.js"></script>
    <script src="https://cdn.datatables.net/buttons/2.3.6/js/buttons.print.min.js"></script>
    <script src="https://cdn.datatables.net/responsive/2.4.1/js/dataTables.responsive.min.js"></script>
    <script src="https://cdn.datatables.net/responsive/2.4.1/js/responsive.bootstrap5.min.js"></script>
    <style>
    /* Base container */
    .stApp, .main, .block-container, #root > div {
        max-width: 100vw !important;
        padding: 0 !important;
        overflow-x: auto !important;
        background-color: #5b65ac !important;
    }
    
    /* Ensure all sections have the same background */
    section.main > div, section[data-testid="stSidebar"] > div {
        background-color: #5b65ac !important;
    }
    
    /* Main content area */
    .main .block-container {
        padding: 1rem 2% !important;
        max-width: 100% !important;
        margin: 0 !important;
        min-width: 100% !important;
    }
    
    /* Table container */
    .dataTables_wrapper {
        width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
        display: block;
        position: relative;
        clear: both;
    }
    
    /* Force full width on the table */
    .dataTable {
        width: 100% !important;
        table-layout: auto !important;
        border-collapse: collapse !important;
    }
    
    /* Table container */
    .dataTables_scroll {
        width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
        position: relative;
        clear: both;
    }
    
    /* Table header and body */
    .dataTables_scrollHead,
    .dataTables_scrollBody {
        width: 100% !important;
        position: relative;
        overflow: hidden;
    }
    
    /* Inner scroll container */
    .dataTables_scrollHeadInner {
        width: auto !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    
    /* Main table */
    .dataTable {
        width: 100% !important;
        margin: 0 !important;
        border-collapse: collapse !important;
        table-layout: auto !important;
    }
    
    /* Table cells */
    .dataTable thead th,
    .dataTable tbody td {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        padding: 8px 12px !important;
        vertical-align: middle;
        border: 1px solid #dee2e6;
    }
    
    /* Header cells */
    .dataTable thead th {
        background-color: #f8f9fa;
        font-weight: 600;
    }
    
    /* Column width handling */
    .dataTable th,
    .dataTable td {
        min-width: 120px !important;
        max-width: 300px !important;
    }
    
    /* Scroll body */
    .dataTables_scrollBody {
        overflow-x: auto !important;
        overflow-y: auto !important;
        -webkit-overflow-scrolling: touch;
    }
    
    /* Fix for header alignment */
    .dataTables_scrollHead {
        overflow: hidden !important;
        border-bottom: 1px solid #dee2e6 !important;
    }
    
    /* Responsive adjustments */
    @media screen and (max-width: 992px) {
        .main .block-container {
            padding: 1rem 0.5rem !important;
        }
        
        .dataTable th,
        .dataTable td {
            padding: 6px 8px !important;
            font-size: 0.9em;
        }
    }
    
    /* Fix for header overlap */
    .stApp {
        overflow-x: auto;
    }
    
    /* Ensure proper spacing between elements */
    .stAlert, .stMarkdown, .stDataFrame {
        margin-bottom: 1.5rem !important;
    }
    
    /* Fix for sticky header */
    .dataTables_scrollHead {
        position: sticky !important;
        top: 0;
        z-index: 100;
        background: white;
    }
    
    /* Ensure proper scrolling */
    .dataTables_scrollBody {
        overflow-x: auto !important;
        max-height: none !important;
    }
    
    /* Fix for button container */
    .dt-buttons {
        margin-bottom: 1rem !important;
    }
    
    /* Make sure the table header is properly aligned */
    .dataTable thead th {
        position: relative;
        background-image: none !important;
    }
    
    /* Fix for RTL text alignment */
    [dir='rtl'] .dataTable th,
    [dir='rtl'] .dataTable td {
        text-align: right;
    }
    
    /* Ensure proper spacing in the sidebar */
    .stSidebar {
        padding: 1rem !important;
    }
    
    /* Fix for Streamlit's markdown headers */
    .stMarkdown h1,
    .stMarkdown h2,
    .stMarkdown h3,
    .stMarkdown h4,
    .stMarkdown h5,
    .stMarkdown h6 {
        margin-top: 1.5em !important;
        margin-bottom: 0.5em !important;
    }
    
    /* Ensure proper spacing for form elements */
    .stTextInput,
    .stTextArea,
    .stSelectbox,
    .stNumberInput,
    .stDateInput,
    .stFileUploader {
        margin-bottom: 1rem !important;
    }
    
    /* Fix for buttons */
    .stButton > button {
        margin: 0.5rem 0;
    }
    
    /* Responsive adjustments */
    @media (max-width: 1200px) {
        .main .block-container {
            padding: 1rem 0.5rem !important;
        }
        
        .dataTable {
            font-size: 0.9em;
        }
        
        .dataTable td, .dataTable th {
            padding: 6px 8px !important;
        }
        
        .dataTables_wrapper .dataTables_length,
        .dataTables_wrapper .dataTables_filter,
        .dataTables_wrapper .dataTables_info,
        .dataTables_wrapper .dataTables_paginate {
            text-align: right !important;
            float: none !important;
            margin-bottom: 0.5rem;
        }
    }
    </style>
    
    <style>
    :root {
        --primary: #3a7bd5; /* Blue */
        --secondary: #00d2ff; /* Cyan */
        --success: #2ecc71;
        --danger: #ff3b30;
        --warning: #f39c12;
        --info: #3498db;
        --light: #f8f9fa;
        --dark: #2c3e50;
        --sidebar-bg: #f8fafc;
    }
    
    * { 
        font-family: 'Segoe UI', 'Tahoma', sans-serif !important; 
        box-sizing: border-box;
    }
    
    /* Main app styling */
    .stApp { 
        background-color: #f8fafc; 
        color: var(--dark); 
        padding: 0;
    }
    
    /* Header */
    .data-header {
        background: linear-gradient(135deg, var(--primary), var(--secondary));
        padding: 1.5rem;
        border-radius: 0.5rem;
        color: white;
        margin: 0 0 1.5rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        position: relative;
        overflow: hidden;
    }
    
    .data-header::before {
        content: '';
        position: absolute;
        top: 0;
        right: 0;
        bottom: 0;
        left: 0;
        background: url("data:image/svg+xml,%3Csvg width='100' height='100' viewBox='0 0 100 100' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M11 18c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zm48 25c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zm-43-7c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zm63 31c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zM34 90c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zm56-76c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zM12 86c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm28-65c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm23-11c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm-6 60c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm29 22c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zM32 63c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm57-13c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm-9-21c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM60 91c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM35 41c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM12 60c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2z' fill='%23ffffff' fill-opacity='0.1' fill-rule='evenodd'/%3E%3C/svg%3E");
        opacity: 0.1;
    }
    
    .data-header h2 { 
        margin: 0; 
        font-size: 1.75rem; 
        font-weight: 700;
        position: relative;
        display: inline-block;
        padding-bottom: 0.5rem;
    }
    
    .data-header h2::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        width: 60px;
        height: 3px;
        background: rgba(255, 255, 255, 0.7);
        border-radius: 3px;
    }
    
    .data-header p { 
        margin: 0.75rem 0 0; 
        opacity: 0.9; 
        font-size: 1rem;
        max-width: 80%;
    }

    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, var(--primary), var(--secondary)) !important;
        color: white !important;
        border-radius: 8px !important;
        padding: 0.5rem 1.25rem !important;
        font-weight: 600 !important;
        border: none !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease !important;
    }
    
    .stButton>button:hover { 
        transform: translateY(-2px) !important; 
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15) !important;
    }

    /* File uploader */
    .stFileUploader > div { 
        border: 2px dashed var(--primary) !important; 
        background-color: rgba(58, 123, 213, 0.05) !important; 
        padding: 1.5rem !important; 
        border-radius: 0.5rem !important;
        transition: all 0.3s ease;
    }
    
    .stFileUploader > div:hover {
        background-color: rgba(58, 123, 213, 0.1) !important;
        border-color: var(--secondary) !important;
    }

    /* DataTables styling */
    .dataTables_wrapper {
        padding: 0 !important;
        margin: 1rem 0 2rem 0 !important;
    }
    
    .dataTables_scroll {
        border-radius: 0.5rem;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }
    
    table.dataTable {
        width: 100% !important;
        margin: 0 !important;
        border-collapse: separate !important;
        border-spacing: 0;
    }
    
    table.dataTable thead th {
        background: linear-gradient(135deg, var(--primary), var(--secondary)) !important;
        color: white !important;
        font-weight: 600 !important;
        font-size: 0.875rem;
        padding: 1rem 1.25rem !important;
        border: none !important;
        position: relative;
        white-space: nowrap;
    }
    
    table.dataTable thead th.sorting::after,
    table.dataTable thead th.sorting_asc::after,
    table.dataTable thead th.sorting_desc::after {
        color: rgba(255, 255, 255, 0.7);
    }
    
    table.dataTable tbody td {
        padding: 0.875rem 1.25rem !important;
        font-size: 0.875rem;
        border-color: #edf2f7 !important;
        vertical-align: middle;
    }
    
    table.dataTable tbody tr {
        background-color: white;
        transition: all 0.2s ease;
    }
    
    table.dataTable tbody tr:nth-child(even) { 
        background-color: #f8fafc !important; 
    }
    
    table.dataTable tbody tr:hover { 
        background-color: #f1f5f9 !important; 
    }
    
    /* Pagination */
    .dataTables_paginate .paginate_button {
        border-radius: 0.375rem !important;
        margin: 0 0.125rem !important;
        padding: 0.25rem 0.5rem !important;
        border: 1px solid #e2e8f0 !important;
        color: #4a5568 !important;
        transition: all 0.2s ease !important;
    }
    
    .dataTables_paginate .paginate_button.current, 
    .dataTables_paginate .paginate_button.current:hover {
        background: linear-gradient(135deg, var(--primary), var(--secondary)) !important;
        color: white !important;
        border-color: transparent !important;
    }
    
    .dataTables_paginate .paginate_button:hover {
        background: #f1f5f9 !important;
        color: #2d3748 !important;
        border-color: #cbd5e0 !important;
    }
    
    /* Search box */
    .dataTables_filter input {
        border: 1px solid #e2e8f0 !important;
        border-radius: 0.375rem !important;
        padding: 0.375rem 0.75rem !important;
        font-size: 0.875rem !important;
        transition: all 0.2s ease !important;
    }
    
    .dataTables_filter input:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px rgba(58, 123, 213, 0.1) !important;
        outline: none !important;
    }
    
    /* Length menu */
    .dataTables_length select {
        border: 1px solid #e2e8f0 !important;
        border-radius: 0.375rem !important;
        padding: 0.25rem 1.75rem 0.25rem 0.5rem !important;
        font-size: 0.875rem !important;
    }
    
    /* Buttons */
    .dt-buttons {
        margin-bottom: 1rem !important;
    }
    
    .dt-button {
        background: white !important;
        border: 1px solid #e2e8f0 !important;
        color: #4a5568 !important;
        border-radius: 0.375rem !important;
        padding: 0.375rem 0.75rem !important;
        font-size: 0.875rem !important;
        margin-right: 0.5rem !important;
        transition: all 0.2s ease !important;
    }
    
    .dt-button:hover {
        background: #f8fafc !important;
        border-color: #cbd5e0 !important;
        color: #2d3748 !important;
    }
    
    /* Responsive adjustments */
    @media (max-width: 768px) {
        .data-header h2 { 
            font-size: 1.5rem; 
        }
        
        .data-header p {
            max-width: 100%;
        }
        
        .dataTables_wrapper .dataTables_info,
        .dataTables_wrapper .dataTables_filter,
        .dataTables_wrapper .dataTables_length,
        .dataTables_wrapper .dataTables_paginate {
            text-align: left !important;
            float: none !important;
            margin-bottom: 0.5rem;
        }
        
        .dt-buttons {
            margin-bottom: 1rem !important;
            text-align: left !important;
        }
    }

    /* Sidebar style */
    .stSidebar { 
        background: var(--sidebar-bg) !important;
        box-shadow: 2px 0 10px rgba(0, 0, 0, 0.05);
    }
    
    .stSidebar .stMarkdown h1,
    .stSidebar .stMarkdown h2,
    .stSidebar .stMarkdown h3 {
        color: var(--primary);
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
    }
    
    .stSidebar .stButton>button {
        width: 100%;
        margin: 0.25rem 0;
        text-align: left;
        padding: 0.5rem 1rem !important;
        border-radius: 0.375rem !important;
        background: white !important;
        color: var(--dark) !important;
        border: 1px solid #e2e8f0 !important;
    }
    
    .stSidebar .stButton>button:hover {
        background: #f8fafc !important;
        transform: translateX(4px) !important;
    }
    </style>
    """

# ------------------- دالة لعرض الجداول بشكل DataTable تفاعلي -------------------
def render_table(df: pd.DataFrame, table_name="data", export_buttons=True):
    """
    Provide download options for a pandas DataFrame.
    
    Args:
        df: Input DataFrame to download
        table_name: Base name for downloaded files (default: "data")
        export_buttons: Whether to show export buttons (default: True)
    """
    if df is None or df.empty:
        st.info("No data available to download.")
        return
    
    # Create a copy of the dataframe to avoid modifying the original
    df2 = df.copy()
    
    st.write(f"### Download {table_name.replace('_', ' ').title()}")
    
    # Show basic info about the data
    st.info(f"Data contains {len(df2)} rows .")
    
    # Create columns for download buttons
    col1, col2 = st.columns(2)
    
    # Add download buttons
    with col1:
        csv = df2.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"{table_name}.csv",
            mime="text/csv"
        )
    with col2:
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            df2.to_excel(writer, index=False, sheet_name=table_name[:31])
        excel_data = excel_buffer.getvalue()
        st.download_button(
            label="Download Excel",
            data=excel_data,
            file_name=f"{table_name}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# ------------------- الدوال الأساسية (من كودك الأصلي مع الحفاظ على المنطق) -------------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS rules
                 (serv_cat text, tooth_number integer,
                  min_patient_age integer, max_patient_age integer,
                  new_cpt text, arabic_desc text, english_desc text,
                  service_code text, tooth_type text, tooth_category text,
                  service_category text, service_type text)''')
    conn.commit()
    conn.close()

def authenticate_upload(password):
    return hashlib.md5(password.encode()).hexdigest() == ADMIN_PASSWORD_HASH

def authenticate_delete(password):
    return hashlib.md5(password.encode()).hexdigest() == DELETE_PASSWORD_HASH

def upload_rules():
    """
    واجهة رفع القواعد محمية بكلمة سر 'password' (مشغل بواسطة ADMIN_PASSWORD_HASH)
    تعرض الجدول باستخدام render_table
    """
    if 'rules_uploaded' not in st.session_state:
        st.session_state.rules_uploaded = False
    if 'show_delete_form' not in st.session_state:
        st.session_state.show_delete_form = False

    st.markdown('<div class="data-header"><h2>⚙️ Dental Rules Management</h2><p>Upload/View/Delete Discount Rules</p></div>', unsafe_allow_html=True)

    # رفع القواعد
    with st.expander("📤 Upload Rules (CSV)"):
        uploaded = st.file_uploader("Select the rules file. (CSV) ", type=["csv"], key="rules_uploader")
        col1, col2 = st.columns([2,1])
        with col1:
            st.caption("Required: At least columns: SERV CAT, TOOTH_NUMBER, MIN_PATIENT_AGE, MAX_PATIENT_AGE")
        with col2:
            pass

        if uploaded is not None:
            pw = st.text_input("Enter upload password:", type="password", key="pw_upload")
            if st.button("Upload Rules", key="btn_upload"):
                if authenticate_upload(pw or ""):
                    try:
                        rules_df = pd.read_csv(uploaded, encoding='utf-8-sig')
                        # Rename expected columns if present
                        rules_df.rename(columns={
                            'SERV CAT': 'serv_cat',
                            'TOOTH_NUMBER': 'tooth_number',
                            'MIN_PATIENT_AGE': 'min_patient_age',
                            'MAX_PATIENT_AGE': 'max_patient_age',
                            'New CPT': 'new_cpt',
                            'Arabic Description': 'arabic_desc',
                            'English Description': 'english_desc',
                            'SERVICE_CODE': 'service_code',
                            'TOOTH_TYPE': 'tooth_type',
                            'TOOTH_CATEGORY': 'tooth_category',
                            'SERVICE_CATEGORY': 'service_category',
                            'Service type': 'service_type'
                        }, inplace=True)
                        conn = sqlite3.connect(DB_NAME)
                        rules_df.to_sql('rules', conn, if_exists='replace', index=False)
                        conn.close()
                        st.success("✅ Rules uploaded successfully!")
                        st.session_state.rules_uploaded = True
                    except Exception as e:
                        st.error(f"❌ An error occurred while uploading the file.: {e}")
                else:
                    st.error("❌ Incorrect upload password.")

    # عرض القواعد وحذفها
    conn = sqlite3.connect(DB_NAME)
    try:
        rules_df = pd.read_sql("SELECT * FROM rules", conn)
    except Exception:
        rules_df = pd.DataFrame()
    conn.close()

    if not rules_df.empty:
        st.markdown("---")
        st.markdown("### 📋 Current Rules")
        render_table(rules_df, table_name="rules")

        st.markdown("---")
        if st.button("🗑️ Show Delete Rules Form"):
            st.session_state.show_delete_form = True

        if st.session_state.get('show_delete_form', False):
            with st.form("delete_form"):
                st.warning("⚠️ Sensitive Operation — Enter Delete Password")
                dpw = st.text_input("Delete Password:", type="password", key="dpw")
                submitted = st.form_submit_button("Confirm Deletion")
                if submitted:
                    if authenticate_delete(dpw or ""):
                        try:
                            conn = sqlite3.connect(DB_NAME)
                            c = conn.cursor()
                            c.execute("DELETE FROM rules")
                            conn.commit()
                            conn.close()
                            st.success("✅ Rules deleted successfully.")
                            st.session_state.rules_uploaded = False
                            st.session_state.show_delete_form = False
                        except Exception as e:
                            st.error(f"❌ An error occurred while deleting: {e}")
                    else:
                        st.error("❌ Incorrect delete password.")

    else:
        st.info("No rules are currently stored.")

# ------------------- دوال تطبيق الخصومات وكشف الشذوذ (من كودك الأصلي) -------------------
def apply_deductions(data_df):
    """Apply deductions based on rules"""
    conn = sqlite3.connect(DB_NAME)
    try:
        rules_df = pd.read_sql("SELECT * FROM rules", conn)
    except Exception:
        rules_df = pd.DataFrame()
    conn.close()

    non_compliant_cases = []
    processed_pairs = set()
    gum_surgery_records = {}
    ioe_records = {}

    # Ensure TRX DATE present for sorting
    if 'TRX DATE' in data_df.columns:
        data_df = data_df.sort_values('TRX DATE')
    else:
        data_df = data_df.copy()

    for index, row in data_df.iterrows():
        service = row.get('SERVICE', '')
        adherent = row.get('ADHERENT#', '')
        trx_date = row.get('TRX DATE') if pd.notna(row.get('TRX DATE')) else None
        prov_net_claimed = float(row.get('PROV NET CLAIMED')) if pd.notna(row.get('PROV NET CLAIMED')) else 0
        prov_desc = str(row.get('PROV ITEM DESC MAPPING', ''))
        age = int(row.get('AGE')) if pd.notna(row.get('AGE')) else 0
        tooth_num = row.get('EXTRACTED_TOOTH')
        quantity = int(row.get('QTYAPP')) if pd.notna(row.get('QTYAPP')) and row.get('QTYAPP') != 0 else 1

        # Rule 1: IOE repeat less than 30 days
        if service == 'IOE' and trx_date is not None:
            if adherent in ioe_records:
                last_date, _ = ioe_records[adherent]
                if (trx_date - last_date) < timedelta(days=30):
                    non_compliant_cases.append({
                        'SSNBR': row.get('SSNBR', ''),
                        'ADHERENT#': adherent,
                        'SERVICE': service,
                        'GM_ITEM_DESCRIPTION': row.get('GM ITEM DESCRIPTION', ''),
                        'PROV_ITEM_DESC': prov_desc,
                        'TOOTH_NUMBER': tooth_num,
                        'PATIENT_AGE': age,
                        'TRX DATE': trx_date.strftime('%Y-%m-%d') if trx_date else '',
                        'PREVIOUS_DATE': last_date.strftime('%Y-%m-%d') if last_date else '',
                        'PROV_NET_CLAIMED': prov_net_claimed,
                        'QTYAPP': quantity,
                        'REASON': 'Follow-up'
                    })
            ioe_records[adherent] = (trx_date, index)

        # Rule 2: specific gum surgery limit
        if 'جراحة اللثة الصديدية' in prov_desc:
            if adherent in gum_surgery_records:
                gum_surgery_records[adherent]['total_qty'] += quantity
                total_qty = gum_surgery_records[adherent]['total_qty']
                if total_qty > 2:
                    excess_qty = min(total_qty - 2, quantity)
                    amount_to_deduct = (prov_net_claimed / quantity) * excess_qty if quantity != 0 else 0
                    non_compliant_cases.append({
                        'SSNBR': row.get('SSNBR', ''),
                        'ADHERENT#': adherent,
                        'SERVICE': service,
                        'GM_ITEM_DESCRIPTION': row.get('GM ITEM DESCRIPTION', ''),
                        'PROV_ITEM_DESC': prov_desc,
                        'TOOTH_NUMBER': tooth_num,
                        'PATIENT_AGE': age,
                        'TRX DATE': trx_date.strftime('%Y-%m-%d') if trx_date else '',
                        'TOTAL_QUANTITY': total_qty,
                        'EXCESS_QUANTITY': excess_qty,
                        'PROV_NET_CLAIMED': amount_to_deduct,
                        'QTYAPP': quantity,
                        'REASON': f'تجاوز حد جراحة اللثة (الحد الأقصى 2، الكمية الإجمالية {total_qty})'
                    })
            else:
                gum_surgery_records[adherent] = {'total_qty': quantity}

        # Rule 3: age mismatch (requires rules)
        if pd.isna(tooth_num) or tooth_num is None:
            continue
        case_id = (row.get('SSNBR',''), adherent, service, tooth_num)
        if case_id in processed_pairs:
            continue

        if not rules_df.empty:
            matching_rules = rules_df[
                (rules_df['serv_cat'] == service) &
                (rules_df['tooth_number'] == tooth_num)
            ]
            if not matching_rules.empty:
                rule = matching_rules.iloc[0]
                min_age = int(rule['min_patient_age']) if pd.notna(rule.get('min_patient_age')) else 0
                max_age = int(rule['max_patient_age']) if pd.notna(rule.get('max_patient_age')) else 120
                if age < min_age or age > max_age:
                    non_compliant_cases.append({
                        'SSNBR': row.get('SSNBR',''),
                        'ADHERENT#': adherent,
                        'SERVICE': service,
                        'GM_ITEM_DESCRIPTION': row.get('GM ITEM DESCRIPTION',''),
                        'TOOTH_NUMBER': tooth_num,
                        'PATIENT_AGE': age,
                        'TRX DATE': trx_date.strftime('%Y-%m-%d') if trx_date else '',
                        'PROV_NET_CLAIMED': prov_net_claimed,
                        'QTYAPP': quantity,
                        'REASON': f'incompatible age'
                    })
                    processed_pairs.add(case_id)

    return pd.DataFrame(non_compliant_cases) if non_compliant_cases else pd.DataFrame()

def detect_fraud_with_isolation(data_df):
    """Detect anomalies using Isolation Forest"""
    if data_df is None or data_df.empty:
        return pd.DataFrame()

    excluded_services = ['XRD', 'IOE', 'CL']
    if 'SERVICE' not in data_df.columns:
        return pd.DataFrame()
    filtered_df = data_df[~data_df['SERVICE'].isin(excluded_services)].copy()
    if filtered_df.empty:
        return pd.DataFrame()

    # aggregate per adherent
    service_counts = filtered_df.groupby('ADHERENT#')['SERVICE'].count().reset_index()
    service_counts.columns = ['ADHERENT#', 'SERVICE_COUNT']
    cost_totals = filtered_df.groupby('ADHERENT#')['PROV NET CLAIMED'].sum().reset_index()
    cost_totals.columns = ['ADHERENT#', 'TOTAL_COST']

    merged_df = pd.merge(filtered_df, service_counts, on='ADHERENT#')
    merged_df = pd.merge(merged_df, cost_totals, on='ADHERENT#')

    # Features
    features = merged_df[['PROV NET CLAIMED', 'QTYAPP', 'SERVICE_COUNT', 'TOTAL_COST']].copy()
    # compute days since last
    if 'TRX DATE' in merged_df.columns:
        features['DAYS_SINCE_LAST'] = merged_df.groupby('ADHERENT#')['TRX DATE'].diff().dt.days.fillna(0)
    else:
        features['DAYS_SINCE_LAST'] = 0

    scaler = StandardScaler()
    X = scaler.fit_transform(features)

    clf = IsolationForest(contamination=0.1, random_state=42)
    predictions = clf.fit_predict(X)

    merged_df['ANOMALY_SCORE'] = -clf.decision_function(X)
    merged_df['IS_FRAUD'] = predictions == -1

    result_df = merged_df[merged_df['IS_FRAUD']].copy()
    if result_df.empty:
        return pd.DataFrame()

    # Risk level
    conditions = [
        (result_df['TOTAL_COST'] > result_df['TOTAL_COST'].quantile(0.9)) &
        (result_df['SERVICE_COUNT'] > result_df['SERVICE_COUNT'].quantile(0.9)),
        (result_df['TOTAL_COST'] > result_df['TOTAL_COST'].quantile(0.75)) |
        (result_df['SERVICE_COUNT'] > result_df['SERVICE_COUNT'].quantile(0.75))
    ]
    choices = ['high risk', 'medium risk']
    result_df['RISK_LEVEL'] = np.select(conditions, choices, default='low risk')

    columns_to_export = [
        'SSNBR', 'ADHERENT#', 'SERVICE', 'GM ITEM DESCRIPTION',
        'PROV ITEM DESC MAPPING', 'TRX DATE', 'PROV NET CLAIMED',
        'QTYAPP', 'SERVICE_COUNT', 'TOTAL_COST', 'ANOMALY_SCORE', 'RISK_LEVEL'
    ]
    # Keep only columns that exist
    columns_to_export = [c for c in columns_to_export if c in result_df.columns]
    result_df = result_df[columns_to_export]

    # Format
    if 'TRX DATE' in result_df.columns:
        try:
            result_df['TRX DATE'] = pd.to_datetime(result_df['TRX DATE']).dt.strftime('%Y-%m-%d')
        except Exception:
            pass
    if 'PROV NET CLAIMED' in result_df.columns:
        result_df['PROV NET CLAIMED'] = result_df['PROV NET CLAIMED'].round(2)
    if 'TOTAL_COST' in result_df.columns:
        result_df['TOTAL_COST'] = result_df['TOTAL_COST'].round(2)
    if 'ANOMALY_SCORE' in result_df.columns:
        result_df['ANOMALY_SCORE'] = result_df['ANOMALY_SCORE'].round(4)

    # Sort by risk
    order_map = {'high risk': 0, 'medium risk': 1, 'low risk': 2}
    result_df['R_ORDER'] = result_df['RISK_LEVEL'].map(order_map).fillna(3)
    result_df = result_df.sort_values(['R_ORDER', 'ANOMALY_SCORE']).drop(columns=['R_ORDER'])

    return result_df

def export_to_csv_with_arabic(df):
    output = io.StringIO()
    df.to_csv(output, index=False, encoding='utf-8-sig')
    output.seek(0)
    return output.getvalue().encode('utf-8-sig')

# ------------------- Data Processing (User Interface) -------------------
def process_data():
    st.markdown('<div class="data-header"><h2>🦷 Dental Data Processing and Risk Assessment</h2><p>Upload the data file, then apply rules and detect anomalies</p></div>', unsafe_allow_html=True)

    # Check rules exist
    conn = sqlite3.connect(DB_NAME)
    try:
        rules_count = pd.read_sql("SELECT COUNT(*) FROM rules", conn).iloc[0,0]
    except Exception:
        rules_count = 0
    conn.close()

    if rules_count == 0:
        st.error("⚠️ No rules have been uploaded yet. Please go to the 'Upload Rules' page to upload rules.")
        return

    with st.expander("📁 Upload Data File (CSV)", expanded=True):
        data_file = st.file_uploader("Select Data File (CSV) - Ensure required columns are present", type="csv", key="data_uploader")

    if data_file:
        try:
            data_df = pd.read_csv(data_file, encoding='utf-8-sig')
            # ensure date parsing
            if 'TRX DATE' in data_df.columns:
                data_df['TRX DATE'] = pd.to_datetime(data_df['TRX DATE'], errors='coerce')
            data_df['QTYAPP'] = pd.to_numeric(data_df.get('QTYAPP', 1), errors='coerce').fillna(1)

            # extract tooth number heuristic if missing
            def extract_tooth_number(description):
                if pd.isna(description): return None
                patterns = [r'tooth[\s\-_]?(\d+)', r't[\s\-_]?(\d+)', r'\b(\d{1,2})\b', r'\((\d{1,2})\)']
                for pattern in patterns:
                    match = re.search(pattern, str(description), re.IGNORECASE)
                    if match:
                        try:
                            return int(match.group(1))
                        except:
                            return None
                return None

            data_df['EXTRACTED_TOOTH'] = data_df.get('GM ITEM DESCRIPTION', '').apply(extract_tooth_number)

            # ------ Apply Deductions ------
            st.markdown("---")
            st.markdown('<div class="data-header"><h2>💰 Deductions and Rule Application</h2></div>', unsafe_allow_html=True)

            with st.spinner("Analyzing data and applying rules..."):
                deductions_df = apply_deductions(data_df)

            if not deductions_df.empty:
                st.success(f"✅ It was discovered {len(deductions_df)} Condition requiring deductions")
                render_table(deductions_df, table_name="deductions")
                total_deduction = deductions_df['PROV_NET_CLAIMED'].sum() if 'PROV_NET_CLAIMED' in deductions_df.columns else 0
                st.warning(f"💸 Total potential deduction amount: **{total_deduction:,.2f}   EGP**")
                csv_data = export_to_csv_with_arabic(deductions_df)
                st.download_button("📥 Download Deductions File", data=csv_data, file_name="Dental_Deductions.csv", mime="text/csv")
            else:
                st.info("🎉 There are no situations that warrant a deduction based on the rules.")

            # ------ Anomaly Detection ------
            st.markdown("---")
            st.markdown('<div class="data-header"><h2>🔎 Anomaly Detection</h2></div>', unsafe_allow_html=True)

            with st.spinner("Analyzing anomalies..."):
                anomaly_df = detect_fraud_with_isolation(data_df)

            if not anomaly_df.empty:
                st.success(f"✅ It was discovered {len(anomaly_df)} anomalies")
                # Show by risk level
                high = anomaly_df[anomaly_df.get('RISK_LEVEL') == 'High Risk']
                med = anomaly_df[anomaly_df.get('RISK_LEVEL') == 'Medium Risk']
                low = anomaly_df[anomaly_df.get('RISK_LEVEL') == 'Low Risk']

                if not high.empty:
                    st.subheader("🔴 High Risk")
                    render_table(high, table_name="high_risk")
                if not med.empty:
                    st.subheader("🟠 Medium Risk")
                    render_table(med, table_name="medium_risk")
                if not low.empty:
                    st.subheader("🟢 Low Risk")
                    render_table(low, table_name="low_risk")

                csv_data = export_to_csv_with_arabic(anomaly_df)
                st.download_button("📥 Download Anomaly Detection Results", data=csv_data, file_name="Anomaly_Detection.csv", mime="text/csv")
            else:
                st.info("🎉 There are no anomalies after excluding the specified services.")

        except Exception as e:
            st.error(f"❌ An error occurred during processing: {e}")

# ------------------- دالة التحقق من دخول الموقع -------------------
def site_authentication():
    if 'site_authenticated' not in st.session_state:
        with st.form("site_login_form"):
            st.markdown("<div style='text-align:center; padding:6px 0;'><img src='https://img.icons8.com/color/96/000000/dental-braces.png' width='60'></div>", unsafe_allow_html=True)
            st.warning("🔐 Please enter the site password to continue")
            site_pass = st.text_input("Site Password:", type="password", key="site_pass")
            submitted = st.form_submit_button("Login")
            if submitted:
                if hashlib.md5((site_pass or "").encode()).hexdigest() == SITE_LOGIN_PASSWORD_HASH:
                    st.session_state.site_authenticated = True
                    st.success("✅ Login successful")
                    st.rerun()
                else:
                    st.error("❌ Incorrect password")
        return False
    return True

# ------------------- الصفحة الرئيسية - أزرار تنقل -------------------
def main():
    setup_ui()

    # require site login first
    if not site_authentication():
        return

    # Sidebar as navigation links (buttons)
    with st.sidebar:
        st.markdown("<div style='text-align:center; padding: 12px 6px;'>"
                    "<img src='https://img.icons8.com/color/96/000000/dental-braces.png' width='70'/>"
                    "<h3 style='margin:6px 0 0; color: var(--dark)'>Dental Audit System</h3>"
                    "<p style='margin:4px 0 0; color: #0f766e;'>AI-Powered Dental Audit</p>"
                    "</div>", unsafe_allow_html=True)

        # navigation buttons
        if st.button("📁 Upload Rules", key="btn_nav_rules"):
            st.session_state.page = "upload_rules"
        if st.button("🦷 Data Processing", key="btn_nav_processing"):
            st.session_state.page = "data_processing"
        st.markdown("---")
        st.markdown("<div style='text-align:center; color: #0b6b61; font-size: 13px;'>"
                    "<p>Version 1.0.0</p>"
                    "<p style='color:#b91c1c; font-weight:700; margin:6px 0 0;'>Mostafa El-beshbeshy</p>"
                    "<p style='font-size:12px; opacity:0.8;'>© Dental Audit System 2025</p>"
                    "</div>", unsafe_allow_html=True)

    # default page
    page = st.session_state.get('page', 'upload_rules')

    if page == "upload_rules":
        upload_rules()
    elif page == "data_processing":
        process_data()
    else:
        # fallback
        upload_rules()

if __name__ == "__main__":
    init_db()
    main()
