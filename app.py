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
    page_title="BCC Town Planning and Estates Portal",
    page_icon="city.png",
    layout="wide"
)

# ── Global High-Contrast + Fluid Media Query Breakpoints ───────────────────
st.markdown("""
<style>
    /* ── FORCE LIGHT THEME OVERRIDE (Mobile & Desktop) ── */
    .stApp, .main, header[data-testid="stHeader"] { background-color: #F4F6FA !important; }
    div[data-testid="stMarkdownContainer"] p, div[data-testid="stMarkdownContainer"] span,
    .stSlider label, .stNumberInput label, label[data-testid="stWidgetLabel"] p,
    div[data-testid="stRadio"] label div[data-testid="stMarkdownContainer"] p {
        color: #1A202C !important; font-weight: 500 !important;
    }
    h1, h2, h3, h4, h5 { color: #1E65B5 !important; }
    
    :root {
        --navy: #1E65B5; --gold: #C49A2A; --bg: #F4F6FA; 
        --card: #FFFFFF; --body: #3A4557; --border: #DDE3EE; --muted: #6B7A96;
    }

    /* ── SINGLE SIDEBAR HAMBURGER + PRESERVE THEME TOGGLE ── */
    button[data-testid="stSidebarCollapseButton"] {
        width: 52px !important; height: 52px !important; padding: 0 !important;
        background: transparent !important; border: none !important; box-shadow: none !important;
    }
    button[data-testid="stSidebarCollapseButton"] svg { display: none !important; }
    button[data-testid="stSidebarCollapseButton"]::before {
        content: "☰" !important; font-size: 29px !important; font-weight: bold !important;
        color: #E8EDF5 !important; display: flex !important; align-items: center; justify-content: center;
        width: 100%; height: 100%;
    }
    button[data-testid="stSidebarCollapseButton"]:hover::before { color: #C49A2A !important; transform: scale(1.1); }
    header[data-testid="stHeader"] button[title="View documentation"],
    header[data-testid="stHeader"] button[aria-label*="theme"],
    header[data-testid="stHeader"] button[data-testid="stHeaderThemeToggle"] {
        display: inline-flex !important; visibility: visible !important; width: 42px !important; height: 42px !important;
    }
    header[data-testid="stHeader"] button svg:not([data-testid*="theme"]) { display: none !important; }
    header[data-testid="stHeader"] button[aria-label*="theme"] svg,
    header[data-testid="stHeader"] button[data-testid="stHeaderThemeToggle"] svg { fill: #E8EDF5 !important; stroke: #E8EDF5 !important; }

    /* ── INPUTS, BUTTONS & EYE ICON ── */
    div.stButton > button {
        -webkit-appearance: none !important; appearance: none !important; background-color: var(--navy) !important;
        color: #FFFFFF !important; border: none !important; border-radius: 6px !important; padding: 12px 24px !important;
        font-weight: 600 !important; min-height: 48px;
    }
    div.stButton > button * { color: #FFFFFF !important; }
    div.stButton > button:hover { background-color: #243660 !important; }
    [data-testid="stTextInput"] button svg { fill: #1A202C !important; stroke: #1A202C !important; color: #1A202C !important; }
    [data-testid="stTextInput"] div[data-baseweb="input"] > div, [data-testid="stNumberInput"] div[data-baseweb="input"] > div,
    [data-testid="stDateInput"] div[data-baseweb="input"] > div, [data-testid="stSelectbox"] div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important; border: 1px solid #DDE3EE !important; min-height: 44px;
    }
    [data-testid="stTextInput"] input, [data-testid="stNumberInput"] input,
    [data-testid="stDateInput"] input, [data-testid="stSelectbox"] div[data-baseweb="select"] {
        color: #000000 !important; -webkit-text-fill-color: #000000 !important;
    }
    div[data-testid="stCheckbox"] { padding: 6px 0; margin-bottom: 4px; }
    [data-testid="stDataFrame"] > div, [data-testid="stTable"] > div { background-color: #FFFFFF !important; }

    /* ── CUSTOM UI COMPONENTS ── */
    .portal-header { 
        background-color: #1E65B5; border-radius: 8px; border-bottom: 4px solid #C49A2A; 
        padding: 22px 26px; margin-bottom: 24px; width: 100%; box-sizing: border-box; 
    }
    .portal-header * { color: #FFFFFF !important; }
    .portal-title { margin: 0 0 14px 0; font-weight: 700; font-size: 1.35rem; letter-spacing: 0.04em; line-height: 1.3; text-transform: uppercase; }
    .card-title { font-size: 0.8rem; font-weight: 700; letter-spacing: 0.09em; text-transform: uppercase; color: var(--muted); margin-bottom: 16px; padding-bottom: 10px; border-bottom: 1px solid var(--border); }
    .kpi-tile { background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 20px 24px; text-align: center; }
    .kpi-label { font-size: 0.75rem; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; color: var(--muted); margin-bottom: 8px; }
    .kpi-value { font-size: 1.6rem; font-weight: 700; color: var(--navy); line-height: 1.1; word-break: break-all; }
    .kpi-sub { font-size: 0.75rem; color: var(--muted); margin-top: 4px; }
    .fee-result { background: var(--navy); border-radius: 10px; padding: 22px 26px; margin-top: 16px; border-left: 4px solid var(--gold); }
    .fee-result .fee-label { color: #A8B8D0; font-size: 0.78rem; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 6px; }
    .fee-result .fee-amount { color: #FFFFFF; font-size: 1.9rem; font-weight: 700; letter-spacing: -0.02em; word-break: break-all; }
    .fee-result .fee-note { color: var(--gold); font-size: 0.78rem; margin-top: 6px; }
    .bcc-divider { border: none; border-top: 1px solid var(--border); margin: 20px 0; }

    /* ── MOBILE RESPONSIVENESS ── */
    @media (max-width: 768px) {
        .portal-header { padding: 14px 16px; margin-bottom: 16px; }
        .portal-title { font-size: 1.05rem; margin-bottom: 10px; }
        .kpi-tile { padding: 14px 16px; margin-bottom: 10px;}
        .kpi-value { font-size: 1.3rem; }
        .fee-result { padding: 16px 18px; }
        .fee-result .fee-amount { font-size: 1.5rem; }
        div[data-testid="stHorizontalBlock"] { gap: 10px !important; }
    }
</style>
""", unsafe_allow_html=True)

# ── Authentication ─────────────────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    _, login_col, _ = st.columns([1, 2, 1])
    with login_col:
        with st.container(border=True):
            st.markdown("<h3 style='text-align: center; margin-top: 0; margin-bottom: 20px;'>Secure Registry Authentication</h3>", unsafe_allow_html=True)
            with st.form("auth_form"):
                password_input = st.text_input("Internal Access Password", type="password", placeholder="Enter password")
                submit_auth = st.form_submit_button("Verify Credentials", use_container_width=True)
                
                if submit_auth:
                    correct_password = st.secrets.get("auth", {}).get("password")
                    if not correct_password:
                        st.error("❌ Secrets not configured. Contact administrator.")
                    elif password_input == correct_password:
                        st.session_state["authenticated"] = True
                        st.session_state.prev_page = "calculator"
                        st.rerun()
                    else:
                        st.error("❌ Invalid access token. Please verify credentials and re-enter.")
    st.stop()

# ── Portal Header Band ─────────────────────────────────────────────────────
header_html = (
    '<div class="portal-header">'
    '  <p class="portal-title">Department of Town Planning and Estates Services</p>'
    '  <div style="display: flex; flex-wrap: wrap; gap: 10px; align-items: center;">'
    '    <span style="background-color: #C49A2A; color: #1E65B5 !important; font-size: 0.72rem; font-weight: 700;'
    '          letter-spacing: 0.06em; text-transform: uppercase; border-radius: 4px;'
    '          padding: 4px 10px; display: inline-block;">'
    '      Charges Review 2026/2027 &nbsp;·&nbsp; Effective Rates'
    '    </span>'
    '    <span style="color: #FFFFFF !important; font-size: 0.78rem; font-weight: 500;'
    '          font-style: italic; display: inline-block; letter-spacing: 0.02em;">'
    '      Created by GIS Specialist Frank Chingoka'
    '    </span>'
    '  </div>'
    '</div>'
)
st.markdown(header_html, unsafe_allow_html=True)

# ── Master Data Configuration ───────────────────────────────────────────────
BCC_RATES = {
    "Residential": {
        "High Density":                    {"rate": 170000.00, "unit": "sqm"},
        "Medium Density":                  {"rate": 190000.00, "unit": "sqm"},
        "Low Density":                     {"rate": 220000.00, "unit": "sqm"},
        "Multi- Units (Medium and Low)":   {"rate": 350000.00, "unit": "sqm"},
    },
    "Institutional": {
        "Churches, Mosques and Schools":   {"rate": 420000.00, "unit": "sqm"},
    },
    "Industrial Development": {
        "Factory / Warehouses":            {"rate": 525000.00, "unit": "sqm"},
    },
    "Office/Commercial Development": {
        "Single Storey":                   {"rate": 525000.00, "unit": "sqm"},
        "Multi- Storey":                   {"rate": 650000.00, "unit": "sqm"},
    },
    "Fences": {
        "Security Fence":                  {"rate": 205000.00, "unit": "linear_meters"},
    },
    "Septic Tank": {
        "Septic Tank Installation":        {"rate": 40000.00,  "unit": "fixed_fee"},
    },
    "Advertising": {
        "Application Fee":                 {"rate": 15000.00,  "unit": "fixed_fee"},
        "Billboard":                       {"rate": 750000.00, "unit": "fixed_fee"},
        "Single Sided Signpost":           {"rate": 125000.00, "unit": "fixed_fee"},
        "Double Sided Signpost":           {"rate": 190000.00, "unit": "fixed_fee"},
        "Composite Signpost":              {"rate": 500000.00, "unit": "fixed_fee"},
        "Gantry":                          {"rate": 3000000.00,"unit": "fixed_fee"},
        "Cantilevered Billboard":          {"rate": 2000000.00,"unit": "fixed_fee"},
    },
    "Miscellaneous": {
        "One surface car parking space":                         {"rate": 280000.00, "unit": "fixed_fee"},
        "Application in Principle (Outline Application)":        {"rate": 750000.00, "unit": "fixed_fee"},
        "Change of Use":                                         {"rate": 750000.00, "unit": "fixed_fee"},
        "Subdivision per plot created":                          {"rate": 150000.00, "unit": "fixed_fee"},
        "Plot Regularisation":                                   {"rate": 500000.00, "unit": "fixed_fee"},
        "Infill Plot Creation":                                  {"rate": 500000.00, "unit": "fixed_fee"},
        "Sewer Application Fees":                                {"rate": 100000.00, "unit": "fixed_fee"},
        "Certificate of Occupancy":                              {"rate": 0.001,     "unit": "percentage_of_final_cost"},
        "LPG Exchange Cage":                                     {"rate": 150000.00, "unit": "fixed_fee"},
        "LPG Exchange & Filler Cage":                            {"rate": 200000.00, "unit": "fixed_fee"},
        "Site Plan Certification":                               {"rate": 15000.00,  "unit": "fixed_fee"},
        "Kiosks for Mobile Money":                               {"rate": 190000.00, "unit": "fixed_fee"},
    },
}

ESTATES_FEES = {
    "Application Forms": {
        "Residential Plot (THA)":   {"rate": 30000.00,  "unit": "fixed_fee"},
        "Residential Plot (PHA)":   {"rate": 60000.00,  "unit": "fixed_fee"},
        "Commercial Plot":          {"rate": 150000.00, "unit": "fixed_fee"},
        "Land Lease Plot (THA)":    {"rate": 100000.00, "unit": "fixed_fee"},
        "Land Lease Plot (PHA)":    {"rate": 150000.00, "unit": "fixed_fee"},
    },
    "Legal Services Fees": {
        "Consent Application Fee":  {"rate": 80000.00,  "unit": "fixed_fee"},
        "Legal Fee":                {"rate": 150000.00, "unit": "fixed_fee"},
    },
    "Processing & Allocation Fees": {
        "Residential Plot":                         {"rate": 200000.00, "unit": "fixed_fee"},
        "Church Plot":                              {"rate": 250000.00, "unit": "fixed_fee"},
        "School Plot":                              {"rate": 500000.00, "unit": "fixed_fee"},
        "Commercial Plot (per 0.0036 ha)":          {"rate": 550000.00, "unit": "qty_based"},
        "Industrial Plot (per 0.0036 ha)":          {"rate": 550000.00, "unit": "qty_based"},
    },
    "Ground Rents": {
        "THA":                      {"rate": 35000.00,  "unit": "fixed_fee"},
        "High Density":             {"rate": 60000.00,  "unit": "fixed_fee"},
        "Medium Density":           {"rate": 80000.00,  "unit": "fixed_fee"},
        "Commercial BY MKT Value":  {"rate": 0.075,     "unit": "market_value"},
    },
    "Legalisation": {
        "Legalisation (THA)":       {"rate": 2000000.00,"unit": "fixed_fee"},
    },
    "Change of Ownership": {
        "Next of Kin":              {"rate": 120000.00, "unit": "fixed_fee"},
        "Private Sale (THA)":       {"rate": 200000.00, "unit": "fixed_fee"},
        "Private Sale (PHA)":       {"rate": 350000.00, "unit": "fixed_fee"},
    },
    "Development Charges": {
        "THAs per 0.036 ha":        {"rate": 2000000.00,"unit": "qty_based"},
    },
    "Beacon Replacement & Survey": {
        "First Beacon":                                      {"rate": 80000.00,  "unit": "fixed_fee"},
        "Extra beacon":                                      {"rate": 40000.00,  "unit": "qty_based"},
        "Survey of Plot":                                    {"rate": 200000.00, "unit": "fixed_fee"},
        "Survey drawing & computation fees (0.036ha)":       {"rate": 150000.00, "unit": "qty_based"},
    },
}

RATE_04_CATS = {"Residential", "Institutional", "Industrial Development", "Office/Commercial Development", "Fences"}
COLUMNS = [
    "Application ID", "Date Received", "Applicant Name", "Plot Number", "Department",
    "Category", "Development Type", "Dimension/Qty", "Est. Cost (MK)", "Total Fee (MK)", "Completed Steps"
]

def _calc_raw_base_fee(dept: str, category: str, rate_info: dict, qty: float, premium: float = 0.0) -> Tuple[float, float]:
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

def _fmt_date_col(series: pd.Series) -> pd.Series:
    def safe_format(x):
        if pd.isna(x) or x == "" or str(x).strip() == "":
            return ""
        try:
            dt = pd.to_datetime(x, dayfirst=True, errors='coerce')
            if pd.notnull(dt):
                return dt.strftime("%d/%m/%Y")
        except:
            pass
        return str(x).strip()
    return series.apply(safe_format)

# ── Cloud Data Synchronizer ───────────────────────────────────────────────
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=5)
def load_data() -> pd.DataFrame:
    try:
        df = conn.read(ttl=0)
        if df is None or df.empty:
            return pd.DataFrame(columns=COLUMNS)
        for col in COLUMNS:
            if col not in df.columns:
                df[col] = "N/A"
        df["Department"] = df["Department"].replace({"N/A": "Town Planning (Scrutiny)"})
        if "Category" in df.columns:
            df["Category"] = df["Category"].astype(str).str.title()
        df["Date Received"] = pd.to_datetime(df["Date Received"], format="%d/%m/%Y", errors="coerce")
        for num_col in ["Total Fee (MK)", "Est. Cost (MK)", "Dimension/Qty"]:
            if num_col in df.columns:
                df[num_col] = pd.to_numeric(df[num_col], errors="coerce").fillna(0.0)
        return df
    except Exception as e:
        st.error(f"Failed to fetch data from registry: {e}")
        return pd.DataFrame(columns=COLUMNS)

# ── Initialization and Navigation ─────────────────────────────────────────
df_bcc = load_data()

st.sidebar.markdown("### 🏛 BCC PORTAL")
st.sidebar.markdown("---")
PAGE_MAP = {
    "🧮 Fee Calculator":        "calculator",
    "📥 New Application Intake": "intake",
    "📊 Submission Analytics":   "analytics",
    "🛤️ Process Tracking":       "tracker",
}
selected_label = st.sidebar.radio("Navigate to:", list(PAGE_MAP.keys()), key="sidebar_nav")
current_page = PAGE_MAP[selected_label]

if st.session_state.get("prev_page") != current_page:
    st.session_state.prev_page = current_page
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ DASHBOARD CONTROLS")
live_mode = st.sidebar.toggle("🔄 Enable Real-Time Live View", value=False)
if live_mode:
    refresh_rate = st.sidebar.slider("Refresh Interval (seconds)", 5, 60, 10)

st.sidebar.markdown("---")
if st.sidebar.button("🔃 Refresh Data Now", use_container_width=True):
    st.cache_data.clear()
    st.rerun()
st.sidebar.caption("Blantyre City Council · Town Planning & Estates")

# ==============================================================================
# MODULE 1: FEE CALCULATOR
# ==============================================================================
def render_calculator():
    st.markdown("## 🧮 FEE CALCULATOR")
    st.markdown("<hr class='bcc-divider'>", unsafe_allow_html=True)
    
    dept_choice = st.radio("Select Department Parameter", ["Town Planning (Scrutiny)", "Estates Services"], horizontal=True, key="calc_dept")
    target_dict = BCC_RATES if dept_choice == "Town Planning (Scrutiny)" else ESTATES_FEES
    col1, col2 = st.columns([1, 1], gap="medium")
    
    with col1:
        with st.container(border=True):
            st.markdown('<div class="card-title">Development / Service Parameters</div>', unsafe_allow_html=True)
            category    = st.selectbox("Plan Category", list(target_dict.keys()), key="calc_cat")
            subcategory = st.selectbox("Service / Development Type", list(target_dict[category].keys()), key="calc_sub")
            
            item_details = target_dict[category][subcategory]
            base_rate    = item_details["rate"]
            unit_type    = item_details["unit"]
            is_04        = (category in RATE_04_CATS) and (dept_choice == "Town Planning (Scrutiny)")
            premium_val  = 0.0
            
            if unit_type == "sqm":
                st.markdown("<hr class='bcc-divider'>", unsafe_allow_html=True)
                st.markdown('<div class="card-title">📐 Area Determination Method</div>', unsafe_allow_html=True)
                input_method = st.radio("Entry format:", ["Enter Total Area Manually", "Calculate Using Geometric Shapes"], horizontal=True, key="calc_method")
                if input_method == "Enter Total Area Manually":
                    input_val = st.number_input("Total Built-up Area (Square Meters)", min_value=0.0, value=100.0, step=10.0, key="calc_man_sqm")
                else:
                    shape = st.selectbox("Select Shape Profile:", ["Rectangle", "Triangle", "Trapezium", "Circle", "Semicircle"], key="calc_shape")
                    if shape == "Rectangle":
                        input_val = st.number_input("Length (m)", value=20.0) * st.number_input("Width (m)", value=15.0)
                    elif shape == "Triangle":
                        input_val = 0.5 * st.number_input("Base Length (m)", value=15.0) * st.number_input("Perpendicular Height (m)", value=10.0)
                    elif shape == "Trapezium":
                        input_val = 0.5 * (st.number_input("Parallel Side A (m)", value=12.0) + st.number_input("Parallel Side B (m)", value=18.0)) * st.number_input("Distance / Height (m)", value=8.0)
                    elif shape == "Circle":
                        input_val = math.pi * st.number_input("Radius (m)", value=7.0) ** 2
                    elif shape == "Semicircle":
                        input_val = 0.5 * math.pi * st.number_input("Radius (m)", value=7.0) ** 2
                st.metric(label="Calculated Spatial Footprint", value=f"{input_val:,.2f} sqm")
            elif unit_type == "linear_meters":
                input_val = st.number_input("Total Fence Length (Meters)", min_value=0.0, value=50.0, step=5.0, key="calc_lin_mtrs")
            elif unit_type == "percentage_of_final_cost":
                input_val = st.number_input("Declared Final Structural Cost (MK)", min_value=0.0, value=5000000.0, step=100000.0, key="calc_pct_cost")
            elif unit_type == "market_value":
                premium_val = st.number_input("Premium Value (MK)", value=1000000.0, step=50000.0, key="calc_mkt_prem")
                input_val   = st.number_input("Plot Area (Square Meters)", value=1000.0, step=10.0, key="calc_mkt_area")
            elif unit_type == "qty_based":
                input_val = st.number_input("Quantity", min_value=1.0, value=1.0, step=1.0, key="calc_qty")
            else:
                input_val = st.number_input("Quantity / Units", min_value=1.0, value=1.0, step=1.0, key="calc_fallback_qty")
            
            addon_accumulated = 0.0
            if dept_choice == "Town Planning (Scrutiny)":
                with st.container(border=True):
                    st.markdown('<div class="card-title">📦 Combine Additional Fees (Optional)</div>', unsafe_allow_html=True)
                    show_app_checkbox = not (category == "Advertising" and subcategory == "Application Fee")
                    if st.checkbox("Include Base App Fee (MK 15,000)", value=show_app_checkbox, disabled=not show_app_checkbox):
                        addon_accumulated += BCC_RATES["Advertising"]["Application Fee"]["rate"]
                    if st.checkbox("Include Septic Tank Fee (MK 40,000)"): addon_accumulated += BCC_RATES["Septic Tank"]["Septic Tank Installation"]["rate"]
                    if st.checkbox("Include Site Plan Cert. (MK 15,000)"): addon_accumulated += BCC_RATES["Miscellaneous"]["Site Plan Certification"]["rate"]
                    if st.checkbox("Include Surface Car Parking (MK 280,000)"): addon_accumulated += BCC_RATES["Miscellaneous"]["One surface car parking space"]["rate"]
                    if st.checkbox("Include Sewer Application Fee (MK 100,000)"): addon_accumulated += BCC_RATES["Miscellaneous"]["Sewer Application Fees"]["rate"]
            
            estimated_cost, base_fee = _calc_raw_base_fee(dept_choice, category, item_details, input_val, premium_val)
            total_fee_due = base_fee + addon_accumulated
            base_fee_label = "Scrutiny Fee" if dept_choice == "Town Planning (Scrutiny)" else "Service Fee"

    with col2:
        with st.container(border=True):
            st.markdown('<div class="card-title">Assessment Breakdown</div>', unsafe_allow_html=True)
            st.markdown(f"""
                <div style="background:#F4F6FA;border-radius:8px;padding:14px 18px;margin-bottom:16px;border:1px solid #DDE3EE;">
                    <div style="font-size:0.75rem;color:#6B7A96;font-weight:600;text-transform:uppercase;letter-spacing:0.07em;">Category</div>
                    <div style="font-size:0.95rem;color:#1B2A4A;font-weight:600;">{category}</div>
                    <div style="font-size:0.75rem;color:#6B7A96;font-weight:600;text-transform:uppercase;letter-spacing:0.07em;margin-top:10px;">Development Type</div>
                    <div style="font-size:0.95rem;color:#1B2A4A;font-weight:600;">{subcategory}</div>
                </div>
            """, unsafe_allow_html=True)
            
            if is_04 or unit_type == "market_value":
                label_text = "Estimated Development Cost" if is_04 else "Calculated Base Valuation"
                st.markdown(f"""
                    <div style="display:flex;gap:12px;margin-bottom:12px;">
                        <div style="flex:1;background:#F4F6FA;border-radius:8px;padding:14px;border:1px solid #DDE3EE;text-align:center;">
                            <div style="font-size:0.72rem;color:#6B7A96;font-weight:600;text-transform:uppercase;">Base Rate/Multiplier</div>
                            <div style="font-size:1.1rem;font-weight:700;color:#1B2A4A;">{base_rate:,.3f}</div>
                        </div>
                        <div style="flex:1;background:#F4F6FA;border-radius:8px;padding:14px;border:1px solid #DDE3EE;text-align:center;">
                            <div style="font-size:0.72rem;color:#6B7A96;font-weight:600;text-transform:uppercase;">Metric / Qty</div>
                            <div style="font-size:1.1rem;font-weight:700;color:#1B2A4A;">{input_val:,.2f}</div>
                        </div>
                    </div>
                    <div style="background:#F4F6FA;border-radius:8px;padding:14px 18px;margin-bottom:12px;border:1px solid #DDE3EE;">
                        <div style="font-size:0.72rem;color:#6B7A96;font-weight:600;text-transform:uppercase;">{label_text}</div>
                        <div style="font-size:1.35rem;font-weight:700;color:#1B2A4A;">MK {estimated_cost:,.2f}</div>
                    </div>
                """, unsafe_allow_html=True)
                
            if addon_accumulated > 0:
                st.markdown(f"""
                    <div style="background:#F4F6FA;border-radius:8px;padding:14px 18px;margin-bottom:12px;border:1px solid #DDE3EE;display:flex;justify-content:space-between;">
                        <div><div style="font-size:0.72rem;color:#6B7A96;font-weight:600;text-transform:uppercase;">{base_fee_label}</div>
                        <div style="font-size:1.05rem;font-weight:700;color:#1B2A4A;">MK {base_fee:,.2f}</div></div>
                        <div style="text-align:right;"><div style="font-size:0.72rem;color:#6B7A96;font-weight:600;text-transform:uppercase;">Add-ons</div>
                        <div style="font-size:1.05rem;font-weight:700;color:#2463EB;">+ MK {addon_accumulated:,.2f}</div></div>
                    </div>
                """, unsafe_allow_html=True)
                
            st.markdown(f"""
                <div class="fee-result">
                    <div class="fee-label">{"Total Fee Payable" if addon_accumulated > 0 else f"Total {dept_choice.split()[0]} Fee Payable"}</div>
                    <div class="fee-amount">MK {total_fee_due:,.2f}</div>
                    <div class="fee-note">{'MK {:,.2f} + Additions MK {:,.2f}'.format(base_fee, addon_accumulated) if addon_accumulated > 0 else f"Calculations for {dept_choice}"}</div>
                </div>
            """, unsafe_allow_html=True)

# ==============================================================================
# MODULE 2: NEW APPLICATION INTAKE
# ==============================================================================
def render_intake(df):
    st.markdown("## 📥 NEW APPLICATION INTAKE")
    st.markdown("<hr class='bcc-divider'>", unsafe_allow_html=True)
    
    def clear_intake_data():
        for key in ["intake_app_id", "intake_applicant", "intake_plot", "intake_fee"]:
            if key in st.session_state:
                st.session_state[key] = "" if "fee" not in key else 0.0

    if st.session_state.get("intake_success_msg"):
        st.success(st.session_state.pop("intake_success_msg"))
        st.balloons()
        
    intake_dept = st.radio("Select Department", ["Town Planning (Scrutiny)", "Estates Services"], horizontal=True, key="intake_dept")
    target_dict = BCC_RATES if intake_dept == "Town Planning (Scrutiny)" else ESTATES_FEES
    
    col1, col2 = st.columns(2, gap="medium")
    with col1:
        app_id = st.text_input("Application / File ID", placeholder="e.g., BCC/TP/2026/250", key="intake_app_id")
        applicant_name = st.text_input("Applicant Name / Developer Entity", key="intake_applicant")
        date_rcvd = st.date_input("Date Received", value=datetime.today(), key="intake_date")
    with col2:
        plot_number = st.text_input("Plot Number / Parcel ID", key="intake_plot")
        intake_category = st.selectbox("Category", list(target_dict.keys()), key="intake_cat")
        intake_subcategory = st.selectbox("Development Type", list(target_dict[intake_category].keys()), key="intake_sub")
        
    st.markdown("<hr class='bcc-divider'>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown('<div class="card-title">Financial Metrics Input</div>', unsafe_allow_html=True)
        rate_info = target_dict[intake_category][intake_subcategory]
        input_fee_paid = st.number_input("Total Amount Received on Receipt (MK)", min_value=0.0, step=5000.0, key="intake_fee")
        
        is_tp = (intake_dept == "Town Planning (Scrutiny)")
        st.markdown("<div style='font-size:0.80rem;color:#6B7A96;font-weight:700;text-transform:uppercase;'>Check items included in this receipt total:</div>", unsafe_allow_html=True)
        
        bundle_col1, bundle_col2, bundle_col3 = st.columns([1, 1, 1])
        with bundle_col1:
            inc_app = st.checkbox("Base App Fee (MK 15,000)", value=True, disabled=not is_tp, key="inc_app")
            inc_site = st.checkbox("Site Plan Cert. (MK 15,000)", disabled=not is_tp, key="inc_site")
        with bundle_col2:
            inc_septic = st.checkbox("Septic Tank (MK 40,000)", disabled=not is_tp, key="inc_septic")
            inc_sewer = st.checkbox("Sewer App Fee (MK 100,000)", disabled=not is_tp, key="inc_sewer")
        with bundle_col3:
            inc_parking = st.checkbox("Car Parking (MK 280,000)", disabled=not is_tp, key="inc_parking")
            
        deductions = 0.0
        if is_tp:
            if inc_app: deductions += BCC_RATES["Advertising"]["Application Fee"]["rate"]
            if inc_septic: deductions += BCC_RATES["Septic Tank"]["Septic Tank Installation"]["rate"]
            if inc_site: deductions += BCC_RATES["Miscellaneous"]["Site Plan Certification"]["rate"]
            if inc_parking: deductions += BCC_RATES["Miscellaneous"]["One surface car parking space"]["rate"]
            if inc_sewer: deductions += BCC_RATES["Miscellaneous"]["Sewer Application Fees"]["rate"]
            
        net_fee = max(0.0, input_fee_paid - deductions) if is_tp else input_fee_paid
        if is_tp and deductions > 0:
            st.caption(f"Net Scrutiny Fee (total − deductions): **MK {net_fee:,.2f}**")
            
        st.markdown("<br>", unsafe_allow_html=True)
        btn_col1, btn_col2 = st.columns(2)
        submit_btn = btn_col1.button("📄 Append Entry to Registry", use_container_width=True)
        btn_col2.button("🧹 Clear Data", use_container_width=True, on_click=clear_intake_data)
            
        if submit_btn:
            errors = [e for e, v in [("Application ID is required.", app_id), ("Applicant Name required.", applicant_name), ("Plot Number required.", plot_number)] if not v.strip()]
            if errors:
                for e in errors: st.error(f"❌ {e}")
            else:
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
                    "Date Received": date_rcvd.strftime("%d/%m/%Y"),
                    "Applicant Name": applicant_name.strip(),
                    "Plot Number": plot_number.strip(),
                    "Department": intake_dept,
                    "Category": intake_category,
                    "Development Type": intake_subcategory,
                    "Dimension/Qty": round(derived_dimension, 2),
                    "Est. Cost (MK)": round(calc_est_cost, 2),
                    "Total Fee (MK)": input_fee_paid,
                    "Completed Steps": "",
                }
                try:
                    df_updated = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    df_updated["Date Received"] = _fmt_date_col(df_updated["Date Received"])
                    conn.update(data=df_updated)
                    st.session_state["intake_success_msg"] = f"✅ Record for **{applicant_name.strip()}** appended securely."
                    clear_intake_data()
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Registry write failed: {e}")

# ==============================================================================
# MODULE 3: SUBMISSION ANALYTICS
# ==============================================================================
def render_analytics(df):
    st.markdown("## 📊 SUBMISSION ANALYTICS")
    st.markdown("<hr class='bcc-divider'>", unsafe_allow_html=True)
    
    view_filter = st.radio("View Data For:", ["All Departments", "Town Planning (Scrutiny)", "Estates Services"], horizontal=True)
    df_filtered = df.copy()
    if view_filter != "All Departments":
        df_filtered = df_filtered[df_filtered["Department"] == view_filter]
        
    if df_filtered.empty:
        st.info("📭 No applications on record for this selection.")
        return

    k1, k2, k3 = st.columns(3, gap="medium")
    k1.markdown(f'<div class="kpi-tile"><div class="kpi-label">Total Applications</div><div class="kpi-value">{len(df_filtered):,}</div><div class="kpi-sub">In selected view</div></div>', unsafe_allow_html=True)
    k2.markdown(f'<div class="kpi-tile"><div class="kpi-label">Total Fees Collected</div><div class="kpi-value" style="font-size:1.2rem;">MK {df_filtered["Total Fee (MK)"].sum():,.0f}</div><div class="kpi-sub">Cumulative revenue</div></div>', unsafe_allow_html=True)
    k3.markdown(f'<div class="kpi-tile"><div class="kpi-label">Average Fee</div><div class="kpi-value" style="font-size:1.2rem;">MK {df_filtered["Total Fee (MK)"].mean():,.0f}</div><div class="kpi-sub">Per application</div></div>', unsafe_allow_html=True)
    
    st.markdown("<hr class='bcc-divider'>", unsafe_allow_html=True)
    st.markdown("#### Submission Trends")
    time_frame = st.radio("Group by:", ["Weekly", "Monthly", "Quarterly"], horizontal=True, key="trend_group")
    
    df_chart = df_filtered.copy()
    df_chart["Date Received"] = pd.to_datetime(df_chart["Date Received"], errors="coerce")
    df_chart = df_chart.dropna(subset=["Date Received"])
    
    if not df_chart.empty:
        if time_frame == "Weekly": period_format, pd_freq = "%d-%m-%Y", "W"
        elif time_frame == "Monthly": period_format, pd_freq = "%b %Y", "M"
        else: period_format, pd_freq = "Q", "Q"
        
        df_chart["Period_Sort"] = df_chart["Date Received"].dt.to_period(pd_freq).dt.start_time
        df_chart["Period"] = df_chart["Date Received"].dt.to_period(pd_freq).astype(str) if pd_freq == "Q" else df_chart["Period_Sort"].dt.strftime(period_format)
        df_chart = df_chart.sort_values("Period_Sort")
        summary = df_chart.groupby(["Period", "Category"], sort=False).size().reset_index(name="Submissions Count")
        
        col1, col2 = st.columns([1, 1], gap="medium")
        with col1:
            fig_trend = px.bar(summary, x="Period", y="Submissions Count", color="Category", title=f"Volume — {time_frame} View", barmode="stack", height=400)
            fig_trend.update_xaxes(type="category", tickangle=-35)
            fig_trend.update_layout(plot_bgcolor="white", paper_bgcolor="white", font_color="#1A202C")
            st.plotly_chart(fig_trend, use_container_width=True)
        with col2:
            pie_data = df_chart.groupby("Category").size().reset_index(name="Total Applications")
            pie_data["Label"] = pie_data["Category"].str.replace(r"^\d+\.\s*", "", regex=True)
            fig_share = px.pie(pie_data, names="Label", values="Total Applications", title="Share by Category", hole=0.35, height=400)
            fig_share.update_layout(plot_bgcolor="white", paper_bgcolor="white", font_color="#1A202C")
            st.plotly_chart(fig_share, use_container_width=True)

    st.markdown("<hr class='bcc-divider'>", unsafe_allow_html=True)
    st.markdown("#### 📋 Application Registry")
    search_query = st.text_input("Search registry:", placeholder="Filter by Plot #, Applicant name, or File ID…", label_visibility="collapsed")
    
    df_display = df_filtered.copy()
    if search_query.strip():
        q = search_query.strip().lower()
        mask = df_display.apply(lambda row: row.astype(str).str.lower().str.contains(q).any(), axis=1)
        df_display = df_display[mask]
        
    df_display_sorted = df_display.sort_values(by="Date Received", ascending=False)
    
    # Leverages Streamlit's native formatting over Pandas .style for faster interactions
    st.dataframe(
        df_display_sorted, 
        use_container_width=True,
        hide_index=True,
        column_config={
            "Est. Cost (MK)": st.column_config.NumberColumn(format="MK %.2f"),
            "Total Fee (MK)": st.column_config.NumberColumn(format="MK %.2f"),
            "Date Received": st.column_config.DateColumn(format="YYYY-MM-DD")
        }
    )

# ==============================================================================
# MODULE 4: PROCESS TRACKING
# ==============================================================================
def render_tracker(df):
    st.markdown("## 🛤️ PROCESS TRACKING")
    st.markdown("<hr class='bcc-divider'>", unsafe_allow_html=True)
    
    search_query = st.text_input("🔍 Enter Application ID or Plot Number to load record:", placeholder="e.g., BCC/TP/2026/250")
    if search_query.strip():
        q = search_query.strip().lower()
        match_idx = df[df["Application ID"].astype(str).str.lower().eq(q) | df["Plot Number"].astype(str).str.lower().eq(q)].index
        
        if len(match_idx) == 0:
            st.warning("⚠️ No matching record found in the registry.")
            return
            
        record_idx = match_idx[0]
        record = df.loc[record_idx]
        st.success(f"✅ **Record Loaded:** {record['Applicant Name']} | **Plot:** {record['Plot Number']}")
        
        track_type = st.radio("Select Workflow Process:", ["Lease Application", "Change of Ownership", "Plan Approval"], horizontal=True)
        
        if track_type == "Lease Application":
            steps = ["Confirmation of Estate", "Confirmation of Details", "City Rates Clearance", "Lease Application Fee Paid", "Application Form Submitted", "Property Inspection Completed", "Surveying Executed", "Development Charges Cleared", "Legal Costs Cleared", "Final Signing by Director of Town Planning and Estates Services"]
        elif track_type == "Plan Approval":
            steps = ["Submission of Plans", "Payment of Scrutiny Fees", "Technical Screening of Plans", "Town Planning Committee Screening and Approval of Plans", "Preparation of Grants Permissions", "Stamping of the Approved plans", "Signing of the plans and grants permissions by the Director of Town Planning and Estates Services"]
        else:
            steps = ["Obtain Letter (Site Office / Deceased Estate)", "Site Verification", "File Check at Civic Offices", "City Rates Clearance", "Clearance Certificate Fee Paid", "Change of Ownership Fee Paid", "Tax Clearance (MRA) Obtained", "Signing by Director of Town Planning and Estates Services", "Signing by Director of Financial Services", "Initial CEO Signature", "Document Preparation", "Final CEO Signature"]
            
        saved_steps_str = str(record.get("Completed Steps", ""))
        saved_steps = saved_steps_str.split(",") if saved_steps_str and saved_steps_str not in ("nan", "N/A") else []
        
        st.markdown(f"### Standard Operating Procedure: {track_type}")
        with st.form("tracker_form"):
            checked_states = [title for i, title in enumerate(steps, 1) if st.checkbox(f"Step {i}: {title}", value=(title in saved_steps))]
            if st.form_submit_button("💾 Save Progress to Registry", use_container_width=True):
                new_steps_str = ",".join(checked_states)
                try:
                    df_fresh = conn.read(ttl=0)
                    fresh_match_idx = df_fresh[df_fresh["Application ID"].astype(str).str.upper() == str(record["Application ID"]).upper()].index
                    if len(fresh_match_idx) > 0:
                        df_fresh.at[fresh_match_idx[0], "Completed Steps"] = new_steps_str
                        df_fresh["Date Received"] = _fmt_date_col(df_fresh["Date Received"])
                        conn.update(data=df_fresh)
                        st.cache_data.clear()
                        st.success("✅ Progress successfully synced to the database!")
                        st.balloons()
                        time.sleep(1.5)
                        st.rerun()
                    else:
                        st.error("❌ Sync Error: Record lost. It may have been deleted. Please refresh.")
                except Exception as e:
                    st.error(f"❌ Sync Error: Could not write to database. ({e})")

# ── Controller ────────────────────────────────────────────────────────────
if current_page == "calculator": render_calculator()
elif current_page == "intake": render_intake(df_bcc)
elif current_page == "analytics": render_analytics(df_bcc)
elif current_page == "tracker": render_tracker(df_bcc)

if live_mode and current_page == "analytics":
    time.sleep(refresh_rate)
    st.rerun()
    st.rerun()
