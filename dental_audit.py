import streamlit as st
import pandas as pd
import sqlite3
import hashlib
from datetime import datetime, timedelta
import re
import io
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# ------ إعداد قاعدة البيانات ------
DB_NAME = "dental_rules.db"
ADMIN_PASSWORD_HASH = "5f4dcc3b5aa765d61d8327deb882cf99"  # كلمة مرور Admin (password)
DELETE_PASSWORD_HASH = "0a8ba44b5cf05598d07aca8a0a3afa58"  # delete123

# ------ تحسينات الواجهة ------
def setup_ui():
    st.set_page_config(
        page_title="Dental Audit System",
        layout="wide",
        page_icon="🦷",
        initial_sidebar_state="expanded"
    )
    st.markdown("""
    <style>
    :root {
        --primary: #2E86AB;
        --secondary: #F18F01;
        --danger: #C73E1D;
        --light: #F7F7F7;
        --dark: #333333;
    }
    * {
        font-family: 'Segoe UI', 'Tahoma', sans-serif !important;
    }
    .stApp {
        background-color: #f8fafc;
        color: var(--dark);
    }
    .stHeader {
        color: var(--primary) !important;
        border-bottom: 2px solid var(--primary);
        padding-bottom: 12px;
    }
    .stButton>button {
        background-color: var(--primary) !important;
        color: white !important;
        border-radius: 12px !important;
        padding: 10px 20px !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: all 0.3s ease !important;
    }
    .stButton>button:hover {
        background-color: var(--secondary) !important;
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    /* تحسين الجداول */
    .stDataFrame {
        border-radius: 16px !important;
        box-shadow: 0 8px 16px rgba(0,0,0,0.1) !important;
        overflow: hidden !important;
        margin: 15px auto;
        max-width: 95%;
        background-color: white;
    }
    .stDataFrame > div {
        overflow-x: auto !important;
        -webkit-overflow-scrolling: touch;
    }
    .stDataFrame table {
        width: 100% !important;
        table-layout: auto !important;
        border-collapse: collapse;
    }
    .stDataFrame th, .stDataFrame td {
        padding: 12px 14px !important;
        white-space: nowrap !important;
        text-align: right !important;
    }
    .stDataFrame th {
        background-color: var(--primary) !important;
        color: white !important;
        font-weight: 600;
    }
    .stDataFrame tr:nth-child(even) {
        background-color: #f8fafc;
    }
    .stDataFrame tr:hover {
        background-color: #f1f5f9 !important;
    }
    /* تلوين الصفوف */
    .dataframe .repetition {
        background-color: #FFDDDD !important;
    }
    .dataframe .surgery {
        background-color: #FFF3CD !important;
    }
    .dataframe .age {
        background-color: #D4EDDA !important;
    }
    /* الشريط الجانبي */
    .css-1d391kg {
        background-color: var(--primary) !important;
    }
    .css-1d391kg .css-1v3fvws, .css-1d391kg .stSelectbox label {
        color: white !important;
        font-weight: 600;
    }
    /* العناوين الجذابة */
    .data-header {
        background: linear-gradient(90deg, var(--primary), var(--secondary));
        padding: 20px;
        border-radius: 16px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.15);
        margin: 20px 0;
        text-align: center;
        color: white;
    }
    .data-header h2 {
        margin: 0;
        font-weight: 700;
        font-size: 24px;
    }
    .data-header p {
        margin: 8px 0 0;
        font-size: 16px;
        opacity: 0.9;
    }
    /* تحسين التحميل */
    .stFileUploader > div {
        border: 2px dashed var(--primary) !important;
        border-radius: 12px !important;
        padding: 30px !important;
        background-color: #ebf8ff;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# ------ الدوال الأساسية ------
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

def authenticate(password):
    return hashlib.md5(password.encode()).hexdigest() == ADMIN_PASSWORD_HASH

def upload_rules():
    if 'rules_uploaded' not in st.session_state:
        st.session_state.rules_uploaded = False
    if 'admin_authenticated' not in st.session_state:
        st.session_state.admin_authenticated = False
    if 'auth_time' not in st.session_state:
        st.session_state.auth_time = None
    if 'show_delete_form' not in st.session_state:
        st.session_state.show_delete_form = False

    # التحقق من انتهاء مهلة 120 ثانية
    if (st.session_state.admin_authenticated and 
        st.session_state.auth_time and 
        (datetime.now() - st.session_state.auth_time).total_seconds() > 120):
        st.session_state.admin_authenticated = False
        st.session_state.auth_time = None
        st.warning("⏰ Your session has timed out. Please enter your password again.")
        st.rerun()

    # نموذج إدخال كلمة المرور (للدخول العام)
    if not st.session_state.rules_uploaded or not st.session_state.admin_authenticated:
        with st.form("admin_auth"):
            st.warning("🔐 This page is for administrators only - password required")
            password = st.text_input("Password:", type="password")
            if st.form_submit_button("Login"):
                if authenticate(password):
                    st.session_state.admin_authenticated = True
                    st.session_state.auth_time = datetime.now()
                    st.success("✅ Authentication successful")
                    st.rerun()
                else:
                    st.error("❌ Incorrect password")

    if st.session_state.get('admin_authenticated', False):
        if not st.session_state.rules_uploaded:
            with st.expander("📤 Upload Dental Rules", expanded=True):
                rules_file = st.file_uploader(
                    "Upload Rules file(CSV)",
                    type="csv",
                    key="rules_uploader",
                    help="The file must contain columns : SERV CAT, TOOTH_NUMBER, MIN_PATIENT_AGE, MAX_PATIENT_AGE"
                )
                if rules_file:
                    try:
                        rules_df = pd.read_csv(rules_file, encoding='utf-8-sig')
                        required_columns = ['SERV CAT', 'TOOTH_NUMBER', 'MIN_PATIENT_AGE', 'MAX_PATIENT_AGE']
                        if all(col in rules_df.columns for col in required_columns):
                            conn = sqlite3.connect(DB_NAME)
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
                            rules_df.to_sql('rules', conn, if_exists='replace', index=False)
                            conn.close()
                            st.success("✅ Rules uploaded successfully!")
                            st.session_state.rules_uploaded = True
                            st.rerun()
                        else:
                            missing_cols = [col for col in required_columns if col not in rules_df.columns]
                            st.error(f"The file is missing the following required columns: {missing_cols}")
                    except Exception as e:
                        st.error(f"An error occurred while uploading: {str(e)}")
        else:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📋 View Current Rules"):
                    conn = sqlite3.connect(DB_NAME)
                    rules_df = pd.read_sql("SELECT * FROM rules", conn)
                    conn.close()
                    st.dataframe(rules_df, use_container_width=True, hide_index=True)

            with col2:
                if st.button("🗑️ Delete Current Rules"):
                    st.session_state.show_delete_form = True

            # نموذج إدخال كلمة سر الحذف
            if st.session_state.show_delete_form:
                with st.form("delete_auth_form"):
                    st.warning("⚠️ Sensitive Operation - Deletion Password Required")
                    delete_password = st.text_input("Deletion Password:", type="password")
                    submit = st.form_submit_button("Confirm Deletion")

                    if submit:
                        # التحقق من كلمة السر
                        entered_hash = hashlib.md5(delete_password.strip().encode('utf-8')).hexdigest()
                        if entered_hash == DELETE_PASSWORD_HASH:
                            try:
                                # إعادة الاتصال بقاعدة البيانات
                                conn = sqlite3.connect(DB_NAME)
                                c = conn.cursor()
                                c.execute("DELETE FROM rules")
                                conn.commit()
                                conn.close()
                                # تحديث الحالة
                                st.session_state.rules_uploaded = False
                                st.session_state.show_delete_form = False
                                st.success("✅ Rules deleted successfully")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error deleting rules: {str(e)}")
                        else:
                            st.error(f"❌ Incorrect deletion password. Entered hash: `{entered_hash}`")




def apply_deductions(data_df):
    """Apply deductions based on rules"""
    conn = sqlite3.connect(DB_NAME)
    rules_df = pd.read_sql("SELECT * FROM rules", conn)
    conn.close()
    non_compliant_cases = []
    processed_pairs = set()
    gum_surgery_records = {}
    ioe_records = {}

    data_df = data_df.sort_values('TRX DATE')

    for index, row in data_df.iterrows():
        service = row['SERVICE']
        adherent = row['ADHERENT#']
        trx_date = row['TRX DATE'] if pd.notna(row['TRX DATE']) else None
        prov_net_claimed = float(row['PROV NET CLAIMED']) if pd.notna(row['PROV NET CLAIMED']) else 0
        prov_desc = str(row['PROV ITEM DESC MAPPING'])
        age = int(row['AGE']) if pd.notna(row['AGE']) else 0
        tooth_num = row['EXTRACTED_TOOTH']
        quantity = int(row['QTYAPP']) if pd.notna(row['QTYAPP']) and row['QTYAPP'] != 0 else 1

        # القاعدة 1: تكرار الاستشارة (IOE) أقل من 30 يوم
        if service == 'IOE' and trx_date:
            if adherent in ioe_records:
                last_date, _ = ioe_records[adherent]
                if (trx_date - last_date) < timedelta(days=30):
                    non_compliant_cases.append({
                        'SSNBR': row['SSNBR'],
                        'ADHERENT#': adherent,
                        'SERVICE': service,
                        'GM_ITEM_DESCRIPTION': row['GM ITEM DESCRIPTION'],
                        'PROV_ITEM_DESC': prov_desc,
                        'TOOTH_NUMBER': tooth_num,
                        'PATIENT_AGE': age,
                        'TRX DATE': trx_date.strftime('%Y-%m-%d'),
                        'PREVIOUS_DATE': last_date.strftime('%Y-%m-%d'),
                        'PROV_NET_CLAIMED': prov_net_claimed,
                        'QTYAPP': quantity,
                        'REASON': 'Follow-up'
                    })
            ioe_records[adherent] = (trx_date, index)

        # القاعدة 2: جراحة اللثة الصديدية
        if 'جراحة اللثة الصديدية' in prov_desc:
            if adherent in gum_surgery_records:
                gum_surgery_records[adherent]['total_qty'] += quantity
                total_qty = gum_surgery_records[adherent]['total_qty']
                if total_qty > 2:
                    excess_qty = min(total_qty - 2, quantity)
                    amount_to_deduct = (prov_net_claimed / quantity) * excess_qty if quantity != 0 else 0
                    non_compliant_cases.append({
                        'SSNBR': row['SSNBR'],
                        'ADHERENT#': adherent,
                        'SERVICE': service,
                        'GM_ITEM_DESCRIPTION': row['GM ITEM DESCRIPTION'],
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

        # القاعدة 3: عدم توافق العمر
        if pd.isna(tooth_num) or tooth_num is None:
            continue
        case_id = (row['SSNBR'], adherent, service, tooth_num)
        if case_id in processed_pairs:
            continue

        matching_rules = rules_df[
            (rules_df['serv_cat'] == service) &
            (rules_df['tooth_number'] == tooth_num)
        ]
        if not matching_rules.empty:
            rule = matching_rules.iloc[0]
            min_age = int(rule['min_patient_age']) if pd.notna(rule['min_patient_age']) else 0
            max_age = int(rule['max_patient_age']) if pd.notna(rule['max_patient_age']) else 120
            if age < min_age or age > max_age:
                non_compliant_cases.append({
                    'SSNBR': row['SSNBR'],
                    'ADHERENT#': adherent,
                    'SERVICE': service,
                    'GM_ITEM_DESCRIPTION': row['GM ITEM DESCRIPTION'],
                    'TOOTH_NUMBER': tooth_num,
                    'PATIENT_AGE': age,
                    'TRX DATE': trx_date.strftime('%Y-%m-%d') if trx_date else '',
                    'PROV_NET_CLAIMED': prov_net_claimed,
                    'QTYAPP': quantity,
                    'REASON': f'incompatible age '
                })
                processed_pairs.add(case_id)

    return pd.DataFrame(non_compliant_cases) if non_compliant_cases else pd.DataFrame()

def detect_fraud_with_isolation(data_df):
    """Detect anomalies using Isolation Forest"""
    excluded_services = ['XRD', 'IOE', 'CL']
    filtered_df = data_df[~data_df['SERVICE'].isin(excluded_services)].copy()
    if filtered_df.empty:
        return pd.DataFrame()

    service_counts = filtered_df.groupby('ADHERENT#')['SERVICE'].count().reset_index()
    service_counts.columns = ['ADHERENT#', 'SERVICE_COUNT']
    cost_totals = filtered_df.groupby('ADHERENT#')['PROV NET CLAIMED'].sum().reset_index()
    cost_totals.columns = ['ADHERENT#', 'TOTAL_COST']

    merged_df = pd.merge(filtered_df, service_counts, on='ADHERENT#')
    merged_df = pd.merge(merged_df, cost_totals, on='ADHERENT#')

    features = merged_df[['PROV NET CLAIMED', 'QTYAPP', 'SERVICE_COUNT', 'TOTAL_COST']].copy()
    features['DAYS_SINCE_LAST'] = merged_df.groupby('ADHERENT#')['TRX DATE'].diff().dt.days.fillna(0)

    scaler = StandardScaler()
    X = scaler.fit_transform(features)

    clf = IsolationForest(contamination=0.1, random_state=42)
    predictions = clf.fit_predict(X)

    merged_df['ANOMALY_SCORE'] = -clf.decision_function(X)
    merged_df['IS_FRAUD'] = predictions == -1

    result_df = merged_df[merged_df['IS_FRAUD']].copy()
    if not result_df.empty:
        conditions = [
            (result_df['TOTAL_COST'] > result_df['TOTAL_COST'].quantile(0.9)) &
            (result_df['SERVICE_COUNT'] > result_df['SERVICE_COUNT'].quantile(0.9)),
            (result_df['TOTAL_COST'] > result_df['TOTAL_COST'].quantile(0.75)) |
            (result_df['SERVICE_COUNT'] > result_df['SERVICE_COUNT'].quantile(0.75))
        ]
        choices = ['High Risk', 'Medium Risk']
        result_df['RISK_LEVEL'] = np.select(conditions, choices, default='Low Risk')

        columns_to_export = [
            'SSNBR', 'ADHERENT#', 'SERVICE', 'GM ITEM DESCRIPTION',
            'PROV ITEM DESC MAPPING', 'TRX DATE', 'PROV NET CLAIMED',
            'QTYAPP', 'SERVICE_COUNT', 'TOTAL_COST', 'ANOMALY_SCORE', 'RISK_LEVEL'
        ]
        result_df = result_df[columns_to_export]

        result_df['TRX DATE'] = result_df['TRX DATE'].dt.strftime('%Y-%m-%d')
        result_df['PROV NET CLAIMED'] = result_df['PROV NET CLAIMED'].round(2)
        result_df['TOTAL_COST'] = result_df['TOTAL_COST'].round(2)
        result_df['ANOMALY_SCORE'] = result_df['ANOMALY_SCORE'].round(4)

        risk_order = {'High Risk': 0, 'Medium Risk': 1, 'Low Risk': 2}
        result_df['RISK_ORDER'] = result_df['RISK_LEVEL'].map(risk_order)
        result_df = result_df.sort_values(['RISK_ORDER', 'ANOMALY_SCORE'])
        result_df = result_df.drop('RISK_ORDER', axis=1)

    return result_df

def export_to_csv_with_arabic(df):
    output = io.StringIO()
    df.to_csv(output, index=False, encoding='utf-8-sig')
    output.seek(0)
    return output.getvalue().encode('utf-8-sig')

def process_data():
    st.markdown("""
    <div class="data-header">
        <h2>🦷 Processing Dental Data and Risk Assessment</h2>
        <p>Data analysis and applying smart rules for anomaly detection</p>
    </div>
    """, unsafe_allow_html=True)

    conn = sqlite3.connect(DB_NAME)
    rules_count = pd.read_sql("SELECT COUNT(*) FROM rules", conn).iloc[0,0]
    conn.close()

    if rules_count == 0:
        st.error("⚠️ The rules have not been uploaded yet. Please contact your administrator.")
        return

    with st.expander("📁 Upload Data File", expanded=True):
        data_file = st.file_uploader(
            "Select Data File (CSV)",
            type="csv",
            help="The file must contain the required data for analysis"
        )

    if data_file:
        try:
            data_df = pd.read_csv(data_file, encoding='utf-8-sig')
            data_df['TRX DATE'] = pd.to_datetime(data_df['TRX DATE'], errors='coerce')
            data_df['QTYAPP'] = pd.to_numeric(data_df['QTYAPP'], errors='coerce').fillna(1)

            def extract_tooth_number(description):
                if pd.isna(description): return None
                patterns = [r'tooth[\s\-_]?(\d+)', r't[\s\-_]?(\d+)', r'\b(\d{1,2})\b', r'\((\d{1,2})\)']
                for pattern in patterns:
                    match = re.search(pattern, str(description), re.IGNORECASE)
                    if match: return int(match.group(1))
                return None

            data_df['EXTRACTED_TOOTH'] = data_df['GM ITEM DESCRIPTION'].apply(extract_tooth_number)

            # ------ تطبيق الخصومات ------
            st.markdown("---")
            st.markdown("""
            <div class="data-header">
                <h2>💰 Deductions Based on Rules</h2>
            </div>
            """, unsafe_allow_html=True)

            with st.spinner("Analyzing data and applying rules..."):
                deductions_df = apply_deductions(data_df)

            if not deductions_df.empty:
                st.success(f"✅ {len(deductions_df)} case detected requiring deduction")
                st.dataframe(deductions_df, use_container_width=True, hide_index=True)
                total_deduction = deductions_df['PROV_NET_CLAIMED'].sum()
                st.warning(f"💸 Total amount to be deducted: **{total_deduction:,.2f} EGP**")
                csv_data = export_to_csv_with_arabic(deductions_df)
                st.download_button("📥 Download Deductions File", data=csv_data, file_name="Dental_Deductions.csv", mime="text/csv")
            else:
                st.info("🎉 No cases detected requiring deduction based on the rules.")

            # ------ كشف الشذوذ ------
            st.markdown("---")
            st.markdown("""
            <div class="data-header">
                <h2>🔎 Anomaly Detection</h2>
            </div>
            """, unsafe_allow_html=True)

            with st.spinner("Analyzing data for anomalies..."):
                anomaly_df = detect_fraud_with_isolation(data_df)

            if not anomaly_df.empty:
                st.success(f"✅ {len(anomaly_df)} case detected as anomalous")

                high_risk = anomaly_df[anomaly_df['RISK_LEVEL'] == 'عالية الخطورة']
                if not high_risk.empty:
                    st.subheader("🔴 High-Risk Cases")
                    st.dataframe(high_risk, use_container_width=True, hide_index=True)

                medium_risk = anomaly_df[anomaly_df['RISK_LEVEL'] == 'متوسطة الخطورة']
                if not medium_risk.empty:
                    st.subheader("🟠 Medium-Risk Cases")
                    st.dataframe(medium_risk, use_container_width=True, hide_index=True)

                low_risk = anomaly_df[anomaly_df['RISK_LEVEL'] == 'منخفضة الخطورة']
                if not low_risk.empty:
                    st.subheader("🟢 Low-Risk Cases")
                    st.dataframe(low_risk, use_container_width=True, hide_index=True)

                csv_data = export_to_csv_with_arabic(anomaly_df)
                st.download_button("📥 Download Anomaly Detection Results", data=csv_data, file_name="Anomaly_Detection.csv", mime="text/csv")
            else:
                st.info("🎉 No anomalous cases detected after excluding specified services.")

        except Exception as e:
            st.error(f"❌ An error occurred during processing: {str(e)}")

def main():
    setup_ui()

    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 20px;">
            <img src="https://img.icons8.com/color/96/000000/dental-braces.png" width="70" style="margin-bottom: 12px;">
            <h3 style="color: blue; margin: 0;">Dental Audit System</h3>
            <p style="color: #3f83fd; margin: 8px 0 0; font-size: 14px;">AI-Powered Dental Audit</p>
        </div>
        """, unsafe_allow_html=True)
        menu_options = ["Data Processing", "Upload Rules"] if st.session_state.get('rules_uploaded', False) else ["Upload Rules", "Data Processing"]
        choice = st.selectbox("Main Menu", menu_options, key="main_menu")
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; color: Blue; font-size: 14px; margin-top: 30px;">
            <p>Version 1.1.0</p>
            <p>Designed by</p>
            <p style="color: red; font-weight: bold; margin: 4px 0;">Mostafa El-beshbeshy</p>
            <p>©  Dental Audit System 2025</p>
        </div>
""", unsafe_allow_html=True)
    if choice == "Upload Rules":
        st.markdown("""
        <div class="data-header">
            <h2>⚙️ Dental Rules Management</h2>
        </div>
        """, unsafe_allow_html=True)
        upload_rules()
    elif choice == "Data Processing":
        process_data()

if __name__ == "__main__":
    init_db()
    main()