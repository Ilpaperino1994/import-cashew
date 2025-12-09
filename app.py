import streamlit as st
import copy
from models import DEFAULT_CASHEW_STRUCTURE
from ui.step1_upload import render_step1
from ui.step2_categories import render_step2
from ui.step3_mapping import render_step3
from ui.step4_export import render_step4

# --- CONFIG & STYLE ---
st.set_page_config(page_title="Wallet to Cashew Migrator", page_icon="🥥", layout="wide")

# CSS Avanzato per UI Moderna e Responsive (Stile Cashew/Material)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

    :root {
        --primary-color: #4CAF50;
        --primary-hover: #45a049;
        --bg-color: #121212;
        --card-bg: #1E1E1E;
        --text-color: #E0E0E0;
        --border-color: #333;
    }

    /* Global Typography */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Wizard Steps Container */
    .wizard-container {
        display: flex;
        justify-content: space-between;
        margin-bottom: 2rem;
        padding: 0;
        gap: 10px;
    }

    .wizard-step {
        flex: 1;
        text-align: center;
        padding: 12px;
        border-radius: 12px;
        background-color: var(--card-bg);
        color: var(--text-color);
        opacity: 0.6;
        font-weight: 600;
        border: 1px solid var(--border-color);
        transition: all 0.3s ease;
        font-size: 0.9rem;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
    }

    .wizard-active {
        background-color: var(--primary-color);
        color: white;
        opacity: 1;
        border-color: var(--primary-color);
        box-shadow: 0 4px 10px rgba(76, 175, 80, 0.3);
    }

    /* Custom Cards for Content */
    .st-card {
        background-color: var(--card-bg);
        padding: 24px;
        border-radius: 16px;
        border: 1px solid var(--border-color);
        margin-bottom: 1rem;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }

    /* Streamlit Components Overrides */
    .stButton button {
        border-radius: 10px;
        font-weight: 600;
        transition: transform 0.1s;
    }
    .stButton button:active {
        transform: scale(0.98);
    }

    div[data-testid="stRadio"] > div {
        background-color: transparent;
    }

    /* Responsive tweaks */
    @media (max-width: 768px) {
        .wizard-step span {
            display: none; /* Hide text on mobile */
        }
        .wizard-step {
            padding: 10px;
        }
        .wizard-step::after {
            content: attr(data-icon);
            font-size: 1.2rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# --- STATE ---
if 'step' not in st.session_state: st.session_state.step = 1
if 'transactions' not in st.session_state: st.session_state.transactions = []
if 'mapping' not in st.session_state: st.session_state.mapping = {}
if 'accounts' not in st.session_state: st.session_state.accounts = {}
if 'cashew_struct' not in st.session_state: st.session_state.cashew_struct = copy.deepcopy(DEFAULT_CASHEW_STRUCTURE)
if 'selected_cat_editor' not in st.session_state: st.session_state.selected_cat_editor = list(st.session_state.cashew_struct.keys())[0]
if 'output_format' not in st.session_state: st.session_state.output_format = "SQL"

# --- HEADER ---
# Custom Title Area
st.markdown("""
<div style="text-align: center; margin-bottom: 30px;">
    <h1 style="margin-bottom: 0;">🥥 Wallet to Cashew</h1>
    <p style="opacity: 0.7;">Migrator Tool</p>
</div>
""", unsafe_allow_html=True)

# --- WIZARD NAVIGATION ---
steps = [
    {"label": "Import", "icon": "📂"},
    {"label": "Categorie", "icon": "🏷️"},
    {"label": "Mapping", "icon": "🤖"},
    {"label": "Export", "icon": "🚀"}
]

# Create HTML for Wizard to allow custom responsive behavior
wizard_html = '<div class="wizard-container">'
for i, s in enumerate(steps):
    active = "wizard-active" if st.session_state.step == i + 1 else ""
    # Remove indentation to avoid Markdown code block interpretation
    wizard_html += f'<div class="wizard-step {active}" data-icon="{s["icon"]}">{s["icon"]} <span>{s["label"]}</span></div>'
wizard_html += '</div>'
st.markdown(wizard_html, unsafe_allow_html=True)

# --- ROUTER ---
# Wrap content in a main container for spacing
with st.container():
    if st.session_state.step == 1:
        render_step1()
    elif st.session_state.step == 2:
        render_step2()
    elif st.session_state.step == 3:
        render_step3()
    elif st.session_state.step == 4:
        render_step4()

# Footer
st.markdown("""
<div style="text-align: center; margin-top: 50px; opacity: 0.3; font-size: 0.8rem;">
    Powered by Python & Streamlit
</div>
""", unsafe_allow_html=True)
