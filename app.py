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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    :root {
        /* Palette Cashew / Material Dark */
        --primary: #2ECC71;         /* Emerald Green */
        --primary-hover: #27AE60;
        --secondary: #34495E;
        --background: #121212;
        --surface: #1E1E1E;
        --surface-hover: #2C2C2C;
        --text-primary: #FFFFFF;
        --text-secondary: #B0BEC5;
        --border: #333333;
        --success: #00C853;
        --error: #FF5252;

        /* Effects */
        --shadow-card: 0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -1px rgba(0, 0, 0, 0.16);
        --shadow-hover: 0 10px 15px -3px rgba(0, 0, 0, 0.4), 0 4px 6px -2px rgba(0, 0, 0, 0.2);
        --glass: rgba(30, 30, 30, 0.7);
        --glass-border: rgba(255, 255, 255, 0.08);
        --radius: 16px;
        --transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    }

    /* Global Typography */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: var(--background);
        color: var(--text-primary);
    }

    h1, h2, h3 {
        color: var(--text-primary);
        font-weight: 700;
        letter-spacing: -0.02em;
    }

    p, small, span, label {
        color: var(--text-secondary);
    }

    /* Streamlit Containers Reset */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 5rem;
        max-width: 1600px; /* Limit on ultrawide but keep wide */
    }

    /* --- WIZARD STEPS --- */
    .wizard-container {
        display: flex;
        justify-content: center;
        margin-bottom: 3rem;
        padding: 0;
        gap: 1rem;
        flex-wrap: wrap;
    }

    .wizard-step {
        background-color: var(--surface);
        color: var(--text-secondary);
        padding: 0.8rem 1.5rem;
        border-radius: 50px; /* Pill shape */
        font-weight: 500;
        border: 1px solid var(--border);
        transition: var(--transition);
        display: flex;
        align-items: center;
        gap: 10px;
        cursor: default;
        font-size: 0.95rem;
    }

    .wizard-active {
        background-color: rgba(46, 204, 113, 0.15); /* Tinted background */
        color: var(--primary);
        border-color: var(--primary);
        box-shadow: 0 0 15px rgba(46, 204, 113, 0.2);
    }

    .wizard-step .icon {
        font-size: 1.2em;
    }

    /* --- CARDS & GLASSMORPHISM --- */
    .st-card {
        background-color: var(--surface);
        padding: 2rem;
        border-radius: var(--radius);
        border: 1px solid var(--border);
        box-shadow: var(--shadow-card);
        margin-bottom: 1.5rem;
        transition: var(--transition);
    }

    .st-card:hover {
        border-color: var(--glass-border);
        box-shadow: var(--shadow-hover);
    }

    /* Hero/Instruction Text */
    .hero-text {
        font-size: clamp(1.5rem, 4vw, 2.5rem);
        font-weight: 800;
        background: linear-gradient(90deg, #FFFFFF, #B0BEC5);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }

    /* --- STREAMLIT WIDGET OVERRIDES --- */

    /* Buttons */
    .stButton button {
        border-radius: 12px;
        font-weight: 600;
        padding: 0.6rem 1.2rem;
        border: none;
        transition: var(--transition);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-size: 0.85rem;
        width: 100%;
    }

    /* Primary Button */
    .stButton button[kind="primary"] {
        background: linear-gradient(135deg, var(--primary) 0%, var(--primary-hover) 100%);
        color: #000 !important; /* Contrast text on bright green */
        box-shadow: 0 4px 12px rgba(46, 204, 113, 0.3);
    }

    .stButton button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(46, 204, 113, 0.4);
    }

    /* Secondary Button (Default) */
    .stButton button[kind="secondary"] {
        background-color: var(--surface-hover);
        color: var(--text-primary);
        border: 1px solid var(--border);
    }

    .stButton button[kind="secondary"]:hover {
        border-color: var(--primary);
        color: var(--primary);
    }

    /* Inputs (Text, Number, Select) */
    div[data-baseweb="input"], div[data-baseweb="select"] > div {
        background-color: var(--background) !important;
        border-radius: 10px !important;
        border: 1px solid var(--border) !important;
        color: var(--text-primary) !important;
    }

    div[data-baseweb="select"] div[role="listbox"] {
        background-color: var(--surface) !important;
    }

    /* File Uploader */
    section[data-testid="stFileUploader"] {
        background-color: var(--background);
        border: 2px dashed var(--border);
        border-radius: var(--radius);
        padding: 2rem;
        transition: var(--transition);
    }

    section[data-testid="stFileUploader"]:hover {
        border-color: var(--primary);
        background-color: rgba(46, 204, 113, 0.05);
    }

    /* Radio Buttons */
    div[role="radiogroup"] label {
        background-color: var(--surface);
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid var(--border);
        margin-right: 10px;
        transition: var(--transition);
        width: 100%;
        justify-content: center;
    }

    div[role="radiogroup"] label:hover {
        border-color: var(--primary);
    }

    /* Mobile Responsiveness */
    @media (max-width: 768px) {
        .wizard-step span {
            display: none;
        }
        .st-card {
            padding: 1.5rem;
        }
        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
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
<div style="text-align: center; margin-bottom: 2rem; margin-top: 1rem;">
    <h1 style="font-size: 3rem; margin-bottom: 0;">🥥 Wallet to Cashew</h1>
    <p style="font-size: 1.1rem; opacity: 0.7;">The premium migration tool for your finances</p>
</div>
""", unsafe_allow_html=True)

# --- WIZARD NAVIGATION ---
steps = [
    {"label": "Import File", "icon": "📂"},
    {"label": "Categories", "icon": "🏷️"},
    {"label": "Smart Mapping", "icon": "🤖"},
    {"label": "Export Data", "icon": "🚀"}
]

wizard_html = '<div class="wizard-container">'
for i, s in enumerate(steps):
    active = "wizard-active" if st.session_state.step == i + 1 else ""
    # Use one-line strings to avoid Markdown code block indentation issues
    wizard_html += f'<div class="wizard-step {active}">'
    wizard_html += f'<span class="icon">{s["icon"]}</span>'
    wizard_html += f'<span>{s["label"]}</span>'
    wizard_html += '</div>'
wizard_html += '</div>'
st.markdown(wizard_html, unsafe_allow_html=True)

# --- ROUTER ---
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
<div style="text-align: center; margin-top: 4rem; padding-bottom: 2rem; opacity: 0.3; font-size: 0.8rem;">
    Designed for perfection.
</div>
""", unsafe_allow_html=True)
