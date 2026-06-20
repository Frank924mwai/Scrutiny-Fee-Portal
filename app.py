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
            password_input = st.text_input("Internal Access Password", type="password", placeholder="••••••••
