"""BCC Town Planning and Estates portal.

Required Streamlit secrets (for example, .streamlit/secrets.toml):

    [auth]
    password = "use-a-long-unique-password"

The Google Sheets connection must be configured as ``connections.gsheets`` for
streamlit-gsheets.  The sheet is the system of record; this application reads
the latest sheet immediately before every write to reduce lost updates.
"""

from __future__ import annotations

import hashlib
import hmac
import html
import json
import logging
import math
import re
from datetime import date
from typing import Any, Mapping

import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_gsheets import GSheetsConnection


st.set_page_config(
    page_title="BCC Town Planning and Estates Portal",
    page_icon="🏛️",
    layout="wide",
)


LOGGER = logging.getLogger(__name__)

TP_DEPARTMENT = "Town Planning (Scrutiny)"
ESTATES_DEPARTMENT = "Estates Services"
SCRUTINY_RATE = 0.004

APPLICATION_ID = "Application ID"
DATE_RECEIVED = "Date Received"
APPLICANT = "Applicant Name"
PLOT_NUMBER = "Plot Number"
DEPARTMENT = "Department"
CATEGORY = "Category"
DEVELOPMENT_TYPE = "Development Type"
DIMENSION = "Dimension/Qty"
ESTIMATED_COST = "Est. Cost (MK)"
CALCULATED_FEE = "Calculated Fee (MK)"
AMOUNT_RECEIVED = "Total Fee (MK)"  # Retained for compatibility with the existing sheet.
BALANCE = "Balance (MK)"
WORKFLOW = "Workflow"
COMPLETED_STEPS = "Completed Steps"

COLUMNS = [
    APPLICATION_ID,
    DATE_RECEIVED,
    APPLICANT,
    PLOT_NUMBER,
    DEPARTMENT,
    CATEGORY,
    DEVELOPMENT_TYPE,
    DIMENSION,
    ESTIMATED_COST,
    CALCULATED_FEE,
    AMOUNT_RECEIVED,
    BALANCE,
    WORKFLOW,
    COMPLETED_STEPS,
]

NUMERIC_COLUMNS = {
    DIMENSION,
    ESTIMATED_COST,
    CALCULATED_FEE,
    AMOUNT_RECEIVED,
    BALANCE,
}


# Keep financial policy in data, not in UI conditionals.  Update these rates only
# after the council has approved the new tariff schedule.
BCC_RATES: dict[str, dict[str, dict[str, Any]]] = {
    "Residential": {
        "High Density": {"rate": 170000.00, "unit": "sqm"},
        "Medium Density": {"rate": 190000.00, "unit": "sqm"},
        "Low Density": {"rate": 220000.00, "unit": "sqm"},
        "Multi-Units (Medium and Low)": {"rate": 350000.00, "unit": "sqm"},
    },
    "Institutional": {
        "Churches, Mosques and Schools": {"rate": 420000.00, "unit": "sqm"},
    },
    "Industrial Development": {
        "Factory / Warehouses": {"rate": 525000.00, "unit": "sqm"},
    },
    "Office/Commercial Development": {
        "Single Storey": {"rate": 525000.00, "unit": "sqm"},
        "Multi-Storey": {"rate": 650000.00, "unit": "sqm"},
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
        "One Surface Car Parking Space": {"rate": 280000.00, "unit": "fixed_fee"},
        "Application in Principle (Outline Application)": {"rate": 750000.00, "unit": "fixed_fee"},
        "Change of Use": {"rate": 750000.00, "unit": "fixed_fee"},
        "Subdivision per Plot Created": {"rate": 150000.00, "unit": "fixed_fee"},
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

ESTATES_FEES: dict[str, dict[str, dict[str, Any]]] = {
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
        "Commercial by Market Value": {"rate": 0.075, "unit": "market_value"},
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
        "Extra Beacon": {"rate": 40000.00, "unit": "qty_based"},
        "Survey of Plot": {"rate": 200000.00, "unit": "fixed_fee"},
        "Survey Drawing & Computation Fees (0.036 ha)": {"rate": 150000.00, "unit": "qty_based"},
    },
}

TP_COST_BASED_CATEGORIES = {
    "Residential",
    "Institutional",
    "Industrial Development",
    "Office/Commercial Development",
    "Fences",
}

TP_ADD_ONS = (
    ("Advertising", "Application Fee", "Application fee"),
    ("Septic Tank", "Septic Tank Installation", "Septic tank fee"),
    ("Miscellaneous", "Site Plan Certification", "Site plan certification"),
    ("Miscellaneous", "One Surface Car Parking Space", "Surface car parking"),
    ("Miscellaneous", "Sewer Application Fees", "Sewer application fee"),
)

WORKFLOWS: dict[str, list[str]] = {
    "Lease Application": [
        "Confirmation of Estate",
        "Confirmation of Details",
        "City Rates Clearance",
        "Lease Application Fee Paid",
        "Application Form Submitted",
        "Property Inspection Completed",
        "Surveying Executed",
        "Development Charges Cleared",
        "Legal Costs Cleared",
        "Final Signing by Director of Town Planning and Estates Services",
    ],
    "Change of Ownership": [
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
        "Final CEO Signature",
    ],
    "Plan Approval": [
        "Submission of Plans",
        "Payment of Scrutiny Fees",
        "Technical Screening of Plans",
        "Town Planning Committee Screening and Approval of Plans",
        "Preparation of Grant Permissions",
        "Stamping of the Approved Plans",
        "Signing of Plans and Grant Permissions by the Director of Town Planning and Estates Services",
    ],
}


def setup_page() -> None:
    st.markdown(
        """
        <style>
        .stApp { background: #f4f6fa; }
        [data-testid="stSidebar"] { background: #1e65b5; }
        [data-testid="stSidebar"] * { color: #ffffff; }
        [data-testid="stSidebar"] div.stButton > button {
            min-height: 2.55rem; color: #ffffff !important; background: #174f8d !important;
            border: 1px solid rgba(255, 255, 255, .62) !important; border-radius: 7px;
            font-weight: 600;
        }
        [data-testid="stSidebar"] div.stButton > button:hover,
        [data-testid="stSidebar"] div.stButton > button:active,
        [data-testid="stSidebar"] div.stButton > button:focus {
            color: #ffffff !important; background: #123b69 !important;
            border-color: #c49a2a !important; box-shadow: none !important;
        }
        [data-testid="stSidebar"] div.stButton > button:focus-visible {
            outline: 2px solid #c49a2a !important; outline-offset: 2px;
        }
        [data-testid="stSidebar"] div.stButton > button * { color: #ffffff !important; }
        .portal-header {
            background: #1e65b5; border-bottom: 4px solid #c49a2a;
            border-radius: 10px; color: white; padding: 1.4rem 1.7rem; margin-bottom: 1.4rem;
        }
        .portal-header h1 { color: white; font-size: 1.45rem; margin: 0 0 .3rem; }
        .portal-header p { margin: 0; color: #dbe8f7; }
        div[data-testid="stMetric"] {
            background: white; border: 1px solid #dde3ee; border-radius: 10px; padding: .85rem;
        }
        .money-card {
            width: 100%; min-width: 0; box-sizing: border-box; background: #ffffff;
            min-height: 5.35rem; border: 1px solid #dde3ee; border-radius: 10px;
            padding: .78rem .9rem; margin: .55rem 0;
        }
        .money-card--emphasis { background: #1e65b5; border-color: #1e65b5; }
        .money-card-label {
            color: #5d6b82; font-size: .68rem; font-weight: 700; letter-spacing: .06em;
            line-height: 1.25; text-transform: uppercase;
        }
        .money-card-value {
            color: #172b4d; font-size: clamp(.82rem, 1.6vw, 1.15rem); font-weight: 700;
            font-variant-numeric: tabular-nums; line-height: 1.28; margin-top: .22rem;
            overflow-wrap: anywhere; word-break: break-word; white-space: normal;
        }
        .money-card--emphasis .money-card-label { color: #dbe8f7; }
        .money-card--emphasis .money-card-value { color: #ffffff; font-size: clamp(.92rem, 1.9vw, 1.3rem); }
        [data-testid="stNumberInput"] input {
            font-size: clamp(.82rem, 1.4vw, 1rem) !important; font-variant-numeric: tabular-nums;
        }
        @media (max-width: 900px) {
            .portal-header { padding: 1rem 1.1rem; }
            .portal-header h1 { font-size: 1.18rem; }
            .money-card { padding: .68rem .75rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def empty_registry() -> pd.DataFrame:
    """Return an empty frame with the complete current schema."""
    return pd.DataFrame(columns=COLUMNS)


def parse_registry_date(value: Any) -> pd.Timestamp | pd.NaT:
    """Parse ISO dates and legacy DD/MM/YYYY dates without locale ambiguity."""
    if pd.isna(value) or str(value).strip() in {"", "nan", "NaT", "N/A"}:
        return pd.NaT

    if isinstance(value, (int, float)) and 20_000 < value < 60_000:
        # Excel serial date. GSheets normally returns a datetime, but this makes
        # the migration robust if an exported numeric date is encountered.
        return pd.to_datetime(value, unit="D", origin="1899-12-30", errors="coerce")

    text = str(value).strip()
    if re.fullmatch(r"\d{1,2}/\d{1,2}/\d{4}", text):
        return pd.to_datetime(text, format="%d/%m/%Y", errors="coerce")
    return pd.to_datetime(value, errors="coerce")


def normalise_registry(raw: pd.DataFrame | None) -> pd.DataFrame:
    """Migrate legacy sheet data into the in-app schema without changing labels."""
    if raw is None or raw.empty:
        return empty_registry()

    df = raw.copy()
    original_columns = set(df.columns)
    for column in COLUMNS:
        if column not in df.columns:
            df[column] = 0.0 if column in NUMERIC_COLUMNS else ""

    # Older sheets have only Total Fee. Treat it as amount received and use it as
    # the best available calculated fee until a record is amended in the portal.
    if CALCULATED_FEE not in original_columns:
        df[CALCULATED_FEE] = df[AMOUNT_RECEIVED]
    if BALANCE not in original_columns:
        df[BALANCE] = 0.0

    for column in NUMERIC_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0.0)

    for column in COLUMNS:
        if column not in NUMERIC_COLUMNS and column != DATE_RECEIVED:
            df[column] = df[column].fillna("").astype(str).str.strip()

    blank_departments = df[DEPARTMENT].isin({"", "N/A", "nan", "None"})
    df.loc[blank_departments, DEPARTMENT] = TP_DEPARTMENT
    df[DATE_RECEIVED] = df[DATE_RECEIVED].apply(parse_registry_date)
    return df


def prepare_for_storage(df: pd.DataFrame) -> pd.DataFrame:
    """Serialise data in a stable, spreadsheet-friendly format."""
    output = normalise_registry(df)
    output[DATE_RECEIVED] = output[DATE_RECEIVED].apply(
        lambda value: value.strftime("%Y-%m-%d") if pd.notna(value) else ""
    )
    for column in NUMERIC_COLUMNS:
        output[column] = output[column].round(2)

    # Preserve any manually managed columns that already exist in the sheet.
    extra_columns = [column for column in df.columns if column not in COLUMNS]
    return output[COLUMNS + extra_columns]


conn = st.connection("gsheets", type=GSheetsConnection)


def read_registry_uncached() -> tuple[pd.DataFrame, str | None]:
    try:
        return normalise_registry(conn.read(ttl=0)), None
    except Exception:
        LOGGER.exception("Registry read failed")
        return empty_registry(), "Unable to read the registry. Check the Google Sheets connection configuration."


@st.cache_data(ttl=15, show_spinner=False)
def load_registry() -> tuple[pd.DataFrame, str | None]:
    """Cache read-only views briefly; every write still performs a fresh read."""
    return read_registry_uncached()


def write_registry(df: pd.DataFrame) -> None:
    conn.update(data=prepare_for_storage(df))
    load_registry.clear()


def money(value: float) -> str:
    return f"MK {value:,.2f}"


def render_value_card(label: str, value: str, *, emphasis: bool = False) -> None:
    """Render a responsive summary value that wraps instead of becoming an ellipsis."""
    classes = "money-card money-card--emphasis" if emphasis else "money-card"
    st.markdown(
        f'<section class="{classes}"><div class="money-card-label">{html.escape(label)}</div>'
        f'<div class="money-card-value">{html.escape(value)}</div></section>',
        unsafe_allow_html=True,
    )


def render_money_card(label: str, value: float, *, emphasis: bool = False) -> None:
    """Render a responsive currency value that wraps instead of becoming an ellipsis."""
    render_value_card(label, money(value), emphasis=emphasis)


def rate_key(category: str, development_type: str) -> str:
    return f"{category}::{development_type}"


def get_rate_table(department: str) -> Mapping[str, Mapping[str, Mapping[str, Any]]]:
    return BCC_RATES if department == TP_DEPARTMENT else ESTATES_FEES


def sync_rate_selection(
    table: Mapping[str, Mapping[str, Mapping[str, Any]]],
    category_key: str,
    type_key: str,
) -> tuple[str, str, Mapping[str, Any]]:
    """Keep dependent selectboxes valid after a department/category change."""
    categories = list(table)
    if st.session_state.get(category_key) not in categories:
        st.session_state[category_key] = categories[0]
    category = st.selectbox("Category", categories, key=category_key)

    development_types = list(table[category])
    if st.session_state.get(type_key) not in development_types:
        st.session_state[type_key] = development_types[0]
    development_type = st.selectbox("Development type", development_types, key=type_key)
    return category, development_type, table[category][development_type]


def calculate_base_fee(
    department: str,
    category: str,
    rate_info: Mapping[str, Any],
    quantity: float,
    premium_per_sqm: float = 0.0,
) -> tuple[float, float]:
    """Return (estimated_cost_or_valuation, base_fee) for a validated input."""
    quantity = max(float(quantity), 0.0)
    premium_per_sqm = max(float(premium_per_sqm), 0.0)
    rate = float(rate_info["rate"])
    unit = str(rate_info["unit"])

    if department == TP_DEPARTMENT:
        if category in TP_COST_BASED_CATEGORIES:
            estimated_cost = quantity * rate
            return estimated_cost, estimated_cost * SCRUTINY_RATE
        if unit == "percentage_of_final_cost":
            return quantity, quantity * rate
        return 0.0, quantity * rate

    if unit == "market_value":
        valuation = premium_per_sqm * quantity
        return valuation, valuation * rate
    return 0.0, quantity * rate


def render_quantity_input(
    rate_info: Mapping[str, Any],
    key_prefix: str,
    *,
    allow_geometry: bool,
) -> tuple[float, float]:
    """Collect the input required by a rate unit and return quantity, premium."""
    unit = str(rate_info["unit"])
    premium = 0.0

    if unit == "sqm":
        if allow_geometry:
            method = st.radio(
                "Area entry method",
                ("Enter total area", "Calculate from a shape"),
                horizontal=True,
                key=f"{key_prefix}_area_method",
            )
            if method == "Calculate from a shape":
                shape = st.selectbox(
                    "Shape", ("Rectangle", "Triangle", "Trapezium", "Circle", "Semicircle"), key=f"{key_prefix}_shape"
                )
                if shape == "Rectangle":
                    length = st.number_input("Length (m)", min_value=0.0, value=20.0, step=0.5, key=f"{key_prefix}_length")
                    width = st.number_input("Width (m)", min_value=0.0, value=15.0, step=0.5, key=f"{key_prefix}_width")
                    quantity = length * width
                elif shape == "Triangle":
                    base = st.number_input("Base (m)", min_value=0.0, value=15.0, step=0.5, key=f"{key_prefix}_base")
                    height = st.number_input("Perpendicular height (m)", min_value=0.0, value=10.0, step=0.5, key=f"{key_prefix}_height")
                    quantity = 0.5 * base * height
                elif shape == "Trapezium":
                    side_a = st.number_input("Parallel side A (m)", min_value=0.0, value=12.0, step=0.5, key=f"{key_prefix}_side_a")
                    side_b = st.number_input("Parallel side B (m)", min_value=0.0, value=18.0, step=0.5, key=f"{key_prefix}_side_b")
                    height = st.number_input("Height (m)", min_value=0.0, value=8.0, step=0.5, key=f"{key_prefix}_trap_height")
                    quantity = 0.5 * (side_a + side_b) * height
                else:
                    radius = st.number_input("Radius (m)", min_value=0.0, value=7.0, step=0.5, key=f"{key_prefix}_radius")
                    quantity = math.pi * radius**2
                    if shape == "Semicircle":
                        quantity *= 0.5
                st.info(f"Calculated area: {quantity:,.2f} sqm")
                return quantity, premium

        quantity = st.number_input(
            "Built-up area (sqm)", min_value=0.0, value=100.0, step=10.0, key=f"{key_prefix}_sqm"
        )
    elif unit == "linear_meters":
        quantity = st.number_input(
            "Fence length (metres)", min_value=0.0, value=50.0, step=5.0, key=f"{key_prefix}_linear"
        )
    elif unit == "percentage_of_final_cost":
        quantity = st.number_input(
            "Declared final structural cost (MK)", min_value=0.0, value=5_000_000.0, step=100_000.0, key=f"{key_prefix}_cost"
        )
    elif unit == "market_value":
        premium = st.number_input(
            "Premium value per sqm (MK)", min_value=0.0, value=1_000_000.0, step=50_000.0, key=f"{key_prefix}_premium"
        )
        quantity = st.number_input(
            "Plot area (sqm)", min_value=0.0, value=1_000.0, step=10.0, key=f"{key_prefix}_market_area"
        )
    else:
        label = "Number of chargeable units" if unit == "qty_based" else "Number of items"
        quantity = st.number_input(label, min_value=1.0, value=1.0, step=1.0, key=f"{key_prefix}_quantity")

    return quantity, premium


def available_tp_add_ons(category: str, development_type: str) -> dict[str, tuple[str, float]]:
    """Exclude the selected base service so it cannot be charged twice."""
    selected_id = rate_key(category, development_type)
    choices: dict[str, tuple[str, float]] = {}
    for add_on_category, add_on_type, label in TP_ADD_ONS:
        add_on_id = rate_key(add_on_category, add_on_type)
        if add_on_id == selected_id:
            continue
        amount = float(BCC_RATES[add_on_category][add_on_type]["rate"])
        choices[add_on_id] = (f"{label} ({money(amount)})", amount)
    return choices


def render_tp_add_ons(category: str, development_type: str, key: str) -> tuple[list[str], float]:
    choices = available_tp_add_ons(category, development_type)
    previous = st.session_state.get(key, [])
    valid_previous = [option for option in previous if option in choices]
    if previous != valid_previous:
        st.session_state[key] = valid_previous

    selected = st.multiselect(
        "Additional fees to include",
        options=list(choices),
        format_func=lambda option: choices[option][0],
        key=key,
        help="Select only fees that form part of this same assessment or receipt.",
    )
    return selected, sum(choices[option][1] for option in selected)


def rate_description(department: str, category: str, rate_info: Mapping[str, Any]) -> str:
    rate = float(rate_info["rate"])
    unit = str(rate_info["unit"])
    if department == TP_DEPARTMENT and category in TP_COST_BASED_CATEGORIES:
        return f"Development rate: {money(rate)} per unit; scrutiny charge: {SCRUTINY_RATE:.1%} of estimated cost"
    if unit == "percentage_of_final_cost":
        return f"Charge: {rate:.2%} of declared final structural cost"
    if unit == "market_value":
        return f"Charge: {rate:.2%} of premium valuation"
    suffix = "chargeable unit" if unit == "qty_based" else "item"
    return f"Rate: {money(rate)} per {suffix}"


def require_authentication() -> None:
    if st.session_state.get("authenticated", False):
        return

    _, login_column, _ = st.columns((1, 1.4, 1))
    with login_column:
        st.title("Registry sign in")
        st.caption("Authorised Town Planning and Estates staff only")
        with st.form("authentication_form"):
            candidate = st.text_input("Internal access password", type="password")
            submitted = st.form_submit_button("Sign in", use_container_width=True)
        if submitted:
            try:
                expected = str(st.secrets["auth"]["password"])
            except (KeyError, FileNotFoundError):
                expected = ""
            if not expected:
                st.error("Authentication is not configured. Contact the system administrator.")
            elif candidate and hmac.compare_digest(candidate, expected):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("The password is not valid.")
    st.stop()


def render_header() -> None:
    st.markdown(
        """
        <section class="portal-header">
            <h1>Department of Town Planning and Estates Services</h1>
            <p>Charges review 2026/2027 · Effective rates registry</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_calculator() -> None:
    st.header("Fee calculator")
    department = st.radio(
        "Department", (TP_DEPARTMENT, ESTATES_DEPARTMENT), horizontal=True, key="calculator_department"
    )
    table = get_rate_table(department)
    left, right = st.columns((1.05, 0.95), gap="large")

    with left:
        category, development_type, rate_info = sync_rate_selection(
            table, "calculator_category", "calculator_development_type"
        )
        st.caption(rate_description(department, category, rate_info))
        quantity, premium = render_quantity_input(rate_info, "calculator", allow_geometry=True)
        add_on_total = 0.0
        selected_add_ons: list[str] = []
        if department == TP_DEPARTMENT:
            st.subheader("Optional combined fees")
            selected_add_ons, add_on_total = render_tp_add_ons(
                category, development_type, "calculator_add_ons"
            )

    estimated_cost, base_fee = calculate_base_fee(department, category, rate_info, quantity, premium)
    total_due = base_fee + add_on_total

    with right:
        st.subheader("Assessment")
        st.write(f"**Category:** {category}")
        st.write(f"**Development type:** {development_type}")
        if estimated_cost:
            render_money_card("Estimated cost / valuation", estimated_cost)
        render_money_card("Base fee", base_fee)
        render_money_card("Additional fees", add_on_total)
        render_money_card("Total fee payable", total_due, emphasis=True)
        if selected_add_ons:
            st.caption(f"Includes {len(selected_add_ons)} selected additional fee(s).")


def request_intake_form_reset() -> None:
    """Request a reset from the button callback without touching live widgets."""
    st.session_state["intake_reset_requested"] = True


def apply_pending_intake_form_reset() -> bool:
    """Clear all intake widget state before this run creates those widgets."""
    if not st.session_state.pop("intake_reset_requested", False):
        return False

    for key in list(st.session_state):
        if key.startswith("intake_") and key != "intake_success_message":
            del st.session_state[key]
    return True


def render_intake() -> None:
    was_reset = apply_pending_intake_form_reset()
    st.header("New application intake")
    st.caption("Record the assessed charge and the actual amount received separately. This supports partial payments.")
    success_message = st.session_state.pop("intake_success_message", None)
    if success_message:
        st.success(success_message)
    elif was_reset:
        st.success("The intake form has been cleared.")

    department = st.radio(
        "Department", (TP_DEPARTMENT, ESTATES_DEPARTMENT), horizontal=True, key="intake_department"
    )
    table = get_rate_table(department)
    first_column, second_column = st.columns(2, gap="large")
    with first_column:
        application_id = st.text_input(
            "Application / file ID", placeholder="e.g. BCC/TP/2026/250", key="intake_application_id"
        ).strip().upper()
        applicant_name = st.text_input("Applicant name / developer entity", key="intake_applicant").strip()
        received_date = st.date_input("Date received", value=date.today(), key="intake_received_date")
    with second_column:
        plot_number = st.text_input("Plot number / parcel ID", key="intake_plot").strip()
        category, development_type, rate_info = sync_rate_selection(
            table, "intake_category", "intake_development_type"
        )

    st.subheader("Assessment and receipt")
    assessment_column, receipt_column = st.columns(2, gap="large")
    with assessment_column:
        st.caption(rate_description(department, category, rate_info))
        quantity, premium = render_quantity_input(rate_info, "intake_measurement", allow_geometry=False)
        add_on_total = 0.0
        selected_add_ons: list[str] = []
        if department == TP_DEPARTMENT:
            selected_add_ons, add_on_total = render_tp_add_ons(category, development_type, "intake_add_ons")

    estimated_cost, base_fee = calculate_base_fee(department, category, rate_info, quantity, premium)
    assessed_total = base_fee + add_on_total
    with receipt_column:
        render_money_card("Assessed fee due", assessed_total, emphasis=True)
        amount_received = st.number_input(
            "Amount received on receipt (MK)", min_value=0.0, value=0.0, step=5_000.0, key="intake_received_amount"
        )
        render_money_card("Amount received", amount_received)
        balance = assessed_total - amount_received
        if balance > 0:
            st.warning(f"Outstanding balance: {money(balance)}")
        elif balance < 0:
            st.info(f"Overpayment to review: {money(abs(balance))}")
        else:
            st.success("Receipt matches the calculated fee.")
        if estimated_cost:
            st.caption(f"Estimated cost / valuation: {money(estimated_cost)}")

    action_column, clear_column = st.columns(2)
    submit = action_column.button("Add application to registry", type="primary", use_container_width=True)
    clear_column.button("Clear form", use_container_width=True, on_click=request_intake_form_reset)

    if not submit:
        return

    errors: list[str] = []
    if not application_id:
        errors.append("Application / file ID is required.")
    if not applicant_name:
        errors.append("Applicant name is required.")
    if not plot_number:
        errors.append("Plot number / parcel ID is required.")
    if amount_received <= 0:
        errors.append("Amount received must be greater than zero.")
    if errors:
        for error in errors:
            st.error(error)
        return

    fresh_registry, read_error = read_registry_uncached()
    if read_error:
        st.error(read_error)
        return
    existing_ids = fresh_registry[APPLICATION_ID].str.upper()
    if application_id in set(existing_ids):
        st.error("That application / file ID already exists. Use a unique ID or update the existing record.")
        return

    new_row = {
        APPLICATION_ID: application_id,
        DATE_RECEIVED: pd.Timestamp(received_date),
        APPLICANT: applicant_name,
        PLOT_NUMBER: plot_number,
        DEPARTMENT: department,
        CATEGORY: category,
        DEVELOPMENT_TYPE: development_type,
        DIMENSION: round(float(quantity), 2),
        ESTIMATED_COST: round(estimated_cost, 2),
        CALCULATED_FEE: round(assessed_total, 2),
        AMOUNT_RECEIVED: round(float(amount_received), 2),
        BALANCE: round(balance, 2),
        WORKFLOW: "",
        COMPLETED_STEPS: "[]",
    }
    try:
        write_registry(pd.concat((fresh_registry, pd.DataFrame([new_row])), ignore_index=True))
    except Exception:
        LOGGER.exception("Registry write failed during intake")
        st.error("The registry could not be updated. No confirmation was received from Google Sheets.")
        return

    request_intake_form_reset()
    st.session_state["intake_success_message"] = f"Application {application_id} was added to the registry."
    st.rerun()


def period_details(series: pd.Series, grouping: str) -> tuple[pd.Series, pd.Series]:
    frequencies = {"Weekly": "W-SUN", "Monthly": "M", "Quarterly": "Q"}
    period_start = series.dt.to_period(frequencies[grouping]).dt.start_time
    if grouping == "Weekly":
        labels = period_start.dt.strftime("Week of %d %b %Y")
    elif grouping == "Monthly":
        labels = period_start.dt.strftime("%b %Y")
    else:
        labels = series.dt.to_period("Q").astype(str)
    return period_start, labels


def render_analytics(df: pd.DataFrame) -> None:
    st.header("Submission analytics")
    department_filter = st.radio(
        "View data for", ("All departments", TP_DEPARTMENT, ESTATES_DEPARTMENT), horizontal=True, key="analytics_department"
    )
    filtered = df.copy()
    if department_filter != "All departments":
        filtered = filtered.loc[filtered[DEPARTMENT] == department_filter].copy()

    if filtered.empty:
        st.info("No applications match this selection.")
        return

    top_left, top_right = st.columns(2, gap="medium")
    with top_left:
        render_value_card("Applications", f"{len(filtered):,}")
    with top_right:
        render_money_card("Assessed fees", float(filtered[CALCULATED_FEE].sum()))
    bottom_left, bottom_right = st.columns(2, gap="medium")
    with bottom_left:
        render_money_card("Amount received", float(filtered[AMOUNT_RECEIVED].sum()))
    with bottom_right:
        render_money_card("Outstanding balance", float(filtered[BALANCE].clip(lower=0).sum()))

    chart_data = filtered.dropna(subset=[DATE_RECEIVED]).copy()
    if not chart_data.empty:
        st.subheader("Submission trends")
        grouping = st.radio("Group by", ("Weekly", "Monthly", "Quarterly"), horizontal=True, key="analytics_grouping")
        chart_data["Period start"], chart_data["Period"] = period_details(chart_data[DATE_RECEIVED], grouping)
        chart_data[CATEGORY] = chart_data[CATEGORY].replace("", "Uncategorised")
        periods = (
            chart_data[["Period", "Period start"]]
            .drop_duplicates()
            .sort_values("Period start")["Period"]
            .tolist()
        )
        volume = (
            chart_data.groupby(["Period", CATEGORY], as_index=False)
            .size()
            .rename(columns={"size": "Submissions"})
        )
        chart_left, chart_right = st.columns(2, gap="large")
        with chart_left:
            trend = px.bar(
                volume,
                x="Period",
                y="Submissions",
                color=CATEGORY,
                barmode="stack",
                category_orders={"Period": periods},
                title=f"Application volume — {grouping.lower()} view",
            )
            trend.update_layout(legend_title_text="Category", margin=dict(l=10, r=10, t=50, b=10))
            st.plotly_chart(trend, use_container_width=True)
        with chart_right:
            share = chart_data.groupby(CATEGORY, as_index=False).size().rename(columns={"size": "Applications"})
            pie = px.pie(share, names=CATEGORY, values="Applications", hole=0.35, title="Share by category")
            pie.update_layout(margin=dict(l=10, r=10, t=50, b=10))
            st.plotly_chart(pie, use_container_width=True)

        st.subheader("Period matrices")
        volume_matrix = pd.crosstab(chart_data[CATEGORY], chart_data["Period"]).reindex(columns=periods, fill_value=0)
        revenue_matrix = (
            chart_data.pivot_table(
                index=CATEGORY, columns="Period", values=AMOUNT_RECEIVED, aggfunc="sum", fill_value=0
            ).reindex(columns=periods, fill_value=0)
        )
        for matrix in (volume_matrix, revenue_matrix):
            matrix["Total"] = matrix.sum(axis=1)
            matrix.loc["Grand Total"] = matrix.sum(axis=0)
        matrix_left, matrix_right = st.columns(2, gap="large")
        with matrix_left:
            st.caption("Application volume")
            st.dataframe(volume_matrix.style.format("{:,.0f}"), use_container_width=True)
        with matrix_right:
            st.caption("Amount received (MK)")
            st.dataframe(revenue_matrix.style.format("{:,.2f}"), use_container_width=True)
    else:
        st.info("No valid received dates are available for trend analysis.")

    st.subheader("Application registry")
    query = st.text_input("Search registry", placeholder="File ID, applicant, plot, category …", key="analytics_search")
    display = filtered.copy()
    if query.strip():
        searchable = display[[APPLICATION_ID, APPLICANT, PLOT_NUMBER, CATEGORY, DEVELOPMENT_TYPE]].fillna("").astype(str)
        matches = searchable.apply(lambda column: column.str.contains(query.strip(), case=False, regex=False)).any(axis=1)
        display = display.loc[matches].copy()
    display = display.sort_values(DATE_RECEIVED, ascending=False, na_position="last")
    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
        column_config={
            DATE_RECEIVED: st.column_config.DateColumn("Date received", format="DD/MM/YYYY"),
            ESTIMATED_COST: st.column_config.NumberColumn(format="MK %.2f"),
            CALCULATED_FEE: st.column_config.NumberColumn(format="MK %.2f"),
            AMOUNT_RECEIVED: st.column_config.NumberColumn("Amount received", format="MK %.2f"),
            BALANCE: st.column_config.NumberColumn(format="MK %.2f"),
        },
    )
    export = prepare_for_storage(display).to_csv(index=False).encode("utf-8")
    st.download_button("Download filtered registry (CSV)", export, "bcc_registry.csv", "text/csv")


def decode_completed_steps(value: Any) -> set[str]:
    """Read the current JSON format and legacy comma-separated cells safely."""
    text = str(value).strip()
    if not text or text.lower() in {"nan", "n/a", "none"}:
        return set()
    try:
        decoded = json.loads(text)
        if isinstance(decoded, list):
            return {str(step) for step in decoded}
    except json.JSONDecodeError:
        pass
    return {step.strip() for step in text.split(",") if step.strip()}


def tracker_key(application_id: str, workflow: str, step_number: int) -> str:
    digest = hashlib.sha1(f"{application_id}|{workflow}|{step_number}".encode()).hexdigest()[:12]
    return f"tracker_{digest}"


def render_tracker(df: pd.DataFrame) -> None:
    st.header("Process tracking")
    if df.empty:
        st.info("No records are available in the registry to track.")
        return

    options = [
        f"{row[APPLICATION_ID]} | Plot: {row[PLOT_NUMBER]} | {row[APPLICANT]}"
        for _, row in df.sort_values(APPLICATION_ID).iterrows()
    ]
    selection = st.selectbox(
        "Find an application", options, index=None, placeholder="Type an application ID, plot number, or applicant name"
    )
    if not selection:
        return

    selected_id = selection.split(" | ", 1)[0]
    record_matches = df.index[df[APPLICATION_ID].str.upper() == selected_id.upper()]
    if record_matches.empty:
        st.warning("The selected record could not be found. Refresh the data and try again.")
        return
    record = df.loc[record_matches[0]]
    st.caption(f"{record[APPLICANT]} · Plot {record[PLOT_NUMBER]}")

    saved_workflow = record[WORKFLOW] if record[WORKFLOW] in WORKFLOWS else "Lease Application"
    workflow = st.radio(
        "Workflow",
        list(WORKFLOWS),
        index=list(WORKFLOWS).index(saved_workflow),
        horizontal=True,
        key=f"workflow_{hashlib.sha1(selected_id.encode()).hexdigest()[:10]}",
    )
    steps = WORKFLOWS[workflow]
    saved_steps = decode_completed_steps(record[COMPLETED_STEPS]) if record[WORKFLOW] == workflow else set()
    completed = sum(step in saved_steps for step in steps)
    st.progress(completed / len(steps), text=f"{completed} of {len(steps)} steps completed")

    form_key = f"tracker_form_{hashlib.sha1(f'{selected_id}|{workflow}'.encode()).hexdigest()[:12]}"
    with st.form(form_key):
        checked_steps = [
            step
            for number, step in enumerate(steps, start=1)
            if st.checkbox(
                f"Step {number}: {step}",
                value=step in saved_steps,
                key=tracker_key(selected_id, workflow, number),
            )
        ]
        save = st.form_submit_button("Save workflow progress", type="primary", use_container_width=True)

    if not save:
        return

    fresh_registry, read_error = read_registry_uncached()
    if read_error:
        st.error(read_error)
        return
    fresh_matches = fresh_registry.index[fresh_registry[APPLICATION_ID].str.upper() == selected_id.upper()]
    if fresh_matches.empty:
        st.error("The record was removed before the update could be saved.")
        return

    fresh_index = fresh_matches[0]
    fresh_registry.at[fresh_index, WORKFLOW] = workflow
    fresh_registry.at[fresh_index, COMPLETED_STEPS] = json.dumps(checked_steps, ensure_ascii=False)
    try:
        write_registry(fresh_registry)
    except Exception:
        LOGGER.exception("Registry write failed during workflow update")
        st.error("The workflow update could not be saved. Please retry after refreshing data.")
        return
    st.success("Workflow progress was saved.")


def render_sidebar() -> tuple[str, bool, int]:
    st.sidebar.title("BCC portal")
    page_labels = {
        "Fee calculator": "calculator",
        "New application intake": "intake",
        "Submission analytics": "analytics",
        "Process tracking": "tracker",
    }
    page_label = st.sidebar.radio("Navigate to", list(page_labels), key="navigation")
    st.sidebar.divider()
    auto_refresh = st.sidebar.toggle("Auto-refresh analytics", value=False)
    refresh_seconds = 30
    if auto_refresh:
        refresh_seconds = st.sidebar.slider("Refresh interval (seconds)", 15, 120, 30, step=15)
    if st.sidebar.button("Refresh data now", use_container_width=True):
        load_registry.clear()
        st.rerun()
    st.sidebar.divider()
    if st.sidebar.button("Sign out", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    st.sidebar.caption("Blantyre City Council · Town Planning & Estates")
    return page_labels[page_label], auto_refresh, refresh_seconds


def render_auto_refreshing_analytics(refresh_seconds: int) -> None:
    """Use Streamlit fragments when installed; never block the server with sleep."""
    fragment = getattr(st, "fragment", None)
    if fragment is None:
        st.info("Automatic refresh requires Streamlit 1.37 or later. Use 'Refresh data now' in the sidebar.")
        registry, error = load_registry()
        if error:
            st.error(error)
        render_analytics(registry)
        return

    @fragment(run_every=f"{refresh_seconds}s")
    def analytics_fragment() -> None:
        registry, error = load_registry()
        if error:
            st.error(error)
        render_analytics(registry)

    analytics_fragment()


def main() -> None:
    setup_page()
    require_authentication()
    render_header()
    current_page, auto_refresh, refresh_seconds = render_sidebar()

    if current_page == "calculator":
        render_calculator()
    elif current_page == "intake":
        render_intake()
    elif current_page == "analytics" and auto_refresh:
        render_auto_refreshing_analytics(refresh_seconds)
    else:
        registry, error = load_registry()
        if error:
            st.error(error)
        if current_page == "analytics":
            render_analytics(registry)
        elif current_page == "tracker":
            render_tracker(registry)


if __name__ == "__main__":
    main()
