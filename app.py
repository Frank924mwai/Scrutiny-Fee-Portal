import streamlit as st
import pandas as pd
import math
from datetime import datetime
from typing import Tuple
from streamlit_gsheets import GSheetsConnection

# ── Page Configuration ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="BCC Town Planning & Estates Portal",
    page_icon="🏛️",
    layout="wide"
)

# ── High-Contrast Styling ─────────────────────────────────────────────────
st.markdown("""
<style>
:root {
    --navy: #1E65B5;
    --gold: #C49A2A;
    --bg: #F4F6FA;
    --card: #FFFFFF;
    --body: #3A4557;
    --border: #DDE3EE;
    --muted: #6B7A96;
}
.stApp { background-color: var(--bg); }
.portal-header { background-color: #1E65B5; border-radius: 8px; border-bottom: 4px solid #C49A2A; padding: 22px 26px; margin-bottom: 24px; }
.portal-title { margin: 0 0 14px 0; color: #FFFFFF !important; font-weight: 700; font-size: 1.35rem; letter-spacing: 0.04em; text-transform: uppercase; }
.card-title { font-size: 0.8rem; font-weight: 700; letter-spacing: 0.09em; text-transform: uppercase; color: var(--muted); margin-bottom: 16px; padding-bottom: 10px; border-bottom: 1px solid var(--border); }
.fee-result { background: var(--navy); border-radius: 10px; padding: 22px 26px; margin-top: 16px; border-left: 4px solid var(--gold); }
.fee-result .fee-label { color: #A8B8D0; font-size: 0.78rem; font-weight: 600; text-transform: uppercase; }
.fee-result .fee-amount { color: #FFFFFF; font-size: 1.9rem; font-weight: 700; }
.kpi-tile { background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 20px; text-align: center; }
</style>
""", unsafe_allow_html=True)

# ── Authentication ────────────────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    _, login_col, _ = st.columns([1, 2, 1])
    with login_col:
        with st.container(border=True):
            st.markdown("<h3 style='text-align: center; margin-top: 0;'>Secure Registry Authentication</h3>", unsafe_allow_html=True)
            with st.form("auth_form"):
                password_input = st.text_input("Internal Access Password", type="password")
                if st.form_submit_button("Verify Credentials", use_container_width=True):
                    try:
                        correct_password = st.secrets["auth"]["password"]
                        if password_input == correct_password:
                            st.session_state["authenticated"] = True
                            st.rerun()
                        else:
                            st.error("❌ Invalid password")
                    except:
                        st.error("❌ Secrets not configured. Contact administrator.")
    st.stop()

# ── Header ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="portal-header">
    <p class="portal-title">Department of Town Planning and Estates Services</p>
    <span style="background-color:#C49A2A; color:#1E65B5; padding:4px 12px; border-radius:4px; font-weight:700;">
        Charges Review 2026/2027
    </span>
</div>
""", unsafe_allow_html=True)

# ── Master Rates ──────────────────────────────────────────────────────────
BCC_RATES = {
    "Residential": {
        "High Density": {"rate": 170000.00, "unit": "sqm"},
        "Medium Density": {"rate": 190000.00, "unit": "sqm"},
        "Low Density": {"rate": 220000.00, "unit": "sqm"},
        "Multi- Units (Medium and Low)": {"rate": 350000.00, "unit": "sqm"},
    },
    "Institutional": {"Churches, Mosques and Schools": {"rate": 420000.00, "unit": "sqm"}},
    "Industrial Development": {"Factory / Warehouses": {"rate": 525000.00, "unit": "sqm"}},
    "Office/Commercial Development": {
        "Single Storey": {"rate": 525000.00, "unit": "sqm"},
        "Multi- Storey": {"rate": 650000.00, "unit": "sqm"},
    },
    "Fences": {"Security Fence": {"rate": 205000.00, "unit": "linear_meters"}},
    "Septic Tank": {"Septic Tank Installation": {"rate": 40000.00, "unit": "fixed_fee"}},
    "Advertising": {
        "Application Fee": {"rate": 15000.00, "unit": "fixed_fee"},
        "Billboard": {"rate": 750000.00, "unit": "fixed_fee"},
        "Single Sided Signpost": {"rate": 125000.00, "unit": "fixed_fee"},
        "Double Sided Signpost": {"rate": 190000.00, "unit": "fixed_fee"},
        "Composite Signpost": {"rate": 500000.00, "unit": "fixed_fee"},
        "Gantry": {"rate": 3000000.00, "unit": "fixed_fee"},
        "Cantilevered Billboard": {"rate": 2000000.00, "unit": "fixed_fee"},
    },
    "Miscellaneous": {
        "One surface car parking space": {"rate": 280000.00, "unit": "fixed_fee"},
        "Application in Principle (Outline Application)": {"rate": 750000.00, "unit": "fixed_fee"},
        "Change of Use": {"rate": 750000.00, "unit": "fixed_fee"},
        "Subdivision per plot created": {"rate": 150000.00, "unit": "fixed_fee"},
        "Plot Regularisation": {"rate": 500000.00, "unit": "fixed_fee"},
        "Infill Plot Creation": {"rate": 500000.00, "unit": "fixed_fee"},
        "Sewer Application Fees": {"rate": 100000.00, "unit": "fixed_fee"},
        "Certificate of Occupancy": {"rate": 0.001, "unit": "percentage_of_final_cost"},
        "LPG Exchange Cage": {"rate": 150000.00, "unit": "fixed_fee"},
        "LPG Exchange & Filler Cage": {"rate": 200000.00, "unit": "fixed_fee"},
        "Site Plan Certification": {"rate": 15000.00, "unit": "fixed_fee"},
        "Kiosks for Mobile Money": {"rate": 190000.00, "unit": "fixed_fee"},
    },
}

ESTATES_FEES = {
    "Application Forms": {
        "Residential Plot (THA)": {"rate": 30000.00, "unit": "fixed_fee"},
        "Residential Plot (PHA)": {"rate": 60000.00, "unit": "fixed_fee"},
        "Commercial Plot": {"rate": 150000.00, "unit": "fixed_fee"},
        "Land Lease Plot (THA)": {"rate": 100000.00, "unit": "fixed_fee"},
        "Land Lease Plot (PHA)": {"rate": 150000.00, "unit": "fixed_fee"},
    },
    "Legal Services Fees": {
        "Consent Application Fee": {"rate": 80000.00, "unit": "fixed_fee"},
        "Legal Fee": {"rate": 150000.00, "unit": "fixed_fee"},
    },
    "Processing & Allocation Fees": {
        "Residential Plot": {"rate": 200000.00, "unit": "fixed_fee"},
        "Church Plot": {"rate": 250000.00, "unit": "fixed_fee"},
        "School Plot": {"rate": 500000.00, "unit": "fixed_fee"},
        "Commercial Plot (per 0.0036 ha)": {"rate": 550000.00, "unit": "qty_based"},
        "Industrial Plot (per 0.0036 ha)": {"rate": 550000.00, "unit": "qty_based"},
    },
    "Ground Rents": {
        "THA": {"rate": 35000.00, "unit": "fixed_fee"},
        "High Density": {"rate": 60000.00, "unit": "fixed_fee"},
        "Medium Density": {"rate": 80000.00, "unit": "fixed_fee"},
        "Commercial BY MKT Value": {"rate": 0.075, "unit": "market_value"},
    },
    "Legalisation": {"Legalisation (THA)": {"rate": 2000000.00, "unit": "fixed_fee"}},
    "Change of Ownership": {
        "Next of Kin": {"rate": 120000.00, "unit": "fixed_fee"},
        "Private Sale (THA)": {"rate": 200000.00, "unit": "fixed_fee"},
        "Private Sale (PHA)": {"rate": 350000.00, "unit": "fixed_fee"},
    },
    "Development Charges": {"THAs per 0.036 ha": {"rate": 2000000.00, "unit": "qty_based"}},
    "Beacon Replacement & Survey": {
        "First Beacon": {"rate": 80000.00, "unit": "fixed_fee"},
        "Extra beacon": {"rate": 40000.00, "unit": "qty_based"},
        "Survey of Plot": {"rate": 200000.00, "unit": "fixed_fee"},
        "Survey drawing & computation fees (0.036ha)": {"rate": 150000.00, "unit": "qty_based"},
    }
}

RATE_04_CATS = {"Residential", "Institutional", "Industrial Development", "Office/Commercial Development", "Fences"}

COLUMNS = ["Application ID", "Date Received", "Applicant Name", "Plot Number", "Department",
           "Category", "Development Type", "Dimension/Qty", "Est. Cost (MK)", "Total Fee (MK)", "Completed Steps"]

# ── Helper Function ───────────────────────────────────────────────────────
def _calc_raw_base_fee(dept: str, category: str, rate_info: dict, qty: float, premium: float = 0.0) -> Tuple[float, float]:
    if dept == "Town Planning (Scrutiny)":
        if category in RATE_04_CATS:
            est_cost = qty * rate_info["rate"]
            fee = est_cost * 0.004
        elif rate_info.get("unit") == "percentage_of_final_cost":
            est_cost = qty
            fee = est_cost * rate_info["rate"]
        else:
            est_cost = 0.0
            fee = qty * rate_info["rate"]
    else:
        if rate_info.get("unit") == "market_value":
            est_cost = premium * qty
            fee = est_cost * rate_info["rate"]
        elif rate_info.get("unit") == "qty_based":
            est_cost = 0.0
            fee = qty * rate_info["rate"]
        else:
            est_cost = 0.0
            fee = rate_info["rate"] * qty
    return est_cost, fee

# ── Data Connection ───────────────────────────────────────────────────────
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=5)
def load_data() -> pd.DataFrame:
    try:
        df = conn.read(ttl="5s")
        if df is None or df.empty:
            return pd.DataFrame(columns=COLUMNS)
        for col in COLUMNS:
            if col not in df.columns:
                df[col] = "N/A" if col in ["Application ID","Applicant Name","Plot Number","Department","Category","Development Type","Completed Steps"] else 0.0
        df["Date Received"] = pd.to_datetime(df["Date Received"], errors='coerce')
        for num_col in ["Total Fee (MK)", "Est. Cost (MK)", "Dimension/Qty"]:
            df[num_col] = pd.to_numeric(df[num_col], errors='coerce').fillna(0.0)
        return df
    except Exception:
        return pd.DataFrame(columns=COLUMNS)

df_bcc = load_data()

# ── Sidebar ───────────────────────────────────────────────────────────────
st.sidebar.markdown("### 🏛️ BCC PORTAL")
st.sidebar.markdown("---")
PAGE_MAP = {
    "🧮 Fee Calculator": "calculator",
    "📥 New Application Intake": "intake",
    "📊 Submission Analytics": "analytics",
    "🛤️ Process Tracking": "tracker"
}
current_page = PAGE_MAP[st.sidebar.radio("Navigate to:", list(PAGE_MAP.keys()))]

# ==============================================================================
# FEE CALCULATOR
# ==============================================================================
if current_page == "calculator":
    st.markdown("## 🧮 FEE CALCULATOR")
    st.markdown("---")
    
    dept_choice = st.radio("Select Department", ["Town Planning (Scrutiny)", "Estates Services"], horizontal=True)
    target_dict = BCC_RATES if dept_choice == "Town Planning (Scrutiny)" else ESTATES_FEES

    col1, col2 = st.columns([1, 1])
    with col1:
        category = st.selectbox("Category", list(target_dict.keys()))
        subcategory = st.selectbox("Service / Development Type", list(target_dict[category].keys()))
        item_details = target_dict[category][subcategory]
        unit_type = item_details["unit"]

        if unit_type == "sqm":
            input_val = st.number_input("Total Built-up Area (sqm)", min_value=0.0, value=100.0)
        elif unit_type == "linear_meters":
            input_val = st.number_input("Total Length (meters)", min_value=0.0, value=50.0)
        elif unit_type == "percentage_of_final_cost":
            input_val = st.number_input("Final Structural Cost (MK)", min_value=0.0, value=5000000.0)
        elif unit_type == "market_value":
            premium = st.number_input("Premium Value (MK)", min_value=0.0, value=1000000.0)
            input_val = st.number_input("Plot Area (sqm)", min_value=0.0, value=1000.0)
        else:
            input_val = st.number_input("Quantity", min_value=1.0, value=1.0)

    estimated_cost, base_fee = _calc_raw_base_fee(dept_choice, category, item_details, input_val)
    total_fee_due = base_fee

    with col2:
        st.markdown(f"""
        <div class="fee-result">
            <div class="fee-label">TOTAL FEE PAYABLE ({dept_choice})</div>
            <div class="fee-amount">MK {total_fee_due:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)

# ==============================================================================
# NEW APPLICATION INTAKE (FIXED)
# ==============================================================================
elif current_page == "intake":
    st.markdown("## 📥 NEW APPLICATION INTAKE")
    st.markdown("---")

    intake_dept = st.radio("Department", ["Town Planning (Scrutiny)", "Estates Services"], horizontal=True)
    target_dict = BCC_RATES if intake_dept == "Town Planning (Scrutiny)" else ESTATES_FEES

    col1, col2 = st.columns(2)
    with col1:
        app_id = st.text_input("Application ID", placeholder="BCC/TP/2026/250")
        applicant_name = st.text_input("Applicant Name")
        date_rcvd = st.date_input("Date Received", value=datetime.today())
    with col2:
        plot_number = st.text_input("Plot Number")
        category = st.selectbox("Category", list(target_dict.keys()))
        subcategory = st.selectbox("Development Type", list(target_dict[category].keys()))

    total_fee_paid = st.number_input("Total Fee Received (MK)", min_value=0.0, step=1000.0, value=0.0)

    if st.button("📄 Save to Registry", type="primary", use_container_width=True):
        if not app_id or not applicant_name or not plot_number:
            st.error("❌ Application ID, Applicant Name and Plot Number are required.")
        else:
            rate_info = target_dict[category][subcategory]
            est_cost, _ = _calc_raw_base_fee(intake_dept, category, rate_info, total_fee_paid / rate_info["rate"] if rate_info["rate"] > 0 else 0)

            new_row = {
                "Application ID": app_id.strip().upper(),
                "Date Received": date_rcvd.strftime("%Y-%m-%d"),
                "Applicant Name": applicant_name.strip(),
                "Plot Number": plot_number.strip(),
                "Department": intake_dept,
                "Category": category,
                "Development Type": subcategory,
                "Dimension/Qty": round(total_fee_paid / rate_info["rate"] if rate_info["rate"] > 0 else 0, 2),
                "Est. Cost (MK)": round(est_cost, 2),
                "Total Fee (MK)": round(total_fee_paid, 2),
                "Completed Steps": ""
            }

            try:
                df_existing = conn.read(ttl=0) or pd.DataFrame(columns=COLUMNS)
                df_updated = pd.concat([df_existing, pd.DataFrame([new_row])], ignore_index=True)
                
                # Ensure date is saved correctly
                df_updated["Date Received"] = pd.to_datetime(df_updated["Date Received"], errors='coerce').dt.strftime("%Y-%m-%d")
                
                conn.update(data=df_updated)
                st.cache_data.clear()
                st.success(f"✅ Record for **{applicant_name}** saved successfully!")
                st.balloons()
            except Exception as e:
                st.error(f"❌ Save failed: {str(e)}")

# ==============================================================================
# ANALYTICS & TRACKER (Simplified)
# ==============================================================================
elif current_page == "analytics":
    st.markdown("## 📊 SUBMISSION ANALYTICS")
    st.markdown("---")
    st.info("Analytics module - full version can be restored if needed.")

elif current_page == "tracker":
    st.markdown("## 🛤️ PROCESS TRACKING")
    st.markdown("---")
    st.info("Tracker module - full version can be restored if needed.")

# ── Footer ────────────────────────────────────────────────────────────────
st.sidebar.caption("Blantyre City Council • Town Planning & Estates")
