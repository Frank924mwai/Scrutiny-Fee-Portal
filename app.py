import streamlit as st
import pandas as pd
import math
import plotly.express as px
from datetime import datetime
import time
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
    '  <p style="margin: 0 0 14px 0; color: #FFFFFF !important; font-weight: 700; font-size: 1.25rem; letter-spacing: 0.04em; line-height: 1.3; text-transform: uppercase;">'
    '    Department of Town Planning and Estates Services'
    '  </p>'
    '  <div style="display: flex; flex-wrap: wrap; gap: 12px; align-items: center;">'
    '    <span style="background-color: #C49A2A; color: #1E65B5; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; border-radius: 4px; padding: 5px 12px; display: inline-block;">'
    '      Registry & Services Portal &nbsp;·&nbsp; Effective Rates'
    '    </span>'
    '    <span style="color: #FFFFFF !important; font-size: 0.8rem; font-weight: 500; font-style: italic; display: inline-block; letter-spacing: 0.02em;">'
    '      Created by GIS Specialist Frank Chingoka'
    '    </span>'
    '  </div >'
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
                    st.error(" ❌  Secrets not configured. Contact administrator.")
                    correct_password = None
                
                if correct_password and password_input == correct_password:
                    st.session_state["authenticated"] = True
                    st.session_state.prev_page = "calculator"
                    st.rerun()
                else:
                    st.error(" ❌  Invalid access token. Please verify credentials and re-enter.")
    st.stop()

# ── Master Data Dictionaries ────────────────────────────────────────────────
BCC_RATES = {
    "Residential": {
        "High Density": {"rate": 170_000.00, "unit": "sqm"},
        "Medium Density": {"rate": 190_000.00, "unit": "sqm"},
        "Low Density": {"rate": 220_000.00, "unit": "sqm"},
        "Multi- Units (Medium and Low)": {"rate": 350_000.00, "unit": "sqm"},
    },
    "Institutional": {
        "Churches, Mosques and Schools": {"rate": 420_000.00, "unit": "sqm"},
    },
    "Industrial Development": {
        "Factory / Warehouses": {"rate": 525_000.00, "unit": "sqm"},
    },
    "Office/Commercial Development": {
        "Single Storey": {"rate": 525_000.00, "unit": "sqm"},
        "Multi- Storey": {"rate": 650_000.00, "unit": "sqm"},
    },
    "Fences": {
        "Security Fence": {"rate": 205_000.00, "unit": "linear_meters"},
    },
    "Septic Tank": {
        "Septic Tank Installation": {"rate": 40_000.00, "unit": "fixed_fee"},
    },
    "Advertising": {
        "Application Fee": {"rate": 15_000.00, "unit": "fixed_fee"},
        "Billboard": {"rate": 750_000.00, "unit": "fixed_fee"},
        "Single Sided Signpost": {"rate": 125_000.00, "unit": "fixed_fee"},
        "Double Sided Signpost": {"rate": 190_000.00, "unit": "fixed_fee"},
        "Composite Signpost": {"rate": 500_000.00, "unit": "fixed_fee"},
        "Gantry": {"rate": 3_000_000.00, "unit": "fixed_fee"},
        "Cantilevered Billboard": {"rate": 2_000_000.00, "unit": "fixed_fee"},
    },
    "Miscellaneous": {
        "One surface car parking space": {"rate": 280_000.00, "unit": "fixed_fee"},
        "Application in Principle (Outline Application)": {"rate": 750_000.00, "unit": "fixed_fee"},
        "Change of Use": {"rate": 750_000.00, "unit": "fixed_fee"},
        "Subdivision per plot created": {"rate": 150_000.00, "unit": "fixed_fee"},
        "Plot Regularisation": {"rate": 500_000.00, "unit": "fixed_fee"},
        "Infill Plot Creation": {"rate": 500_000.00, "unit": "fixed_fee"},
        "Sewer Application Fees": {"rate": 100_000.00, "unit": "fixed_fee"},
        "Certificate of Occupancy": {"rate": 0.001, "unit": "percentage_of_final_cost"},
        "LPG Exchange Cage": {"rate": 150_000.00, "unit": "fixed_fee"},
        "LPG Exchange & Filler Cage": {"rate": 200_000.00, "unit": "fixed_fee"},
        "Site Plan Certification": {"rate": 15_000.00, "unit": "fixed_fee"},
        "Kiosks for Mobile Money": {"rate": 190_000.00, "unit": "fixed_fee"},
    },
}

ESTATES_FEES = {
    "Application Forms": {
        "Residential Plot (THA)": {"rate": 30_000.00, "unit": "fixed_fee"},
        "Residential Plot (PHA)": {"rate": 60_000.00, "unit": "fixed_fee"},
        "Commercial Plot": {"rate": 150_000.00, "unit": "fixed_fee"},
        "Land Lease Plot (THA)": {"rate": 100_000.00, "unit": "fixed_fee"},
        "Land Lease Plot (PHA)": {"rate": 150_000.00, "unit": "fixed_fee"},
    },
    "Legal Services Fees": {
        "Consent Application Fee": {"rate": 80_000.00, "unit": "fixed_fee"},
        "Legal Fee": {"rate": 150_000.00, "unit": "fixed_fee"},
    },
    "Processing & Allocation Fees": {
        "Residential Plot": {"rate": 200_000.00, "unit": "fixed_fee"},
        "Church Plot": {"rate": 250_000.00, "unit": "fixed_fee"},
        "School Plot": {"rate": 500_000.00, "unit": "fixed_fee"},
        "Commercial Plot (per 0.0036 ha)": {"rate": 550_000.00, "unit": "qty_based"},
        "Industrial Plot (per 0.0036 ha)": {"rate": 550_000.00, "unit": "qty_based"},
    },
    "Ground Rents": {
        "THA": {"rate": 35_000.00, "unit": "fixed_fee"},
        "High Density": {"rate": 60_000.00, "unit": "fixed_fee"},
        "Medium Density": {"rate": 80_000.00, "unit": "fixed_fee"},
        "Commercial BY MKT Value": {"rate": 0.075, "unit": "market_value"},
    },
    "Legalisation": {
        "Legalisation (THA)": {"rate": 2_000_000.00, "unit": "fixed_fee"},
    },
    "Change of Ownership": {
        "Next of Kin": {"rate": 120_000.00, "unit": "fixed_fee"},
        "Private Sale (THA)": {"rate": 200_000.00, "unit": "fixed_fee"},
        "Private Sale (PHA)": {"rate": 350_000.00, "unit": "fixed_fee"},
    },
    "Development Charges": {
        "THAs per 0.036 ha": {"rate": 2_000_000.00, "unit": "qty_based"},
    },
    "Beacon Replacement & Survey": {
        "First Beacon": {"rate": 80_000.00, "unit": "fixed_fee"},
        "Extra beacon": {"rate": 40_000.00, "unit": "qty_based"},
        "Survey of Plot": {"rate": 200_000.00, "unit": "fixed_fee"},
        "Survey drawing & computation fees (0.036ha)": {"rate": 150_000.00, "unit": "qty_based"},
    }
}

RATE_04_CATS = {"Residential", "Institutional", "Industrial Development", "Office/Commercial Development", "Fences"}
COLUMNS = ["Application ID", "Date Received", "Applicant Name", "Plot Number", "Department",
           "Category", "Development Type", "Dimension/Qty", "Est. Cost (MK)", "Total Fee (MK)"]

def _calc_raw_base_fee(dept: str, category: str, rate_info: dict, qty: float, premium: float = 0.0) -> tuple[float, float]:
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
            est_cost = premium * qty  # Premium * Area
            fee = premium * rate_info["rate"] * qty
        elif rate_info["unit"] == "qty_based":
            est_cost = 0.0
            fee = qty * rate_info["rate"]
        else:
            est_cost = 0.0
            fee = rate_info["rate"] * qty  # qty usually 1 for fixed fees
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
        
        # Retroactive patch for older scrutiny records missing Department
        df["Department"] = df["Department"].replace({"N/A": "Town Planning (Scrutiny)"})
        
        if "Category" in df.columns:
            df["Category"] = df["Category"].astype(str).str.title()
            
        df["Date Received"] = pd.to_datetime(df["Date Received"], errors='coerce')
        
        # Ensure 'Total Fee (MK)' replaces legacy 'Scrutiny Fee (MK)'
        if "Scrutiny Fee (MK)" in df.columns and df["Total Fee (MK)"].eq("N/A").all():
            df["Total Fee (MK)"] = df["Scrutiny Fee (MK)"]
            
        return df
    except Exception:
        return pd.DataFrame(columns=COLUMNS)

df_bcc = load_data()

# ── Sidebar ────────────────────────────────────────────────────────────────
st.sidebar.markdown("###  🏛  BCC PORTAL")
st.sidebar.markdown("---")
PAGE_MAP = {
    " 🧮  Fee Calculator": "calculator",
    " 📥  New Application Intake": "intake",
    " 📊  Submission Analytics": "analytics",
    " 🛤️  Process Tracking": "tracker"
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
st.sidebar.markdown("###  ⚙️  DASHBOARD CONTROLS")
live_mode = st.sidebar.toggle(" 🔄  Enable Real-Time Live View", value=False)
if live_mode:
    refresh_rate = st.sidebar.slider("Refresh Interval (seconds)", 5, 60, 10)

st.sidebar.markdown("---")
st.sidebar.caption("Blantyre City Council · Town Planning & Estates")

#  ══════════════════════════════════════════════════════════════════════════════
# MODULE 1 — FEE CALCULATOR (DUAL DEPARTMENT)
#  ══════════════════════════════════════════════════════════════════════════════
if current_page == "calculator":
    st.markdown("##  🧮  FEE CALCULATOR")
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
                st.markdown('<div class="card-title"> 📐  Area Determination Method</div>', unsafe_allow_html=True)
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
                input_val = st.number_input("Declared Final Structural Cost (MK)", min_value=0.0, value=5_000_000.0, step=100_000.0)
            
            elif unit_type == "market_value":
                premium_val = st.number_input("Premium Value (MK)", min_value=0.0, value=1_000_000.0, step=50_000.0)
                input_val = st.number_input("Plot Area (Square Meters)", min_value=0.0, value=1000.0, step=10.0)
                
            elif unit_type == "qty_based":
                input_val = st.number_input("Quantity (e.g. number of 0.036ha portions or beacons)", min_value=1.0, value=1.0, step=1.0)
                
            else:
                input_val = st.number_input("Quantity / Units", min_value=1.0, value=1.0, step=1.0)

        addon_accumulated = 0.0
        # Dynamic Add-on Fees Bundle Engine (Only for Scrutiny as in original)
        if dept_choice == "Town Planning (Scrutiny)":
            with st.container(border=True):
                st.markdown('<div class="card-title"> 📦  Combine Additional Fees (Optional)</div>', unsafe_allow_html=True)
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
                    '    <div style="flex:1;background:#F4F6FA;border-radius:8px;padding:14px;border:1px solid #DDE3EE;text-align:center;">'
                    '        <div style="font-size:0.72rem;color:#6B7A
