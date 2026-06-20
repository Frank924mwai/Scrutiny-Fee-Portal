import streamlit as st
import pandas as pd
import math
import plotly.express as px
from datetime import datetime
import time
from streamlit_gsheets import GSheetsConnection

# ── Page Configuration ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="BCC Town Planning Fees Portal",
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
    /* ─── SPECIFIC INPUT FIXES (Backgrounds White, Text Black) ─── */
   
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
    /* Password Eye Icon Visibility */
    [data-testid="stTextInput"] button svg {
        fill: #000000 !important;
        stroke: #000000 !important;
        color: #000000 !important;
    }
    /* Radio Buttons (Circles White Inside) */
    div[role="radiogroup"] div[data-baseweb="radio"] > div:first-child {
        background-color: #FFFFFF !important;
        border: 2px solid #000000 !important;
    }
    /* Inner dot when radio is checked */
    div[role="radiogroup"] div[data-baseweb="radio"] input:checked + div > div {
        background-color: #1E65B5 !important;
    }
    /* Number Input Up/Down Stepper Buttons */
    [data-testid="stNumberInputStepUp"],
    [data-testid="stNumberInputStepDown"] {
        background-color: #FFFFFF !important;
    }
    [data-testid="stNumberInputStepUp"] svg,
    [data-testid="stNumberInputStepDown"] svg {
        fill: #000000 !important;
    }
    /* Original styling */
    .bcc-header { background: var(--navy); border-radius: 10px; padding: 24px 32px 20px; margin-bottom: 28px; border-bottom: 3px solid var(--gold); }
    .bcc-header h1 { color: #FFFFFF; font-size: 1.75rem; font-weight: 700; margin: 0 0 4px; letter-spacing: -0.01em; }
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
    ' Charges Review Portal &nbsp;·&nbsp; Effective Rates'
    ' </span>'
    ' <span style="color: #FFFFFF !important; font-size: 0.8rem; font-weight: 500; font-style: italic; display: inline-block; letter-spacing: 0.02em;">'
    ' Created by GIS Specialist Frank Chingoka'
    ' </span>'
    ' </div>'
    '</div>'
)
st.markdown(header_html, unsafe_allow_html=True)

# ── Authentication (Secrets only) ───────────────────────────────────────────
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
                    st.error("❌ Secrets not configured. Contact administrator.")
                    correct_password = None
                if correct_password and password_input == correct_password:
                    st.session_state["authenticated"] = True
                    st.rerun()
                else:
                    st.error("❌ Invalid access token. Please verify credentials and re-enter.")
    st.stop()

# ── Master Data Structure ──────────────────────────────────────────────────
BCC_RATES = {
    "Residential": {
        "High Density": {"rate": 170_000.00, "unit": "sqm"},
        "Medium Density": {"rate": 190_000.00, "unit": "sqm"},
        "Low Density": {"rate": 220_000.00, "unit": "sqm"},
        "Multi- Units (Medium and Low)":{"rate": 350_000.00, "unit": "sqm"},
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
        "Billboard Prime Areas": {"rate": 1_000_000.00, "unit": "fixed_fee"},
        "Billboard Other Areas": {"rate": 750_000.00, "unit": "fixed_fee"},
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
        "LPG Exchange & Filler Cage": {"rate": 250_000.00, "unit": "fixed_fee"},
    },
}

RATE_04_CATS = {
    "Residential",
    "Institutional",
    "Industrial Development",
    "Office/Commercial Development",
    "Fences",
}

COLUMNS = ["Application ID", "Date Received", "Applicant Name", "Plot Number",
           "Category", "Development Type", "Dimension/Qty", "Est. Cost (MK)", "Scrutiny Fee (MK)"]

def _calc_fee(category: str, rate_info: dict, qty: float, subcategory: str = "") -> tuple[float, float]:
    if category in RATE_04_CATS:
        est_cost = qty * rate_info["rate"]
        fee = est_cost * 0.004
    elif rate_info["unit"] == "percentage_of_final_cost":
        est_cost = qty
        fee = est_cost * rate_info["rate"]
    else:
        est_cost = 0.0
        fee = qty * rate_info["rate"]
    
    if subcategory != "Application Fee":
        fee += BCC_RATES["Advertising"]["Application Fee"]["rate"]
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
        if "Category" in df.columns:
            df["Category"] = df["Category"].astype(str).str.title()
        df["Date Received"] = pd.to_datetime(df["Date Received"], errors='coerce')
        return df
    except Exception:
        return pd.DataFrame(columns=COLUMNS)

df_bcc = load_data()

# ── Sidebar Navigation ─────────────────────────────────────────────────────
st.sidebar.markdown("### 🏛 BCC PORTAL")
st.sidebar.markdown("---")

PAGE_MAP = {
    "🧮 Scrutiny Fee Calculator": "calculator",
    "📥 New Application Intake": "intake",
    "📊 Submission Analytics": "analytics"
}

selected_label = st.sidebar.radio("Navigate to:", list(PAGE_MAP.keys()), key="sidebar_nav")
current_page = PAGE_MAP[selected_label]

# ── Page Change Handler ────────────────────────────────────────────────────
if "prev_page" not in st.session_state:
    st.session_state.prev_page = current_page

if st.session_state.prev_page != current_page:
    keys_to_clear = [k for k in st.session_state.keys()
                     if k.startswith("calc_") or k.startswith("intake_") or k.startswith("trend_")]
    for k in keys_to_clear:
        if k in st.session_state:
            del st.session_state[k]
    st.session_state.prev_page = current_page
    st.rerun()

# ── Dashboard Controls ─────────────────────────────────────────────────────
st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ DASHBOARD CONTROLS")
live_mode = st.sidebar.toggle("🔄 Enable Real-Time Live View", value=False)
if live_mode:
    refresh_rate = st.sidebar.slider("Refresh Interval (seconds)", 5, 60, 10)
st.sidebar.markdown("---")
st.sidebar.caption("Blantyre City Council · Town Planning Section")

# ══════════════════════════════════════════════════════════════════════════════
# MODULE 1 — SCRUTINY FEE CALCULATOR
# ══════════════════════════════════════════════════════════════════════════════
if current_page == "calculator":
    st.markdown("## 🧮 SCRUTINY FEE CALCULATOR")
    st.markdown("<hr class='bcc-divider'>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1], gap="large")
   
    with col1:
        with st.container(border=True):
            st.markdown('<div class="card-title">Development Parameters</div>', unsafe_allow_html=True)
            category = st.selectbox("Plan Category", list(BCC_RATES.keys()), key="calc_cat")
            subcategory = st.selectbox("Development Type", list(BCC_RATES[category].keys()), key="calc_sub")
            item_details = BCC_RATES[category][subcategory]
            base_rate = item_details["rate"]
            unit_type = item_details["unit"]
            is_04 = category in RATE_04_CATS
           
            if unit_type == "sqm":
                st.markdown("<hr class='bcc-divider'>", unsafe_allow_html=True)
                st.markdown('<div class="card-title">📐 Area Determination Method</div>', unsafe_allow_html=True)
                input_method = st.radio(
                    "Entry format:",
                    ["Enter Total Area Manually", "Calculate Using Geometric Shapes"],
                    horizontal=True, key="calc_method"
                )
                if input_method == "Enter Total Area Manually":
                    input_val = st.number_input("Total Built-up Area (Square Meters)", min_value=0.0, value=100.0, step=10.0, key="calc_man_sqm")
                else:
                    shape = st.selectbox("Select Shape Profile:", ["Rectangle", "Triangle", "Trapezium", "Circle", "Semicircle"], key="calc_shape")
                    if shape == "Rectangle":
                        length = st.number_input("Length (m)", min_value=0.0, value=20.0, step=1.0, key="calc_rect_l")
                        width = st.number_input("Width (m)", min_value=0.0, value=15.0, step=1.0, key="calc_rect_w")
                        input_val = length * width
                    elif shape == "Triangle":
                        base = st.number_input("Base Length (m)", min_value=0.0, value=15.0, step=1.0, key="calc_tri_b")
                        height = st.number_input("Perpendicular Height (m)", min_value=0.0, value=10.0, step=1.0, key="calc_tri_h")
                        input_val = 0.5 * base * height
                    elif shape == "Trapezium":
                        side_a = st.number_input("Parallel Side A Length (m)", min_value=0.0, value=12.0, step=1.0, key="calc_trap_a")
                        side_b = st.number_input("Parallel Side B Length (m)", min_value=0.0, value=18.0, step=1.0, key="calc_trap_b")
                        trap_height = st.number_input("Perpendicular Distance / Height (m)", min_value=0.0, value=8.0, step=1.0, key="calc_trap_h")
                        input_val = 0.5 * (side_a + side_b) * trap_height
                    elif shape == "Circle":
                        radius = st.number_input("Radius (m)", min_value=0.0, value=7.0, step=0.5, key="calc_circ_r")
                        input_val = math.pi * radius ** 2
                    elif shape == "Semicircle":
                        semi_radius = st.number_input("Radius (m)", min_value=0.0, value=7.0, step=0.5, key="calc_semi_r")
                        input_val = 0.5 * math.pi * semi_radius ** 2
                    st.metric(label="Calculated Spatial Footprint", value=f"{input_val:,.2f} sqm")
            elif unit_type == "linear_meters":
                input_val = st.number_input("Total Fence Length (Meters)", min_value=0.0, value=50.0, step=5.0, key="calc_lin_m")
            elif unit_type == "percentage_of_final_cost":
                input_val = st.number_input("Declared Final Structural Cost (MK)", min_value=0.0, value=5_000_000.0, step=100_000.0, key="calc_pct_cost")
            else:
                input_val = st.number_input("Quantity / Number of Items", min_value=1.0, value=1.0, step=1.0, key="calc_fixed_qty")
    
    # Calculate after inputs are defined
    estimated_cost, scrutiny_fee_due = _calc_fee(category, item_details, input_val, subcategory)
   
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
            
            if is_04:
                st.markdown(f"""
                <div style="display:flex;gap:12px;margin-bottom:12px;">
                    <div style="flex:1;background:#F4F6FA;border-radius:8px;padding:14px;border:1px solid #DDE3EE;text-align:center;">
                        <div style="font-size:0.72rem;color:#6B7A96;font-weight:600;text-transform:uppercase;letter-spacing:0.07em;">Base Rate</div>
                        <div style="font-size:1.1rem;font-weight:700;color:#1B2A4A;">MK {base_rate:,.0f}</div>
                        <div style="font-size:0.72rem;color:#6B7A96;">per m²</div>
                    </div>
                    <div style="flex:1;background:#F4F6FA;border-radius:8px;padding:14px;border:1px solid #DDE3EE;text-align:center;">
                        <div style="font-size:0.72rem;color:#6B7A96;font-weight:600;text-transform:uppercase;letter-spacing:0.07em;">Quantity</div>
                        <div style="font-size:1.1rem;font-weight:700;color:#1B2A4A;">{input_val:,.2f}</div>
                        <div style="font-size:0.72rem;color:#6B7A96;">sqm</div>
                    </div>
                </div>
                <div style="background:#F4F6FA;border-radius:8px;padding:14px 18px;margin-bottom:12px;border:1px solid #DDE3EE;">
                    <div style="font-size:0.72rem;color:#6B7A96;font-weight:600;text-transform:uppercase;letter-spacing:0.07em;margin-bottom:4px;">Estimated Development Cost</div>
                    <div style="font-size:1.35rem;font-weight:700;color:#1B2A4A;">MK {estimated_cost:,.2f}</div>
                </div>
                <div class="fee-result">
                    <div class="fee-label">Scrutiny Fee Due (0.4%)</div>
                    <div class="fee-amount">MK {scrutiny_fee_due:,.2f}</div>
                    <div class="fee-note">0.4% of estimated development cost + Application Fee</div>
                </div>
                """, unsafe_allow_html=True)
            elif unit_type == "percentage_of_final_cost":
                st.markdown(f"""
                <div style="background:#F4F6FA;border-radius:8px;padding:14px 18px;margin-bottom:12px;border:1px solid #DDE3EE;">
                    <div style="font-size:0.72rem;color:#6B7A96;font-weight:600;text-transform:uppercase;letter-spacing:0.07em;margin-bottom:4px;">Declared Final Cost</div>
                    <div style="font-size:1.35rem;font-weight:700;color:#1B2A4A;">MK {estimated_cost:,.2f}</div>
                </div>
                <div class="fee-result">
                    <div class="fee-label">Scrutiny Fee Due (0.1%)</div>
                    <div class="fee-amount">MK {scrutiny_fee_due:,.2f}</div>
                    <div class="fee-note">0.1% of declared final cost + Application Fee</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="fee-result">
                    <div class="fee-label">Total Scrutiny Fee Due</div>
                    <div class="fee-amount">MK {scrutiny_fee_due:,.2f}</div>
                    <div class="fee-note">Fixed rate — {subcategory}</div>
                </div>
                """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# MODULE 2 — NEW APPLICATION INTAKE
# ══════════════════════════════════════════════════════════════════════════════
elif current_page == "intake":
    st.markdown("## 📥 NEW APPLICATION INTAKE")
    st.markdown("<hr class='bcc-divider'>", unsafe_allow_html=True)
    st.markdown("Complete the fields below to register a new plan submission to the BCC registry.")
   
    col1, col2 = st.columns(2, gap="large")
    with col1:
        app_id = st.text_input("Application / File ID", placeholder="e.g., BCC/TP/2026/250", key="intake_id")
        applicant_name = st.text_input("Applicant Name / Developer Entity", placeholder="e.g., Shanaloli Manda / FS Investments", key="intake_name")
        date_rcvd = st.date_input("Date Received", value=datetime.today(), key="intake_date")
    with col2:
        plot_number = st.text_input("Plot Number / Parcel ID", placeholder="e.g., Plot BC 24", key="intake_plot")
        intake_category = st.selectbox("Plan Category", list(BCC_RATES.keys()), key="intake_cat")
        intake_subcategory = st.selectbox("Development Type", list(BCC_RATES[intake_category].keys()), key="intake_sub")
   
    st.markdown("<hr class='bcc-divider'>", unsafe_allow_html=True)
   
    with st.container(border=True):
        st.markdown('<div class="card-title">Dimensional Metrics</div>', unsafe_allow_html=True)
        rate_info = BCC_RATES[intake_category][intake_subcategory]
        if rate_info["unit"] == "sqm":
            measure_val = st.number_input("Total Built-up Area (sqm)", min_value=0.1, value=120.0, key="intake_sqm")
        elif rate_info["unit"] == "linear_meters":
            measure_val = st.number_input("Total Fence Length (meters)", min_value=0.1, value=40.0, key="intake_lin")
        elif rate_info["unit"] == "percentage_of_final_cost":
            measure_val = st.number_input("Declared Final Structural Cost (MK)", min_value=1.0, value=10_000_000.0, key="intake_cost")
        else:
            measure_val = st.number_input("Quantity / Count Item Total", min_value=1.0, value=1.0, step=1.0, key="intake_qty")
   
    st.markdown("<br>", unsafe_allow_html=True)
    submit_btn = st.button("📄 Append Entry to Registry", use_container_width=True)
   
    if submit_btn:
        errors = []
        if not app_id.strip(): errors.append("Application ID Reference Number is required.")
        if not applicant_name.strip(): errors.append("Applicant Name is required.")
        if not plot_number.strip(): errors.append("Plot Number is required.")
        if errors:
            for e in errors:
                st.error(f"❌ {e}")
        else:
            calc_est_cost, calc_fee = _calc_fee(intake_category, rate_info, measure_val, intake_subcategory)
            new_row = {
                "Application ID": app_id.strip().upper(),
                "Date Received": date_rcvd.strftime("%Y-%m-%d"),
                "Applicant Name": applicant_name.strip(),
                "Plot Number": plot_number.strip(),
                "Category": intake_category,
                "Development Type": intake_subcategory,
                "Dimension/Qty": measure_val,
                "Est. Cost (MK)": calc_est_cost,
                "Scrutiny Fee (MK)": calc_fee,
            }
            try:
                df_existing = conn.read(ttl=0)
            except Exception:
                df_existing = pd.DataFrame(columns=COLUMNS)
            df_updated = pd.concat([df_existing, pd.DataFrame([new_row])], ignore_index=True)
            conn.update(data=df_updated)
            st.cache_data.clear()
            st.success(f"✅ Record for **{applicant_name.strip()} ({plot_number.strip()})** appended securely to cloud index file.")
            st.balloons()

# ══════════════════════════════════════════════════════════════════════════════
# MODULE 3 — SUBMISSION ANALYTICS
# ══════════════════════════════════════════════════════════════════════════════
else:
    st.markdown("## 📊 SUBMISSION ANALYTICS")
    st.markdown("<hr class='bcc-divider'>", unsafe_allow_html=True)
   
    if df_bcc.empty:
        st.info("📭 No applications on record yet. Use **New Application Intake** to add your first entry.")
    else:
        total_apps = len(df_bcc)
        total_fees = df_bcc["Scrutiny Fee (MK)"].sum()
        avg_fee = df_bcc["Scrutiny Fee (MK)"].mean()
       
        k1, k2, k3 = st.columns(3, gap="large")
        k1.markdown(f"""
        <div class="kpi-tile">
            <div class="kpi-label">Total Applications</div>
            <div class="kpi-value">{total_apps:,}</div>
            <div class="kpi-sub">All time on record</div>
        </div>""", unsafe_allow_html=True)
        k2.markdown(f"""
        <div class="kpi-tile">
            <div class="kpi-label">Total Fees Collected</div>
            <div class="kpi-value" style="font-size:1.25rem;">MK {total_fees:,.0f}</div>
            <div class="kpi-sub">Cumulative scrutiny fees</div>
        </div>""", unsafe_allow_html=True)
        k3.markdown(f"""
        <div class="kpi-tile">
            <div class="kpi-label">Average Scrutiny Fee</div>
            <div class="kpi-value" style="font-size:1.25rem;">MK {avg_fee:,.0f}</div>
            <div class="kpi-sub">Per application</div>
        </div>""", unsafe_allow_html=True)
       
        st.markdown("<hr class='bcc-divider'>", unsafe_allow_html=True)
        st.markdown("#### Submission Trends")
       
        time_frame = st.radio("Group by:", ["Weekly", "Monthly", "Quarterly"], horizontal=True, key="trend_group")
       
        df_chart = df_bcc.copy()
        df_chart["Date Received"] = pd.to_datetime(df_chart["Date Received"], errors='coerce')
        df_chart = df_chart.dropna(subset=["Date Received"])
       
        if not df_chart.empty:
            period_map = {"Weekly": "W", "Monthly": "M", "Quarterly": "Q"}
            if time_frame == "Weekly":
                df_chart["Period"] = df_chart["Date Received"].dt.to_period("W").dt.start_time.dt.strftime('%Y-%m-%d')
            else:
                df_chart["Period"] = df_chart["Date Received"].dt.to_period(period_map[time_frame]).astype(str)
           
            summary = df_chart.groupby(["Period", "Category"]).size().reset_index(name="Submissions Count")
           
            col1, col2 = st.columns([3, 2], gap="large")
           
            with col1:
                fig_trend = px.bar(
                    summary, x="Period", y="Submissions Count", color="Category",
                    title=f"Submission Volume — {time_frame} View",
                    barmode="stack", height=580,
                    color_discrete_sequence=px.colors.qualitative.Safe
                )
                fig_trend.update_layout(
                    autosize=True,
                    plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
                    font=dict(size=14, color="#1A202C"),
                    title_font=dict(size=20, color="#1B2A4A"),
                    legend=dict(orientation="h", yanchor="top", y=1.15, xanchor="center", x=0.5, font=dict(size=13, color="#1A202C")),
                    margin=dict(t=130, b=110, l=50, r=30),
                    xaxis=dict(tickangle=-35, tickfont=dict(size=12, color="#1A202C"), title="Period", title_font=dict(size=14, color="#1A202C")),
                    yaxis=dict(tickfont=dict(size=13, color="#1A202C"), title="Number of Submissions", title_font=dict(size=14, color="#1A202C"), gridcolor="#EEF0F5")
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
                    font=dict(size=14, color="#1A202C"),
                    title_font=dict(size=20, color="#1B2A4A"),
                    legend=dict(orientation="h", yanchor="bottom", y=-0.25, font=dict(size=13, color="#1A202C"))
                )
                st.plotly_chart(fig_share, use_container_width=True, theme=None)
           
            st.markdown("<hr class='bcc-divider'>", unsafe_allow_html=True)
            st.markdown(f"#### 🗓️ Volume Matrix — {time_frame} Summary")
           
            pivot_table = df_chart.pivot_table(
                index="Category", columns="Period",
                values="Application ID", aggfunc="count", fill_value=0,
            )
            pivot_table.loc['TOTAL'] = pivot_table.sum()
           
            styled_pivot = pivot_table.style.set_properties(**{
                'background-color': '#FFFFFF',
                'color': '#000000',
                'border-color': '#DDE3EE'
            }).apply(
                lambda row: ['font-weight: bold; background-color: #F4F6FA;' if row.name == 'TOTAL' else '' for _ in row], axis=1
            )
            st.dataframe(styled_pivot, use_container_width=True)
       
        # Search registry
        st.markdown("<hr class='bcc-divider'>", unsafe_allow_html=True)
        st.markdown("#### 📋 Application Registry")
        search_query = st.text_input("Search registry:", placeholder="Filter by Plot #, Applicant name, or File ID…", label_visibility="collapsed")
        df_display = df_bcc.copy()
       
        if search_query.strip():
            q = search_query.strip().lower()
            df_display = df_display[
                df_display["Application ID"].astype(str).str.lower().str.contains(q, na=False) |
                df_display["Applicant Name"].astype(str).str.lower().str.contains(q, na=False) |
                df_display["Plot Number"].astype(str).str.lower().str.contains(q, na=False)
            ]
       
        display_cols_map = {
            "Est. Cost (MK)": "Est. Cost Base (MK)",
            "Scrutiny Fee (MK)": "Scrutiny Fee Charged (MK)"
        }
        df_display_renamed = df_display.sort_values(by="Date Received", ascending=False).rename(columns=display_cols_map)
       
        format_dict = {
            "Est. Cost Base (MK)": "{:,.2f}",
            "Scrutiny Fee Charged (MK)": "{:,.2f}"
        }
        if pd.api.types.is_datetime64_any_dtype(df_display_renamed["Date Received"]):
            format_dict["Date Received"] = lambda x: x.strftime('%Y-%m-%d') if pd.notnull(x) else ""
       
        styled_df = df_display_renamed.style.set_properties(**{
            'background-color': '#FFFFFF',
            'color': '#000000',
            'border-color': '#DDE3EE'
        }).format(format_dict)
       
        st.dataframe(styled_df, use_container_width=True)

# ── Live Mode ───────────────────────────────────────────────────────────────
if live_mode:
    time.sleep(refresh_rate)
    st.rerun()
