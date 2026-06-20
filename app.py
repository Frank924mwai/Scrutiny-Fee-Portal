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
                        input
