import streamlit as st
import pandas as pd
import math
import plotly.express as px
from datetime import datetime
import time
from typing import Tuple
from streamlit_gsheets import GSheetsConnection

# ── Page Configuration ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="BCC Town Planning & Estates Portal",
    page_icon="city.png",
    layout="wide"
)

# ── Global High-Contrast + Mobile Fixes ────────────────────────────────────
st.markdown("""
<style>
/* High-contrast overrides */
div[data-testid="stMarkdownContainer"] p,
div[data-testid="stMarkdownContainer"] span,
.stSlider label, .stNumberInput label, label[data-testid="stWidgetLabel"] p,
div[data-testid="stRadio"] label div[data-testid="stMarkdownContainer"] p {
    color: #1A202C !important;
    font-weight: 500 !important;
}
h3 { color: #1E65B5 !important; }
/* Palette */
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
/* Sidebar */
[data-testid="stSidebar"] { background-color: var(--navy) !important; }
[data-testid="stSidebar"] * { color: #E8EDF5 !important; }
/* Buttons */
div.stButton > button {
    background-color: var(--navy) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 10px 24px !important;
    font-weight: 600 !important;
}
div.stButton > button:hover {
    background-color: #243660 !important;
}
/* Input Container Backgrounds */
[data-testid="stTextInput"] div[data-baseweb="input"] > div,
[data-testid="stNumberInput"] div[data-baseweb="input"] > div,
[data-testid="stDateInput"] div[data-baseweb="input"] > div,
[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
    background-color: #FFFFFF !important;
    border: 1px solid #DDE3EE !important;
}
/* Input Text Colors */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stDateInput"] input,
[data-testid="stSelectbox"] div[data-baseweb="select"] {
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
}
/* Radio Buttons */
div[role="radiogroup"] div[data-baseweb="radio"] > div:first-child {
    background-color: #FFFFFF !important;
    border: 2px solid #000000 !important;
}
div[role="radiogroup"] div[data-baseweb="radio"] input:checked + div > div {
    background-color: #1E65B5 !important;
}
/* Custom CSS classes */
.card-title { font-size: 0.78rem; font-weight: 700; letter-spacing: 0.09em; text-transform: uppercase; color: var(--muted); margin-bottom: 16px; padding-bottom: 10px; border-bottom: 1px solid var(--border); }
.kpi-tile { background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 20px 24px; text-align: center; }
.kpi-label { font-size: 0.75rem; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; color: var(--muted); margin-bottom: 8px; }
.kpi-value { font-size: 1.6rem; font-weight: 700; color: var(--navy); line-height: 1.1; }
.kpi-sub { font-size: 0.75rem; color: var(--muted); margin-top: 4px; }
.fee-result { background: var(--navy); border-radius: 10px; padding: 22px 26px; margin-top: 16px; border-left: 4px solid var(--gold); }
.fee-result .fee-label { color: #A8B8D0; font-size: 0.78rem; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 6px; }
.fee-result .fee-amount { color: #FFFFFF; font-size: 1.9rem; font-weight: 700; letter-spacing: -0.02em; }
.fee-result .fee-note { color: var(--gold); font-size: 0.78rem; margin-top: 6px; }
.bcc-divider { border: none; border-top: 1px solid var(--border); margin: 24px 0; }
.tracker-step { padding: 12px; margin-bottom: 8px; background: #FFFFFF; border-left: 4px solid #1E65B5; border-radius: 4px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
.tracker-title { font-weight: 600; color: #1B2A4A; font-size: 0.95rem; }
.tracker-desc { font-size: 0.8rem; color: #6B7A96; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)

# ── Portal Header Band ────────────────────────────────────────────────────────
header_html = (
    '<div style="background-color: #1E65B5; border-radius: 8px; border-bottom: 4px solid #C49A2A; padding: 22px 26px; margin-bottom: 28px; width: 100%; box-sizing: border-box;">'
    ' <p style="margin: 0 0 14px 0; color: #FFFFFF !important; font-weight: 700; font-size: 1.25rem; letter-spacing: 0.04em; line-height: 1.3; text-transform: uppercase;">'
    ' Department of Town Planning and Estates Services'
    ' </p>'
    ' <div style="display: flex; flex-wrap: wrap; gap: 12px; align-items: center;">'
    ' <span style="background-color: #C49A2A; color: #1E65B5; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; border-radius: 4px; padding: 5px 12px; display: inline-block;">'
    ' Charges Review 2026/2027 &nbsp;·&nbsp; Effective Rates'
    ' </span>'
    ' <span style="color: #FFFFFF !important; font-size: 0.8rem; font-weight: 500; font-style: italic; display: inline-block; letter-spacing: 0.02em;">'
    ' Created by GIS Specialist Frank Chingoka'
    ' </span>'
    ' </div>'
    '</div>'
)
st.markdown(header_html, unsafe_allow_html=True)

# ── Authentication ─────────────────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    _, login_col, _ = st.columns([1, 1.5, 1])
    with login_col:
        with st.container(border=True):
            st.markdown("<h3 style='text-align: center; margin-top: 0; margin-bottom: 20px;'>Secure Registry Authentication</h3>", unsafe_allow_html=True)
            password_input = st.text_input("Internal Access Password", type="password", placeholder="••••••••")
            submit_auth = st.button("Verify Credentials", use_container_width=True)
           
            if submit_auth:
                try:
                    correct_password = st.secrets["auth"]["password"]
                except Exception:
                    st.error(" ❌ Secrets not configured. Contact administrator.")
                    correct_password = None
               
                if correct_password and password_input == correct_password:
                    st.session_state["authenticated"] = True
                    st.session_state.prev_page = "calculator"
                    st.rerun()
                else:
                    st.error(" ❌ Invalid access token. Please verify credentials and re-enter.")
    st.stop()

# ── Master Data Dictionaries ────────────────────────────────────────────────
BCC_RATES = {
    "Residential": {
        "High Density": {"rate": 170000.00, "unit": "sqm"},
        "Medium Density": {"rate": 190000.00, "unit": "sqm"},
        "Low Density": {"rate": 220000.00, "unit": "sqm"},
        "Multi- Units (Medium and Low)": {"rate": 350000.00, "unit": "sqm"},
    },
    "Institutional": {
        "Churches, Mosques and Schools": {"rate": 420000.00, "unit": "sqm"},
    },
    "Industrial Development": {
        "Factory / Warehouses": {"rate": 525000.00, "unit": "sqm"},
    },
    "Office/Commercial Development": {
        "Single Storey": {"rate": 525000.00, "unit": "sqm"},
        "Multi- Storey": {"rate": 650000.00, "unit": "sqm"},
    },
    "Fences": {
        "Security Fence": {"rate": 205000.00, "unit": "linear_meters"},
    },
    "Septic Tank": {
        "Septic Tank Installation": {"rate": 40000.00, "unit": "fixed_fee"},
    },
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
    "Legalisation": {
        "Legalisation (THA)": {"rate": 2000000.00, "unit": "fixed_fee"},
    },
    "Change of Ownership": {
        "Next of Kin": {"rate": 120000.00, "unit": "fixed_fee"},
        "Private Sale (THA)": {"rate": 200000.00, "unit": "fixed_fee"},
        "Private Sale (PHA)": {"rate": 350000.00, "unit": "fixed_fee"},
    },
    "Development Charges": {
        "THAs per 0.036 ha": {"rate": 2000000.00, "unit": "qty_based"},
    },
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

def _calc_raw_base_fee(dept: str, category: str, rate_info: dict, qty: float, premium: float = 0.0) -> Tuple[float, float]:
    """Calculates pure base fee depending on Department and category types."""
    if dept == "Town Planning (Scrutiny)":
        if category in RATE_04_CATS:
            est_cost = qty * rate_info["rate"]
            fee = est_cost * 0.004
        elif rate_info["unit"] == "percentage_of_final_cost":
            est_cost = qty
            fee = est_cost * rate_info["rate"]
        else:
            est_cost = 0.0
            fee = qty * rate_info["rate"]
        return est_cost, fee
    else:
        # Estates Logic
        if rate_info["unit"] == "market_value":
            est_cost = premium * qty
            fee = premium * rate_info["rate"] * qty
        elif rate_info["unit"] == "qty_based":
            est_cost = 0.0
            fee = qty * rate_info["rate"]
        else:
            est_cost = 0.0
            fee = rate_info["rate"] * qty
        return est_cost, fee

# ── Google Sheets Connection ───────────────────────────────────────────────
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=5)
def load_data() -> pd.DataFrame:
    try:
        df = conn.read(ttl="5s")
        if df is None or df.empty:
            return pd.DataFrame(columns=COLUMNS)
       
        for col in COLUMNS:
            if col not in df.columns:
                df[col] = "N/A"
       
        df["Department"] = df["Department"].replace({"N/A": "Town Planning (Scrutiny)"})
       
        if "Category" in df.columns:
            df["Category"] = df["Category"].astype(str).str.title()
           
        df["Date Received"] = pd.to_datetime(df["Date Received"], errors='coerce')
       
        if "Scrutiny Fee (MK)" in df.columns and df["Total Fee (MK)"].eq("N/A").all():
            df["Total Fee (MK)"] = df["Scrutiny Fee (MK)"]
           
        return df
    except Exception:
        return pd.DataFrame(columns=COLUMNS)

df_bcc = load_data()

# ── Sidebar ────────────────────────────────────────────────────────────────
st.sidebar.markdown("### 🏛 BCC PORTAL")
st.sidebar.markdown("---")
PAGE_MAP = {
    " 🧮 Fee Calculator": "calculator",
    " 📥 New Application Intake": "intake",
    " 📊 Submission Analytics": "analytics",
    " 🛤️ Process Tracking": "tracker"
}
selected_label = st.sidebar.radio("Navigate to:", list(PAGE_MAP.keys()), key="sidebar_nav")
current_page = PAGE_MAP[selected_label]

# ── Page Change Handler ────────────────────────────────────────────────────
if "prev_page" not in st.session_state:
    st.session_state.prev_page = current_page

if st.session_state.prev_page != current_page:
    keys_to_clear = [k for k in st.session_state.keys()
                     if k.startswith("calc_") or k.startswith("intake_") or k.startswith("trend_") or k.startswith("dept_")]
    for k in keys_to_clear:
        if k in st.session_state:
            del st.session_state[k]
    st.session_state.prev_page = current_page
    st.rerun()

# ── Dashboard Controls ─────────────────────────────────────────────────────
st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ DASHBOARD CONTROLS")
live_mode = st.sidebar.toggle(" 🔄 Enable Real-Time Live View", value=False)
if live_mode:
    refresh_rate = st.sidebar.slider("Refresh Interval (seconds)", 5, 60, 10)
st.sidebar.markdown("---")
st.sidebar.caption("Blantyre City Council · Town Planning & Estates")

# ══════════════════════════════════════════════════════════════════════════════
# MODULE 1 — FEE CALCULATOR (DUAL DEPARTMENT)
# ══════════════════════════════════════════════════════════════════════════════
if current_page == "calculator":
    st.markdown("## 🧮 FEE CALCULATOR")
    st.markdown("<hr class='bcc-divider'>", unsafe_allow_html=True)
   
    dept_choice = st.radio("Select Department Parameter", ["Town Planning (Scrutiny)", "Estates Services"], horizontal=True, key="calc_dept")
    target_dict = BCC_RATES if dept_choice == "Town Planning (Scrutiny)" else ESTATES_FEES
    col1, col2 = st.columns([1, 1], gap="large")
    with col1:
        with st.container(border=True):
            st.markdown('<div class="card-title">Development / Service Parameters</div>', unsafe_allow_html=True)
           
            category = st.selectbox("Plan Category", list(target_dict.keys()), key="calc_cat")
            subcategory = st.selectbox("Service / Development Type", list(target_dict[category].keys()), key="calc_sub")
           
            item_details = target_dict[category][subcategory]
            base_rate = item_details["rate"]
            unit_type = item_details["unit"]
            is_04 = (category in RATE_04_CATS) and (dept_choice == "Town Planning (Scrutiny)")
           
            premium_val = 0.0
           
            if unit_type == "sqm":
                st.markdown("<hr class='bcc-divider'>", unsafe_allow_html=True)
                st.markdown('<div class="card-title"> 📐 Area Determination Method</div>', unsafe_allow_html=True)
                input_method = st.radio("Entry format:", ["Enter Total Area Manually", "Calculate Using Geometric Shapes"], horizontal=True, key="calc_method")
                if input_method == "Enter Total Area Manually":
                    input_val = st.number_input("Total Built-up Area (Square Meters)", min_value=0.0, value=100.0, step=10.0, key="calc_man_sqm")
                else:
                    shape = st.selectbox("Select Shape Profile:", ["Rectangle", "Triangle", "Trapezium", "Circle", "Semicircle"], key="calc_shape")
                    if shape == "Rectangle":
                        length = st.number_input("Length (m)", min_value=0.0, value=20.0, step=1.0)
                        width = st.number_input("Width (m)", min_value=0.0, value=15.0, step=1.0)
                        input_val = length * width
                    elif shape == "Triangle":
                        base = st.number_input("Base Length (m)", min_value=0.0, value=15.0, step=1.0)
                        height = st.number_input("Perpendicular Height (m)", min_value=0.0, value=10.0, step=1.0)
                        input_val = 0.5 * base * height
                    elif shape == "Trapezium":
                        side_a = st.number_input("Parallel Side A (m)", min_value=0.0, value=12.0, step=1.0)
                        side_b = st.number_input("Parallel Side B (m)", min_value=0.0, value=18.0, step=1.0)
                        trap_height = st.number_input("Distance / Height (m)", min_value=0.0, value=8.0, step=1.0)
                        input_val = 0.5 * (side_a + side_b) * trap_height
                    elif shape == "Circle":
                        radius = st.number_input("Radius (m)", min_value=0.0, value=7.0, step=0.5)
                        input_val = math.pi * radius ** 2
                    elif shape == "Semicircle":
                        semi_radius = st.number_input("Radius (m)", min_value=0.0, value=7.0, step=0.5)
                        input_val = 0.5 * math.pi * semi_radius ** 2
                st.metric(label="Calculated Spatial Footprint", value=f"{input_val:,.2f} sqm")
           
            elif unit_type == "linear_meters":
                input_val = st.number_input("Total Fence Length (Meters)", min_value=0.0, value=50.0, step=5.0)
           
            elif unit_type == "percentage_of_final_cost":
                input_val = st.number_input("Declared Final Structural Cost (MK)", min_value=0.0, value=5000000.0, step=100000.0)
           
            elif unit_type == "market_value":
                premium_val = st.number_input("Premium Value (MK)", min_value=0.0, value=1000000.0, step=50000.0)
                input_val = st.number_input("Plot Area (Square Meters)", min_value=0.0, value=1000.0, step=10.0)
               
            elif unit_type == "qty_based":
                input_val = st.number_input("Quantity (e.g. number of 0.036ha portions or beacons)", min_value=1.0, value=1.0, step=1.0)
               
            else:
                input_val = st.number_input("Quantity / Units", min_value=1.0, value=1.0, step=1.0)
        addon_accumulated = 0.0
        if dept_choice == "Town Planning (Scrutiny)":
            with st.container(border=True):
                st.markdown('<div class="card-title"> 📦 Combine Additional Fees (Optional)</div>', unsafe_allow_html=True)
                show_app_checkbox = not (category == "Advertising" and subcategory == "Application Fee")
               
                calc_inc_app = st.checkbox("Include Base Application Fee (MK 15,000)", value=show_app_checkbox, disabled=not show_app_checkbox)
                calc_inc_septic = st.checkbox("Include Septic Tank Fee (MK 40,000)", value=False)
                calc_inc_site = st.checkbox("Include Site Plan Cert. (MK 15,000)", value=False)
                calc_inc_parking = st.checkbox("Include Surface Car Parking (MK 280,000)", value=False)
                calc_inc_sewer = st.checkbox("Include Sewer Application Fee (MK 100,000)", value=False)
               
                if calc_inc_app and show_app_checkbox: addon_accumulated += BCC_RATES["Advertising"]["Application Fee"]["rate"]
                if calc_inc_septic: addon_accumulated += BCC_RATES["Septic Tank"]["Septic Tank Installation"]["rate"]
                if calc_inc_site: addon_accumulated += BCC_RATES["Miscellaneous"]["Site Plan Certification"]["rate"]
                if calc_inc_parking: addon_accumulated += BCC_RATES["Miscellaneous"]["One surface car parking space"]["rate"]
                if calc_inc_sewer: addon_accumulated += BCC_RATES["Miscellaneous"]["Sewer Application Fees"]["rate"]
        estimated_cost, base_fee = _calc_raw_base_fee(dept_choice, category, item_details, input_val, premium_val)
        total_fee_due = base_fee + addon_accumulated
    with col2:
        with st.container(border=True):
            st.markdown('<div class="card-title">Assessment Breakdown</div>', unsafe_allow_html=True)
           
            st.markdown(f"""
            <div style="background:#F4F6FA;border-radius:8px;padding:14px 18px;margin-bottom:16px;border:1px solid #DDE3EE;">
                <div style="font-size:0.75rem;color:#6B7A96;font-weight:600;text-transform:uppercase;letter-spacing:0.07em;margin-bottom:4px;">Category</div>
                <div style="font-size:0.95rem;color:#1B2A4A;font-weight:600;">{category}</div>
                <div style="font-size:0.75rem;color:#6B7A96;font-weight:600;text-transform:uppercase;letter-spacing:0.07em;margin-top:10px;margin-bottom:4px;">Development Type</div>
                <div style="font-size:0.95rem;color:#1B2A4A;font-weight:600;">{subcategory}</div>
            </div>
            """, unsafe_allow_html=True)
           
            if is_04 or unit_type == "market_value":
                label_text = "Estimated Development Cost" if is_04 else "Calculated Base Valuation"
                card_html = (
                    '<div style="display:flex;gap:12px;margin-bottom:12px;">'
                    ' <div style="flex:1;background:#F4F6FA;border-radius:8px;padding:14px;border:1px solid #DDE3EE;text-align:center;">'
                    ' <div style="font-size:0.72rem;color:#6B7A96;font-weight:600;text-transform:uppercase;letter-spacing:0.07em;">Base Rate/Multiplier</div>'
                    f' <div style="font-size:1.1rem;font-weight:700;color:#1B2A4A;">{base_rate:,.3f}</div>'
                    ' </div>'
                    ' <div style="flex:1;background:#F4F6FA;border-radius:8px;padding:14px;border:1px solid #DDE3EE;text-align:center;">'
                    ' <div style="font-size:0.72rem;color:#6B7A96;font-weight:600;text-transform:uppercase;letter-spacing:0.07em;">Metric / Qty</div>'
                    f' <div style="font-size:1.1rem;font-weight:700;color:#1B2A4A;">{input_val:,.2f}</div>'
                    ' </div>'
                    '</div>'
                    '<div style="background:#F4F6FA;border-radius:8px;padding:14px 18px;margin-bottom:12px;border:1px solid #DDE3EE;">'
                    f' <div style="font-size:0.72rem;color:#6B7A96;font-weight:600;text-transform:uppercase;letter-spacing:0.07em;margin-bottom:4px;">{label_text}</div>'
                    f' <div style="font-size:1.35rem;font-weight:700;color:#1B2A4A;">MK {estimated_cost:,.2f}</div>'
                    '</div>'
                )
                st.markdown(card_html, unsafe_allow_html=True)
               
            if addon_accumulated > 0:
                addon_html = (
                    '<div style="background:#F4F6FA;border-radius:8px;padding:14px 18px;margin-bottom:12px;border:1px solid #DDE3EE; display:flex; justify-content:space-between; align-items:center;">'
                    ' <div>'
                    ' <div style="font-size:0.72rem;color:#6B7A96;font-weight:600;text-transform:uppercase;letter-spacing:0.07em;">Base Fee Due</div>'
                    f' <div style="font-size:1.05rem;font-weight:700;color:#1B2A4A;">MK {base_fee:,.2f}</div>'
                    ' </div>'
                    ' <div style="text-align:right;">'
                    ' <div style="font-size:0.72rem;color:#6B7A96;font-weight:600;text-transform:uppercase;letter-spacing:0.07em;">Combined Add-ons</div>'
                    f' <div style="font-size:1.05rem;font-weight:700;color:#2463EB;">+ MK {addon_accumulated:,.2f}</div>'
                    ' </div>'
                    '</div>'
                )
                st.markdown(addon_html, unsafe_allow_html=True)
               
            st.markdown(f"""
            <div class="fee-result">
                <div class="fee-label">Total Invoice Amount Payable</div>
                <div class="fee-amount">MK {total_fee_due:,.2f}</div>
                <div class="fee-note">Reflects calculations for {dept_choice} procedures.</div>
            </div>
            """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# MODULE 2 — NEW APPLICATION INTAKE
# ══════════════════════════════════════════════════════════════════════════════
elif current_page == "intake":
    st.markdown("## 📥 NEW APPLICATION INTAKE")
    st.markdown("<hr class='bcc-divider'>", unsafe_allow_html=True)
    st.markdown("Complete the fields below to register a new plan submission or estate service to the BCC registry.")
    intake_dept = st.radio("Select Department", ["Town Planning (Scrutiny)", "Estates Services"], horizontal=True, key="intake_dept")
    target_dict = BCC_RATES if intake_dept == "Town Planning (Scrutiny)" else ESTATES_FEES
    col1, col2 = st.columns(2, gap="large")
    with col1:
        app_id = st.text_input("Application / File ID", placeholder="e.g., BCC/TP/2026/250")
        applicant_name = st.text_input("Applicant Name / Developer Entity")
        date_rcvd = st.date_input("Date Received", value=datetime.today())
    with col2:
        plot_number = st.text_input("Plot Number / Parcel ID")
        intake_category = st.selectbox("Category", list(target_dict.keys()), key="intake_cat")
        intake_subcategory = st.selectbox("Development Type", list(target_dict[intake_category].keys()), key="intake_sub")
    st.markdown("<hr class='bcc-divider'>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown('<div class="card-title">Financial Metrics Input</div>', unsafe_allow_html=True)
        rate_info = target_dict[intake_category][intake_subcategory]
        input_fee_paid = st.number_input("Total Amount Received on Receipt (MK)", min_value=0.0, value=50000.0, step=5000.0)
        is_tp = (intake_dept == "Town Planning (Scrutiny)")
       
        st.markdown("<div style='font-size:0.80rem; color:#6B7A96; font-weight:700; text-transform:uppercase; letter-spacing:0.05em; margin-top:15px; margin-bottom:5px;'>Check items included in this receipt total:</div>", unsafe_allow_html=True)
       
        bundle_col1, bundle_col2, bundle_col3 = st.columns(3)
        with bundle_col1:
            intake_inc_app = st.checkbox("Base Application Fee (MK 15,000)", value=True, disabled=not is_tp)
            intake_inc_site = st.checkbox("Site Plan Cert. (MK 15,000)", value=False, disabled=not is_tp)
        with bundle_col2:
            intake_inc_septic = st.checkbox("Septic Tank Installation (MK 40,000)", value=False, disabled=not is_tp)
            intake_inc_sewer = st.checkbox("Sewer Application Fee (MK 100,000)", value=False, disabled=not is_tp)
        with bundle_col3:
            intake_inc_parking = st.checkbox("Surface Car Parking (MK 280,000)", value=False, disabled=not is_tp)
        deductions = 0.0
        if is_tp:
            if intake_inc_app: deductions += BCC_RATES["Advertising"]["Application Fee"]["rate"]
            if intake_inc_septic: deductions += BCC_RATES["Septic Tank"]["Septic Tank Installation"]["rate"]
            if intake_inc_site: deductions += BCC_RATES["Miscellaneous"]["Site Plan Certification"]["rate"]
            if intake_inc_parking: deductions += BCC_RATES["Miscellaneous"]["One surface car parking space"]["rate"]
            if intake_inc_sewer: deductions += BCC_RATES["Miscellaneous"]["Sewer Application Fees"]["rate"]
        st.markdown("<br>", unsafe_allow_html=True)
        submit_btn = st.button(" 📄 Append Entry to Registry", use_container_width=True)
        if submit_btn:
            errors = []
            if not app_id.strip(): errors.append("Application ID Reference Number is required.")
            if not applicant_name.strip(): errors.append("Applicant Name is required.")
            if not plot_number.strip(): errors.append("Plot Number is required.")
           
            if errors:
                for e in errors: st.error(f" ❌ {e}")
            else:
                net_fee = max(0.0, input_fee_paid - deductions)
               
                if intake_dept == "Town Planning (Scrutiny)" and (intake_category in RATE_04_CATS):
                    calc_est_cost = net_fee / 0.004
                    derived_dimension = calc_est_cost / rate_info["rate"] if rate_info["rate"] > 0 else 0.0
                elif rate_info["unit"] in ["percentage_of_final_cost", "market_value"]:
                    calc_est_cost = net_fee / rate_info["rate"] if rate_info["rate"] > 0 else 0.0
                    derived_dimension = calc_est_cost
                else:
                    calc_est_cost = 0.0
                    derived_dimension = net_fee / rate_info["rate"] if rate_info["rate"] > 0 else 1.0
                new_row = {
                    "Application ID": app_id.strip().upper(),
                    "Date Received": date_rcvd.strftime("%Y-%m-%d"),
                    "Applicant Name": applicant_name.strip(),
                    "Plot Number": plot_number.strip(),
                    "Department": intake_dept,
                    "Category": intake_category,
                    "Development Type": intake_subcategory,
                    "Dimension/Qty": round(derived_dimension, 2),
                    "Est. Cost (MK)": round(calc_est_cost, 2),
                    "Total Fee (MK)": input_fee_paid,
                }
               
                try:
                    df_existing = conn.read(ttl=0)
                except Exception:
                    df_existing = pd.DataFrame(columns=COLUMNS)
                   
                df_updated = pd.concat([df_existing, pd.DataFrame([new_row])], ignore_index=True)
                conn.update(data=df_updated)
                st.cache_data.clear()
                st.success(f" ✅ Record for **{applicant_name.strip()} ({plot_number.strip()})** appended securely to cloud index file.")
                st.balloons()

# ══════════════════════════════════════════════════════════════════════════════
# MODULE 3 — SUBMISSION ANALYTICS
# ══════════════════════════════════════════════════════════════════════════════
elif current_page == "analytics":
    st.markdown("## 📊 SUBMISSION ANALYTICS")
    st.markdown("<hr class='bcc-divider'>", unsafe_allow_html=True)
   
    view_filter = st.radio("View Data For:", ["All Departments", "Town Planning (Scrutiny)", "Estates Services"], horizontal=True, key="analytics_view")
    
    df_filtered = df_bcc.copy()
    if view_filter == "Town Planning (Scrutiny)":
        df_filtered = df_filtered[df_filtered["Department"] == "Town Planning (Scrutiny)"]
    elif view_filter == "Estates Services":
        df_filtered = df_filtered[df_filtered["Department"] == "Estates Services"]
    # For All Departments: keep both (already in df_filtered)

    if df_filtered.empty:
        st.info(" 📭 No applications on record for this selection. Use **New Application Intake** to add entries.")
    else:
        total_apps = len(df_filtered)
        total_fees = df_filtered["Total Fee (MK)"].sum()
        avg_fee = df_filtered["Total Fee (MK)"].mean() if total_apps > 0 else 0

        k1, k2, k3 = st.columns(3, gap="large")
        k1.markdown(f"""
        <div class="kpi-tile">
            <div class="kpi-label">Total Applications</div>
            <div class="kpi-value">{total_apps:,}</div>
            <div class="kpi-sub">In selected view</div>
        </div>""", unsafe_allow_html=True)
        k2.markdown(f"""
        <div class="kpi-tile">
            <div class="kpi-label">Total Fees Collected</div>
            <div class="kpi-value" style="font-size:1.25rem;">MK {total_fees:,.0f}</div>
            <div class="kpi-sub">Cumulative revenue</div>
        </div>""", unsafe_allow_html=True)
        k3.markdown(f"""
        <div class="kpi-tile">
            <div class="kpi-label">Average Fee</div>
            <div class="kpi-value" style="font-size:1.25rem;">MK {avg_fee:,.0f}</div>
            <div class="kpi-sub">Per application</div>
        </div>""", unsafe_allow_html=True)

        st.markdown("<hr class='bcc-divider'>", unsafe_allow_html=True)
        st.markdown("#### Submission Trends")
        time_frame = st.radio("Group by:", ["Weekly", "Monthly", "Quarterly"], horizontal=True, key="trend_group")
        
        df_chart = df_filtered.copy()
        df_chart["Date Received"] = pd.to_datetime(df_chart["Date Received"], errors='coerce')
        df_chart = df_chart.dropna(subset=["Date Received"])

        if not df_chart.empty:
            if time_frame == "Weekly":
                df_chart["Period"] = df_chart["Date Received"].dt.to_period("W").dt.start_time.dt.strftime('%Y-%m-%d')
            elif time_frame == "Monthly":
                df_chart["Period"] = df_chart["Date Received"].dt.to_period("M").dt.start_time.dt.strftime('%b %Y')
            else:
                df_chart["Period"] = df_chart["Date Received"].dt.to_period("Q").astype(str)

            summary = df_chart.groupby(["Period", "Category"]).size().reset_index(name="Submissions Count")
            
            col1, col2 = st.columns([3, 2], gap="large")
            with col1:
                fig_trend = px.bar(
                    summary, x="Period", y="Submissions Count", color="Category",
                    title=f"Submission Volume — {time_frame} View ({view_filter})",
                    barmode="stack", height=580,
                    color_discrete_sequence=px.colors.qualitative.Safe
                )
                fig_trend.update_xaxes(type='category')
                fig_trend.update_layout(
                    autosize=True, plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
                    font=dict(size=14, color="#1A202C"), title_font=dict(size=20, color="#1B2A4A"),
                    legend=dict(orientation="h", yanchor="top", y=1.15, xanchor="center", x=0.5, font=dict(size=13, color="#1A202C")),
                    margin=dict(t=130, b=110, l=50, r=30),
                    xaxis=dict(tickangle=-35, tickfont=dict(size=12, color="#1A202C"), title="Period"),
                    yaxis=dict(tickfont=dict(size=13, color="#1A202C"), title="Number of Submissions", gridcolor="#EEF0F5")
                )
                st.plotly_chart(fig_trend, use_container_width=True, theme=None)
            with col2:
                pie_data = df_chart.groupby("Category").size().reset_index(name="Total Applications")
                pie_data["Label"] = pie_data["Category"].str.replace(r"^\d+\.\s*", "", regex=True)
                fig_share = px.pie(
                    pie_data, names="Label", values="Total Applications",
                    title="Share by Category", hole=0.38, height=580,
                    color_discrete_sequence=px.colors.qualitative.Safe
                )
                fig_share.update_traces(textposition="inside", textinfo="percent+value", textfont_size=14, textfont_color="#1A202C")
                fig_share.update_layout(
                    plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
                    font=dict(size=14, color="#1A202C"), title_font=dict(size=20, color="#1B2A4A"),
                    legend=dict(orientation="h", yanchor="bottom", y=-0.25, font=dict(size=13, color="#1A202C"))
                )
                st.plotly_chart(fig_share, use_container_width=True, theme=None)

            st.markdown("<hr class='bcc-divider'>", unsafe_allow_html=True)
            st.markdown("#### 🧮 Volume Matrix (Category by Period)")
            matrix_df = pd.crosstab(df_chart["Category"], df_chart["Period"])
            matrix_df["Total"] = matrix_df.sum(axis=1)
            matrix_df.loc["Grand Total"] = matrix_df.sum(axis=0)
            
            styled_matrix = matrix_df.style.background_gradient(
                cmap="Blues",
                axis=None,
                subset=(matrix_df.index[:-1], matrix_df.columns[:-1])
            ).format("{:,.0f}")
           
            st.dataframe(styled_matrix, use_container_width=True)

        st.markdown("<hr class='bcc-divider'>", unsafe_allow_html=True)
        st.markdown("#### 📋 Application Registry")
        search_query = st.text_input("Search registry:", placeholder="Filter by Plot #, Applicant name, or File ID…", label_visibility="collapsed")
       
        df_display = df_filtered.copy()
        if search_query.strip():
            q = search_query.strip().lower()
            df_display = df_display[
                df_display["Application ID"].astype(str).str.lower().str.contains(q, na=False) |
                df_display["Applicant Name"].astype(str).str.lower().str.contains(q, na=False) |
                df_display["Plot Number"].astype(str).str.lower().str.contains(q, na=False)
            ]
        df_display_renamed = df_display.sort_values(by="Date Received", ascending=False)
        format_dict = {
            "Est. Cost (MK)": "{:,.2f}",
            "Total Fee (MK)": "{:,.2f}"
        }
        if pd.api.types.is_datetime64_any_dtype(df_display_renamed["Date Received"]):
            format_dict["Date Received"] = lambda x: x.strftime('%Y-%m-%d') if pd.notnull(x) else ""
        styled_df = df_display_renamed.style.set_properties(**{
            'background-color': '#FFFFFF', 'color': '#000000', 'border-color': '#DDE3EE'
        }).format(format_dict)
        st.dataframe(styled_df, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# MODULE 4 — PROCESS TRACKING
# ══════════════════════════════════════════════════════════════════════════════
elif current_page == "tracker":
    st.markdown("## 🛤️ PROCESS TRACKING")
    st.markdown("<hr class='bcc-divider'>", unsafe_allow_html=True)
    st.markdown("Search for an existing application to update its operational phase.")
    
    col_search, col_btn = st.columns([4, 1])
    with col_search:
        search_query = st.text_input("🔍 Enter Application ID or Plot Number to load record:", placeholder="e.g., BCC/TP/2026/250 or Plot BC 24", key="tracker_search")
    with col_btn:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    if st.button("🗑️ Clear Search", use_container_width=True):
        st.session_state.tracker_search = ""
        st.rerun()

    if search_query.strip():
        q = search_query.strip().lower()
        match_idx = df_bcc[
            df_bcc["Application ID"].astype(str).str.lower().eq(q) |
            df_bcc["Plot Number"].astype(str).str.lower().eq(q)
        ].index
        
        if len(match_idx) == 0:
            st.warning("⚠️ No matching record found in the registry. Please check the ID or Plot Number.")
        else:
            record_idx = match_idx[0]
            record = df_bcc.loc[record_idx]
           
            st.success(f"✅ **Record Loaded:** {record['Applicant Name']} | **Plot:** {record['Plot Number']} | **Category:** {record['Category']}")
           
            st.markdown("<br>", unsafe_allow_html=True)
           
            track_type = st.radio("Select Workflow Process for this application:", ["Lease Application", "Change of Ownership", "Plan Approval"], horizontal=True)
           
            if track_type == "Lease Application":
                steps = [
                    "Confirmation of Estate",
                    "Confirmation of Details",
                    "City Rates Clearance",
                    "Lease Application Fee Paid",
                    "Application Form Submitted",
                    "Property Inspection Completed",
                    "Surveying Executed",
                    "Development Charges Cleared",
                    "Legal Costs Cleared",
                    "Final Signing by Director of Town Planning and Estates Services"
                ]
            elif track_type == "Plan Approval":
                steps = [
                    "Submission of Plans",
                    "Payment of Scrutiny Fees",
                    "Technical Screening of Plans",
                    "Town Planning Committee Screening and Approval of Plans",
                    "Preparation of Grants Permissions",
                    "Stamping of the Approved plans",
                    "Signing of the plans and grants permissions by the Director of Town Planning and Estates Services"
                ]
            else:
                steps = [
                    "Obtain Letter (Site Office / Deceased Estate)",
                    "Site Verification",
                    "File Check at Civic Offices",
                    "City Rates Clearance",
                    "Clearance Certificate Fee Paid",
                    "Change of Ownership Fee Paid",
                    "Tax Clearance (MRA) Obtained",
                    "Signing by Director of Town Planning and Estates Services",
                    "Signing by Director of Financial Services",
                    "Initial CEO Signature",
                    "Document Preparation",
                    "Final CEO Signature"
                ]
            
            saved_steps_str = str(record.get("Completed Steps", ""))
            if saved_steps_str in ["nan", "N/A", ""]:
                saved_steps_str = ""
            saved_steps = [s.strip() for s in saved_steps_str.split(",") if s.strip()]
            
            st.markdown(f"### Standard Operating Procedure: {track_type}")
           
            with st.form("tracker_form"):
                checked_states = []
                for i, title in enumerate(steps, 1):
                    is_checked = title in saved_steps
                    checked = st.checkbox(f"Step {i}: {title}", value=is_checked)
                    if checked:
                        checked_states.append(title)
               
                st.markdown("<br>", unsafe_allow_html=True)
                submitted = st.form_submit_button(" 💾 Save Progress to Registry", use_container_width=True)
               
                if submitted:
                    new_steps_str = ",".join(checked_states)
                    df_bcc.at[record_idx, "Completed Steps"] = new_steps_str
                    conn.update(data=df_bcc)
                    st.cache_data.clear()
                    st.success("✅ Progress successfully synced to the database!")
                    st.balloons()

# ── Live Mode ───────────────────────────────────────────────────────────────
if live_mode:
    time.sleep(refresh_rate)
    st.rerun()
