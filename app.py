import streamlit as st
import copy
from models import DEFAULT_CASHEW_STRUCTURE
from ui.step1_upload import render_step1
from ui.step2_categories import render_step2
from ui.step3_mapping import render_step3
from ui.step4_export import render_step4

# --- CONFIG & STYLE ---
st.set_page_config(page_title="Wallet to Cashew Migrator", page_icon="🥥", layout="wide")

# CSS Avanzato per UI Moderna e Responsive
# Nota: Non cerchiamo di wrappare i widget in div HTML custom perché Streamlit non lo permette.
# Invece, stilizziamo i contenitori nativi e gli elementi globali.
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Global Typography */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    h1, h2, h3 {
        font-weight: 700;
        letter-spacing: -0.02em;
    }

    /* Gradient Text for Main Titles */
    .gradient-text {
        background: linear-gradient(90deg, #2ECC71, #3498DB);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
    }

    /* --- CUSTOM WIZARD --- */
    .wizard-container {
        display: flex;
        justify-content: center;
        margin-bottom: 2rem;
        gap: 1rem;
        flex-wrap: wrap;
    }
    .wizard-step {
        background-color: #1E1E1E;
        color: #B0BEC5;
        padding: 0.8rem 1.5rem;
        border-radius: 50px;
        font-weight: 500;
        border: 1px solid #333;
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 0.9rem;
        transition: all 0.3s ease;
    }
    .wizard-active {
        background-color: rgba(46, 204, 113, 0.2);
        color: #2ECC71;
        border-color: #2ECC71;
        box-shadow: 0 0 15px rgba(46, 204, 113, 0.3);
    }

    /* --- STREAMLIT COMPONENTS STYLING --- */

    /* Styled Containers (st.container(border=True)) */
    div[data-testid="stVerticalBlockBorderWrapper"] > div {
        background-color: #1E1E1E;
        border-radius: 16px;
        border: 1px solid #333;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        padding: 20px;
    }

    /* Primary Buttons */
    div.stButton > button {
        border-radius: 10px;
        font-weight: 600;
        border: none;
        padding: 0.5rem 1rem;
        transition: transform 0.1s;
    }
    div.stButton > button:active {
        transform: scale(0.98);
    }

    /* File Uploader */
    div[data-testid="stFileUploader"] {
        padding: 1rem;
        border-radius: 10px;
    }

    /* Custom Classes for Text */
    .hero-title {
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
        text-align: center;
    }
    .hero-subtitle {
        font-size: 1.2rem;
        opacity: 0.7;
        text-align: center;
        margin-bottom: 2rem;
        max-width: 600px;
        margin-left: auto;
        margin-right: auto;
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
st.markdown('<h1 class="hero-title"><span class="gradient-text">Wallet to Cashew</span></h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-subtitle">Il tool premium per migrare le tue finanze senza perdere un centesimo.</p>', unsafe_allow_html=True)

# --- WIZARD NAVIGATION ---
steps = [
    {"label": "Importa", "icon": "📂"},
    {"label": "Categorie", "icon": "🏷️"},
    {"label": "Mapping", "icon": "🤖"},
    {"label": "Esporta", "icon": "🚀"}
]

wizard_html = '<div class="wizard-container">'
for i, s in enumerate(steps):
    active = "wizard-active" if st.session_state.step == i + 1 else ""
    wizard_html += f'<div class="wizard-step {active}">'
    wizard_html += f'<span>{s["icon"]} {s["label"]}</span>'
    wizard_html += '</div>'
wizard_html += '</div>'
st.markdown(wizard_html, unsafe_allow_html=True)

# --- ROUTER ---
# Using a main container for consistent spacing
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
