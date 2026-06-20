import streamlit as st

# ── 1. Page Configuration (MUST be first Streamlit call) ──────────────────────
st.set_page_config(
    page_title="BCC Town Planning Fees Portal",
    page_icon="🏢",
    layout="wide"
)

# ── Global High-Contrast Mobile Typography Overrides ──────────────────────────
st.markdown("""
<style>
    /* Force form subheaders, labels, and text markdown to remain high-contrast dark gray/black */
    div[data-testid="stMarkdownContainer"] p, 
    div[data-testid="stMarkdownContainer"] span,
    .stSlider label, 
    .stNumberInput label,
    label[data-testid="stWidgetLabel"] p {
        color: #1A202C !important;
        font-weight: 500 !important;
    }
    
    /* Target radio button option text specifically (Area method, Trends grouping) */
    div[data-testid="stRadio"] label div[data-testid="stMarkdownContainer"] p {
        color: #1A202C !important;
        font-weight: 500 !important;
    }
    
    /* Target section headings inside your forms */
    h3 {
        color: #1E65B5 !important;
    }

    /* Plotly chart transparent viewport override rules */
    iframe[title="st.plotly_chart"] {
        background-color: transparent !important;
    }
    div[data-testid="stPlotlyChart"] {
        background-color: transparent !important;
    }
</style>
""", unsafe_allow_html=True)

import pandas as pd
import os
import math
import plotly.express as px
from datetime import datetime
import time
from streamlit_gsheets import GSheetsConnection

# ── Global Styling ────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Palette ──────────────────────────────────────────────────────────────── */
:root {
    --navy:   #1E65B5;
    --gold:   #C49A2A;
    --bg:      #F4F6FA;
    --card:   #FFFFFF;
    --body:   #3A4557;
    --border: #DDE3EE;
    --muted:  #6B7A96;
} 

/* ── Page background ──────────────────────────────────────────────────────── */
.stApp { background-color: var(--bg); } 

/* ── Sidebar ──────────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background-color: var(--navy) !important;
}
[data-testid="stSidebar"] * {
    color: #E8EDF5 !important;
}
[data-testid="stSidebar"] .stRadio label {
    font-size: 0.95rem;
    padding: 6px 0;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: var(--gold) !important;
    font-size: 0.85rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
} 

/* ── Top header band ──────────────────────────────────────────────────────── */
.bcc-header {
    background: var(--navy);
    border-radius: 10px;
    padding: 24px 32px 20px;
    margin-bottom: 28px;
    border-bottom: 3px solid var(--gold);
}
.bcc-header h1 {
    color: #FFFFFF;
    font-size: 1.75rem;
    font-weight: 700;
    margin: 0 0 4px;
    letter-spacing: -0.01em;
}
.bcc-header .subtitle {
    color: #A8B8D0;
    font-size: 0.92rem;
    margin: 0;
}
.bcc-header .badge {
    display: inline-block;
    background: var(--gold);
    color: var(--navy);
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    border-radius: 4px;
    padding: 3px 9px;
    margin-top: 10px;
} 

/* ── Section page headings ────────────────────────────────────────────────── */
h1 { color: var(--navy) !important; font-size: 1.5rem !important; }
h2 { color: var(--navy) !important; }
h3 { color: var(--navy) !important; font-size: 1.05rem !important; } 

/* ── Card Typography Extensions ───────────────────────────────────────────── */
.card-title {
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 16px;
    padding-bottom: 10px;
    border-bottom: 1px solid var(--border);
} 

/* ── KPI tiles ────────────────────────────────────────────────────────────── */
.kpi-tile {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 20px 24px;
    text-align: center;
}
.kpi-label {
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 8px;
}
.kpi-value {
    font-size: 1.6rem;
    font-weight: 700;
    color: var(--navy);
    line-height: 1.1;
}
.kpi-sub {
    font-size: 0.75rem;
    color: var(--muted);
    margin-top: 4px;
} 

/* ── Fee result box ───────────────────────────────────────────────────────── */
.fee-result {
    background: var(--navy);
    border-radius: 10px;
    padding: 22px 26px;
    margin-top: 16px;
    border-left: 4px solid var(--gold);
}
.fee-result .fee-label {
    color: #A8B8D0;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 6px;
}
.fee-result .fee-amount {
    color: #FFFFFF;
    font-size: 1.9rem;
    font-weight: 700;
    letter-spacing: -0.02em;
}
.fee-result .fee-note {
    color: var(--gold);
    font-size: 0.78rem;
    margin-top: 6px;
} 

/* ── Divider ──────────────────────────────────────────────────────────────── */
.bcc-divider {
    border: none;
    border-top: 1px solid var(--border);
    margin: 24px 0;
} 

/* ── Streamlit widget tweaks ──────────────────────────────────────────────── */
[data-testid="stMetric"] {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 14px 18px !important;
}
[data-testid="stMetricLabel"] { color: var(--muted) !important; font-size: 0.8rem !important; }
[data-testid="stMetricValue"] { color: var(--navy) !important; } 

/* Info boxes */
[data-testid="stAlert"] {
    border-radius: 8px !important;
} 

/* Selectbox / input consistent height */
.stSelectbox > div > div,
.stTextInput > div > div {
    border-radius: 6px !important;
} 

/* Action Button overrides */
div.stButton > button {
    background-color: var(--navy) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 10px 24px !important;
    font-weight: 600 !important;
    letter-spacing: 0.03em;
    transition: background 0.2s;
}
div.stButton > button:hover {
    background-color: #243660 !important;
} 

/* Dataframe container borders */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    overflow: hidden;
}
</style>
""", unsafe_allow_html=True)

# ── Portal Header Band ────────────────────────────────────────────────────────
header_html = (
    '<div style="background-color: #1E65B5; border-radius: 8px; border-bottom: 4px solid #C49A2A; padding: 22px 26px; margin-bottom: 28px; width: 100%; box-sizing: border-box;">'
    '    <p style="margin: 0 0 14px 0; color: #FFFFFF !important; font-weight: 700; font-size: 1.25rem; letter-spacing: 0.04em; line-height: 1.3; text-transform: uppercase;">'
    '        Department of Town Planning and Estates Services'
    '    </p>'
    '    <div style="display: flex; flex-wrap: wrap; gap: 12px; align-items: center;">'
    '        <span style="background-color: #C49A2A; color: #1E65B5; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; border-radius: 4px; padding: 5px 12px; display: inline-block;">'
    '            Charges Review Portal &nbsp;·&nbsp; Effective Rates'
    '        </span>'
    '        <span style="color: #FFFFFF !important; font-size: 0.8rem; font-weight: 500; font-style: italic; display: inline-block; letter-spacing: 0.02em;">'
    '            Created by GIS Specialist Frank Chingoka'
    '        </span>'
    '    </div>'
    '</div>'
)
st.markdown(header_html, unsafe_allow_html=True)

# ── Authentication Gate Layer ─────────────────────────────────────────────────
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
                if password_input == st.secrets["portal_password"]:
                    st.session_state["authenticated"] = True
                    st.rerun()
                else:
                    st.error("❌ Invalid access token. Please verify credentials and re-enter.")
    st.stop()

# ── 2. Master Data Structure ──────────────────────────────────────────────────
BCC_RATES = {
    "Residential": {
        "High Density":                 {"rate": 170_000.00, "unit": "sqm"},
        "Medium Density":               {"rate": 190_000.00, "unit": "sqm"},
        "Low Density":                  {"rate": 220_000.00, "unit": "sqm"},
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
        "Application Fee":          {"rate":    15_000.00, "unit": "fixed_fee"},
        "Billboard Prime Areas":    {"rate": 1_000_000.00, "unit": "fixed_fee"},
        "Billboard Other Areas":    {"rate":   750_000.00, "unit": "fixed_fee"},
        "Single Sided Signpost":    {"rate":   125_000.00, "unit": "fixed_fee"},
        "Double Sided Signpost":    {"rate":   190_000.00, "unit": "fixed_fee"},
        "Composite Signpost":       {"rate":   500_000.00, "unit": "fixed_fee"},
        "Gantry":                   {"rate": 3_000_000.00, "unit": "fixed_fee"},
        "Cantilevered Billboard":   {"rate": 2_000_000.00, "unit": "fixed_fee"},
    },
    "Miscellaneous": {
        "One surface car parking space":              {"rate":   280_000.00, "unit": "fixed_fee"},
        "Application in Principle (Outline Application)": {"rate": 750_000.00, "unit": "fixed_fee"},
        "Change of Use":                              {"rate":   750_000.00, "unit": "fixed_fee"},
        "Subdivision per plot created":               {"rate":   150_000.00, "unit": "fixed_fee"},
        "Plot Regularisation":                        {"rate":   500_000.00, "unit": "fixed_fee"},
        "Infill Plot Creation":                       {"rate":   500_000.00, "unit": "fixed_fee"},
        "Sewer Application Fees":                     {"rate":   100_000.00, "unit": "fixed_fee"},
        "Certificate of Occupancy":                   {"rate":        0.001,  "unit": "percentage_of_final_cost"},
        "LPG Exchange Cage":                          {"rate":   150_000.00, "unit": "fixed_fee"},
        "LPG Exchange & Filler Cage":                 {"rate":   250_000.00, "unit": "fixed_fee"},
    },
}

RATE_04_CATS = {
    "Residential",
    "Institutional",
    "Industrial Development",
    "Office/Commercial Development",
    "Fences",
}

# ── 3. Data Engine (Cloud Sheets Integration) ─────────────────────────────────
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

    if category == "Advertising" and subcategory != "Application Fee":
        app_fee_baseline = BCC_RATES["Advertising"]["Application Fee"]["rate"]
        fee += app_fee_baseline

    return est_cost, fee

conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=5)
def load_data() -> pd.DataFrame:
    try:
        df = conn.read()
        if df is None or df.empty:
            return pd.DataFrame(columns=COLUMNS)

        for col in COLUMNS:
            if col not in df.columns:
                df[col] = "N/A"

        if "Category" in df.columns:
            df["Category"] = df["Category"].astype(str).str.strip().str.title()

        df["Date Received"] = pd.to_datetime(df["Date Received"], errors='coerce')
        return df
    except Exception:
        return pd.DataFrame(columns=COLUMNS)

df_bcc = load_data()

# ── 4. Sidebar Navigation ─────────────────────────────────────────────────────
st.sidebar.markdown("### 🏛 BCC PORTAL")
st.sidebar.markdown("---")

PAGE_MAP = {
    "🧮 Scrutiny Fee Calculator": "Scrutiny Fee Calculator",
    "📥 New Application Intake": "New Application Intake",
    "📊 Submission Analytics": "Submission Analytics"
}

selected_label = st.sidebar.radio("Navigate to:", list(PAGE_MAP.keys()))
page = PAGE_MAP[selected_label]

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
if page == "Scrutiny Fee Calculator":
    st.markdown("## 🧮 SCRUTINY FEE CALCULATOR")
    st.markdown("<hr class='bcc-divider'>", unsafe_allow_html=True)
    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        with st.container(border=True):
            st.markdown('<div class="card-title">Development Parameters</div>', unsafe_allow_html=True)
            category    = st.selectbox("Plan Category", list(BCC_RATES.keys()), key="calc_cat")
            subcategory = st.selectbox("Development Type", list(BCC_RATES[category].keys()), key="calc_sub")

            item_details = BCC_RATES[category][subcategory]
            base_rate    = item_details["rate"]
            unit_type    = item_details["unit"]
            is_04        = category in RATE_04_CATS

            input_val  = 0.0
            unit_label = ""

            if unit_type == "sqm":
                st.markdown("<hr class='bcc-divider'>", unsafe_allow_html=True)
                st.markdown('<div class="card-title">📐 Area Determination Method</div>', unsafe_allow_html=True)
                input_method = st.radio(
                    "Entry format:",
                    ["Enter Total Area Manually", "Calculate Using Geometric Shapes"],
                    horizontal=True,
                )

                if input_method == "Enter Total Area Manually":
                    input_val = st.number_input("Total Built-up Area (Square Meters)", min_value=0.0, value=100.0, step=10.0, key="calc_man_sqm")
                else:
                    shape = st.selectbox("Select Shape Profile:", ["Rectangle", "Triangle", "Trapezium", "Circle", "Semicircle"])

                    if shape == "Rectangle":
                        length = st.number_input("Length (m)", min_value=0.0, value=20.0, step=1.0)
                        width  = st.number_input("Width (m)",  min_value=0.0, value=15.0, step=1.0)
                        input_val = length * width
                    elif shape == "Triangle":
                        base   = st.number_input("Base Length (m)",          min_value=0.0, value=15.0, step=1.0)
                        height = st.number_input("Perpendicular Height (m)", min_value=0.0, value=10.0, step=1.0)
                        input_val = 0.5 * base * height
                    elif shape == "Trapezium":
                        side_a      = st.number_input("Parallel Side A Length (m)",          min_value=0.0, value=12.0, step=1.0)
                        side_b      = st.number_input("Parallel Side B Length (m)",          min_value=0.0, value=18.0, step=1.0)
                        trap_height = st.number_input("Perpendicular Distance / Height (m)", min_value=0.0, value=8.0,  step=1.0)
                        input_val = 0.5 * (side_a + side_b) * trap_height
                    elif shape == "Circle":
                        radius = st.number_input("Radius (m)", min_value=0.0, value=7.0, step=0.5)
                        input_val = math.pi * radius ** 2
                    elif shape == "Semicircle":
                        semi_radius = st.number_input("Radius (m)", min_value=0.0, value=7.0, step=0.5)
                        input_val = 0.5 * math.pi * semi_radius ** 2

                    st.metric(label="Calculated Spatial Footprint", value=f"{input_val:,.2f} sqm")
                unit_label = "per m²"

            elif unit_type == "linear_meters":
                input_val  = st.number_input("Total Fence Length (Meters)", min_value=0.0, value=50.0, step=5.0, key="calc_lin_m")
                unit_label = "per linear meter"
            elif unit_type == "percentage_of_final_cost":
                input_val  = st.number_input("Declared Final Structural Cost (MK)", min_value=0.0, value=5_000_000.0, step=100_000.0, key="calc_pct_cost")
                unit_label = "0.1% of final cost"
            else:
                input_val  = st.number_input("Quantity / Number of Items", min_value=1.0, value=1.0, step=1.0, key="calc_fixed_qty")
                unit_label = "fixed rate fee"

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
                        <div style="font-size:0.72rem;color:#6B7A96;">{unit_label}</div>
                    </div>
                    <div style="flex:1;background:#F4F6FA;border-radius:8px;padding:14px;border:1px solid #DDE3EE;text-align:center;">
                        <div style="font-size:0.72rem;color:#6B7A96;font-weight:600;text-transform:uppercase;letter-spacing:0.07em;">Quantity</div>
                        <div style="font-size:1.1rem;font-weight:700;color:#1B2A4A;">{input_val:,.2f}</div>
                        <div style="font-size:0.72rem;color:#6B7A96;">units</div>
                    </div>
                </div>
                <div style="background:#F4F6FA;border-radius:8px;padding:14px 18px;margin-bottom:12px;border:1px solid #DDE3EE;">
                    <div style="font-size:0.72rem;color:#6B7A96;font-weight:600;text-transform:uppercase;letter-spacing:0.07em;margin-bottom:4px;">Estimated Development Cost</div>
                    <div style="font-size:1.35rem;font-weight:700;color:#1B2A4A;">MK {estimated_cost:,.2f}</div>
                </div>
                <div class="fee-result">
                    <div class="fee-label">Scrutiny Fee Due (0.4%)</div>
                    <div class="fee-amount">MK {scrutiny_fee_due:,.2f}</div>
                    <div class="fee-note">0.4% of estimated development cost</div>
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
                    <div class="fee-note">0.1% of declared final cost</div>
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
# MODULE 2 — APPLICATION INTAKE FORM
# ══════════════════════════════════════════════════════════════════════════════
elif page == "New Application Intake":
    st.markdown("## 📥 NEW APPLICATION INTAKE")
    st.markdown("<hr class='bcc-divider'>", unsafe_allow_html=True)
    st.markdown("Complete the fields below to register a new plan submission to the BCC registry.")

    col1, col2 = st.columns(2, gap="large")

    with col1:
        app_id         = st.text_input("Application / File ID", placeholder="e.g., BCC/TP/2026/250")
        applicant_name = st.text_input("Applicant Name / Developer Entity", placeholder="e.g., Shanaloli Manda / FS Investments")
        date_rcvd      = st.date_input("Date Received", value=datetime.today())

    with col2:
        plot_number        = st.text_input("Plot Number / Parcel ID", placeholder="e.g., Plot BC 24")
        intake_category    = st.selectbox("Plan Category", list(BCC_RATES.keys()), key="intake_cat")
        intake_subcategory = st.selectbox("Development Type", list(BCC_RATES[intake_category].keys()), key="intake_sub")

    st.markdown("<hr class='bcc-divider'>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown('<div class="card-title">Dimensional Metrics</div>', unsafe_allow_html=True)
        rate_info = BCC_RATES[intake_category][intake_subcategory]

        if rate_info["unit"] == "sqm":
            measure_val = st.number_input("Total Built-up Area (sqm)",           min_value=0.1, value=120.0)
        elif rate_info["unit"] == "linear_meters":
            measure_val = st.number_input("Total Fence Length (meters)",         min_value=0.1, value=40.0)
        elif rate_info["unit"] == "percentage_of_final_cost":
            measure_val = st.number_input("Declared Final Structural Cost (MK)", min_value=1.0, value=10_000_000.0)
        else:
            measure_val = st.number_input("Quantity / Count Item Total",         min_value=1.0, value=1.0, step=1.0)

    st.markdown("<br>", unsafe_allow_html=True)
    submit_btn = st.button("📄 Append Entry to Registry")

    if submit_btn:
        errors = []
        if not app_id.strip():         errors.append("Application ID Reference Number is required.")
        if not applicant_name.strip(): errors.append("Applicant Name is required.")
        if not plot_number.strip():    errors.append("Plot Number is required.")

        if errors:
            for e in errors:
                st.error(f"❌ {e}")
        else:
            calc_est_cost, calc_fee = _calc_fee(intake_category, rate_info, measure_val, intake_subcategory)

            new_row = {
                "Application ID":    app_id.strip().upper(),
                "Date Received":     date_rcvd.strftime("%Y-%m-%d"),
                "Applicant Name":    applicant_name.strip(),
                "Plot Number":       plot_number.strip().upper(),
                "Category":          intake_category,
                "Development Type":  intake_subcategory,
                "Dimension/Qty":     measure_val,
                "Est. Cost (MK)":    calc_est_cost,
                "Scrutiny Fee (MK)": calc_fee,
            }

            try:
                df_existing = conn.read(ttl=0)
            except Exception:
                df_existing = pd.DataFrame(columns=COLUMNS)

            df_updated = pd.concat([df_existing, pd.DataFrame([new_row])], ignore_index=True)
            conn.update(worksheet="Sheet1", data=df_updated)

            st.cache_data.clear()
            st.success(f"✅ Record for **{applicant_name.strip()} ({plot_number.strip()})** appended securely to cloud index file.")
            st.balloons()

# ══════════════════════════════════════════════════════════════════════════════
# MODULE 3 — SUBMISSION ANALYTICS & SEARCH REGISTRY
# ══════════════════════════════════════════════════════════════════════════════
else:
    st.markdown("## 📊 SUBMISSION ANALYTICS")
    st.markdown("<hr class='bcc-divider'>", unsafe_allow_html=True)

    if df_bcc.empty:
        st.info("📭 No applications on record yet. Use **New Application Intake** to add your first entry, then return here to see analytics.")
    else:
        total_apps  = len(df_bcc)
        total_fees  = df_bcc["Scrutiny Fee (MK)"].sum()
        avg_fee     = df_bcc["Scrutiny Fee (MK)"].mean()

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
        time_frame = st.radio("Group by:", ["Weekly", "Monthly", "Quarterly"], horizontal=True)

        df_chart = df_bcc.copy()
        df_chart["Date Received"] = pd.to_datetime(df_chart["Date Received"], errors='coerce')
        df_chart = df_chart.dropna(subset=["Date Received"])

        if df_chart.empty:
            st.warning("⚠️ No valid date stamps found to display dynamic trend lines.")
        else:
            period_map = {"Weekly": "W", "Monthly": "M", "Quarterly": "Q"}

            if time_frame == "Weekly":
                df_chart["Period"] = df_chart["Date Received"].dt.to_period("W").dt.start_time.dt.strftime('%Y-%m-%d')
            else:
                df_chart["Period"] = df_chart["Date Received"].dt.to_period(period_map[time_frame]).astype(str)

            summary = df_chart.groupby(["Period", "Category"]).size().reset_index(name="Submissions Count")
            col1, col2 = st.columns([3, 2],gap="large")
            with col1:
            fig_trend = px.bar(
            summary,
            x="Period", y="Submissions Count", color="Category",
            title=f"Submission Volume — {time_frame} View",
            barmode="stack",
            color_discrete_sequence=["#1E65B5", "#C49A2A", "#3A4557", "#6B7A96", "#A8B8D0"], # Custom brand palette)
                
                fig_trend.update_layout(
                    font=dict(family="Source Sans Pro, sans-serif", color="#1A202C", size=12),
                    title_font=dict(size=14, color="#1B2A4A", weight="bold"),
                    xaxis=dict(
                        title=dict(text="Time Interval", font=dict(color="#1A202C", size=13, weight="bold")),
                        tickfont=dict(color="#1A202C", size=11),
                        gridcolor="#EEF0F5",
                        linecolor="#1A202C",
                        type="category",
                        tickangle=-45
                    ),
                    yaxis=dict(
                        title=dict(text="Total Volume Collected", font=dict(color="#1A202C", size=13, weight="bold")),
                        tickfont=dict(color="#1A202C", size=11),
                        gridcolor="#E2E8F0",
                        linecolor="#1A202C"
                    ),
                    legend=dict(
                        title=dict(font=dict(color="#1A202C", size=11, weight="bold")),
                        orientation="h",
                        yanchor="top", y=-0.4,
                        xanchor="center", x=0.5,
                        font=dict(color="#1A202C", size=11),
                        bgcolor="rgba(255, 255, 255, 0.7)"
                    ),
                    margin=dict(t=50, b=120, l=0, r=0),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)"
                )
                st.plotly_chart(fig_trend, use_container_width=True)

            with col2:
                pie_data  = df_chart.groupby("Category").size().reset_index(name="Total Applications")
                pie_data["Label"] = pie_data["Category"].str.replace(r"^\d+\.\s*", "", regex=True)
            fig_share = px.pie(
                pie_data,
                names="Label",
                values="Total Applications",
                title="Share by Category",
                color_discrete_sequence=["#1E65B5", "#C49A2A", "#3A4557", "#6B7A96", "#A8B8D0"], # Custom brand palette
                hole=0.38,
            )
                fig_share.update_traces(
                    textposition="inside",
                    textinfo="percent+value",
                    insidetextfont=dict(color='#FFFFFF', size=11, weight="bold"),
                    outsidetextfont=dict(color='#1A202C', size=11, weight="bold"),
                    pull=[0.02] * len(pie_data),
                )
                fig_share.update_layout(
                    font=dict(family="Source Sans Pro, sans-serif", color="#1A202C", size=11),
                    title_font=dict(size=14, color="#1B2A4A", weight="bold"),
                    showlegend=True,
                    legend=dict(
                        title=dict(font=dict(color="#1A202C", size=11, weight="bold")),
                        orientation="h",
                        yanchor="top", y=-0.15,
                        xanchor="center", x=0.5,
                        font=dict(color="#1A202C", size=10),
                        bgcolor="rgba(255, 255, 255, 0.7)"
                    ),
                    margin=dict(t=50, b=100, l=0, r=0),
                    paper_bgcolor="rgba(0,0,0,0)"
                )
                st.plotly_chart(fig_share, use_container_width=True)

            st.markdown("<hr class='bcc-divider'>", unsafe_allow_html=True)
            st.markdown(f"#### 🗓️ Volume Matrix — {time_frame} Summary Table")

            pivot_table = df_chart.pivot_table(
                index="Category", columns="Period",
                values="Application ID", aggfunc="count", fill_value=0,
            )
            
            # Formulate margins calculation cleanly
            pivot_table['TOTAL'] = pivot_table.sum(axis=1)
            pivot_table.loc['GRAND TOTAL'] = pivot_table.sum(axis=0)

            styled_pivot = pivot_table.style.apply(
                lambda row: ['font-weight: bold; background-color: #EEF2F6;' if row.name == 'GRAND TOTAL' else '' for _ in row],
                axis=1
            )
            st.dataframe(styled_pivot, use_container_width=True)

        # ── Search registry ──
        st.markdown("<hr class='bcc-divider'>", unsafe_allow_html=True)
        st.markdown("#### 📋 Application Registry")
        search_query = st.text_input(
            "Search registry:",
            placeholder="Filter by Plot #, Applicant name, or File ID…",
            label_visibility="collapsed",
        )

        df_display = df_bcc.copy()
        if search_query.strip():
            q = search_query.strip().lower()
            df_display = df_display[
                df_display["Application ID"].astype(str).str.lower().str.contains(q, na=False)
                | df_display["Applicant Name"].astype(str).str.lower().str.contains(q, na=False)
                | df_display["Plot Number"].astype(str).str.lower().str.contains(q, na=False)
            ]

        st.dataframe(
            df_display.sort_values(by="Date Received", ascending=False),
            column_config={
                "Date Received":     st.column_config.DateColumn("Date Received"),
                "Est. Cost (MK)":    st.column_config.NumberColumn("Est. Cost Base (MK)",       format="%,.2f"),
                "Scrutiny Fee (MK)": st.column_config.NumberColumn("Scrutiny Fee Charged (MK)", format="%,.2f"),
            },
            use_container_width=True,
        )

# ── 5. Passive Execution Loop for Live Tracker ────────────────────────────────
if live_mode and not df_bcc.empty:
    if "last_refresh" not in st.session_state:
        st.session_state["last_refresh"] = time.time()
    
    current_time = time.time()
    if current_time - st.session_state["last_refresh"] >= refresh_rate:
        st.session_state["last_refresh"] = current_time
        st.rerun()
    else:
        time.sleep(1)
        st.rerun()
